
from flask import Blueprint, request, jsonify, render_template, redirect, url_for,  flash, current_app
from app import db
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.loyalty import CustomerLoyalty, LoyaltyProgram
from app.forms.customer import CustomerForm,  ReportFormCustomer
from app.utilities.utils import send_whatsapp_message, send_whatsapp_image, send_whatsapp_pdf
from app.utilities.utils import format_phone_number , format_currency
from datetime import datetime
from config import Config
import os
from math import ceil
from sqlalchemy import func, case
from sqlalchemy.exc import IntegrityError,DataError
from PIL import Image
import base64
import logging
from flask_mail import Message
from transformers import LlamaTokenizer, LlamaForCausalLM
import torch


customer = Blueprint('customer', __name__)
model_name = Config.AIML_MODEL_NAME
tokenizer = LlamaTokenizer.from_pretrained(model_name)
model = LlamaForCausalLM.from_pretrained(model_name)

def get_welcome_message():
    return "*Congratulations!!, you have joined our membership program.*\n*Wait for surprises and interesting promotions!*"

 
@customer.route('/customer', methods=['GET'])
def dashboard():
    total_orders = db.session.query(db.func.count(Invoice.id)).scalar()
    total_omset = db.session.query(db.func.sum(Invoice.net_amount)).scalar()
    total_bayar = db.session.query(db.func.sum(Invoice.paid_amount)).scalar()
    total_piutang = db.session.query(db.func.sum(Invoice.net_amount-Invoice.paid_amount)).scalar()

    total_customers = db.session.query(db.func.count(Customer.id)).scalar()

   
    search_name = request.args.get('search_name', '')
    page = request.args.get('page', 1, type=int)
    per_page = 4
    all_customers = db.session.query(Customer).all()

    if search_name:
        if search_name.startswith('0'):
            search_name = search_name.replace('0', '', 1)
        search = f"%{search_name}%"
        all_customers = all_customers.filter(
            db.or_(
                Customer.name.ilike(search),
                Customer.phone.ilike(search),
                Customer.address_line1.ilike(search),
                Customer.address_line2.ilike(search),
                Customer.city.ilike(search),
                Customer.email.ilike(search)
            )
        )

    customer_data = []
    for customer in all_customers:
        customer_orders = db.session.query(db.func.count(Invoice.id)).filter_by(customer_id=customer.id).scalar()
        customer_omset = db.session.query(db.func.sum(Invoice.net_amount)).filter_by(customer_id=customer.id).scalar()
        customer_bayar = db.session.query(db.func.sum(Invoice.paid_amount)).filter_by(customer_id=customer.id).scalar()
        customer_piutang = db.session.query(db.func.sum(Invoice.net_amount-Invoice.paid_amount)).filter_by(customer_id=customer.id).scalar()
        customer_data.append({
            'customer': customer,
            'customer_orders': format_currency(customer_orders),
            'customer_omset': format_currency(customer_omset),
            'customer_bayar': format_currency(customer_bayar),
            'customer_piutang': format_currency(customer_piutang )           
        })

    total_customers = len(all_customers)
    total_pages = ceil(total_customers / per_page)

    customers = customer_data[(page - 1) * per_page: page * per_page]

    form = CustomerForm()  

    return render_template('customer/dashboard.html',
        total_orders=format_currency(total_orders),
        total_omset=format_currency(total_omset),
        total_piutang=format_currency(total_piutang),
        total_bayar=format_currency(total_bayar),
        customers=customers,
        search_name=search_name, 
        page=page, 
        total_pages=total_pages, 
        form=form)

@customer.route('/customer/share_customer_card/<int:customer_id>', methods=['POST'])
def share_customer_card(customer_id):
    try:
        customer = Customer.query.filter_by(id=customer_id).first()
         
        # Render the customer card HTML
        html_content = render_template('customer/customer_card.html', customer_data={'customer': customer, 'company': current_user.company})

        # Capture the card-container as an image (assuming a suitable HTML-to-image service or library is used)
        image = html_to_image(html_content)  # Implement this function as needed

        # Convert image to a format suitable for sending
        image_io = io.BytesIO()
        image.save(image_io, 'PNG')
        image_io.seek(0)
        image_base64 = base64.b64encode(image_io.read()).decode('utf-8')
        image_url = f'data:image/png;base64,{image_base64}'

        # Send the image via WhatsApp
        welcome_message = get_welcome_message()
        send_whatsapp_image(customer.phone_number, image_url, welcome_message, current_user.add_key_1)

        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@customer.route('/customer/add_customer', methods=['GET', 'POST'])
