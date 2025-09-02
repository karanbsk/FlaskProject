# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import get_config
from flask_migrate import Migrate
import logging



#initialize db and migrate
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    
    config_class = get_config()
    
    if config_class.ENV_NAME == "Production":
        if not os.getenv("PROD_DATABASE_URI"):
            # Fallback for CI/CD environments without real DB
            print(" No PROD_DATABASE_URI found. Using SQLite for CI.")
            config_class.SQLALCHEMY_DATABASE_URI = "sqlite:///ci_test.db"
        else:
            config_class.init_db_uri() # Ensure DB URI is set for Production
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, 'templates')
    static_path = os.path.join(base_dir, 'static')
             
    #Initialize Flask App
    app = Flask(__name__,template_folder=template_path, static_folder=static_path)
    app.config.from_object(config_class)
    
    
    app.config.from_object(get_config())
     
     
    app.jinja_env.auto_reload = app.debug  
    # Force Flask/Jinja template auto-reload
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = app.config['TEMPLATES_AUTO_RELOAD']
    if app.debug:
        @app.before_request
        def clear_jinja_cache():
            app.jinja_env.cache = {}
    
    
    # Set up logging
    log_level = app.config.get("LOG_LEVEL", "INFO")
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    app.logger.addHandler(handler)
    
    
    #initialize extensions
    db.init_app(app)
    migrate.init_app(app, db) 
    
  
    #Import models, routes, blueprints
    from app.blueprints.main import main
    from app.routes import user_bp
    
    #Blueprints
    app.register_blueprint(main)
    app.register_blueprint(user_bp)
    
    @app.context_processor
    def inject_env():
        return dict(env_name=app.config.get("ENV_NAME", "Production"), debug=app.debug)
    
    @app.shell_context_processor
    def make_shell_context():
        from .models import User # Avoid circular import
        return {'db': db, 'User': User}

    #Error Handlers
    @app.errorhandler(404)
    def not_found(_):
        return ("404 Error - Page Not Found", 404)
    
    @app.errorhandler(500)
    def server_error(_):
        return ("500 Error - Internal Server Error", 500)
    
    
    return app
