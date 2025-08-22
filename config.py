#config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY',"dev-insecure-key")
    #Add common configs here (e.g., SESSSION_COOKIE_SECURE, etc.)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Add production-specific configs here (e.g., database URI, etc.)
    
class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    # Add testing-specific configs here (e.g., test database URI, etc.)
    