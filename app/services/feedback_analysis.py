# services/feedback_analysis.py
from app.models.feedback import CustomerFeedback
from collections import defaultdict

def analyze_feedback():
    feedbacks = CustomerFeedback.query.all()
    analysis = defaultdict(list)
    for feedback in feedbacks:
        analysis[feedback.campaign_id].append({
            'rating': feedback.rating,
            'text': feedback.feedback_text
        })
    # Implementasikan logika analisis, misalnya rata-rata rating per kampanye
    campaign_ratings = {}
    for campaign_id, items in analysis.items():
        ratings = [item['rating'] for item in items if item['rating'] is not None]
        if ratings:
            average = sum(ratings) / len(ratings)
            campaign_ratings[campaign_id] = average
    return campaign_ratings
