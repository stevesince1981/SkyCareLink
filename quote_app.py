import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Create Flask app
quote_app = Flask(__name__, template_folder='templates')
quote_app.secret_key = os.environ.get("SESSION_SECRET", "quote-demo-key")

# Database configuration
quote_app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
quote_app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
db = SQLAlchemy(quote_app, model_class=Base)

# Define models directly here to avoid import issues
from datetime import datetime, timedelta
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'individual', 'affiliate', 'admin'
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Rate limiting
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    # Relationships
    quotes_requested = db.relationship('Quote', foreign_keys='Quote.individual_id', back_populates='individual')
    quotes_responded = db.relationship('Quote', foreign_keys='Quote.affiliate_id', back_populates='affiliate')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self):
        self.verification_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(50))
        return self.verification_token
    
    def is_locked(self):
        return self.locked_until and self.locked_until > datetime.utcnow()
    
    def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=5)
    
    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.locked_until = None

class Quote(db.Model):
    __tablename__ = 'quotes'
    
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(50), unique=True, nullable=False)
    individual_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Quote details
    pickup_location = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(255), nullable=False)
    transport_date = db.Column(db.DateTime, nullable=False)
    patient_condition = db.Column(db.Text)
    special_requirements = db.Column(db.Text)
    
    # Quote response
    quoted_price = db.Column(db.Float)
    quote_details = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, quoted, confirmed, cancelled
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    quoted_at = db.Column(db.DateTime)
    confirmed_at = db.Column(db.DateTime)
    
    # Relationships
    individual = db.relationship('User', foreign_keys=[individual_id], back_populates='quotes_requested')
    affiliate = db.relationship('User', foreign_keys=[affiliate_id], back_populates='quotes_responded')
    
    @staticmethod
    def generate_reference():
        today = datetime.utcnow().strftime('%Y%m%d')
        # Get count of quotes today
        count = Quote.query.filter(Quote.reference_number.like(f'Q-{today}-%')).count() + 1
        return f'Q-{today}-{count:04d}'

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    template = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # SENT, FAILED
    smtp_response = db.Column(db.Text)
    error_message = db.Column(db.Text)
    
    # Related quote if applicable
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'))
    quote = db.relationship('Quote')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Related entities
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'))
    
    user = db.relationship('User')
    quote = db.relationship('Quote')

# Import services
from services.email_service import email_service

# Import and register blueprints
from routes.auth import auth_bp
from routes.quotes import quotes_bp
from routes.affiliate import affiliate_bp
from routes.admin import admin_bp

quote_app.register_blueprint(auth_bp)
quote_app.register_blueprint(quotes_bp)
quote_app.register_blueprint(affiliate_bp)
quote_app.register_blueprint(admin_bp)

# Create tables and admin user
with quote_app.app_context():
    db.create_all()
    
    # Create admin user if none exists
    admin_user = User.query.filter_by(user_type='admin').first()
    if not admin_user:
        admin = User(
            email='admin@skycarelink.com',
            user_type='admin',
            is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✓ Created admin user: admin@skycarelink.com / admin123")

# Home route
@quote_app.route('/')
def home():
    return '''
    <html>
    <head>
        <title>SkyCareLink Quote System</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .card { box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card mt-5">
                        <div class="card-header bg-primary text-white text-center">
                            <h2>SkyCareLink Quote System</h2>
                            <p class="mb-0">Medical Transport Quote Platform</p>
                        </div>
                        <div class="card-body text-center">
                            <h4 class="mb-4">Welcome to the Pilot System</h4>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <a href="/register" class="btn btn-success btn-lg w-100">Create Account</a>
                                    <small class="text-muted d-block mt-2">New users</small>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <a href="/login" class="btn btn-primary btn-lg w-100">Sign In</a>
                                    <small class="text-muted d-block mt-2">Existing users</small>
                                </div>
                            </div>
                            <hr>
                            <div class="mt-3">
                                <h6>Admin Access</h6>
                                <p class="small text-muted">admin@skycarelink.com / admin123</p>
                                <a href="/admin/dashboard" class="btn btn-outline-dark">Admin Dashboard</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == "__main__":
    quote_app.run(host="0.0.0.0", port=5000, debug=True)