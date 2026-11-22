from flask import Blueprint
from controllers import user_controller
from utils.decorators import role_required

user_bp = Blueprint("user", __name__)


@user_bp.route("/dashboard", methods=["GET"])
@role_required("user")
def dashboard():
    return user_controller.dashboard()


@user_bp.route("/treks/<int:trek_id>", methods=["GET"])
@role_required("user")
def trek_detail(trek_id):
    return user_controller.trek_detail(trek_id)


@user_bp.route("/treks/<int:trek_id>/book", methods=["POST"])
@role_required("user")
def book_trek(trek_id):
    return user_controller.book_trek(trek_id)


@user_bp.route("/bookings", methods=["GET"])
@role_required("user")
def bookings():
    return user_controller.bookings()


@user_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@role_required("user")
def cancel_booking(booking_id):
    return user_controller.cancel_booking(booking_id)


@user_bp.route("/profile", methods=["GET", "POST"])
@role_required("user")
def profile():
    return user_controller.profile()