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
from export import export_csv, export_pdf, export_all_csv

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
    status = request.args.get("status", "")
    entries = get_log_entries(category, search=search or None, status=status or None)
    patients = get_all_patients()

    return render_template(
        "log_view.html",
        category=category,
        entries=entries,
        patients=patients,
        categories=LOG_CATEGORIES,
        search=search,
        status_filter=status,
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
                create_log_entry(patient_id, log_cat)
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
    date_of_encounter = request.form.get("date_of_encounter", "").strip() or None
    notes = request.form.get("notes", "").strip()
    status = request.form.get("status", "Pending")
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
    redirect_to = request.form.get("redirect_to", "/")

    if not patient_id or log_category not in LOG_CATEGORIES:
        flash("Please select a patient and a valid log category.", "error")
        return redirect(redirect_to)

    create_log_entry(patient_id, log_category, date_of_encounter, notes, status, follow_up_date,
                     advocate, community, problem, appointment_timeframe,
                     procedure_type, eye, laser_date, procedure, derm_date)
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
        date_of_encounter = request.form.get("date_of_encounter", "").strip() or None
        notes = request.form.get("notes", "").strip()
        status = request.form.get("status", "Pending")
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

        update_log_entry(entry_id, date_of_encounter, notes, status, follow_up_date,
                         advocate, community, problem, appointment_timeframe,
                         procedure_type, eye, laser_date, procedure, derm_date)
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
    if category == "all":
        data = export_all_csv()
        filename = "all_mission_logs.csv"
    elif category in LOG_CATEGORIES:
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


# --- Start the app ---

if __name__ == "__main__":
    init_db()
    print("\n  Medical Mission Logs is running!")
    print("  Open your browser to: http://localhost:5000\n")
    app.run(debug=True, port=5000)
