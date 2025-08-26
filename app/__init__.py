# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.blueprints.main import main
from config import DevelopmentConfig, ProductionConfig, TestingConfig

#initialize db
db = SQLAlchemy()

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__,template_folder='templates', static_folder='static')
    app.config.from_object(config_class)

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
