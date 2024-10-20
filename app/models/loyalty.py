#loyalty.py
from app import db
from datetime import datetime

class LoyaltyProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    points = db.Column(db.Float, default=0.0)
    points_rp = db.Column(db.Float, default=0.0) #
    points_active = db.Column(db.Boolean, default=True)
    discount = db.Column(db.Float, default=0.0)
    discount_type = db.Column(db.Float, default=0.0) #('1', 'Persen'), ('2', 'Rupiah'), ('3', 'Gratis')
    discount_repeat_number = db.Column(db.Integer, nullable=True, default=1)
    discount_repeat = db.Column(db.Boolean, default=True)
    discount_active = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    is_newcustomer = db.Column(db.Boolean, default=True)
    is_oldcustomer = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, onupdate=datetime.utcnow)
    # Relationship
    tiers = db.relationship('LoyaltyTier', backref='loyalty_program', lazy=True)  
    
    @property
    def campaigns(self):
        from app.models.campaign import Campaign
        return db.relationship('Campaign', backref='loyalty_program', lazy=True)

class LoyaltyTier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('loyalty_program.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    points_threshold = db.Column(db.Integer, nullable=False)  
    benefits = db.Column(db.String(255), nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, onupdate=datetime.utcnow)

class CustomerLoyalty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('loyalty_program.id'), nullable=False)  
    tier_id = db.Column(db.Integer, db.ForeignKey('loyalty_tier.id'), nullable=True)
    total_points_earned = db.Column(db.Float, nullable=True, default=0.0)
    total_points_used = db.Column(db.Float, nullable=True, default=0.0)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
class ReferralProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('loyalty_program.id'), nullable=False)
    referrer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    referee_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    reward_points = db.Column(db.Integer, default=0)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
