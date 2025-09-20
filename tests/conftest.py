# tests/conftest.py
import os
import subprocess
import pytest
from pathlib import Path
from app import create_app, db

# load .env.test if present (helps CI/local)
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env.test", override=True)

# app imports (adapt if your project uses different names)
from app import create_app, db as _db
from config import build_postgres_uri  # if you have it, otherwise use env var
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Utility to create a compliant random password (used by factory)
def make_compliant_password(min_length: int = 12) -> str:
    import string, random
    if min_length < 8:
        min_length = 12
    lowers = string.ascii_lowercase
    uppers = string.ascii_uppercase
    digits = string.digits
    specials = "@$!%*?&#"
    password_chars = [random.choice(lowers), random.choice(uppers), random.choice(digits), random.choice(specials)]
    all_chars = lowers + uppers + digits + specials
    remaining = max(min_length - len(password_chars), 0)
    password_chars += [random.choice(all_chars) for _ in range(remaining)]
    random.shuffle(password_chars)
    return "".join(password_chars)

# Build PG URL; prefer explicit env var, then config builder
def _build_pg_url():
    url = os.environ.get("DATABASE_URL") or os.environ.get("TEST_DATABASE_URL")
    if url:
        return url
    try:
        url = build_postgres_uri()
    except Exception:
        url = None
    if url:
        return url
    # fallback to POSTGRES_* env vars
    user = os.environ.get("POSTGRES_USER")
    pwd = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST", "db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB")
    

    if user and pwd and db:
        return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
    return None

@pytest.fixture(scope="session")
def pg_url():
    url = build_postgres_uri()
    print(f"DEBUG: what's in build_postgres_uri():{build_postgres_uri()}")
    print(f"DEBUG: pg_url:{url}")
    if not url:
        raise RuntimeError("No Postgres URL available (set DATABASE_URL or TEST_DATABASE_URL or POSTGRES_* env vars)")
    return url

@pytest.fixture(scope="session")
def pg_engine(pg_url):
    engine = create_engine(pg_url)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def app():
     """
    Session-scoped Flask app for fast unit tests.
    Use an in-memory SQLite DB so unit-level tests that touch db work.
    """
     cfg = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }
     try:
        _app = create_app(cfg)
     except TypeError:
        _app = create_app()
        _app.config.update(cfg)

    # Avoid calling init_app twice. If the app factory already registered the extension,
    # init_app may raise or re-register. So attempt init_app but ignore duplicate errors.
     try:
        _db.init_app(_app)
     except Exception:
        # If it's already been initialized by create_app, ignore the error.
        pass

    # Create schema once for the session under app context
     with _app.app_context():
        try:
            _db.create_all()
        except Exception:
            # If create_all fails (e.g. different metadata), raise so you can inspect
            raise

     yield _app

    # teardown - drop tables and remove session
     with _app.app_context():
        try:
            _db.session.remove()
        except Exception:
            pass
        try:
            _db.drop_all()
        except Exception:
            pass



@pytest.fixture(autouse=True)
def _maybe_push_app_ctx(request):
    """
    Autouse fixture that pushes the appropriate app context for tests that touch Flask globals / db.
    - For integration/pg tests use pg_app (Postgres-backed app).
    - For unit/other tests use app (in-memory sqlite app).
    """
    markers = ("unit", "integration", "functional", "regression", "pg")
    if not any(m in request.keywords for m in markers):
        # do nothing for tests not marked
        yield
        return

    # Choose the app fixture depending on test type:
    # - integration or pg markers -> use 'pg_app' fixture (postgres-backed)
    # - otherwise -> use 'app' fixture (sqlite in-memory)
    if ("integration" in request.keywords) or ("pg" in request.keywords):
        app_fixture_name = "pg_app"
    else:
        app_fixture_name = "app"

    # request.getfixturevalue will raise if fixture missing; wrap to provide clearer message
    try:
        app_obj = request.getfixturevalue(app_fixture_name)
    except Exception as e:
        raise RuntimeError(
            f"Required fixture '{app_fixture_name}' not available for test '{request.node.name}': {e}"
        )

    # push context for the chosen app
    with app_obj.app_context():
        yield



import os
from subprocess import run, CalledProcessError, CompletedProcess
from pathlib import Path

@pytest.fixture(scope="session")
def pg_app(pg_url, pg_engine):
    """
    Session-scoped Flask app bound to Postgres DB for integration tests.
    Prefer migrations via alembic; otherwise fall back to create_all.
    """
    
    cfg = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": pg_url, "WTF_CSRF_ENABLED": False}
    try:
        _app = create_app(cfg)
    except TypeError:
        _app = create_app()
        _app.config.update(cfg)

    # Safe init_app usage: try but ignore duplicate registration errors
    try:
        _db.init_app(_app)
    except Exception:
        pass
    from sqlalchemy import inspect

