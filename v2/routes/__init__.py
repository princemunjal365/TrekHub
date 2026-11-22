from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.staff_routes import staff_bp
from routes.user_routes import user_bp
from routes.payment_routes import payment_bp
from routes.location_routes import location_bp
from routes.review_routes import review_bp
from routes.api_routes import api_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(payment_bp, url_prefix="/payment")
    app.register_blueprint(location_bp, url_prefix="/location")
    app.register_blueprint(review_bp, url_prefix="/review")
    app.register_blueprint(api_bp, url_prefix="/api")