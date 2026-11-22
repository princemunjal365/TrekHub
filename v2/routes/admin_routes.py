from flask import Blueprint
from controllers import admin_controller
from utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard", methods=["GET"])
@role_required("admin")
def dashboard():
    return admin_controller.dashboard()


@admin_bp.route("/treks", methods=["GET"])
@role_required("admin")
def manage_treks():
    return admin_controller.manage_treks()


@admin_bp.route("/treks/create", methods=["GET", "POST"])
@role_required("admin")
def create_trek():
    return admin_controller.create_trek()


@admin_bp.route("/treks/<int:trek_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_trek(trek_id):
    return admin_controller.edit_trek(trek_id)


@admin_bp.route("/treks/<int:trek_id>/delete", methods=["POST"])
@role_required("admin")
def delete_trek(trek_id):
    return admin_controller.delete_trek(trek_id)


@admin_bp.route("/treks/<int:trek_id>/assign-staff", methods=["POST"])
@role_required("admin")
def assign_staff(trek_id):
    return admin_controller.assign_staff(trek_id)


@admin_bp.route("/staff", methods=["GET"])
@role_required("admin")
def manage_staff():
    return admin_controller.manage_staff()


@admin_bp.route("/staff/<int:staff_id>/approve", methods=["POST"])
@role_required("admin")
def approve_staff(staff_id):
    return admin_controller.approve_staff(staff_id)


@admin_bp.route("/staff/<int:staff_id>/toggle-blacklist", methods=["POST"])
@role_required("admin")
def toggle_blacklist_staff(staff_id):
    return admin_controller.toggle_blacklist_staff(staff_id)


@admin_bp.route("/users", methods=["GET"])
@role_required("admin")
def manage_users():
    return admin_controller.manage_users()


@admin_bp.route("/users/<int:user_id>/toggle-blacklist", methods=["POST"])
@role_required("admin")
def toggle_blacklist_user(user_id):
    return admin_controller.toggle_blacklist_user(user_id)


@admin_bp.route("/bookings", methods=["GET"])
@role_required("admin")
def all_bookings():
    return admin_controller.all_bookings()


@admin_bp.route("/feedback", methods=["GET"])
@role_required("admin")
def completed_feedback():
    return admin_controller.completed_feedback()