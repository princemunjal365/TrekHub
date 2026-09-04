from flask import Flask
from model import db

app = None

def setup_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tms.sqlite3" 
    db.init_app(app) 
    app.app_context().push()
    
setup_app()

from controller import *

if __name__ == "__main__":
    app.run()
