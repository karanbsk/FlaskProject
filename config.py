# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Determine environment (default: development)
FLASK_ENV = os.environ.get("FLASK_ENV", "development")

# Handle SECRET_KEY centrally
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if FLASK_ENV == "production":
        raise ValueError("Production SECRET_KEY must be set as an environment variable!")
    else:
        SECRET_KEY = "dev-secret-key"  # Safe for dev/testing/CI
        
class Config:
    """
    Base configuration:
    - Centralized SECRET_KEY handling
    - Secure defaults for production
    """
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True  # Cookies only sent over HTTPS
    REMEMBER_COOKIE_SECURE = True
    ENV_NAME = "Base"
    # Add other security settings as needed
    # e.g., CSRF_COOKIE_SECURE, PERMANENT_SESSION_LIFETIME, etc.

class DevelopmentConfig(Config):
    DEBUG = True
    ENV_NAME = "Development"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DEV_DATABASE_URI',
        f"sqlite:///{os.path.join(basedir, 'dev_database.db')}"
    )
    SESSION_COOKIE_SECURE = False  # Allow insecure cookies for local dev

class ProductionConfig(Config):
    DEBUG = False
    ENV_NAME = "Production"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'PROD_DATABASE_URI',
        f"sqlite:///{os.path.join(basedir, 'prod_database.db')}"
    )


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    ENV_NAME = "Testing"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DATABASE_URI',
        f"sqlite:///{os.path.join(basedir, 'test_database.db')}"
    )
    SESSION_COOKIE_SECURE = False

    
