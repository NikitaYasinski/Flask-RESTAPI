from flask import Flask, jsonify
import json
from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv
from flask_cors import CORS

project_folder = os.path.expanduser('~/app')  # adjust as appropriate
load_dotenv(os.path.join(project_folder, '.env'))

app = Flask(__name__)
CORS(app)
app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
app.config['MYSQL_USER'] = os.getenv('DB_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('DB_NAME')

mysql = MySQL(app)

@app.route('/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
def get_user(id):
    cur = mysql.connection.cursor()
    resultValue = cur.execute(f"SELECT * FROM user_list WHERE id={id}")
    user1 = cur.fetchone()
    data = {}
    keys = ['id', 'name', 'city']
    for k, v in zip(keys, user1):
        data[k] = v
    return json.dumps(data)


@app.route('/users/<int:id>', meathods=['GET'])
def get_user(id):
    cur = mysql.connection.cursor()
    resultValue = cur.execute(f"SELECT * FROM user_list WHERE id={id}")
    user1 = cur.fetchone()
    data = {}
    keys = ['id', 'name', 'city']
    for k, v in zip(keys, user1):
        data[k] = v
    return json.dumps(data)

@app.route('/users/<int:user_id>/notes', methods=['GET'])
def get_note(user_id):
    cur = mysql.connection.cursor()
    resultValue = cur.execute(f'''
    SELECT user_list.id, user_list.name, user_notes.id, user_notes.title, user_notes.content FROM user_list 
    INNER JOIN user_notes ON user_list.id = user_notes.user_id 
    WHERE user_list.id={user_id}
    ''')
    user2 = cur.fetchall()
    
    data = {}
    keys = ('user_id', 'user_name', 'note_id', 'title', 'content')
    print(user2) 
    for i in range(len(user2)):
        result = {}
        for k, v in zip(keys, user2[i]):
            result[k] = v
        data[f'note {i}'] = result
    return json.dumps(data, indent=4)

@app.route('/')
def index():
    return 'Hello World!'

if __name__ == "__main__":
    app.run(port=5000, debug=True, host='0.0.0.0')
