from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SelectField, SubmitField, DateField, RadioField
from wtforms.validators import DataRequired, Length, Email, Optional, NumberRange
from app.utilities.custom_fields import AppDateField

class ReportForm(FlaskForm):
    date_from = DateField('From Date', validators=[Optional()])
    date_until = DateField('Until Date', validators=[Optional()])
    criteria = SelectField('Period', choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], validators=[Optional()])
    reporttype = SelectField('Report Type', choices=[
        ('kpi', 'Key Performance Indicators (KPIs)'),
        ('omset', 'Revenue and Payment Report'), 
        ('cash_flow', 'Cash Flow'), 
        ('aging', 'Accounts Receivable Aging Schedule'), 
        ('piutang', 'Customer Receivables List')
    ], validators=[Optional()])
    submit = SubmitField('Generate Report')


class ReportFormBelum(FlaskForm):
    date_from = DateField('From Date', validators=[Optional()])
    date_until = DateField('Until Date', validators=[Optional()])
    criteria = SelectField('Period', choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], validators=[Optional()])
    reporttype = SelectField('Report Type', choices=[
        ('kpi', 'Key Performance Indicators (KPIs)'),
        ('omset', 'Revenue and Payment Report'), 
        ('aging', 'Accounts Receivable Aging Schedule'), 
        ('piutang', 'Customer Receivables List'),
        ('inventory', 'Inventory Report'),
        ('open_invoice', 'Open Invoice Report'),
        ('order_process', 'Orders in Process Report'),
        ('order_complated', 'Completed Orders Report')
    ], validators=[Optional()])
    submit = SubmitField('Generate Report')
