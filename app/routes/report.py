import requests
from flask import Blueprint, render_template, redirect, url_for, request
from flask import flash, request, current_app , send_file, jsonify
from flask_paginate import Pagination, get_page_parameter
from flask_mail import Message
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, cast, Integer,and_ , func,  case, and_ ,  extract, func , select

from sqlalchemy.exc import IntegrityError,DataError
from sqlalchemy.orm import joinedload , aliased
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from math import ceil
from weasyprint import HTML
import pdfkit
import imgkit
from PyPDF2 import PdfMerger
import qrcode
from io import BytesIO
import os
from PIL import Image
import base64
import logging
import tempfile
import time
from config import Config
from xendit import Configuration, ApiClient, XenditSdkException
from xendit.apis import InvoiceApi, PaymentMethodApi, PaymentRequestApi

from werkzeug.exceptions import abort
from decimal import Decimal
from config import Config
from app import db, mail
from app.models.user import User, SubscriptionOrder, SubscriptionPlan, Module, Task, Role, Permission, Company, Branch
from app.models.invoice import Invoice, PriorityList,PaymentTerms 
from app.models.invoice_detail import InvoiceDetail
from app.models.customer import Customer
from app.models.task import TaskInvoice, TaskFlowInvoice
from app.models.product import Product, UnitList , ProductImage , ProductField
from app.models.payment import Payment
from app.models.sales_parameter import SalesParameter

from app.forms.report import ReportForm

from app.utilities.utils import generate_security_code, calculate_invoice_totals
from app.utilities.utils import format_phone_number, send_whatsapp_message, send_whatsapp_image, send_whatsapp_pdf
from app.utilities.utils import generate_qr_code, format_currency,tax_rate,generate_qr_code_payment
from app.utilities.utils import generate_payment_id, calculate_check_digit , validate_invoice_id, validate_payment_id
from decimal import Decimal
from num2words import num2words

import matplotlib.pyplot as plt
import io
import plotly.graph_objs as go
import pandas as pd
from openai import OpenAI
from groq import Groq
import transformers
import torch
from transformers import AutoTokenizer


report = Blueprint('report', __name__)

MODEL_NAME = Config.AIML_MODEL_NAME
ENDPOINT = Config.AIML_ENDPOINT
API_KEY = Config.AIML_API_KEY

client = OpenAI(
    api_key=API_KEY,
    base_url=ENDPOINT,
)

def get_company_branch_filter():
    if current_user.company.has_branches:
        return current_user.company_id, current_user.branch_id
    else:
        return current_user.company_id, None

def get_payment_company_branch_filter():
    if current_user.company.has_branches:
        return current_user.company_id, current_user.branch_id
    else:
        return current_user.company_id, None

def query_summed_data(criteria, date_from, date_until):
    company_filter, branch_filter = get_company_branch_filter()
    payment_company_filter, payment_branch_filter = get_payment_company_branch_filter()

    # Group by the appropriate time period based on the criteria
    time_grouping = get_time_group(criteria)
    payment_time_grouping = get_payment_time_group(criteria)

    # Query for invoices to calculate sum_amount and sum_balance
    invoice_data = db.session.query(
        func.sum(Invoice.net_amount).label('sum_amount'),
        func.sum(Invoice.net_amount - Invoice.paid_amount).label('sum_balance'),
        *time_grouping
    ).filter(
        Invoice.created_date >= date_from,
        Invoice.created_date <= date_until,
        Invoice.company_id == company_filter
    )
    
    if branch_filter:
        invoice_data = invoice_data.filter(Invoice.branch_id == branch_filter)

    invoice_data = invoice_data.group_by(*time_grouping).all()

    # Query for payments to calculate sum_paid
    payment_data = db.session.query(
        func.sum(Payment.amount).label('sum_paid'),
        *payment_time_grouping
    ).filter(
        Payment.created_date >= date_from,
        Payment.created_date <= date_until,
        Payment.company_id == payment_company_filter
    )
    
    if payment_branch_filter:
        payment_data = payment_data.filter(Payment.branch_id == payment_branch_filter)

    payment_data = payment_data.group_by(*payment_time_grouping).all()

    return invoice_data, payment_data

def get_time_group(criteria):
    if criteria == "monthly":
        return extract('year', Invoice.created_date), extract('month', Invoice.created_date)
    elif criteria == "weekly":
        return extract('year', Invoice.created_date), extract('week', Invoice.created_date)
    elif criteria == "daily":
        return extract('year', Invoice.created_date), extract('month', Invoice.created_date), extract('day', Invoice.created_date)
    return None

