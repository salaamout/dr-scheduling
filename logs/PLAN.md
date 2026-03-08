# Medical Mission Logs — Web Database Plan

**Created:** March 8, 2026  
**Updated:** March 8, 2026  
**Status:** DRAFT v2 — Awaiting final approval before build

---

## 1. Overview

Build a **local web application** (runs on a single laptop, no internet required) to store and manage patient logs for a medical mission. The system will support **5 log categories**:

| # | Log Category | Description |
|---|---|---|
| 1 | **Priority Patients for Next Year** | Patients flagged for priority follow-up in the next mission cycle |
| 2 | **Dermatology** | Dermatology-related patient encounters and notes |
| 3 | **Laser** | Laser treatment cases and records |
| 4 | **Guzman Referrals** | Patients referred to/from Guzman |
| 5 | **Darlene Prosthetics** | Prosthetics cases managed through Darlene |

**Key constraints:**
- Single user, single laptop — no network, no authentication needed
- Launches locally in a web browser (e.g., http://localhost:5000)
- All data stored in a local file (SQLite database)

---

## 2. Decisions Made

| Question | Answer |
|---|---|
| **Hosting** | Local only — runs on your laptop, opens in your browser |
| **Users** | Single user, no login required |
| **Core fields per log** | Full Name, Chart ID, Date of Birth (more fields TBD) |
| **Search & filter** | ✅ Yes |
| **Export to CSV** | ✅ Yes |
| **Export to PDF** | ✅ Yes |
| **Dashboard with add-patient** | ✅ Yes |
| **Photo/file attachments** | ❌ No |
| **HIPAA compliance** | ❌ Not required |

---

## 3. Still Needed From You

Before building, I just need clarification on a couple of things:

- [ ] **Additional fields per log category** — Each log will have Full Name, Chart ID, and Date of Birth. What other fields do you want? (e.g., Notes, Status, Date of Visit, Follow-up Date, Diagnosis, Treatment). You mentioned you'll do more specifics later — just let me know when ready.
- [ ] **Do any of the 5 logs need unique/different fields**, or will they all share the same structure?

---

## 4. Technology Stack

Since this is a single-laptop app with no network needed, we're using the **simplest possible stack**:

| Layer | Technology | Why |
|---|---|---|
| **Backend** | Python (Flask) | Lightweight, easy to run, perfect for local apps |
| **Database** | SQLite | Single file, no database server to install, built into Python |
| **Frontend** | HTML + Tailwind CSS + vanilla JavaScript | Simple, fast, no build step needed |
| **PDF Export** | WeasyPrint or ReportLab (Python library) | Generates PDFs from log data |
| **CSV Export** | Python `csv` module (built-in) | No extra dependencies |

### How It Works
1. You run one command in the terminal: `python app.py`
2. It opens in your browser at `http://localhost:5000`
3. All data is saved in a single file (`mission_logs.db`) on your laptop
4. To back up your data, just copy that one file

---

## 5. Data Model

### 5.1 Patients Table

Every patient entered into any log is stored here once. A patient can appear in multiple logs.

```
patients
├── id              (auto-generated unique ID)
├── full_name       (text, required)
├── chart_id        (text, required, unique)
├── date_of_birth   (date, required)
├── notes           (text, optional — general notes about the patient)
├── created_at      (auto-generated timestamp)
└── updated_at      (auto-generated timestamp)
```

### 5.2 Log Entries Table

Each entry links a patient to one of the 5 log categories, with category-specific details.

```
log_entries
├── id                  (auto-generated unique ID)
├── patient_id          (links to patients table)
├── log_category        (one of: Priority | Dermatology | Laser | Guzman Referrals | Darlene Prosthetics)
├── date_of_encounter   (date, optional)
├── notes               (text, optional — log-specific notes)
├── status              (Pending | In Progress | Completed — optional)
├── follow_up_date      (date, optional)
├── advocate            (text, optional — Priority Patients & Dermatology)
├── community           (text, optional — Priority Patients & Dermatology)
├── problem             (text, optional — Guzman Referrals only)
├── appointment_timeframe (text, optional — Guzman Referrals only)
├── procedure_type      (text, optional — Laser only)
├── eye                 (OS | OD | OU, optional — Laser only)
├── laser_date          (date, optional — Laser only)
├── procedure           (text, optional — Dermatology only)
├── derm_date           (date, optional — Dermatology only)
├── created_at          (auto-generated timestamp)
└── updated_at          (auto-generated timestamp)
```

> **Note:** Category-specific fields are only shown in the UI for their respective log types and will be blank for other log types. If you later decide certain logs need additional unique fields (e.g., "Prosthetic Type" for Darlene Prosthetics), we can easily add them.

### 5.3 How the Two Tables Relate

```
┌──────────────┐        ┌──────────────────┐
│   patients   │ 1───┐  │   log_entries    │
│──────────────│     │  │──────────────────│
│ id           │     └──│ patient_id       │
│ full_name    │        │ log_category     │
│ chart_id     │        │ date_of_encounter│
│ date_of_birth│        │ notes            │
│ notes        │        │ status           │
└──────────────┘        │ follow_up_date   │
                        │ advocate         │
                        │ community        │
                        │ problem          │
                        │ appt_timeframe   │
                        │ procedure_type   │
                        │ eye              │
                        │ laser_date       │
                        │ procedure        │
                        │ derm_date        │
                        └──────────────────┘

One patient → many log entries
(e.g., same patient can be in Dermatology AND Priority logs)
```

---

## 6. Features

### 6.1 Dashboard (Home Page)
- Summary cards showing the count of patients in each of the 5 logs
- Quick "Add Patient" button directly on the dashboard
- Quick "Add to Log" button to assign an existing patient to a log
- Recent activity feed (last 10 entries added/updated)

### 6.2 Log Views (One Page Per Log)
- Table view showing all patients in that log category
- Columns: Full Name, Chart ID, Date of Birth, Date of Encounter, Status, Notes
- Click a row to view/edit the full entry
- "Add Patient to This Log" button

### 6.3 Patient Management
- Add a new patient (Full Name, Chart ID, Date of Birth)
- Edit patient details
- Delete a patient (with confirmation)
- View which logs a patient appears in

### 6.4 Search & Filter
- Search across all logs by patient name or Chart ID
- Filter each log by status (Pending / In Progress / Completed)
- Filter by date range

### 6.5 Export
- **CSV Export**: Download any log as a `.csv` file (opens in Excel)
- **PDF Export**: Download any log as a formatted `.pdf` document
- Export all logs at once, or one at a time

---

## 7. User Interface Mockup (Text)

```
┌─────────────────────────────────────────────────────────┐
│  🏥 Medical Mission Logs          [Search: _________ ]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  DASHBOARD                          [+ Add Patient]     │
│                                                         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐             │
│  │ Priority  │ │ Dermatol. │ │  Laser    │             │
│  │   12 pts  │ │   8 pts   │ │  15 pts   │             │
│  └───────────┘ └───────────┘ └───────────┘             │
│  ┌───────────┐ ┌───────────┐                            │
│  │ Guzman    │ │ Darlene   │                            │
│  │  Referrals│ │Prosthetics│                            │
│  │   6 pts   │ │   4 pts   │                            │
│  └───────────┘ └───────────┘                            │
│                                                         │
│  RECENT ACTIVITY                                        │
│  • Added Juan Garcia to Dermatology — Mar 8            │
│  • Updated Maria Lopez (Priority) — Mar 8              │
│                                                         │
├───────┬───────┬───────┬───────────┬───────────┬────────┤
│ Home  │Priori.│Derma. │  Laser    │  Guzman   │Darlene │
└───────┴───────┴───────┴───────────┴───────────┴────────┘
```

---

## 8. Project Structure

```
logs/
├── app.py                  # Main application — run this to start
├── database.py             # Database setup and helper functions
├── models.py               # Patient and LogEntry data models
├── export.py               # CSV and PDF export functions
├── mission_logs.db         # SQLite database file (auto-created)
├── templates/              # HTML pages
│   ├── base.html           #   Shared layout (header, nav, footer)
│   ├── dashboard.html      #   Dashboard / home page
│   ├── log_view.html       #   Individual log category view
│   ├── patient_form.html   #   Add/edit patient form
│   └── log_entry_form.html #   Add/edit log entry form
├── static/                 # CSS, JavaScript
│   ├── style.css
│   └── app.js
├── PLAN.md                 # This document
└── README.md               # How to run the app
```

---

## 9. How to Run (Preview)

Once built, running the app will be this simple:

```bash
# First time only — install dependencies:
pip install flask weasyprint

# Start the app:
cd /Users/kyleeaton/dr_projects/logs
python app.py

# Then open your browser to:
# http://localhost:5000
```

---

## 10. Next Steps

1. ✅ ~~Define requirements~~ — Done
2. **You review this plan** — approve or suggest changes
3. **You provide additional fields** for each log category (when ready)
4. **I build the app** — can start with the core fields (Full Name, Chart ID, DOB) and add more later
5. **You test it** on your laptop
6. **We refine** based on your feedback

---

## 11. Decisions Log

| Date | Decision |
|---|---|
| 2026-03-08 | Initial plan created |
| 2026-03-08 | Stack decided: Python/Flask + SQLite (local laptop app) |
| 2026-03-08 | Single user, no auth, no HIPAA |
| 2026-03-08 | Core fields: Full Name, Chart ID, Date of Birth |
| 2026-03-08 | Features: Dashboard, search/filter, CSV export, PDF export |
| 2026-03-08 | **BUILD STARTED** — Basic fields (Full Name, Chart ID, DOB), unique fields per log to be added later |

---

*App has been built! Run `python app.py` and open http://localhost:5000*
