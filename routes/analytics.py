from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from flask import Blueprint, jsonify, redirect, render_template, session

from app import login_required
from services.supabase_client import supabase


analytics_bp = Blueprint("analytics", __name__)


def _safe_int(val: Any, default: int = 0) -> int:
  try:
    return int(val)
  except Exception:
    return default


@analytics_bp.route("/", methods=["GET"])
@login_required
def index():
  # Keep /analytics for backward compatibility but show the same dashboard view.
  data = _collect_analytics_data()
  return render_template("analytics.html", analytics=data)


@analytics_bp.route("/data", methods=["GET"])
@login_required
def data():
  data = _collect_analytics_data()
  return jsonify({"success": True, "data": data})


@analytics_bp.route("/candidate-analytics", methods=["GET"])
@login_required
def candidate_analytics_page():
  # Recruiter/admin only
  if session.get("role", "recruiter") not in ("recruiter", "admin"):
    return redirect("/dashboard")
  return render_template("candidate_analytics.html")


def collect_analytics_data() -> Dict[str, Any]:
  return _collect_analytics_data()


def _collect_analytics_data() -> Dict[str, Any]:
  total_jobs = 0
  total_candidates = 0
  status_counts: Dict[str, int] = {}
  score_distribution: Dict[str, int] = {"Poor": 0, "Average": 0, "Good": 0, "Excellent": 0}
  top_skills: List[Dict[str, Any]] = []
  candidates_per_job: List[Dict[str, Any]] = []
  jobs_stats: List[Dict[str, Any]] = []
  daily_uploads: List[Dict[str, Any]] = []
  hiring_rate = 0.0
  most_active_job = ""

  # Jobs
  jobs: List[Dict[str, Any]] = []
  for _ in range(2):
    try:
      jobs_res = supabase.table("job_roles").select("id, title, status").execute()
      jobs = jobs_res.data or []
      break
    except Exception:
      jobs = []
      continue
  total_jobs = len(jobs)

  # Candidates
  candidates: List[Dict[str, Any]] = []
  for _ in range(2):
    try:
      # Do NOT fetch huge fields (like full resume text) for analytics aggregation.
      cand_res = (
        supabase.table("candidates")
        .select("id, job_role_id, status, ai_score, parsed_data, upload_date")
        .execute()
      )
      candidates = cand_res.data or []
      break
    except Exception:
      candidates = []
      continue
  total_candidates = len(candidates)

  # Status counts and score distribution
  status_counter = Counter()
  job_counter = Counter()
  hired_count = 0

  # Per-job aggregates for the "Job Performance" table
  per_job: Dict[str, Dict[str, Any]] = {}

  scores: List[float] = []
  skills_counter = Counter()
  date_counter = Counter()

  for c in candidates:
    status = c.get("status", "pending")
    status_counter[status] += 1

    if status == "hired":
      hired_count += 1

    job_role_id = c.get("job_role_id")
    if job_role_id:
      job_counter[job_role_id] += 1

      if job_role_id not in per_job:
        per_job[job_role_id] = {
          "job_id": job_role_id,
          "job_title": "",
          "total_candidates": 0,
          "sum_scores": 0.0,
          "shortlisted": 0,
          "hired": 0,
        }

      per_job[job_role_id]["total_candidates"] += 1

    score = float(c.get("ai_score") or 0.0)
    scores.append(score)
    if job_role_id and job_role_id in per_job:
      per_job[job_role_id]["sum_scores"] += score

    if score < 40:
      score_distribution["Poor"] += 1
    elif score < 60:
      score_distribution["Average"] += 1
    elif score < 80:
      score_distribution["Good"] += 1
    else:
      score_distribution["Excellent"] += 1

    if job_role_id and job_role_id in per_job:
      if status == "shortlisted":
        per_job[job_role_id]["shortlisted"] += 1
      if status == "hired":
        per_job[job_role_id]["hired"] += 1

    parsed = c.get("parsed_data") or {}
    skills = []
    if isinstance(parsed, dict):
      skills = parsed.get("skills_extracted") or []
    for skill in skills or []:
      skills_counter[skill] += 1

    # upload_date per day
    upload_date = c.get("upload_date")
    if upload_date:
      try:
        dt = datetime.fromisoformat(upload_date.replace("Z", "+00:00"))
        day_key = dt.date().isoformat()
        date_counter[day_key] += 1
      except Exception:
        pass

  status_counts = dict(status_counter)

  # Top 10 skills
  top_skills = [
    {"skill": name, "count": count} for name, count in skills_counter.most_common(10)
  ]

  # Candidates per job (top 5)
  job_title_map = {j["id"]: j.get("title", "") for j in jobs}
  for job_id, count in job_counter.most_common(5):
    candidates_per_job.append(
      {"job_id": job_id, "job_title": job_title_map.get(job_id, ""), "count": count}
    )

  # Per-job stats list (all jobs that have at least one candidate)
  for job_id, stats in per_job.items():
    stats["job_title"] = job_title_map.get(job_id, "")
    total = _safe_int(stats.get("total_candidates"), 0)
    sum_scores = float(stats.get("sum_scores") or 0.0)
    avg = sum_scores / total if total else 0.0
    jobs_stats.append(
      {
        "job_id": job_id,
        "job_title": stats.get("job_title") or "",
        "total_candidates": total,
        "average_score": avg,
        "shortlisted": _safe_int(stats.get("shortlisted"), 0),
        "hired": _safe_int(stats.get("hired"), 0),
      }
    )

  if total_candidates:
    hiring_rate = (hired_count / total_candidates) * 100.0

  if candidates_per_job:
    most_active_job = candidates_per_job[0].get("job_title", "")

  # Daily uploads: last 14 days sorted ascending
  for date_str, count in sorted(date_counter.items()):
    daily_uploads.append({"date": date_str, "count": count})

  avg_score = sum(scores) / len(scores) if scores else 0.0

  return {
    "total_jobs": total_jobs,
    "total_candidates": total_candidates,
    "status_counts": status_counts,
    "score_distribution": score_distribution,
    "top_skills": top_skills,
    "candidates_per_job": candidates_per_job,
    "jobs_stats": jobs_stats,
    "daily_uploads": daily_uploads,
    "average_score": avg_score,
    "hiring_rate": hiring_rate,
    "most_active_job": most_active_job,
  }

