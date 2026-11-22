import os
from flask import Flask, render_template, redirect, url_for, request, jsonify
from config import Config
from models import db, bcrypt, jwt
from routes import register_blueprints
from utils.seed import seed_admin
from utils.helpers import (get_logged_in_user, format_inr, status_badge_class, difficulty_badge_class,)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    register_blueprints(app)
    
    @app.context_processor
    def inject_helpers():
        return {
            "current_user": get_logged_in_user(),
            "format_inr": format_inr,
            "status_badge_class": status_badge_class,
            "difficulty_badge_class": difficulty_badge_class,
        }

    @app.route("/")
    def index():
        return render_template("index.html")

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Authentication required"}), 401
        return redirect(url_for("auth.login"))

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Token expired"}), 401
        return redirect(url_for("auth.login"))

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Invalid token"}), 401
        return redirect(url_for("auth.login"))

    with app.app_context():
        db.create_all()
        seed_admin()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)