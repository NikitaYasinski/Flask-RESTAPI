from flask import Flask, jsonify, request, make_response
import json
from flaskext.mysql import MySQL
import os
from dotenv import load_dotenv
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import uuid
import datetime

project_folder = os.path.expanduser('~/app')  # adjust as appropriate
load_dotenv(os.path.join(project_folder, '.env'))

app = Flask(__name__)
CORS(app)
mysql = MySQL()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = os.getenv('DB_USER')
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('DB_PASSWORD')
app.config['MYSQL_DATABASE_DB'] = os.getenv('DB_NAME')
app.config['MYSQL_DATABASE_HOST'] = os.getenv('DB_HOST')
mysql.init_app(app)

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return json.dumps({'message': 'a valid token is missing'})

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            conn = mysql.connect()
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM admins WHERE public_id={data['public_id']} LIMIT 1")
            current_user = cur.fetchall()
        except:
            return jsonify({'message': 'token is invalid'})

        return f(current_user, *args, **kwargs)
    return decorator

@app.route('/register', methods=['GET', 'POST'])
def signup_user():  
    data = request.get_json()  

    hashed_password = generate_password_hash(data['password'], method='sha256')
    
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(f'''
    INSERT INTO admins(public_id, name, password, admin) VALUES ({str(uuid.uuid4())}, '{data['name']}', '{hashed_password}', FALSE)
    ''')
    conn.commit()    

    return jsonify({'message': 'registered successfully'})

@app.route('/login', methods=['GET', 'POST'])  
def login_user(): 
 
    auth = request.authorization   

    if not auth or not auth.username or not auth.password:  
        return make_response('could not verify', 401, {'WWW.Authentication': 'Basic realm: "login required"'})    
  
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM admins WHERE name='{auth.username}' LIMIT 1")
    user = cur.fetchall()
     
    if check_password_hash(user[3], auth.password):  
        token = jwt.encode({'public_id': user[1], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])  
        return jsonify({'token' : token.decode('UTF-8')}) 

    return make_response('could not verify',  401, {'WWW.Authentication': 'Basic realm: "login required"'})

@app.route('/users', methods=['GET', 'POST'])
@token_required
def manage_users():
    
    if request.method == 'GET':
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM user_list")
        user1 = cur.fetchall()
        data = {}
        keys = ['id', 'name', 'city']
        for i in range(len(user1)):
            result = {}
            for k, v in zip(keys, user1[i]):
                result[k] = v
            data[f'user {i + 1}'] = result
        if data == {}:
            return json.dumps({'message': 'there are no users'})
        return json.dumps(data, indent=4)
    
    if request.method == 'POST':
        conn = mysql.connect()
        cur = conn.cursor()
        user_name = request.json['name']
        user_city = request.json['city']
        cur.execute(f"INSERT INTO user_list(name, city) VALUES ('{user_name}', '{user_city}')")
        conn.commit()
        return json.dumps({'message': 'success'})


@app.route('/users/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def manage_user(id):
    
    if request.method == 'GET':
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM user_list WHERE id={id}")
        user1 = cur.fetchall()
        data = {}
        keys = ['id', 'name', 'city']
        for i in range(len(user1)):
            result = {}
            for k, v in zip(keys, user1[i]):
                result[k] = v
            data[f'user {i + 1}'] = result
        if data == {}:
            return json.dumps({'message': f'there is no user with id={id}'})
        return json.dumps(data, indent=4)
    
    if request.method == 'DELETE':
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM user_list WHERE id={id}")
        conn.commit()
        return json.dumps({'message': 'success'})

    if request.method == 'PUT':
        conn = mysql.connect()
        cur = conn.cursor()
        user_name = request.json['name']
        user_city = request.json['city']
        cur.execute(f"UPDATE user_list SET name='{user_name}', city='{user_city}' WHERE id={id}")
        conn.commit()
        return json.dumps({'message': 'success'})

@app.route('/users/<int:user_id>/notes', methods=['GET', 'POST'])
@token_required
def manage_notes(user_id):
    
    if request.method == 'GET':
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(f'''
        SELECT user_list.name, user_notes.title, user_notes.content FROM user_list 
        INNER JOIN list_notes ON user_list.id=list_notes.user_id
        INNER JOIN user_notes ON list_notes.note_id=user_notes.id
        WHERE user_list.id={user_id}
        ''')
        user2 = cur.fetchall()
    
        data = {}
        keys = ('user_name', 'title', 'content')
        for i in range(len(user2)):
            result = {}
            for k, v in zip(keys, user2[i]):
                result[k] = v
            data[f'note {i + 1}'] = result
        if data == {}:
            return json.dumps({'message': 'there are no notes'})    
        return json.dumps(data, indent=4)

    if request.method == 'POST':
        conn = mysql.connect()
        cur = conn.cursor()
        note_title = request.json['title']
        note_content = request.json['content']
        cur.execute(f'''
        INSERT INTO user_notes(title, content) VALUES ('{note_title}', '{note_content}')
        ''')
        cur.execute(f'''
        INSERT INTO list_notes(user_id) VALUES ('{user_id}')
        ''')
        conn.commit()
        return json.dumps({'message': 'success'})

@app.route('/users/<int:user_id>/notes/<int:note_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def manage_note(user_id, note_id):
    
    if request.method == 'GET':
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(f'''
        SELECT user_list.name, user_notes.title, user_notes.content FROM user_list 
        INNER JOIN list_notes ON user_list.id=list_notes.user_id
        INNER JOIN user_notes ON list_notes.note_id=user_notes.id
        WHERE user_list.id={user_id} AND user_notes_id={note_id}
        ''')
        user3 = cur.fetchall()
    
        data = {}
        keys = ('user_name', 'title', 'content')
        for i in range(len(user3)):
            result = {}
            for k, v in zip(keys, user3[i]):
                result[k] = v
            data[f'note {i + 1}'] = result
        if data == {}:
            return json.dumps({'message': 'error'})
        return json.dumps(data, indent=4)
    
    if request.method == 'DELETE':
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM list_notes WHERE user_id={user_id} AND note_id={note_id}")
        cur.execute(f"DELETE FROM user_notes WHERE id={note_id}")
        conn.commit()
        return json.dumps({'message': 'success'})

    if request.method == 'PUT':
        conn = mysql.connect()
        cur = conn.cursor()
        note_title = request.json['title']
        note_content = request.json['content']
        cur.execute(f'''
        UPDATE user_notes SET title='{note_title}', content='{note_content}' WHERE id={note_id}
        ''')
        conn.commit()
        return json.dumps({'message': 'success'})

if __name__ == "__main__":
    app.run(port=5000, debug=True, host='0.0.0.0')
