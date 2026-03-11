from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Optional
import os
import shutil
from datetime import datetime
import glob

app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'  # Setting a fixed secret key for development
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True  # Enable CSRF protection for forms
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Don't check CSRF on all requests by default
app.config['WTF_CSRF_TIME_LIMIT'] = None  # Disable CSRF token expiration
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cookies in browser
app.config['SESSION_COOKIE_SECURE'] = False  # Allow cookies over HTTP (not just HTTPS)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Protect against XSS
app.config['BACKUP_DIR'] = os.path.join(app.instance_path, 'backups')  # Directory for database backups
app.config['MAX_BACKUPS'] = 100  # Maximum number of backup files to keep
app.config['BACKUP_INTERVAL'] = 600  # Backup interval in seconds (10 minutes)
app.config['PERIODIC_BACKUP_INTERVAL'] = 21600  # Keep one backup per 6 hours for older backups

db = SQLAlchemy(app)

# Create backup directory if it doesn't exist
os.makedirs(app.config['BACKUP_DIR'], exist_ok=True)

def get_backup_datetime(backup_path):
    """Extract datetime from backup filename."""
    filename = os.path.basename(backup_path)
    timestamp = filename.replace('patients_', '').replace('.db', '')
    return datetime.strptime(timestamp, '%Y%m%d_%H%M%S')

