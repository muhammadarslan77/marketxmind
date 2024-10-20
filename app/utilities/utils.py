from datetime import datetime, timedelta
import random
import string
import requests
import os
import logging
import re
import json
from config import Config
from urllib.parse import quote
import uuid
import re

import base64

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def is_valid_email(email_val):
    # Define the regular expression for a valid email address
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
    # Use re.match() to check if email_val matches the regex
    if re.match(email_regex, email_val):
        return True
    else:
        return False

def current_utc_datetime():
    return datetime.utcnow()
   
def format_currency(amount):
    if amount is None:
        return "0"   
    return "{:,.0f}".format(amount).replace(",", ".")

def tax_rate():
    return 0.11

def calculate_total_price(price_per_month, months):
    # Ensure inputs are of correct type
    try:
        price_per_month = float(price_per_month)
        months = int(months)
    except (ValueError, TypeError) as e:
        raise ValueError("Invalid input types for price_per_month or months") from e

    # Determine the discount based on the number of months
    if months == 12:
        discount = 0.12
    elif months == 6:
        discount = 0.08
    elif months == 1:
        discount = 0.02
    else:
        discount = 0

    # Calculate the total price
    total_price = price_per_month * months * (1 - discount)
    
    # Return the total price rounded to 2 decimal places
    return round(total_price, 2)

    
def calculate_total_tax(amount):
    # Ensure inputs are of correct type
    try:
        amount = float(amount)
    except (ValueError, TypeError) as e:
        raise ValueError("Invalid input type for amount") from e

    # Get the global tax rate
    rate = tax_rate()
    total_tax = amount * rate
    
    return round(total_tax, 2)  # Return rounded value


def generate_security_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def calculate_invoice_totals(details):
    total_amount = sum(detail['unit_price'] * detail['quantity'] for detail in details)
    total_discount = sum(detail['discount'] for detail in details)
    total_tax = total_amount * tax_rate
    net_amount = total_amount - total_discount + total_tax
    return total_amount, total_discount, total_tax, net_amount
    
def format_phone_number(phone_number, default_country_code='+62'):
    """
    Formats a phone number to a standardized international format.
    
    Args:
        phone_number (str): The phone number to format.
        default_country_code (str): The default country code to use if none is provided. Defaults to '+62' (Indonesia).

    Returns:
        str: The formatted phone number.
    """
    # Remove all non-numeric characters
    phone_number = re.sub(r'\D', '', phone_number)
    country_code_numeric = default_country_code.lstrip('+')

    if phone_number.startswith(country_code_numeric):
        if phone_number.startswith(country_code_numeric + '0'):
            phone_number = phone_number[len(country_code_numeric) + 1:]
        else:
            return f'+{phone_number}'
    elif phone_number.startswith('0'):
        phone_number = phone_number.lstrip('0')
    
    return f'{default_country_code}{phone_number}'
    
    
def send_whatsapp_message(phone_number, message, api_key):
    phone_no = format_phone_number(phone_number)
    url = 'https://app.watbiz.com/api/whatsapp/send'

    headers = {
    'Api-key': api_key,
    'Content-Type': 'application/json'
        }

    postdata = {
    "contact": [
        {
            "number": phone_no,
            "message": message
        }
        ]
    }

    response = requests.post(url, data=json.dumps(postdata), headers=headers)
    return 
        
 
def send_whatsapp_image(phone_number, image_filename, caption , api_key):
    phone_no = format_phone_number(phone_number)
    image_url = f"http://127.0.0.1:5000/{image_filename}"
    
    url = 'https://app.watbiz.com/api/whatsapp/send'

    headers = {
    'Api-key': api_key,
    'Content-Type': 'application/json'
        }

    postdata = {
    "contact": [
        {
            "number": phone_no,
            "message": caption,
            "media" : "image",
            "url" :image_url
        }
        ]
    }

    response = requests.post(url, data=json.dumps(postdata), headers=headers)
    return 

def send_whatsapp_pdf(phone_number, pdf_url, api_key):
    phone_no = format_phone_number(phone_number)
    url = 'https://app.watbiz.com/api/whatsapp/send'

    headers = {
    'Api-key': api_key,
    'Content-Type': 'application/json'
        }

    postdata = {
    "contact": [
        {
            "number": phone_no,
            "message": caption,
            "media" : "document",
            "url" :pdf_url
        }
        ]
    }

    response = requests.post(url, data=json.dumps(postdata), headers=headers)
    return 

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_payment_id():
    unique_id = uuid.uuid4().int  # Generate a unique identifier (UUID as an integer)
    identifier = str(unique_id)[:15]  # Convert to string and take the first 15 digits
    check_digit = calculate_check_digit(identifier)  # Calculate the check digit
    payment_id = f"{identifier}{check_digit}"  # Combine the identifier with the check digit
    return payment_id

def calculate_check_digit(identifier):

    def luhn_algorithm(number):
        digits = [int(d) for d in number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            double = d * 2
            checksum += double if double < 10 else double - 9
        return (10 - (checksum % 10)) % 10

    return str(luhn_algorithm(identifier))

def validate_invoice_id(invoice_id):
  
    if len(invoice_id) != 7:  # Example length: 6 digits + 1 check digit
        return False  # Invalid length for invoice ID

    identifier = invoice_id[:6]
    check_digit = invoice_id[6]

    # Validate identifier part (must be all digits)
    if not identifier.isdigit() or not check_digit.isdigit():
        return False

    # Calculate and verify check digit
    calculated_check_digit = calculate_check_digit(identifier)
    return check_digit == calculated_check_digit

def validate_payment_id(payment_id):
    """
    Validate a payment ID by checking its format and the check digit.
    """
    if len(payment_id) != 12:  # Example length: 11 digits + 1 check digit
        return False  # Invalid length for payment ID

    identifier = payment_id[:11]
    check_digit = payment_id[11]

    # Validate identifier part (must be all digits)
    if not identifier.isdigit() or not check_digit.isdigit():
        return False

    # Calculate and verify check digit
    calculated_check_digit = calculate_check_digit(identifier)
    return check_digit == calculated_check_digit


    
    


