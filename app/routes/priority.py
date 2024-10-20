from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.models.sales_parameter  import SalesParameter
from app.models.invoice  import PriorityList, PaymentTerms
from app.forms.priority import PriorityListForm , DeletePriorityForm
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import base64
import io
import os
from PIL import Image  
from io import BytesIO
from config import Config

priority = Blueprint('priority', __name__)

@priority.route('/priority/create', methods=['GET', 'POST'])
def create_priority():
    form = PriorityListForm()
    if form.validate_on_submit():
        priority = PriorityList(
            name=form.name.data,
            AdditionalCost=form.AdditionalCost.data,
            ProcessingTimeValue=form.ProcessingTimeValue.data,
            ProcessingTimeUnit=form.ProcessingTimeUnit.data,
            is_default=form.is_default.data,
            is_active=form.is_active.data,
            user_id=current_user.id,
            user_app_id=1
        )
        db.session.add(priority)
        db.session.commit()
        flash('PriorityList created successfully!', 'success')
        return redirect(url_for('priority.list_priorities'))
    return render_template('priority/create_priority.html', form=form)


@priority.route('/priority/priorities', methods=['GET'])
def list_priorities():
    priority = PriorityList.query.filter_by(user_app_id=1).all()
    form = DeletePriorityForm()
    return render_template('priority/list_priorities.html', priorities=priority ,form=form)


@priority.route('/priority/<int:id>/update', methods=['GET', 'POST'])
def update_priority(id):
    priority = PriorityList.query.get_or_404(id)
    form = PriorityListForm(obj=priority)
    if form.validate_on_submit():
        priority.name = form.name.data
        priority.AdditionalCost = form.AdditionalCost.data
        priority.ProcessingTimeValue = form.ProcessingTimeValue.data
        priority.ProcessingTimeUnit = form.ProcessingTimeUnit.data
        priority.is_default = form.is_default.data
        priority.is_active = form.is_active.data
        db.session.commit()
        flash('PriorityList updated successfully!', 'success')
        return redirect(url_for('priority.list_priorities'))
    return render_template('priority/update_priority.html', form=form)


@priority.route('/priority/<int:id>/delete', methods=['POST'])
def delete_priority(id):
    priority = PriorityList.query.get_or_404(id)
    db.session.delete(priority)
    db.session.commit()
    flash('PriorityList deleted successfully!', 'success')
    return redirect(url_for('priority.list_priorities'))
