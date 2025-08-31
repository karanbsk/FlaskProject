#app/main.py
from flask import request,redirect, url_for, Blueprint, render_template, flash  
from app.models import User
from app import db
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', title="Flask App", message="Hello from a dynamic template!")


#--------------------USER WEBPAGE--------------------
@main.route('/ui')
def ui():
    
    users = User.query.all()
    return render_template('ui.html', title="UI Page", message="Welcome to the UI Page!", users=users)

#CREATE
@main.route('/ui/create_user', methods=['POST'])
def create_user_ui():
    from werkzeug.security import generate_password_hash
    username=request.form['username']
    email=request.form['email']
    password=request.form['password']
    new_user = User(username=username, email=email, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    flash('User created successfully!', 'success')
    return redirect(url_for('main.ui'))

#EDIT
@main.route('/ui/edit_user/<int:user_id>', methods=['POST'])
def edit_user_ui(user_id):
    user = User.query.get_or_404(user_id)
    user.username = request.form['username']
    user.email = request.form['email']
    db.session.commit()
    flash('User updated successfully!', 'success')
    return redirect(url_for('main.ui'))

#DELETE
@main.route('/ui/delete_user/<int:user_id>', methods=['POST'])
def delete_user_ui(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('main.ui'))

#------------------DASHBOARD WEBPAGE------------------
@main.route('/dashboard')
def dashboard():
    import os
    from flask import current_app
    from zoneinfo import ZoneInfo
    import socket
    from sqlalchemy import text

    # App environment
    env_name = current_app.config.get("APP_CONFIG", "development")
    
    # Server info
    ist = ZoneInfo('Asia/Kolkata')
    server_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
    hostname = os.getenv("APP_HOSTNAME", socket.gethostname())

    try:
        db.session.execute(text("SELECT 1"))
        db_status = "Up"
    except Exception as e:
        current_app.logger.error(f"DB connection error: {e}")
        db_status = "Down"

    return render_template(
        'dashboard.html',
        env_name=env_name,
        server_time=server_time,
        hostname=hostname,
        db_status=db_status
    )
#------------------ABOUT WEBPAGE------------------
@main.route('/about')
def about():
    return render_template('about.html', title="About", message="About this Flask Application")
