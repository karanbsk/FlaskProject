# tests/conftest.py  <-- copy/paste and save (overwrite)
import os
import tempfile
import pytest

@pytest.fixture(scope="function")
def app():
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_uri = f"sqlite:///{temp_db_path}"

    # make sure the environment is set before we import create_app (defense in-depth)
    os.environ['SQLALCHEMY_DATABASE_URI'] = db_uri
    os.environ['DATABASE_URL'] = db_uri

    print("\n=== TEST DB URI ===", db_uri, "\n")

    # import after env var set so factory sees env if it reads it.
    from app import create_app, db as _db

    desired_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": db_uri,
        "WTF_CSRF_ENABLED": False,
    }

    # call factory (works either way)
    try:
        app = create_app(desired_config)
    except TypeError:
        app = create_app()
        app.config.update(desired_config)

    # IMPORTANT: ensure Flask-SQLAlchemy binds to our sqlite engine
    try:
        _db.init_app(app)
    except Exception:
        pass

    with app.app_context():
        _db.create_all()
        yield app

    try:
        os.remove(temp_db_path)
    except Exception:
        pass

@pytest.fixture
def client(app):
    return app.test_client()
