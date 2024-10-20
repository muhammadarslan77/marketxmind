from app import db
from app.models.product import Product, UnitList , ProductImage 
from datetime import datetime , timedelta
from sqlalchemy import Enum
from enum import Enum as PyEnum

class InvoiceDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=True,default=0.0)
    unit_price = db.Column(db.Float, nullable=True,default=0)
    unit_name = db.Column(db.String(100), nullable=True, default='Unit')
    discount_code = db.Column(db.String(50),nullable=True, default='')
    discount = db.Column(db.Float, nullable=True,default=0.0)
    total_amount = db.Column(db.Float, nullable=True,default=0.0)
    net_amount = db.Column(db.Float, nullable=True,default=0.0)
    admin_fee = db.Column(db.Float, nullable=True, default=0.0)
    delivery_fee = db.Column(db.Float, nullable=True, default=0.0)
    status = db.Column(db.String(255), default='checkout')  # 'order', 'processing', etc.
    priority_id = db.Column(db.Integer, nullable=True,default=0)
    additional_cost = db.Column(db.Float, nullable=True, default=0.0)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    due_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, nullable=True)
    product = db.relationship('Product', backref='invoice_details', lazy=True)
    def __repr__(self):
        return f'<InvoiceDetail {self.id}>'
    
