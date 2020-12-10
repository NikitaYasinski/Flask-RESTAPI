from flask import Flask, jsonify, request, make_response
import os
from dotenv import load_dotenv
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import uuid
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    jwt_refresh_token_required,
    create_refresh_token,
    get_jwt_identity,
)

app = Flask(__name__)
CORS(app)


app.config["JWT_SECRET_KEY"] = "potatoes"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(minutes=20)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=60)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://{}:{}@{}/{}".format(
    os.getenv("DB_USER"),
    os.getenv("DB_PASSWORD"),
    os.getenv("DB_HOST"),
    os.getenv("DB_NAME"),
)

db = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(50))
    checked = db.Column(db.Boolean)
    user_name = db.Column(db.String(50))


# def token_required(f):
#   @wraps(f)
#  def decorated(*args, **kwargs):
#     token = None
#
#       if "x-access-token" in request.headers:
#          token = request.headers["x-access-token"]
#
#       if not token:
#          return jsonify({"message": "Token is missing!"}), 401
#
#       try:
#          data = jwt.decode(token, app.config["SECRET_KEY"])
#         current_user = User.query.filter_by(public_id=data["public_id"]).first()
#    except:
#       return jsonify({"message": "Token is invalid!"}), 401
#
#       return f(current_user, *args, **kwargs)
#
#   return decorated


@app.route("/register")
def create_user():
    data = request.get_json()

    hashed_password = generate_password_hash(data["password"], method="sha256")

    new_user = User(
        public_id=str(uuid.uuid4()), name=data["name"], password=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "New user created!"})


@app.route("/login")
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response(
            "Could not verify",
            401,
            {"WWW-Authenticate": 'Basic realm="Login required!"'},
        )

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response(
            "Could not verify",
            401,
            {"WWW-Authenticate": 'Basic realm="Login required!"'},
        )

    if check_password_hash(user.password, auth.password):
        ret = {
            "access_token": create_access_token(identity=user.name),
            "refresh_token": create_refresh_token(identity=user.name),
        }

        return jsonify(ret)

    return make_response(
        "Could not verify", 401, {"WWW-Authenticate": 'Basic realm="Login required!"'}
    )


@app.route("/refresh", methods=["POST"])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    ret = {
        "access_token": create_access_token(identity=current_user),
        "refresh_token": create_refresh_token(identity=current_user),
    }
    return jsonify(ret), 200


@app.before_request
def create_db():
    db.create_all()


@app.route("/user", methods=["GET"])
@jwt_required
def get_all_users():

    users = User.query.all()

    output = []
    for user in users:
        user_data = {}
        user_data["id"] = user.id
        user_data["public_id"] = user.public_id
        user_data["name"] = user.name
        user_data["password"] = user.password
        output.append(user_data)

    return jsonify({"users": output})


@app.route("/user/<public_id>", methods=["GET"])
@jwt_required
def get_one_user(public_id):

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({"message": "No user found!"})

    user_data = {}
    user_data["id"] = user.id
    user_data["public_id"] = user.public_id
    user_data["name"] = user.name
    user_data["password"] = user.password

    return jsonify({"user": user_data})


@app.route("/user/<public_id>", methods=["DELETE"])
@jwt_required
def delete_user(public_id):

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({"message": "No user found!"})

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted!"})


@app.route("/note", methods=["GET"])
@jwt_required
def get_all_notes():
    notes = Note.query.filter_by(user_name=get_jwt_identity()).all()

    output = []

    for note in notes:
        note_data = {}
        note_data["id"] = note.id
        note_data["text"] = note.text
        note_data["checked"] = note.checked
        output.append(note_data)

    return jsonify({"notes": output})


@app.route("/note/<note_id>", methods=["GET"])
@jwt_required
def get_one_note(note_id):
    note = Note.query.filter_by(id=note_id, user_name=get_jwt_identity()).first()

    if not note:
        return jsonify({"message": "No note found!"})

    note_data = {}
    note_data["id"] = note.id
    note_data["text"] = note.text
    note_data["checked"] = note.checked

    return jsonify(note_data)


@app.route("/note", methods=["POST"])
@jwt_required
def create_note():
    data = request.get_json()

    new_note = Note(text=data["text"], checked=False, user_name=get_jwt_identity())
    db.session.add(new_note)
    db.session.commit()

    return jsonify({"message": "Note created!"})


@app.route("/note/<note_id>", methods=["PUT"])
@jwt_required
def complete_note(note_id):
    note = Note.query.filter_by(id=note_id, user_name=get_jwt_identity()).first()

    if not note:
        return jsonify({"message": "No note found!"})

    note.checked = True
    db.session.commit()

    return jsonify({"message": "Note has been checked!"})


@app.route("/note/<note_id>", methods=["DELETE"])
@jwt_required
def delete_note(note_id):
    note = Note.query.filter_by(id=note_id, user_name=get_jwt_identity()).first()

    if not note:
        return jsonify({"message": "No note found!"})

    db.session.delete(note)
    db.session.commit()

    return jsonify({"message": "Note deleted!"})


if __name__ == "__main__":
    app.run(port=5000, debug=True, host='0.0.0.0')