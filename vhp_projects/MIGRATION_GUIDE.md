# Moving Patient Database to a New Mac

The built `PatientDatabase.app` contains everything — the app, your database, and backups — in a single file.

---

## Steps

### 1. Old Mac — grab the app

If you've been using the **Desktop app**, just copy it — your data is already inside:
```
~/Desktop/PatientDatabase.app
```

> **Note:** If you've been running the app from the terminal (`python run.py`) instead,
> rebuild first so the latest data gets bundled in:
> ```bash
> cd /Users/kyleeaton/dr_projects/vhp_projects
> ./scripts/build_app.sh
> ```
> Then copy `dist/PatientDatabase.app`.

### 2. New Mac — copy and open

- **AirDrop, USB drive, or shared folder** → send `PatientDatabase.app` to the new Mac.
- If macOS blocks it on first launch, run this once:
  ```bash
  xattr -cr /path/to/PatientDatabase.app
  ```
- Double-click to run. Your patients are already there.

That's it. ✅
