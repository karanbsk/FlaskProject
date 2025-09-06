# inspect_tmpdb.py
import sqlite3, sys, os

if len(sys.argv) != 2:
    print("Usage: python inspect_tmpdb.py \"C:\\full\\path\\to\\dbfile.db\"")
    sys.exit(1)

db_path = sys.argv[1]
if not os.path.exists(db_path):
    print("File not found:", db_path)
    sys.exit(2)

suspicious_patterns = ["%inject%", "%'--%", "%--%", "% OR %1=1%", "% OR 1=1%"]

def try_query(cur, table, col, pattern):
    try:
        cur.execute(f"SELECT rowid, * FROM {table} WHERE {col} LIKE ?", (pattern,))
        return cur.fetchall()
    except Exception:
        return []

with sqlite3.connect(db_path) as conn:
    cur = conn.cursor()
    print("Inspecting DB:", db_path)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    if not tables:
        print("No tables found in this DB.")
        sys.exit(0)
    print("Tables:", tables)

    for t in tables:
        try:
            cur.execute(f"PRAGMA table_info({t});")
            cols = [r[1] for r in cur.fetchall()]
        except Exception as e:
            print(f"  Could not read schema for table {t}: {e}")
            continue

        user_like_cols = [c for c in cols if c.lower() in ("username","user_name","email","email_address","name")]
        print(f"\nTable: {t}  Columns: {cols}")
        if user_like_cols:
            print("  Candidate user columns:", user_like_cols)

        found_any = False
        cols_to_search = user_like_cols or cols
        for col in cols_to_search:
            for pat in suspicious_patterns:
                rows = try_query(cur, t, col, pat)
                if rows:
                    found_any = True
                    print(f"  >>> Matches in table '{t}', column '{col}' pattern '{pat}':")
                    for r in rows:
                        print("     ", r)

        # catch any username containing a quote or double dash
        for col in cols:
            try:
                cur.execute(f"SELECT rowid, * FROM {t} WHERE {col} LIKE ? OR {col} LIKE ?", ("%'%","%--%"))
                rows = cur.fetchall()
                if rows:
                    found_any = True
                    print(f"  >>> Rows in {t} where {col} contains quote or --:")
                    for r in rows:
                        print("     ", r)
            except Exception:
                pass

        if not found_any:
            print("  No suspicious rows found in this table.")
