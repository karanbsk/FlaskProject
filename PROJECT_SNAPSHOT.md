# PROJECT SNAPSHOT

**Project Path:** G:\Karan\python_projects\FlaskProject

**Generated on:** 2025-08-23 10:47:22

## Folder Structure

```
FlaskProject/
    .env
    config.py
    create_db.py
    PROJECT_SNAPSHOT.md
    config.py
    README.md
    requirements.txt
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
    instance/
        dev.db
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
#config.py
import os
from flask_sqlalchemy import SQLAlchemy

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY',"dev-insecure-key")
    #Add common configs here (e.g., SESSSION_COOKIE_SECURE, etc.)
    ENV_NAME="Production" # default

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev_database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENV_NAME="Development" # used in templates
    
class ProductionConfig(Config):
    DEBUG = False
    # Add production-specific configs here (e.g., database URI, etc.)
    ENV_NAME="Production" # used in templates
    
class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    # Add testing-specific configs here (e.g., test database URI, etc.)
    
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

### PROJECT_SNAPSHOT.md

```md

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

### tools\snapshot_generator.py

```py
import os
from datetime import datetime

# === CONFIGURATION ===
PROJECT_ROOT = "G:/Karan/python_projects/FlaskProject"  # change to your project root
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "PROJECT_SNAPSHOT.md")

EXCLUDE_FOLDERS = {'.git', 'flask_venv', '__pycache__', '.env'}
EXCLUDE_FILES = {'.gitignore'}
EXCLUDE_CODE_SNIPPETS_IN_FOLDERS = {'.github'}
ALLOWED_EXTENSIONS = {'.py', '.html', '.css', '.js', '.json', '.md', '.txt'}

# === HELPER FUNCTION TO GENERATE FOLDER STRUCTURE ===
def generate_folder_structure(root_dir, exclude=None):
    exclude = exclude or set()
    tree_lines = []

    for root, dirs, files in os.walk(root_dir):
        # Remove excluded dirs
        dirs[:] = [d for d in dirs if d not in exclude]
        depth = root.replace(root_dir, '').count(os.sep)
        indent = '    ' * depth
        folder_name = os.path.basename(root)
        tree_lines.append(f"{indent}{folder_name}/")
        for f in files:
            if f not in EXCLUDE_FILES:
                tree_lines.append(f"{indent}    {f}")
    return tree_lines

# === HELPER FUNCTION TO COLLECT CODE SNIPPETS ===
def collect_code_snippets(root_dir, exclude=None, allowed_ext=None):
    exclude = exclude or set()
    allowed_ext = allowed_ext or ALLOWED_EXTENSIONS
    snippets = []
    for root, dirs, files in os.walk(root_dir):
        # Remove excluded dirs
        dirs[:] = [d for d in dirs if d not in exclude]
        # Skip folders that shouldn't have code snippets
        if any(skip in root.split(os.sep) for skip in EXCLUDE_CODE_SNIPPETS_IN_FOLDERS):
            continue
        for f in files:
            if f in EXCLUDE_FILES:
                continue
            if os.path.splitext(f)[1] in allowed_ext:
                file_path = os.path.join(root, f)
                rel_path = os.path.relpath(file_path, root_dir)
                snippets.append((rel_path, file_path))
    return snippets

# === GENERATE SNAPSHOT ===
def generate_snapshot():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# PROJECT SNAPSHOT\n\n")
        f.write(f"**Project Path:** {PROJECT_ROOT}\n\n")
        f.write(f"**Generated on:** {timestamp}\n\n")
        
        f.write("## Folder Structure\n\n")
        folder_tree = generate_folder_structure(PROJECT_ROOT, EXCLUDE_FOLDERS)
        f.write("```\n")
        for line in folder_tree:
            f.write(f"{line}\n")
        f.write("```\n\n")

        f.write("## Key Code Snippets\n\n")
        code_files = collect_code_snippets(PROJECT_ROOT, exclude=EXCLUDE_FOLDERS)
        for rel_path, full_path in code_files:
            f.write(f"### {rel_path}\n\n")
            ext = os.path.splitext(rel_path)[1][1:]  # use extension as code type
            f.write(f"```{ext}\n")
            try:
                with open(full_path, 'r', encoding='utf-8') as code_file:
                    f.write(code_file.read())
            except Exception as e:
                f.write(f"# Could not read file: {e}\n")
            f.write("\n```\n\n")

        f.write("## Project Overview & Commands\n\n")
        f.write("- Python version: 3.x\n")
        f.write("- Virtual Environment: flask_venv\n")
        f.write("- Database: SQLite (dev_database.db)\n")
        f.write("- To create DB: `python create_db.py`\n")
        f.write("- To run app:\n")
        f.write("```powershell\n")
        f.write("$env:FLASK_APP=\"wsgi\"\n")
        f.write("$env:FLASK_ENV=\"development\"\n")
        f.write("flask run\n")
        f.write("```\n\n")
        
        f.write("## Next Planned Features\n\n")
        f.write("- Add Flask-Login authentication\n")
        f.write("- Add CI/CD via GitHub Actions\n")
        f.write("- Environment-based configuration\n")

    print(f"Snapshot generated successfully at {OUTPUT_FILE}")

# === RUN SCRIPT ===
if __name__ == "__main__":
    generate_snapshot()

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
