# Medical Mission Logs

A local web application for managing patient logs during medical missions.

## How to Run

1. Open a terminal and navigate to this folder:
   ```
   cd /Users/kyleeaton/dr_projects/logs
   ```

2. Start the app:
   ```
   python app.py
   ```

3. Open your browser to: **http://localhost:5000**

## Features

- **Dashboard** — Overview of all 5 log categories with patient counts
- **5 Log Categories** — Priority Patients, Dermatology, Laser, Guzman Referrals, Darlene Prosthetics
- **Add/Edit/Delete** patients and log entries
- **Search** patients by name or Chart ID
- **Filter** log entries by status
- **Export to CSV** — Download any log or all logs as a CSV file
- **Export to PDF** — Download any log as a formatted PDF

## Data

All data is stored locally in `mission_logs.db` (SQLite database file). To back up your data, simply copy this file.

## Requirements

- Python 3.x
- Flask
- fpdf2
