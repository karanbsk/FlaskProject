# debug_psycopg_connect_fixed.py
import os, sys, traceback, types, importlib

# Ensure tests' sqlite URI is visible to imports
os.environ.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')
os.environ.setdefault('DATABASE_URL', os.environ['SQLALCHEMY_DATABASE_URI'])

# Build a fake psycopg2 module with commonly imported attributes so imports succeed.
fake = types.ModuleType('psycopg2')

# basic attributes many libs expect
fake.paramstyle = 'pyformat'

# define a lightweight exception hierarchy used by DB libs
class FakeError(Exception): pass
class FakeDatabaseError(FakeError): pass
class FakeOperationalError(FakeError): pass

fake.Error = FakeError
fake.DatabaseError = FakeDatabaseError
fake.OperationalError = FakeOperationalError

# fake connect that prints a stacktrace and exits so we can find the caller
def _connect(*a, **kw):
    print("\n--- psycopg2.connect CALLED ---")
    print("Args:", a, "Kwargs:", kw)
    print("Stack (most recent call last):")
    traceback.print_stack()
    # stop here so it's obvious where connect was attempted
    raise SystemExit("psycopg2.connect() was called (see stack above)")

fake.connect = _connect

# Minimal submodules commonly imported
ext = types.ModuleType('psycopg2.extensions')
# some code expects this constant; set to any value
setattr(ext, 'ISOLATION_LEVEL_AUTOCOMMIT', 1)
setattr(ext, 'ISOLATION_LEVEL_READ_COMMITTED', 2)
setattr(ext, 'paramstyle', fake.paramstyle)
sys.modules['psycopg2.extensions'] = ext

extras = types.ModuleType('psycopg2.extras')
sys.modules['psycopg2.extras'] = extras

# Provide _psycopg, sometimes imported indirectly
_psycopg = types.ModuleType('psycopg2._psycopg')
sys.modules['psycopg2._psycopg'] = _psycopg

# Insert our fake module into sys.modules so imports use it
sys.modules['psycopg2'] = fake

print("Set SQLALCHEMY_DATABASE_URI =", os.environ['SQLALCHEMY_DATABASE_URI'])
print("Importing app package to trigger import-time DB usage...")

try:
    app_mod = importlib.import_module('app')   # triggers app.__init__ and subimports
    # If create_app exists, attempt to call it to exercise additional code paths:
    if hasattr(app_mod, 'create_app'):
        try:
            print("Calling create_app() (no args)...")
            app_mod.create_app()
        except TypeError:
            print("Calling create_app(config) ...")
            try:
                app_mod.create_app({'TESTING': True})
            except Exception as e:
                print("create_app raised:", type(e), e)
except SystemExit as se:
    print("DEBUG EXIT:", se)
except Exception:
    print("Exception during import:")
    traceback.print_exc()
