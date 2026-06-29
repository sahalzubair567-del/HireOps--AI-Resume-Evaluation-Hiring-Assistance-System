from __future__ import annotations

from typing import Any, Dict, List

from openai import OpenAI

from config import GPT_MODEL, OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)

def _normalize_skill(s: str) -> str:
  return (s or "").strip().lower()

def _normalize_skill_key(s: str) -> str:
  """Normalize skill text for matching (case-insensitive, punctuation-insensitive)."""
  s = _normalize_skill(s)
  # Keep only letters/numbers so "Node.js" matches "node js"
  return "".join(ch for ch in s if ch.isalnum())


def _compute_skill_match_breakdown(required_skills, skills_extracted) -> Dict[str, Any]:
  """Build a consistent skill_match_breakdown using required_skills + extracted skills.

  required_skills: usually [{skill: str, weight: int}, ...]
  skills_extracted: array of strings
  """
  req_items = []
  for r in (required_skills or []):
    if isinstance(r, dict):
      name = r.get("skill") or r.get("name")
      if name:
        req_items.append({"skill": str(name), "weight": int(r.get("weight") or 1)})
    elif isinstance(r, str) and r.strip():
      req_items.append({"skill": r.strip(), "weight": 1})

  cand_list = []
  for s in (skills_extracted or []):
    if s is None:
      continue
    cand_list.append(str(s))
  cand_norm = {_normalize_skill_key(s) for s in cand_list if _normalize_skill_key(s)}

  breakdown: Dict[str, Any] = {}
  for r in req_items:
    skill_name = r["skill"]
    weight = max(1, int(r.get("weight") or 1))
    matched = _normalize_skill_key(skill_name) in cand_norm
    breakdown[skill_name] = {"matched": bool(matched), "weight": weight}

  return breakdown


def _extract_marketplace_skills(profile: Dict[str, Any]) -> List[str]:
  skills = profile.get("skills") or []
  out: List[str] = []
  for s in skills:
    if isinstance(s, dict):
      val = s.get("name") or s.get("skill") or ""
    else:
      val = str(s)
    val = val.strip()
    if val:
      out.append(val)
  return out


def _deterministic_marketplace_score(profile: Dict[str, Any], job_role: Dict[str, Any]) -> Dict[str, Any]:
  """Fallback scoring without AI (fast + predictable)."""
  req = job_role.get("required_skills") or []
  # required_skills format: [{skill: str, weight: int}, ...]
  req_items = []
  for r in req:
    if isinstance(r, dict) and (r.get("skill") or r.get("name")):
      req_items.append({"skill": str(r.get("skill") or r.get("name")), "weight": int(r.get("weight") or 1)})
  req_total = sum(max(1, int(x.get("weight") or 1)) for x in req_items) or 1

  cand_skills = _extract_marketplace_skills(profile)
  cand_set = {_normalize_skill_key(s) for s in cand_skills}
  matched = []
  matched_weight = 0
  for r in req_items:
    sk = _normalize_skill_key(r["skill"])
    w = max(1, int(r.get("weight") or 1))
    if sk and sk in cand_set:
      matched.append(r["skill"])
      matched_weight += w

  skill_score = (matched_weight / req_total) * 100.0

  years = profile.get("years_experience")
  try:
    years_val = float(years) if years is not None else 0.0
  except Exception:
    years_val = 0.0
  try:
    exp_min = float(job_role.get("experience_min") or 0)
    exp_max = float(job_role.get("experience_max") or 0)
  except Exception:
    exp_min, exp_max = 0.0, 0.0
  exp_score = 0.0
  if exp_min <= 0 and exp_max <= 0:
    exp_score = 70.0
  elif exp_min <= years_val <= (exp_max if exp_max > 0 else years_val):
    exp_score = 100.0
  else:
    # proportional outside range
    target = exp_min if years_val < exp_min else (exp_max if exp_max > 0 else exp_min)
    exp_score = max(0.0, min(100.0, (years_val / (target or 1.0)) * 100.0))

  # Weight skills heavily; add experience as secondary
  score = 0.7 * skill_score + 0.3 * exp_score
  score = max(0.0, min(100.0, float(score)))

  reasons: List[str] = []
  if matched:
    reasons.append(
      f"Strong alignment with key required skills: {', '.join(matched[:6])}{'…' if len(matched) > 6 else ''}."
    )
  else:
    reasons.append(
      "Potential gap: could strengthen fit by adding or clearly highlighting the required skills in the profile."
    )
  reasons.append(f"Experience: {int(years_val) if years_val.is_integer() else years_val} years.")
  if profile.get("headline"):
    reasons.append(f"Headline: {profile.get('headline')}.")

  return {"score": round(score, 2), "reasons": reasons[:6]}


