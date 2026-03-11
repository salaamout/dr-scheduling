"""
VHP Patient Database - Route Handlers
"""
import logging
from collections import defaultdict
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from .backup import RESTORE_SLOTS
from .forms import PROCEDURE_OPTIONS, PatientForm
from .models import Patient, db

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_patient_from_form(form):
    """Build a Patient instance from a validated form.

    Shared by new_patient and duplicate_patient to eliminate code duplication.
    """
    return Patient(
        surgery_type=form.surgery_type.data,
        surgery_date=form.surgery_date.data,
        chart_number=form.chart_number.data,
        name=form.name.data,
        age=form.age.data,
        sex=form.sex.data,
        eye=form.eye.data or None,
        procedure=form.procedure.data,
        advocate=form.advocate.data,
        community=form.community.data,
        number=form.number.data,
        notes=form.notes.data,
        cancelled=form.cancelled.data,
    )


def _preserve_filters():
    """Return a dict of the current filter/sort query parameters."""
    params = {}
    for key in ('surgery_date', 'surgery_type', 'sort', 'order', 'search'):
        val = request.args.get(key)
        if val:
            params[key] = val
    return params


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route('/')
def index():
    """Display the main patient listing with optional filtering and sorting."""
    query = Patient.query.filter_by(deleted=False)

    surgery_date = request.args.get('surgery_date')
    surgery_type = request.args.get('surgery_type')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '').strip()

    if surgery_date:
        query = query.filter(Patient.surgery_date == surgery_date)
    if surgery_type:
        query = query.filter(Patient.surgery_type == surgery_type)

    # Search by chart number or name within the filtered set
    if search:
        like_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Patient.chart_number.ilike(like_term),
                Patient.name.ilike(like_term),
            )
        )

    if sort:
        sort_column = getattr(Patient, sort, Patient.surgery_date)
        if order == 'desc':
            sort_column = sort_column.desc()
        patients = query.order_by(sort_column).all()
    else:
        patients = query.order_by(
            Patient.surgery_date,
            Patient.surgery_type,
            Patient.number,
        ).all()

    # Count excludes cancelled patients
    patient_count = sum(1 for p in patients if not p.cancelled)

    filters = _preserve_filters()

    return render_template(
        'index.html',
        patients=patients,
        sort=sort,
        order=order,
        patient_count=patient_count,
        filters=filters,
    )


@bp.route('/trash')
def trash():
    """Show soft-deleted patients."""
    deleted_patients = (
        Patient.query.filter_by(deleted=True)
        .order_by(Patient.surgery_date)
        .all()
    )
    return render_template('trash.html', patients=deleted_patients)


@bp.route('/restore/<int:patient_id>', methods=['POST'])
def restore_patient(patient_id):
    """Restore a soft-deleted patient."""
    patient = Patient.query.get_or_404(patient_id)
    patient.deleted = False
    db.session.commit()
    flash(f'Patient {patient.name} restored.', 'success')
    return redirect(url_for('main.trash'))


@bp.route('/new', methods=['GET', 'POST'])
def new_patient():
    """Create a new patient record."""
    form = PatientForm()

    surgery_type = request.args.get('surgery_type')
    if surgery_type and request.method == 'GET':
        form.surgery_type.data = surgery_type

    if request.method == 'GET' and not form.surgery_date.data:
        form.surgery_date.data = datetime.now().date()

    # Capture return filters so we can redirect back with them
    filters = {}
    for key in ('surgery_date', 'surgery_type', 'sort', 'order', 'search'):
        val = request.args.get(key)
        if val:
            filters[key] = val

    if form.validate_on_submit():
        patient = _create_patient_from_form(form)
        db.session.add(patient)
        db.session.commit()
        flash('Patient created successfully.', 'success')
        return redirect(url_for('main.index', **filters))

    return render_template(
        'patient_form.html', form=form, filters=filters,
        procedure_options=PROCEDURE_OPTIONS,
    )


