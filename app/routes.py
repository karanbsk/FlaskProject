# app/routes.py
from flask import jsonify, Blueprint, request, render_template, flash, redirect, url_for
from app.services import users_service
from sqlalchemy.exc import IntegrityError
import re
from app import db
from app.models import User
from werkzeug.security import generate_password_hash


user_bp = Blueprint('user_bp', __name__, url_prefix='/api/users')

EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")
USERNAME_RE = re.compile(r'^[A-Za-z0-9._-]{3,50}$')  # allow only safe chars
SUSPICIOUS_USERNAME_RE = re.compile(r"(?:'|--|;|\bOR\b|\bAND\b|\bUNION\b|\bSELECT\b)", re.I)

# GET all users
@user_bp.route("", methods=['GET'])
def list_users_api():
    users = users_service.list_users()
    return jsonify([u.to_dict() for u in users]), 200

# CREATE user
@user_bp.route("", methods=['POST'])
def create_user_api():
    # Accept either JSON or form data
    json_data = request.get_json(silent=True)
    is_json = json_data is not None

    if is_json:
        data = json_data
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''
        confirm = data.get('confirm_password') or ''
    else:
        form = request.form
        username = (form.get('username') or '').strip()
        email = (form.get('email') or '').strip()
        password = form.get('password') or ''
        confirm = form.get('confirm_password') or ''
        
    # early suspicious username check (keeps UI behaviour)
    if username and SUSPICIOUS_USERNAME_RE.search(username):
        if is_json:
            return jsonify({"errors": ["Invalid username."]}), 422
        form_data = {'username': username, 'email': email or ''}
        return render_template(
            'ui.html',
            users=User.query.order_by(User.created_at.desc()).all(),
            form_data=form_data,
            error_message="Invalid username.",
            open_modal='create'
        ), 422

    # validations
    errors = []
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
        if is_json:
            return jsonify({"errors": errors}), 422
        form_data = {'username': username, 'email': email}
        return render_template(
            'ui.html',
            users=User.query.order_by(User.created_at.desc()).all(),
            form_data=form_data,
            error_message=' '.join(errors),
            open_modal='create'
        ), 422

    # create user
    try:
        user = User(username=username, email=email)
        user.password = password  # model will validate and hash
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        msg = 'User with that username or email already exists.'
        if is_json:
            return jsonify({"errors": [msg]}), 422
        form_data = {'username': username, 'email': email}
        return render_template(
            'ui.html',
            users=User.query.order_by(User.created_at.desc()).all(),
            form_data=form_data,
            error_message=msg,
            open_modal='create'
        ), 422

    # Success response
    if is_json:
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "message": "User created successfully."
        }), 201
    if request.path.startswith("/api/") or request.is_json:
        return jsonify({"id": user.id, "username": user.username}), 201, {"Location": f"/api/users/{user.id}"}

    flash('User created successfully.', 'success')
    return redirect("/api/users")



# RESET password
@user_bp.route("/reset_password", methods=["POST"])
def reset_password_api():
    data = request.get_json() or {}
    try:
        users_service.reset_password(data.get("username"), data.get("new_password"))
        return jsonify({"message": "Password reset successful"}), 200
    except users_service.UserNotFound as e:
        return jsonify({"error": str(e)}), 404

# Option A: delete by username via POST JSON (simple for tests)
@user_bp.route("/delete", methods=["POST"])
def delete_user_api():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400
    try:
        users_service.delete_user(username)
        return jsonify({"message": "User deleted successfully"}), 200
    except users_service.UserNotFound as e:
        return jsonify({"error": str(e)}), 404
    except users_service.RootDeletionError as e:
        return jsonify({"error": str(e)}), 400
