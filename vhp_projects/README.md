# VHP Patient Database

A local web-based patient database for managing surgical records, built with Flask and SQLite.

## Features

- **Patient CRUD** — Create, read, update, and delete patient records
- **Surgery type tracking** — Cataract, Plastics, Strabismus, Pterygium, Dermatology
- **Print individual patient records** — Laserband stickers and single surgery logs
- **Print daily surgery log** — Generate printable logs by date and surgery type
- **Column sorting & filtering** — Sort by any column, filter by date or surgery type
- **Soft delete with trash/restore** — Move patients to trash and restore them later
- **Automatic database backups** — Periodic backups with smart retention

## Installation

```bash
# Clone the repository
git clone https://github.com/salaamout/dr-scheduling.git
cd dr-scheduling

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## How to Run

```bash
python run.py
# Open http://127.0.0.1:5001
```

## Project Structure

```
vhp_projects/
├── app/
│   ├── __init__.py        # App factory
│   ├── config.py          # Configuration
│   ├── models.py          # Patient SQLAlchemy model
│   ├── forms.py           # WTForms definitions
│   ├── routes.py          # Route handlers (Blueprint)
│   └── backup.py          # Backup manager
├── static/
│   ├── css/style.css      # Shared styles
│   └── js/app.js          # Client-side JavaScript
├── templates/
│   ├── base.html          # Shared layout
│   ├── index.html         # Patient listing
│   ├── patient_form.html  # Create/edit form
│   ├── trash.html         # Deleted patients
│   ├── print_stickers.html
│   ├── print_schedule.html
│   └── print_log.html
├── instance/
│   ├── patients.db        # SQLite database
│   └── backups/           # Automatic backups
├── scripts/
│   ├── build_app.sh       # PyInstaller build
│   ├── create_mac_app.sh  # (deprecated)
│   ├── create_icon.sh     # (deprecated)
│   └── launch_app.py      # (deprecated)
├── run.py                 # Entry point
├── requirements.txt
└── .gitignore
```

## Distribution (Mac App)

Build a standalone Mac application with PyInstaller:

```bash
./scripts/build_app.sh
```

This creates `dist/PatientDatabase.app` — copy it to any Mac and double-click to run.

## Database Backup System

The application automatically creates periodic backups of your database to prevent data loss. Backups are stored in `instance/backups/`.

### Backup Features

- Automatic backups every 10 minutes
- Timestamped backup files (`patients_YYYYMMDD_HHMMSS.db`)
- Keeps up to 100 backup files
- Smart retention: keeps all recent backups, one per 6-hour period for older ones

### Configuration

Backup settings can be adjusted in `app/config.py`:

```python
BACKUP_INTERVAL = 600            # Time between backups in seconds (10 minutes)
MAX_BACKUPS = 100                # Maximum number of backup files to keep
PERIODIC_BACKUP_INTERVAL = 21600 # Keep one backup per 6 hours for older backups
```

### Restoring from a Backup

```bash
# Stop the application
pkill -f "python.*run.py"

# List available backups
ls -l instance/backups/patients_*.db

# Restore a backup
cp instance/backups/patients_YYYYMMDD_HHMMSS.db instance/patients.db

# Restart the application
python run.py
```

## License

Private — for VHP use only.