@bp.route('/print/<int:patient_id>')
def print_patient(patient_id):
    """Print a patient record.

    Supported print types (via ?type= query param):
      - laserband  (default)
      - log        (single surgery log)

    Returns 400 for unknown print types.
    """
    print_type = request.args.get('type', 'laserband')
    patient = Patient.query.get_or_404(patient_id)

    if print_type == 'laserband':
        return render_template('print_stickers.html', p=patient)
    elif print_type == 'log':
        log_type = request.args.get('log_type', 'Single')
        if log_type == 'Single':
            return render_template('print_log.html', p=patient, log_type=log_type)

    flash('Unknown print type requested.', 'error')
    return redirect(url_for('main.index')), 400


@bp.route('/print/daily-log')
def print_daily_log():
    """Print the daily surgery log for a given date and surgery type."""
    surgery_date_str = request.args.get('surgery_date')
    surgery_type = request.args.get('surgery_type')

    if not surgery_date_str or not surgery_type:
        flash('Missing surgery date or type.', 'error')
        return redirect(url_for('main.index'))

    try:
        surgery_date = datetime.strptime(surgery_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
        return redirect(url_for('main.index'))

    patients = (
        Patient.query.filter_by(
            surgery_type=surgery_type,
            surgery_date=surgery_date,
            deleted=False,
        )
        .order_by(Patient.number)
        .all()
    )

    return render_template(
        'print_log.html',
        patients=patients,
        log_type='Daily',
        surgery_type=surgery_type,
        surgery_date=surgery_date_str,
    )


@bp.route('/edit/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    """Edit an existing patient record."""
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)

    # Capture return filters so we can redirect back with them
    filters = {}
    for key in ('surgery_date', 'surgery_type', 'sort', 'order', 'search'):
        val = request.args.get(key)
        if val:
            filters[key] = val

    if form.validate_on_submit():
        form.populate_obj(patient)
        # Ensure empty eye value is stored as None
        if not patient.eye:
            patient.eye = None
        db.session.commit()
        flash('Patient updated successfully.', 'success')
        return redirect(url_for('main.index', **filters))

    return render_template(
        'patient_form.html', form=form, edit=True, filters=filters,
        procedure_options=PROCEDURE_OPTIONS,
    )


@bp.route('/delete/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    """Soft-delete a patient (move to trash)."""
    patient = Patient.query.get_or_404(patient_id)
    patient.deleted = True
    db.session.commit()
    flash(f'Patient {patient.name} moved to trash.', 'success')

    # Preserve filters when redirecting back
    filters = {}
    for key in ('surgery_date', 'surgery_type', 'sort', 'order', 'search'):
        val = request.form.get(key) or request.args.get(key)
        if val:
            filters[key] = val
    return redirect(url_for('main.index', **filters))


@bp.route('/duplicate/<int:patient_id>', methods=['GET', 'POST'])
def duplicate_patient(patient_id):
    """Duplicate an existing patient record."""
    # Capture return filters
    filters = {}
    for key in ('surgery_date', 'surgery_type', 'sort', 'order', 'search'):
        val = request.args.get(key)
        if val:
            filters[key] = val

    if request.method == 'GET':
        patient = Patient.query.get_or_404(patient_id)
        form = PatientForm(obj=patient)
        form.number.data = ''  # Clear surgery number for the new record
        return render_template(
            'patient_form.html', form=form, duplicate=True, filters=filters,
            procedure_options=PROCEDURE_OPTIONS,
        )

    form = PatientForm()
    if form.validate_on_submit():
        patient = _create_patient_from_form(form)
        db.session.add(patient)
        db.session.commit()
        flash('Patient duplicated successfully.', 'success')
        return redirect(url_for('main.index', **filters))

    return render_template(
        'patient_form.html', form=form, duplicate=True, filters=filters,
        procedure_options=PROCEDURE_OPTIONS,
    )


@bp.route('/update-number/<int:patient_id>', methods=['POST'])
def update_number(patient_id):
    """Inline update of surgery number from the main page."""
    patient = Patient.query.get_or_404(patient_id)
    data = request.get_json()
    if data and 'number' in data:
        patient.number = data['number']
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False, error='Missing number'), 400


@bp.route('/toggle-cancelled/<int:patient_id>', methods=['POST'])
def toggle_cancelled(patient_id):
    """Toggle the cancelled status of a patient."""
    patient = Patient.query.get_or_404(patient_id)
    patient.cancelled = not patient.cancelled
    db.session.commit()
    return jsonify(success=True, cancelled=patient.cancelled)


@bp.route('/count-summary')
def count_summary():
    """Show a summary of surgery counts grouped by date and surgery type."""
    patients = (
        Patient.query
        .filter_by(deleted=False, cancelled=False)
        .order_by(Patient.surgery_date, Patient.surgery_type)
        .all()
    )

    # Build summary: {date: {surgery_type: count}}
    summary = defaultdict(lambda: defaultdict(int))
    all_types = set()
    for p in patients:
        summary[p.surgery_date][p.surgery_type] += 1
        all_types.add(p.surgery_type)

    # Sort dates and types
    sorted_dates = sorted(summary.keys())
    sorted_types = sorted(all_types)

    # Build totals per date and grand totals per type
    date_totals = {d: sum(summary[d].values()) for d in sorted_dates}
    type_totals = defaultdict(int)
    for d in sorted_dates:
        for t in sorted_types:
            type_totals[t] += summary[d].get(t, 0)
    grand_total = sum(date_totals.values())

    return render_template(
        'count_summary.html',
        summary=summary,
        sorted_dates=sorted_dates,
        sorted_types=sorted_types,
        date_totals=date_totals,
        type_totals=type_totals,
        grand_total=grand_total,
    )


# ---------------------------------------------------------------------------
# Backup & Restore
# ---------------------------------------------------------------------------

@bp.route('/backups')
def backups_page():
    """Display the backup management page."""
    from . import backup_manager

    backups = backup_manager.list_backups()
    return render_template(
        'backups.html',
        backups=backups,
        restore_slots=RESTORE_SLOTS,
    )


@bp.route('/backup/create', methods=['POST'])
def manual_backup():
    """Create a manual backup immediately."""
    from . import backup_manager

    path = backup_manager.create_backup()
    if path:
        flash('Manual backup created successfully.', 'success')
    else:
        flash('Failed to create backup — database file not found.', 'error')
    return redirect(url_for('main.backups_page'))


@bp.route('/backup/restore', methods=['POST'])
def restore_from_backup():
    """Restore the database from a specific backup file."""
    from . import backup_manager

    filename = request.form.get('filename', '')
    if not filename:
        flash('No backup file specified.', 'error')
        return redirect(url_for('main.backups_page'))

    success, message = backup_manager.restore_backup(filename)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('main.backups_page'))


@bp.route('/backup/restore-slot', methods=['POST'])
def restore_from_slot():
    """Restore the database from the closest backup to a given time slot."""
    from . import backup_manager

    minutes = request.form.get('minutes', type=int)
    if minutes is None:
        flash('Invalid time slot.', 'error')
        return redirect(url_for('main.backups_page'))

    backup = backup_manager.find_closest_backup(minutes)
    if not backup:
        flash(
            'No backup available for that time slot. '
            'Backups are created every 10 minutes — please wait and try again.',
            'error',
        )
        return redirect(url_for('main.backups_page'))

    success, message = backup_manager.restore_backup(backup['filename'])
    if success:
        flash(
            f"Restored to backup from {backup['age_label']} "
            f"({backup['timestamp']}). {message}",
            'success',
        )
    else:
        flash(message, 'error')
    return redirect(url_for('main.backups_page'))


@bp.route('/backup/delete', methods=['POST'])
def delete_backup():
    """Delete a single backup file."""
    from . import backup_manager

    filename = request.form.get('filename', '')
    if not filename:
        flash('No backup file specified.', 'error')
        return redirect(url_for('main.backups_page'))

    success, message = backup_manager.delete_backup(filename)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('main.backups_page'))
