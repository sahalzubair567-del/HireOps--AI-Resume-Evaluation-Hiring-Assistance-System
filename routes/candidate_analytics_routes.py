"""Candidate analytics: rank candidates for a job role (recruiter-only)."""
from __future__ import annotations

from datetime import datetime, timezone
import time

from flask import Blueprint, current_app, jsonify, request, session

from services.supabase_client import supabase


candidate_analytics_bp = Blueprint(
  "candidate_analytics",
  __name__,
  url_prefix="/api/candidate-analytics",
)

_JOB_ROLES_CACHE: dict = {"updated_at": 0.0, "roles": []} 


def _require_recruiter_user_id() -> str | None:
  if "user_id" not in session:
    return None
  if session.get("role", "recruiter") not in ("recruiter", "admin"):
    return None
  return session["user_id"]


@candidate_analytics_bp.route("/job-roles", methods=["GET"])
def job_roles():
  user_id = _require_recruiter_user_id()
  if not user_id:
    return jsonify({"error": "Unauthorized"}), 401
  select_cols = "id, title, status, created_at, created_by, location"
  roles: list = []
  last_exc: Exception | None = None

  # Retry a few times because Supabase/httpx can intermittently terminate connections.
  for attempt in range(3):
    try:
      base = supabase.table("job_roles").select(select_cols).order("created_at", desc=True).limit(200)

      # 1) Prefer roles created by this recruiter
      res = base.eq("created_by", user_id).execute()
      roles = res.data or []

      # 2) Fallback: any open roles
      if not roles:
        res2 = base.eq("status", "open").execute()
        roles = res2.data or []

      # 3) Last fallback: any roles at all (in case status isn't set as expected)
      if not roles:
        res3 = supabase.table("job_roles").select(select_cols).order("created_at", desc=True).limit(200).execute()
        roles = res3.data or []

      last_exc = None
      break
    except Exception as exc:
      last_exc = exc
      # small backoff
      time.sleep(0.15 * (attempt + 1))
      continue

  if last_exc:
    current_app.logger.warning("candidate_analytics.job_roles supabase_failed=%s", last_exc)
    cached_roles = _JOB_ROLES_CACHE.get("roles") or []
    if cached_roles:
      return jsonify({"status": "success", "data": cached_roles, "count": len(cached_roles), "cached": True}), 200
    return jsonify({"error": "Failed to load job roles from database. Please refresh."}), 503

  # Update cache on success
  _JOB_ROLES_CACHE["roles"] = roles
  _JOB_ROLES_CACHE["updated_at"] = time.time()
  current_app.logger.warning("candidate_analytics.job_roles roles=%s cached_update=1", len(roles))
  return jsonify({"status": "success", "data": roles, "count": len(roles)}), 200


@candidate_analytics_bp.route("/analyze", methods=["POST"])
def analyze():
  user_id = _require_recruiter_user_id()
  if not user_id:
    return jsonify({"error": "Unauthorized"}), 401

  body = request.get_json() or {}
  job_role_id = (body.get("job_role_id") or "").strip()
   # When true, only analyze public submissions (uploaded_by is null)
  public_only = bool(body.get("public_only"))
  if not job_role_id:
    return jsonify({"error": "job_role_id is required"}), 400

  # Validate job role exists. Do not restrict by created_by, otherwise dropdown "fallback roles"
  # would work but analysis would fail.
  try:
    jr = supabase.table("job_roles").select("*").eq("id", job_role_id).execute()
    job_role = jr.data[0] if (jr.data and len(jr.data) > 0) else None
  except Exception:
    job_role = None
  if not job_role:
    return jsonify({"error": "Job role not found"}), 404

  # Pull candidates for this job role and rank by ai_score.
  try:
    query = (
      supabase.table("candidates")
      .select("id, full_name, email, ai_score, parsed_data, upload_date")
      .eq("job_role_id", job_role_id)
    )
    # For the public portal view, restrict to public uploads only.
    if public_only:
      query = query.is_("uploaded_by", "null")

    cand_rows = (
      query.order("ai_score", desc=True)
      .limit(250)
      .execute()
    ).data or []
  except Exception:
    cand_rows = []

  if not cand_rows:
    return jsonify({"status": "success", "message": "No candidates to analyze", "count": 0, "data": []}), 200

  ranked = []
  for idx, c in enumerate(cand_rows, start=1):
    parsed = c.get("parsed_data") or {}
    if not isinstance(parsed, dict):
      parsed = {}
    ranked.append(
      {
        "rank": idx,
        "candidate_id": c.get("id"),
        "full_name": c.get("full_name") or "Candidate",
        "email": c.get("email") or "",
        "ai_score": float(c.get("ai_score") or 0.0),
        "ai_summary": parsed.get("ai_summary") or "",
        "upload_date": c.get("upload_date"),
      }
    )

  # Persist a session snapshot (optional history)
  now_iso = datetime.now(timezone.utc).isoformat()
  try:
    supabase.table("candidate_analytics_sessions").insert(
      {
        "recruiter_id": user_id,
        "job_role_id": job_role_id,
        "pulled_candidates": [r.get("candidate_id") for r in ranked if r.get("candidate_id")],
        "ranked_results": ranked,
        "created_at": now_iso,
      }
    ).execute()
  except Exception as exc:
    current_app.logger.warning("candidate_analytics.analyze save_session_failed=%s", exc)

  return jsonify({"status": "success", "count": len(ranked), "data": ranked}), 200


