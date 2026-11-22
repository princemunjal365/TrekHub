from datetime import datetime, timezone
from models import db


class LocationUpdate(db.Model):
    __tablename__ = "location_updates"

    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    checkpoint_name = db.Column(db.String(150), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    trek = db.relationship("Trek", back_populates="locations")
    user = db.relationship("User", back_populates="location_updates")

    def to_dict(self):
        return {
            "id": self.id,
            "trek_id": self.trek_id,
            "user_id": self.user_id,
            "updated_by": self.user.name if self.user else None,
            "role": self.user.role if self.user else None,
            "checkpoint_name": self.checkpoint_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "note": self.note,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }