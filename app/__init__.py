from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager

app = Flask(__name__)

CORS(app)

app.config.from_object("config")
db = SQLAlchemy(app)
jwt = JWTManager(app)

from app.mod_auth.routes import mod_auth as auth_module

app.register_blueprint(auth_module)


@app.before_request
def create_db():
    db.create_all()
