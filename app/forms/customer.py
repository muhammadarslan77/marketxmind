from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, SubmitField, RadioField, DateField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, NumberRange

class CustomerForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    address_line1 = StringField('Address', validators=[DataRequired()])
    address_line2 = StringField('')
    city = StringField('City', validators=[DataRequired()])
    zip = StringField('Postal Code', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    company_name = StringField('Company Name')
    receivable_balance = FloatField('Receivable Balance', default=0.0)
    sales_term = StringField('Sales Term')
    credit_limit = FloatField('Credit Limit', default=0.0)
    type = SelectField('Type', choices=[('personal', 'Personal'), ('business', 'Business')])
    status = SelectField('Status', choices=[('active', 'Active'), ('blacklist', 'Blacklist'), ('deactivate', 'Deactivate'), ('member', 'Member')])


class ReportFormCustomer(FlaskForm):
    date_from = DateField('From Date', validators=[Optional()])
    date_until = DateField('Until Date', validators=[Optional()])
    customer_name = StringField('Customer Name', validators=[Optional()])
    order_count = IntegerField('Minimum Order Count', validators=[Optional(), NumberRange(min=0)])
    reward_count = IntegerField('Minimum Amount Count', validators=[Optional(), NumberRange(min=0)])
    sort_by = SelectField('Sort By', choices=[('name', 'Name'), ('order_count', 'Number of Invoices'), ('reward_count', 'Number of Receivables')], validators=[Optional()])
    sort_order = SelectField('Sort Order', choices=[('asc', 'Ascending'), ('desc', 'Descending')], validators=[Optional()])
    report_type = RadioField('Report Type', choices=[('detail', 'Detail'), ('summary', 'Summary')], default='detail', validators=[Optional()])
    submit = SubmitField('Generate Report')
