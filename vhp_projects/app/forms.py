"""
VHP Patient Database - WTForms Form Definitions
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, TextAreaField, SubmitField,
    SelectField, IntegerField, RadioField, BooleanField,
)
from wtforms.validators import DataRequired, Optional


# Procedure autofill options per surgery type
PROCEDURE_OPTIONS = {
    'cataract': ['Cataract', 'Bilateral Lenses', 'Vitrectomy'],
    'plastics': [
        'Blepharoplasty', 'Ptosis', 'Enucleation', 'Evisceration', 'DCR',
        'Cantoplasty', 'Ectropion Repair', 'Cyst Removal', 'Socket Repair',
        'Papilloma', 'Dermis Fat Graft', 'Blocked Tear Duct',
    ],
    'strabismus': ['Strabismus'],
    'pterygium': [],
    'derm': [],
}


class PatientForm(FlaskForm):
    """Form for creating and editing patient records."""

    surgery_type = SelectField(
        'Type of Surgery',
        choices=[
            ('cataract', 'Cataract'),
            ('plastics', 'Plastics'),
            ('strabismus', 'Strabismus'),
            ('pterygium', 'Pterygium'),
            ('derm', 'Dermatology'),
        ],
        validators=[DataRequired()],
    )
    surgery_date = DateField(
        'Date of Surgery', format='%Y-%m-%d', validators=[DataRequired()]
    )
    chart_number = StringField('Chart #', validators=[DataRequired()])
    name = StringField('Patient Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    sex = SelectField(
        'Sex',
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        validators=[DataRequired()],
    )
    procedure = TextAreaField('Procedure', validators=[DataRequired()])
    eye = RadioField(
        'Eye',
        choices=[('', 'N/A'), ('OD', 'OD (Right)'), ('OS', 'OS (Left)'), ('OU', 'OU (Both)')],
        default='',
        validators=[Optional()],
    )
    advocate = StringField('Advocate', validators=[Optional()])
    community = StringField('Community', validators=[Optional()])
    number = StringField('Surgery Number', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    cancelled = BooleanField('Cancelled', validators=[Optional()])
    submit = SubmitField('Save')
