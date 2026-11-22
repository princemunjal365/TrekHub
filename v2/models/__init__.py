from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

from models.user import User
from models.trek import Trek
from models.booking import Booking
from models.payment import Payment
from models.location import LocationUpdate
from models.review import Review