def get_payment_time_group(criteria):
    if criteria == "monthly":
        return extract('year', Payment.created_date), extract('month', Payment.created_date)
    elif criteria == "weekly":
        return extract('year', Payment.created_date), extract('week', Payment.created_date)
    elif criteria == "daily":
        return extract('year', Payment.created_date), extract('month', Payment.created_date), extract('day', Payment.created_date)
    return None
 
def query_aging_data():
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None

    company = db.session.query(Company).filter(Company.id == company_id).first()
    branch = db.session.query(Branch).filter(
                Branch.company_id == company_id,
                Branch.id == branch_id).first() if branch_id else None
    if branch :
        invoices = Invoice.query.filter(
            Invoice.company_id == company_id,
            Invoice.branch_id == branch_id,
            Invoice.net_amount > Invoice.paid_amount   
        ).all()
    else :
        invoices = Invoice.query.filter(
            Invoice.company_id == company_id,
            Invoice.net_amount > Invoice.paid_amount   
        ).all()
        
    return invoices

def query_aging_customer():
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None

    company = db.session.query(Company).filter(Company.id == company_id).first()
    branch = db.session.query(Branch).filter(
                Branch.company_id == company_id,
                Branch.id == branch_id).first() if branch_id else None
    if branch :   
    
        results = db.session.query(
                        Customer.name,
                        Customer.phone,
                        func.count(Invoice.id).label('open_invoice'),
                        func.sum(Invoice.net_amount - Invoice.paid_amount).label('ar_balance'),
                        func.min(Invoice.created_date).label('invoice_first'),
                        func.max(Invoice.created_date).label('invoice_last')
                    ).join(Invoice, Customer.id == Invoice.customer_id) \
                     .filter(Invoice.net_amount > Invoice.paid_amount,  Invoice.company_id == company_id,
            Invoice.branch_id == branch_id) \
                     .group_by(Customer.name,Customer.phone) \
                     .all()
    else :
        results = db.session.query(
                        Customer.name,
                        Customer.phone,
                        func.count(Invoice.id).label('open_invoice'),
                        func.sum(Invoice.net_amount - Invoice.paid_amount).label('ar_balance'),
                        func.min(Invoice.created_date).label('invoice_first'),
                        func.max(Invoice.created_date).label('invoice_last')
                    ).join(Invoice, Customer.id == Invoice.customer_id) \
                     .filter(Invoice.net_amount > Invoice.paid_amount,  Invoice.company_id == company_id) \
                     .group_by(Customer.name,Customer.phone) \
                     .all()
        return results
def prepare_aging_data(invoices):
    if not invoices:
        return {'1-30 hari': (0, 0), '31-60 hari': (0, 0), '61-90 hari': (0, 0), '91+ hari': (0, 0)}

    aging_data = {'1-30 hari': [0, 0], '31-60 hari': [0, 0], '61-90 hari': [0, 0], '91+ hari': [0, 0]}  # [count, sum_amount]

    for invoice in invoices:
        if invoice.created_date:
            days_overdue = (datetime.now() - invoice.created_date).days
            if days_overdue <= 30:
                aging_data['1-30 hari'][0] += 1
                aging_data['1-30 hari'][1] += ( invoice.net_amount - invoice.paid_amount)
            elif days_overdue <= 60:
                aging_data['31-60 hari'][0] += 1
                aging_data['31-60 hari'][1] += ( invoice.net_amount - invoice.paid_amount)
            elif days_overdue <= 90:
                aging_data['61-90 hari'][0] += 1
                aging_data['61-90 hari'][1] += ( invoice.net_amount - invoice.paid_amount)
            else:
                aging_data['91+ hari'][0] += 1
                aging_data['91+ hari'][1] += ( invoice.net_amount - invoice.paid_amount)

    return aging_data

def create_bar_chart(title, labels, values):
    return {
        'labels': labels,
        'datasets': [{
            'label': title,
            'data': values,
            'backgroundColor': ['rgba(75, 192, 192, 0.6)', 'rgba(153, 102, 255, 0.6)', 'rgba(255, 159, 64, 0.6)', 'rgba(255, 99, 132, 0.6)'],
            'borderColor': ['rgba(75, 192, 192, 1)', 'rgba(153, 102, 255, 1)', 'rgba(255, 159, 64, 1)', 'rgba(255, 99, 132, 1)'],
            'borderWidth': 2,
            'borderRadius': 5
        }]
    }


