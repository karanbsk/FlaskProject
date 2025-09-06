import sqlite3

db = "test_database.db"  # adjust path if needed
conn = sqlite3.connect(db)
cur = conn.cursor()

print("Tables in DB:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cur.fetchall())

print("\nChecking 'users' table for malicious entries...")
try:
    cur.execute("SELECT id, username, email FROM users WHERE username LIKE ?", ("%inject%",))
    rows = cur.fetchall()
    if rows:
        print("⚠️ Found suspicious rows:")
        for r in rows:
            print(r)
    else:
        print("✅ No suspicious usernames found.")
except sqlite3.Error as e:
    print("Error querying users table:", e)

conn.close()
