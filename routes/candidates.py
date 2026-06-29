from __future__ import annotations

import csv
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import (
  Blueprint,
  Response,
  jsonify,
  redirect,
  render_template,
  request,
  session,
)

from app import login_required
from services import gpt_service, resume_parser
from services.scoring_service import get_score_color, get_score_label
from services.supabase_client import supabase


candidates_bp = Blueprint("candidates", __name__)


def _get_current_user_id() -> str | None:
  return session.get("user_id")


@candidates_bp.route("/public-submissions", methods=["GET"])
@login_required
def public_submissions():
  try:
    res = (
      supabase.table("candidates")
      .select("*")
      .order("upload_date", desc=True)
      .execute()
    )
    candidates = res.data or []
  except Exception:
    candidates = []

  job_ids = list({c.get("job_role_id") for c in candidates if c.get("job_role_id")})
  jobs_map: Dict[str, Dict[str, Any]] = {}
  if job_ids:
    try:
      jr = supabase.table("job_roles").select("*").in_("id", job_ids).execute()
      jobs_map = {j["id"]: j for j in jr.data or []}
    except Exception:
      jobs_map = {}

  for c in candidates:
    c["job"] = jobs_map.get(c.get("job_role_id"))

  return render_template("candidates/public_submissions.html", candidates=candidates)


@candidates_bp.route("/apply/<job_id>", methods=["GET", "POST"])
def public_apply(job_id: str):
  if request.method == "GET":
    try:
      job_res = supabase.table("job_roles").select("*").eq("id", job_id).execute()
      job = job_res.data[0] if job_res.data else None
    except Exception:
      job = None

    if not job:
      return render_template("public_apply_not_found.html"), 404

    return render_template("public_apply.html", job=job)

  files = request.files.getlist("resumes")
  if not files:
    return jsonify({"success": False, "error": "No files uploaded"}), 400

  from config import MAX_RESUMES_PER_UPLOAD

  files = files[: MAX_RESUMES_PER_UPLOAD]

  try:
    job_res = supabase.table("job_roles").select("*").eq("id", job_id).execute()
    job = job_res.data[0] if job_res.data else None
  except Exception:
    job = None

  if not job:
    return jsonify({"success": False, "error": "Job not found"}), 404

  processed = 0
  for f in files:
    filename = f.filename or ""
    if not filename:
      continue
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in {"pdf", "docx"}:
      continue

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
      temp_path = tmp.name
      f.save(temp_path)

    try:
      resume_text = resume_parser.extract_text(temp_path, filename)
      analysis = gpt_service.analyze_resume(resume_text, job)

      candidate_data: Dict[str, Any] = {
        "full_name": analysis.get("full_name", ""),
        "email": analysis.get("email", ""),
        "phone": analysis.get("phone", ""),
        "job_role_id": job_id,
        "resume_text": resume_text,
        "ai_score": analysis.get("ai_score", 0.0),
        "parsed_data": analysis,
        "score_breakdown": analysis.get("skill_match_breakdown", {}),
        "uploaded_by": None,
        "resume_url": None,
        "notes": None,
        "upload_date": datetime.now(timezone.utc).isoformat(),
        "is_marketplace": False,
      }

      supabase.table("candidates").insert(candidate_data).execute()
      processed += 1
    except Exception:
      pass
    finally:
      try:
        os.remove(temp_path)
      except OSError:
        pass

  return jsonify({"success": True, "count": processed, "job_id": job_id})


