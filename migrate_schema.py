import sqlite3

def update_db():
    conn = sqlite3.connect('instance/app.db')
    c = conn.cursor()
    
    # Try adding tags column, skip if already exists
    try:
        c.execute("ALTER TABLE pin ADD COLUMN tags VARCHAR(255)")
        print("Added tags column to pinned table.")
    except sqlite3.OperationalError as e:
        print(f"Skipping adding tags: {e}")

    # Create Comment table
    try:
        c.execute('''
        CREATE TABLE IF NOT EXISTS comment (
            id INTEGER NOT NULL PRIMARY KEY,
            text TEXT NOT NULL,
            created_at DATETIME,
            user_id INTEGER NOT NULL,
            pin_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user (id),
            FOREIGN KEY(pin_id) REFERENCES pin (id)
        )
        ''')
        print("Created comment table.")
    except sqlite3.OperationalError as e:
        print(f"Error creating comment table: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_db()
