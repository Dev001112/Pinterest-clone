"""
Safe DB upgrade script — run ONCE to add all new columns.
Usage:
    .venv\Scripts\python.exe fix_db.py
"""
import sqlite3, os, sys

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')

if not os.path.exists(DB_PATH):
    print(f"DB not found at {DB_PATH} — creating via Flask instead")
    sys.path.insert(0, os.path.dirname(__file__))
    from app import create_app, db
    app = create_app()
    with app.app_context():
        db.create_all()
    print("Done — DB created from scratch, all tables present.")
    sys.exit(0)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

def column_exists(table, col):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == col for row in cur.fetchall())

def table_exists(table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None

changes = [
    # (table, column, definition)
    ("pin",     "source_url", "VARCHAR(500)"),
    ("pin",     "views",      "INTEGER NOT NULL DEFAULT 0"),
    ("message", "is_read",    "BOOLEAN NOT NULL DEFAULT 0"),
    ("user",    "website",    "VARCHAR(255)"),
    ("board",   "description","TEXT"),
    ("board",   "is_private", "BOOLEAN NOT NULL DEFAULT 0"),
]

print(f"Using DB: {DB_PATH}")

for table, col, defn in changes:
    if not table_exists(table):
        print(f"  [SKIP] table '{table}' does not exist")
        continue
    if column_exists(table, col):
        print(f"  [OK]   {table}.{col} already exists")
    else:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
        print(f"  [ADD]  {table}.{col} {defn}")

# Create new tables via Flask/SQLAlchemy (handles Notification, updates board, etc.)
conn.commit()
conn.close()
print("\nColumn migration done. Creating any missing tables...")

sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("Tables created/verified OK")

print("\n✅ All done! You can now run:  python run.py")
