# create_db.py
import os
from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    config_name = os.getenv("APP_CONFIG", "development").lower()
    print(f"Database created for {config_name.upper()} successfully!")
