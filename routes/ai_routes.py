from __future__ import annotations

from flask import Blueprint, jsonify, request

from app import login_required
from services import gpt_service
from services.supabase_client import supabase


ai_bp = Blueprint("ai_routes", __name__)


@ai_bp.route("/generate-questions/<candidate_id>", methods=["POST"])
@login_required
def generate_questions(candidate_id: str):
  try:
    cand_res = supabase.table("candidates").select("*").eq("id", candidate_id).execute()
    candidate = cand_res.data[0] if cand_res.data else None
  except Exception:
    candidate = None

  if not candidate:
    return jsonify({"success": False, "error": "Candidate not found"}), 404

  job_id = candidate.get("job_role_id")
  job = None
  if job_id:
    try:
      job_res = supabase.table("job_roles").select("*").eq("id", job_id).execute()
      job = job_res.data[0] if job_res.data else None
    except Exception:
      job = None

  if not job:
    return jsonify({"success": False, "error": "Job not found"}), 404

  parsed = candidate.get("parsed_data") or {}
  if not isinstance(parsed, dict):
    parsed = {}
  cand_ctx = dict(candidate)
  cand_ctx.update(parsed)
  questions = gpt_service.generate_interview_questions(cand_ctx, job)

  return jsonify({"success": True, "questions": questions})


@ai_bp.route("/generate-email/<candidate_id>", methods=["POST"])
@login_required
def generate_email(candidate_id: str):
  email_type = (request.form.get("type") or "").strip() or "acceptance"
  if email_type not in ("acceptance", "rejection"):
    email_type = "acceptance"

  try:
    cand_res = supabase.table("candidates").select("*").eq("id", candidate_id).execute()
    candidate = cand_res.data[0] if cand_res.data else None
  except Exception:
    candidate = None

  if not candidate:
    return jsonify({"success": False, "error": "Candidate not found"}), 404

  job_id = candidate.get("job_role_id")
  job = None
  if job_id:
    try:
      job_res = supabase.table("job_roles").select("*").eq("id", job_id).execute()
      job = job_res.data[0] if job_res.data else None
    except Exception:
      job = None

  if not job:
    return jsonify({"success": False, "error": "Job not found"}), 404

  parsed = candidate.get("parsed_data") or {}
  if not isinstance(parsed, dict):
    parsed = {}
  cand_ctx = dict(candidate)
  cand_ctx.update(parsed)
  draft = gpt_service.generate_email_draft(cand_ctx, job, email_type)

  return jsonify({"success": True, "subject": draft.get("subject", ""), "body": draft.get("body", "")})


@ai_bp.route("/reanalyze/<candidate_id>", methods=["POST"])
@login_required
def reanalyze(candidate_id: str):
  try:
    cand_res = supabase.table("candidates").select("*").eq("id", candidate_id).execute()
    candidate = cand_res.data[0] if cand_res.data else None
  except Exception:
    candidate = None

  if not candidate:
    return jsonify({"success": False, "error": "Candidate not found"}), 404

  job_id = candidate.get("job_role_id")
  job = None
  if job_id:
    try:
      job_res = supabase.table("job_roles").select("*").eq("id", job_id).execute()
      job = job_res.data[0] if job_res.data else None
    except Exception:
      job = None

  if not job:
    return jsonify({"success": False, "error": "Job not found"}), 404

  resume_text = candidate.get("resume_text", "") or ""
  analysis = gpt_service.analyze_resume(resume_text, job)

  try:
    supabase.table("candidates").update(
      {
        "ai_score": analysis.get("ai_score", 0.0),
        "parsed_data": analysis,
        "score_breakdown": analysis.get("skill_match_breakdown", {}),
      }
    ).eq("id", candidate_id).execute()
  except Exception:
    return jsonify({"success": False, "error": "Failed to update candidate"}), 500

  return jsonify({"success": True, "score": analysis.get("ai_score", 0.0)})