@candidates_bp.route("/upload/<job_id>", methods=["GET", "POST"])
@login_required
def upload(job_id: str):
  if request.method == "GET":
    try:
      job_res = supabase.table("job_roles").select("*").eq("id", job_id).execute()
      job = job_res.data[0] if job_res.data else None
    except Exception:
      job = None

    if not job:
      return redirect("/jobs/")

    return render_template("candidates/upload.html", job=job)

  # POST: handle file upload
  files = request.files.getlist("resumes")
  if not files:
    return jsonify({"success": False, "error": "No files uploaded"}), 400

  # Limit to MAX_RESUMES_PER_UPLOAD enforced on frontend; backend is defensive as well
  from config import MAX_RESUMES_PER_UPLOAD

  files = files[: MAX_RESUMES_PER_UPLOAD]

  try:
    job_res = supabase.table("job_roles").select("*").eq("id", job_id).execute()
    job = job_res.data[0] if job_res.data else None
  except Exception:
    job = None

  if not job:
    return jsonify({"success": False, "error": "Job not found"}), 404

  processed = 0
  for f in files:
    filename = f.filename or ""
    if not filename:
      continue
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in {"pdf", "docx"}:
      continue

    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
      temp_path = tmp.name
      f.save(temp_path)

    try:
      resume_text = resume_parser.extract_text(temp_path, filename)
      analysis = gpt_service.analyze_resume(resume_text, job)

      candidate_data: Dict[str, Any] = {
        "full_name": analysis.get("full_name", ""),
        "email": analysis.get("email", ""),
        "phone": analysis.get("phone", ""),
        "job_role_id": job_id,
        "resume_text": resume_text,
        "ai_score": analysis.get("ai_score", 0.0),
        "parsed_data": analysis,
        "score_breakdown": analysis.get("skill_match_breakdown", {}),
        "uploaded_by": _get_current_user_id(),
        "resume_url": None,
        "notes": None,
        "upload_date": datetime.now(timezone.utc).isoformat(),
        "is_marketplace": False,
      }

      supabase.table("candidates").insert(candidate_data).execute()
      processed += 1
    except Exception:
      # Skip failed file, continue with others
      pass
    finally:
      try:
        os.remove(temp_path)
      except OSError:
        pass

  return jsonify({"success": True, "count": processed, "job_id": job_id})


@candidates_bp.route("/<candidate_id>", methods=["GET"])
@login_required
def candidate_detail(candidate_id: str):
  try:
    cand_res = (
      supabase.table("candidates")
      .select("*")
      .eq("id", candidate_id)
      .execute()
    )
    candidate = cand_res.data[0] if cand_res.data else None
  except Exception:
    candidate = None

  if not candidate:
    return redirect("/jobs/")

  job_id = candidate.get("job_role_id")
  job = None
  if job_id:
    try:
      job_res = supabase.table("job_roles").select("*").eq("id", job_id).execute()
      job = job_res.data[0] if job_res.data else None
    except Exception:
      job = None

  # Notes: stored as plain text on candidates.notes (newline-separated)
  notes_text = (candidate.get("notes") or "").strip()
  notes: List[Dict[str, Any]] = []
  if notes_text:
    for line in [x.strip() for x in notes_text.splitlines() if x.strip()]:
      notes.append({"recruiter_name": "Recruiter", "note": line, "created_at": ""})

  score = float(candidate.get("ai_score") or 0.0)
  score_label = get_score_label(score)
  score_color = get_score_color(score)

  return render_template(
    "candidates/detail.html",
    candidate=candidate,
    job=job,
    notes=notes,
    interview_questions=[],
    email_drafts=[],
    score_label=score_label,
    score_color=score_color,
  )


@candidates_bp.route("/<candidate_id>/status", methods=["POST"])
@login_required
def update_status(candidate_id: str):
  new_status = (request.form.get("status") or "").strip()
  if not new_status:
    return jsonify({"success": False, "error": "Missing status"}), 400

  # Get existing candidate to know old status
  old_status = None
  try:
    cand_res = supabase.table("candidates").select("*").eq("id", candidate_id).execute()
    candidate = cand_res.data[0] if cand_res.data else None
    if candidate:
      old_status = candidate.get("status")
  except Exception:
    candidate = None

  try:
    supabase.table("candidates").update({"status": new_status}).eq("id", candidate_id).execute()
  except Exception:
    return jsonify({"success": False, "error": "Failed to update status"}), 500

  # Append status change to candidates.notes for lightweight history.
  try:
    recruiter_name = session.get("full_name", "Recruiter")
    now_iso = datetime.now(timezone.utc).isoformat()
    note_line = f"[{now_iso}] Status: {old_status or 'unknown'} → {new_status} ({recruiter_name})"
    existing = (candidate or {}).get("notes") or ""
    combined = (existing + "\n" + note_line).strip() if existing else note_line
    supabase.table("candidates").update({"notes": combined}).eq("id", candidate_id).execute()
  except Exception:
    pass

  return jsonify({"success": True, "status": new_status})


