from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity
from sqlalchemy import or_, func
from models import db, User, Trek, Booking, LocationUpdate, Review


VALID_DIFFICULTIES = ("Easy", "Moderate", "Hard")
VALID_TREK_STATUSES = ("Pending", "Approved", "Open", "Closed", "Started", "Completed")


def _get_current_user():
    identity = get_jwt_identity()
    if not identity:
        return None
    return User.query.get(int(identity))


def api_login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    if user.is_blacklisted:
        return jsonify({"error": "Account is blacklisted"}), 403

    if user.role == "staff" and not user.is_approved:
        return jsonify({"error": "Staff account is pending Admin approval"}), 403

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )

    return jsonify({
        "access_token": access_token,
        "user": user.to_dict(),
    }), 200


def get_treks():
    query = request.args.get("q", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    location = request.args.get("location", "").strip()
    status = request.args.get("status", "").strip()

    treks_query = Trek.query

    if query:
        treks_query = treks_query.filter(
            or_(Trek.name.ilike(f"%{query}%"), Trek.location.ilike(f"%{query}%"))
        )

    if difficulty in VALID_DIFFICULTIES:
        treks_query = treks_query.filter_by(difficulty=difficulty)

    if location:
        treks_query = treks_query.filter(Trek.location.ilike(f"%{location}%"))

    if status in VALID_TREK_STATUSES:
        treks_query = treks_query.filter_by(status=status)

    treks = treks_query.order_by(Trek.start_date.asc()).all()
    return jsonify({"treks": [trek.to_dict() for trek in treks]}), 200


def get_trek(trek_id):
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"error": "Trek not found"}), 404

    avg_rating = (
        db.session.query(func.avg(Review.rating))
        .filter(Review.trek_id == trek.id)
        .scalar()
    )

    data = trek.to_dict()
    data["average_rating"] = round(avg_rating, 1) if avg_rating else None
    data["review_count"] = Review.query.filter_by(trek_id=trek.id).count()
    return jsonify({"trek": data}), 200


def create_trek():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    location = str(data.get("location", "")).strip()
    difficulty = str(data.get("difficulty", "Moderate")).strip()
    status = str(data.get("status", "Open")).strip()
    description = str(data.get("description", "")).strip()
    assigned_staff_id = data.get("assigned_staff_id")

    if not name or not location:
        return jsonify({"error": "Name and location are required"}), 400

    if difficulty not in VALID_DIFFICULTIES or status not in VALID_TREK_STATUSES:
        return jsonify({"error": "Invalid difficulty or status"}), 400

    try:
        duration_days = int(data.get("duration_days", 0))
        total_slots = int(data.get("total_slots", 0))
        price = float(data.get("price", 0))
        start_date = datetime.strptime(str(data.get("start_date", "")), "%Y-%m-%d").date()
        end_date = datetime.strptime(str(data.get("end_date", "")), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric values or date format (YYYY-MM-DD)"}), 400

    if duration_days < 1 or total_slots < 1 or price < 0:
        return jsonify({"error": "Duration and slots must be at least 1, price cannot be negative"}), 400

    if end_date < start_date:
        return jsonify({"error": "End date cannot be earlier than start date"}), 400

    valid_staff_id = None
    if assigned_staff_id is not None:
        staff = User.query.filter_by(
            id=int(assigned_staff_id), role="staff", is_approved=True, is_blacklisted=False
        ).first()
        if not staff:
            return jsonify({"error": "Assigned staff member is not eligible"}), 400
        valid_staff_id = staff.id

    trek = Trek(
        name=name,
        location=location,
        difficulty=difficulty,
        duration_days=duration_days,
        total_slots=total_slots,
        available_slots=total_slots,
        price=price,
        assigned_staff_id=valid_staff_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        description=description or None,
    )

    db.session.add(trek)
    db.session.commit()
    return jsonify({"message": "Trek created", "trek": trek.to_dict()}), 201


def update_trek(trek_id):
    user = _get_current_user()
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"error": "Trek not found"}), 404

    if user.role == "staff" and trek.assigned_staff_id != user.id:
        return jsonify({"error": "Not authorised to update this trek"}), 403

    data = request.get_json(silent=True) or {}

    if "status" in data:
        status = str(data["status"]).strip()
        if status not in VALID_TREK_STATUSES:
            return jsonify({"error": "Invalid trek status"}), 400
        trek.status = status
        if status == "Completed":
            Booking.query.filter_by(trek_id=trek.id, status="Booked").update({"status": "Completed"})

    booked_slots = (
        db.session.query(func.coalesce(func.sum(Booking.slots_booked), 0))
        .filter(Booking.trek_id == trek.id, Booking.status != "Cancelled")
        .scalar()
    )

    if user.role == "staff":
        if "available_slots" in data:
            try:
                available_slots = int(data["available_slots"])
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid available_slots value"}), 400
            if available_slots < 0:
                return jsonify({"error": "Available slots cannot be negative"}), 400
            trek.available_slots = available_slots
            trek.total_slots = booked_slots + available_slots
    else:
        if "name" in data and str(data["name"]).strip():
            trek.name = str(data["name"]).strip()
        if "location" in data and str(data["location"]).strip():
            trek.location = str(data["location"]).strip()
        if "difficulty" in data:
            if data["difficulty"] not in VALID_DIFFICULTIES:
                return jsonify({"error": "Invalid difficulty"}), 400
            trek.difficulty = data["difficulty"]
        if "duration_days" in data:
            try:
                duration_days = int(data["duration_days"])
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid duration_days"}), 400
            if duration_days < 1:
                return jsonify({"error": "Duration must be at least 1"}), 400
            trek.duration_days = duration_days
        if "price" in data:
            try:
                price = float(data["price"])
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid price"}), 400
            if price < 0:
                return jsonify({"error": "Price cannot be negative"}), 400
            trek.price = price
        if "total_slots" in data:
            try:
                total_slots = int(data["total_slots"])
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid total_slots"}), 400
            if total_slots < booked_slots:
                return jsonify({"error": f"Total slots cannot be less than booked slots ({booked_slots})"}), 400
            trek.total_slots = total_slots
            trek.available_slots = total_slots - booked_slots
        if "description" in data:
            trek.description = str(data["description"]).strip() or None

    db.session.commit()
    return jsonify({"message": "Trek updated", "trek": trek.to_dict()}), 200


