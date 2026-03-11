"""
VHP Patient Database - Backup Manager
"""
import glob
import logging
import os
import shutil
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Quick-restore time slots shown on the backups page
RESTORE_SLOTS = [
    {'label': '10 minutes ago', 'minutes': 10},
    {'label': '30 minutes ago', 'minutes': 30},
    {'label': '1 hour ago', 'minutes': 60},
    {'label': '2 hours ago', 'minutes': 120},
    {'label': '6 hours ago', 'minutes': 360},
    {'label': '12 hours ago', 'minutes': 720},
    {'label': '1 day ago', 'minutes': 1440},
]


def _format_age(delta):
    """Format a timedelta into a human-readable age string."""
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f'{total_seconds}s ago'
    if total_seconds < 3600:
        mins = total_seconds // 60
        return f'{mins}m ago'
    if total_seconds < 86400:
        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        return f'{hours}h {mins}m ago'
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    return f'{days}d {hours}h ago'


class BackupManager:
    """Manages automatic database backups with periodic retention."""

    def __init__(self, app=None):
        self._last_backup = datetime.min
        self.app = app

    def init_app(self, app):
        """Initialize with a Flask app."""
        self.app = app
        os.makedirs(app.config['BACKUP_DIR'], exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_backup_datetime(backup_path):
        """Extract datetime from backup filename."""
        filename = os.path.basename(backup_path)
        # Strip the prefix (patients_ or patients_pre_restore_) and .db suffix
        timestamp = filename.replace('.db', '')
        # Handle pre-restore safety backups
        if 'pre_restore_' in timestamp:
            timestamp = timestamp.split('pre_restore_')[-1]
        else:
            timestamp = timestamp.replace('patients_', '')
        return datetime.strptime(timestamp, '%Y%m%d_%H%M%S')

    def _should_keep_backup(self, backup_path, periodic_backups):
        """Determine if a backup should be kept based on periodic retention rules."""
        backup_time = self._get_backup_datetime(backup_path)
        interval_hours = self.app.config['PERIODIC_BACKUP_INTERVAL'] // 3600

        period_start = backup_time.replace(
            hour=(backup_time.hour // interval_hours) * interval_hours,
            minute=0,
            second=0,
        )
        period_key = period_start.strftime('%Y%m%d_%H')

        if period_key not in periodic_backups:
            periodic_backups[period_key] = backup_path
            return True

        existing_time = self._get_backup_datetime(periodic_backups[period_key])
        if abs(backup_time - period_start) < abs(existing_time - period_start):
            periodic_backups[period_key] = backup_path
            return True

        return False

    def _db_path(self):
        """Return the path to the live database."""
        return os.path.join(self.app.instance_path, 'patients.db')

    # ------------------------------------------------------------------
    # Create & clean-up
    # ------------------------------------------------------------------

    def create_backup(self):
        """Create a timestamped backup of the database. Returns the path or None."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_path = self._db_path()
        backup_path = os.path.join(
            self.app.config['BACKUP_DIR'], f'patients_{timestamp}.db'
        )

        if not os.path.exists(db_path):
            return None

        try:
            shutil.copy2(db_path, backup_path)
        except OSError:
            logger.exception('Failed to create database backup')
            return None

        self._cleanup_old_backups()
        return backup_path

    def _cleanup_old_backups(self):
        """Remove old backups that exceed retention limits."""
        backups = sorted(
            glob.glob(os.path.join(self.app.config['BACKUP_DIR'], 'patients_*.db'))
        )

        if len(backups) <= self.app.config['MAX_BACKUPS']:
            return

        periodic_backups = {}
        keep_recent = self.app.config['MAX_BACKUPS'] // 2
        to_evaluate = backups[:-keep_recent] if len(backups) > keep_recent else []

        for backup in to_evaluate:
            if not self._should_keep_backup(backup, periodic_backups):
                try:
                    os.remove(backup)
                except OSError:
                    logger.exception('Failed to remove old backup: %s', backup)

    # ------------------------------------------------------------------
    # List / find / restore
    # ------------------------------------------------------------------

    def list_backups(self):
        """Return a list of all available backups sorted newest-first.

        Each item is a dict with filename, path, timestamp, age_label, size_kb.
        """
        backup_dir = self.app.config['BACKUP_DIR']
        os.makedirs(backup_dir, exist_ok=True)
        backups = []
        now = datetime.now()

        for fname in os.listdir(backup_dir):
            if fname.startswith('patients_') and fname.endswith('.db'):
                fpath = os.path.join(backup_dir, fname)
                mtime = os.path.getmtime(fpath)
                created = datetime.fromtimestamp(mtime)
                age = now - created
                size_kb = os.path.getsize(fpath) / 1024

                backups.append({
                    'filename': fname,
                    'path': fpath,
                    'timestamp': created.strftime('%Y-%m-%d %H:%M:%S'),
                    'age_label': _format_age(age),
                    'size_kb': round(size_kb, 1),
                })

        backups.sort(key=lambda b: b['timestamp'], reverse=True)
        return backups

    def find_closest_backup(self, minutes_ago):
        """Find the backup closest to the requested number of minutes ago."""
        target_time = datetime.now() - timedelta(minutes=minutes_ago)
        backups = self.list_backups()

        if not backups:
            return None

        best = None
        best_diff = None
        for b in backups:
            b_time = datetime.strptime(b['timestamp'], '%Y-%m-%d %H:%M:%S')
            diff = abs((b_time - target_time).total_seconds())
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best = b

        return best

    def restore_backup(self, backup_filename):
        """Restore the database from a backup file.

        Creates a safety backup of the current DB before restoring.
        Returns (success: bool, message: str).
        """
        backup_dir = self.app.config['BACKUP_DIR']
        backup_path = os.path.join(backup_dir, backup_filename)

        if not os.path.exists(backup_path):
            return False, f'Backup file not found: {backup_filename}'

        db_path = self._db_path()

        # Safety backup of the current DB before overwriting
        if os.path.exists(db_path):
            safety_name = (
                f"patients_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            safety_path = os.path.join(backup_dir, safety_name)
            shutil.copy2(db_path, safety_path)

        # Overwrite the current database with the backup
        shutil.copy2(backup_path, db_path)
        return True, (
            f'Database restored from {backup_filename}. '
            'A safety backup of the previous state was saved.'
        )

    def delete_backup(self, backup_filename):
        """Delete a single backup file. Returns (success, message)."""
        backup_dir = self.app.config['BACKUP_DIR']
        backup_path = os.path.join(backup_dir, backup_filename)

        if not os.path.exists(backup_path):
            return False, f'Backup file not found: {backup_filename}'

        try:
            os.remove(backup_path)
            return True, f'Backup {backup_filename} deleted.'
        except OSError:
            logger.exception('Failed to delete backup: %s', backup_filename)
            return False, f'Failed to delete backup: {backup_filename}'

    # ------------------------------------------------------------------
    # Periodic check (called via before_request)
    # ------------------------------------------------------------------

    def check_backup(self):
        """Create a backup if enough time has elapsed since the last one."""
        now = datetime.now()
        if (now - self._last_backup).total_seconds() >= self.app.config['BACKUP_INTERVAL']:
            self.create_backup()
            self._last_backup = now
