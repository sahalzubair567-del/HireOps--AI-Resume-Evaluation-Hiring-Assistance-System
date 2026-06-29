"""Recruiter dashboard: stats + shortlist selections (recruiter_selections)."""
from __future__ import annotations

from typing import Any, Dict, List

from services.supabase_client import supabase


def get_stats(user_id: str) -> dict | None:
  """Dashboard stats based on recruiter_selections."""
  try:
    sel = (
      supabase.table("recruiter_selections")
      .select("id, status")
      .eq("recruiter_id", user_id)
      .execute()
    )
    selections = sel.data or []
    total = len(selections)
    accepted = sum(1 for s in selections if (s.get("status") or "").lower() == "accepted")
    pending = sum(1 for s in selections if (s.get("status") or "").lower() == "pending")
    rate = f"{(accepted / total * 100):.0f}%" if total > 0 else "0%"
    return {
      "candidates_viewed": 0,
      "selections_made": total,
      "accepted": accepted,
      "pending": pending,
      "acceptance_rate": rate,
    }
  except Exception:
    return {
      "candidates_viewed": 0,
      "selections_made": 0,
      "accepted": 0,
      "pending": 0,
      "acceptance_rate": "0%",
    }


def get_selections(user_id: str, status_filter: str = "all") -> List[Dict[str, Any]]:
  """List selections made by recruiter. status_filter: all, pending, accepted, rejected."""
  try:
    q = (
      supabase.table("recruiter_selections")
      .select("*")
      .eq("recruiter_id", user_id)
      .order("selected_at", desc=True)
    )
    if status_filter in ("pending", "accepted", "rejected"):
      q = q.eq("status", status_filter)
    rows = q.execute().data or []
  except Exception:
    rows = []

  candidate_ids = [r.get("candidate_id") for r in rows if r.get("candidate_id")]
  candidates_by_id: Dict[str, Dict[str, Any]] = {}
  if candidate_ids:
    try:
      cres = supabase.table("candidates").select("id, full_name, email, job_role_id, ai_score, status").in_("id", candidate_ids).execute()
      for c in (cres.data or []):
        cid = c.get("id")
        if cid:
          candidates_by_id[cid] = c
    except Exception:
      candidates_by_id = {}

  job_ids = list({c.get("job_role_id") for c in candidates_by_id.values() if c.get("job_role_id")})
  jobs_by_id: Dict[str, Dict[str, Any]] = {}
  if job_ids:
    try:
      jres = supabase.table("job_roles").select("id, title").in_("id", job_ids).execute()
      for j in (jres.data or []):
        jid = j.get("id")
        if jid:
          jobs_by_id[jid] = j
    except Exception:
      jobs_by_id = {}

  out: List[Dict[str, Any]] = []
  for r in rows:
    cand = candidates_by_id.get(r.get("candidate_id") or "", {})
    job = jobs_by_id.get(cand.get("job_role_id") or "", {})
    out.append(
      {
        "id": r.get("id"),
        "candidate_id": r.get("candidate_id"),
        "candidate_name": cand.get("full_name") or "Candidate",
        "candidate_email": cand.get("email") or "",
        "job_title": job.get("title") or "",
        "status": r.get("status") or "pending",
        "selected_at": r.get("selected_at"),
        "notes": r.get("notes") or "",
      }
    )
  return out


def make_selection(user_id: str, candidate_id: str, job_role_id: str | None = None, notes: str | None = None) -> tuple[dict, int]:
  """Create a recruiter_selections row."""
  if not candidate_id:
    return {"error": "candidate_id required"}, 400

  try:
    payload: Dict[str, Any] = {
      "recruiter_id": user_id,
      "candidate_id": candidate_id,
      "job_role_id": job_role_id,
      "status": "pending",
      "notes": (notes or "").strip() or None,
    }
    row = supabase.table("recruiter_selections").insert(payload).execute()
    if row.data and len(row.data) > 0:
      return {"status": "success", "data": row.data[0]}, 201
  except Exception:
    pass

  return {"error": "Failed to create selection"}, 500
