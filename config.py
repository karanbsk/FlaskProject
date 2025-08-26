# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Base configuration:
    - Use environment variables for secrets and database URIs
    - Provide sane defaults for development
    """
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-key')  # Must override in production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENV_NAME = "Production"  # Default
    SESSION_COOKIE_SECURE = True  # Cookies only sent over HTTPS
    REMEMBER_COOKIE_SECURE = True
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
    # SECRET_KEY must always come from environment in production

# Ensure production SECRET_KEY is set securely
if ProductionConfig.SECRET_KEY == 'dev-insecure-key':
    raise ValueError("Production SECRET_KEY must be set as an environment variable!")

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    ENV_NAME = "Testing"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DATABASE_URI',
        f"sqlite:///{os.path.join(basedir, 'test_database.db')}"
    )
    SESSION_COOKIE_SECURE = False

    
