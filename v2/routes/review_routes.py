from flask import Blueprint
from controllers import review_controller
from utils.decorators import role_required

review_bp = Blueprint("review", __name__)


@review_bp.route("/trek/<int:trek_id>", methods=["GET", "POST"])
@role_required("user")
def add_review(trek_id):
    return review_controller.add_review(trek_id)


@review_bp.route("/<int:review_id>/delete", methods=["POST"])
@role_required("user", "admin")
def delete_review(review_id):
    return review_controller.delete_review(review_id)