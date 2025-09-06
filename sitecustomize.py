# sitecustomize.py  (debugging only — remove after use)
import builtins, traceback, sys, importlib

_orig_import = builtins.__import__

def _wrap_psycopg2_connect(mod):
    try:
        # wrap connect so we print a stacktrace and stop the run for debugging
        real_connect = getattr(mod, "connect", None)
        def _debug_connect(*a, **kw):
            print("\n--- DEBUG: psycopg2.connect() CALLED ---")
            print("Args:", a, "Kw:", kw)
            print("Full stack (most recent call last):")
            traceback.print_stack()
            # stop execution so the caller is obvious
            sys.exit("DEBUG EXIT: psycopg2.connect() was called (see stack above)")
        # replace connect with wrapper
        setattr(mod, "connect", _debug_connect)
    except Exception:
        pass

def _debug_import(name, globals=None, locals=None, fromlist=(), level=0):
    mod = _orig_import(name, globals, locals, fromlist, level)
    # When psycopg2 (or submodule) is imported, wrap its connect
    if name == "psycopg2" or name.startswith("psycopg2."):
        _wrap_psycopg2_connect(mod)
    return mod

# Patch builtins.__import__ so we can wrap psycopg2 as soon as it's imported
builtins.__import__ = _debug_import

# Also, if psycopg2 already imported earlier, wrap it now
try:
    import psycopg2 as _pg
    _wrap_psycopg2_connect(_pg)
except Exception:
    pass
