"""
Medical Mission Logs — Main Application
Run this file to start the app: python app.py
Then open http://localhost:5000 in your browser.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, Response
from database import (
    init_db, LOG_CATEGORIES,
    get_all_patients, get_patient, create_patient, update_patient, delete_patient,
    get_log_entries, get_log_entry, create_log_entry, update_log_entry, delete_log_entry,
    get_dashboard_counts, get_recent_activity, get_patient_logs,
)
from export import export_csv, export_pdf, export_all_zip
from backup import (
    start_backup_scheduler, create_backup, list_backups,
    find_closest_backup, restore_backup, RESTORE_SLOTS,
)

app = Flask(__name__)
app.secret_key = "medical-mission-logs-local-key"


# --- Dashboard ---

@app.route("/")
def dashboard():
    counts = get_dashboard_counts()
    recent = get_recent_activity(10)
    patients = get_all_patients()
    return render_template(
        "dashboard.html",
        counts=counts,
        recent=recent,
        categories=LOG_CATEGORIES,
        patients=patients,
    )


# --- Log Views ---

@app.route("/log/<category>")
def log_view(category):
    if category not in LOG_CATEGORIES:
        flash(f"Unknown log category: {category}", "error")
        return redirect(url_for("dashboard"))

    search = request.args.get("search", "")
    entries = get_log_entries(category, search=search or None)
    patients = get_all_patients()

    return render_template(
        "log_view.html",
        category=category,
        entries=entries,
        patients=patients,
        categories=LOG_CATEGORIES,
        search=search,
    )


# --- Patient CRUD ---

@app.route("/patient/add", methods=["POST"])
def add_patient():
    full_name = request.form.get("full_name", "").strip()
    chart_id = request.form.get("chart_id", "").strip()
    date_of_birth = request.form.get("date_of_birth", "").strip()
    notes = request.form.get("notes", "").strip()
    redirect_to = request.form.get("redirect_to", "/")

    if not full_name or not chart_id or not date_of_birth:
        flash("Full Name, Chart ID, and Date of Birth are required.", "error")
        return redirect(redirect_to)

    try:
        patient_id = create_patient(full_name, chart_id, date_of_birth, notes)
        flash(f"Patient '{full_name}' added successfully.", "success")
    except Exception as e:
        if "UNIQUE" in str(e):
            flash(f"A patient with Chart ID '{chart_id}' already exists.", "error")
        else:
            flash(f"Error adding patient: {e}", "error")
        return redirect(redirect_to)

    # Add to any selected log categories
    add_to_logs = request.form.getlist("add_to_log")
    added_logs = []
    for log_cat in add_to_logs:
        if log_cat and log_cat in LOG_CATEGORIES:
            try:
                # Gather category-specific fields
                kwargs = {}
                if log_cat == "Priority Patients":
                    kwargs["advocate"] = request.form.get("priority_advocate", "").strip()
                    kwargs["community"] = request.form.get("priority_community", "").strip()
                    kwargs["surgery_type"] = request.form.get("priority_surgery_type", "").strip()
                elif log_cat == "Dermatology":
                    kwargs["advocate"] = request.form.get("derm_advocate", "").strip()
                    kwargs["community"] = request.form.get("derm_community", "").strip()
                    kwargs["procedure"] = request.form.get("derm_procedure", "").strip()
                    kwargs["derm_date"] = request.form.get("derm_derm_date", "").strip()
                    kwargs["procedure_count"] = request.form.get("derm_procedure_count", 1, type=int) or 1
                elif log_cat == "Laser":
                    kwargs["procedure_type"] = request.form.get("laser_procedure_type", "").strip()
                    kwargs["eye"] = request.form.get("laser_eye", "").strip()
                    kwargs["laser_date"] = request.form.get("laser_laser_date", "").strip()
                elif log_cat == "Guzman Referrals":
                    kwargs["problem"] = request.form.get("guzman_problem", "").strip()
                    kwargs["appointment_timeframe"] = request.form.get("guzman_appointment_timeframe", "").strip()
                elif log_cat == "Darlene Prosthetics":
                    kwargs["notes"] = request.form.get("darlene_notes", "").strip()
                create_log_entry(patient_id, log_cat, **kwargs)
                added_logs.append(log_cat)
            except Exception:
                pass
    if added_logs:
        flash(f"Also added to: {', '.join(added_logs)}", "success")

    return redirect(redirect_to)


@app.route("/patient/<int:patient_id>")
def view_patient(patient_id):
    patient = get_patient(patient_id)
    if not patient:
        flash("Patient not found.", "error")
        return redirect(url_for("dashboard"))

    logs = get_patient_logs(patient_id)
    return render_template(
        "patient_view.html",
        patient=patient,
        logs=logs,
        categories=LOG_CATEGORIES,
    )


@app.route("/patient/<int:patient_id>/edit", methods=["GET", "POST"])
def edit_patient(patient_id):
    patient = get_patient(patient_id)
    if not patient:
        flash("Patient not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        chart_id = request.form.get("chart_id", "").strip()
        date_of_birth = request.form.get("date_of_birth", "").strip()
        notes = request.form.get("notes", "").strip()

        if not full_name or not chart_id or not date_of_birth:
            flash("Full Name, Chart ID, and Date of Birth are required.", "error")
            return render_template("patient_edit.html", patient=patient, categories=LOG_CATEGORIES)

        try:
            update_patient(patient_id, full_name, chart_id, date_of_birth, notes)
            flash(f"Patient '{full_name}' updated.", "success")
            return redirect(url_for("view_patient", patient_id=patient_id))
        except Exception as e:
            if "UNIQUE" in str(e):
                flash(f"A patient with Chart ID '{chart_id}' already exists.", "error")
            else:
                flash(f"Error updating patient: {e}", "error")

    return render_template("patient_edit.html", patient=patient, categories=LOG_CATEGORIES)


@app.route("/patient/<int:patient_id>/delete", methods=["POST"])
def remove_patient(patient_id):
    patient = get_patient(patient_id)
    if patient:
        delete_patient(patient_id)
        flash(f"Patient '{patient['full_name']}' deleted.", "success")
    return redirect(url_for("dashboard"))


# --- Log Entry CRUD ---

@app.route("/log-entry/add", methods=["POST"])
def add_log_entry():
    patient_id = request.form.get("patient_id", type=int)
    log_category = request.form.get("log_category", "")
    notes = request.form.get("notes", "").strip()
    follow_up_date = request.form.get("follow_up_date", "").strip() or None
    advocate = request.form.get("advocate", "").strip()
    community = request.form.get("community", "").strip()
    problem = request.form.get("problem", "").strip()
    appointment_timeframe = request.form.get("appointment_timeframe", "").strip()
    procedure_type = request.form.get("procedure_type", "").strip()
    eye = request.form.get("eye", "").strip()
    laser_date = request.form.get("laser_date", "").strip()
    procedure = request.form.get("procedure", "").strip()
    derm_date = request.form.get("derm_date", "").strip()
    surgery_type = request.form.get("surgery_type", "").strip()
    procedure_count = request.form.get("procedure_count", 1, type=int) or 1
    redirect_to = request.form.get("redirect_to", "/")

    if not patient_id or log_category not in LOG_CATEGORIES:
        flash("Please select a patient and a valid log category.", "error")
        return redirect(redirect_to)

    create_log_entry(patient_id, log_category, notes, follow_up_date,
                     advocate, community, problem, appointment_timeframe,
                     procedure_type, eye, laser_date, procedure, derm_date, surgery_type, procedure_count)
    patient = get_patient(patient_id)
    name = patient["full_name"] if patient else "Patient"
    flash(f"'{name}' added to {log_category} log.", "success")
    return redirect(redirect_to)


@app.route("/log-entry/<int:entry_id>/edit", methods=["GET", "POST"])
def edit_log_entry(entry_id):
    entry = get_log_entry(entry_id)
    if not entry:
        flash("Log entry not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        notes = request.form.get("notes", "").strip()
        follow_up_date = request.form.get("follow_up_date", "").strip() or None
        advocate = request.form.get("advocate", "").strip()
        community = request.form.get("community", "").strip()
        problem = request.form.get("problem", "").strip()
        appointment_timeframe = request.form.get("appointment_timeframe", "").strip()
        procedure_type = request.form.get("procedure_type", "").strip()
        eye = request.form.get("eye", "").strip()
        laser_date = request.form.get("laser_date", "").strip()
        procedure = request.form.get("procedure", "").strip()
        derm_date = request.form.get("derm_date", "").strip()
        surgery_type = request.form.get("surgery_type", "").strip()
        procedure_count = request.form.get("procedure_count", 1, type=int) or 1

        update_log_entry(entry_id, notes, follow_up_date,
                         advocate, community, problem, appointment_timeframe,
                         procedure_type, eye, laser_date, procedure, derm_date, surgery_type, procedure_count)
        flash("Log entry updated.", "success")
        return redirect(url_for("log_view", category=entry["log_category"]))

    return render_template("log_entry_edit.html", entry=entry, categories=LOG_CATEGORIES)


@app.route("/log-entry/<int:entry_id>/delete", methods=["POST"])
def remove_log_entry(entry_id):
    entry = get_log_entry(entry_id)
    category = entry["log_category"] if entry else None
    delete_log_entry(entry_id)
    flash("Log entry deleted.", "success")
    if category:
        return redirect(url_for("log_view", category=category))
    return redirect(url_for("dashboard"))


# --- Export ---

@app.route("/export/<category>/csv")
def export_log_csv(category):
    if category in LOG_CATEGORIES:
        data = export_csv(category)
        filename = f"{category.lower().replace(' ', '_')}_log.csv"
    else:
        flash("Unknown category.", "error")
        return redirect(url_for("dashboard"))

    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/export/all/zip")
def export_all_zip_route():
    data = export_all_zip()
    return Response(
        data,
        mimetype="application/zip",
        headers={"Content-Disposition": "attachment; filename=mission_logs_export.zip"},
    )


@app.route("/export/<category>/pdf")
def export_log_pdf(category):
    if category not in LOG_CATEGORIES:
        flash("Unknown category.", "error")
        return redirect(url_for("dashboard"))

    data = export_pdf(category)
    filename = f"{category.lower().replace(' ', '_')}_log.pdf"

    return Response(
        data,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# --- Search ---

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    patients = get_all_patients(search=query) if query else []
    return render_template(
        "search_results.html",
        query=query,
        patients=patients,
        categories=LOG_CATEGORIES,
    )


# --- Backup & Restore ---

@app.route("/backups")
def backups_page():
    backups = list_backups()
    return render_template(
        "backups.html",
        backups=backups,
        restore_slots=RESTORE_SLOTS,
        categories=LOG_CATEGORIES,
    )


@app.route("/backup/create", methods=["POST"])
def manual_backup():
    path = create_backup()
    if path:
        flash("Manual backup created successfully.", "success")
    else:
        flash("Failed to create backup — database file not found.", "error")
    return redirect(url_for("backups_page"))


@app.route("/backup/restore", methods=["POST"])
def restore_from_backup():
    filename = request.form.get("filename", "")
    if not filename:
        flash("No backup file specified.", "error")
        return redirect(url_for("backups_page"))

    success, message = restore_backup(filename)
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
    return redirect(url_for("backups_page"))


@app.route("/backup/restore-slot", methods=["POST"])
def restore_from_slot():
    minutes = request.form.get("minutes", type=int)
    if minutes is None:
        flash("Invalid time slot.", "error")
        return redirect(url_for("backups_page"))

    backup = find_closest_backup(minutes)
    if not backup:
        flash("No backup available for that time slot. Backups are created every 5 minutes — please wait a bit and try again.", "error")
        return redirect(url_for("backups_page"))

    success, message = restore_backup(backup["filename"])
    if success:
        flash(f"Restored to backup from {backup['age_label']} ({backup['timestamp']}). {message}", "success")
    else:
        flash(message, "error")
    return redirect(url_for("backups_page"))


# --- Start the app ---

if __name__ == "__main__":
    init_db()
    start_backup_scheduler()
    print("\n  Medical Mission Logs is running!")
    print("  Open your browser to: http://localhost:9874\n")
    app.run(debug=True, port=9874)
