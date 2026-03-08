# Medical Mission Logs

A local web application for managing patient logs during medical missions.

---

## Quick Start (Double-Click)

### On Mac
1. Double-click **`MedicalMissionLogs.command`**
2. The app starts and your browser opens automatically

> **First time on a new Mac?** If you get a security warning, right-click the file → Open → Open.

### On Windows
1. Double-click **`MedicalMissionLogs.bat`**
2. The app starts and your browser opens automatically

> **First time on a new PC?** Make sure Python is installed first (see "Moving to Another Computer" below).

---

## Moving to Another Computer

### What to copy
Copy this **entire folder** to the new computer (USB drive, AirDrop, cloud, etc.).
The folder contains everything: the app code, your database, templates, and backups.

### What the new computer needs
1. **Python 3** — Download from [python.org/downloads](https://www.python.org/downloads/)
   - **Windows:** Check ✅ **"Add Python to PATH"** during installation
   - **Mac:** The installer handles everything
2. That's it! The first time you launch the app, it will automatically install the required packages (Flask, fpdf2).

### Step by step
1. Install Python 3 on the new computer
2. Copy this entire folder to the new computer
3. Double-click **`MedicalMissionLogs.command`** (Mac) or **`MedicalMissionLogs.bat`** (Windows)
4. The app installs its dependencies automatically and opens in your browser

---

## Manual Start (Terminal)

If you prefer the command line:

```
cd path/to/this/folder
pip install -r requirements.txt
python start.py
```

Or directly:
```
python app.py
```
Then open **http://localhost:5000** in your browser.

---

## Features

- **Dashboard** — Overview of all 5 log categories with patient counts
- **5 Log Categories** — Priority Patients, Dermatology, Laser, Guzman Referrals, Darlene Prosthetics
- **Add/Edit/Delete** patients and log entries
- **Search** patients by name or Chart ID
- **Filter** log entries by status
- **Export to CSV** — Download any log or all logs as a CSV file
- **Export to PDF** — Download any log as a formatted PDF
- **Automatic Backups** — Database backed up every 5 minutes, kept for 48 hours
- **Restore** — Restore from any backup point via the Backups page

## Data

All data is stored locally in `mission_logs.db` (SQLite database file). Backups are stored in the `backups/` folder.

## Requirements

- Python 3.x
- Flask
- fpdf2

All Python packages are listed in `requirements.txt` and installed automatically by the launcher.
