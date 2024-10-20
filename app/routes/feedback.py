# api/feedback.py
from flask import Blueprint, request, jsonify
from app.models.feedback import CustomerFeedback
from app import db

feedback = Blueprint('feedback', __name__)

@feedback.route('/feedback', methods=['POST'])
def collect_feedback():
    data = request.json
    feedback = CustomerFeedback(
        customer_id=data['customer_id'],
        campaign_id=data['campaign_id'],
        feedback_text=data.get('feedback_text'),
        rating=data.get('rating')
    )
    db.session.add(feedback)
    db.session.commit()
    return jsonify({'message': 'Feedback submitted'}), 201
