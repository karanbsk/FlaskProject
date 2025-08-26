# PROJECT SNAPSHOT

**Project Path:** /mnt/g/Karan/python_projects/FlaskProject

**Generated on:** 2025-08-26 16:28:01

## Folder Structure

```
FlaskProject/
    .dockerignore
    requirements.txt
    docker-compose.prod.yml
    .flake8
    requirements-dev.txt
    PROJECT_SNAPSHOT.md
    config.py
    README.md
    wsgi.py
    Dockerfile
    docker-compose.dev.yml
    create_db.py
    tests/
        test_routes.py
        conftest.py
    .github/
        workflows/
            snapshot.yml
    app/
        __init__.py
        blueprints/
            main.py
            __init__.py
        static/
            style.css
        templates/
            base.html
            index.html
    tools/
        snapshot_generator.py
```

## Key Code Snippets

### requirements.txt

```txt
# Core framework
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
SQLAlchemy==2.0.34
python-dotenv==1.0.1
gunicorn>=21.2

```

### requirements-dev.txt

```txt
-r requirements.txt

# Development utilities
autopep8
flake8

# Testing
pytest
pytest-flask
tox
coverage

```

### PROJECT_SNAPSHOT.md

```md

```

### config.py

```py
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

    

```

### README.md

```md
# Flask Project

A simple Flask web application with a modular structure for scalability and maintainability.

---

## 🚀 Features
- Organized Flask app structure
- Templates and static files inside the `app` package
- Ready for future scaling with Blueprints

---

## 📂 Project Structure

```
FlaskProject/
│
├── app/
│   ├── __init__.py      # Initialize Flask app
│   ├── routes.py        # Application routes
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JS, Images
│
├── app.py               # Entry point
├── requirements.txt     # Dependencies
├── .gitignore           # Ignored files
└── README.md            # Documentation
```
---

## 🛠️ Setup & Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd FlaskProject
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate    # Linux / macOS
venv\Scripts\activate       # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application
```bash
flask run
```
By default, the app will run on `http://127.0.0.1:5000/`.

---

## ✅ Future Enhancements
- Add Blueprints for modular routes
- Implement Jinja2 templates with dynamic data
- Add database integration (SQLite, PostgreSQL)
- Implement authentication system
- Dockerize the application

---

## 🤝 Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📜 License
[MIT](LICENSE)

```

### wsgi.py

```py
#wsgi.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run() #Debug comes from config

```

### create_db.py

```py
# create_db.py
import os
from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    config_name = os.getenv("APP_CONFIG", "development").lower()
    print(f"Database created for {config_name.upper()} successfully!")

```

### tests/test_routes.py

```py
def test_index(client):
    response = client.get('/')
    
    assert response.status_code == 200
    assert b'Welcome to the Flask App!' in response.data

```

### tests/conftest.py

```py
import pytest
from app import create_app, db

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

```

### app/__init__.py

```py
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

```

### app/blueprints/main.py

```py
#app/routes.py
from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', title="Flask App", message="Hello from a dynamic template!")


```

### app/blueprints/__init__.py

```py



```

### app/static/style.css

```css
body{

    font-family: 'Courier New', Courier, monospace;margin: 2rem; }
h1 { margin-bottom: .5rem; }
```

### app/templates/base.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Flask Project{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
    <main class="container">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

### app/templates/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask Blueprint App</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            color: #333;
            text-align: center;
            padding: 50px;
        }
        h1 {
            color: #007bff;
        }
        .container {
            background: #fff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: inline-block;
            margin-top: 50px;
        }
        .footer {
            margin-top: 20px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to the Flask App!</h1>
        <p>Your Blueprint + Application Factory setup is working perfectly.</p>
    </div>
    <div class="footer">
        Powered by Flask {% if env_name == "Development" %}- This is a Dev Page{% endif %}
    </div>
</body>
</html>

```

## Project Overview & Commands

- Python version: 3.x
- Virtual Environment: flask_venv
- Database: SQLite (dev_database.db)
- To create DB: `python create_db.py`
- To run app:
```powershell
$env:FLASK_APP="wsgi"
$env:FLASK_ENV="development"
flask run
```

## Next Planned Features

- Add Flask-Login authentication
- Add CI/CD via GitHub Actions
- Environment-based configuration
