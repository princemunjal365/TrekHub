from datetime import date, datetime
from flask import render_template, request, redirect, url_for, flash, g
from models import db, Trek, Booking

ALLOWED_TREK_STATUSES = ["Open", "Closed", "Started", "Completed"]
BOOKING_STATUSES = ["Booked", "Completed", "Cancelled"]


def _as_date(value):
    return value.date() if isinstance(value, datetime) else value


def _valid_statuses_for_trek(trek):
    if trek.status == "Completed":
        return ["Completed"]

    today = date.today()
    start = _as_date(trek.start_date)
    end = _as_date(trek.end_date)

    if today < start:
        return ["Open", "Closed"]
    if today < end:
        return ["Closed", "Started"]
    if today == end:
        return ["Closed", "Started", "Completed"]
    return ["Closed", "Completed"]


def _validate_status_by_date(trek, new_status):
    if trek.status == "Completed":
        return "This trek is already completed and its status cannot be changed."

    today = date.today()
    start = _as_date(trek.start_date)
    end = _as_date(trek.end_date)

    if new_status == "Open" and today >= start:
        return f"Cannot set trek to Open on or after its start date ({start.strftime('%d %b %Y')})."
    if new_status == "Started" and today < start:
        return f"Cannot mark trek as Started before its start date ({start.strftime('%d %b %Y')})."
    if new_status == "Started" and today > end:
        return f"Cannot mark trek as Started after its end date ({end.strftime('%d %b %Y')})."
    if new_status == "Completed" and today < end:
        return f"Cannot mark trek as Completed before its end date ({end.strftime('%d %b %Y')})."
    return None


def _build_trek_stats(treks):
    stats = []
    for trek in treks:
        registered_count = sum(
            b.slots_booked for b in trek.bookings if b.status != "Cancelled"
        )
        is_completed = trek.status == "Completed"
        valid_statuses = _valid_statuses_for_trek(trek)
        stats.append(
            {
                "trek": trek,
                "registered_count": registered_count,
                "is_completed": is_completed,
                "valid_statuses": valid_statuses,
                "can_start": not is_completed and "Started" in valid_statuses and trek.status != "Started",
                "can_complete": not is_completed and "Completed" in valid_statuses,
            }
        )
    return stats


def _mark_bookings_completed(trek):
    for booking in trek.bookings:
        if booking.status == "Booked":
            booking.status = "Completed"


def dashboard():
    staff = g.current_user
    treks = (
        Trek.query.filter_by(assigned_staff_id=staff.id)
        .filter(Trek.status != "Completed")
        .order_by(Trek.start_date.asc())
        .all()
    )
    trek_stats = _build_trek_stats(treks)
    total_participants = sum(item["registered_count"] for item in trek_stats)

    return render_template(
        "staff/dashboard.html",
        staff=staff,
        total_treks=len(treks),
        total_participants=total_participants,
        trek_stats=trek_stats,
    )


def assigned_treks():
    staff = g.current_user
    status_filter = request.args.get("status", "").strip()

    query = Trek.query.filter_by(assigned_staff_id=staff.id)
    if status_filter in ALLOWED_TREK_STATUSES:
        query = query.filter_by(status=status_filter)

    treks = query.order_by(Trek.start_date.asc()).all()
    trek_stats = _build_trek_stats(treks)

    return render_template(
        "staff/assigned_treks.html",
        trek_stats=trek_stats,
        status_filter=status_filter,
        allowed_statuses=ALLOWED_TREK_STATUSES,
    )


