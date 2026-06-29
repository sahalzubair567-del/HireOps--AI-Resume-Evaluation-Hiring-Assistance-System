"""
Backfill candidates.skill_match_breakdown deterministically.

This fixes cases where the AI returned an inconsistent structure/casing so the UI shows 0/3.

Run: python backfill_skill_breakdown.py
"""

from services.supabase_client import supabase
from services.gpt_service import _compute_skill_match_breakdown


def main() -> None:
  # Current schema uses job_role_id and stores extracted skills under parsed_data.skills_extracted
  cands = (
    supabase.table("candidates")
    .select("id, job_role_id, parsed_data")
    .execute()
    .data
    or []
  )
  job_ids = list({c.get("job_role_id") for c in cands if c.get("job_role_id")})
  jobs_by_id = {}
  if job_ids:
    jobs = supabase.table("job_roles").select("id, required_skills").in_("id", job_ids).execute().data or []
    jobs_by_id = {j["id"]: j for j in jobs}

  updated = 0
  for c in cands:
    job_id = c.get("job_role_id")
    job = jobs_by_id.get(job_id) if job_id else None
    if not job:
      continue
    parsed = c.get("parsed_data") or {}
    if not isinstance(parsed, dict):
      parsed = {}
    extracted = parsed.get("skills_extracted") or []
    breakdown = _compute_skill_match_breakdown(job.get("required_skills"), extracted)
    # Current schema column is score_breakdown (jsonb)
    supabase.table("candidates").update({"score_breakdown": breakdown}).eq("id", c["id"]).execute()
    updated += 1

  print(f"Backfill complete. Updated {updated} candidates.")


if __name__ == "__main__":
  main()

