# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.blueprints.main import main
from config import DevelopmentConfig, ProductionConfig, TestingConfig

#initialize db
db = SQLAlchemy()

# Map string to config class
CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}

def create_app():
        
    # Load config based on environment variable
    config_name = os.getenv("APP_CONFIG", "development").lower()
    config_class = CONFIG_MAP.get(config_name, DevelopmentConfig)
    
    #Initialize Flask App
    app = Flask(__name__,template_folder='templates', static_folder='static')
    app.config.from_object(config_class)
    
    app.debug = True if config_name == "development" else False
    
    #initialize db with app
    db.init_app(app)
    
    #Blueprints
    app.register_blueprint(main)
    
    @app.context_processor
    def inject_env():
        return dict(env_name=app.config.get("ENV_NAME", "Production"))

    #Error Handlers
    @app.errorhandler(404)
    def not_found(__):
        return ("404 Error - Page Not Found", 404)
    
    @app.errorhandler(500)
    def server_error(__):
        return ("500 Error - Internal Server Error", 500)
    
    
    return app