def delete_trek(trek_id):
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"error": "Trek not found"}), 404

    db.session.delete(trek)
    db.session.commit()
    return jsonify({"message": "Trek deleted"}), 200


def get_users():
    role = request.args.get("role", "").strip().lower()
    query = request.args.get("q", "").strip()

    users_query = User.query
    if role in ("admin", "staff", "user"):
        users_query = users_query.filter_by(role=role)

    if query:
        if query.isdigit():
            users_query = users_query.filter(
                or_(User.id == int(query), User.name.ilike(f"%{query}%"))
            )
        else:
            users_query = users_query.filter(
                or_(User.name.ilike(f"%{query}%"), User.email.ilike(f"%{query}%"))
            )

    users = users_query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


def get_user(user_id):
    current = _get_current_user()
    if current.role != "admin" and current.id != user_id:
        return jsonify({"error": "Not authorised to view this profile"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict()}), 200


def get_bookings():
    user = _get_current_user()

    if user.role == "admin":
        bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    elif user.role == "staff":
        assigned_ids = [t.id for t in Trek.query.filter_by(assigned_staff_id=user.id).all()]
        bookings = (
            Booking.query.filter(Booking.trek_id.in_(assigned_ids))
            .order_by(Booking.booking_date.desc())
            .all()
        )
    else:
        bookings = (
            Booking.query.filter_by(user_id=user.id)
            .order_by(Booking.booking_date.desc())
            .all()
        )

    return jsonify({"bookings": [b.to_dict() for b in bookings]}), 200


def create_booking():
    user = _get_current_user()
    if user.role != "user":
        return jsonify({"error": "Only trekkers can book treks"}), 403

    data = request.get_json(silent=True) or {}
    try:
        trek_id = int(data.get("trek_id", 0))
        slots_booked = int(data.get("slots_booked", 1))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid trek_id or slots_booked"}), 400

    if slots_booked < 1:
        return jsonify({"error": "You must book at least 1 slot"}), 400

    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"error": "Trek not found"}), 404

    if trek.status != "Open":
        return jsonify({"error": "Trek is not open for booking"}), 400

    existing = Booking.query.filter_by(
        user_id=user.id, trek_id=trek.id, status="Booked"
    ).first()
    if existing:
        return jsonify({"error": "You already have an active booking for this trek"}), 409

    if trek.available_slots < slots_booked:
        return jsonify({"error": f"Only {trek.available_slots} slot(s) remaining"}), 400

    booking = Booking(
        user_id=user.id,
        trek_id=trek.id,
        slots_booked=slots_booked,
        total_amount=round(trek.price * slots_booked, 2),
        status="Booked",
    )
    trek.available_slots -= slots_booked

    db.session.add(booking)
    db.session.commit()
    return jsonify({"message": "Booking created", "booking": booking.to_dict()}), 201


def cancel_booking(booking_id):
    user = _get_current_user()
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if user.role != "admin" and booking.user_id != user.id:
        return jsonify({"error": "Not authorised to cancel this booking"}), 403

    if booking.status != "Booked":
        return jsonify({"error": "Only active bookings can be cancelled"}), 400

    if booking.trek.status in ("Started", "Completed"):
        return jsonify({"error": "Cannot cancel after trek has started or completed"}), 400

    booking.status = "Cancelled"
    booking.trek.available_slots += booking.slots_booked

    if booking.payment and booking.payment.status == "Paid":
        booking.payment.status = "Refunded"

    db.session.commit()
    return jsonify({"message": "Booking cancelled", "booking": booking.to_dict()}), 200


def get_trek_locations(trek_id):
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"error": "Trek not found"}), 404

    updates = (
        LocationUpdate.query.filter_by(trek_id=trek.id)
        .order_by(LocationUpdate.updated_at.desc())
        .all()
    )
    return jsonify({"locations": [u.to_dict() for u in updates]}), 200


def get_trek_reviews(trek_id):
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"error": "Trek not found"}), 404

    reviews = (
        Review.query.filter_by(trek_id=trek.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return jsonify({"reviews": [r.to_dict() for r in reviews]}), 200


def get_stats():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="user").count()
    total_staff = User.query.filter_by(role="staff").count()
    total_bookings = Booking.query.count()

    popular_treks = (
        db.session.query(Trek.name, func.count(Booking.id).label("bookings"))
        .outerjoin(Booking, Trek.id == Booking.trek_id)
        .group_by(Trek.id)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
        .all()
    )

    status_counts = (
        db.session.query(Trek.status, func.count(Trek.id))
        .group_by(Trek.status)
        .all()
    )

    return jsonify({
        "total_treks": total_treks,
        "total_users": total_users,
        "total_staff": total_staff,
        "total_bookings": total_bookings,
        "popular_treks": [{"name": name, "bookings": count} for name, count in popular_treks],
        "status_breakdown": dict(status_counts),
    }), 200