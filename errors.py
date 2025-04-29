import os
import subprocess
import pickle
import hashlib
import sqlite3
import logging
import yaml
from flask import Flask, request

app = Flask(__name__)

aws_access_key = "ASIAU4FLKAWMOKDDKJEM"
aws_secret_key = "IQoJb3JpZ2luX2VjEAQaCXVzLXdlc3QtMiJHMEUCIQD/ut0uj4po+gkWbWnSRu6lot2Zuvsy4DX+zUXIb8nE07iGNiJpaB07/BkFnO6Ayu0jUUpT6OQa+VKqxkTbZTnc/gahYhhkoSO5xrz40mlq4SELu+h8XmUyJOuackr1YKcj/VdrqBuLZfp79fPoqbAz4eJNgNHa2ELfsdebD/2HFFYR/ga3iqipHtOsr7v/B1k60fXY06w3wSFnakjusMvF0uxbuk6lfZA1Jx1nx3zOJ646tlKhf+gJuhhQuWwQpPl3iN3B5P/AZKWXbMEoEy05vROovhZHOPxh8mbOyCCWS7njdHXNUklmfFsUiix4sIb0Aj9m0lvUeU1Lj3g4GTSM9udTexbXd9Pj9wCJLvFmI8ykfLkPgtj3jWNpw3OWav8PBUR4BNM51vbRZ8BIaHCV/fs7HZPapRlFgppZ3luCEws0/aYu0+/ur58zqsqp1rc/5rChf5VnaIMOvTgbcGOqYB2I6SOpuQ9NSKkRqpz41Onk55I2Orv1fYfN+brUdGpJfshXwoABDbDMaMzz1GhayF/4L6XVsT8Ag5w0brcZaQNKK6Dp0bgU0E3LL+X9d/qIfszSwlG+QAAwr/YZCMzI3K4IEjo7pnotioAtIEiM730qX+X6hqjVK0eucjkE4RixJWfyqGTxshpN8wSdk7XiwMaOHGHNUJXUvxdZOSDZrKUzKABNxMXg=="

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


# Command Injection vulnerability
def list_files(directory):
    os.system(f"ls {directory}")

# Path Traversal vuln
def read_file(filename):
    with open(f"/var/data/{filename}", "r") as f:
        return f.read()
    
def divide(a, b):
    try:
        return a / b
    except Exception as e:
        return str(e)
    
def auth(user, pw):
    logging.info(f"Authenticating {user} with password {pw}")


def load_config(yaml_str):
    return yaml.load(yaml_str)