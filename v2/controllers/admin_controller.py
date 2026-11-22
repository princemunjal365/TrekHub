from datetime import date, datetime
from flask import render_template, request, redirect, url_for, flash
from sqlalchemy import func, or_
from models import db, User, Trek, Booking, Review

DIFFICULTIES = ["Easy", "Moderate", "Hard"]
TREK_STATUSES = ["Open", "Closed", "Started", "Completed"]


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _find_staff_clash(staff_id, start_date, end_date, exclude_trek_id=None):
    if not staff_id or not start_date or not end_date:
        return None

    start_d = _as_date(start_date)
    end_d = _as_date(end_date)

    candidates = Trek.query.filter(
        Trek.assigned_staff_id == int(staff_id),
        Trek.status != "Completed",
    ).all()

    for other in candidates:
        if exclude_trek_id is not None and other.id == exclude_trek_id:
            continue
        other_start = _as_date(other.start_date)
        other_end = _as_date(other.end_date)
        if start_d <= other_end and end_d >= other_start:
            return other

    return None


def _get_clashing_trek_ids(treks):
    clashing_ids = set()
    active_assigned = [
        t for t in Trek.query.filter(
            Trek.assigned_staff_id.isnot(None),
            Trek.status != "Completed",
        ).all()
    ]

    for trek in treks:
        if not trek.assigned_staff_id or trek.status == "Completed":
            continue
        t_start = _as_date(trek.start_date)
        t_end = _as_date(trek.end_date)
        for other in active_assigned:
            if other.id == trek.id or other.assigned_staff_id != trek.assigned_staff_id:
                continue
            o_start = _as_date(other.start_date)
            o_end = _as_date(other.end_date)
            if t_start <= o_end and t_end >= o_start:
                clashing_ids.add(trek.id)
                break

    return clashing_ids


def dashboard():
    active_treks_filter = Trek.status != "Completed"

    status_counts = {
        status: Trek.query.filter_by(status=status).count()
        for status in TREK_STATUSES
    }
    completed_treks_count = status_counts.get("Completed", 0)
    total_treks = sum(status_counts.values())

    total_users = User.query.filter_by(role="user").count()
    total_staff = User.query.filter_by(role="staff").count()
    pending_staff_count = User.query.filter_by(role="staff", is_approved=False, is_blacklisted=False).count()
    total_bookings = (
        Booking.query.join(Trek, Booking.trek_id == Trek.id)
        .filter(active_treks_filter)
        .count()
    )

    popular_treks = (
        db.session.query(Trek.name, func.count(Booking.id))
        .outerjoin(Booking, Trek.id == Booking.trek_id)
        .filter(active_treks_filter)
        .group_by(Trek.id)
        .order_by(func.count(Booking.id).desc(), Trek.name.asc())
        .limit(5)
        .all()
    )

    recent_bookings = (
        Booking.query.join(Trek, Booking.trek_id == Trek.id)
        .filter(active_treks_filter)
        .order_by(Booking.booking_date.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        total_treks=total_treks,
        completed_treks_count=completed_treks_count,
        total_users=total_users,
        total_staff=total_staff,
        pending_staff_count=pending_staff_count,
        total_bookings=total_bookings,
        popular_treks=popular_treks,
        status_counts=status_counts,
        recent_bookings=recent_bookings,
    )


def manage_treks():
    query = request.args.get("q", "").strip()
    trek_query = Trek.query

    if query:
        if query.lstrip("#").isdigit():
            trek_id = int(query.lstrip("#"))
            trek_query = trek_query.filter(
                or_(
                    Trek.id == trek_id,
                    Trek.name.ilike(f"%{query}%"),
                    Trek.location.ilike(f"%{query}%"),
                )
            )
        else:
            trek_query = trek_query.filter(
                or_(
                    Trek.name.ilike(f"%{query}%"),
                    Trek.location.ilike(f"%{query}%"),
                )
            )

    treks = trek_query.order_by(Trek.start_date.asc()).all()
    approved_staff = (
        User.query.filter_by(role="staff", is_approved=True, is_blacklisted=False)
        .order_by(User.name.asc())
        .all()
    )
    clashing_trek_ids = _get_clashing_trek_ids(treks)

    return render_template(
        "admin/manage_treks.html",
        treks=treks,
        approved_staff=approved_staff,
        query=query,
        clashing_trek_ids=clashing_trek_ids,
    )


def create_trek():
    approved_staff = (
        User.query.filter_by(role="staff", is_approved=True, is_blacklisted=False)
        .order_by(User.name.asc())
        .all()
    )

    if request.method == "GET":
        return render_template(
            "admin/trek_form.html",
            trek=None,
            difficulties=DIFFICULTIES,
            statuses=TREK_STATUSES,
            approved_staff=approved_staff,
        )

    name = request.form.get("name", "").strip()
    location = request.form.get("location", "").strip()
    difficulty = request.form.get("difficulty", "Moderate").strip()
    status = request.form.get("status", "Open").strip()
    description = request.form.get("description", "").strip()
    raw_slots = request.form.get("total_slots", "").strip()
    raw_price = request.form.get("price", "").strip()
    raw_start = request.form.get("start_date", "").strip()
    raw_end = request.form.get("end_date", "").strip()
    raw_staff_id = request.form.get("assigned_staff_id", "").strip()

    if not name or not location or not raw_start or not raw_end:
        flash("Name, location, start date, and end date are required.", "danger")
        return redirect(url_for("admin.create_trek"))

    try:
        total_slots = int(raw_slots)
        price = float(raw_price)
        start_date = datetime.strptime(raw_start, "%Y-%m-%d").date()
        end_date = datetime.strptime(raw_end, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid number or date format provided.", "danger")
        return redirect(url_for("admin.create_trek"))

    if end_date < start_date:
        flash("End date cannot be earlier than start date.", "danger")
        return redirect(url_for("admin.create_trek"))

    if total_slots < 1 or price < 0:
        flash("Slots must be at least 1 and price cannot be negative.", "danger")
        return redirect(url_for("admin.create_trek"))

    assigned_staff_id = int(raw_staff_id) if raw_staff_id.isdigit() else None
    resolved_status = status if status in TREK_STATUSES else "Open"
    if assigned_staff_id and resolved_status != "Completed":
        clash = _find_staff_clash(assigned_staff_id, start_date, end_date)
        if clash:
            staff_member = User.query.get(assigned_staff_id)
            staff_name = staff_member.name if staff_member else "Selected staff"
            flash(
                f"{staff_name} is already assigned to '{clash.name}' ({clash.start_date} to {clash.end_date}).",
                "danger",
            )
            return redirect(url_for("admin.create_trek"))

    duration_days = (end_date - start_date).days + 1

    trek = Trek(
        name=name,
        location=location,
        difficulty=difficulty if difficulty in DIFFICULTIES else "Moderate",
        duration_days=duration_days,
        total_slots=total_slots,
        available_slots=total_slots,
        price=price,
        start_date=start_date,
        end_date=end_date,
        status=resolved_status,
        description=description or None,
        assigned_staff_id=assigned_staff_id,
    )

    db.session.add(trek)
    db.session.commit()
    flash(f"Trek '{trek.name}' created ({duration_days} day(s)).", "success")
    return redirect(url_for("admin.manage_treks"))


def edit_trek(trek_id):
    trek = Trek.query.get(trek_id)
    if not trek:
        flash("Trek not found.", "danger")
        return redirect(url_for("admin.manage_treks"))

    approved_staff = (
        User.query.filter_by(role="staff", is_approved=True, is_blacklisted=False)
        .order_by(User.name.asc())
        .all()
    )

    if request.method == "GET":
        return render_template(
            "admin/trek_form.html",
            trek=trek,
            difficulties=DIFFICULTIES,
            statuses=TREK_STATUSES,
            approved_staff=approved_staff,
        )

    name = request.form.get("name", "").strip()
    location = request.form.get("location", "").strip()
    difficulty = request.form.get("difficulty", "Moderate").strip()
    status = request.form.get("status", "Open").strip()
    description = request.form.get("description", "").strip()
    raw_slots = request.form.get("total_slots", "").strip()
    raw_price = request.form.get("price", "").strip()
    raw_start = request.form.get("start_date", "").strip()
    raw_end = request.form.get("end_date", "").strip()
    raw_staff_id = request.form.get("assigned_staff_id", "").strip()

    if not name or not location or not raw_start or not raw_end:
        flash("Name, location, start date, and end date are required.", "danger")
        return redirect(url_for("admin.edit_trek", trek_id=trek.id))

    try:
        new_total_slots = int(raw_slots)
        price = float(raw_price)
        start_date = datetime.strptime(raw_start, "%Y-%m-%d").date()
        end_date = datetime.strptime(raw_end, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid number or date format provided.", "danger")
        return redirect(url_for("admin.edit_trek", trek_id=trek.id))

    if end_date < start_date:
        flash("End date cannot be earlier than start date.", "danger")
        return redirect(url_for("admin.edit_trek", trek_id=trek.id))

    if new_total_slots < 1 or price < 0:
        flash("Slots must be at least 1 and price cannot be negative.", "danger")
        return redirect(url_for("admin.edit_trek", trek_id=trek.id))

    booked_slots = sum(b.slots_booked for b in trek.bookings if b.status != "Cancelled")
    if new_total_slots < booked_slots:
        flash(f"Total slots cannot be less than already booked slots ({booked_slots}).", "danger")
        return redirect(url_for("admin.edit_trek", trek_id=trek.id))

    assigned_staff_id = int(raw_staff_id) if raw_staff_id.isdigit() else None
    resolved_status = status if status in TREK_STATUSES else trek.status
    if assigned_staff_id and resolved_status != "Completed":
        clash = _find_staff_clash(
            assigned_staff_id,
            start_date,
            end_date,
            exclude_trek_id=trek.id,
        )
        if clash:
            staff_member = User.query.get(assigned_staff_id)
            staff_name = staff_member.name if staff_member else "Selected staff"
            flash(
                f"{staff_name} is already assigned to '{clash.name}' ({clash.start_date} to {clash.end_date}).",
                "danger",
            )
            return redirect(url_for("admin.edit_trek", trek_id=trek.id))

    trek.name = name
    trek.location = location
    trek.difficulty = difficulty if difficulty in DIFFICULTIES else trek.difficulty
    trek.duration_days = (end_date - start_date).days + 1
    trek.total_slots = new_total_slots
    trek.available_slots = new_total_slots - booked_slots
    trek.price = price
    trek.start_date = start_date
    trek.end_date = end_date
    trek.status = resolved_status
    trek.description = description or None
    trek.assigned_staff_id = assigned_staff_id

    db.session.commit()
    flash(f"Trek '{trek.name}' updated ({trek.duration_days} day(s)).", "success")
    return redirect(url_for("admin.manage_treks"))


def delete_trek(trek_id):
    trek = Trek.query.get(trek_id)
    if not trek:
        flash("Trek not found.", "danger")
        return redirect(url_for("admin.manage_treks"))

    name = trek.name
    db.session.delete(trek)
    db.session.commit()
    flash(f"Trek '{name}' deleted.", "info")
    return redirect(url_for("admin.manage_treks"))


def assign_staff(trek_id):
    trek = Trek.query.get(trek_id)
    if not trek:
        flash("Trek not found.", "danger")
        return redirect(url_for("admin.manage_treks"))

    raw_staff_id = request.form.get("staff_id", "").strip()
    if not raw_staff_id:
        trek.assigned_staff_id = None
        db.session.commit()
        flash(f"Unassigned staff from '{trek.name}'.", "info")
        return redirect(url_for("admin.manage_treks"))

    if not raw_staff_id.isdigit():
        flash("Invalid staff selection.", "danger")
        return redirect(url_for("admin.manage_treks"))

    staff = User.query.filter_by(id=int(raw_staff_id), role="staff", is_approved=True, is_blacklisted=False).first()
    if not staff:
        flash("Selected staff member is not approved or does not exist.", "danger")
        return redirect(url_for("admin.manage_treks"))

    if trek.status != "Completed":
        clash = _find_staff_clash(
            staff.id,
            trek.start_date,
            trek.end_date,
            exclude_trek_id=trek.id,
        )
        if clash:
            flash(
                f"Cannot assign {staff.name}: date clash with '{clash.name}' ({clash.start_date} to {clash.end_date}).",
                "danger",
            )
            return redirect(url_for("admin.manage_treks"))

    trek.assigned_staff_id = staff.id
    db.session.commit()
    flash(f"Assigned {staff.name} to '{trek.name}'.", "success")
    return redirect(url_for("admin.manage_treks"))


def manage_staff():
    query = request.args.get("q", "").strip()
    staff_query = User.query.filter_by(role="staff")

    if query:
        if query.lstrip("#").isdigit():
            staff_id = int(query.lstrip("#"))
            staff_query = staff_query.filter(
                or_(
                    User.id == staff_id,
                    User.name.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%"),
                )
            )
        else:
            staff_query = staff_query.filter(
                or_(
                    User.name.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%"),
                )
            )

    staff_members = staff_query.order_by(User.created_at.desc()).all()
    return render_template("admin/manage_staff.html", staff_members=staff_members, query=query)


def approve_staff(staff_id):
    staff = User.query.filter_by(id=staff_id, role="staff").first()
    if not staff:
        flash("Staff account not found.", "danger")
        return redirect(url_for("admin.manage_staff"))

    staff.is_approved = True
    db.session.commit()
    flash(f"Approved staff account for {staff.name}.", "success")
    return redirect(url_for("admin.manage_staff"))


def toggle_blacklist_staff(staff_id):
    staff = User.query.filter_by(id=staff_id, role="staff").first()
    if not staff:
        flash("Staff account not found.", "danger")
        return redirect(url_for("admin.manage_staff"))

    staff.is_blacklisted = not staff.is_blacklisted
    db.session.commit()
    state = "blacklisted" if staff.is_blacklisted else "restored"
    flash(f"Staff account for {staff.name} has been {state}.", "warning" if staff.is_blacklisted else "success")
    return redirect(url_for("admin.manage_staff"))


def manage_users():
    query = request.args.get("q", "").strip()
    user_query = User.query.filter_by(role="user")

    if query:
        if query.lstrip("#").isdigit():
            user_id = int(query.lstrip("#"))
            user_query = user_query.filter(
                or_(
                    User.id == user_id,
                    User.name.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%"),
                )
            )
        else:
            user_query = user_query.filter(
                or_(
                    User.name.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%"),
                )
            )

    users = user_query.order_by(User.created_at.desc()).all()
    return render_template("admin/manage_users.html", users=users, query=query)


def toggle_blacklist_user(user_id):
    user = User.query.filter_by(id=user_id, role="user").first()
    if not user:
        flash("User account not found.", "danger")
        return redirect(url_for("admin.manage_users"))

    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    state = "blacklisted" if user.is_blacklisted else "restored"
    flash(f"User account for {user.name} has been {state}.", "warning" if user.is_blacklisted else "success")
    return redirect(url_for("admin.manage_users"))


def all_bookings():
    status_filter = request.args.get("status", "").strip()
    booking_query = Booking.query

    if status_filter in ("Booked", "Completed", "Cancelled"):
        booking_query = booking_query.filter_by(status=status_filter)

    bookings = booking_query.order_by(Booking.booking_date.desc()).all()
    return render_template("admin/all_bookings.html", bookings=bookings, status_filter=status_filter)


def completed_feedback():
    selected_trek_id = request.args.get("trek_id", type=int)

    completed_treks = (
        Trek.query.filter_by(status="Completed")
        .order_by(Trek.end_date.desc(), Trek.name.asc())
        .all()
    )

    feedback_query = (
        Review.query.join(Trek, Review.trek_id == Trek.id)
        .filter(Trek.status == "Completed")
    )

    if selected_trek_id:
        feedback_query = feedback_query.filter(Review.trek_id == selected_trek_id)

    feedback_list = feedback_query.order_by(Review.created_at.desc()).all()

    return render_template(
        "admin/completed_feedback.html",
        feedback_list=feedback_list,
        completed_treks=completed_treks,
        selected_trek_id=selected_trek_id,
    )