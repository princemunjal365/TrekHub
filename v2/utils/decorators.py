from functools import wraps
from flask import request, redirect, url_for, flash, jsonify, make_response, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, unset_jwt_cookies
from models import User


def _role_dashboard(role):
    return {
        "admin": "admin.dashboard",
        "staff": "staff.dashboard",
        "user": "user.dashboard",
    }.get(role, "index")


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            identity = get_jwt_identity()
            is_api = request.path.startswith("/api/")

            user = User.query.get(int(identity)) if identity and str(identity).isdigit() else None
            if not user:
                if is_api:
                    return jsonify({"error": "User not found"}), 401
                response = make_response(redirect(url_for("auth.login")))
                unset_jwt_cookies(response)
                flash("Session expired. Please log in again.", "warning")
                return response

            if user.is_blacklisted:
                if is_api:
                    return jsonify({"error": "Account is blacklisted"}), 403
                response = make_response(redirect(url_for("auth.login")))
                unset_jwt_cookies(response)
                flash("Your account has been blacklisted.", "danger")
                return response

            if user.role == "staff" and not user.is_approved:
                if is_api:
                    return jsonify({"error": "Staff account is pending Admin approval"}), 403
                response = make_response(redirect(url_for("auth.login")))
                unset_jwt_cookies(response)
                flash("Your staff account is pending Admin approval.", "warning")
                return response

            if roles and user.role not in roles:
                if is_api:
                    return jsonify({"error": "Access denied for your role"}), 403
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for(_role_dashboard(user.role)))

            g.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator