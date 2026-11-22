from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User_Credentials(db.Model):
    __tablename__ = "user_credentials"
    user_id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String, unique = True, nullable = False)
    password = db.Column(db.String, nullable = False)
    role = db.Column(db.String, nullable = False)
    auth_key = db.Column(db.String)
    
class Trekker_Profile(db.Model):
    __tablename__ = "trekker_profile"
    trekker_id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_credentials.user_id'), nullable = False)
    name = db.Column(db.String, nullable = False)
    address = db.Column(db.String, nullable = False)
    status = db.Column(db.String, nullable = False, default = 'active')
    
class Staff_Profile(db.Model):
    __tablename__ = "staff_profile"
    staff_id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_credentials.user_id'), nullable = False)
    name = db.Column(db.String, nullable = False)
    address = db.Column(db.String, nullable = False)
    status = db.Column(db.String, nullable = False, default = 'pending')
    rated_by = db.Column(db.Integer, nullable = False, default = 0)
    ratings = db.Column(db.Float, nullable = True)
    treks_completed = db.Column(db.Integer, nullable = False, default = 0)

class Treks(db.Model):
    __tablename__ = "treks"
    trek_id = db.Column(db.Integer, primary_key = True)
    trek_name = db.Column(db.String , nullable = False)
    assigned_staff = db.Column(db.Integer, db.ForeignKey('staff_profile.staff_id'), nullable = False)
    location = db.Column(db.String, nullable = False)
    difficulty = db.Column(db.String, nullable = False)
    available_slots = db.Column(db.Integer, nullable = False)
    booking_last_date = db.Column(db.Date, nullable = False)
    duration = db.Column(db.Integer, nullable = False)
    start_date = db.Column(db.Date, nullable = False)
    end_date = db.Column(db.Date, nullable = False)
    status = db.Column(db.String, nullable = False, default = 'open')
    rated_by = db.Column(db.Integer, nullable = False, default = 0)
    ratings = db.Column(db.Float, nullable = True)

class Bookings(db.Model):
    __tablename__ = "bookings"    
    booking_id = db.Column(db.Integer, primary_key = True)
    trekker_id = db.Column(db.Integer, db.ForeignKey('trekker_profile.trekker_id'), nullable = False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.trek_id'), nullable = False)
    booking_date = db.Column(db.DateTime, nullable = False)
    status = db.Column(db.String, nullable = False, default = 'pending')
    rated_staff = db.Column(db.String, nullable = False, default = 'no')
    rated_trek = db.Column(db.String, nullable = False, default = 'no')
    __table_args__ = ( db.UniqueConstraint('trekker_id', 'trek_id', name='_trekker_trek_uc'),)