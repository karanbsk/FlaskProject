#app/main.py
from flask import request,redirect, url_for, Blueprint, render_template, flash  
from app.models import User
from app import db
import re
from datetime import datetime
from app.comman_utils import validate_password
from app.services import users_service
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash


main = Blueprint('main', __name__)

USERNAME_RE = re.compile(r'^[A-Za-z0-9._-]{3,50}$')

@main.route('/')
def index():
    return render_template('index.html', title="Flask App", message="Hello from a dynamic template!")
#--------------------Alias Page--------------------
@main.route("/users", methods=["GET"])
def users_page_alias():
    """Alias for /ui returning the HTML user list (used by major tests)."""
    users = User.query.order_by(User.username.asc()).all()
    return render_template("ui.html", title="Users", users=users)

@main.route("/users/add", methods=["POST"])
def users_add_alias():
    """Accept form-data add user (UI). Delegates to users_service."""
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    # if client posted confirm password field in UI form:
    confirm = request.form.get("confirm_password", request.form.get("confirm", ""))

    # Basic validation for the UI path (keep UX-friendly behavior)
    if not username or not email or not password:
        flash("username, email and password are required", "danger")
        return redirect(url_for("main.users_page_alias"))
    try:
        users_service.create_user(username, email, password)
        flash("User added successfully", "success")
    except users_service.UserAlreadyExists:
        flash("Username or email already exists", "danger")
    except ValueError as ve:
        # Password policy error
        flash(str(ve), "danger")
    except Exception as e:
        # log if you have logger; keep UX safe
        flash("Unable to create user", "danger")
    return redirect(url_for("main.users_page_alias"))

@main.route("/users/reset_password", methods=["POST"])
def users_reset_password_alias():
    """Reset password by username (UI form)."""
    username = request.form.get("username", "").strip()
    new_password = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")
    if not username or not new_password:
        flash("username and new password are required", "danger")
        return redirect(url_for("main.users_page_alias"))
    try:
        users_service.reset_password(username, new_password)
        flash("Password reset successful", "success")
    except users_service.UserNotFound:
        flash("User not found", "danger")
    except ValueError as ve:
        flash(str(ve), "danger")
    return redirect(url_for("main.users_page_alias"))

@main.route("/users/delete", methods=["POST"])
def users_delete_alias():
    """Delete user by username (UI form)."""
    username = request.form.get("username", "").strip()
    if not username:
        flash("username is required", "danger")
        return redirect(url_for("main.users_page_alias"))
    try:
        users_service.delete_user(username)
        flash("User deleted successfully", "success")
    except users_service.UserNotFound:
        flash("User not found", "danger")
    except users_service.RootDeletionError:
        flash("Root user cannot be deleted", "danger")
    return redirect(url_for("main.users_page_alias"))

#--------------------USER WEBPAGE--------------------
@main.route('/ui')
def ui():
    
    users = User.query.order_by(User.username.asc()).all()
    return render_template('ui.html', title="UI Page", message="Welcome to the UI Page!", users=users)

#CREATE
@main.route('/ui/create_user', methods=['POST'])
def create_user_ui():
   
    form = request.form
    username = (form.get('username') or '').strip()
    email = (form.get('email') or '').strip()
    password = form.get('password') or ''
    confirm = form.get('confirm_password') or ''

    errors = []

    # Strong server-side validation (reject SQL injection-style input)
    if not username:
        errors.append("Username is required.")
    elif not USERNAME_RE.match(username):
        errors.append("Invalid username. Use 3-50 characters: letters, digits, . _ - only.")

    if not email or '@' not in email:
        errors.append("Invalid email address.")

    if len(password) < 8:
        errors.append("Password too short (min 8).")

    if password != confirm:
        errors.append("Passwords do not match.")

    if errors:
        # re-render the UI page with inline errors and keep create modal open
        form_data = {'username': username, 'email': email}
        return render_template(
            'ui.html',
            users=User.query.order_by(User.created_at.desc()).all(),
            form_data=form_data,
            error_message=' '.join(errors),
            open_modal='create'
        ), 422

    # Safe create using SQLAlchemy ORM (parameterized) and proper password hashing
    try:
        pw_hash = generate_password_hash(password)  # Werkzeug PBKDF2
        user = User(username=username, email=email, password_hash=pw_hash)
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        form_data = {'username': username, 'email': email}
        return render_template(
            'ui.html',
            users=User.query.order_by(User.created_at.desc()).all(),
            form_data=form_data,
            error_message='User with that username or email already exists.',
            open_modal='create'
        ), 422

    flash('User created successfully.', 'success')
    return redirect(url_for('main.users_list'))
        

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
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    from sqlalchemy import text
    from datetime import timezone
    # App environment
    env_name = current_app.config.get("APP_CONFIG", "development")
        

    # Server time
    ist = ZoneInfo('Asia/Kolkata')
    try:
        ist = ZoneInfo('Asia/Kolkata')
    except ZoneInfoNotFoundError:
    # Platform/CI may not have tzdata installed (Windows). Fallback to UTC.
        ist = timezone.utc

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
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    from datetime import datetime, timezone

    env_name = current_app.config.get("APP_CONFIG", "development")

    ist = ZoneInfo('Asia/Kolkata')
    try:
        ist = ZoneInfo('Asia/Kolkata')
    except ZoneInfoNotFoundError:
    # Platform/CI may not have tzdata installed (Windows). Fallback to UTC.
        ist = timezone.utc
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
