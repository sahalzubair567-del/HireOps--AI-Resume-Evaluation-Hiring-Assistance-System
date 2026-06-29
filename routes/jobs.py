from __future__ import annotations

import ast
from typing import Dict, List

from flask import Blueprint, flash, redirect, render_template, request, session

from app import login_required
from services.supabase_client import supabase


jobs_bp = Blueprint("jobs", __name__)


def _parse_required_skills(form) -> List[str]:
  names = form.getlist("skill_name[]")
  skills: List[str] = []
  for name in names:
    name = (name or "").strip()
    if not name:
      continue
    skills.append(name)
  return skills


def _normalize_required_skills(value) -> List[str]:
  """Return required_skills as a clean list[str], even if legacy formats exist."""
  if not value:
    return []

  # If Supabase returns a PostgreSQL text[] this is already list[str].
  if isinstance(value, list):
    out: List[str] = []
    for item in value:
      if isinstance(item, str):
        s = item.strip()
        if not s:
          continue
        # Legacy case: stringified dict like "{'skill': 'react', 'weight': 1}"
        if s.startswith("{") and "skill" in s:
          try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, dict) and parsed.get("skill"):
              out.append(str(parsed["skill"]).strip())
              continue
          except Exception:
            pass
        out.append(s)
      elif isinstance(item, dict):
        if item.get("skill"):
          out.append(str(item["skill"]).strip())
      else:
        out.append(str(item).strip())
    return [x for x in out if x]

  # If a single dict is stored, extract it.
  if isinstance(value, dict):
    if value.get("skill"):
      return [str(value["skill"]).strip()]
    return [str(value).strip()]

  # Fallback: single string, maybe comma-separated or a stringified python list/dict.
  if isinstance(value, str):
    s = value.strip()
    if not s:
      return []
    if s.startswith("[") or s.startswith("{"):
      try:
        parsed = ast.literal_eval(s)
        return _normalize_required_skills(parsed)
      except Exception:
        return [s]
    if "," in s:
      return [x.strip() for x in s.split(",") if x.strip()]
    return [s]

  return [str(value).strip()]


@jobs_bp.route("/", methods=["GET"])
@login_required
def list_jobs():
  try:
    jobs_res = (
      supabase.table("job_roles")
      .select("*")
      .order("created_at", desc=True)
      .execute()
    )
    jobs = jobs_res.data or []
  except Exception:
    jobs = []

  # Fetch candidate counts per job
  counts: Dict[str, int] = {}
  try:
    cand_res = supabase.table("candidates").select("job_role_id").execute()
    for row in cand_res.data or []:
      job_role_id = row.get("job_role_id")
      if job_role_id:
        counts[job_role_id] = counts.get(job_role_id, 0) + 1
  except Exception:
    counts = {}

  for job in jobs:
    job["candidate_count"] = counts.get(job.get("id"), 0)
    job["required_skills"] = _normalize_required_skills(job.get("required_skills"))

  return render_template("jobs/list.html", jobs=jobs)


@jobs_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_job():
  if request.method == "GET":
    return render_template("jobs/create.html", job=None)

  form = request.form
  title = (form.get("title") or "").strip()
  description = (form.get("description") or "").strip()
  status = (form.get("status") or "open").strip()
  employment_type = (form.get("employment_type") or "").strip() or None
  location = (form.get("location") or "").strip() or None
  min_experience = int(form.get("min_experience") or 0)
  max_experience = int(form.get("max_experience") or 0)

  required_skills = _parse_required_skills(form)

  if not title:
    flash("Title is required.", "error")
    return render_template("jobs/create.html", job=None)

  try:
    payload = {
      "title": title,
      "description": description,
      "min_experience": min_experience,
      "max_experience": max_experience,
      "location": location,
      "status": status,
      "required_skills": required_skills,
      "created_by": session.get("user_id"),
    }
    # Some Supabase instances can have a stale schema cache after migrations.
    # Only send optional fields when set to reduce cache-related failures.
    if employment_type:
      payload["employment_type"] = employment_type

    supabase.table("job_roles").insert(payload).execute()
    flash("Job role created.", "success")
  except Exception as exc:
    print(f"Could not create job role title={title!r}: {exc}")
    # Surface the real cause in the UI to make debugging possible.
    flash(f"Could not create job role. ({type(exc).__name__}: {exc})", "error")

  return redirect("/jobs/")


@jobs_bp.route("/<job_id>", methods=["GET"])
@login_required
def job_detail(job_id: str):
  try:
    job_res = supabase.table("job_roles").select("*").eq("id", job_id).execute()
    job = job_res.data[0] if job_res.data else None
  except Exception:
    job = None

  if not job:
    flash("Job not found.", "error")
    return redirect("/jobs/")

  job["required_skills"] = _normalize_required_skills(job.get("required_skills"))

  try:
    cand_res = (
      supabase.table("candidates")
      .select("*")
      .eq("job_role_id", job_id)
      .order("ai_score", desc=True)
      .execute()
    )
    candidates = cand_res.data or []
  except Exception:
    candidates = []

  return render_template("jobs/detail.html", job=job, candidates=candidates)


@jobs_bp.route("/<job_id>/edit", methods=["GET", "POST"])
@login_required
def edit_job(job_id: str):
  try:
    job_res = supabase.table("job_roles").select("*").eq("id", job_id).execute()
    job = job_res.data[0] if job_res.data else None
  except Exception:
    job = None

  if not job:
    flash("Job not found.", "error")
    return redirect("/jobs/")

  if request.method == "GET":
    job["required_skills"] = _normalize_required_skills(job.get("required_skills"))
    return render_template("jobs/create.html", job=job)

  form = request.form
  title = (form.get("title") or "").strip()
  description = (form.get("description") or "").strip()
  status = (form.get("status") or "open").strip()
  employment_type = (form.get("employment_type") or "").strip() or None
  location = (form.get("location") or "").strip() or None
  min_experience = int(form.get("min_experience") or 0)
  max_experience = int(form.get("max_experience") or 0)

  required_skills = _parse_required_skills(form)

  try:
    payload = {
      "title": title,
      "description": description,
      "min_experience": min_experience,
      "max_experience": max_experience,
      "location": location,
      "status": status,
      "required_skills": required_skills,
    }
    if employment_type:
      payload["employment_type"] = employment_type

    supabase.table("job_roles").update(payload).eq("id", job_id).execute()
    flash("Job role updated.", "success")
  except Exception as exc:
    # Print the real error so it's debuggable in the Flask console.
    print(f"Could not update job role id={job_id}: {exc}")
    flash(f"Could not update job role. ({type(exc).__name__}: {exc})", "error")

  return redirect(f"/jobs/{job_id}")


@jobs_bp.route("/<job_id>/delete", methods=["POST"])
@login_required
def delete_job(job_id: str):
  try:
    supabase.table("job_roles").delete().eq("id", job_id).execute()
    flash("Job role deleted.", "success")
  except Exception:
    flash("Could not delete job role.", "error")

  return redirect("/jobs/")

