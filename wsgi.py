#wsgi.py
from app import create_app
import os

if not os.environ.get("APP_CONFIG"):
    os.environ["APP_CONFIG"] = "production"

app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) #Debug comes from config