def update_trek(trek_id):
    staff = g.current_user
    trek = Trek.query.filter_by(id=trek_id, assigned_staff_id=staff.id).first()
    if not trek:
        flash("Trek not found or not assigned to you.", "danger")
        return redirect(url_for("staff.assigned_treks"))

    if trek.status == "Completed":
        flash("This trek is already completed and can no longer be modified.", "warning")
        return redirect(url_for("staff.assigned_treks"))

    raw_slots = request.form.get("available_slots", "").strip()
    new_status = request.form.get("status", "").strip()

    try:
        available_slots = int(raw_slots)
    except ValueError:
        flash("Available slots must be a valid number.", "danger")
        return redirect(url_for("staff.assigned_treks"))

    if available_slots < 0 or available_slots > trek.total_slots:
        flash(f"Available slots must be between 0 and {trek.total_slots}.", "danger")
        return redirect(url_for("staff.assigned_treks"))

    if new_status not in ALLOWED_TREK_STATUSES:
        flash("Invalid trek status selected.", "danger")
        return redirect(url_for("staff.assigned_treks"))

    date_error = _validate_status_by_date(trek, new_status)
    if date_error:
        flash(date_error, "warning")
        return redirect(url_for("staff.assigned_treks"))

    trek.available_slots = available_slots
    trek.status = new_status
    if new_status == "Completed":
        _mark_bookings_completed(trek)

    db.session.commit()
    flash(f"Updated '{trek.name}' successfully.", "success")
    return redirect(url_for("staff.assigned_treks"))


def mark_trek_status(trek_id):
    staff = g.current_user
    trek = Trek.query.filter_by(id=trek_id, assigned_staff_id=staff.id).first()
    if not trek:
        flash("Trek not found or not assigned to you.", "danger")
        return redirect(url_for("staff.assigned_treks"))

    if trek.status == "Completed":
        flash("This trek is already completed and its status cannot be changed.", "warning")
        return redirect(request.referrer or url_for("staff.assigned_treks"))

    new_status = request.form.get("status", "").strip()
    if new_status not in ALLOWED_TREK_STATUSES:
        flash("Invalid status requested.", "danger")
        return redirect(url_for("staff.assigned_treks"))

    date_error = _validate_status_by_date(trek, new_status)
    if date_error:
        flash(date_error, "warning")
        return redirect(request.referrer or url_for("staff.assigned_treks"))

    trek.status = new_status
    if new_status == "Completed":
        _mark_bookings_completed(trek)

    db.session.commit()
    flash(f"'{trek.name}' marked as {new_status}.", "success")
    return redirect(request.referrer or url_for("staff.assigned_treks"))


def participants(trek_id):
    staff = g.current_user
    trek = Trek.query.filter_by(id=trek_id, assigned_staff_id=staff.id).first()
    if not trek:
        flash("Trek not found or not assigned to you.", "danger")
        return redirect(url_for("staff.assigned_treks"))

    bookings = (
        Booking.query.filter_by(trek_id=trek.id)
        .order_by(Booking.booking_date.desc())
        .all()
    )

    return render_template(
        "staff/participants.html",
        trek=trek,
        bookings=bookings,
        booking_statuses=BOOKING_STATUSES,
    )


def update_booking_status(trek_id, booking_id):
    staff = g.current_user
    trek = Trek.query.filter_by(id=trek_id, assigned_staff_id=staff.id).first()
    if not trek:
        flash("Trek not found or not assigned to you.", "danger")
        return redirect(url_for("staff.assigned_treks"))

    booking = Booking.query.filter_by(id=booking_id, trek_id=trek.id).first()
    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for("staff.participants", trek_id=trek.id))

    new_status = request.form.get("status", "").strip()
    if new_status not in BOOKING_STATUSES:
        flash("Invalid booking status.", "danger")
        return redirect(url_for("staff.participants", trek_id=trek.id))

    old_status = booking.status
    if old_status != "Cancelled" and new_status == "Cancelled":
        trek.available_slots = min(trek.total_slots, trek.available_slots + booking.slots_booked)
    elif old_status == "Cancelled" and new_status != "Cancelled":
        if trek.available_slots < booking.slots_booked:
            flash("Not enough available slots to restore this booking.", "danger")
            return redirect(url_for("staff.participants", trek_id=trek.id))
        trek.available_slots -= booking.slots_booked

    booking.status = new_status
    db.session.commit()
    flash(f"Booking #{booking.id} status updated to {new_status}.", "success")
    return redirect(url_for("staff.participants", trek_id=trek.id))