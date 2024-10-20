# api/segmentation.py
from flask import Blueprint, request, jsonify
from app.models.customer import Customer
from app.models.loyalty import CustomerLoyalty

segmentation = Blueprint('segmentation', __name__)

@segmentation.route('/segmentation', methods=['POST'])
def segment_customers():
    data = request.json
    # Contoh sederhana: segment berdasarkan poin
    min_points = data.get('min_points', 0)
    max_points = data.get('max_points', None)
    
    query = Customer.query.join(CustomerLoyalty).filter(CustomerLoyalty.points >= min_points)
    if max_points:
        query = query.filter(CustomerLoyalty.points <= max_points)
    
    customers = query.all()
    customer_list = [{'id': c.id, 'name': c.name, 'points': c.loyalty.points} for c in customers]
    return jsonify({'customers': customer_list}), 200
