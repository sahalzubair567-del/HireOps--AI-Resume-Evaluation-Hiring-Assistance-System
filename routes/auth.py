from __future__ import annotations

import bcrypt
from flask import Blueprint, flash, redirect, render_template, request, session

from services.supabase_client import supabase


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "GET":
    return render_template("login.html")

  email = (request.form.get("email") or "").strip().lower()
  password = (request.form.get("password") or "").encode("utf-8")

  if not email or not password:
    flash("Email and password are required.", "error")
    return render_template("login.html")

  try:
    result = supabase.table("users").select("*").eq("email", email).execute()
    users = result.data or []
    user = users[0] if users else None
  except Exception:
    user = None

  if not user:
    flash("Invalid credentials", "error")
    return render_template("login.html")

  stored_hash = (user.get("password_hash") or "").encode("utf-8")
  if not stored_hash or not bcrypt.checkpw(password, stored_hash):
    flash("Invalid credentials", "error")
    return render_template("login.html")

  session["user_id"] = user["id"]
  session["full_name"] = user.get("full_name", "")
  session["role"] = user.get("role", "recruiter")

  # Recruiter-only app: send user to recruiter home
  return redirect("/dashboard/recruiter")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
  # Back-compat: keep /signup URL, but recruiter-only.
  if request.method == "GET":
    return render_template("register.html")

  email = (request.form.get("email") or "").strip().lower()
  password = (request.form.get("password") or "").encode("utf-8")
  full_name = (request.form.get("full_name") or "").strip()

  if not email or not password or not full_name:
    flash("Email, password, and name are required.", "error")
    return render_template("register.html")

  password_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")

  try:
    existing = supabase.table("users").select("id").eq("email", email).execute()
    if existing.data and len(existing.data) > 0:
      flash("This email is already registered. Please sign in.", "error")
      return render_template("register.html")
  except Exception:
    pass

  try:
    insert_user = {
      "full_name": full_name,
      "email": email,
      "password_hash": password_hash,
      "role": "recruiter",
    }
    result = supabase.table("users").insert(insert_user).execute()
    if not result.data or len(result.data) == 0:
      raise ValueError("No user returned")
    user_row = result.data[0]
    user_id = user_row["id"]
  except Exception as e:
    flash("Could not create account. Please try again.", "error")
    return render_template("register.html")

  session["user_id"] = user_id
  session["full_name"] = full_name
  session["role"] = "recruiter"
  flash("Account created. Welcome!", "success")
  return redirect("/dashboard/recruiter")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
  # Canonical recruiter signup URL
  if request.method == "GET":
    return render_template("register.html")

  # Reuse /signup POST logic
  return signup()


@auth_bp.route("/logout")
def logout():
  session.clear()
  return redirect("/login")

