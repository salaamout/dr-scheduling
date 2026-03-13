"""
VHP Patient Database - Application Factory
"""
import os
import shutil
import sys

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .backup import BackupManager
from .config import Config
from .models import db

csrf = CSRFProtect()
backup_manager = BackupManager()


def _get_data_dir():
    """Return a writable, persistent directory for the database and backups.

    When running as a frozen PyInstaller .app on macOS the bundle contents
    are read-only (and may live inside a temporary ``_MEIPASS`` folder), so
    we store mutable data under ``~/Library/Application Support/VHP Scheduling/``
    instead.  On a normal (non-frozen) run we just use the project-level
    ``instance/`` folder as before.
    """
    if getattr(sys, 'frozen', False):
        # macOS convention for writable app data
        support = os.path.join(os.path.expanduser('~'),
                               'Library', 'Application Support',
                               'VHP Scheduling')
        os.makedirs(support, exist_ok=True)
        return support
    return None  # use Flask default


def _seed_data_dir(data_dir, bundle_instance_dir):
    """Copy the bundled seed database into *data_dir* if it doesn't exist yet."""
    dest_db = os.path.join(data_dir, 'patients.db')
    src_db = os.path.join(bundle_instance_dir, 'patients.db')
    if not os.path.exists(dest_db) and os.path.exists(src_db):
        shutil.copy2(src_db, dest_db)
    # Also seed backups
    dest_backups = os.path.join(data_dir, 'backups')
    src_backups = os.path.join(bundle_instance_dir, 'backups')
    if not os.path.exists(dest_backups) and os.path.isdir(src_backups):
        shutil.copytree(src_backups, dest_backups)


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    frozen = getattr(sys, 'frozen', False)

    # When frozen, _MEIPASS is where PyInstaller unpacked our data files.
    if frozen:
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    data_dir = _get_data_dir()

    # If we have a dedicated writable data dir, tell Flask to use it as
    # instance_path so that the relative sqlite:///patients.db URI works.
    extra = {}
    if data_dir is not None:
        extra['instance_path'] = data_dir

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static'),
        **extra,
    )
    app.config.from_object(config_class)

    # When running frozen for the first time, copy the seed database from
    # the bundle into the writable data directory.
    if frozen and data_dir is not None:
        _seed_data_dir(data_dir, os.path.join(base_dir, 'instance'))

    # Set backup directory dynamically based on instance path
    if app.config['BACKUP_DIR'] is None:
        app.config['BACKUP_DIR'] = os.path.join(app.instance_path, 'backups')

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    backup_manager.init_app(app)

    # Register blueprint
    from .routes import bp
    app.register_blueprint(bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Periodic backup check before each request
    @app.before_request
    def _check_backup():
        backup_manager.check_backup()

    return app
