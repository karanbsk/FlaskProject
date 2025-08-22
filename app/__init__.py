# app/__init__.py
from flask import Flask

def create_app(config_class="config.DevelopmentConfig"):
    app = Flask(__name__,template_folder='templates', static_folder='static')
    app.config.from_object(config_class)

    #Blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    #Error Handlers
    @app.errorhandler(404)
    def not_found(__):
        return ("404 Error - Page Not Found", 404)
    
    @app.errorhandler(500)
    def server_error(__):
        return ("500 Error - Internal Server Error", 500)
    
    
    return app