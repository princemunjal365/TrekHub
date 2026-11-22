from datetime import datetime, timezone
from models import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(30), nullable=False, default="UPI")
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    paid_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    booking = db.relationship("Booking", back_populates="payment")
    user = db.relationship("User", back_populates="payments")

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "transaction_id": self.transaction_id,
            "status": self.status,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }