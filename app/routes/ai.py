# blueprints/ai.py

from flask import Blueprint, jsonify, request
from app import db
from app.models.customer import Customer
from app.models.campaign import  Campaign

ai = Blueprint('ai', __name__)

@ai.route('/calculate_tier/<int:customer_id>', methods=['POST'])
def calculate_tier(customer_id):
    use_external = request.json.get('use_external', False)  # Determine if we use external AI

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    customer.calculate_tier_AI(use_external=use_external)
    return jsonify({"message": "Customer tier calculated successfully", "tier": customer.tier})

@ai.route('/generate_campaign/<int:campaign_id>/<int:customer_id>', methods=['POST'])
def generate_campaign(campaign_id, customer_id):
    use_external = request.json.get('use_external', False)  # Use external AI or internal
    campaign = Campaign.query.get(campaign_id)
    customer = Customer.query.get(customer_id)

    if not campaign or not customer:
        return jsonify({"error": "Campaign or Customer not found"}), 404

    content = customer.generate_campaign_content(campaign, use_external=use_external)
    return jsonify({"message": "Campaign content generated", "content": content})
