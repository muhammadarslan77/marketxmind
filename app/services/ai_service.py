# services/ai_service.py

import random
import logging
from app import db
from app.models.customer import Customer
from app.models.campaign import  Campaign

class AIService:
    def calculate_tier_internal(self, customer):
        """
        Internal AI/ML logic to calculate customer tier based on activity.
        """
        # Example of a simple rule-based ML logic
        activity_score = self.calculate_activity_score(customer)
        if activity_score > 1000:
            return "Gold"
        elif 500 <= activity_score <= 999:
            return "Silver"
        else:
            return "Bronze"

    def calculate_activity_score(self, customer):
        """
        Calculate activity score based on customer behavior.
        More complex AI/ML models can be integrated here.
        """
        orders = len(customer.orders)  # Number of orders
        total_spent = sum(order.total_amount for order in customer.orders)
        last_order_days = (datetime.utcnow() - customer.orders[-1].created_date).days if customer.orders else 0

        score = orders * 10 + total_spent / 100 - last_order_days / 30  # Simplified logic
        return max(0, score)  # Ensure the score is non-negative

    def calculate_tier_external(self, customer):
        """
        Call external AI API to determine customer tier.
        """
        # Example: Integration with OpenAI or any external AI service
        try:
            response = openai.Completion.create(
                engine="gpt-4o",
                prompt=f"Calculate customer tier based on {customer.name}'s purchase history: {customer.orders}",
                max_tokens=50
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"External AI service failed: {e}")
            return "Unknown"  # Fallback

    def generate_campaign_content_internal(self, campaign, customer):
        """
        Generate campaign content using internal logic or ML model.
        """
        customer_name = customer.name
        discount = campaign.discount
        return f"Hi {customer_name}, enjoy a {discount}% discount on your next purchase!"

    def generate_campaign_content_external(self, campaign, customer):
        """
        Call external AI/ML model to generate personalized campaign content.
        """
        try:
            response = openai.Completion.create(
                engine="gpt-4o",
                prompt=f"Generate a personalized email for {customer.name} promoting {campaign.name} with a discount of {campaign.discount}%",
                max_tokens=150
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"External AI service failed: {e}")
            return "Check out our latest discounts!"  # Fallback content

ai_service = AIService()
