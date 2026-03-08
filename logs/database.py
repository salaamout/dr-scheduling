"""
Database setup and helper functions for Medical Mission Logs.
Uses SQLite — all data stored in a single local file.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mission_logs.db")

LOG_CATEGORIES = [
    "Priority Patients",
    "Dermatology",
    "Laser",
    "Guzman Referrals",
    "Darlene Prosthetics",
]


def get_db():
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            chart_id TEXT NOT NULL UNIQUE,
            date_of_birth TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            log_category TEXT NOT NULL,
            date_of_encounter TEXT,
            notes TEXT DEFAULT '',
            status TEXT DEFAULT 'Pending',
            follow_up_date TEXT,
            advocate TEXT DEFAULT '',
            community TEXT DEFAULT '',
            problem TEXT DEFAULT '',
            appointment_timeframe TEXT DEFAULT '',
            procedure_type TEXT DEFAULT '',
            eye TEXT DEFAULT '',
            laser_date TEXT DEFAULT '',
            procedure TEXT DEFAULT '',
            derm_date TEXT DEFAULT '',
            surgery_type TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)

    # Add columns if they don't exist (migration for existing DBs)
    migration_columns = [
        ("advocate", "TEXT DEFAULT ''"),
        ("community", "TEXT DEFAULT ''"),
        ("problem", "TEXT DEFAULT ''"),
        ("appointment_timeframe", "TEXT DEFAULT ''"),
        ("procedure_type", "TEXT DEFAULT ''"),
        ("eye", "TEXT DEFAULT ''"),
        ("laser_date", "TEXT DEFAULT ''"),
        ("procedure", "TEXT DEFAULT ''"),
        ("derm_date", "TEXT DEFAULT ''"),
        ("surgery_type", "TEXT DEFAULT ''"),
    ]
    for col_name, col_type in migration_columns:
        try:
            cursor.execute(f"ALTER TABLE log_entries ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


# --- Patient CRUD ---

def get_all_patients(search=None):
    """Get all patients, optionally filtered by search term."""
    conn = get_db()
    if search:
        patients = conn.execute(
            "SELECT * FROM patients WHERE full_name LIKE ? OR chart_id LIKE ? ORDER BY full_name",
            (f"%{search}%", f"%{search}%"),
        ).fetchall()
    else:
        patients = conn.execute("SELECT * FROM patients ORDER BY full_name").fetchall()
    conn.close()
    return patients


def get_patient(patient_id):
    """Get a single patient by ID."""
    conn = get_db()
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    return patient


def create_patient(full_name, chart_id, date_of_birth, notes=""):
    """Create a new patient. Returns the new patient ID."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO patients (full_name, chart_id, date_of_birth, notes) VALUES (?, ?, ?, ?)",
        (full_name, chart_id, date_of_birth, notes),
    )
    conn.commit()
    patient_id = cursor.lastrowid
    conn.close()
    return patient_id


def update_patient(patient_id, full_name, chart_id, date_of_birth, notes=""):
    """Update an existing patient."""
    conn = get_db()
    conn.execute(
        """UPDATE patients SET full_name = ?, chart_id = ?, date_of_birth = ?, notes = ?,
           updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (full_name, chart_id, date_of_birth, notes, patient_id),
    )
    conn.commit()
    conn.close()


def delete_patient(patient_id):
    """Delete a patient and all their log entries."""
    conn = get_db()
    conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()


# --- Log Entry CRUD ---

def get_log_entries(log_category, search=None):
    """Get all log entries for a category with optional filters."""
    conn = get_db()
    query = """
        SELECT le.*, p.full_name, p.chart_id, p.date_of_birth
        FROM log_entries le
        JOIN patients p ON le.patient_id = p.id
        WHERE le.log_category = ?
    """
    params = [log_category]

    if search:
        query += " AND (p.full_name LIKE ? OR p.chart_id LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY le.created_at DESC"
    entries = conn.execute(query, params).fetchall()
    conn.close()
    return entries


def get_log_entry(entry_id):
    """Get a single log entry by ID."""
    conn = get_db()
    entry = conn.execute(
        """SELECT le.*, p.full_name, p.chart_id, p.date_of_birth
           FROM log_entries le
           JOIN patients p ON le.patient_id = p.id
           WHERE le.id = ?""",
        (entry_id,),
    ).fetchone()
    conn.close()
    return entry


def create_log_entry(patient_id, log_category, notes="", follow_up_date=None,
                     advocate="", community="", problem="", appointment_timeframe="",
                     procedure_type="", eye="", laser_date="", procedure="", derm_date="", surgery_type=""):
    """Create a new log entry."""
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO log_entries (patient_id, log_category, notes, follow_up_date,
           advocate, community, problem, appointment_timeframe, procedure_type, eye, laser_date, procedure, derm_date, surgery_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (patient_id, log_category, notes, follow_up_date,
         advocate, community, problem, appointment_timeframe, procedure_type, eye, laser_date, procedure, derm_date, surgery_type),
    )
    conn.commit()
    entry_id = cursor.lastrowid
    conn.close()
    return entry_id


def update_log_entry(entry_id, notes="", follow_up_date=None,
                     advocate="", community="", problem="", appointment_timeframe="",
                     procedure_type="", eye="", laser_date="", procedure="", derm_date="", surgery_type=""):
    """Update an existing log entry."""
    conn = get_db()
    conn.execute(
        """UPDATE log_entries SET notes = ?, follow_up_date = ?,
           advocate = ?, community = ?, problem = ?, appointment_timeframe = ?,
           procedure_type = ?, eye = ?, laser_date = ?, procedure = ?, derm_date = ?, surgery_type = ?,
           updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (notes, follow_up_date,
         advocate, community, problem, appointment_timeframe,
         procedure_type, eye, laser_date, procedure, derm_date, surgery_type, entry_id),
    )
    conn.commit()
    conn.close()


def delete_log_entry(entry_id):
    """Delete a log entry."""
    conn = get_db()
    conn.execute("DELETE FROM log_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


# --- Dashboard helpers ---

def get_dashboard_counts():
    """Get patient count per log category."""
    conn = get_db()
    counts = {}
    for cat in LOG_CATEGORIES:
        row = conn.execute(
            "SELECT COUNT(DISTINCT patient_id) as cnt FROM log_entries WHERE log_category = ?",
            (cat,),
        ).fetchone()
        counts[cat] = row["cnt"]
    conn.close()
    return counts


def get_recent_activity(limit=10):
    """Get the most recent log entries across all categories."""
    conn = get_db()
    entries = conn.execute(
        """SELECT le.*, p.full_name, p.chart_id
           FROM log_entries le
           JOIN patients p ON le.patient_id = p.id
           ORDER BY le.created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return entries


def get_patient_logs(patient_id):
    """Get all log entries for a specific patient."""
    conn = get_db()
    entries = conn.execute(
        """SELECT * FROM log_entries WHERE patient_id = ? ORDER BY created_at DESC""",
        (patient_id,),
    ).fetchall()
    conn.close()
    return entries
