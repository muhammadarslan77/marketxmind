# ml/churn_prediction.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for,  flash, current_app
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import joblib
from app.models.customer import Customer
from app.models.invoice import Invoice
from app import db

def train_churn_model_v2(data):
    X = data[['total_spent', 'frequency_of_purchase', 'inactivity_period']]
    y = data['churn']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
    
    model = LogisticRegression()
    model.fit(X_train, y_train)
    return model

def train_churn_model():
    
    customers = db.session.query(Customer).all()
     
    if not customers:
        print(f"No customers found for company ID {company_id} and branch ID {branch_id}.")
        return
    
    # Prepare data for training
    data = []
    for customer in customers:
        data.append({
            'company': company_id,
            'points': customer.loyalty.points if customer.loyalty else 0,
            'total_transactions': get_total_transactions(customer.id),
            'membership_duration': (datetime.utcnow() - customer.created_date).days,
            'churn': customer.status == 'churned' 
        })
    
    df = pd.DataFrame(data)
    
    # Ensure the dataframe has enough records to train the model
    if df.empty or len(df) < 10:  # Assuming 10 is a minimum threshold for training
        print("Not enough data to train the model.")
        return
    
    # Feature selection
    X = df[['company', 'points', 'total_transactions', 'membership_duration']]
    y = df['churn']
    
    # Split the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train the RandomForest model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate the model
    accuracy = model.score(X_test, y_test)
    print(f'Churn Model Accuracy: {accuracy}')
    
    # Save the trained model
    joblib.dump(model, f'models/churn_model_{company_id}.pkl')  # Save model specific to company


def predict_churn(customer_id):

       
    customer = Customer.query.get(customer_id)
    model = joblib.load('models/churn_model_{company_id}.pk')
    features = [
        customer.loyalty.points if customer.loyalty else 0,
        get_total_transactions(customer.id),
        (datetime.utcnow() - customer.created_date).days
    ]
    prediction = model.predict([features])
    return prediction[0]

def get_total_transactions(customer_id):
    return Invoice.query.filter_by(customer_id=customer_id).count()
