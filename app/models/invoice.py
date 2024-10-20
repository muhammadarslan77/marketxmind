#invoice.py
from app import db
import random
from datetime import datetime
from sqlalchemy import UniqueConstraint
from sqlalchemy import Enum
from enum import Enum as PyEnum


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.String(9), nullable=False)  
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    sales_order = db.Column(db.String(250), nullable=True, default='')
    additional_notes = db.Column(db.Text, nullable=True, default='')
    status = db.Column(db.String(255), default='checkout')
    total_amount = db.Column(db.Float, nullable=True, default=0.0)
    discount_code = db.Column(db.String(50),nullable=True, default='')
    total_discount = db.Column(db.Float, nullable=True, default=0.0)
    total_tax = db.Column(db.Float, nullable=True, default=0.0)
    admin_fee = db.Column(db.Float, nullable=True, default=0.0)
    delivery_fee = db.Column(db.Float, nullable=True, default=0.0)
    priority_id = db.Column(db.Integer, nullable=True,default=0)
    priority_terms = db.Column(db.String(50), default='REGULAR')
    additional_cost = db.Column(db.Float, nullable=True, default=0.0)
    net_amount = db.Column(db.Float, nullable=True, default=0.0)
    paid_amount = db.Column(db.Float, nullable=True, default=0.0)
    security_code = db.Column(db.String(255), unique=True)
    tasks_seq = db.Column(db.Integer, nullable=True, default=0)
    tasks = db.relationship('TaskInvoice', backref='invoice', lazy=True)
    details = db.relationship('InvoiceDetail', backref='invoice', lazy=True)
    payment_id = db.Column(db.Integer, nullable=True,default=0)
    payment_terms = db.Column(db.String(50), default='COD')
    delivery_terms = db.Column(db.String(50), default='FOB')
    terms_disc = db.Column(db.Float, nullable=True, default=0.0)
    terms_days_disc = db.Column(db.Integer, nullable=True, default=0)
    terms_days_due = db.Column(db.Integer, nullable=True, default=0)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    due_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    delivery_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, nullable=True)
    loyalty_points_earned = db.Column(db.Float, nullable=True, default=0.0)
    loyalty_points_used = db.Column(db.Float, nullable=True, default=0.0)
    discount_applied = db.Column(db.Float, nullable=True, default=0.0)
    loyalty_program_id = db.Column(db.Integer, db.ForeignKey('loyalty_program.id'), nullable=True)  
   
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.invoice_id = self.generate_invoice_id()

    def generate_invoice_id(self):
        """Generate a unique invoice ID."""
        current_year = datetime.now().year
        year_component = f"{1 + (current_year - 2024):02d}"  # 2-digit year calculation

        while True:
            # Generate 6-digit random number
            identifier = f"{random.randint(100000, 999999)}"
            check_digit = self.calculate_check_digit(identifier)
            invoice_id = f"{year_component}{identifier}{check_digit}"

            # Ensure the invoice_id is unique
            if not Invoice.query.filter_by(invoice_id=invoice_id).first():
                break

        return invoice_id

    def calculate_check_digit(self, identifier):
        """Calculate a check digit using the Luhn algorithm."""
        def luhn_algorithm(number):
            digits = [int(d) for d in number]
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                double = d * 2
                checksum += double if double < 10 else double - 9
            return (10 - (checksum % 10)) % 10

        return str(luhn_algorithm(identifier))
        
    def apply_loyalty_points(self):

        customer_loyalty = CustomerLoyalty.query.filter_by(customer_id=self.customer_id, program_id=self.loyalty_program_id).first()
        if customer_loyalty:
            loyalty_program = LoyaltyProgram.query.get(customer_loyalty.program_id)
            if loyalty_program and loyalty_program.is_active and loyalty_program.points_active:
                points_earned = (self.total_amount - self.total_discount) / loyalty_program.points
                customer_loyalty.total_points_earned += points_earned
                next_tier = LoyaltyTier.query.filter(
                    LoyaltyTier.program_id == customer_loyalty.program_id,
                    LoyaltyTier.points_threshold > customer_loyalty.tier_id  # Points threshold of next tiers
                ).order_by(LoyaltyTier.points_threshold.asc()).first()

                if next_tier and customer_loyalty.total_points_earned >= next_tier.points_threshold:
                    customer_loyalty.tier_id = next_tier.id
                    print(f"Customer ID {self.customer_id} has been upgraded to Tier ID {next_tier.id}.")
                db.session.commit()
               
        
    def apply_loyalty_point_rewards(self):

        customer_loyalty = CustomerLoyalty.query.filter_by(customer_id=self.customer_id, program_id=self.loyalty_program_id).first()
        if customer_loyalty:
            loyalty_program = LoyaltyProgram.query.get(customer_loyalty.program_id)
            if loyalty_program and loyalty_program.is_active and loyalty_program.points_active:
                if (self.total_amount - self.total_discount) > (loyalty_program.points_rp * (customer_loyalty.total_points_earned -  customer_loyalty.total_points_used)) :
                    points_used = (customer_loyalty.total_points_earned -  customer_loyalty.total_points_used)
                else :
                    points_used=  self.total_discount / loyalty_program.points_rp
                customer_loyalty.total_points_used +=  points_used
                self.discount_applied =  points_used *  loyalty_program.points_rp
                self.total_discount +=   self.discount_applied
                self.net_amount -= self.discount_applied
                db.session.commit()
                
    def apply_loyalty_discount_rewards(self):

        customer_loyalty = CustomerLoyalty.query.filter_by(customer_id=self.customer_id, program_id=self.loyalty_program_id).first()
        if customer_loyalty:
            loyalty_program = LoyaltyProgram.query.get(customer_loyalty.program_id)
            if loyalty_program and loyalty_program.is_active and loyalty_program.discount_active:
                    if loyalty_program.discount_type == 1:  # Percent discount
                        self.discount_applied = self.total_amount * (loyalty_program.discount / 100)
                    elif campaign.discount_type == 2:  # Fixed amount discount
                        self.discount_applied = loyalty_program.discount
                    elif campaign.discount_type == 3:  # Free item discount
                        self.discount_applied = self.total_amount
                    else :
                        self.discount_applied =  0
                    self  .total_discount +=   self.discount_applied
                    self.net_amount -= self.discount_applied
                    db.session.commit()
                
    def __repr__(self):
        return f"<Invoice {self.invoice_id}>"
    
        
class PaymentTerms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    day_discount = db.Column(db.Integer, nullable=True, default=0)
    persen_discount = db.Column(db.Float, nullable=True, default=0.0)
    day_duedate = db.Column(db.Integer, nullable=True, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_payment = db.Column(db.Boolean, default=False)
    is_default = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, nullable=True)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())


class PriorityList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, default="REGULAR")
    AdditionalCost = db.Column(db.Float, nullable=False, default=0.0)
    ProcessingTimeValue = db.Column(db.Float, nullable=False, default=0.0)
    ProcessingTimeUnit = db.Column(db.String(10), nullable=False, default="DAY")
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, nullable=True)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())