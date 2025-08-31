# tests/conftest.py
import os
import pytest
from app import create_app, db

os.environ['APP_CONFIG'] = 'testing'  # Ensure testing config is used

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
