import base64
from datetime import datetime
import hashlib
import hmac
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from flask import render_template, request, redirect, url_for, flash, current_app, g
from models import db, Trek, Booking, Payment


def _razorpay_credentials():
    key_id = current_app.config.get("RAZORPAY_KEY_ID", "").strip()
    key_secret = current_app.config.get("RAZORPAY_KEY_SECRET", "").strip()
    if not key_id or not key_secret:
        return None, None
    return key_id, key_secret


def _create_razorpay_order(key_id, key_secret, amount_paise, receipt_code):
    payload = json.dumps(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt_code[:40],
        }
    ).encode("utf-8")

    token = base64.b64encode(f"{key_id}:{key_secret}".encode("utf-8")).decode("ascii")
    req = Request(
        "https://api.razorpay.com/v1/orders",
        data=payload,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _verify_razorpay_signature(key_secret, order_id, payment_id, signature):
    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(
        key_secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _resolve_order_request():
    booking_id = request.args.get("booking_id", type=int) or request.form.get("booking_id", type=int)
    if booking_id:
        booking = Booking.query.get(booking_id)
        if not booking:
            return None, None, 0, "Booking not found."
        return booking, booking.trek, booking.slots_booked, None

    trek_id = request.args.get("trek_id", type=int) or request.form.get("trek_id", type=int)
    slots = request.args.get("slots", type=int) or request.form.get("slots", type=int)
    if not trek_id or not slots:
        return None, None, 0, "Invalid checkout request."

    trek = Trek.query.get(trek_id)
    if not trek:
        return None, None, 0, "Trek not found."

    return None, trek, slots, None


def checkout():
    user = g.current_user
    booking, trek, slots_booked, err = _resolve_order_request()
    if err:
        flash(err, "danger")
        return redirect(url_for("user.dashboard"))

    if booking and user.role != "admin" and booking.user_id != user.id:
        flash("Access denied for this booking.", "danger")
        return redirect(url_for("user.bookings"))

    if booking:
        total_amount = booking.total_amount
        existing_payment = booking.payment
    else:
        if trek.status != "Open":
            flash(f"Cannot book this trek because its status is '{trek.status}'.", "warning")
            return redirect(url_for("user.trek_detail", trek_id=trek.id))
        if slots_booked < 1 or slots_booked > trek.available_slots:
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
        total_amount = round(float(trek.price) * slots_booked, 2)
        existing_payment = None

    key_id, key_secret = _razorpay_credentials()
    if not key_id or not key_secret:
        flash("Razorpay Test Mode keys are not configured.", "danger")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    amount_paise = int(round(total_amount * 100))
    receipt_code = f"booking_{booking.id}" if booking else f"trek_{trek.id}_u_{user.id}"

    try:
        order = _create_razorpay_order(key_id, key_secret, amount_paise, receipt_code)
    except (HTTPError, URLError, TimeoutError, ValueError):
        flash("Unable to start Razorpay checkout right now. Please try again.", "danger")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    return render_template(
        "user/payment.html",
        user=user,
        booking=booking,
        trek=trek,
        slots_booked=slots_booked,
        total_amount=total_amount,
        amount_paise=amount_paise,
        payment=existing_payment,
        razorpay_key_id=key_id,
        razorpay_order_id=order["id"],
    )


def verify_payment():
    user = g.current_user
    if request.method == "GET":
        return redirect(url_for("user.bookings"))

    razorpay_order_id = request.form.get("razorpay_order_id", "").strip()
    razorpay_payment_id = request.form.get("razorpay_payment_id", "").strip()
    razorpay_signature = request.form.get("razorpay_signature", "").strip()

    booking, trek, slots_booked, err = _resolve_order_request()
    if err:
        flash(err, "danger")
        return redirect(url_for("user.dashboard"))

    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        flash("Payment was not completed. No booking was created and no slots were deducted.", "warning")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    _, key_secret = _razorpay_credentials()
    if not key_secret:
        flash("Razorpay configuration missing.", "danger")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    if not _verify_razorpay_signature(key_secret, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        flash("Payment signature verification failed. No booking was created.", "danger")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    if booking:
        total_amount = booking.total_amount
        existing_payment = booking.payment
    else:
        if trek.status != "Open" or slots_booked < 1 or slots_booked > trek.available_slots:
            flash("Selected slots are no longer available. No booking was created.", "warning")
            return redirect(url_for("user.trek_detail", trek_id=trek.id))

        total_amount = round(float(trek.price) * slots_booked, 2)
        booking = Booking(
            user_id=user.id,
            trek_id=trek.id,
            slots_booked=slots_booked,
            total_amount=total_amount,
            status="Booked",
        )
        trek.available_slots -= slots_booked
        db.session.add(booking)
        db.session.flush()
        existing_payment = None

    if existing_payment:
        existing_payment.user_id = booking.user_id
        existing_payment.payment_method = "Razorpay (Test)"
        existing_payment.transaction_id = razorpay_payment_id
        existing_payment.amount = total_amount
        existing_payment.status = "Paid"
        existing_payment.paid_at = datetime.utcnow()
    else:
        payment = Payment(
            booking_id=booking.id,
            user_id=booking.user_id,
            amount=total_amount,
            payment_method="Razorpay (Test)",
            transaction_id=razorpay_payment_id,
            status="Paid",
            paid_at=datetime.utcnow(),
        )
        db.session.add(payment)

    booking.status = "Booked"
    db.session.commit()

    flash(f"Razorpay payment verified! Booking #{booking.id} confirmed for {slots_booked} slot(s).", "success")
    return redirect(url_for("payment.receipt", booking_id=booking.id))


def receipt(booking_id):
    user = g.current_user
    booking = Booking.query.get(booking_id)
    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for("user.bookings"))

    if user.role != "admin" and booking.user_id != user.id:
        flash("Access denied for this receipt.", "danger")
        return redirect(url_for("user.bookings"))

    return render_template(
        "user/payment.html",
        user=user,
        booking=booking,
        trek=booking.trek,
        slots_booked=booking.slots_booked,
        total_amount=booking.total_amount,
        amount_paise=int(round(float(booking.total_amount) * 100)),
        payment=booking.payment,
        razorpay_key_id=current_app.config.get("RAZORPAY_KEY_ID", ""),
        razorpay_order_id="",
    )