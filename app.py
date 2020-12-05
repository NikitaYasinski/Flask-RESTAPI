from flask import Flask, jsonify, request
import json
from flaskext.mysql import MySQL
import os
from dotenv import load_dotenv
from flask_cors import CORS

project_folder = os.path.expanduser('~/app')  # adjust as appropriate
load_dotenv(os.path.join(project_folder, '.env'))

app = Flask(__name__)
CORS(app)
mysql = MySQL()
 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = os.getenv('DB_USER')
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('DB_PASSWORD')
app.config['MYSQL_DATABASE_DB'] = os.getenv('DB_NAME')
app.config['MYSQL_DATABASE_HOST'] = os.getenv('DB_HOST')
mysql.init_app(app)

@app.route('/users', methods=['GET', 'POST'])
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

@app.route('/users/<int:user_id>/notes', methods=['GET'])
def get_note(user_id):
    conn = mysql.connect()
    cur = conn.cursor()
    resultValue = cur.execute(f'''
    SELECT user_list.id, user_list.name, user_notes.id, user_notes.title, user_notes.content FROM user_list 
    INNER JOIN user_notes ON user_list.id = user_notes.user_id 
    WHERE user_list.id={user_id}
    ''')
    user2 = cur.fetchall()
    
    data = {}
    keys = ('user_id', 'user_name', 'note_id', 'title', 'content')
    for i in range(len(user2)):
        result = {}
        for k, v in zip(keys, user2[i]):
            result[k] = v
        data[f'note {i + 1}'] = result
    return json.dumps(data, indent=4)

@app.route('/')
def index():
    return 'Hello World!'

if __name__ == "__main__":
    app.run(port=5000, debug=True, host='0.0.0.0')
