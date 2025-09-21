# migrations/env.py
import logging
from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from flask import current_app
import os
from sqlalchemy import create_engine

# ensure project root is on sys.path (useful if alembic invoked from different CWD)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the Flask app factory and DB extension after adding project root
try:
    # create_app must be importable from app (adjust if your factory lives elsewhere)
    from app import create_app
    from app import db as _db
except Exception:
    # fallback: try importing current app context elements; this keeps env.py resilient
    try:
        from app import db as _db
    except Exception:
        _db = None

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# fileConfig(config.config_file_name)
# logger = logging.getLogger('alembic.env')

cfg_name = config.config_file_name or 'alembic.ini'
project_root_cfg = os.path.join(str(PROJECT_ROOT), 'alembic.ini')
migrations_cfg = os.path.join(os.path.dirname(__file__), cfg_name)

if os.path.exists(project_root_cfg):
    # Prefer alembic.ini in project root (one level above migrations/)
    fileConfig(project_root_cfg)
    config.config_file_name = project_root_cfg
elif os.path.exists(migrations_cfg):
    # fallback: migrations/alembic.ini (only used if root file missing)
    fileConfig(migrations_cfg)
    config.config_file_name = migrations_cfg
else:
    # Don't raise here; use basic logging so alembic can continue and give clearer errors later.
    logging.basicConfig()
    logging.getLogger().warning(
        "alembic.ini not found at %s or %s. Using basic logging. "
        "Place alembic.ini in project root or set ALEMBIC_DB_URL/DATABASE_URL.",
        project_root_cfg, migrations_cfg
    )


def get_engine():
    """
    Return a sqlalchemy Engine using Flask-Migrate/Flask-SQLAlchemy extension.
    Compatible with Flask-SQLAlchemy <3 and >=3.

    This tries the imported _db first (if available), then current_app/migrate.
    """
    # Prefer the directly-imported db object if present (works without app context)
    if _db is not None:
        try:
            # Flask-SQLAlchemy <3
            return _db.get_engine()
        except Exception:
            try:
                # Flask-SQLAlchemy >=3
                return _db.engine
            except Exception:
                pass

    # If that didn't work, try to use current_app (requires app context)
    try:
        if current_app and 'migrate' in current_app.extensions:
            # Flask-Migrate exposes the db via the migrate extension
            return current_app.extensions['migrate'].db.get_engine()
    except Exception:
        pass

    raise RuntimeError("Could not determine SQLAlchemy engine for Alembic. Ensure app is importable and configured.")


def get_engine_url():
    """Return engine URL string for alembic (escape percent signs for config)."""
    engine = get_engine()
    try:
        return engine.url.render_as_string(hide_password=False).replace('%', '%%')
    except Exception:
        return str(engine.url).replace('%', '%%')

alembic_db_url = os.environ.get("ALEMBIC_DB_URL") or os.environ.get("DATABASE_URL")
if alembic_db_url:
    config.set_main_option("sqlalchemy.url", alembic_db_url)
#if not config.get_main_option("sqlalchemy.url"):
#    config.set_main_option("sqlalchemy.url", get_engine_url())
    
# Ensure the Flask app is created so current_app is available when alembic runs
def ensure_flask_app():
    """
    Create and return a Flask app instance and ensure an application context
    is active so Flask-SQLAlchemy can access current_app and extensions.
    """
    # Prefer to return an existing application if present
    try:
        existing = current_app._get_current_object()
        if existing is not None:
            return existing
    except Exception:
        # no current app; proceed to create one
        pass

    # Call the app factory. If your factory accepts a config name from env,
    # prefer that (e.g. APP_CONFIG). Adjust as needed.
    app = create_app()

    # Push an application context so current_app and extensions are available
    ctx = app.app_context()
    ctx.push()

    # Return the app (context stays active for the alembic run lifetime)
    return app


# create or get the Flask app so we can get the DB/engine
app = ensure_flask_app()

# set the sqlalchemy.url in alembic config so offline mode works
config.set_main_option('sqlalchemy.url', get_engine_url())

# target_metadata for 'autogenerate'
try:
    # Prefer migrate extension's db (requires app context)
    target_db = app.extensions.get('migrate').db
except Exception:
    # if flask-migrate not registered, try the imported _db
    target_db = _db

def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas.get(None)
    return getattr(target_db, 'metadata', None)

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logging.logger.info('No changes in schema detected.')

    conf_args = {}
    conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
