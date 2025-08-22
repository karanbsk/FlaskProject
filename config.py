#config.py
import os
from flask_sqlalchemy import SQLAlchemy

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY',"dev-insecure-key")
    #Add common configs here (e.g., SESSSION_COOKIE_SECURE, etc.)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev_database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG = False
    # Add production-specific configs here (e.g., database URI, etc.)
    
class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    # Add testing-specific configs here (e.g., test database URI, etc.)
    