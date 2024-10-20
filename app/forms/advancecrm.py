from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, FloatField, TextAreaField, StringField, IntegerField, BooleanField, SelectField, SubmitField, DateField, RadioField
from wtforms.validators import DataRequired, Length, Email, Optional, NumberRange
from app.utilities.custom_fields import AppDateField

class LoyaltyProgramForm(FlaskForm):
    name = StringField('Program Name', validators=[DataRequired()])
    description = StringField('Program Description', validators=[Optional()])
    points = IntegerField('Points Given for Every USD Purchase Multiple', validators=[Optional()])
    discount = FloatField('Discount Amount (% or Rp. Amount)', validators=[Optional()])

    # New fields
    discount_type = SelectField(
        'Discount Type',
        choices=[('1', 'Percentage'), ('2', 'USD'), ('3', 'Free')],
        validators=[Optional()]
    )
    discount_repeat_number = IntegerField(
        'Discount Given for Every Transaction Multiple',
        validators=[Optional()],
        default=1
    )
    discount_repeat = BooleanField(
        'Discount Repeated for Every Multiple',
        default=True,
        description="Check if the discount is applied for every transaction multiple"
    )
    discount_points = BooleanField(
        'Discount and Points Given Together',
        default=True,
        description="Check if customers still receive reward points for the given discount"
    )

    submit = SubmitField('Create Program')


class CampaignForm(FlaskForm):
    name = StringField('Program Name', validators=[DataRequired()])
    discount = FloatField('Discount (%)', validators=[DataRequired()])
    target_segment = StringField('Target Segment (e.g., VIP, Regular)', validators=[DataRequired()])
    duration = IntegerField('Campaign Duration (Days)', validators=[DataRequired()])
    repeat = IntegerField('Repeat Interval (Days)', validators=[DataRequired()])
    submit = SubmitField('Create Program')


class FeedbackForm(FlaskForm):
    customer_id = IntegerField('Customer ID', validators=[DataRequired()])
    feedback_text = TextAreaField('Feedback', validators=[DataRequired()])
    rating = IntegerField('Rating (1-5)', validators=[DataRequired()])
    submit = SubmitField('Submit Feedback')
