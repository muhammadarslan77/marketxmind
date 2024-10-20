#campaign.py
from app import db
from datetime import datetime

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(250), nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('loyalty_program.id'), nullable=False)
    transaction_number = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)  
    text_email = db.Column(db.Text, nullable=False) 
    text_sms = db.Column(db.String(250), nullable=True)
    is_scheduler = db.Column(db.Boolean, default=False)
    interval_days = db.Column(db.Integer, nullable=True)
    current_date_notification = db.Column(db.Date, nullable=True)
    next_date_notification = db.Column(db.Date, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    whatsapp = db.Column(db.Boolean, default=True)
    sms = db.Column(db.Boolean, default=True)
    email = db.Column(db.Boolean, default=True)
    campaigns_metrics = db.relationship('CampaignMetric', backref='campaign', lazy=True)
    @property
    def loyalty_program(self):
        from app.models.loyalty import LoyaltyProgram  # Deferred import
        return db.relationship('LoyaltyProgram', backref='campaigns', lazy=True)
        
    def generate_campaign_content(self):
        # This is where AI/ML comes in to create personalized content
        pass

class CampaignMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    recorded_date = db.Column(db.DateTime, default=datetime.utcnow)
