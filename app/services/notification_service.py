# services/notification_service.py
from flask_mail import Message
from app import mail
from app.models.customer import Customer

def send_promotional_email(customer_id, subject, body):
    customer = Customer.query.get(customer_id)
    if customer and customer.email:
        msg = Message(subject, recipients=[customer.email], body=body)
        mail.send(msg)

def send_sms(customer_phone, message):
    # Menggunakan Twilio atau layanan SMS lainnya
    from twilio.rest import Client
    account_sid = 'your_account_sid'
    auth_token = 'your_auth_token'
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=message,
        from_='+1234567890',
        to=customer_phone
    )
