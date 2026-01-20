from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    result = db.Column(db.String(128))
    units = db.Column(db.String(32))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
