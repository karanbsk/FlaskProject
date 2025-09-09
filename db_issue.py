# db_issue.py -- diagnostic helper to print build_postgres_uri() result
import os
import sys
import importlib

# Put project root (one level up from this script) onto sys.path so "import app.*" works
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = SCRIPT_DIR  # file is in project root already; adjust if stored elsewhere
if not PROJECT_ROOT in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("Project root ->", PROJECT_ROOT)
print("sys.path[0] ->", sys.path[0])

try:
    cfg = importlib.import_module("app.config")
except Exception as e:
    print("IMPORT ERROR when importing app.config:", type(e).__name__, e)
    # show listing of app/ to help debug
    app_dir = os.path.join(PROJECT_ROOT, "app")
    print("\nContents of", app_dir)
    try:
        for name in sorted(os.listdir(app_dir)):
            print("  ", name)
    except Exception as e2:
        print("  Could not list app/:", type(e2).__name__, e2)
    raise SystemExit(1)

# If we have build_postgres_uri(), call it and print result
if hasattr(cfg, "build_postgres_uri"):
    try:
        uri = cfg.build_postgres_uri()
        print("\nbuild_postgres_uri() ->", uri)
    except Exception as e:
        print("Error while calling build_postgres_uri():", type(e).__name__, e)
else:
    import inspect
    print("build_postgres_uri not found. app.config source:\n")
    print(inspect.getsource(cfg))
