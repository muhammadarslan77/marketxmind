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

from werkzeug.exceptions import abort
from decimal import Decimal
from config import Config
from app import db, mail
from app.models.user import User, SubscriptionOrder, SubscriptionPlan, Module, Task, Role, Permission, Company, Branch
from app.models.invoice import Invoice, PriorityList,PaymentTerms 
from app.models.invoice_detail import InvoiceDetail
from app.models.customer import Customer
from app.models.task import TaskInvoice, TaskFlowInvoice
from app.models.crm import MemberCrm, TransactionCrm, PromotionCrm 
from app.models.product import Product, UnitList , ProductImage , ProductField
from app.models.payment import Payment
from app.models.sales_parameter import SalesParameter

from decimal import Decimal
from num2words import num2words

import matplotlib.pyplot as plt
import io
import plotly.graph_objs as go
import pandas as pd
from openai import OpenAI

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

    total_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter(
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True
    ).scalar()

    total_transactions = db.session.query(func.count(Invoice.id)).filter(
        Invoice.company_id == company_id,
        Invoice.branch_id == branch_id if branch_id else True
    ).scalar()

    if total_transactions == 0 or total_transactions is None:
        return 0

    atv = total_revenue / total_transactions
    return atv

def calculate_churn_rate():
    company_id = current_user.company_id
    branch_id = current_user.branch_id if current_user.branch_id else None

    today = datetime.today().date()
    start_of_period = today.replace(day=1) - timedelta(days=1)

  
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


    result = db.session.query(
        func.count(Customer.id),   
        func.count(
            func.nullif(subquery.c.last_purchase_date > start_of_period, False)
        )   s
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



def generate_kpi_recommendations(revenue_growth, retention_rate, cltv, atv, churn_rate, cash_flow):
    # Konfigurasi Azure OpenAI
    '''
    API_VERSION = Config.AZZUREOPENAI_API_VERSION
    MODEL_NAME = Config.AZZUREOPENAI_MODEL_NAME
    ENDPOINT = Config.AZZUREOPENAI_ENDPOINT
    API_KEY = Config.AZZUREOPENAI_API_KEY
    '''
    try:
        '''
        client = AzureOpenAI(
            azure_endpoint=ENDPOINT,
            api_version=API_VERSION,
            api_key=API_KEY
        )
        '''
       
        prompt = f"""
        I have the following KPIs related to sales and customer payments:

        Revenue Growth Rate: {revenue_growth}%
        Customer Retention Rate: {retention_rate}%
        Customer Lifetime Value (CLTV): Rp. {cltv:,}
        Average Transaction Value (ATV): Rp. {atv:,}
        Churn Rate: {churn_rate}%
        Cash Flow from Customer Payments: Rp. {cash_flow:,}

        Based on these KPIs, I would like you to generate detailed recommendations for improving business performance in Indonesian. Each KPI should be represented as a visually appealing HTML card with the following structure:

        Title: Display the KPI name (e.g., 'Revenue Growth Rate').
        Percentage/Value: Present the KPI value in large, bold font.
        Description: Provide a brief analysis of the KPI.
        Action Steps: Suggest actionable strategies to enhance performance for each KPI.

        Design Specifications:
        The cards should be structured using CSS for a professional, modern layout.
        Use icons for each KPI (e.g., graph for growth rate, person for customer retention, etc.).
        Apply subtle background colors for each card, with hover effects to enhance interactivity.
        Ensure that the key metrics and recommendations stand out for easy readability and engagement.

        Please integrate the output within the following HTML template structure and Generate without any explanation or additional text.
       <!-- Revenue Growth Rate (revenue_growth_rate)-->
        <div class="col-md-12 mb-4">
            <div class="card shadow-lg bg-gradient-success text-white">
                <div class="card-body d-flex align-items-center">
                    <i class="fa-solid fa-chart-area display-3 me-4"></i>
                    <div>
                        <h4 class="fw-bold">Tingkat Pertumbuhan Pendapatan</h4>
                        <h1 class="display-3">{{ revenue_growth_rate  | currency }}%</h1>
                        <p>Description: Provide a brief analysis of the Revenue Growth Rate.</p>
						<p>Action Steps: Suggest actionable strategies to enhance performance for Revenue Growth Rate.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Customer Retention Rate (CRR)-->
        <div class="col-md-12 mb-4">
            <div class="card shadow-lg bg-gradient-info text-white">
                <div class="card-body d-flex align-items-center">
                    <i class="fa-solid fa-user-check display-3 me-4"></i>
                    <div>
                        <h4 class="fw-bold">Tingkat Retensi Pelanggan (CRR)</h4>
                        <h1 class="display-3">{{ customer_retention_rate  | currency }}%</h1>
                        <p>Description: Provide a brief analysis of the CRRI.</p>
						<p>Action Steps: Suggest actionable strategies to enhance performance for CRR.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Customer Lifetime Value (CLTV) -->
        <div class="col-md-12 mb-4">
            <div class="card shadow-lg bg-gradient-warning text-white">
                <div class="card-body d-flex align-items-center">
                    <i class="fa-solid fa-wallet display-3 me-4"></i>
                    <div>
                        <h4 class="fw-bold">Nilai Umur Pelanggan (CLTV)</h4>
                        <h1 class="display-3">Rp. {{ cltv  | currency }}</h1>
                        <p>Description: Provide a brief analysis of the CLTV.</p>
						<p>Action Steps: Suggest actionable strategies to enhance performance for CLTV.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Average Transaction Value (ATV) -->
        <div class="col-md-12 mb-4">
            <div class="card shadow-lg bg-gradient-primary text-white">
                <div class="card-body d-flex align-items-center">
                    <i class="fa-solid fa-money-bill-wave display-3 me-4"></i>
                    <div>
                        <h4 class="fw-bold">Nilai Transaksi Rata-Rata (ATV)</h4>
                        <h1 class="display-3">Rp. {{ atv  | currency  }}</h1>
                        <p>Description: Provide a brief analysis of the ATV.</p>
						<p>Action Steps: Suggest actionable strategies to enhance performance for ATV.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Churn Rate -->
        <div class="col-md-12 mb-4">
            <div class="card shadow-lg bg-gradient-danger text-white">
                <div class="card-body d-flex align-items-center">
                    <i class="fa-solid fa-user-slash display-3 me-4"></i>
                    <div>
                        <h4 class="fw-bold">Tingkat Pengunduran Diri (Churn Rate)</h4>
                        <h1 class="display-3">{{ churn_rate  | currency }}%</h1>
                        <p>Description: Provide a brief analysis of the churn_rate.</p>
						<p>Action Steps: Suggest actionable strategies to enhance performance for churn_rate.</p>
                    </div>
                </div>
            </div>
        </div>
		<!-- cash_flow -->
        <div class="col-md-12 mb-4">
            <div class="card shadow-lg bg-gradient-danger text-white">
                <div class="card-body d-flex align-items-center">
                    <i class="fa-solid fa-comments-dollar display-3 me-4"></i>
                    <div>
                        <h4 class="fw-bold">Cash Flow Dari Pembayaran Pelanggan</h4>
                        <h1 class="display-3">Rp. {{ cash_flow  | currency }}</h1>
                        <p>Description: Provide a brief analysis of the KPI.</p>
						<p>Action Steps: Suggest actionable strategies to enhance performance for each KPI.</p>
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
            max_tokens=5000,
        )
        
        recommendation = completion.choices[0].message.content
        return recommendation

    except Exception as e:
        return f"Layanan analisis dan rekomendasi belum diaktifkan."

