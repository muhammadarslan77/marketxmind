from flask_wtf import FlaskForm
from wtforms import HiddenField, DecimalField, StringField, IntegerField, TextAreaField, FloatField, SelectField, SubmitField, FieldList, FormField, MultipleFileField, DateField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange
from app.models.product import UnitList, ProductImage, Product
from flask_login import current_user
from app import db  # Import db from your app module

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    existing_model = SelectField('Existing Model', choices=[])
 
    new_model = StringField('Or Enter New Model', validators=[Optional()])
    
    qr_code = StringField('Barcode/QR Code', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])

    unit = SelectField('Unit', validators=[Optional()])
    price_unit = FloatField('Price per Unit', default=0.0, validators=[NumberRange(min=0)], render_kw={"type": "number"})
    qty_unit = FloatField('Quantity per Unit', default=1.0, validators=[NumberRange(min=1)], render_kw={"type": "number"})

    unit_sales = SelectField('Sales Unit', validators=[Optional()])
    price_sales = FloatField('Price per Sales Unit', default=0.0, validators=[Optional(), NumberRange(min=0)], render_kw={"type": "number"})
    ratio_qty_sales = FloatField('Ratio per Sales Unit', default=1.0, validators=[Optional(), NumberRange(min=1)], render_kw={"type": "number"})
    qty_sales = FloatField('Quantity for Sales Unit', validators=[Optional()])

    unit_purchases = SelectField('Purchase Unit', validators=[Optional()])
    price_purchases = FloatField('Price per Purchase Unit', default=0.0, validators=[Optional(), NumberRange(min=0)], render_kw={"type": "number"})
    ratio_qty_purchases = FloatField('Ratio per Purchase Unit', default=1.0, validators=[Optional(), NumberRange(min=1)], render_kw={"type": "number"})
    qty_purchases = FloatField('Quantity for Purchase Unit', validators=[Optional()])

    qty_reorder = FloatField('Reorder Quantity', default=1.0, validators=[NumberRange(min=0)], render_kw={"type": "number"})

    is_active = BooleanField('Is Active', default=True)
    is_service = BooleanField('Is Service', default=False)
    is_sale = BooleanField('Is Sale', default=True)
    is_buy = BooleanField('Is Buy', default=False)
    is_raw = BooleanField('Is Raw', default=False)
    is_sell_online = BooleanField('Is Sell Online', default=False)

    images = MultipleFileField('Product Images', render_kw={"multiple": True})

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        distinct_models = db.session.query(Product.model.distinct()).filter_by(user_app_id=current_user.user_app_id).all()
        self.existing_model.choices = [
            ('', 'Pilih Model yang Ada')] + [(model[0], model[0]) for model in distinct_models] + [('new', 'Tambah Model Baru')]
        unit_choices = [
            (str(unit.id), unit.UnitName) 
            for unit in UnitList.query.filter_by(user_app_id=current_user.user_app_id).all()
        ]
        self.unit.choices = unit_choices
        self.unit_sales.choices = unit_choices
        self.unit_purchases.choices = unit_choices

    def calculate_qty(self):
        unit = UnitList.query.get(self.unit.data)
        unit_sales = UnitList.query.get(self.unit_sales.data)
        unit_purchases = UnitList.query.get(self.unit_purchases.data)

        if unit_sales and unit:
            if unit_sales.Dimension != unit.Dimension:
                self.qty_sales.data = self.ratio_qty_sales.data * (unit_sales.Dimension / unit.Dimension)
            else:
                self.qty_sales.data = self.ratio_qty_sales.data

        if unit_purchases and unit:
            if unit_purchases.Dimension != unit.Dimension:
                self.qty_purchases.data = self.ratio_qty_purchases.data * (unit_purchases.Dimension / unit.Dimension)
                self.unit_purchases.data=unit_purchases.UnitName
            else:
                self.qty_purchases.data = self.ratio_qty_purchases.data
                
class UnitListForm(FlaskForm):
    UnitName = StringField('Name', validators=[DataRequired()])
    UnitSymbol = StringField('Simbol', validators=[DataRequired()])
    Dimension = IntegerField('Dimension', default=1, validators=[DataRequired()])
    Label1 = StringField('Label 1', default="Unit", validators=[DataRequired()])
    Label2 = StringField('Label 2', default="", validators=[Optional()])
    Label3 = StringField('Label 3', default="", validators=[Optional()])
    submit = SubmitField('Submit')