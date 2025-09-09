# tests/conftest.py
import os
import subprocess
import pytest
from sqlalchemy import create_engine
from app import create_app, db as _db
from config import build_postgres_uri
from sqlalchemy.orm import sessionmaker, scoped_session

@pytest.fixture(scope="session")
def pg_url():
    url = build_postgres_uri()
    if not url:
        raise RuntimeError("DATABASE_URL must be set to run Postgres tests (e.g. from .env.test)")
    return url

@pytest.fixture(scope="session")
def pg_engine(pg_url):
    engine = create_engine(pg_url)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def pg_app(pg_url, pg_engine):
    # create app bound to the Postgres test DB
    config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": pg_url, "WTF_CSRF_ENABLED": False}
    try:
        app = create_app(config)
    except TypeError:
        app = create_app()
        app.config.update(config)

    with app.app_context():
        # Prefer running alembic migrations; fallback to create_all
        try:
            subprocess.check_call(["alembic", "upgrade", "head"])
        except Exception:
            _db.metadata.create_all(bind=pg_engine)

        yield app

        # teardown: drop all tables
        _db.metadata.drop_all(bind=pg_engine)

@pytest.fixture
def pg_client(pg_app, db_session):
    return pg_app.test_client()

# Optional: per-test transaction (fast isolation)
@pytest.fixture(scope="function")
def db_session(pg_app, pg_engine):
    """Begin a transaction and rollback at test end for isolation."""
    conn = pg_engine.connect()
    trans = conn.begin()
    Session = sessionmaker(bind=conn) 
    sess = scoped_session(Session)
    old_session = getattr(_db, 'session', None)
    _db.session = sess
    try:
        yield sess
    finally:
        try:
            sess.remove()
        except Exception:
            pass
        trans.rollback()
        conn.close()
        _db.session = old_session

def make_compliant_password(min_length: int = 12) -> str:
    import string
    import random
    """
    Returns a password that meets:
      - at least min_length characters
      - at least one uppercase, one lowercase, one digit, one special char
    """
    if min_length < 8:
        min_length = 12

    lowers = string.ascii_lowercase
    uppers = string.ascii_uppercase
    digits = string.digits
    specials = "@$!%*?&#"

    # ensure at least one of each required class
    password_chars = [
        random.choice(lowers),
        random.choice(uppers),
        random.choice(digits),
        random.choice(specials),
    ]

    # fill the rest with a mix of allowed characters
    all_chars = lowers + uppers + digits + specials
    remaining = max(min_length - len(password_chars), 0)
    password_chars += [random.choice(all_chars) for _ in range(remaining)]

    # shuffle so positions aren't predictable, then join
    random.shuffle(password_chars)
    return "".join(password_chars)

# def _password_is_valid(pw: str) -> bool:
#     import re
#     if len(pw) < 8:
#         return False
#     if not re.search(r"[A-Z]", pw): return False
#     if not re.search(r"[a-z]", pw): return False
#     if not re.search(r"\d", pw): return False
#     if not re.search(r"@$!%*?&#", pw): return False
#     return True

@pytest.fixture
def user_factory(db_session):
    from app.services.users_service import create_user as svc_create_user

    def make_user(username="u", email=None, password=None, create=True):
        if email is None:
            email = f"{username}@example.com"
        if password is None:
            password = make_compliant_password(min_length=12)
        if not create:
            return {"username": username, "email": email, "password": password}
        
        user = svc_create_user(username=username, email=email, password=password)
        db_session.add(user)
        db_session.commit()
        return user, password, email
    return make_user
