from app import db

import uuid
from sqlalchemy import func

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(20), unique=True, nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_date = db.Column(db.DateTime, default=func.current_timestamp())
    status = db.Column(db.String(20), default='completed')
    created_date = db.Column(db.DateTime, default=func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=func.current_timestamp())
    user_id = db.Column(db.Integer, nullable=True)
  