@report.route('/report/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None
    if not company_id :
        return render_template('dashboard/error_message.html', success= False, title='Access Denied', message = 'Company has not been created.', message_id ='Identitas usaha belum di buat.')
    if company_id ==0 :
        return render_template('dashboard/error_message.html', success= False, title='Access Denied', message = 'Company has not been created.', message_id ='Identitas usaha belum di buat.')

    company = db.session.query(Company).filter(Company.id == company_id).first()
    if not company :
        return render_template('dashboard/error_message.html', success= False, title='Access Denied', message = 'Company has not been created.', message_id ='Identitas usaha belum di buat.')
  
    
    branch = db.session.query(Branch).filter(
                Branch.company_id == company_id,
                Branch.id == branch_id).first() if branch_id else None

    total_customers = Customer.query.filter(
        Customer.status == 'active',
        Customer.company_id == company_id,
        (Customer.branch_id == branch_id) if branch_id else True
    ).count()

    avg_receivable_balance = db.session.query(
        func.avg(Invoice.net_amount - Invoice.paid_amount)
    ).filter(
        Invoice.company_id == company_id,
        (Invoice.branch_id == branch_id) if branch_id else True
    ).scalar()

    total_receivable_balance = db.session.query(
        func.sum(Invoice.net_amount - Invoice.paid_amount)
    ).filter(
        Invoice.company_id == company_id,
        (Invoice.branch_id == branch_id) if branch_id else True
    ).scalar()

    total_invoices = Invoice.query.filter(
        Invoice.company_id == company_id,
        (Invoice.branch_id == branch_id) if branch_id else True
    ).count()

    avg_invoice_amount = db.session.query(
        func.avg(Invoice.total_amount)
    ).filter(
        Invoice.company_id == company_id,
        (Invoice.branch_id == branch_id) if branch_id else True
    ).scalar()

    total_revenue = db.session.query(
        func.sum(Invoice.paid_amount)
    ).filter(
        Invoice.company_id == company_id,
        (Invoice.branch_id == branch_id) if branch_id else True
    ).scalar()

    labels = []
    total_values = []
    paid_values = []
    table_data = []

    form = ReportForm()

    if form.validate_on_submit():
        criteria = form.criteria.data
        date_from = form.date_from.data
        date_until = form.date_until.data
        report_type = form.reporttype.data
        if report_type =='omset' :
            invoice_data, payment_data = query_summed_data(criteria, date_from, date_until)

            invoice_grouped_data = []
            for row in invoice_data:

                invoice_grouped_data.append({
                    "time_period":f"{row[2]}-{row[3]}" if criteria != "daily" else f"{row[2]}-{row[3]}-{row[4]}",
                    "sum_amount": row.sum_amount,
                    "sum_balance": row.sum_balance
                })

            payment_grouped_data = []
            for row in payment_data:
        
                payment_grouped_data.append({
                    "time_period": f"{row[1]}-{row[2]}" if criteria != "daily" else f"{row[1]}-{row[2]}-{row[3]}",
                    "sum_paid": row.sum_paid
                })


            labels = [d['time_period'] for d in invoice_grouped_data]
            total_values = [d['sum_amount'] or 0 for d in invoice_grouped_data]
            paid_values = [d['sum_paid'] or 0 for d in payment_grouped_data]

            table_data = []
            for i, label in enumerate(labels):
                table_data.append({
                    "time_period": label,
                    "total_amount": total_values[i] if i < len(total_values) else 0,
                    "paid_amount": paid_values[i] if i < len(paid_values) else 0
                })

            return render_template('report/dashboard_graph.html', form=form,
                                       total_customers=total_customers,
                                       avg_receivable_balance=avg_receivable_balance,
                                       total_receivable_balance=total_receivable_balance,
                                       total_invoices=total_invoices,
                                       avg_invoice_amount=avg_invoice_amount,
                                       total_revenue=total_revenue,
                                       labels=labels,
                                       total_values=total_values,
                                       paid_values=paid_values,
                                       table_data=table_data,
                                       report_type=report_type)
        
        elif report_type =='aging' :

            invoices = query_aging_data()

            aging_data = prepare_aging_data(invoices)

            aging_labels = list(aging_data.keys())
            aging_invoice_count = [data[0] for data in aging_data.values()]
            aging_invoice_sum = [data[1] for data in aging_data.values()]

            aging_table_data = [(label, data[0], data[1]) for label, data in aging_data.items()]
            print_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return render_template(
                'report/aging_schedule.html',
                aging_labels=aging_labels,
                aging_invoice_count=aging_invoice_count,
                aging_invoice_sum=aging_invoice_sum,
                aging_table_data=aging_table_data ,
                print_date=print_date
            )
        elif report_type =='piutang' :

            ar_data = query_aging_customer ()

            print_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return render_template('report/ar_customers.html', ar_data=ar_data, print_date=print_date)
        elif report_type=='kpi' :
            revenue_growth_rate = calculate_revenue_growth_rate()
            customer_retention_rate = calculate_customer_retention_rate()
            cltv = calculate_cltv()   
            atv = calculate_atv()
            churn_rate= calculate_churn_rate()
            cash_flow=calculate_cash_flow()

            recommendation = generate_kpi_recommendations(revenue_growth_rate, customer_retention_rate, cltv, atv,churn_rate,cash_flow)
            recommendation = recommendation.replace("`", "").replace("html", "")
            return render_template('report/kpi_dashboard.html',
                                   revenue_growth_rate=revenue_growth_rate,
                                   customer_retention_rate=customer_retention_rate,
                                   cltv=cltv,
                                   atv=atv,
                                   churn_rate=churn_rate,
                                   cash_flow=cash_flow,
                                   recommendation=recommendation)
                                  
    return render_template('report/dashboard.html', form=form,
                           total_customers=total_customers,
                           avg_receivable_balance=avg_receivable_balance,
                           total_receivable_balance=total_receivable_balance,
                           total_invoices=total_invoices,
                           avg_invoice_amount=avg_invoice_amount,
                           total_revenue=total_revenue)
                           
@report.route('/report/product-sales')
def product_sales():
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None

    company = db.session.query(Company).filter(Company.id == company_id).first()
    branch = db.session.query(Branch).filter(
                Branch.company_id == company_id,
                Branch.id == branch_id).first() if branch_id else None
    if branch :            
        top_selling_products = db.session.query(Product.name, func.sum(InvoiceDetail.quantity)).filter(
            InvoiceDetail.company_id==company_id,
            InvoiceDetail.branch_id== branch_id).group_by(Product.name).order_by(func.sum(InvoiceDetail.quantity).desc()).limit(10).all()
    else :
        top_selling_products = db.session.query(Product.name, func.sum(InvoiceDetail.quantity)).filter(
            InvoiceDetail.company_id==company_id).group_by(Product.name).order_by(func.sum(InvoiceDetail.quantity).desc()).limit(10).all()
    
    sales_chart = create_bar_chart('Top-Selling Products', [p[0] for p in top_selling_products], [p[1] for p in top_selling_products])

    return render_template('report/product_sales.html', sales_chart=sales_chart)


def get_month_date_range(months_back=0):
    today = datetime.today()
    first_day_of_this_month = today.replace(day=1)
    first_day_of_target_month = first_day_of_this_month - timedelta(days=months_back * 30)
    last_day_of_target_month = (first_day_of_target_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    return first_day_of_target_month, last_day_of_target_month

def calculate_revenue_growth_rate():
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None

    start_of_last_month, end_of_last_month = get_month_date_range(months_back=1)
    start_of_this_month, end_of_this_month = get_month_date_range(months_back=0)

    if branch_id:
        last_month_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter(
            Invoice.created_date.between(start_of_last_month, end_of_last_month),
            Invoice.company_id == company_id,
            Invoice.branch_id == branch_id
        ).scalar()

        current_month_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter(
            Invoice.created_date.between(start_of_this_month, end_of_this_month),
            Invoice.company_id == company_id,
            Invoice.branch_id == branch_id
        ).scalar()
    else:
    
        last_month_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter(
            Invoice.created_date.between(start_of_last_month, end_of_last_month),
            Invoice.company_id == company_id
        ).scalar()

        current_month_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter(
            Invoice.created_date.between(start_of_this_month, end_of_this_month),
            Invoice.company_id == company_id
        ).scalar()

    if current_month_revenue is None or last_month_revenue is None :
        return 0
    if last_month_revenue == 0 or current_month_revenue == 0  :
        return 0
    revenue_growth_rate = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
    return revenue_growth_rate

def calculate_customer_retention_rate():
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None

    # Define date ranges (e.g., last month)
    start_of_last_month, end_of_last_month = get_month_date_range(months_back=1)
    start_of_this_month, end_of_this_month = get_month_date_range(months_back=0)

    # Customers last month
    customers_last_month = db.session.query(Invoice.customer_id).filter(
        Invoice.created_date.between(start_of_last_month, end_of_last_month),
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True
    ).distinct().count()

    # Customers retained in the current month
    customers_retained_this_month = db.session.query(Invoice.customer_id).filter(
        Invoice.created_date.between(start_of_this_month, end_of_this_month),
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True,
        Invoice.customer_id.in_(
            db.session.query(Invoice.customer_id).filter(
                Invoice.created_date.between(start_of_last_month, end_of_last_month),
                Invoice.company_id == company_id,
                Invoice.branch_id == branch_id if branch_id else True
            )
        )
    ).distinct().count()

    if customers_last_month == 0:
        return 0
    customer_retention_rate = (customers_retained_this_month / customers_last_month) * 100
    return customer_retention_rate

# Average Transaction Value (ATV) calculation
def calculate_atv():
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None

    # Get the total sales revenue over a period (e.g., month)
    total_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter(
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True
    ).scalar()

    # Get the total number of transactions (invoices)
    total_transactions = db.session.query(func.count(Invoice.id)).filter(
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True
    ).scalar()

    # Ensure that total transactions are not zero to avoid division by zero
    if total_transactions == 0 or total_transactions is None:
        return 0

    # Average Transaction Value (ATV)
    atv = total_revenue / total_transactions
    return atv

def calculate_churn_rate():
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None

    # Calculate the start of the current period (e.g., the start of the month)
    today = datetime.today().date()
    start_of_period = today.replace(day=1) - timedelta(days=1)

    # Subquery to get the last purchase date for each customer
    subquery = (
        db.session.query(
            Invoice.customer_id,
            func.max(Invoice.created_date).label('last_purchase_date')
        )
        .filter(
            Invoice.company_id == company_id,
            Invoice.branch_id == branch_id if branch_id else True
        )
        .group_by(Invoice.customer_id)
        .subquery()
    )

    # Query to get the total number of customers and the number of lost customers
    result = db.session.query(
        func.count(Customer.id),  # Total customers
        func.count(
            func.nullif(subquery.c.last_purchase_date > start_of_period, False)
        )  # Lost customers
    ).outerjoin(subquery, Customer.id == subquery.c.customer_id).filter(
        Customer.company_id == company_id,
        Customer.branch_id == branch_id if branch_id else True
    ).first()

    total_customers, retained_customers = result

    if total_customers == 0:
        return 0

    lost_customers = total_customers - retained_customers
    churn_rate = (lost_customers / total_customers) * 100
    return churn_rate


def calculate_cltv():
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None

    # Get total revenue and total number of purchases
    total_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter(
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True
    ).scalar()

    total_purchases = db.session.query(func.count(Invoice.id)).filter(
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True
    ).scalar()


    unique_customers = db.session.query(func.count(func.distinct(Invoice.customer_id))).filter(
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True
    ).scalar()


    if total_purchases == 0:
        return 0
    avg_purchase_value = total_revenue / total_purchases


    if unique_customers == 0:
        return 0
    avg_purchase_frequency = total_purchases / unique_customers

    customer_lifespan = 2  


    cltv = avg_purchase_value * avg_purchase_frequency * customer_lifespan
    return cltv

def calculate_cash_flow():
    start_date = None
    end_date = None
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None
    today = datetime.today().date()

    start_of_period = start_date if start_date else today.replace(day=1)
    end_of_period = end_date if end_date else today

    if isinstance(start_of_period, datetime):
        start_of_period = start_of_period.date()
    if isinstance(end_of_period, datetime):
        end_of_period = end_of_period.date()

    total_cash_payments_query = db.session.query(
        func.sum(Payment.amount).label('total_cash_payments')
    ).filter(
        Payment.payment_method == 'cash',
        Payment.company_id == company_id,
        Payment.branch_id == branch_id if branch_id else True,
        Payment.payment_date >= start_of_period,   
        Payment.payment_date <= end_of_period     
    )

    total_discount_query = db.session.query(
        func.sum(Invoice.total_discount).label('total_discount')
    ).filter(
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True,
        Invoice.created_date >= start_of_period,   
        Invoice.created_date <= end_of_period      
    )
    

    total_refunds_query = db.session.query(
        func.sum(Invoice.total_amount).label('total_refunds')
    ).join(Invoice.tasks).filter(
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True,
        (TaskInvoice.status.ilike('%refund%') | TaskInvoice.status.ilike('%retur%')),
        TaskInvoice.created_date >= start_of_period,      
        TaskInvoice.created_date <= end_of_period        
    )


    total_cash_payments = total_cash_payments_query.scalar() or 0
    total_discounts = total_discount_query.scalar() or 0
    total_refunds = total_refunds_query.scalar() or 0

    net_cash_flow = total_cash_payments - total_discounts - total_refunds
  
    return net_cash_flow


    
@report.route('/report/download-report', methods=['GET'])
def download_report():
    rendered_html = render_template('dashboard.html')   
    pdf = pdfkit.from_string(rendered_html, False)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=business_report.pdf'
    return response
    
@report.route('/report/financial-overview', methods=['POST'])
def financial_overview():
    if request.method == 'POST':
        criteria = request.form.get('criteria')   
        report_type = request.form.get('report_type')   

        # Query data based on selected criteria
        invoices = Invoice.query.all()
        payments = Payment.query.all()

        # Calculate financial metrics
        total_invoices = len(invoices)
        avg_invoice_amount = sum([invoice.total_amount for invoice in invoices]) / total_invoices
        total_revenue = sum([invoice.paid_amount for invoice in invoices if invoice.status == 'paid'])
        pending_invoices = [invoice for invoice in invoices if invoice.status == 'pending']

        # Payment Method Distribution
        payment_methods = db.session.query(Payment.payment_method, db.func.count(Payment.id)).group_by(Payment.payment_method).all()

        # Prepare data for charting
        chart_data = prepare_chart_data(invoices)

        # Return JSON data for interactive charting with jQuery/JS
        if report_type == 'graph':
            return jsonify(chart_data)

        # Render the financial report template
        return render_template('report/financial_overview.html', invoices=invoices, total_invoices=total_invoices,
                               avg_invoice_amount=avg_invoice_amount, total_revenue=total_revenue, pending_invoices=pending_invoices,
                               payment_methods=payment_methods, report_type=report_type)


    return render_template('report/financial_overview.html')

@report.route('/report/generate-pdf', methods=['POST'])
def generate_pdf():
    # Generate financial report and convert it to PDF
    invoices = Invoice.query.all()
    rendered = render_template('pdf_template.html', invoices=invoices)
    pdf = pdfkit.from_string(rendered, False)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=financial_report.pdf'
    return response
    
def prepare_chart_data(invoices):
    invoice_data = {'1-30 days': 0, '31-60 days': 0, '61-90 days': 0, '91+ days': 0}
    for invoice in invoices:
        days_overdue = (datetime.now() - invoice.due_date).days
        if 1 <= days_overdue <= 30:
            invoice_data['1-30 days'] += 1
        elif 31 <= days_overdue <= 60:
            invoice_data['31-60 days'] += 1
        elif 61 <= days_overdue <= 90:
            invoice_data['61-90 days'] += 1
        else:
            invoice_data['91+ days'] += 1

    return invoice_data
    
def generate_graph():
    plt.figure(figsize=(6, 4))
    # Example: Invoice aging graph
    plt.bar(['1-30', '31-60', '61-90', '90+'], [10, 20, 5, 1], color='blue')
    plt.title('Invoice Aging')
    plt.xlabel('Days Overdue')
    plt.ylabel('Count')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return img

def generate_kpi_recommendations_v1(revenue_growth, retention_rate, cltv, atv, churn_rate, cash_flow):
    #try:

    prompt = f"""
    I have the following KPIs related to sales and customer payments:

    Revenue Growth Rate: {revenue_growth}%
    Customer Retention Rate: {retention_rate}%
    Customer Lifetime Value (CLTV): Rp. {cltv:,}
    Average Transaction Value (ATV): Rp. {atv:,}
    Churn Rate: {churn_rate}%
    Cash Flow from Customer Payments: Rp. {cash_flow:,}

    Based on these KPIs, Generate detailed recommendations for improving business performance in Indonesian. Each KPI should be represented as a visually appealing HTML card with the following structure:

    Title: Display the KPI name.
    Percentage/Value: Present the KPI value in large, bold font.
    Description: Provide a brief analysis of the KPI.
    Action Steps: Suggest actionable strategies to enhance performance for each KPI.

    Design Specifications:
    The cards should be structured using CSS for a professional, modern layout.
    Use icons for each KPI (e.g., graph for growth rate, person for customer retention, etc.).
    Apply subtitle background colors for each card, with hover effects to enhance interactivity.
    Ensure that the key metrics and recommendations stand out for easy readability and engagement.

    Return only the code in your reply and the following HTML template structure :.
    <div class="col-md-12 mb-4">
        <div class="card shadow-lg bg-gradient-success text-white">
            <div class="card-body d-flex align-items-center">
                <i class="fa-solid icon display-3 me-4"></i>
                <div>
                    <h4 class="fw-bold">Title: Display the KPI name.</h4>
                    <h1 class="display-3">{{ Percentage/Value  | currency }}</h1>
                    <p>Description.</p>
                    <p>Action Step</p>
                </div>
            </div>
        </div>
    </div>

    """
   

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        
    )
    
    recommendation = completion.choices[0].message.content
    return recommendation
    
    #except Exception as e:
    #    return f"Layanan analisis dan rekomendasi belum diaktifkan."
    
def generate_kpi_recommendations(revenue_growth, retention_rate, cltv, atv, churn_rate, cash_flow):
    
    system_prompt = """
    You are an expert at generating recommendations based on sales and customer KPIs.
    You will generate detailed business recommendations for each KPI.
    You are given the following KPIs:

    Revenue Growth Rate: {revenue_growth}%
    Customer Retention Rate: {retention_rate}%
    Customer Lifetime Value (CLTV): Rp. {cltv:,}
    Average Transaction Value (ATV): Rp. {atv:,}
    Churn Rate: {churn_rate}%
    Cash Flow from Customer Payments: Rp. {cash_flow:,}

    Based on these KPIs, generate HTML cards for each KPI with recommendations. Each card must include:
    - Title: The KPI name.
    - Value: The KPI percentage or value, highlighted.
    - Description: A brief analysis of the KPI.
    - Action Steps: Actionable strategies for improving performance.
    - Design: Use CSS to create a visually appealing, modern layout.

    Return only the code for each card in a format that follows this structure:
    <div class="col-md-12 mb-4">
        <div class="card shadow-lg bg-gradient-success text-white">
            <div class="card-body d-flex align-items-center">
                <i class="fa-solid icon display-3 me-4"></i>
                <div>
                    <h4 class="fw-bold">Title: Display the KPI name.</h4>
                    <h1 class="display-3">{{ Percentage/Value  | currency }}</h1>
                    <p>Description: Brief analysis of the KPI.</p>
                    <p>Action Step: Suggest actionable strategies to enhance performance for each KPI.</p>
                </div>
            </div>
        </div>
    </div>
    """

    
    system_prompt = system_prompt.format(
        revenue_growth=revenue_growth,
        retention_rate=retention_rate,
        cltv=cltv,
        atv=atv,
        churn_rate=churn_rate,
        cash_flow=cash_flow
    )

   
    function_definitions = """[
        {
            "name": "generate_recommendation",
            "description": "Generate KPI cards and recommendations.",
            "parameters": {
                "type": "dict",
                "required": [
                    "revenue_growth", "retention_rate", "cltv", "atv", "churn_rate", "cash_flow"
                ],
                "properties": {
                    "revenue_growth": {"type": "number", "description": "Revenue growth percentage"},
                    "retention_rate": {"type": "number", "description": "Customer retention rate percentage"},
                    "cltv": {"type": "number", "description": "Customer lifetime value in currency"},
                    "atv": {"type": "number", "description": "Average transaction value in currency"},
                    "churn_rate": {"type": "number", "description": "Churn rate percentage"},
                    "cash_flow": {"type": "number", "description": "Cash flow from customer payments in currency"}
                }
            }
        }
    ]
    """

    
    completion = client.chat.completions.create(
        model="Llama-3.2-1B",  # Using the Llama 3.2 Lightweight model variant (1B/3B)
        messages=[{
            "role": "system",
            "content": system_prompt,
        }],
        function_definitions=function_definitions
    )
    
    recommendation = completion.choices[0].message.content
    return recommendation



