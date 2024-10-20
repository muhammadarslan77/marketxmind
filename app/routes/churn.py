# api/churn.py
from flask import Blueprint, jsonify
from app.ml.churn_prediction import predict_churn

churn = Blueprint('churn', __name__)

@churn.route('/churn/predict/<int:customer_id>', methods=['GET'])
def churn_prediction(customer_id):
    prediction = predict_churn(customer_id)
    return jsonify({'customer_id': customer_id, 'churn_prediction': bool(prediction)}), 200
