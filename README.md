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