@candidates_bp.route("/<candidate_id>/note", methods=["POST"])
@login_required
def add_note(candidate_id: str):
  note_text = (request.form.get("note") or "").strip()
  if not note_text:
    return jsonify({"success": False, "error": "Note text is required"}), 400

  recruiter_name = session.get("full_name", "Recruiter")
  now_iso = datetime.now(timezone.utc).isoformat()
  line = f"[{now_iso}] {recruiter_name}: {note_text}"
  try:
    cand_res = supabase.table("candidates").select("notes").eq("id", candidate_id).execute()
    existing = (cand_res.data or [{}])[0].get("notes") or ""
    combined = (existing + "\n" + line).strip() if existing else line
    supabase.table("candidates").update({"notes": combined}).eq("id", candidate_id).execute()
  except Exception:
    return jsonify({"success": False, "error": "Failed to add note"}), 500

  return jsonify({"success": True, "note": {"note": line, "recruiter_name": recruiter_name, "created_at": now_iso}})


@candidates_bp.route("/compare", methods=["GET"])
@login_required
def compare():
  ids_param = request.args.get("ids") or ""
  ids = [i for i in ids_param.split(",") if i][:3]

  if not ids:
    return redirect("/jobs/")

  try:
    res = supabase.table("candidates").select("*").in_("id", ids).execute()
    candidates = res.data or []
  except Exception:
    candidates = []

  # Attach job info
  job_ids = {c.get("job_role_id") for c in candidates if c.get("job_role_id")}
  jobs_map: Dict[str, Dict[str, Any]] = {}
  if job_ids:
    try:
      jobs_res = supabase.table("job_roles").select("*").in_("id", list(job_ids)).execute()
      for j in jobs_res.data or []:
        jobs_map[j["id"]] = j
    except Exception:
      jobs_map = {}

  for c in candidates:
    c["job"] = jobs_map.get(c.get("job_role_id"))

  return render_template("candidates/compare.html", candidates=candidates)


@candidates_bp.route("/export/<job_id>", methods=["GET"])
@login_required
def export(job_id: str):
  # shortlisted/interview/hired only
  try:
    res = (
      supabase.table("candidates")
      .select("*")
      .eq("job_role_id", job_id)
      .in_("status", ["shortlisted", "interview", "hired"])
      .execute()
    )
    candidates = res.data or []
  except Exception:
    candidates = []

  def generate():
    output = []
    header = [
      "Name",
      "Email",
      "Phone",
      "Score",
      "Status",
      "Skills",
      "Experience",
      "Education",
      "Summary",
    ]
    output.append(header)
    for c in candidates:
      parsed = c.get("parsed_data") or {}
      if not isinstance(parsed, dict):
        parsed = {}
      skills = parsed.get("skills_extracted") or []
      row = [
        c.get("full_name", ""),
        c.get("email", ""),
        c.get("phone", ""),
        c.get("ai_score", 0),
        c.get("status", ""),
        ", ".join(skills or []),
        parsed.get("experience_years", 0),
        parsed.get("education", ""),
        parsed.get("ai_summary", ""),
      ]
      output.append(row)

    # Use csv module to create CSV content
    from io import StringIO

    sio = StringIO()
    writer = csv.writer(sio)
    for row in output:
      writer.writerow(row)
    yield sio.getvalue()

  headers = {
    "Content-Disposition": f"attachment; filename=job_{job_id}_candidates.csv",
    "Content-Type": "text/csv",
  }

  return Response(generate(), headers=headers)


@candidates_bp.route("/pipeline", methods=["GET"])
@login_required
def pipeline():
  # Optional filter by job
  job_id = request.args.get("job_id")

  try:
    query = supabase.table("candidates").select("*")
    if job_id:
      query = query.eq("job_role_id", job_id)
    res = query.execute()
    candidates = res.data or []
  except Exception:
    candidates = []

  # Attach job info
  job_ids = {c.get("job_role_id") for c in candidates if c.get("job_role_id")}
  jobs_map: Dict[str, Dict[str, Any]] = {}
  if job_ids:
    try:
      jobs_res = supabase.table("job_roles").select("*").in_("id", list(job_ids)).execute()
      for j in jobs_res.data or []:
        jobs_map[j["id"]] = j
    except Exception:
      jobs_map = {}

  for c in candidates:
    c["job"] = jobs_map.get(c.get("job_role_id"))

  return render_template("pipeline.html", candidates=candidates)

