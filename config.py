# config.py
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

# Determine environment variables
config_name = os.getenv("APP_CONFIG", "development").lower()

if config_name == "development":
    os.environ.setdefault("POSTGRES_USER", "postgres")
    os.environ.setdefault("POSTGRES_PASSWORD", "postgres") 
    os.environ.setdefault("POSTGRES_DB", "flaskdb") # Dev DB name
    os.environ.setdefault("POSTGRES_HOST", "db") # Docker service name
    os.environ.setdefault("POSTGRES_PORT", "5432") 

# Handle SECRET_KEY centrally
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if config_name == "production":
        raise ValueError("Production SECRET_KEY must be set as an environment variable!")
    else:
        SECRET_KEY = "dev-secret-key"  # Safe for dev/testing/CI

# Helper function to build Postgres URI        
def build_postgres_uri():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB")
    if all([user, password, host, port, db_name]):
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    return None

class Config:
    """
    Base configuration:
    - Centralized SECRET_KEY handling
    - Secure defaults for production
    """
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Security Defaults
    SESSION_COOKIE_SECURE = True  # Cookies only sent over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    REMEMBER_COOKIE_SECURE = True # Cookies only sent over HTTPS
    REMEMBER_COOKIE_HTTPONLY = True # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = "Lax"  # CSRF protection
    CSRF_COOKIE_SECURE = True  # CSRF cookie only sent over HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)  # 1 hour
    
    # Centralized logging level
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    
    ENV_NAME = "Base"
    # Add other security settings as needed
    # e.g., CSRF_COOKIE_SECURE, PERMANENT_SESSION_LIFETIME, etc.

class DevelopmentConfig(Config):
    DEBUG = True
    ENV_NAME = "Development"
    SESSION_COOKIE_SECURE = False  # Allow for local dev
    REMEMBER_COOKIE_SECURE = False  # Allow for local dev
    CSRF_COOKIE_SECURE = False  # Allow for local dev
    SQLALCHEMY_DATABASE_URI = build_postgres_uri() or f"sqlite:///{os.path.join(basedir, 'dev_database.db')}"
    SQLALCHEMY_ECHO = True # Log SQL queries for debugging

class ProductionConfig(Config):
    DEBUG = False
    ENV_NAME = "Production"
    SQLALCHEMY_DATABASE_URI = build_postgres_uri() 
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("Postgres URI must be set in Production!") # Ensure DB URI is set


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    ENV_NAME = "Testing"
    SESSION_COOKIE_SECURE = False  
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URI',
        f"sqlite:///{os.path.join(basedir, 'test_database.db')}"
    )
    
"""
Configuration Loader:
- Reads APP_CONFIG from environment (default: development)
- Maps to DevelopmentConfig, ProductionConfig, or TestingConfig
- Use get_config() in app factory and scripts for dynamic environment handling
"""
# Map string to config class    
CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}

# Function to get config class based on environment variable
def get_config():
    """Return the appropriate config class based on APP_CONFIG environment variable."""
    config_name = os.getenv("APP_CONFIG", "development").lower()
    return CONFIG_MAP.get(config_name, DevelopmentConfig)    

# Helper function to get config name
def get_config_name():
    return os.getenv("APP_CONFIG", "development").lower()
