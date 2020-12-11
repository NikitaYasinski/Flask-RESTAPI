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
    user_id = db.Column(db.Integer)

class Permission(db.Model):
    user_from = db.Column(db.Integer, primary_key=True, autoincrement=False)
    user_to = db.Column(db.Integer, primary_key=True, autoincrement=False)
    get_perm = db.Column(db.Boolean)
    post_perm = db.Column(db.Boolean)
    put_perm = db.Column(db.Boolean)
    delete_perm = db.Column(db.Boolean)

def permission(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        

@app.route("/user/<int:user_from>/note/perm/<int:user_to>")
@jwt_required
def create_perm(user_from, user_to):
    if user_from == get_jwt_identity(): 
        data = request.get_json()

        new_perm = Permission(
            user_from=user_from, user_to=user_to, get_perm=data["get_perm"], 
            post_perm=data["post_perm"], put_perm=data["put_perm"], delete_perm=data["delete_perm"]
        )
        db.session.merge(new_perm)
        db.session.commit()

        return jsonify({"message": "New permission created!"})
    else:
        return jsonify({"message": "Permission denied!"})


@app.route("/register", )
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
            "access_token": create_access_token(identity=user.id),
            "refresh_token": create_refresh_token(identity=user.id),
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


@app.route("/user/<int:user_id>", methods=["GET"])
@jwt_required
def get_one_user(user_id):

    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({"message": "No user found!"})

    user_data = {}
    user_data["id"] = user.id
    user_data["public_id"] = user.public_id
    user_data["name"] = user.name
    user_data["password"] = user.password

    return jsonify({"user": user_data, "iden": get_jwt_identity()})


@app.route("/user/<int:user_id>", methods=["DELETE"])
@jwt_required
def delete_user(user_id):

    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({"message": "No user found!"})

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted!"})


@app.route("/user/<int:user_id>/note", methods=["GET"])
@jwt_required
def get_all_notes(user_id):
    
    perm = Permission.query.filter_by(user_from=user_id, user_to=get_jwt_identity()).first()

    if not perm:
        if user_id != get_jwt_identity():
            return jsonify({"message": "Permission denied!"})

    if perm.get_perm is True or user_id == get_jwt_identity():

        notes = Note.query.filter_by(user_id=user_id).all()

        output = []

        for note in notes:
            note_data = {}
            note_data["id"] = note.id
            note_data["text"] = note.text
            note_data["checked"] = note.checked
            output.append(note_data)

        return jsonify({"notes": output})
    else:
        return jsonify({"message": "Permission denied!"})


@app.route("/user/<int:user_id>/note/<note_id>", methods=["GET"])
@jwt_required
def get_one_note(user_id, note_id):
    perm = Permission.query.filter_by(user_from=user_id, user_to=get_jwt_identity()).first()

    if not perm:
        if user_id != get_jwt_identity():
            return jsonify({"message": "Permission denied!"})
    
    if perm.get_perm is True or user_id == get_jwt_identity():

        note = Note.query.filter_by(id=note_id, user_id=user_id).first()

        if not note:
            return jsonify({"message": "No note found!"})

        note_data = {}
        note_data["id"] = note.id
        note_data["text"] = note.text
        note_data["checked"] = note.checked

        return jsonify(note_data)
    else:
        return jsonify({"message": "Permission denied!"})


@app.route("/user/<int:user_id>/note", methods=["POST"])
@jwt_required
def create_note(user_id):
    data = request.get_json()

    perm = Permission.query.filter_by(user_from=user_id, user_to=get_jwt_identity()).first()

    if not perm:
        if user_id != get_jwt_identity():
            return jsonify({"message": "Permission denied!"})

    if perm.post_perm is True or user_id == get_jwt_identity():

        new_note = Note(text=data["text"], checked=False, user_id=user_id)
        db.session.add(new_note)
        db.session.commit()
    else:
        return jsonify({"message": "Permission denied!"})

    return jsonify({"message": "Note created!"})


@app.route("/user/<int:user_id>/note/<note_id>", methods=["PUT"])
@jwt_required
def complete_note(user_id, note_id):
    perm = Permission.query.filter_by(user_from=user_id, user_to=get_jwt_identity()).first()

    if not perm:
        if user_id != get_jwt_identity():
            return jsonify({"message": "Permission denied!"})

    if perm.put_perm is True or user_id == get_jwt_identity():
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()

        if not note:
            return jsonify({"message": "No note found!"})

        note.checked = True
        db.session.commit()
    else:
        return jsonify({"message": "Permission denied!"})

    return jsonify({"message": "Note has been checked!"})


@app.route("/user/<int:user_id>/note/<note_id>", methods=["DELETE"])
@jwt_required
def delete_note(user_id, note_id):
    perm = Permission.query.filter_by(user_from=user_id, user_to=get_jwt_identity()).first()

    if not perm:
        if user_id != get_jwt_identity():
            return jsonify({"message": "Permission denied!"})

    if perm.put_perm is True or user_id == get_jwt_identity():
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()

        if not note:
            return jsonify({"message": "No note found!"})

        db.session.delete(note)
        db.session.commit()
    else:
        return jsonify({"message": "Permission denied!"})


    return jsonify({"message": "Note deleted!"})


if __name__ == "__main__":
    app.run(port=5000, debug=True, host='0.0.0.0')