"""Recruiter dashboard API."""
from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from services.dashboard_recruiter import get_selections, get_stats, make_selection

dashboard_rec_bp = Blueprint("dashboard_recruiter", __name__, url_prefix="/api/dashboard/recruiter")


def _require_recruiter():
  if "user_id" not in session:
    return None
  role = session.get("role", "recruiter")
  if role not in ("recruiter", "admin"):
    return None
  return session["user_id"]


@dashboard_rec_bp.route("/stats", methods=["GET"])
def stats():
  user_id = _require_recruiter()
  if not user_id:
    return jsonify({"error": "Unauthorized"}), 401
  data = get_stats(user_id)
  # Never 404 here; an empty dashboard is worse UX than showing 0s.
  if data is None:
    data = {
      "candidates_viewed": 0,
      "selections_made": 0,
      "accepted": 0,
      "pending": 0,
      "acceptance_rate": "0%",
    }
  return jsonify({"status": "success", "data": data}), 200


@dashboard_rec_bp.route("/selections", methods=["GET"])
def selections():
  user_id = _require_recruiter()
  if not user_id:
    return jsonify({"error": "Unauthorized"}), 401
  status_filter = request.args.get("status", "all")
  data = get_selections(user_id, status_filter)
  return jsonify({"status": "success", "data": data, "count": len(data)}), 200


@dashboard_rec_bp.route("/make-selection", methods=["POST"])
def make_selection_route():
  user_id = _require_recruiter()
  if not user_id:
    return jsonify({"error": "Unauthorized"}), 401
  body = request.get_json() or {}
  candidate_id = body.get("candidate_id")
  job_role_id = body.get("job_role_id")
  notes = body.get("notes")
  if not candidate_id:
    return jsonify({"error": "candidate_id required"}), 400
  data, code = make_selection(user_id, candidate_id, job_role_id=job_role_id, notes=notes)
  return jsonify(data), code
