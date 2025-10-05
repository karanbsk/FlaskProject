#app/services/users_service.py
from app.models import User
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Union, Dict, Any

# Custom Exceptions for error handling
class UserAlreadyExists(Exception):...
class UserNotFound(Exception):...
class RootDeletionError(Exception):...


def list_users():
    return User.query.order_by(User.username.asc()).all()

def create_user(username:str, email:str, password:str):
    raw_password = password
    if not username or not email or not raw_password:
        raise ValueError("username, email, password are required")
    if User.query.filter((User.username == username) | (User.email == email)).first():
        raise UserAlreadyExists("Username or email already exists.")
    
    new_user = User(username=username, email=email)
    new_user.set_password(raw_password)
    db.session.add(new_user)
    db.session.commit()
    return new_user


def reset_password(username:str, new_password:str):
    user = User.query.filter_by(username=username).first()
    if not user:
        raise UserNotFound("User not found.")
    
    user.set_password(new_password)
    db.session.commit()
    return user


def delete_user(identifier: Union[int, str]):
    """
    Delete a user by username (str) or id (int).
    Returns True on success, False if user not found.
    Raises RootDeletionError if attempted on a root user.
    """
    # Try numeric id first
    user = None
    if isinstance(identifier, int):
        user =db.session.get(User, identifier)
    else:
        user = User.query.filter_by(username=identifier).first()

    if not user:
        # Test-friendly return value (instead of raising)
        return False

    if getattr(user, "is_root", False):
        raise RootDeletionError("Root user cannot be deleted.")

    db.session.delete(user)
    db.session.commit()
    return True


def hash_password(password: str) -> str:
    """Return a salted hash for the given password."""
    if password is None:
        raise ValueError("password required")
    return generate_password_hash(password)


def verify_password(hashed: str, password: str) -> bool:
    """Verify that the password matches the given hash."""
    if not hashed or password is None:
        return False
    return check_password_hash(hashed, password)

import logging

logger = logging.getLogger(__name__)

def update_user(user_id, updates: dict):
    """
    Update a user's fields and return the updated User instance.
    Returns None if user not found.
    Raises exceptions for unexpected failures (so tests surface errors).
    """
    if not isinstance(updates, dict):
        raise ValueError("updates must be a dict")

    # Use Session.get() to avoid Query.get() deprecation warning
    user = db.session.get(User, user_id)
    if user is None:
        logger.debug("update_user: user id %s not found", user_id)
        return None

    # Whitelist allowed fields
    allowed = {"username", "email", "password", "first_name", "last_name"}
    changed = False
    for key in allowed.intersection(updates.keys()):
        value = updates.get(key)
        if key == "password":
            if hasattr(user, "set_password") and callable(user.set_password):
                user.set_password(value)
            else:
                user.password = generate_password_hash(value)
            changed = True
        else:
            # optional validation: skip None/empty updates
            if value is not None:
                setattr(user, key, value)
                changed = True

    if not changed:
        # nothing to do, but return the user object so the caller can inspect it
        return user

    try:
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user
    except Exception as exc:
        # rollback and raise so tests fail fast with the real problem
        logger.exception("Failed to update user %s", user_id)
        db.session.rollback()
        raise
