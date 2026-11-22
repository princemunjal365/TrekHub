from flask import render_template, request, redirect, url_for, flash, make_response
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from models import db, User


def _dashboard_for_role(role):
    return {
        "admin": "admin.dashboard",
        "staff": "staff.dashboard",
        "user": "user.dashboard",
    }.get(role, "index")


def _is_valid_mobile(number):
    return number.isdigit() and len(number) == 10


def register():
    if request.method == "GET":
        return render_template("auth/register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role", "user").strip().lower()
    phone = request.form.get("phone", "").strip()
    emergency_contact = request.form.get("emergency_contact", "").strip()
    experience = request.form.get("experience", "").strip()

    if not name or not email or not password:
        flash("Name, email, and password are required.", "danger")
        return redirect(url_for("auth.register"))

    if len(password) < 6:
        flash("Password must be at least 6 characters long.", "danger")
        return redirect(url_for("auth.register"))

    if role not in ("user", "staff"):
        flash("Invalid account role selected.", "danger")
        return redirect(url_for("auth.register"))

    if not _is_valid_mobile(phone):
        flash("Phone number must be a valid 10-digit number.", "danger")
        return redirect(url_for("auth.register"))

    if emergency_contact and not _is_valid_mobile(emergency_contact):
        flash("Emergency contact must be a valid 10-digit number.", "danger")
        return redirect(url_for("auth.register"))

    if User.query.filter_by(email=email).first():
        flash("An account with this email already exists.", "warning")
        return redirect(url_for("auth.register"))

    user = User(
        name=name,
        email=email,
        role=role,
        phone=phone,
        emergency_contact=emergency_contact or None,
        experience=experience if role == "staff" and experience else None,
        is_approved=(role == "user"),
        is_blacklisted=False,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    if role == "staff":
        flash("Staff account registered! Please wait for Admin approval before logging in.", "info")
    else:
        flash("Account created successfully! You can now log in.", "success")

    return redirect(url_for("auth.login"))


def login():
    if request.method == "GET":
        return render_template("auth/login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Email and password are required.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash("Invalid email or password.", "danger")
        return redirect(url_for("auth.login"))

    if user.is_blacklisted:
        flash("Your account has been blacklisted by Admin.", "danger")
        return redirect(url_for("auth.login"))

    if user.role == "staff" and not user.is_approved:
        flash("Your staff account is still pending Admin approval.", "warning")
        return redirect(url_for("auth.login"))

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )

    response = make_response(redirect(url_for(_dashboard_for_role(user.role))))
    set_access_cookies(response, access_token)
    flash(f"Welcome back, {user.name}!", "success")
    return response


def logout():
    response = make_response(redirect(url_for("auth.login")))
    unset_jwt_cookies(response)
    flash("You have been logged out.", "info")
    return response