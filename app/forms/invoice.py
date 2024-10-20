from flask_wtf import FlaskForm
from wtforms import HiddenField, DecimalField, StringField, IntegerField, TextAreaField, FloatField, SelectField, FieldList, FormField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange 
from app.models.invoice import Invoice, PaymentTerms  
from app.models.task import TaskFlowInvoice
from datetime import date
from flask_login import  current_user

class InvoiceDetailForm(FlaskForm):
    product_id = IntegerField('Product ID')
    service_id = IntegerField('Service ID')
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    unit_name = StringField('Unit Name', validators=[DataRequired()])
    unit_price = FloatField('Unit Price', validators=[DataRequired()])
    discount = FloatField('Discount')
    total_amount = FloatField('Total Amount', validators=[DataRequired()])
    status = SelectField('Status', choices=[('order', 'Order'), ('invoice', 'Invoice'), ('processing', 'Processing'), ('received', 'Received'), ('retur', 'Return')])  

class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])
    address = StringField('Address', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    submit = SubmitField('Add Customer')

class InvoiceForm(FlaskForm):
    existing_customer = SelectField('Select Existing Customer', coerce=int)
    new_customer = FormField(CustomerForm)
    additional_notes = TextAreaField('Additional Notes')
    reference = SelectField('Reference', choices=[('regular', 'Regular'), ('express', 'Express'), ('other', 'Other')])
    promotion_program = StringField('Promotion Program')
    total_amount = FloatField('Total Amount', validators=[DataRequired()])
    total_discount = FloatField('Total Discount', default=0.0)
    total_tax = FloatField('Total Tax', default=0.0)
    net_amount = FloatField('Net Amount', validators=[DataRequired()])
    payment_terms = SelectField('Payment Terms', choices=[('COD', 'COD'), ('Net 30', 'Net 30'), ('Net 60', 'Net 60')], default='COD')
    delivery_terms = SelectField('Delivery Terms', choices=[('FOB', 'FOB'), ('EXW', 'EXW'), ('DAP', 'DAP')], default='FOB')
    terms_disc = FloatField('Discount Terms', default=0.0)
    terms_days_disc = FloatField('Days Discount', default=0)
    terms_days_due = FloatField('Days Due', default=0)
    items = FieldList(FormField(InvoiceDetailForm), min_entries=1)
    created_date_date = DateField('Date', default=date.today)
    due_date = DateField('Due Date', default=date.today)
    submit = SubmitField('Save Invoice')
    
    def validate_customer_id(form, field):
        customer = Customer.query.get(field.data)
        if not customer:
            raise ValidationError('Customer ID does not exist.')
        if customer.sales_term != 'COD' and customer.receivable_balance + form.net_amount.data > customer.credit_limit:
            raise ValidationError('Customer credit limit exceeded.')
 
class CashPaymentForm(FlaskForm):
    jumlah_bayar = DecimalField(
        'Jumlah Bayar', 
        validators=[DataRequired(), NumberRange(min=0)], 
        render_kw={"min": "0", "step": "1000"}
    )
    hidden_jumlah_bayar = HiddenField('Hidden Jumlah Bayar')
    submit = SubmitField('Proses Pembayaran')
    
class InvoiceConfirmationForm(FlaskForm):
    created_date = DateField('Invoice Date', default=date.today, validators=[DataRequired()])
    due_date = DateField('Due Date', default=date.today, validators=[DataRequired()])
    payment_terms = SelectField('Payment Terms', choices=[], default='COD', validators=[DataRequired()])
    additional_notes = TextAreaField('Additional Notes')
    submit = SubmitField('Save Invoice')

    def __init__(self, *args, **kwargs):
        super(InvoiceConfirmationForm, self).__init__(*args, **kwargs)
        # Load dynamic choices for payment terms
        self.payment_terms.choices = self.get_payment_terms_choices()

    def get_payment_terms_choices(self):
        # This method should fetch payment terms dynamically based on the user_app_id
        payment_terms = PaymentTerms.query.filter_by(user_app_id=current_user.user_app_id).all()  
        return [(term.id, term.name) for term in payment_terms]
        
class InvoiceTaskForm(FlaskForm):
    task_seq = SelectField('Task Sequence', coerce=int)  
    review_notes = TextAreaField('Review')
    assigned_to = StringField('Assigned To', validators=[DataRequired()])
    submit = SubmitField('Update')