def should_keep_backup(backup_path, periodic_backups):
    """Determine if a backup should be kept based on periodic retention rules."""
    backup_time = get_backup_datetime(backup_path)
    
    # Always keep if it's our only backup for a 6-hour period
    period_start = backup_time.replace(hour=(backup_time.hour // 6) * 6, minute=0, second=0)
    period_key = period_start.strftime('%Y%m%d_%H')
    
    if period_key not in periodic_backups:
        periodic_backups[period_key] = backup_path
        return True
    
    # If we already have a backup for this period, keep the one closest to the period start
    existing_backup_time = get_backup_datetime(periodic_backups[period_key])
    if abs(backup_time - period_start) < abs(existing_backup_time - period_start):
        # This backup is better for the period
        periodic_backups[period_key] = backup_path
        return True
    
    return False

def create_db_backup():
    """Create a timestamped backup of the database."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_path = os.path.join(app.instance_path, 'patients.db')
    backup_path = os.path.join(app.config['BACKUP_DIR'], f'patients_{timestamp}.db')
    
    # Only create backup if the database exists
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        
        # Get all backups sorted by date
        backups = sorted(glob.glob(os.path.join(app.config['BACKUP_DIR'], 'patients_*.db')))
        
        if len(backups) > app.config['MAX_BACKUPS']:
            # Keep track of the best backup for each 6-hour period
            periodic_backups = {}
            
            # Always keep the most recent MAX_BACKUPS/2 backups
            keep_recent = app.config['MAX_BACKUPS'] // 2
            to_evaluate = backups[:-keep_recent] if len(backups) > keep_recent else []
            
            # Evaluate older backups for periodic retention
            files_to_remove = []
            for backup in to_evaluate:
                if not should_keep_backup(backup, periodic_backups):
                    files_to_remove.append(backup)
            
            # Remove files that don't meet retention criteria
            for backup in files_to_remove:
                try:
                    os.remove(backup)
                except OSError:
                    pass  # Handle potential file system errors gracefully

# Track the last backup time
_last_backup = datetime.min

@app.before_request
def check_backup():
    """Check if it's time to create a new backup before processing a request."""
    global _last_backup
    now = datetime.now()
    
    # Create a backup if enough time has passed since the last one
    if (now - _last_backup).total_seconds() >= app.config['BACKUP_INTERVAL']:
        create_db_backup()
        _last_backup = now

# Initialize database tables when app starts
@app.before_request
def initialize_database():
    """Initialize database tables if they don't exist."""
    # Remove this function after first call to avoid repeated checks
    app.before_request_funcs[None].remove(initialize_database)
    
    with app.app_context():
        db.create_all()
        print("Database initialized successfully")

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    surgery_type = db.Column(db.String(50), nullable=False)
    surgery_date = db.Column(db.Date, nullable=False)
    chart_number = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    procedure = db.Column(db.Text, nullable=False)
    advocate = db.Column(db.String(120))
    community = db.Column(db.String(120))
    number = db.Column(db.String(50))  # Using string to allow for any format
    notes = db.Column(db.Text)
    deleted = db.Column(db.Boolean, default=False, nullable=False)  # Flag for soft delete

class PatientForm(FlaskForm):
    surgery_type = SelectField('Type of Surgery', 
                             choices=[('cataract', 'Cataract'),
                                     ('plastics', 'Plastics'),
                                     ('strabismus', 'Strabismus'),
                                     ('pterygium', 'Pterygium'),
                                     ('derm', 'Dermatology')],
                             validators=[DataRequired()])
    surgery_date = DateField('Date of Surgery', format='%Y-%m-%d', validators=[DataRequired()])
    chart_number = StringField('Chart #', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    sex = SelectField('Sex', 
                     choices=[('M', 'Male'),
                             ('F', 'Female'),
                             ('O', 'Other')],
                     validators=[DataRequired()])
    procedure = TextAreaField('Procedure', validators=[DataRequired()])
    advocate = StringField('Advocate', validators=[Optional()])
    community = StringField('Community', validators=[Optional()])
    number = StringField('Surgery Number', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save')

@app.route('/')
def index():
    query = Patient.query.filter_by(deleted=False)

    surgery_date = request.args.get('surgery_date')
    surgery_type = request.args.get('surgery_type')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    if surgery_date:
        query = query.filter(Patient.surgery_date == surgery_date)
    if surgery_type:
        query = query.filter(Patient.surgery_type == surgery_type)

    # Handle sorting
    if sort:
        sort_column = getattr(Patient, sort, Patient.surgery_date)
        if order == 'desc':
            sort_column = sort_column.desc()
        patients = query.order_by(sort_column).all()
    else:
        # Default sorting: date, surgery type, surgery number
        patients = query.order_by(
            Patient.surgery_date,
            Patient.surgery_type,
            Patient.number
        ).all()
    
    return render_template('index.html', patients=patients, sort=sort, order=order)

@app.route('/trash')
def trash():
    deleted_patients = Patient.query.filter_by(deleted=True).order_by(Patient.surgery_date).all()
    return render_template('trash.html', patients=deleted_patients)

@app.route('/restore/<int:patient_id>', methods=['POST'])
def restore_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.deleted = False
    db.session.commit()
    return redirect(url_for('trash'))

@app.route('/new', methods=['GET', 'POST'])
def new_patient():
    form = PatientForm()
    # Set default surgery type from URL parameter if present
    surgery_type = request.args.get('surgery_type')
    if surgery_type and request.method == 'GET':
        form.surgery_type.data = surgery_type
    # Set default surgery date to today if it's a GET request
    if request.method == 'GET' and not form.surgery_date.data:
        form.surgery_date.data = datetime.now().date()
    if form.validate_on_submit():
        patient = Patient(
            surgery_type=form.surgery_type.data,
            surgery_date=form.surgery_date.data,
            chart_number=form.chart_number.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            age=form.age.data,
            sex=form.sex.data,
            procedure=form.procedure.data,
            advocate=form.advocate.data,
            community=form.community.data,
            number=form.number.data,
            notes=form.notes.data
        )
        db.session.add(patient)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('patient_form.html', form=form)

@app.route('/print/<int:patient_id>')
def print_patient(patient_id):
    print_type = request.args.get('type', 'laserband')
    patient = Patient.query.get_or_404(patient_id)
    
    if print_type == 'laserband':
        return render_template('print_stickers.html', p=patient)
    elif print_type == 'log':
        log_type = request.args.get('log_type', 'Single')
        if log_type == 'Single':
            return render_template('print_log.html', p=patient, log_type=log_type)

@app.route('/print/daily-log')
def print_daily_log():
    surgery_date_str = request.args.get('surgery_date')
    surgery_type = request.args.get('surgery_type')
    
    if not surgery_date_str or not surgery_type:
        return "Missing surgery date or type", 400
    
    # Parse the date string
    surgery_date = datetime.strptime(surgery_date_str, '%Y-%m-%d').date()
    
    # Get all patients for the specified surgery type and date
    patients = Patient.query.filter_by(
        surgery_type=surgery_type,
        surgery_date=surgery_date,
        deleted=False
    ).order_by(Patient.number).all()
    
    return render_template('print_log.html', 
                         patients=patients,
                         log_type='Daily',
                         surgery_type=surgery_type,
                         surgery_date=surgery_date_str)

@app.route('/edit/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('patient_form.html', form=form, edit=True)

@app.route('/delete/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.deleted = True
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/duplicate/<int:patient_id>', methods=['GET', 'POST'])
def duplicate_patient(patient_id):
    if request.method == 'GET':
        patient = Patient.query.get_or_404(patient_id)
        form = PatientForm(obj=patient)
        # Surgery date is now copied automatically
        form.number.data = ''          # Clear the surgery number for the new record
        return render_template('patient_form.html', form=form, duplicate=True)
    else:  # POST
        form = PatientForm()
        if form.validate_on_submit():
            patient = Patient(
                surgery_type=form.surgery_type.data,
                surgery_date=form.surgery_date.data,
                chart_number=form.chart_number.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                age=form.age.data,
                sex=form.sex.data,
                procedure=form.procedure.data,
                advocate=form.advocate.data,
                community=form.community.data,
                number=form.number.data,
                notes=form.notes.data
            )
            db.session.add(patient)
            db.session.commit()
            return redirect(url_for('index'))
        return render_template('patient_form.html', form=form, duplicate=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Get port from environment variable or use default (5001 to avoid macOS Control Center on 5000)
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=True, port=port, host='127.0.0.1')