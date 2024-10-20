from wtforms.fields import DateField
from flask import current_app

class AppDateField(DateField):
    def __init__(self, label='', validators=None, format=None, **kwargs):
        if format is None:
            format = current_app.config['DATE_FORMAT']
        super().__init__(label, validators, format=format, **kwargs)