def analyze_marketplace_candidate(profile: Dict[str, Any], job_role: Dict[str, Any]) -> Dict[str, Any]:
  """AI analysis for marketplace profiles. Returns {score: 0-100, reasons: [..]}.

  Falls back to deterministic scoring if AI fails or no key is configured.
  """
  # If the OpenAI key is missing, skip the AI call.
  if not OPENAI_API_KEY:
    return _deterministic_marketplace_score(profile, job_role)

  system_prompt = (
    "You are an expert recruiter. Score a candidate profile for a job role. "
    "Return a JSON object with: score (0-100 number) and reasons (array of 3-6 short bullet strings). "
    "The reasons must be written so they can be shown under a heading like 'Why this candidate is rank X'. "
    "Follow these rules strictly: "
    "(1) Start with 2-4 bullets that are purely positive, highlighting strengths and evidence for the current rank "
    "(for example: 'Strong experience with React and Python', '9 years working on web platforms'). "
    "(2) If you mention gaps or missing skills, put them after the positive bullets and start them with phrases like "
    "'Potential gap:' or 'Could improve fit by:'. "
    "(3) Avoid harsh negative phrasing like 'lacks', 'missing', 'does not have'. Instead, use growth framing such as "
    "'Could strengthen fit by gaining more experience with Django and Node.js'. "
    "(4) Keep the tone neutral and recruiter-friendly."
  )
  user_prompt = f"""Job Role:
Title: {job_role.get('title', '')}
Department: {job_role.get('department', '')}
Description: {job_role.get('description', '')}
Required Skills (with weights): {job_role.get('required_skills', [])}
Min Experience: {job_role.get('experience_min', 0)}
Max Experience: {job_role.get('experience_max', 0)}

Candidate Profile:
Full Name: {profile.get('full_name', '')}
Headline: {profile.get('headline', '')}
Location: {profile.get('location', '')}
Years Experience: {profile.get('years_experience', 0)}
Skills: {profile.get('skills', [])}
Bio: {profile.get('bio', '')}

Return JSON exactly like:
{{\"score\": 0, \"reasons\": [\"...\"]}}
"""

  data = _safe_json_object_call(system_prompt, user_prompt, max_tokens=500)
  try:
    score = float(data.get("score") or 0.0)
  except Exception:
    score = 0.0
  reasons = data.get("reasons") or []
  if not isinstance(reasons, list):
    reasons = []
  reasons = [str(r) for r in reasons if r is not None and str(r).strip()]
  reasons = _positivize_reasons(reasons)
  score = max(0.0, min(100.0, float(score)))
  if score == 0.0 and not reasons:
    return _deterministic_marketplace_score(profile, job_role)
  return {"score": round(score, 2), "reasons": reasons[:6]}


def _positivize_reasons(reasons: List[str]) -> List[str]:
  """
  Lightly rewrite common negative phrases into softer, growth-oriented language so
  the bullets read positively even if the model outputs harsher wording.
  """
  out: List[str] = []
  for r in reasons:
    text = r or ""
    lower = text.lower()

    # If the bullet already starts with a growth phrase, keep it.
    if lower.strip().startswith(("potential gap:", "could improve", "could strengthen", "opportunity to")):
      out.append(text)
      continue

    replaced = text
    # Simple phrase softening – keep it conservative to avoid changing meaning too much.
    if " lacks " in lower or lower.startswith("lacks "):
      replaced = text.replace("lacks", "could strengthen fit by adding").replace("Lacks", "Could strengthen fit by adding")
      replaced = "Potential gap: " + replaced
    elif "does not have" in lower:
      replaced = text.replace("does not have", "could strengthen fit by building more experience with")
      replaced = "Potential gap: " + replaced
    elif "missing" in lower:
      replaced = text.replace("missing", "could strengthen fit by adding")
      replaced = "Potential gap: " + replaced

    out.append(replaced)

  return out


def _safe_json_object_call(system_prompt: str, user_prompt: str, max_tokens: int) -> Dict[str, Any]:
  try:
    response = client.chat.completions.create(
      model=GPT_MODEL,
      temperature=0.3,
      max_tokens=max_tokens,
      response_format={"type": "json_object"},
      messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
      ],
    )
    content = response.choices[0].message.content or "{}"
  except Exception:
    return {}

  try:
    import json

    return json.loads(content)
  except Exception:
    return {}


def _safe_json_array_call(system_prompt: str, user_prompt: str, max_tokens: int) -> List[Dict[str, Any]]:
  try:
    response = client.chat.completions.create(
      model=GPT_MODEL,
      temperature=0.7,
      max_tokens=max_tokens,
      response_format={"type": "json_object"},
      messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
      ],
    )
    content = response.choices[0].message.content or "{}"
  except Exception:
    return []

  try:
    import json

    data = json.loads(content)
    # If the model wraps the array, try to unwrap common keys
    if isinstance(data, list):
      return data
    if isinstance(data, dict):
      for key in ("items", "questions", "data"):
        if isinstance(data.get(key), list):
          return data[key]
  except Exception:
    return []

  return []


