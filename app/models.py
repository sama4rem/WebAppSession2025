# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, date # Importons 'date' explicitement pour plus de clarté

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    school_name = db.Column(db.String(150), nullable=True)
    birth_date = db.Column(db.String(10), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    sessions = db.relationship('Session', backref='student', lazy=True, cascade="all, delete-orphan")


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    remark = db.Column(db.Text, nullable=True)
    
    # ✅ LIGNE CORRIGÉE CI-DESSOUS
    date = db.Column(db.Date, default=date.today, nullable=False)
    
    selected = db.Column(db.Boolean, default=False, nullable=False)


class ProgrammeSelection(db.Model):
    __tablename__ = "selections_maths_2bac"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    chapter_name = db.Column(db.String(255), nullable=False)

    student = db.relationship("Student", backref="programme_selections")