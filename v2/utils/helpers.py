from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import User


def get_logged_in_user():
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity and str(identity).isdigit():
            user = User.query.get(int(identity))
            if user and not user.is_blacklisted:
                return user
    except Exception:
        return None
    return None


def format_inr(amount):
    try:
        value = float(amount)
    except (ValueError, TypeError):
        return "₹0.00"
    return f"₹{value:,.2f}"


def status_badge_class(status):
    mapping = {
        "Open": "bg-success",
        "Approved": "bg-info text-dark",
        "Pending": "bg-warning text-dark",
        "Started": "bg-primary",
        "Closed": "bg-secondary",
        "Completed": "bg-dark",
        "Booked": "bg-success",
        "Cancelled": "bg-danger",
        "Paid": "bg-success",
        "Refunded": "bg-secondary",
    }
    return mapping.get(status, "bg-secondary")


def difficulty_badge_class(difficulty):
    mapping = {
        "Easy": "bg-success",
        "Moderate": "bg-warning text-dark",
        "Hard": "bg-danger",
    }
    return mapping.get(difficulty, "bg-secondary")