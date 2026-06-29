from functools import wraps

import os
from flask import Flask, redirect, render_template, request, session

from config import FLASK_SECRET_KEY


def login_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if "user_id" not in session:
      return redirect("/login")
    return f(*args, **kwargs)

  return decorated


def create_app() -> Flask:
  app = Flask(__name__, static_folder="static", template_folder="templates")
  app.secret_key = FLASK_SECRET_KEY

  # Register blueprints
  from routes.auth import auth_bp
  from routes.jobs import jobs_bp
  from routes.candidates import candidates_bp
  from routes.ai_routes import ai_bp
  from routes.analytics import analytics_bp
  from routes.dashboard_recruiter_routes import dashboard_rec_bp
  from routes.candidate_analytics_routes import candidate_analytics_bp

  app.register_blueprint(auth_bp)
  app.register_blueprint(jobs_bp, url_prefix="/jobs")
  app.register_blueprint(candidates_bp, url_prefix="/candidates")
  app.register_blueprint(ai_bp, url_prefix="/ai")
  app.register_blueprint(analytics_bp, url_prefix="/analytics")
  app.register_blueprint(dashboard_rec_bp)
  app.register_blueprint(candidate_analytics_bp)

  @app.route("/")
  def index():
    if "user_id" in session:
      # Send logged-in users to the main reports dashboard.
      return redirect("/dashboard")
    return redirect("/landing")

  @app.route("/landing")
  def landing():
    if "user_id" in session:
      return redirect("/dashboard/recruiter")
    return render_template("landing.html")

  @app.route("/dashboard")
  @login_required
  def dashboard():
    from routes.analytics import collect_analytics_data
    data = collect_analytics_data()
    # Show the reports/analytics view directly on the main dashboard.
    return render_template("analytics.html", analytics=data)

  @app.route("/dashboard/recruiter")
  @login_required
  def dashboard_recruiter():
    # Keep this route working but just forward to the main dashboard view.
    return redirect("/dashboard")

  @app.route("/pipeline")
  @login_required
  def pipeline():
    if session.get("role", "recruiter") not in ("recruiter", "admin"):
      return redirect("/dashboard")
    from services.supabase_client import supabase

    selected_job_id = (request.args.get("job_id") or "").strip() or None

    try:
      # Keep payload small: pipeline doesn't need full resume_text.
      q = supabase.table("candidates").select("id, job_role_id, full_name, status, ai_score, parsed_data, upload_date")
      if selected_job_id:
        q = q.eq("job_role_id", selected_job_id)
      res = q.execute()
      candidates = res.data or []
    except Exception:
      candidates = []

    # Job roles for the dropdown filter
    job_roles = []
    try:
      jr_q = supabase.table("job_roles").select("id, title, location, created_by, created_at").order("created_at", desc=True)
      if session.get("role", "recruiter") != "admin":
        jr_q = jr_q.eq("created_by", session.get("user_id"))
      job_roles = jr_q.execute().data or []
    except Exception:
      job_roles = []

    job_ids = list({c.get("job_role_id") for c in candidates if c.get("job_role_id")})
    jobs_map = {}
    if job_ids:
      try:
        jr = supabase.table("job_roles").select("*").in_("id", job_ids).execute()
        jobs_map = {j["id"]: j for j in jr.data or []}
      except Exception:
        pass
    for c in candidates:
      c["job"] = jobs_map.get(c.get("job_role_id"))
    return render_template(
      "pipeline.html",
      candidates=candidates,
      job_roles=job_roles,
      selected_job_id=selected_job_id or "",
    )

  return app


if __name__ == "__main__":
  app = create_app()
  # Avoid port conflicts on Windows and allow easy override.
  port = int(os.getenv("PORT", "5001"))
  debug = os.getenv("FLASK_DEBUG", "0") == "1"
  app.run(debug=debug, port=port)

