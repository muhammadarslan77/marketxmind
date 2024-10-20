# routes/campaign.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.models.campaign import Campaign, CampaignMetric
from app.models.loyalty import LoyaltyProgram
from app.forms.campaign import CampaignForm, DeleteCampaignForm
import re
from markupsafe import escape

campaign = Blueprint('campaign', __name__)

@campaign.route('/campaigns', methods=['GET'])
def list_campaigns():
    campaigns = Campaign.query.all()
    form =DeleteCampaignForm()
    return render_template('campaign/list_campaign.html', campaigns=campaigns, form=form)


@campaign.route('/campaign/add', methods=['GET', 'POST'])
def add_campaign():
    form = CampaignForm()
    # Populate choices for the loyalty program dropdown
    form.program_id.choices = [(p.id, p.name) for p in LoyaltyProgram.query.all()]
    if form.validate_on_submit():
        new_campaign = Campaign(
            name=form.name.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            transaction_number=form.transaction_number.data,
            text=re.sub(r'<[^>]*>', '', form.text.data) ,
            text_email=form.text_email.data,
            text_sms=form.text_sms.data,
            is_scheduler=form.is_scheduler.data,
            interval_days=form.interval_days.data,
            whatsapp=form.whatsapp.data,
            sms=form.sms.data,
            email=form.email.data,
            is_active=form.is_active.data,
            program_id=form.program_id.data
        )
        db.session.add(new_campaign)
        db.session.commit()
        flash('Campaign berhasil ditambahkan!', 'success')
        return redirect(url_for('campaign.list_campaigns'))
    else :
        print('Form errors:', form.errors)
    return render_template('campaign/add_campaign.html', form=form)



@campaign.route('/campaign/edit/<int:id>', methods=['GET', 'POST'])
def update_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    form = CampaignForm(obj=campaign)
    form.program_id.choices = [(p.id, p.name) for p in LoyaltyProgram.query.filter_by(company_id=current_user.company_id).all()]

    if form.validate_on_submit():
        campaign.name = form.name.data
        campaign.description = form.description.data
        campaign.start_date = form.start_date.data
        campaign.end_date = form.end_date.data
        campaign.transaction_number = form.transaction_number.data
        campaign.text = re.sub(r'<[^>]*>', '', form.text.data)
        campaign.text_email = form.text_email.data
        campaign.text_sms = form.text_sms.data
        campaign.is_scheduler = form.is_scheduler.data
        campaign.interval_days = form.interval_days.data
        campaign.whatsapp = form.whatsapp.data
        campaign.sms = form.sms.data
        campaign.email = form.email.data
        campaign.is_active = form.is_active.data
        campaign.program_id = form.program_id.data
        
        db.session.commit()
        flash('Campaign berhasil diperbarui!', 'success')
        return redirect(url_for('campaign.list_campaigns'))

    return render_template('campaign/add_campaign.html', form=form)


@campaign.route('/campaign/delete/<int:id>', methods=['POST'])
def delete_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    if campaign :
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign berhasil dihapus!', 'success')
    return redirect(url_for('campaign.list_campaigns'))