# drop any existing tables first to ensure alembic migrations apply cleanly
    
    # --- Prepare to run alembic (explicit config path + env) ---
    project_root = Path(__file__).resolve().parent.parent
    alembic_ini = project_root / "alembic.ini"
    alembic_cmd = ["alembic", "-c", str(alembic_ini), "upgrade", "head"]

    proc_env = os.environ.copy()
    proc_env["ALEMBIC_DB_URL"] = pg_url
    proc_env["DATABASE_URL"] = pg_url
    proc_env["SQLALCHEMY_DATABASE_URI"] = pg_url
    proc_env["PYTHONPATH"] = str(project_root) + os.pathsep + proc_env.get("PYTHONPATH", "")
    
    import sqlalchemy as _sa

    with pg_engine.connect() as conn:
        inspector = inspect(conn)
        # Get all public tables, but exclude alembic_version which alembic maintains
        existing_tables = [t for t in inspector.get_table_names(schema='public') if t != 'alembic_version']

        if existing_tables:
            print("Dropping existing application tables before alembic upgrade:", existing_tables)
            # Use a transaction and DROP TABLE ... CASCADE for each table to ensure a clean slate.
            # We use sa.text to avoid quoting issues and execute on the raw connection.
            for tbl in existing_tables:
                try:
                    conn.execute(_sa.text(f'DROP TABLE IF EXISTS "{tbl}" CASCADE'))
                except Exception as exc:
                    # Log and re-raise so you can see failures in CI/test output
                    print(f"Failed to drop table {tbl}: {exc}")
                    raise
        
    # Run migrations (or fallback to create_all)
    try:
        res: CompletedProcess = run(
            alembic_cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            env=proc_env,
        )
        if res.stdout:
            print("Alembic stdout:", res.stdout)
        if res.stderr:
            print("Alembic stderr:", res.stderr)

    except FileNotFoundError:
        print("Alembic CLI not found on PATH; falling back to create_all()")
        _db.metadata.create_all(bind=pg_engine)

    except CalledProcessError as e:
        print("Alembic command failed with return code", e.returncode)
        if getattr(e, "stdout", None):
            print("alembic stdout:\n", e.stdout)
        if getattr(e, "stderr", None):
            print("alembic stderr:\n", e.stderr)
        print("Falling back to _db.metadata.create_all(bind=pg_engine)")
        _db.metadata.create_all(bind=pg_engine)

    # --- Yield the app to tests ---
    yield _app

    # --- Teardown: drop schema (best-effort) ---
    with _app.app_context():
        from app.models import User
        _db.session.query(User).filter(User.username.in_(["root", "admin"])).delete(synchronize_session=False)
        _db.session.commit()


@pytest.fixture(scope="function")
def db_session(pg_app, pg_engine):
    """
    Provide a SQLAlchemy session wrapped in a SAVEPOINT/transaction that rolls back after each test.
    Keeps DB schema for the session but isolates test data per test.
    """
    conn = pg_engine.connect()
    trans = conn.begin()
    Session = sessionmaker(bind=conn)
    sess = scoped_session(Session)
    old_session = getattr(_db, "session", None)
    _db.session = sess
    try:
        yield sess
    finally:
        try:
            sess.remove()
        except Exception:
            pass
        try:
            if trans.is_active:
                trans.rollback()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        _db.session = old_session

@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

@pytest.fixture(scope="function")
def pg_client(pg_app, db_session):
    return pg_app.test_client()

# Simple user factory for tests (creates user in db_session by default)
@pytest.fixture
def user_factory(db_session):
    from werkzeug.security import generate_password_hash
    import secrets
    from app.models import User

    def _factory(username=None, email=None, password=None, create=True):
        username = username or f"user_{secrets.token_hex(4)}"
        email = email or f"{username}@example.com"
        raw_password = password or make_compliant_password()
        pw_hash = generate_password_hash(raw_password)
        if create:
            user = User(username=username, email=email)
            # If your model has set_password, call it; else set a field
            if hasattr(user, "set_password"):
                user.set_password(raw_password)
            else:
                user.password = pw_hash
            db_session.add(user)
            db_session.commit()
            return (user, raw_password, email)
        return {"username": username, "email": email, "password": raw_password}

    return _factory

from sqlalchemy import MetaData

@pytest.fixture(scope="session", autouse=True)
def recreate_database(pg_url, pg_engine):
    """
    Create/tear-down the test schema for the whole session.
    - Lazy-imports app and _db to avoid pytest collection collisions.
    - Ensures model modules are imported so metadata is populated.
    - Create tables via _db.metadata.create_all(bind=pg_engine).
    """
    # lazy imports
    from app import create_app, db as _db
    import importlib

    # Create app and ensure test DB URL
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI=pg_url)

    ctx = app.app_context()
    ctx.push()

    try:
        # Import models to populate metadata (adjust module path if needed)
        try:
            importlib.import_module("app.models")
        except Exception:
            # If your models use multiple modules, import them here or ensure app factory imports them
            pass

        # Create schema using the metadata attached to the app's SQLAlchemy instance.
        # Prefer metadata.create_all (avoids SQLAlchemy.create_all signature mismatch)
        _db.metadata.create_all(bind=pg_engine)

        yield

    finally:
        # best-effort cleanup
        try:
            _db.session.remove()
        except Exception:
            pass
        try:
            _db.metadata.drop_all(bind=pg_engine)
        except Exception:
            pass
        ctx.pop()
