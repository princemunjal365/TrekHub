from flask import Blueprint
from controllers import location_controller
from utils.decorators import role_required

location_bp = Blueprint("location", __name__)


@location_bp.route("/trek/<int:trek_id>", methods=["GET"])
@role_required("admin", "staff", "user")
def view_location(trek_id):
    return location_controller.view_location(trek_id)


@location_bp.route("/trek/<int:trek_id>/update", methods=["POST"])
@role_required("admin", "staff", "user")
def update_location(trek_id):
    return location_controller.update_location(trek_id)


@location_bp.route("/<int:location_id>/delete", methods=["POST"])
@role_required("admin", "staff", "user")
def delete_location(location_id):
    return location_controller.delete_location(location_id)