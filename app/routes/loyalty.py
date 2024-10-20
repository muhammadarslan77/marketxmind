# routes/loyalty.py
from flask_wtf import FlaskForm
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.models.loyalty import LoyaltyProgram, LoyaltyTier
from app.forms.loyalty import LoyaltyProgramForm, LoyaltyTierForm, DeleteTierForm,  DeleteLoyaltyProgramForm

loyalty = Blueprint('loyalty', __name__)

@loyalty.route('/loyalty/programs', methods=['GET'])
def list_programs():
    programs = LoyaltyProgram.query.all()
    form = DeleteLoyaltyProgramForm()
    return render_template('loyalty/list_loyalty.html', programs=programs,form=form)


@loyalty.route('/loyalty/program/add', methods=['GET', 'POST'])
def add_program():
    form = LoyaltyProgramForm()
    if form.validate_on_submit():
        new_program = LoyaltyProgram(
            name=form.name.data,
            description=form.description.data,
            points=form.points.data,
            points_rp=form.points_rp.data,
            points_active=form.points_active.data,
            discount=form.discount.data,
            discount_type=int(form.discount_type.data),
            discount_repeat_number=form.discount_repeat_number.data,
            discount_repeat=form.discount_repeat.data,
            discount_points=form.discount_points.data,
            is_active=form.is_active.data,
            is_newcustomer = form.is_newcustomer.data,
            is_oldcustomer = form.is_newcustomer.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )
        db.session.add(new_program)
        db.session.commit()
        flash('Loyalty added!', 'success')
        return redirect(url_for('loyalty.list_programs'))
    
    return render_template('loyalty/add_loyalty_program.html', form=form)


@loyalty.route('/loyalty/program/edit/<int:id>', methods=['GET', 'POST'])
def update_program(id):
    program = LoyaltyProgram.query.get_or_404(id)
    form = LoyaltyProgramForm(obj=program)
    
    if form.validate_on_submit():
        program.name = form.name.data
        program.description = form.description.data
        program.points = form.points.data
        program.points_rp=form.points_rp.data
        program.points_active=form.points_active.data
        program.discount = form.discount.data
        program.discount_type = int(form.discount_type.data)
        program.discount_repeat_number = form.discount_repeat_number.data
        program.discount_repeat = form.discount_repeat.data
        program.discount_points = form.discount_points.data
        program.is_active=form.is_active.data
        program.is_newcustomer = form.is_newcustomer.data
        program.is_oldcustomer = form.is_newcustomer.data
        program.start_date=form.start_date.data
        program.end_date=form.end_date.data
        db.session.commit()
        #flash('Loyalty updated!', 'success')
        return redirect(url_for('loyalty.list_programs'))
    
    return render_template('loyalty/add_loyalty_program.html', form=form)


@loyalty.route('/loyalty/program/delete/<int:id>', methods=['POST'])
def delete_program(id):
    form = DeleteLoyaltyProgramForm()
    if form.validate_on_submit():
        program = LoyaltyProgram.query.get_or_404(id)
        if program :
            db.session.delete(program)
            db.session.commit()
        #flash('Loyalty deleted!', 'success')
    return redirect(url_for('loyalty.list_programs'))

@loyalty.route('/loyalty/tiers', methods=['GET'])
def list_tiers():

    tiers = db.session.query(LoyaltyTier, LoyaltyProgram) \
            .join(LoyaltyProgram, LoyaltyTier.program_id == LoyaltyProgram.id).all()
    form = DeleteTierForm()
    return render_template('loyalty/list_tiers.html', tiers=tiers,form=form)

@loyalty.route('/loyalty/tier/add', methods=['GET', 'POST'])
def add_tier():
    form = LoyaltyTierForm()
    form.program_id.choices = [(p.id, p.name) for p in LoyaltyProgram.query.filter_by(company_id=current_user.company_id).all()]

    if form.validate_on_submit():
        new_tier = LoyaltyTier(
            name=form.name.data,
            points_threshold=form.points_threshold.data,
            benefits=form.benefits.data,
            program_id=form.program_id.data
        )
        db.session.add(new_tier)
        db.session.commit()
        flash('Loyalty Tier added!', 'success')
        return redirect(url_for('loyalty.list_tiers'))
    
    return render_template('loyalty/add_tier.html', form=form)


@loyalty.route('/loyalty/tier/edit/<int:id>', methods=['GET', 'POST'])
def edit_tier(id):
    tier = LoyaltyTier.query.get_or_404(id)
    form = LoyaltyTierForm(obj=tier)
    form.program_id.choices = [(p.id, p.name) for p in LoyaltyProgram.query.all()]

    if form.validate_on_submit():
        tier.name = form.name.data
        tier.points_threshold = form.points_threshold.data
        tier.benefits = form.benefits.data
        tier.program_id = form.program_id.data
        db.session.commit()
        flash('Loyalty Tier updated!', 'success')
        return redirect(url_for('loyalty.list_tiers'))
    
    return render_template('loyalty/add_tier.html', form=form)


@loyalty.route('/loyalty/tier/delete/<int:id>', methods=['POST'])
def delete_tier(id):
    form = DeleteTierForm()
    if form.validate_on_submit():
        tier = LoyaltyTier.query.get_or_404(id)
        if tier: 
            db.session.delete(tier)
            db.session.commit()
            flash('Loyalty Tier deleted!', 'success')
    return redirect(url_for('loyalty.list_tiers'))