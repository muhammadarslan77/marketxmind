# feedback.py
from app import db
from app.models.loyalty import LoyaltyProgram ,LoyaltyTier, CustomerLoyalty, ReferralProgram
from app.models.customer import Customer
from datetime import datetime

class CustomerFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    feedback_text = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True) 
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

