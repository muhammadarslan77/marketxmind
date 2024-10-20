# services/campaign_service.py
from app import db
from app.models.campaign import Campaign
from app.models.customer import Customer
from app.models.loyalty import CustomerLoyalty
from datetime import datetime

def evaluate_campaigns():
    today = datetime.utcnow()
    active_campaigns = Campaign.query.filter(
        Campaign.start_date <= today,
        Campaign.end_date >= today,
        Campaign.status == 'active'
    ).all()
    
    for campaign in active_campaigns:
        # Logika evaluasi, misalnya menghitung jumlah transaksi
        transactions = get_transactions_for_campaign(campaign)
        metric = CampaignMetric(
            campaign_id=campaign.id,
            metric_name='total_transactions',
            metric_value=len(transactions)
        )
        db.session.add(metric)
        
        # Berikan poin kepada pelanggan yang memenuhi syarat
        for txn in transactions:
            customer = Customer.query.get(txn.customer_id)
            customer.add_points(campaign.program, txn.amount * campaign.program.points_per_dollar)
    
    db.session.commit()

def get_transactions_for_campaign(campaign):
    # Implementasi tergantung pada model transaksi Anda
    # Contoh:
    return Transaction.query.filter(
        Transaction.date >= campaign.start_date,
        Transaction.date <= campaign.end_date
    ).all()
