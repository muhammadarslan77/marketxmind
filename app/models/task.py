from app import db
from datetime import datetime

class TaskInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    task_seq = db.Column(db.Integer, nullable=False)
    task_seq_prev = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), nullable=False)
    review_notes = db.Column(db.Text)
    is_payment = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.String(100), nullable=False)
    assigned_to = db.Column(db.String(100), nullable=False)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, nullable=True)
  
    def __repr__(self):
        return f'<TaskInvoice {self.id}>'

        
class TaskFlowInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_seq = db.Column(db.Integer, nullable=False)
    task_seq_prev = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(255), nullable=False)
    review_notes = db.Column(db.Text)
    is_payment = db.Column(db.Boolean, default=False)
    customer_email = db.Column(db.Boolean, default=True)
    customer_wa = db.Column(db.Boolean, default=True)
    customer_sms = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(100), nullable=False)
    assigned_to = db.Column(db.String(255), nullable=False)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, nullable=True)
    def __repr__(self):
        return f'<TaskFlowInvoice {self.id}>'
 