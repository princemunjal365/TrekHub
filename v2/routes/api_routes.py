from flask import Blueprint
from controllers import api_controller
from utils.decorators import role_required

api_bp = Blueprint("api", __name__)


@api_bp.route("/login", methods=["POST"])
def api_login():
    return api_controller.api_login()


@api_bp.route("/treks", methods=["GET"])
def get_treks():
    return api_controller.get_treks()


@api_bp.route("/treks/<int:trek_id>", methods=["GET"])
def get_trek(trek_id):
    return api_controller.get_trek(trek_id)


@api_bp.route("/treks", methods=["POST"])
@role_required("admin")
def create_trek():
    return api_controller.create_trek()


@api_bp.route("/treks/<int:trek_id>", methods=["PUT", "PATCH"])
@role_required("admin", "staff")
def update_trek(trek_id):
    return api_controller.update_trek(trek_id)


@api_bp.route("/treks/<int:trek_id>", methods=["DELETE"])
@role_required("admin")
def delete_trek(trek_id):
    return api_controller.delete_trek(trek_id)


@api_bp.route("/users", methods=["GET"])
@role_required("admin")
def get_users():
    return api_controller.get_users()


@api_bp.route("/users/<int:user_id>", methods=["GET"])
@role_required("admin", "staff", "user")
def get_user(user_id):
    return api_controller.get_user(user_id)


@api_bp.route("/bookings", methods=["GET"])
@role_required("admin", "staff", "user")
def get_bookings():
    return api_controller.get_bookings()


@api_bp.route("/bookings", methods=["POST"])
@role_required("user")
def create_booking():
    return api_controller.create_booking()


@api_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST", "DELETE"])
@role_required("user", "admin")
def cancel_booking(booking_id):
    return api_controller.cancel_booking(booking_id)


@api_bp.route("/treks/<int:trek_id>/locations", methods=["GET"])
@role_required("admin", "staff", "user")
def get_trek_locations(trek_id):
    return api_controller.get_trek_locations(trek_id)


@api_bp.route("/treks/<int:trek_id>/reviews", methods=["GET"])
def get_trek_reviews(trek_id):
    return api_controller.get_trek_reviews(trek_id)


@api_bp.route("/stats", methods=["GET"])
@role_required("admin")
def get_stats():
    return api_controller.get_stats()