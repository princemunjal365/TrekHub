from flask import render_template, request, redirect, url_for, flash
from flask_jwt_extended import get_jwt_identity
from models import db, User, Trek, Booking, LocationUpdate


def _get_current_user():
    return User.query.get_or_404(int(get_jwt_identity()))


def _role_dashboard(role):
    return {
        "admin": "admin.dashboard",
        "staff": "staff.dashboard",
        "user": "user.dashboard",
    }.get(role, "index")


def _has_trek_access(user, trek):
    if user.role == "admin":
        return True
    if user.role == "staff":
        return trek.assigned_staff_id == user.id
    if user.role == "user":
        booking = Booking.query.filter(
            Booking.user_id == user.id,
            Booking.trek_id == trek.id,
            Booking.status != "Cancelled",
        ).first()
        return booking is not None
    return False


def view_location(trek_id):
    user = _get_current_user()
    trek = Trek.query.get_or_404(trek_id)

    if not _has_trek_access(user, trek):
        flash("You do not have access to live location updates for this trek.", "danger")
        return redirect(url_for(_role_dashboard(user.role)))

    updates = (
        LocationUpdate.query.filter_by(trek_id=trek.id)
        .order_by(LocationUpdate.updated_at.desc())
        .all()
    )

    latest_staff_location = next(
        (u for u in updates if u.user and u.user.role == "staff"),
        None,
    )
    trekker_updates = [u for u in updates if u.user and u.user.role == "user"]

    template_name = "staff/update_location.html" if user.role == "staff" else "user/live_location.html"

    return render_template(
        template_name,
        user=user,
        trek=trek,
        updates=updates,
        latest_staff_location=latest_staff_location,
        trekker_updates=trekker_updates,
    )


def update_location(trek_id):
    user = _get_current_user()
    trek = Trek.query.get_or_404(trek_id)

    if not _has_trek_access(user, trek):
        flash("You are not authorised to post location updates for this trek.", "danger")
        return redirect(url_for(_role_dashboard(user.role)))

    checkpoint_name = request.form.get("checkpoint_name", "").strip()
    latitude_raw = request.form.get("latitude", "").strip()
    longitude_raw = request.form.get("longitude", "").strip()
    note = request.form.get("note", "").strip()

    if not checkpoint_name:
        flash("Checkpoint name is required.", "danger")
        return redirect(url_for("location.view_location", trek_id=trek.id))

    try:
        latitude = float(latitude_raw)
        longitude = float(longitude_raw)
    except ValueError:
        flash("Latitude and longitude must be valid numbers.", "danger")
        return redirect(url_for("location.view_location", trek_id=trek.id))

    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        flash("Coordinates out of valid range (lat: -90 to 90, lng: -180 to 180).", "danger")
        return redirect(url_for("location.view_location", trek_id=trek.id))

    entry = LocationUpdate(
        trek_id=trek.id,
        user_id=user.id,
        checkpoint_name=checkpoint_name,
        latitude=latitude,
        longitude=longitude,
        note=note or None,
    )

    db.session.add(entry)
    db.session.commit()
    flash("Location checkpoint updated successfully.", "success")
    return redirect(url_for("location.view_location", trek_id=trek.id))


def delete_location(location_id):
    user = _get_current_user()
    entry = LocationUpdate.query.get_or_404(location_id)
    trek = entry.trek

    is_allowed = (
        user.role == "admin"
        or entry.user_id == user.id
        or (user.role == "staff" and trek.assigned_staff_id == user.id)
    )
    if not is_allowed:
        flash("You are not authorised to remove this location update.", "danger")
        return redirect(url_for("location.view_location", trek_id=trek.id))

    db.session.delete(entry)
    db.session.commit()
    flash("Location update removed.", "info")
    return redirect(url_for("location.view_location", trek_id=trek.id))