# services/dynamic_discount.py
from app.models.customer import Customer
from app.services.notification_service import send_promotional_email

def apply_dynamic_discounts():
    customers = Customer.query.all()
    for customer in customers:
        # Contoh: berikan diskon jika poin di atas threshold tertentu
        if customer.loyalty and customer.loyalty.points > 1000:
            discount = 20  # 20% diskon
            subject = "Terima Kasih atas Loyalitas Anda!"
            body = f"Dapatkan diskon {discount}% untuk pembelian berikutnya sebagai apresiasi kami."
            send_promotional_email(customer.id, subject, body)
