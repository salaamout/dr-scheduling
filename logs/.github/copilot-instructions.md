# Copilot Instructions — Medical Mission Logs

## Project Overview

This is a **Flask-based Medical Mission Logs** web application used on a single laptop during medical missions. It tracks patients across 5 log categories, supports CSV/PDF/ZIP export, search, and automatic SQLite backups.

- **Stack:** Python 3, Flask, SQLite, Jinja2 templates, fpdf2
- **Virtual env:** `.venv` (located at project root)
- **Python executable:** `.venv/bin/python`
- **App entry point:** `python app.py` — runs on **port 9874**
- **Database:** `mission_logs.db` (SQLite, same directory)
- **No external test framework** — tests use a standalone script with a `check()` helper

## Log Categories

The app has exactly 5 log categories:

1. **Priority Patients** — patients flagged for next-year follow-up
2. **Dermatology** — derm encounters, procedures, biopsies
3. **Laser** — laser treatments (YAG, SLT), tracked by eye (OD/OS/OU)
4. **Guzman Referrals** — referrals to/from Guzman
5. **Darlene Prosthetics** — prosthetics cases

## Key Routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Dashboard with counts & recent activity |
| `/log/<category>` | GET | View log entries for a category |
| `/patient/add` | POST | Add a new patient |
| `/patient/<id>/edit` | GET/POST | Edit patient |
| `/patient/<id>/delete` | POST | Delete patient + their log entries |
| `/log-entry/add` | POST | Add a log entry |
| `/log-entry/<id>/edit` | GET/POST | Edit a log entry |
| `/log-entry/<id>/delete` | POST | Delete a log entry |
| `/export/<category>/csv` | GET | Export a category as CSV |
| `/export/<category>/pdf` | GET | Export a category as PDF |
| `/export/all/zip` | GET | Export all categories as a ZIP of CSVs |
| `/search?q=<term>` | GET | Search patients/entries |
| `/backups` | GET | View/restore backups |

## "Test Latest Changes" Workflow

When the user says **"test latest changes"**, follow these steps:

### Step 1 — Review what changed

Run `git diff HEAD` (or `git diff` for unstaged changes) to see what was modified. Understand which files, routes, fields, templates, or database columns changed.

### Step 2 — Update the test script if needed

Open `test_changes.py` and determine whether the changes from Step 1 require new or modified test assertions. For example:

- **New route added** → add a request to that route and assert status 200 + expected content
- **New field/column added** → add assertions that the field appears in the relevant log view, CSV export, edit page, and CRUD operations
- **Field removed** → update or remove assertions that check for the old field
- **New dropdown options** → add assertions verifying the `<select>` and `<option>` elements
- **Template changes** → add assertions checking for new text/elements in rendered HTML
- **Export changes** → verify CSV headers, PDF generation, ZIP contents

The test script uses Flask's built-in test client (`app.test_client()`) — **no running server is needed**. Keep the existing `check(condition, pass_msg, fail_msg)` pattern. Add new tests in the appropriate numbered section or create a new section if needed.

### Step 3 — Run the tests

Run this exact command from the project root:

```
/Users/kyleeaton/dr_projects/logs/.venv/bin/python test_changes.py
```

**Do NOT start the Flask server first.** The test script imports the app directly and uses Flask's test client.

### Step 4 — Fix failures

If any tests fail:
1. Read the failure messages carefully
2. Determine whether the bug is in the app code or the test script
3. Fix the appropriate file(s)
4. Re-run the test script until all tests pass

## Test Script Structure (`test_changes.py`)

The test script is organized into numbered sections:

1. **Dashboard** — renders, shows counts, has export links
2. **Log category pages** — all 5 categories load with 200
3. **Dermatology-specific** — `# Procedures` column, `procedure_count` field
4. **Dropdowns** — `<select>` elements in Laser, Guzman, Priority views
5. **CSV exports** — all 5 categories export, correct headers
6. **ZIP export** — downloads, correct Content-Type, contains 5 CSVs
7. **PDF exports** — all 5 categories, correct Content-Type
8. **Search & Backups** — both pages load
9. **CRUD** — add patient → add log entries (Derm with procedure_count, Laser with YAG/OU) → verify dashboard
10. **Edit log entry** — load edit page, submit changes with updated fields
11. **Cleanup** — delete test patient and associated entries

The script exits with code 0 on success, 1 on any failure. It prints a summary with ✅/❌ markers.

## General Development Notes

- Templates are in `templates/` — Jinja2 with a `base.html` layout
- Database functions are in `database.py` — all SQL is there
- Export logic is in `export.py` (CSV, PDF, ZIP)
- Backup logic is in `backup.py` (scheduler, create, restore)
- `start.py` handles first-run setup and launches the app
- The app auto-creates the database on first run via `init_db()`
