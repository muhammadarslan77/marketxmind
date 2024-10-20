import time
import requests
import threading
from datetime import datetime
#from app.models.models import Member, Transaction, Notification
from config import Config
from urllib.parse import quote

class WhatsAppBulk:
    def __init__(self) -> None:
        self.API_KEY = Config.TEXTME_API_KEY

    def send_notification(self, company_id: int, transaction_number: int, wait: int = 8.1):
        def run(num, message):
            encoded_text = quote(message)
            txtBotURL = f'https://api.textmebot.com/send.php?recipient={num}&apikey={self.API_KEY}&text={encoded_text}'
            try:
                response = requests.get(txtBotURL)
                print(response.text)
            except requests.RequestException as e:
                print(f"Error sending message to {num}: {e}")

        def multhread():
            try:
                notifications = db.session.query(Notification).filter_by(company_id=company_id, transaction_number=transaction_number).all()
                for notification in notifications:
                    transaction_counts = (
                        db.session.query(Transaction.member_id, db.func.count(Transaction.id).label('count'))
                        .filter_by(company_id=company_id, is_rewarded=False)
                        .group_by(Transaction.member_id)
                        .having(db.func.count(Transaction.id) == transaction_number)
                        .all()
                    )

                    for count in transaction_counts:
                        member = db.session.query(Member).filter_by(id=count.member_id).first()
                        if member and member.phone_number:
                            message = notification.text
                            thread = threading.Thread(target=run, args=(member.phone_number, message), name=f't{count.member_id}')
                            thread.start()
                            if wait:
                                time.sleep(wait)
            except Exception as e:
                print(f"Error sending notifications: {e}")

        return multhread()

    def send_scheduled_notifications(self):
        def run(num, message):
            encoded_text = quote(message)
            txtBotURL = f'https://api.textmebot.com/send.php?recipient={num}&apikey={self.API_KEY}&text={encoded_text}'
            try:
                response = requests.get(txtBotURL)
                print(response.text)
            except requests.RequestException as e:
                print(f"Error sending message to {num}: {e}")

        def multhread():
            try:
                today = datetime.utcnow().date()
                notifications = db.session.query(Notification).filter_by(is_scheduler=True).filter(Notification.next_date_notification <= today).all()
                for notification in notifications:
                    transaction_counts = (
                        db.session.query(Transaction.member_id, db.func.count(Transaction.id).label('count'))
                        .filter_by(company_id=notification.company_id, is_rewarded=False)
                        .group_by(Transaction.member_id)
                        .having(db.func.count(Transaction.id) == notification.transaction_number)
                        .all()
                    )

                    for count in transaction_counts:
                        member = db.session.query(Member).filter_by(id=count.member_id).first()
                        if member and member.phone_number:
                            message = notification.text
                            thread = threading.Thread(target=run, args=(member.phone_number, message), name=f't{count.member_id}')
                            thread.start()
                            if wait:
                                time.sleep(wait)
                    
                    notification.update_next_notification()
            except Exception as e:
                print(f"Error sending scheduled notifications: {e}")

        return multhread()
