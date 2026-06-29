"""Sample data seeding for HireOps.

Run: python seed.py
"""

import bcrypt

from services.supabase_client import supabase


def ensure_user(email: str, full_name: str, password: str, role: str) -> None:
  res = supabase.table("users").select("*").eq("email", email).execute()
  if res.data:
    return
  password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
  supabase.table("users").insert(
    {
      "full_name": full_name,
      "email": email,
      "password_hash": password_hash,
      "role": role,
    }
  ).execute()


def ensure_job(title: str, location: str, description: str, required_skills, creator_email: str):
  res = supabase.table("job_roles").select("*").eq("title", title).execute()
  if res.data:
    return

  # Find creator user
  user_res = supabase.table("users").select("*").eq("email", creator_email).execute()
  user = user_res.data[0] if user_res.data else None
  created_by = user["id"] if user else None

  supabase.table("job_roles").insert(
    {
      "title": title,
      "location": location,
      "description": description,
      "required_skills": [s["skill"] for s in required_skills],
      "min_experience": 1,
      "max_experience": 5,
      "status": "open",
      "created_by": created_by,
    }
  ).execute()


def main() -> None:
  # Demo users
  ensure_user("admin@demo.com", "Admin User", "password123", "admin")
  ensure_user("recruiter@demo.com", "Demo Recruiter", "password123", "recruiter")

  # Sample job roles with 5-6 skills each
  ensure_job(
    "Software Engineer",
    "Engineering",
    "Build and maintain backend and frontend systems.",
    [
      {"skill": "Python", "weight": 3},
      {"skill": "Flask", "weight": 2},
      {"skill": "SQL", "weight": 3},
      {"skill": "APIs", "weight": 2},
      {"skill": "Git", "weight": 1},
      {"skill": "Docker", "weight": 1},
    ],
    "admin@demo.com",
  )

  ensure_job(
    "Data Analyst",
    "Analytics",
    "Analyze business data and create dashboards.",
    [
      {"skill": "SQL", "weight": 3},
      {"skill": "Excel", "weight": 2},
      {"skill": "Python", "weight": 2},
      {"skill": "Power BI", "weight": 2},
      {"skill": "Statistics", "weight": 3},
    ],
    "admin@demo.com",
  )

  ensure_job(
    "Product Manager",
    "Product",
    "Own product roadmap and work with cross-functional teams.",
    [
      {"skill": "Roadmapping", "weight": 3},
      {"skill": "Stakeholder Management", "weight": 2},
      {"skill": "Data Analysis", "weight": 2},
      {"skill": "User Research", "weight": 2},
      {"skill": "Agile", "weight": 1},
    ],
    "admin@demo.com",
  )

  print("Seeding completed.")


if __name__ == "__main__":
  main()


