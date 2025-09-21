# app/routes.py
from flask import jsonify, Blueprint, request, render_template, flash, redirect, url_for
from app.services import users_service
from sqlalchemy.exc import IntegrityError
import re
from app import db
from app.models import User
from werkzeug.security import generate_password_hash
from app.utils import validate_password
from flask import current_app


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
            return jsonify({"message": "Invalid username.", "errors": ["Invalid username."]}), 422
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
            return jsonify({"message": "Validation failed", "errors": errors}), 422
        form_data = {'username': username, 'email': email}
        return render_template(
            'ui.html',
            users=User.query.order_by(User.created_at.desc()).all(),
            form_data=form_data,
            error_message=' '.join(errors),
            open_modal='create'
        ), 422

    # create user (handle model-level validation cleanly)
    try:
        user = User(username=username, email=email)
        try:
            # model may raise ValueError or other exception types for policy violations
            user.password = password
        except Exception as ve:
            # Treat model validation errors as 422 (Unprocessable Entity)
            db.session.rollback()
            msg = str(ve) if ve is not None else "Password validation failed"
            if is_json:
                return jsonify({"message": "Password validation failed", "errors": {"password": msg}}), 422
            form_data = {'username': username, 'email': email}
            return render_template(
                'ui.html',
                users=User.query.order_by(User.created_at.desc()).all(),
                form_data=form_data,
                error_message=msg,
                open_modal='create'
            ), 422

        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        msg = 'User with that username or email already exists.'
        if is_json:
            return jsonify({"message": msg, "errors": [msg]}), 422
        form_data = {'username': username, 'email': email}
        return render_template(
            'ui.html',
            users=User.query.order_by(User.created_at.desc()).all(),
            form_data=form_data,
            error_message=msg,
            open_modal='create'
        ), 422
    except Exception as exc:
        # Unexpected error: log and return 500 for API clients
        db.session.rollback()
        current_app.logger.exception("Unexpected error creating user")
        if is_json:
            return jsonify({"message": "Internal error creating user"}), 500
        # HTML fallback: show a friendly message and return to UI
        form_data = {'username': username, 'email': email}
        return render_template(
            'ui.html',
            users=User.query.order_by(User.created_at.desc()).all(),
            form_data=form_data,
            error_message="Unexpected error creating user",
            open_modal='create'
        ), 500

    # Success response
    if is_json:
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "message": "User created successfully."
        }), 201

    # HTML flow (server-rendered): flash and redirect to UI page
    flash('User created successfully.', 'success')
    return redirect(url_for('main.ui'))



# RESET password
@user_bp.route("/<int:user_id>/reset_password", methods=["POST"])
def reset_password_api(user_id):
    data = request.get_json(silent=True) or request.form.to_dict()
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    # Validate
    is_valid, msg = validate_password(new_password, confirm_password)
    if not is_valid:
        return jsonify({"message": "Password validation failed", "errors": {"new_password": msg}}), 422

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found", "errors": {"user_id": "No user for given id"}}), 404

    try:
        user.set_password(new_password)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Password reset successful"}), 200
    except ValueError as ve:
        db.session.rollback()
        return jsonify({"message": str(ve)}), 422
    except Exception as e:
        current_app.logger.exception("Error resetting password")
        db.session.rollback()
        return jsonify({"message": "Internal error", "errors": {"exception": str(e)}}), 500

# Option A: delete by username via POST JSON (simple for tests)
@user_bp.route("/<int:user_id>", methods=["DELETE", "POST"])
def delete_user_api(user_id):
    user = User.query.get(user_id)
    if not user: return jsonify({"message":"User Not found"}), 404
    if user.is_root: return jsonify({"message":"Cannot delete root"}), 400
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting User", "errors": {"exception": str(e)}}), 500
    
