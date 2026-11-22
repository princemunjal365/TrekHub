import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")


class Config:
    SECRET_KEY = os.environ.get("TREKHUB_SECRET_KEY", "trekhub-secret-key-2026")
    JWT_SECRET_KEY = os.environ.get("TREKHUB_JWT_SECRET_KEY", "trekhub-jwt-secret-key-2026")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(INSTANCE_DIR, "trekhub.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_TOKEN_LOCATION = ["cookies", "headers"]
    JWT_ACCESS_COOKIE_NAME = "trekhub_access_token"
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_SESSION_COOKIE = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=6)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ADMIN_NAME = "Admin"
    ADMIN_EMAIL = os.environ.get("TREKHUB_ADMIN_EMAIL", "admin@trekhub.com")
    ADMIN_PASSWORD = os.environ.get("TREKHUB_ADMIN_PASSWORD", "Admin@123")
    RAZORPAY_KEY_ID = os.environ.get("TREKHUB_RAZORPAY_KEY_ID", "enter your razorpay key secret")
    RAZORPAY_KEY_SECRET = os.environ.get("TREKHUB_RAZORPAY_KEY_SECRET", "enter your razorpay key secret")