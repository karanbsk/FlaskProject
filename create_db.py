# create_db.py
from config import get_config_name
from app import create_app, db


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        print(f"Database created for {get_config_name().upper()} successfully!")
