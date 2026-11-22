from flask import Blueprint
from controllers import payment_controller
from utils.decorators import role_required

payment_bp = Blueprint("payment", __name__, url_prefix="/payment")


@payment_bp.route("/checkout", methods=["GET", "POST"])
@payment_bp.route("/checkout/<int:booking_id>", methods=["GET", "POST"])
@role_required("user", "admin")
def checkout(booking_id=None):
    return payment_controller.checkout()


@payment_bp.route("/verify", methods=["GET", "POST"])
@role_required("user", "admin")
def verify():
    return payment_controller.verify_payment()


@payment_bp.route("/receipt/<int:booking_id>", methods=["GET"])
@role_required("user", "admin")
def receipt(booking_id):
    return payment_controller.receipt(booking_id)