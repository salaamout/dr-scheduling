"""
VHP Patient Database - Database Models
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Patient(db.Model):
    """Patient record model."""

    id = db.Column(db.Integer, primary_key=True)
    surgery_type = db.Column(db.String(50), nullable=False)
    surgery_date = db.Column(db.Date, nullable=False)
    chart_number = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(240), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    eye = db.Column(db.String(2))  # OD, OS, or OU
    procedure = db.Column(db.Text, nullable=False)
    advocate = db.Column(db.String(120))
    community = db.Column(db.String(120))
    number = db.Column(db.String(50))  # Surgery number — string to allow any format
    notes = db.Column(db.Text)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    cancelled = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Patient {self.name}>'
