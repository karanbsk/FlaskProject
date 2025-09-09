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
    return jsonify([[u.to_dict() for u in users]]), 200

# CREATE user
@user_bp.route("", methods=['POST'])
def create_user_api():
    form = request.form
    username = (form.get('username') or '').strip()
    if username and SUSPICIOUS_USERNAME_RE.search(username):
        # return 422 + render page with inline message so tests and UI see an error
        form_data = {'username': username, 'email': form.get('email', '')}
        return render_template(
            'ui.html',
            users=User.query.order_by(User.created_at.desc()).all(),
            form_data=form_data,
            error_message="Invalid username.",
            open_modal='create'
        ), 422
    email = (form.get('email') or '').strip()
    password = form.get('password') or ''
    confirm = form.get('confirm_password') or ''

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
        form_data = {'username': username, 'email': email}
        return render_template(
            'ui.html',
            users=User.query.order_by(User.created_at.desc()).all(),
            form_data=form_data,
            error_message=' '.join(errors),
            open_modal='create'
        ), 422

    try:
        pw_hash = generate_password_hash(password)
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
