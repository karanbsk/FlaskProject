# app/models.py
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import re
from sqlalchemy import Column, DateTime, func

class User(db.Model):
    __tablename__ = 'users'
      
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    is_root = db.Column(db.Boolean, default=False, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
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
        if not isinstance(password, str):
            return False
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
    
    # add property setter/getter
    @property
    def password(self):
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, raw_password):
        # validate then set the hash using existing helper
        self.set_password(raw_password)
    
    def __init__(self, username=None, email=None, password=None, is_root=False, **kwargs):
        if username is not None:
            self.username = username
        if email is not None:
            self.email = email.lower()
        self.is_root = is_root
        if password:  # only set if provided
            self.password = password
        for k, v in kwargs.items():
            if k == 'password':
                continue
            setattr(self, k, v)  

   
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


from sqlalchemy import event

@event.listens_for(User, "before_delete")
def prevent_root_delete(mapper, connection, target):
    """
    Prevent removing the mandatory root user at ORM delete time.
    We import RootDeletionError from the service module lazily so we avoid
    circular imports. If the import fails, fall back to RuntimeError.
    """
    try:
        # Import here to reduce circular import risk
        from app.services.users_service import RootDeletionError
    except Exception:
        RootDeletionError = RuntimeError

    if getattr(target, "is_root", False):
        raise RootDeletionError("Deleting the root user is not permitted")
