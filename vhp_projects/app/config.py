"""
VHP Patient Database - Configuration
"""
import os


class Config:
    """Flask application configuration."""

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///patients.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Session cookies
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True

    # Backup settings
    BACKUP_DIR = None  # Set dynamically in create_app
    MAX_BACKUPS = 100
    BACKUP_INTERVAL = 600  # 10 minutes
    PERIODIC_BACKUP_INTERVAL = 21600  # 6 hours
