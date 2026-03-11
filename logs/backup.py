"""
Backup & Restore system for the Medical Mission Logs database.
Automatically creates periodic backups and allows restoring from them.
"""

import os
import shutil
import threading
import time
from datetime import datetime, timedelta

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "mission_logs.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

# How often to create a backup (in seconds) — every 5 minutes
BACKUP_INTERVAL = 5 * 60

# How long to keep backups — 48 hours
BACKUP_RETENTION = 48 * 60 * 60

# Time slots the user can restore from
RESTORE_SLOTS = [
    {"label": "5 minutes ago", "minutes": 5},
    {"label": "10 minutes ago", "minutes": 10},
    {"label": "20 minutes ago", "minutes": 20},
    {"label": "1 hour ago", "minutes": 60},
    {"label": "2 hours ago", "minutes": 120},
    {"label": "4 hours ago", "minutes": 240},
    {"label": "1 day ago", "minutes": 1440},
]


def ensure_backup_dir():
    """Create the backups directory if it doesn't exist."""
    os.makedirs(BACKUP_DIR, exist_ok=True)


def create_backup():
    """
    Create a timestamped copy of the database file.
    Returns the backup file path, or None if the DB doesn't exist.
    """
    if not os.path.exists(DB_PATH):
        return None

    ensure_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"mission_logs_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def cleanup_old_backups():
    """Remove backups older than BACKUP_RETENTION."""
    ensure_backup_dir()
    cutoff = time.time() - BACKUP_RETENTION
    for fname in os.listdir(BACKUP_DIR):
        fpath = os.path.join(BACKUP_DIR, fname)
        if os.path.isfile(fpath) and fname.startswith("mission_logs_") and fname.endswith(".db"):
            if os.path.getmtime(fpath) < cutoff:
                os.remove(fpath)


def list_backups():
    """
    Return a list of all available backups sorted newest-first.
    Each item is a dict with 'filename', 'path', 'timestamp', 'age_label'.
    """
    ensure_backup_dir()
    backups = []
    now = datetime.now()

    for fname in os.listdir(BACKUP_DIR):
        if fname.startswith("mission_logs_") and fname.endswith(".db"):
            fpath = os.path.join(BACKUP_DIR, fname)
            mtime = os.path.getmtime(fpath)
            created = datetime.fromtimestamp(mtime)
            age = now - created
            size_kb = os.path.getsize(fpath) / 1024

            backups.append({
                "filename": fname,
                "path": fpath,
                "timestamp": created.strftime("%Y-%m-%d %H:%M:%S"),
                "age_label": _format_age(age),
                "size_kb": round(size_kb, 1),
            })

    backups.sort(key=lambda b: b["timestamp"], reverse=True)
    return backups


def find_closest_backup(minutes_ago):
    """
    Find the backup closest to the requested number of minutes ago.
    Returns the backup dict or None.
    """
    target_time = datetime.now() - timedelta(minutes=minutes_ago)
    backups = list_backups()

    if not backups:
        return None

    best = None
    best_diff = None
    for b in backups:
        b_time = datetime.strptime(b["timestamp"], "%Y-%m-%d %H:%M:%S")
        diff = abs((b_time - target_time).total_seconds())
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best = b

    return best


def restore_backup(backup_filename):
    """
    Restore the database from a backup file.
    Creates a safety backup of the current DB before restoring.
    Returns (success: bool, message: str).
    """
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    if not os.path.exists(backup_path):
        return False, f"Backup file not found: {backup_filename}"

    # Safety backup of the current DB before overwriting
    if os.path.exists(DB_PATH):
        ensure_backup_dir()
        safety_name = f"mission_logs_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        safety_path = os.path.join(BACKUP_DIR, safety_name)
        shutil.copy2(DB_PATH, safety_path)

    # Overwrite the current database with the backup
    shutil.copy2(backup_path, DB_PATH)
    return True, f"Database restored from {backup_filename}. A safety backup was saved."


def _format_age(delta):
    """Format a timedelta into a human-readable age string."""
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds}s ago"
    elif total_seconds < 3600:
        mins = total_seconds // 60
        return f"{mins}m ago"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        return f"{hours}h {mins}m ago"
    else:
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        return f"{days}d {hours}h ago"


# --- Background backup scheduler ---

_scheduler_thread = None


def _backup_loop():
    """Background thread that creates periodic backups."""
    while True:
        try:
            create_backup()
            cleanup_old_backups()
        except Exception as e:
            print(f"[Backup] Error: {e}")
        time.sleep(BACKUP_INTERVAL)


def start_backup_scheduler():
    """Start the background backup scheduler (runs every 5 minutes)."""
    global _scheduler_thread
    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        return  # Already running

    # Create an initial backup immediately
    try:
        path = create_backup()
        if path:
            print(f"  [Backup] Initial backup created: {os.path.basename(path)}")
    except Exception as e:
        print(f"  [Backup] Error creating initial backup: {e}")

    _scheduler_thread = threading.Thread(target=_backup_loop, daemon=True)
    _scheduler_thread.start()
    print("  [Backup] Automatic backups enabled (every 5 minutes)")
