import importlib, sys, os


# adjust module path if your config is in app/config.py
try:
    cfg = importlib.import_module('app.config')
except Exception as e:
    print("Error importing app.config:", e)
    sys.exit(2)

if hasattr(cfg, 'build_postgres_uri'):
    print("Invoking build_postgres_uri()...")
    try:
        print("Result:", cfg.build_postgres_uri())
    except Exception as e:
        print("Error calling build_postgres_uri():", e)
else:
    print("build_postgres_uri not found in app.config. Show file content instead.")
    import inspect
    print(inspect.getsource(cfg))
