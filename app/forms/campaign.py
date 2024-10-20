from flask_wtf import FlaskForm
from wtforms import HiddenField, BooleanField, DateField, StringField, IntegerField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

class CampaignForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    program_id = SelectField('Loyalty Program', coerce=int, validators=[DataRequired()])
    transaction_number = IntegerField('Transaction Number', validators=[Optional()], default=0)
    text = TextAreaField('WhatsApp Text', validators=[Optional()])
    text_email = TextAreaField('Email Text', validators=[Optional()])
    text_sms = StringField('SMS Text', validators=[Optional()])
    is_scheduler = BooleanField('Use Scheduling', default=False)
    interval_days = IntegerField('Scheduled Every (Days)', validators=[Optional()], default=1)
    whatsapp = BooleanField('Enable WhatsApp', default=True)
    sms = BooleanField('Enable SMS', default=True)
    email = BooleanField('Enable Email', default=True)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save')

    
class DeleteCampaignForm(FlaskForm):
    campaign_id = HiddenField('Notification ID')
    submit = SubmitField('Delete')
