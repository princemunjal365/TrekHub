from flask import current_app
from models import db, User


def seed_admin():
    admin_email = current_app.config["ADMIN_EMAIL"].strip().lower()
    existing_admin = User.query.filter_by(role="admin").first()

    if existing_admin:
        return existing_admin

    admin = User(
        name=current_app.config["ADMIN_NAME"],
        email=admin_email,
        role="admin",
        is_approved=True,
        is_blacklisted=False,
    )
    admin.set_password(current_app.config["ADMIN_PASSWORD"])

    db.session.add(admin)
    db.session.commit()
    return admin