# app/models.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import re



class User(db.Model):
    __tablename__ = 'users'
      
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    is_root = db.Column(db.Boolean, default=False, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    force_password_change = db.Column(db.Boolean, default=False, nullable=False)
    
    def set_password(self, password):
        #  Validation before hashing
        if not self.validate_password(password):
            raise ValueError(
                "Password must be at least 8 characters long, contain one uppercase, one lowercase, one digit, and one special character."
            )
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def validate_password(password):
        """Validates password against policy"""
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"[0-9]", password):
            return False
        if not re.search(r"[@$!%*?&#]", password):
            return False
        return True
    
    def __init__(self, username, email, password=None, is_root=False):
        self.username = username
        self.email = email.lower()
        self.is_root = is_root
        if password:  # only set if provided
            self.set_password(password)

   
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }    

    def __repr__(self):
        return f'User(id={self.id}, username={self.username}, email={self.email})'
