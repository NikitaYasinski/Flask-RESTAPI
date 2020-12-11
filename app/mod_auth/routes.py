from flask import Flask, jsonify, request, make_response, Blueprint
import uuid
from app import db
from app import jwt
from app.mod_auth.models import User, Note, Permission
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    jwt_refresh_token_required,
    create_refresh_token,
    get_jwt_identity,
)

mod_auth = Blueprint('auth', __name__)

@mod_auth.route("/user/<int:user_from>/note/perm/<int:user_to>")
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


@mod_auth.route("/register", )
def create_user():
    data = request.get_json()

    hashed_password = generate_password_hash(data["password"], method="sha256")

    new_user = User(
        public_id=str(uuid.uuid4()), name=data["name"], password=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "New user created!"})


@mod_auth.route("/login")
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


@mod_auth.route("/refresh", methods=["POST"])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    ret = {
        "access_token": create_access_token(identity=current_user),
        "refresh_token": create_refresh_token(identity=current_user),
    }
    return jsonify(ret), 200


@mod_auth.route("/user", methods=["GET"])
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


@mod_auth.route("/user/<int:user_id>", methods=["GET"])
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


@mod_auth.route("/user/<int:user_id>", methods=["DELETE"])
@jwt_required
def delete_user(user_id):

    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({"message": "No user found!"})

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted!"})


@mod_auth.route("/user/<int:user_id>/note", methods=["GET"])
@jwt_required
def get_all_notes(user_id):
    
    perm = Permission.query.filter_by(user_from=user_id, user_to=get_jwt_identity()).first()

    if not perm:
        if user_id != get_jwt_identity():
            return jsonify({"message": "Permission denied!"})

    if user_id == get_jwt_identity() or perm.get_perm is True:

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


@mod_auth.route("/user/<int:user_id>/note/<note_id>", methods=["GET"])
@jwt_required
def get_one_note(user_id, note_id):
    perm = Permission.query.filter_by(user_from=user_id, user_to=get_jwt_identity()).first()

    if not perm:
        if user_id != get_jwt_identity():
            return jsonify({"message": "Permission denied!"})
    
    if user_id == get_jwt_identity() or perm.get_perm is True:

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


@mod_auth.route("/user/<int:user_id>/note", methods=["POST"])
@jwt_required
def create_note(user_id):
    data = request.get_json()

    perm = Permission.query.filter_by(user_from=user_id, user_to=get_jwt_identity()).first()

    if not perm:
        if user_id != get_jwt_identity():
            return jsonify({"message": "Permission denied!"})

    if user_id == get_jwt_identity() or perm.post_perm is True :

        new_note = Note(text=data["text"], checked=False, user_id=user_id)
        db.session.add(new_note)
        db.session.commit()
    else:
        return jsonify({"message": "Permission denied!"})

    return jsonify({"message": "Note created!"})


@mod_auth.route("/user/<int:user_id>/note/<note_id>", methods=["PUT"])
@jwt_required
def complete_note(user_id, note_id):
    perm = Permission.query.filter_by(user_from=user_id, user_to=get_jwt_identity()).first()

    if not perm:
        if user_id != get_jwt_identity():
            return jsonify({"message": "Permission denied!"})

    if user_id == get_jwt_identity() or perm.put_perm is True:
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()

        if not note:
            return jsonify({"message": "No note found!"})

        note.checked = True
        db.session.commit()
    else:
        return jsonify({"message": "Permission denied!"})

    return jsonify({"message": "Note has been checked!"})


@mod_auth.route("/user/<int:user_id>/note/<note_id>", methods=["DELETE"])
@jwt_required
def delete_note(user_id, note_id):
    perm = Permission.query.filter_by(user_from=user_id, user_to=get_jwt_identity()).first()

    if not perm:
        if user_id != get_jwt_identity():
            return jsonify({"message": "Permission denied!"})

    if user_id == get_jwt_identity() or perm.put_perm is True:
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()

        if not note:
            return jsonify({"message": "No note found!"})

        db.session.delete(note)
        db.session.commit()
    else:
        return jsonify({"message": "Permission denied!"})


    return jsonify({"message": "Note deleted!"})