def add_customer():
    form = CustomerForm()
   
    if form.validate_on_submit():
        name = form.name.data.upper()
        phone = form.phone.data
        if phone:
            phone = format_phone_number(phone)
 
        existing_customer = None
       
        existing_customer = Customer.query.filter_by(
                phone=phone
            ).first()
        if existing_customer:
            return redirect(url_for('customer.view_customer',customer_id=existing_customer.id))  
           
            
        try:
            new_customer = Customer(
                name=name,
                address_line1=form.address_line1.data,
                address_line2=form.address_line2.data,
                city=form.city.data,
                zip=form.zip.data,
                phone=phone,
                email=form.email.data,
                company_name='',
                receivable_balance=form.receivable_balance.data,
                credit_limit=form.credit_limit.data,
                type=form.type.data,
                status=form.status.data
            )

            db.session.add(new_customer)
            db.session.commit()
            welcome_message = get_welcome_message()
            end_whatsapp_message(new_customer.phone, welcome_message, current_user.add_key_1)
            return redirect(url_for('customer.view_customer', customer_id=new_customer.id))
      
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while adding the customer: {str(e)}", "error")
            return redirect(url_for('customer.add_customer'))
     
    return render_template('customer/new_customer.html', form=form)



@customer.route('/customer/view_customer/<int:customer_id>', methods=['GET'])
def view_customer(customer_id):
    customer =[]
    customer_orders = 0
    customer_omset = 0
    customer_bayar = 0
    customer_piutang = 0
    customer =  Customer.query.filter_by(id=customer_id).first()
    if customer :
        customer_orders = db.session.query(db.func.count(Invoice.id)).filter_by(customer_id=customer.id).scalar()
        customer_omset = db.session.query(db.func.sum(Invoice.net_amount)).filter_by(customer_id=customer.id).scalar()
        customer_bayar = db.session.query(db.func.sum(Invoice.paid_amount)).filter_by(customer_id=customer.id).scalar()
        customer_piutang = db.session.query(db.func.sum(Invoice.net_amount-Invoice.paid_amount)).filter_by(customer_id=customer.id).scalar()
        
    
    customer_data = {
        'customer': customer,
        'customer_orders': format_currency(customer_orders),
        'customer_omset': format_currency(customer_omset),
        'customer_bayar': format_currency(customer_bayar),
        'customer_piutang': format_currency(customer_piutang ) 
    }
    
    return render_template('customer/view_customer.html', customer_data=customer_data)


