"""
VHP Patient Database - Application Factory
"""
import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .backup import BackupManager
from .config import Config
from .models import db

csrf = CSRFProtect()
backup_manager = BackupManager()


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static'),
    )
    app.config.from_object(config_class)

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
