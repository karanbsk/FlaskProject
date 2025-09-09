#app/services.users_service.py
from app.models import User
from app import db

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


def delete_user(username:str):
    user = User.query.filter_by(username=username).first()
    if not user:
        raise UserNotFound("User not found")
    if user.is_root:
        raise RootDeletionError("Root user cannot be deleted.")
    
    db.session.delete(user)
    db.session.commit()
    return True
