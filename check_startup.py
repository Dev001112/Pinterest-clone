import sys, os, traceback

log_path = r'd:\pinterest\startup_log.txt'

with open(log_path, 'w') as f:
    f.write("=== PinBoard Startup Test ===\n")
    try:
        sys.path.insert(0, r'd:\pinterest')
        os.chdir(r'd:\pinterest')

        f.write("Importing create_app...\n")
        from app import create_app, db
        f.write("create_app imported OK\n")

        f.write("Creating app...\n")
        app = create_app()
        f.write("App created OK\n")

        with app.app_context():
            f.write("Testing DB queries...\n")
            from app.models import User, Pin, Tag, Notification
            user_count = User.query.count()
            pin_count = Pin.query.count()
            f.write(f"Users: {user_count}, Pins: {pin_count}\n")

            # Check columns
            from sqlalchemy import text
            with db.engine.connect() as conn:
                for table in ['user', 'pin', 'message', 'board']:
                    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                    cols = [r[1] for r in rows]
                    f.write(f"  {table}: {cols}\n")

            f.write("All checks passed!\n")

    except Exception as e:
        f.write(f"\nERROR: {e}\n")
        traceback.print_exc(file=f)

print(f"Done — check {log_path}")