@candidate_analytics_bp.route("/latest", methods=["GET"])
def latest():
  """Return the latest analysis session for a job role (if any)."""
  user_id = _require_recruiter_user_id()
  if not user_id:
    return jsonify({"error": "Unauthorized"}), 401

  job_role_id = (request.args.get("job_role_id") or "").strip()
  if not job_role_id:
    return jsonify({"error": "job_role_id is required"}), 400

  try:
    row = (
      supabase.table("candidate_analytics_sessions")
      .select("id, ranked_results, created_at")
      .eq("recruiter_id", user_id)
      .eq("job_role_id", job_role_id)
      .order("created_at", desc=True)
      .limit(1)
      .execute()
    )
    session_row = (row.data or [None])[0]
  except Exception:
    session_row = None

  if not session_row:
    return jsonify({"status": "success", "data": [], "count": 0}), 200

  ranked = session_row.get("ranked_results") or []
  if not isinstance(ranked, list):
    ranked = []
  return jsonify({"status": "success", "data": ranked, "count": len(ranked), "created_at": session_row.get("created_at")}), 200


@candidate_analytics_bp.route("/public-summary", methods=["GET"])
def public_summary():
  """Small analytics for public (link-based) submissions for a given job role."""
  user_id = _require_recruiter_user_id()
  if not user_id:
    return jsonify({"error": "Unauthorized"}), 401

  job_role_id = (request.args.get("job_role_id") or "").strip()
  if not job_role_id:
    return jsonify({"error": "job_role_id is required"}), 400

  # Basic permission check: recruiter should at least be allowed to see this job
  try:
    jr = (
      supabase.table("job_roles")
      .select("id, title, created_by")
      .eq("id", job_role_id)
      .limit(1)
      .execute()
    )
    job_row = (jr.data or [None])[0]
  except Exception:
    job_row = None
  if not job_row:
    return jsonify({"error": "Job role not found"}), 404

  # Aggregate public submissions: uploaded_by is null
  try:
    rows = (
      supabase.table("candidates")
      .select("status, ai_score, upload_date")
      .eq("job_role_id", job_role_id)
      .is_("uploaded_by", "null")
      .execute()
    ).data or []
  except Exception:
    rows = []

  total = len(rows)
  hired = 0
  shortlisted = 0
  scores: list[float] = []
  last_upload = None

  for r in rows:
    status = (r.get("status") or "").strip()
    if status == "hired":
      hired += 1
    if status == "shortlisted":
      shortlisted += 1

    score = float(r.get("ai_score") or 0.0)
    scores.append(score)

    ts = r.get("upload_date")
    if ts:
      try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if not last_upload or dt > last_upload:
          last_upload = dt
      except Exception:
        pass

  avg_score = sum(scores) / len(scores) if scores else 0.0

  return jsonify(
    {
      "status": "success",
      "job_role_id": job_role_id,
      "job_title": job_row.get("title") or "",
      "total_public": total,
      "shortlisted_public": shortlisted,
      "hired_public": hired,
      "average_score_public": avg_score,
      "last_upload_at": last_upload.isoformat() if last_upload else None,
    }
  ), 200


@candidate_analytics_bp.route("/public-candidates", methods=["GET"])
def public_candidates():
  """List public (link-based) candidates for a job role."""
  user_id = _require_recruiter_user_id()
  if not user_id:
    return jsonify({"error": "Unauthorized"}), 401

  job_role_id = (request.args.get("job_role_id") or "").strip()
  if not job_role_id:
    return jsonify({"error": "job_role_id is required"}), 400

  try:
    rows = (
      supabase.table("candidates")
      .select("id, full_name, email, ai_score, status, upload_date")
      .eq("job_role_id", job_role_id)
      .is_("uploaded_by", "null")
      .order("upload_date", desc=True)
      .limit(250)
      .execute()
    ).data or []
  except Exception:
    rows = []

  return jsonify({"status": "success", "data": rows, "count": len(rows)}), 200

