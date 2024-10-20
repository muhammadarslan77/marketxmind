import os
import logging
import locale
from datetime import datetime
from flask import Flask, render_template, send_from_directory, send_file, request, redirect, url_for , flash , jsonify 
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from .utilities.utils import calculate_total_price, format_currency, current_utc_datetime, tax_rate, calculate_total_tax 
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
   
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    with app.app_context():
        from .models import customer
        from .models import invoice
        from .models import invoice_detail
        from .models import payment
        from .models import product
        from .models import loyalty
        from .models import campaign
        from .models import feedback
        from .models import task

 
    from app.routes.advancecrm import advancecrm as advancecrm_bp
    from app.routes.segmentation import segmentation as segmentation_bp
    from app.routes.campaign import campaign as campaign_bp
    from app.routes.loyalty import loyalty as loyalty_bp
    from app.routes.feedback import feedback as feedback_bp
    from app.routes.churn import churn as churn_bp
    from app.routes.customer import customer as customer_bp
        
    app.register_blueprint(advancecrm_bp)
    app.register_blueprint(segmentation_bp)
    app.register_blueprint(campaign_bp)
    app.register_blueprint(loyalty_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(churn_bp)
    app.register_blueprint(customer_bp)
    locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')

    logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    
    app.jinja_env.filters['currency'] = format_currency
    app.jinja_env.globals['current_utc_datetime'] = current_utc_datetime
    app.jinja_env.globals['tax_rate'] = tax_rate
    app.jinja_env.globals['calculate_total_tax'] = calculate_total_tax
    
    
    @app.route('/img/icons/icon-512x512.png')
    def icon_512_512():
        image_dir = os.path.join(app.root_path, 'static', 'dashboard', 'img', 'icons')
        return send_from_directory(image_dir, 'icon-512x512.png')
    @app.route('/image/<filename>')
    def serve_image(filename):
        try:
            img_path_dir = os.path.join('app', 'static', 'temp', 'downloads')
            image_path = os.path.abspath(os.path.join(img_path_dir, filename))
            return send_file(image_path, mimetype='image/jpeg')
        except FileNotFoundError:
            return jsonify({'error': 'Image not found'}), 404
            
        
    @app.route('/service-worker.js')
    def service_worker():
        return send_from_directory('static', 'service-worker.js')
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('dashboard/error_message.html', success= False, title='Error 400', message = 'CSRF token missing or invalid.', message_id ='CSRF token missing or invalid.')
    
    @app.route('/', methods=['GET'])
    def index():
        return render_template('intro.html')
        
    
    @app.route('/dashboard/access_denied')
    def error_message():    
        return render_template('dashboard/error_message.html', success= False, title='Access Denied', message = 'You do not have permission to access this resource', message_id ='Anda tidak memiliki izin untuk mengakses sumber daya ini.')
    
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('400.html'), 400

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    return app
