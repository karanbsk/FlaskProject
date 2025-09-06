# scan_dbs_for_injection.py
import sqlite3, pathlib, re, sys

# where to search
search_paths = [
    pathlib.Path("instance"),
    pathlib.Path("."),   # project root
]

# candidate user table names to try
user_tables = ["users", "user", "auth_user", "accounts", "app_user", "users_table"]

# suspicious patterns to search for
suspicious_patterns = [
    "%inject%",   # your known malicious payload
    "%'--%",      # quotes + comment
    "%--%",       # SQL comment
    "% OR %1=1%", # typical attack wording (loose check)
]

def scan_db(db_path):
    print(f"\n=== Scanning {db_path} ===")
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        if not tables:
            print("  [no tables]")
            return
        print("  Tables:", tables)

        # try known user tables first, but also check any table if unknown
        tables_to_check = [t for t in user_tables if t in tables] or tables

        for t in tables_to_check:
            try:
                # attempt a safe parameterized sample
                print(f"  -> Checking table '{t}' for suspicious usernames...")
                for pat in suspicious_patterns:
                    cur.execute(f"SELECT rowid, * FROM {t} WHERE username LIKE ?", (pat,))
                    rows = cur.fetchall()
                    if rows:
                        print(f"    Found rows matching {pat}:")
                        for r in rows:
                            print("     ", r)
                # also detect rows with single quote or double dash in username/email
                cur.execute(f"SELECT rowid, * FROM {t} WHERE username LIKE ? OR username LIKE ?", ("%'%","%--%"))
                rows = cur.fetchall()
                if rows:
                    print("    Found rows containing quote or -- in username:")
                    for r in rows:
                        print("     ", r)
            except Exception as e:
                # skip if different schema
                print(f"    (skipped '{t}' — {e})")
    except Exception as e:
        print("  Error opening DB:", e)
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    # gather .db files in search_paths
    db_files = []
    for p in search_paths:
        if not p.exists():
            continue
        for f in p.rglob("*.db"):
            db_files.append(f.resolve())
    # also look for .sqlite and .sqlite3 in root
    for ext in ("*.sqlite", "*.sqlite3"):
        for f in pathlib.Path(".").rglob(ext):
            db_files.append(f.resolve())

    if not db_files:
        print("No local .db files found in instance/ or project root.")
        sys.exit(0)
    print("Found DB files:")
    for f in db_files:
        print(" ", f)
    for db in db_files:
        scan_db(db)
