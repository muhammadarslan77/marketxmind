# services/retention_service.py
from app.ml.churn_prediction import predict_churn
from app.services.notification_service import send_promotional_email, send_sms
from app.models.customer import Customer

def retain_customers():
    customers = Customer.query.all()
    for customer in customers:
        if predict_churn(customer.id):
            # Kirimkan promosi retensi
            subject = "Kami Akan Merindukan Anda!"
            body = "Dapatkan diskon 20% untuk pembelian berikutnya sebagai terima kasih atas kesetiaan Anda."
            send_promotional_email(customer.id, subject, body)
            if customer.phone:
                send_sms(customer.phone, "Dapatkan diskon 20% untuk pembelian berikutnya sebagai terima kasih atas kesetiaan Anda.")
