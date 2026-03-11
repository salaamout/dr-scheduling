"""
Database migration script: Merge first_name + last_name → name, add eye and cancelled columns.

Run this ONCE before starting the updated application.
It will:
  1. Add column 'name' (if not exists)
  2. Add column 'eye' (if not exists)
  3. Add column 'cancelled' (if not exists)
  4. Merge first_name + ' ' + last_name → name for all existing rows
  5. (Optionally) drop first_name and last_name columns

SQLite doesn't support DROP COLUMN in older versions, so the old columns
are left in place but unused.  They will be ignored by SQLAlchemy.
"""
import os
import sqlite3
import sys


def migrate(db_path):
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Get current columns
    cur.execute("PRAGMA table_info(patient)")
    columns = {row[1] for row in cur.fetchall()}

    # 1. Add 'name' column
    if 'name' not in columns:
        print("Adding 'name' column...")
        cur.execute("ALTER TABLE patient ADD COLUMN name TEXT DEFAULT ''")
    else:
        print("'name' column already exists, skipping.")

    # 2. Add 'eye' column
    if 'eye' not in columns:
        print("Adding 'eye' column...")
        cur.execute("ALTER TABLE patient ADD COLUMN eye TEXT")
    else:
        print("'eye' column already exists, skipping.")

    # 3. Add 'cancelled' column
    if 'cancelled' not in columns:
        print("Adding 'cancelled' column...")
        cur.execute("ALTER TABLE patient ADD COLUMN cancelled BOOLEAN DEFAULT 0 NOT NULL")
    else:
        print("'cancelled' column already exists, skipping.")

    # 4. Merge first_name + last_name → name (only for rows where name is empty)
    if 'first_name' in columns and 'last_name' in columns:
        cur.execute(
            "UPDATE patient SET name = TRIM(first_name || ' ' || last_name) "
            "WHERE name IS NULL OR name = ''"
        )
        updated = cur.rowcount
        print(f"Merged first_name + last_name → name for {updated} row(s).")
    else:
        print("No first_name/last_name columns found — nothing to merge.")

    conn.commit()
    conn.close()
    print("Migration complete!")


if __name__ == '__main__':
    # Default to the instance/patients.db path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_db = os.path.join(base_dir, 'instance', 'patients.db')

    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db
    print(f"Migrating database: {db_path}")
    migrate(db_path)
