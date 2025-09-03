from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import os, json
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'defaultsecret')

USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f) or create_initial_admin()
    return create_initial_admin()

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def create_initial_admin():
    users = {
        "saf": {
            "password": generate_password_hash("12345"),
            "role": "admin"
        }
    }
    save_users(users)
    return users

users = load_users()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and user['role'] == role and check_password_hash(user['password'], password):
            session['user'] = username
            session['role'] = role
            return redirect(url_for('home'))
        else:
            error = "Invalid credentials or role mismatch."
    return render_template('login.html', role=role, error=error)

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('home.html', username=session['user'], role=session['role'])

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    message = ""
    if request.method == 'POST':
        new_user = request.form['new_user'].strip()
        new_pass = request.form['new_pass']
        new_role = request.form['new_role']
        if not new_user or not new_pass or not new_role:
            message = "Please fill in all fields."
        elif new_user in users:
            message = "User already exists."
        else:
            users[new_user] = {
                'password': generate_password_hash(new_pass),
                'role': new_role
            }
            save_users(users)
            message = f"User '{new_user}' added successfully."
    return render_template('admin.html', users=users, message=message)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user' not in session:
        return redirect(url_for('index'))

    message = ""
    if request.method == 'POST':
        current = request.form['current']
        new = request.form['new']
        confirm = request.form['confirm']
        user = users[session['user']]
        if not check_password_hash(user['password'], current):
            message = "Current password is incorrect."
        elif new != confirm:
            message = "New passwords do not match."
        else:
            users[session['user']]['password'] = generate_password_hash(new)
            save_users(users)
            message = "Password changed successfully."
    return render_template('change_password.html', message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080)
