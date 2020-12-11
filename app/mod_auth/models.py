from app import db

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