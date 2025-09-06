# app/models.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import re



class User(db.Model):
    __tablename__ = 'users'
      
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    is_root = db.Column(db.Boolean, default=False, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    force_password_change = db.Column(db.Boolean, default=False, nullable=False)
    
    # ---- password handling ----
    @property
    def password(self):
        # make it write-only to avoid accidental read/leak
        raise AttributeError("Password is write-only.")
    
    @password.setter
    def password(self, raw_password: str):
        self.set_password(raw_password)
    
    def set_password(self, raw_password: str):
        if not self.validate_password(raw_password):
            raise ValueError(
                "Password must be at least 8 characters long, contain one uppercase, "
                "one lowercase, one digit, and one special character."
            )
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @staticmethod
    def validate_password(password):
        """Validates password against policy"""
        if len(password) < 8: return False
        
        if not re.search(r"[A-Z]", password): return False
        
        if not re.search(r"[a-z]", password): return False
        
        if not re.search(r"[0-9]", password): return False
        
        if not re.search(r"[@$!%*?&#]", password): return False
        
        return True

   
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            "is_root": bool(self.is_root),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }    

    def __repr__(self):
        return f'User(id={self.id}, username={self.username}, email={self.email})'
