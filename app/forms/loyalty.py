# forms/loyalty.py
from flask_wtf import FlaskForm
from wtforms import DateField, HiddenField, TextAreaField, StringField, IntegerField, FloatField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

class LoyaltyProgramForm(FlaskForm):
    name = StringField('Program Name', validators=[DataRequired()])
    description = StringField('Program Description', validators=[Optional()])
    points_active = BooleanField(
        'Activate Point Reward',
        default=True
    )
    points = IntegerField('Points Given For Purchases Multiples of USD ', validators=[Optional()])
    points_rp = IntegerField('Point Value in USD', validators=[Optional()])
    discount = FloatField('Discount Amount Given (% or Rp Amount)', validators=[Optional()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()]) 
    discount_type = SelectField(
        'Discount Type',
        choices=[('1', 'Percent'), ('2', 'USD'), ('3', 'Free')],
        validators=[Optional()]
    )
    discount_repeat_number = IntegerField(
        'Discount given for transactions in multiples of ',
        validators=[Optional()],
        default=1
    )
    discount_repeat = BooleanField(
        'Discount given repeatedly for every multiple',
        default=True
    )
    discount_points = BooleanField(
        'Activate Discount Rewards',
        default=True
    )
    is_active = BooleanField('Active', default=True)
    is_newcustomer = BooleanField('New Customer', default=True)
    is_oldcustomer = BooleanField('Existing Customer', default=True)
    submit = SubmitField('Create Program')


class LoyaltyTierForm(FlaskForm):
    name = StringField('Tier Name', validators=[DataRequired()])
    points_threshold = IntegerField('Point Threshold (Minimum)', validators=[DataRequired()])
    benefits = TextAreaField('Tier Benefits', validators=[Optional()])
    program_id = SelectField('Loyalty Program', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Tier')


class DeleteTierForm(FlaskForm):
    tier_id = HiddenField('Tier ID')
    submit = SubmitField('Delete')
    
    
class DeleteLoyaltyProgramForm(FlaskForm):
    program_id = HiddenField('Program ID')
    submit = SubmitField('Delete')
