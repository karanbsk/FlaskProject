#app/main.py
from flask import request,redirect, url_for, Blueprint, render_template, flash  
from app.models import User
from app import db
import re
from datetime import datetime
from app.utils import validate_password

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', title="Flask App", message="Hello from a dynamic template!")


#--------------------USER WEBPAGE--------------------
@main.route('/ui')
def ui():
    
    users = User.query.order_by(User.username.asc()).all()
    return render_template('ui.html', title="UI Page", message="Welcome to the UI Page!", users=users)

#CREATE
@main.route('/ui/create_user', methods=['POST'])
def create_user_ui():
    from werkzeug.security import generate_password_hash
    
    username=request.form['username']
    email=request.form['email']
    password=request.form['password']
    confirm_password=request.form['confirm_password']
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return render_template(
            "ui.html", 
            users=User.query.all(), 
            error_message="Invalid email address.", 
            open_modal="create",
            form_data={"username": username, "email": email}   #preserve
        )
        
    is_valid, message = validate_password(password, confirm_password)
    if not is_valid:
        return render_template(
            "ui.html", 
            users=User.query.all(), 
            error_message=message, 
            open_modal="create",
            form_data={"username": username, "email": email}   #preserve
        )    
        
    try:
        hashed_pwd = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        return render_template(
            "ui.html",
            users=User.query.all(),
            error_message=f'Error creating user: {str(e)}',
            open_modal="create",
            form_data={"username": username, "email": email}   #preserve
        )
        
    return redirect(url_for('main.ui'))

# RESET PASSWORD
@main.route('/ui/reset_password/<int:user_id>', methods=['POST'])
def reset_password_ui(user_id):
    user = User.query.get_or_404(user_id)

    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Password validation
    is_valid, message = validate_password(new_password, confirm_password)
    if not is_valid:
        users = User.query.order_by(User.username.asc()).all()
        return render_template(
            "ui.html",
            users=users,
            error_message=message,
            open_modal_id=user.id
        )
    try:
        # Set the new password with validation
        user.set_password(new_password)

        # If it was a "force_password_change" root user, mark it complete
        if user.force_password_change:
            user.force_password_change = False  

            db.session.commit()
            flash('Password reset successfully!', 'success')  
            return redirect(url_for('main.ui'))
        
    except ValueError as ve:
        db.session.rollback()
        users = User.query.order_by(User.username.asc()).all()
        return render_template(
            "ui.html",
            users=users,
            error_message=str(ve),
            open_modal_id=user.id
        )  


#DELETE
@main.route('/ui/delete_user/<int:user_id>', methods=['POST'])
def delete_user_ui(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.is_root:
        flash('Cannot delete root user!', 'danger')
        return redirect(url_for('main.ui'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('main.ui'))

#------------------DASHBOARD WEBPAGE------------------
@main.route('/dashboard')
def dashboard():
    import os, socket, time, psutil, requests
    from flask import current_app
    from zoneinfo import ZoneInfo
    from sqlalchemy import text

    # App environment
    env_name = current_app.config.get("APP_CONFIG", "development")

    # Server time
    ist = ZoneInfo('Asia/Kolkata')
    server_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
    hostname = os.getenv("APP_HOSTNAME", socket.gethostname())

    # Database health check (basic + latency + row count)
    try:
        start = time.time()
        row_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        latency = round((time.time() - start) * 1000, 2)  # ms
        db_status = {"status": "Up", "latency": latency, "rows": row_count}
    except Exception as e:
        current_app.logger.error(f"DB connection error: {e}")
        db_status = {"status": "Down", "latency": None, "rows": None}

    # App health (static for now, self check always "Healthy")
    app_health = "Healthy"

    # Container details
    container_id = "N/A"
    try:
        with open("/proc/self/cgroup", "r") as f:
            for line in f:
                if "docker" in line:
                    container_id = line.strip().split("/")[-1][:12]
    except Exception:
        pass
    container_image = os.getenv("APP_IMAGE", "unknown")
    uptime = f"{(time.time() - psutil.boot_time())/3600:.2f} hrs"

    container_info = {
        "id": container_id,
        "image": container_image,
        "uptime": uptime
    }

    # System usage
    system_usage = {
        "cpu": psutil.cpu_percent(interval=1),
        "memory": psutil.virtual_memory().percent
    }

    # API health checks
    api_health = {}
    base_url = os.getenv("APP_BASE_URL", "http://localhost:5000")
    endpoints = ["/", "/ui", "/api/users"]
    for ep in endpoints:
        try:
            r = requests.get(base_url + ep, timeout=2)
            api_health[ep] = "Healthy" if r.status_code == 200 else f"Error {r.status_code}"
        except Exception as e:
            api_health[ep] = f"Down ({str(e)})"

    return render_template(
        'dashboard.html',
        env_name=env_name,
        server_time=server_time,
        hostname=hostname,
        db_status=db_status,
        app_health=app_health,
        container_info=container_info,
        system_usage=system_usage,
        api_health=api_health
    )


#------------------DASHBOARD JSON ENDPOINT------------------
@main.route('/dashboard/data')
def dashboard_data():
    import os, socket, time, psutil, requests
    from flask import current_app, jsonify
    from sqlalchemy import text
    from zoneinfo import ZoneInfo

    env_name = current_app.config.get("APP_CONFIG", "development")

    ist = ZoneInfo('Asia/Kolkata')
    server_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
    hostname = os.getenv("APP_HOSTNAME", socket.gethostname())

    try:
        start = time.time()
        row_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        latency = round((time.time() - start) * 1000, 2)
        db_status = {"status": "Up", "latency": latency, "rows": row_count}
    except Exception as e:
        db_status = {"status": "Down", "latency": None, "rows": None}

    container_id = "N/A"
    try:
        with open("/proc/self/cgroup", "r") as f:
            for line in f:
                if "docker" in line:
                    container_id = line.strip().split("/")[-1][:12]
    except Exception:
        pass
    container_image = os.getenv("APP_IMAGE", "unknown")
    uptime = f"{(time.time() - psutil.boot_time())/3600:.2f} hrs"

    system_usage = {
        "cpu": psutil.cpu_percent(interval=1),
        "memory": psutil.virtual_memory().percent
    }

    api_health = {}
    base_url = os.getenv("APP_BASE_URL", "http://localhost:5000")
    for ep in ["/", "/ui", "/api/users"]:
        try:
            r = requests.get(base_url + ep, timeout=2)
            api_health[ep] = "Healthy" if r.status_code == 200 else f"Error {r.status_code}"
        except Exception:
            api_health[ep] = "Down"

    return jsonify({
        "env_name": env_name,
        "server_time": server_time,
        "hostname": hostname,
        "db_status": db_status,
        "container_info": {"id": container_id, "image": container_image, "uptime": uptime},
        "system_usage": system_usage,
        "api_health": api_health,
        "app_health": "Healthy"
    })

#------------------ABOUT WEBPAGE------------------
@main.route('/about')
def about():
    return render_template('about.html', title="About", message="About this Flask Application")
