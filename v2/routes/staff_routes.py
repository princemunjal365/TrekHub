from flask import Blueprint
from controllers import staff_controller
from utils.decorators import role_required

staff_bp = Blueprint("staff", __name__)


@staff_bp.route("/dashboard", methods=["GET"])
@role_required("staff")
def dashboard():
    return staff_controller.dashboard()


@staff_bp.route("/treks", methods=["GET"])
@role_required("staff")
def assigned_treks():
    return staff_controller.assigned_treks()


@staff_bp.route("/treks/<int:trek_id>/update", methods=["POST"])
@role_required("staff")
def update_trek(trek_id):
    return staff_controller.update_trek(trek_id)


@staff_bp.route("/treks/<int:trek_id>/status", methods=["POST"])
@role_required("staff")
def mark_trek_status(trek_id):
    return staff_controller.mark_trek_status(trek_id)


@staff_bp.route("/treks/<int:trek_id>/participants", methods=["GET"])
@role_required("staff")
def participants(trek_id):
    return staff_controller.participants(trek_id)


@staff_bp.route("/treks/<int:trek_id>/bookings/<int:booking_id>/status", methods=["POST"])
@role_required("staff")
def update_booking_status(trek_id, booking_id):
    return staff_controller.update_booking_status(trek_id, booking_id)