@customer.route('/customer/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id):
    customer = Customer.query.filter_by(id=customer_id).first()
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        name = form.name.data.upper()
        phone = form.phone.data
        if phone:
            phone = format_phone_number(phone)
        if current_user.user_app_id:
            creditlimit=form.credit_limit.data
        else :
            creditlimit=0

        customer.name=name,
        customer.address_line1=form.address_line1.data,
        customer.address_line2=form.address_line2.data,
        customer.city=form.city.data,
        customer.zip=form.zip.data,
        customer.phone=phone,
        email=form.email.data,
        customer.credit_limit=creditlimit,
        customer.type=form.type.data
        customer.status=form.status.data
        valid_fields = ['name',  'phone',  'address_line1', 'address_line2',  'city',  'zip', 'email','credit_limit','type' ]
        updated_data = {field: getattr(customer, field) for field in valid_fields}
        
        db.session.commit()
        return redirect(url_for('customer.view_customer',customer_id=customer.id))
        
    return render_template('customer/edit_customer.html', form=form, customer=customer)


@customer.route('/customer/customer_card/<int:customer_id>', methods=['GET'])
def customer_card(customer_id):
   
    customer=[]
    customer =  Customer.query.filter_by(id=customer_id).first()
    
    member_data = {
        'member': customer
    }
    
    return render_template('customer/customer_card.html', member_data=member_data)


@customer.route('/crm/delete_customer/<int:customer_id>', methods=['GET'])
def delete_customer(customer_id):
    customer = Customer.query.filter_by(id=customer_id).first()
    if customer :
        db.session.delete(customer)
        db.session.commit()
    
    return redirect(url_for('customer.dashboard'))


@customer.route('/customer/report', methods=['GET', 'POST'])
def report():
   
    form = ReportFormCrm()

    reward_case = case(
        (Invoice.is_rewarded == True, 1),
        else_=0
    )

    query = db.session.query(
        Customer.name,
        Customer.phone,
        func.count(Invoice.id).label('order_count'),
        func.sum(reward_case).label('reward_count')
    ).join(Invoice, Invoice.customer_id == Customer.id).group_by(Customer.id)

    summary_query = db.session.query(
        func.date(Invoice.date).label('date'),
        func.count(Invoice.id).label('order_count'),
        func.sum(reward_case).label('reward_count')
    ).join(Customer, Invoice.customer_id == Customer.id).group_by(func.date(Invoice.date)).order_by(func.date(Invoice.date))

    if form.validate_on_submit():
        if form.date_from.data and form.date_until.data:
            query = query.filter(Invoice.date.between(form.date_from.data, form.date_until.data))
            summary_query = summary_query.filter(Invoice.date.between(form.date_from.data, form.date_until.data))
        if form.customer_name.data:
            query = query.filter(Customer.name.ilike(f"%{form.customer_name.data}%"))
        if form.order_count.data:
            query = query.having(func.count(Invoice.id) >= form.order_count.data)
        if form.reward_count.data:
            query = query.having(func.sum(reward_case) >= form.reward_count.data)
        if form.sort_by.data and form.sort_order.data:
            sort_column = form.sort_by.data
            sort_order = form.sort_order.data
            if sort_column == 'order_count':
                sort_column = func.count(Invoice.id)
            elif sort_column == 'reward_count':
                sort_column = func.sum(reward_case)
            else:
                sort_column = getattr(Customer, sort_column)
            if sort_order == 'desc':
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)

    results = query.all()
    summary_results = summary_query.all() if form.report_type.data == 'summary' else []
    return render_template('customer/report.html', form=form, results=results, summary_results=summary_results)
    
# Function to fetch customer and transaction details
def get_customer_data(customer_id):
    customer = Customer.query.get(customer_id)
    invoices = Invoice.query.filter_by(customer_id=customer_id).all()
    loyalty = CustomerLoyalty.query.filter_by(customer_id=customer_id).first()

    total_spent = sum(invoice.total_amount for invoice in invoices)
    total_loyalty_points = loyalty.total_points_earned if loyalty else 0

    customer_data = {
        "name": customer.name,
        "total_spent": total_spent,
        "total_loyalty_points": total_loyalty_points,
        "num_invoices": len(invoices),
    }
    return customer_data
    
#Pricing Strategy Based on AI Insights    
@customer.route('/customer/pricing-strategy/<int:customer_id>', methods=['GET'])
def pricing_strategy(customer_id):
    customer_data = get_customer_data(customer_id)
    
    customer_info = f"Customer {customer_data['name']} has spent {customer_data['total_spent']}."

    # Tokenize and generate insights for pricing strategy
    inputs = tokenizer(customer_info, return_tensors="pt")
    output = model.generate(inputs.input_ids, max_length=100)
    strategy = tokenizer.decode(output[0], skip_special_tokens=True)

    return jsonify({"pricing_strategy": strategy}), 200
    
    
#Implementing Recommendation and Segmentation    
@customer.route('/customer/recommendations/<int:customer_id>', methods=['GET'])
def generate_recommendations(customer_id):
    customer_data = get_customer_data(customer_id)
    
    # Create a recommendation prompt based on purchase history
    customer_history = f"Customer {customer_data['name']} spent {customer_data['total_spent']} across {customer_data['num_invoices']} purchases."

    # Tokenize and generate product recommendations
    inputs = tokenizer(customer_history, return_tensors="pt")
    output = model.generate(inputs.input_ids, max_length=100)
    insights = tokenizer.decode(output[0], skip_special_tokens=True)

    return jsonify({"recommendations": insights}), 200

 