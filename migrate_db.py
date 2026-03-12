"""
Run this script ONCE to migrate the database schema to include all the new columns.
Usage (from d:\pinterest):
    .venv\Scripts\python.exe migrate_db.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db

def main():
    app = create_app()
    with app.app_context():
        # Use db.create_all for new tables (safe – only creates what doesn't exist)
        db.create_all()

        # --- Add new columns to existing tables via raw SQL (SQLite compatible) ---
        conn = db.engine.raw_connection()
        cur = conn.cursor()

        alterations = [
            # Pin table
            ("SELECT source_url FROM pin LIMIT 1",
             "ALTER TABLE pin ADD COLUMN source_url VARCHAR(500)"),
            ("SELECT views FROM pin LIMIT 1",
             "ALTER TABLE pin ADD COLUMN views INTEGER DEFAULT 0 NOT NULL"),
            # Message table
            ("SELECT is_read FROM message LIMIT 1",
             "ALTER TABLE message ADD COLUMN is_read BOOLEAN DEFAULT 0 NOT NULL"),
            # User table
            ("SELECT website FROM user LIMIT 1",
             "ALTER TABLE user ADD COLUMN website VARCHAR(255)"),
            # Board table
            ("SELECT description FROM board LIMIT 1",
             "ALTER TABLE board ADD COLUMN description TEXT"),
            ("SELECT is_private FROM board LIMIT 1",
             "ALTER TABLE board ADD COLUMN is_private BOOLEAN DEFAULT 0"),
        ]

        for check_sql, alter_sql in alterations:
            try:
                cur.execute(check_sql)
                print(f"  already exists: {alter_sql.split('ADD COLUMN')[1].strip().split()[0]}")
            except Exception:
                try:
                    cur.execute(alter_sql)
                    conn.commit()
                    col = alter_sql.split('ADD COLUMN')[1].strip().split()[0]
                    print(f"  added column: {col}")
                except Exception as e:
                    print(f"  ERROR on alter: {e}")

        conn.close()
        print("\nAll done! Database is up to date.")
        print("You can now run:  python run.py")

if __name__ == "__main__":
    main()
