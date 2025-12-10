from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON 
db = SQLAlchemy()

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(255))

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(64), db.ForeignKey('case.case_id'), nullable=False)
    test_name = db.Column(db.String(64))
    sample_type = db.Column(db.String(64))
    image_id = db.Column(db.String(255))  # Filename/image identifier
    result = db.Column(JSON)
    units = db.Column(db.String(32))
    report_version = db.Column(db.String(32)) 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # utcnow is now deprecated, but this works with the current environment
