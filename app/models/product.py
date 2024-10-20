import os
from app import db
from sqlalchemy import Enum
from enum import Enum as PyEnum
from config import Config
from openai import OpenAI
import re
from sqlalchemy.exc import SQLAlchemyError


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    model = db.Column(db.String(100), nullable=True)
    qr_code = db.Column(db.String(255), nullable=True, default="")
    description = db.Column(db.Text, nullable=True)
    unit = db.Column(db.String(100), nullable=False, default="unit")
    price_unit = db.Column(db.Float, nullable=False, default=0.0)
    qty_unit = db.Column(db.Float, nullable=False, default=1.0)
    cogs = db.Column(db.Float, nullable=False, default=0.0)
    
    unit_sales = db.Column(db.String(100), nullable=False, default="unit")
    price_sales = db.Column(db.Float, nullable=False, default=0.0)
    qty_sales = db.Column(db.Float, nullable=False, default=1.0)
    ratio_qty_sales = db.Column(db.Float, nullable=False, default=1.0)
    
    unit_purchases = db.Column(db.String(100), nullable=False, default="unit")
    price_purchases = db.Column(db.Float, nullable=False, default=0.0)
    qty_purchases = db.Column(db.Float, nullable=False, default=1.0)
    ratio_qty_purchases = db.Column(db.Float, nullable=False, default=1.0)
    
    qty_reorder = db.Column(db.Float, nullable=False, default=0.0)
    qty_on_hand = db.Column(db.Float, nullable=False, default=0.0)
    cogs_perunit = db.Column(db.String(100), nullable=False, default="unit")
     
    is_active = db.Column(db.Boolean, default=False)
    is_service = db.Column(db.Boolean, default=False)
    is_sale = db.Column(db.Boolean, default=True)
    is_buy = db.Column(db.Boolean, default=False)
    is_raw = db.Column(db.Boolean, default=False)
    is_sell_online = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, nullable=True)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    carbon_emission = db.Column(db.Float, nullable=True, default=0.0)
    calculate_emission = db.Column(db.Text, nullable=True,default='')
    
    images = db.relationship('ProductImage', backref='product', lazy=True)

    def __init__(self, name, model, description=None, unit="unit", price_unit=0.0, 
                 qty_unit=1.0, cogs=0.0, unit_sales="unit", price_sales=0.0, 
                 qty_sales=1.0, ratio_qty_sales=1.0, unit_purchases="unit", 
                 price_purchases=0.0, qty_purchases=1.0, ratio_qty_purchases=1.0, 
                 qty_reorder=0.0, qty_on_hand=0.0, cogs_perunit="unit", 
                 is_active=False, is_service=False, is_sale=True, 
                 is_buy=False, is_raw=False, is_sell_online=False, 
                 user_id=None ):
        self.name = name
        self.model = model
        self.description = description or ""
        self.unit = unit
        self.price_unit = price_unit
        self.qty_unit = qty_unit
        self.cogs = cogs
        self.unit_sales = unit_sales
        self.price_sales = price_sales
        self.qty_sales = qty_sales
        self.ratio_qty_sales = ratio_qty_sales
        self.unit_purchases = unit_purchases
        self.price_purchases = price_purchases
        self.qty_purchases = qty_purchases
        self.ratio_qty_purchases = ratio_qty_purchases
        self.qty_reorder = qty_reorder
        self.qty_on_hand = qty_on_hand
        self.cogs_perunit = cogs_perunit
        self.is_active = is_active
        self.is_service = is_service
        self.is_sale = is_sale
        self.is_buy = is_buy
        self.is_raw = is_raw
        self.is_sell_online = is_sell_online
        self.user_id = user_id

        
        
    def predict_carbon_emission(self):
        
        unit = UnitList.query.filter_by(id=self.unit).first()
        unit_name = unit.UnitSymbol if unit else "Unit"
        
        unit_sales = UnitList.query.filter_by(id=self.unit_sales).first()
        unit_sales_name = unit_sales.UnitSymbol if unit_sales else "Unit"
        
        unit_purchases = UnitList.query.filter_by(id=self.unit_purchases).first()
        unit_purchases_name = unit_purchases.UnitSymbol if unit_purchases else "Unit"

        user_prompt = (f"Estimate the carbon footprint in kg CO2e for {self.name}, {self.model}, {self.description}, {self.qty_sales}-{unit_sales_name} in Indonesia. Respond with only a number."  
        )
        print(user_prompt)
        try:
         
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{
                    "role": "user",
                    "content": user_prompt,
                }],
            )
            emissions_value = completion.choices[0].message.content
            numeric_value = re.sub(r'[^\d.]', '', emissions_value)
            if numeric_value:
                emission_prediction = float(numeric_value)
            else:
                emission_prediction = 0.0  

            calculate_emission = emissions_value if emissions_value else ""
            
        except Exception as e:
            emission_prediction = 0.0  
            calculate_emission = ''

        self.calculate_emission = emission_prediction
        self.carbon_emission = calculate_emission
        
        try:
            db.session.commit() 
        except SQLAlchemyError as e:
            db.session.rollback()

class UnitList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    UnitName = db.Column(db.String(30), nullable=False, default="Unit")
    UnitSymbol = db.Column(db.String(10), nullable=False, default="Unit")
    Dimension = db.Column(db.Integer, nullable=False, default=1)
    Label1 = db.Column(db.String(20), nullable=False, default="Unit")
    Label2 = db.Column(db.String(20), nullable=True, default="")
    Label3 = db.Column(db.String(20), nullable=True, default="")
    user_id = db.Column(db.Integer, nullable=True)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())


class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(255), nullable=True)
    image_name_300 = db.Column(db.String(255), nullable=True)
    image_name_original = db.Column(db.String(255), nullable=True)
    image_file = db.Column(db.String(255), nullable=True)
    Dimension = db.Column(db.Text, nullable=True)
    is_main = db.Column(db.Boolean, default=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=True)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())

