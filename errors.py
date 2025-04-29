import os
import subprocess
import pickle
import hashlib
import sqlite3
from flask import Flask, request

app = Flask(__name__)

# 1. Hardcoded secret
API_KEY = "12345-abcdef-SECRET"

# 2. Insecure use of subprocess with user input
@app.route('/ping', methods=['GET'])
def ping():
    host = request.args.get('host')
    return subprocess.check_output(f"ping -c 1 {host}", shell=True)  # command injection

# 3. Insecure deserialization
@app.route('/load', methods=['POST'])
def load():
    data = request.data
    obj = pickle.loads(data)  # unsafe deserialization
    return str(obj)

# 4. SQL injection
@app.route('/user')
def get_user():
    username = request.args.get('username')
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = '%s'" % username)  # SQL injection
    result = cursor.fetchall()
    return str(result)

# 5. Weak cryptography
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()  # weak hash function

# 6. Use of eval
@app.route('/eval')
def run_eval():
    code = request.args.get('code')
    return str(eval(code))  # arbitrary code execution

# 7. Missing TLS verification
def fetch_url(url):
    import requests
    r = requests.get(url, verify=False)  # disables SSL certificate verification
    return r.text

# 8. Potential XSS (Flask doesn't auto-escape plain strings)
@app.route('/greet')
def greet():
    name = request.args.get('name', '')
    return f"<h1>Hello {name}</h1>"  # unsanitized user input in HTML
