#customer.py
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from app import db

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    address_line1 = db.Column(db.String(100))
    address_line2 = db.Column(db.String(100))
    city = db.Column(db.String(100))
    zip = db.Column(db.String(20))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    company_name = db.Column(db.String(100))
    receivable_balance = db.Column(db.Float, default=0.0)
    credit_limit = db.Column(db.Integer, default=0)
    type = db.Column(db.String(20))
    status = db.Column(db.String(20))
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, nullable=True)
    preferences = db.Column(db.String(255), nullable=True)  

    customer_loyalties = db.relationship('CustomerLoyalty', backref='customer_ref', lazy=True, overlaps="customer,loyalty")
    invoices = db.relationship('Invoice', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name}>'
        
    def generate_unique_key(self):
        if self.user_app_id and self.phone:
            return f'{self.user_app_id}_{self.phone}'
        return None

    def add_points(self):
        from app.models.loyalty import LoyaltyProgram, CustomerLoyalty
        if not self.loyalty:
            self.loyalty = CustomerLoyalty(
                customer_id=self.id, 
                program_id=program.id, 
                total_points_earned=0,
                total_points_used=0
            )
        self.update_tier(program)

    def update_tier(self, program):
        from app.models.loyalty import LoyaltyTier
        tiers = LoyaltyTier.query.filter_by(program_id=program.id).order_by(LoyaltyTier.points_threshold.desc()).all()
        for tier in tiers:
            if self.loyalty.points >= tier.points_threshold:
                self.loyalty.tier_id = tier.id
                break
        db.session.commit()
        
    def calculate_tier_AI(self):
        '''
        # Sample feature generation: customer activity data
        X, y = self.generate_customer_activity_data()
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Preprocess data (scale if necessary)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        # Train a RandomForest model for tier prediction
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Predict the customer's tier
        customer_data = self.get_customer_data()  # Generate customer feature vector
        customer_data_scaled = scaler.transform([customer_data])
        predicted_tier = model.predict(customer_data_scaled)

        # Update customer's loyalty tier
        self.loyalty.tier_id = predicted_tier[0]
        db.session.commit()
        '''
        from services.ai_service import ai_service
        if use_external:
            self.tier = ai_service.calculate_tier_external(self)
        else:
            self.tier = ai_service.calculate_tier_internal(self)
        db.session.commit()

    def generate_customer_activity_data(self):
        """
        Generate synthetic data for training the ML model.
        X contains feature vectors (e.g., total purchase amount, number of purchases).
        y contains labels (tier categories).
        """
        # Example: Generating dummy data for simplicity
        X = np.random.rand(1000, 5)  # 1000 samples with 5 features (purchase history, loyalty points, etc.)
        y = np.random.randint(0, 3, 1000)  # 3 loyalty tiers
        return X, y

    def get_customer_data(self):
        """
        Get real customer activity data for tier prediction.
        """
        # Example feature vector for this customer
        customer_data = [
            self.loyalty.loyalty_points_earned,  # Example features
            self.total_spent(),
            self.purchase_frequency(),
            # Add more relevant customer features
        ]
        return customer_data
        
    def generate_campaign_content(self, campaign, use_external=False):
        """
        Generate personalized campaign content using AI/ML.
        """
        from services.ai_service import ai_service
        if use_external:
            return ai_service.generate_campaign_content_external(campaign, self)
        else:
            return ai_service.generate_campaign_content_internal(campaign, self)
