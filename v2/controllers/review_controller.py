from flask import render_template, request, redirect, url_for, flash, g
from models import db, Trek, Booking, Review


def _has_completed_trek_booking(user_id, trek_id):
    return (
        Booking.query.filter_by(user_id=user_id, trek_id=trek_id)
        .filter(Booking.status != "Cancelled")
        .first()
        is not None
    )


def add_review(trek_id):
    user = g.current_user
    trek = Trek.query.get(trek_id)
    if not trek:
        flash("Trek not found.", "danger")
        return redirect(url_for("user.dashboard"))

    if trek.status != "Completed":
        flash("You can only submit feedback after the trek is marked Completed.", "warning")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    if not _has_completed_trek_booking(user.id, trek.id):
        flash("Only trekkers who booked this completed trek can submit feedback.", "warning")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))

    existing_review = Review.query.filter_by(user_id=user.id, trek_id=trek.id).first()

    if request.method == "GET":
        return render_template(
            "user/review_form.html",
            trek=trek,
            review=existing_review,
        )

    raw_rating = request.form.get("rating", "").strip()
    comment = request.form.get("comment", "").strip()

    try:
        rating = int(raw_rating)
    except ValueError:
        flash("Rating must be a number between 1 and 5.", "danger")
        return redirect(url_for("review.add_review", trek_id=trek.id))

    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5.", "danger")
        return redirect(url_for("review.add_review", trek_id=trek.id))

    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment or None
        db.session.commit()
        flash("Your feedback has been updated.", "success")
    else:
        review = Review(
            user_id=user.id,
            trek_id=trek.id,
            rating=rating,
            comment=comment or None,
        )
        db.session.add(review)
        db.session.commit()
        flash("Thank you! Your feedback has been submitted to Admin and Trek Staff.", "success")

    return redirect(url_for("user.trek_detail", trek_id=trek.id))


def delete_review(review_id):
    user = g.current_user
    review = Review.query.get(review_id)
    if not review:
        flash("Feedback not found.", "danger")
        return redirect(url_for("user.dashboard"))

    if user.role != "admin" and review.user_id != user.id:
        flash("You do not have permission to delete this feedback.", "danger")
        return redirect(url_for("user.trek_detail", trek_id=review.trek_id))

    trek_id = review.trek_id
    db.session.delete(review)
    db.session.commit()
    flash("Feedback removed.", "info")
    return redirect(url_for("user.trek_detail", trek_id=trek_id))