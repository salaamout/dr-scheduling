# Copilot Instructions — VHP Patient Scheduling

## Project Overview

This is a **Flask-based patient scheduling app** ("VHP Scheduling") used on a single laptop during medical mission trips.
It tracks surgical patients across multiple surgery types, supports printing (laserbands & daily logs),
search/filter/sort, a count summary, soft-delete/trash, and automatic SQLite backups.

- **Stack:** Python 3, Flask, SQLAlchemy, WTForms (Flask-WTF), Jinja2 templates
- **Virtual env:** `.venv` (located at project root)
- **Python executable:** `.venv/bin/python`
- **App entry point:** `python run.py` — runs on **port 8420**
- **Database:** `instance/patients.db` (SQLite)
- **Backups:** `instance/backups/` — automatic every 10 minutes, pruned to keep 1 per 6-hour period
- **macOS packaging:** PyInstaller `.app` bundle, deployed to Desktop

## Surgery Types

The app tracks patients across these surgery types (each with its own procedure autofill options):

1. **Cataract** — Cataract, Bilateral Lenses, Vitrectomy
2. **Plastics** — Blepharoplasty, Ptosis, Enucleation, Evisceration, DCR, Cantoplasty, Ectropion Repair, Cyst Removal, Socket Repair, Papilloma, Dermis Fat Graft, Blocked Tear Duct
3. **Strabismus** — Strabismus
4. **Pterygium** — (no preset procedures)
5. **Dermatology** — (no preset procedures)

## Patient Model Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `surgery_type` | String(50) | Yes | One of: cataract, plastics, strabismus, pterygium, derm |
| `surgery_date` | Date | Yes | |
| `chart_number` | String(50) | Yes | |
| `name` | String(240) | Yes | |
| `age` | Integer | Yes | |
| `sex` | String(10) | Yes | M, F, or O |
| `eye` | String(2) | No | OD, OS, OU, or None |
| `procedure` | Text | Yes | |
| `advocate` | String(120) | No | |
| `community` | String(120) | No | |
| `number` | String(50) | No | Surgery number (string to allow any format) |
| `notes` | Text | No | |
| `deleted` | Boolean | Yes | Default False — soft-delete flag |
| `cancelled` | Boolean | Yes | Default False |

## Key Routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Main patient listing with filter, sort, search |
| `/new` | GET/POST | Create a new patient record |
| `/edit/<int:patient_id>` | GET/POST | Edit an existing patient |
| `/delete/<int:patient_id>` | POST | Soft-delete a patient (move to trash) |
| `/duplicate/<int:patient_id>` | GET/POST | Duplicate an existing patient |
| `/restore/<int:patient_id>` | POST | Restore a soft-deleted patient |
| `/trash` | GET | View soft-deleted patients |
| `/print/<int:patient_id>` | GET | Print a patient (laserband or single log via `?type=`) |
| `/print/daily-log` | GET | Print daily surgery log for a date + type |
| `/update-number/<int:patient_id>` | POST (JSON) | Inline AJAX update of surgery number |
| `/toggle-cancelled/<int:patient_id>` | POST (JSON) | Toggle cancelled status via AJAX |
| `/count-summary` | GET | Summary of surgery counts grouped by date and type |
| `/backups` | GET | Backup management page |
| `/backup/create` | POST | Create a manual backup |
| `/backup/restore` | POST | Restore from a specific backup file |
| `/backup/restore-slot` | POST | Restore from closest backup to a time slot |
| `/backup/delete` | POST | Delete a single backup file |

## Common Phrases → Actions

### "Rebuild the app" / "rebuild and replace the one on the desktop"
This means: **build the macOS .app with PyInstaller and copy it to the Desktop**, replacing any existing version. Run:
```
cd /Users/kyleeaton/dr_projects/vhp_projects && ./scripts/deploy_to_desktop.sh
```
This single script handles: activate venv → PyInstaller build → remove old Desktop app → copy new app to Desktop.

If the user says "rebuild the app", they mean the **VHP Scheduling** app (the main one). If they specifically say "PatientDatabase", use the `PatientDatabase.spec` instead.

### "Run the app" / "start the server"
```
cd /Users/kyleeaton/dr_projects/vhp_projects && .venv/bin/python run.py
```

### "Run the tests"
```
cd /Users/kyleeaton/dr_projects/vhp_projects && .venv/bin/python -m pytest test_app.py -v
```
**Do NOT start the Flask server first.** Tests use Flask's built-in test client with an in-memory SQLite database.

## Test Suite Structure (`test_app.py`)

The test file uses `unittest` and is organized into these test classes:

1. **TestAppFactory** — verifies `create_app()` produces a properly configured Flask app, checks config defaults, instance path creation, backup dir setup, and that all expected routes are registered
2. **TestPatientModel** — tests the Patient SQLAlchemy model: creating patients, default values for `deleted`/`cancelled`, nullable optional fields, `__repr__`
3. **TestPatientForm** — validates WTForms form: valid data, missing required fields, `PROCEDURE_OPTIONS` keys for all 5 surgery types
4. **TestRoutes** — integration tests for all route handlers:
   - Index: empty, with patients, filter by date, filter by type, search by name, search by chart number, sort, hides deleted, count excludes cancelled
   - Trash: shows deleted, empty state
   - Restore: restores soft-deleted patient
   - New patient: GET form, POST creation, surgery_type prefill from query param
   - Edit patient: GET form, POST update, clearing eye field, 404 for nonexistent
   - Delete: soft-delete, preserves filters in redirect
   - Duplicate: GET form (clears number), POST creation
   - Print: laserband, single log, unknown type, 404 for nonexistent
   - Daily log: valid request, missing params, invalid date
   - Update number: AJAX success, missing data
   - Toggle cancelled: AJAX toggle on/off
   - Count summary: empty, with data, excludes deleted, excludes cancelled
5. **TestBackupManager** — tests backup creation, missing DB handling, datetime parsing, interval checking, periodic keep/discard logic
6. **TestCSRF** — verifies CSRF is enabled in production config, secret key is not hardcoded, CSRF meta tag appears in base template

## Build Details

- **Spec files:** `VHPScheduling.spec` (main app), `PatientDatabase.spec` (legacy name)
- **Build output:** `dist/VHP Scheduling.app`
- **Desktop target:** `~/Desktop/VHP Scheduling.app`
- **Deploy script:** `scripts/deploy_to_desktop.sh`

## General Development Notes

- **App factory** is in `app/__init__.py` — `create_app(config_class)` initializes Flask, SQLAlchemy, CSRF, backup manager, and registers the blueprint
- **Routes** are in `app/routes.py` — all handlers live on a single `main` blueprint
- **Models** are in `app/models.py` — single `Patient` model with SQLAlchemy
- **Forms** are in `app/forms.py` — `PatientForm` (WTForms) + `PROCEDURE_OPTIONS` dict
- **Config** is in `app/config.py` — `Config` class with defaults (overridden by `TestConfig` in tests)
- **Backup logic** is in `app/backup.py` — `BackupManager` class with periodic/manual backup, restore, and pruning
- **Templates** are in `templates/` — Jinja2 with a `base.html` layout
- **Static assets** are in `static/css/style.css` and `static/js/app.js`
- **Database** is SQLite at `instance/patients.db`; uses Flask's `instance_path` (writable `~/Library/Application Support/VHP Scheduling/` when frozen)
- Filters (surgery_date, surgery_type, sort, order, search) are preserved across redirects via `_preserve_filters()` helper
