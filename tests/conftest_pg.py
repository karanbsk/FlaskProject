# tests/conftest_pg.py
import os
import subprocess
import pytest
from sqlalchemy import create_engine
#from sqlalchemy_utils import database_exists, create_database  # optional
from app import create_app, db as _db

def build_database_url_from_env():
    # prefer explicit DATABASE_URL, else build from POSTGRES_* vars
    url = os.environ.get("DATABASE_URL") or os.environ.get("TEST_DATABASE_URL")
    if url:
        return url
    user = os.environ.get("POSTGRES_USER")
    pwd = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB")
    if not (user and pwd and db):
        raise RuntimeError("DATABASE_URL or POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB must be set")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

@pytest.fixture(scope="session")
def pg_url():
    return build_database_url_from_env()

@pytest.fixture(scope="session")
def pg_engine(pg_url):
    engine = create_engine(pg_url)
    # Optionally create DB if you have privileges:
    # if not database_exists(engine.url):
    #     create_database(engine.url)
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

    _db.init_app(app)

    with app.app_context():
        # Prefer running alembic migrations in project root; fallback to create_all
        try:
            subprocess.check_call(["alembic", "upgrade", "head"])
        except Exception:
            _db.create_all(bind=pg_engine)

        yield app

        # teardown: drop all tables
        _db.drop_all(bind=pg_engine)

@pytest.fixture(scope="function")
def db_session(pg_app, pg_engine):
    """
    Provide a SQLAlchemy session wrapped in a SAVEPOINT/transaction that rolls back after test.
    This keeps DB schema for session but isolates test data.
    """
    conn = pg_engine.connect()
    trans = conn.begin()
    # bind a session to the connection
    options = dict(bind=conn, binds={})
    sess = _db.create_scoped_session(options=options)
    _db.session = sess
    try:
        yield sess
    finally:
        sess.remove()
        trans.rollback()
        conn.close()

@pytest.fixture(scope="function")
def pg_client(pg_app, db_session):
    # ensure tests use pg_app (with DB) and transactional db_session is active
    return pg_app.test_client()
