from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string

class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(String(20), nullable=False)  # 'individual', 'affiliate', 'admin'
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Rate limiting
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Relationships
    quotes_requested = relationship('Quote', foreign_keys='Quote.individual_id', back_populates='individual')
    quotes_responded = relationship('Quote', foreign_keys='Quote.affiliate_id', back_populates='affiliate')
    
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
    
    id = Column(Integer, primary_key=True)
    reference_number = Column(String(50), unique=True, nullable=False)
    individual_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    affiliate_id = Column(Integer, ForeignKey('users.id'))
    
    # Quote details
    pickup_location = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    transport_date = Column(DateTime, nullable=False)
    patient_condition = Column(Text)
    special_requirements = Column(Text)
    
    # Quote response
    quoted_price = Column(Float)
    quote_details = Column(Text)
    status = Column(String(20), default='pending')  # pending, quoted, confirmed, cancelled
    
    created_at = Column(DateTime, default=datetime.utcnow)
    quoted_at = Column(DateTime)
    confirmed_at = Column(DateTime)
    
    # Relationships
    individual = relationship('User', foreign_keys=[individual_id], back_populates='quotes_requested')
    affiliate = relationship('User', foreign_keys=[affiliate_id], back_populates='quotes_responded')
    
    @staticmethod
    def generate_reference():
        today = datetime.utcnow().strftime('%Y%m%d')
        # Get count of quotes today
        count = Quote.query.filter(Quote.reference_number.like(f'Q-{today}-%')).count() + 1
        return f'Q-{today}-{count:04d}'

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    template = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)  # SENT, FAILED
    smtp_response = Column(Text)
    error_message = Column(Text)
    
    # Related quote if applicable
    quote_id = Column(Integer, ForeignKey('quotes.id'))
    quote = relationship('Quote')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Related entities
    quote_id = Column(Integer, ForeignKey('quotes.id'))
    
    user = relationship('User')
    quote = relationship('Quote')