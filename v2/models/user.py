from datetime import datetime, timezone
from models import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    emergency_contact = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="user")
    experience = db.Column(db.String(200), nullable=True)
    is_approved = db.Column(db.Boolean, nullable=False, default=True)
    is_blacklisted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    assigned_treks = db.relationship("Trek", back_populates="assigned_staff", lazy=True)
    bookings = db.relationship("Booking", back_populates="user", lazy=True, cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="user", lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="user", lazy=True, cascade="all, delete-orphan")
    location_updates = db.relationship("LocationUpdate", back_populates="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "emergency_contact": self.emergency_contact,
            "role": self.role,
            "experience": self.experience,
            "is_approved": self.is_approved,
            "is_blacklisted": self.is_blacklisted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }