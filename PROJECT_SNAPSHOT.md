# PROJECT SNAPSHOT

**Project Path:** /home/runner/work/FlaskProject/FlaskProject

**Generated on:** 2025-08-23 07:44:51

## Folder Structure

```
FlaskProject/
    PROJECT_SNAPSHOT.md
    requirements.txt
    README.md
    wsgi.py
    create_db.py
    config.py
    app/
        __init__.py
        blueprints/
            main.py
            __init__.py
        templates/
            base.html
            index.html
        static/
            style.css
    tools/
        snapshot_generator.py
    .github/
        workflows/
            snapshot.yml
```

## Key Code Snippets

### PROJECT_SNAPSHOT.md

```md

```

### requirements.txt

```txt
blinker==1.9.0
click==8.2.1
colorama==0.4.6
Flask==3.1.2
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.2
python-dotenv==1.1.1
Werkzeug==3.1.3

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
from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    print("Database created successfully!")
```

### config.py

```py
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
    
```

### app/__init__.py

```py
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
        <h1>Hello, Flask!</h1>
        <p>Your Blueprint + Application Factory setup is working perfectly.</p>
    </div>
    <div class="footer">
        Powered by Flask | Config: Development
    </div>
</body>
</html>

```

### app/static/style.css

```css
body{

    font-family: 'Courier New', Courier, monospace;margin: 2rem; }
h1 { margin-bottom: .5rem; }
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
