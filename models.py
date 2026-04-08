from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    role = db.Column(db.String(50))
    scans = db.relationship('Scan', backref='owner', lazy=True)

# class Scan(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     disease_name = db.Column(db.String(100), nullable=False)
#     confidence = db.Column(db.Float, nullable=False)
#     image_file = db.Column(db.String(100), nullable=False)
#     treatment = db.Column(db.Text)
#     prevention = db.Column(db.Text)
#     date_created = db.Column(db.DateTime, default=datetime.utcnow)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    disease_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    prevention = db.Column(db.Text)

    supplement_name = db.Column(db.String(200))
    supplement_link = db.Column(db.String(500))
    supplement_image = db.Column(db.String(200))  
    confidence = db.Column(db.Float)

    image_file = db.Column(db.String(200))

    date_scanned = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))