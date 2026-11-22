from flask import render_template, request, redirect, url_for, flash, g
from sqlalchemy import or_
from models import db, Trek, Booking, Review


def _is_valid_mobile(number):
    return number.isdigit() and len(number) == 10


def dashboard():
    user = g.current_user
    query = request.args.get("q", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    location = request.args.get("location", "").strip()

    trek_query = Trek.query.filter(Trek.status.in_(["Open", "Started"]))

    if query:
        trek_query = trek_query.filter(
            or_(
                Trek.name.ilike(f"%{query}%"),
                Trek.location.ilike(f"%{query}%"),
                Trek.description.ilike(f"%{query}%"),
            )
        )

    if difficulty in ("Easy", "Moderate", "Hard"):
        trek_query = trek_query.filter_by(difficulty=difficulty)

    if location:
        trek_query = trek_query.filter(Trek.location.ilike(f"%{location}%"))

    available_treks = trek_query.order_by(Trek.start_date.asc()).all()

    all_locations = (
        db.session.query(Trek.location)
        .filter(Trek.status.in_(["Open", "Started"]))
        .distinct()
        .order_by(Trek.location.asc())
        .all()
    )
    locations = [row[0] for row in all_locations if row[0]]

    user_bookings = (
        Booking.query.join(Trek, Booking.trek_id == Trek.id)
        .filter(Booking.user_id == user.id, Trek.status != "Completed")
        .order_by(Booking.booking_date.desc())
        .all()
    )

    return render_template(
        "user/dashboard.html",
        user=user,
        available_treks=available_treks,
        user_bookings=user_bookings,
        query=query,
        selected_difficulty=difficulty,
        selected_location=location,
        difficulties=["Easy", "Moderate", "Hard"],
        locations=locations,
    )


def trek_detail(trek_id):
    user = g.current_user
    trek = Trek.query.get(trek_id)
    if not trek:
        flash("Trek not found.", "danger")
        return redirect(url_for("user.dashboard"))

    existing_booking = (
        Booking.query.filter_by(user_id=user.id, trek_id=trek.id)
        .filter(Booking.status != "Cancelled")
        .order_by(Booking.id.desc())
        .first()
    )

    can_view_all_feedback = user.role == "admin" or (
        user.role == "staff" and trek.assigned_staff_id == user.id
    )

    if can_view_all_feedback:
        reviews = (
            Review.query.filter_by(trek_id=trek.id)
            .order_by(Review.created_at.desc())
            .all()
        )
    else:
        reviews = []

    existing_review = Review.query.filter_by(user_id=user.id, trek_id=trek.id).first()

    avg_rating = None
    if can_view_all_feedback and reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)

    return render_template(
        "user/trek_detail.html",
        user=user,
        trek=trek,
        existing_booking=existing_booking,
        can_view_all_feedback=can_view_all_feedback,
        reviews=reviews,
        existing_review=existing_review,
        avg_rating=avg_rating,
    )


def book_trek(trek_id):
    user = g.current_user
    trek = Trek.query.get(trek_id)
    if not trek:
        flash("Trek not found.", "danger")
        return redirect(url_for("user.dashboard"))

    if trek.status != "Open":
        flash(f"Cannot book this trek because its status is '{trek.status}'.", "warning")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    raw_slots = request.form.get("slots_booked", "1").strip()
    try:
        slots_booked = int(raw_slots)
    except ValueError:
        flash("Slots must be a valid number.", "danger")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    if slots_booked < 1:
        flash("Please book at least 1 slot.", "danger")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    if slots_booked > trek.available_slots:
        flash(f"Only {trek.available_slots} slot(s) available for this trek.", "warning")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    active_booking = (
        Booking.query.filter_by(user_id=user.id, trek_id=trek.id)
        .filter(Booking.status != "Cancelled")
        .first()
    )
    if active_booking:
        flash("You already have an active booking for this trek.", "info")
        return redirect(url_for("user.bookings"))

    return redirect(url_for("payment.checkout", trek_id=trek.id, slots=slots_booked))


def bookings():
    user = g.current_user
    status_filter = request.args.get("status", "").strip()

    booking_query = Booking.query.filter_by(user_id=user.id)
    if status_filter in ("Booked", "Completed", "Cancelled"):
        booking_query = booking_query.filter_by(status=status_filter)

    user_bookings = booking_query.order_by(Booking.booking_date.desc()).all()
    reviewed_trek_ids = {
        r.trek_id for r in Review.query.filter_by(user_id=user.id).all()
    }

    return render_template(
        "user/bookings.html",
        user=user,
        bookings=user_bookings,
        status_filter=status_filter,
        reviewed_trek_ids=reviewed_trek_ids,
    )


def cancel_booking(booking_id):
    user = g.current_user
    booking = Booking.query.filter_by(id=booking_id, user_id=user.id).first()
    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for("user.bookings"))

    if booking.status == "Cancelled":
        flash("This booking is already cancelled.", "info")
        return redirect(url_for("user.bookings"))

    if booking.status == "Completed" or booking.trek.status in ("Started", "Completed"):
        flash("Cannot cancel a booking once the trek has started or completed.", "warning")
        return redirect(url_for("user.bookings"))

    trek = booking.trek
    trek.available_slots = min(trek.total_slots, trek.available_slots + booking.slots_booked)
    booking.status = "Cancelled"

    if booking.payment and booking.payment.status == "Paid":
        booking.payment.status = "Refunded"

    db.session.commit()
    flash(f"Booking #{booking.id} cancelled and {booking.slots_booked} slot(s) released.", "info")
    return redirect(url_for("user.bookings"))


def profile():
    user = g.current_user

    if request.method == "GET":
        return render_template("user/profile.html", user=user)

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    emergency_contact = request.form.get("emergency_contact", "").strip()
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")

    if not name:
        flash("Full name cannot be empty.", "danger")
        return redirect(url_for("user.profile"))

    if phone and not _is_valid_mobile(phone):
        flash("Phone number must be a valid 10-digit number.", "danger")
        return redirect(url_for("user.profile"))

    if emergency_contact and not _is_valid_mobile(emergency_contact):
        flash("Emergency contact must be a valid 10-digit number.", "danger")
        return redirect(url_for("user.profile"))

    user.name = name
    user.phone = phone or None
    user.emergency_contact = emergency_contact or None

    if new_password:
        if not current_password or not user.check_password(current_password):
            flash("Enter your valid current password to set a new password.", "danger")
            return redirect(url_for("user.profile"))
        if len(new_password) < 6:
            flash("New password must be at least 6 characters long.", "danger")
            return redirect(url_for("user.profile"))
        user.set_password(new_password)

    db.session.commit()
    flash("Profile updated successfully.", "success")
    return redirect(url_for("user.profile"))