def analyze_resume(resume_text: str, job: Dict[str, Any]) -> Dict[str, Any]:
  """
  Call GPT to analyze a resume for a specific job.

  Returns a dict with the exact keys specified in the PRD.
  On failure, returns a dict with safe default values.
  """
  system_prompt = (
    "You are an expert technical recruiter. Analyze the resume and return a structured JSON."
  )

  min_exp = job.get("min_experience", job.get("experience_min", 0))
  max_exp = job.get("max_experience", job.get("experience_max", 0))
  user_prompt = f"""Job Title: {job.get('title', '')}
Required Skills (with weights 1-3): {job.get('required_skills', [])}
Min Experience: {min_exp} years
Max Experience: {max_exp} years

Resume Text:
{resume_text}

Return a JSON with exactly these keys:
- full_name: string
- email: string (or "" if not found)
- phone: string (or "" if not found)
- skills_extracted: array of strings
- experience_years: float
- education: string (highest degree + institution)
- skill_match_breakdown: object where each key is a required skill name and value is {{"matched": bool, "weight": int}}
- ai_score: float between 0 and 100 calculated as:
    * 60% from skill match (weighted: sum matched skill weights / sum all skill weights * 100)
    * 25% from experience match (if within min-max range = 100, else proportional)
    * 15% from education (postgraduate=100, graduate=75, diploma=50, other=25)
- ai_summary: 2-3 sentence recruiter-friendly summary of this candidate's fit
"""

  data = _safe_json_object_call(system_prompt, user_prompt, max_tokens=1500)

  skills_extracted = data.get("skills_extracted", [])
  if not isinstance(skills_extracted, list):
    skills_extracted = []

  # IMPORTANT: Don't trust the model for skill_match_breakdown.
  # Build it ourselves so UI counts like "2/3 skills" are correct even with casing/punctuation differences.
  skill_match_breakdown = _compute_skill_match_breakdown(job.get("required_skills"), skills_extracted)

  # Fill safe defaults for any missing keys
  return {
    "full_name": data.get("full_name", ""),
    "email": data.get("email", ""),
    "phone": data.get("phone", ""),
    "skills_extracted": skills_extracted,
    "experience_years": data.get("experience_years", 0.0),
    "education": data.get("education", ""),
    "skill_match_breakdown": skill_match_breakdown,
    "ai_score": data.get("ai_score", 0.0),
    "ai_summary": data.get("ai_summary", ""),
  }


def generate_interview_questions(candidate: Dict[str, Any], job: Dict[str, Any]) -> List[Dict[str, Any]]:
  system_prompt = "You are a senior hiring manager creating interview questions."

  user_prompt = f"""Candidate: {candidate.get('full_name', '')}
Job Role: {job.get('title', '')}
Candidate Skills: {candidate.get('skills_extracted', [])}
Experience: {candidate.get('experience_years', 0)} years
Education: {candidate.get('education', '')}
AI Summary: {candidate.get('ai_summary', '')}

Generate exactly 10 interview questions as a JSON array.
Each item: {{"question": string, "category": one of ["Technical","Behavioral","Situational","Culture Fit"], "difficulty": one of ["Easy","Medium","Hard"]}}
Mix categories: 5 Technical, 2 Behavioral, 2 Situational, 1 Culture Fit.
Make questions specific to this candidate's background.
"""

  questions = _safe_json_array_call(system_prompt, user_prompt, max_tokens=1000)

  # Ensure we always return a list of dicts with expected keys
  normalized: List[Dict[str, Any]] = []
  for q in questions:
    if not isinstance(q, dict):
      continue
    normalized.append(
      {
        "question": q.get("question", ""),
        "category": q.get("category", "Technical"),
        "difficulty": q.get("difficulty", "Medium"),
      }
    )
  return normalized


def generate_email_draft(candidate: Dict[str, Any], job: Dict[str, Any], email_type: str) -> Dict[str, str]:
  system_prompt = "You are an HR professional writing recruitment emails."

  user_prompt = f"""Write a professional {email_type} email for:
Candidate Name: {candidate.get('full_name', '')}
Job Role: {job.get('title', '')}
Company Name: TechCorp Solutions

Return JSON with keys: "subject" (string) and "body" (string, use \\n for line breaks).
Keep it warm, professional, and concise. No placeholders in brackets.
"""

  data = _safe_json_object_call(system_prompt, user_prompt, max_tokens=600)

  return {
    "subject": data.get("subject", ""),
    "body": data.get("body", ""),
  }

