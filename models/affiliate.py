from datetime import datetime
from consumer_main_final import consumer_app as app, db

class Affiliate(db.Model):
    """Affiliate/Co-founder model with buy-in payment tracking"""
    __tablename__ = 'affiliates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Info
    company_name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    
    # Status
    is_active = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='pending')  # pending, verified, active, inactive
    
    # Buy-in Payment Tracking
    buy_in_required_total = db.Column(db.Numeric(10, 2), default=5000.00)  # Required amount
    buy_in_paid_total = db.Column(db.Numeric(10, 2), default=0.00)  # Amount paid so far
    buy_in_paid = db.Column(db.Boolean, default=False)  # Fully paid flag
    buy_in_paid_date = db.Column(db.DateTime)  # Date of full payment
    
    # Payment History (JSON field for tracking partial payments)
    payment_history = db.Column(db.Text)  # JSON string of payment records
    
    # Email Tracking
    verification_email_sent = db.Column(db.Boolean, default=False)
    verification_email_sent_date = db.Column(db.DateTime)
    welcome_email_sent = db.Column(db.Boolean, default=False)
    welcome_email_sent_date = db.Column(db.DateTime)
    
    # Terms Acceptance
    terms_understood_timestamp = db.Column(db.DateTime)  # "I understand" acceptance
    terms_version = db.Column(db.String(20), default='v1.0')
    
    # Call Center Settings
    day_phone = db.Column(db.String(20))
    after_hours_phone = db.Column(db.String(20))
    business_hours_start = db.Column(db.Integer, default=8)
    business_hours_end = db.Column(db.Integer, default=18)
    accepts_after_hours = db.Column(db.Boolean, default=False)
    accepts_level_1 = db.Column(db.Boolean, default=True)
    accepts_level_2 = db.Column(db.Boolean, default=True)
    accepts_level_3 = db.Column(db.Boolean, default=False)
    emergency_outreach = db.Column(db.Boolean, default=False)
    ground_transport_capable = db.Column(db.Boolean, default=False)
    coverage_radius = db.Column(db.Integer, default=150)
    coverage_regions = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Affiliate {self.company_name} - {self.email}>'
    
    @property
    def buy_in_remaining(self):
        """Calculate remaining buy-in amount"""
        return float(self.buy_in_required_total) - float(self.buy_in_paid_total)
    
    @property
    def buy_in_percent_complete(self):
        """Calculate percentage of buy-in completed"""
        if self.buy_in_required_total == 0:
            return 100
        return (float(self.buy_in_paid_total) / float(self.buy_in_required_total)) * 100
    
    def add_payment(self, amount, payment_method='manual', notes=''):
        """Add a partial payment and update totals"""
        import json
        
        # Update paid total
        self.buy_in_paid_total = float(self.buy_in_paid_total) + float(amount)
        
        # Check if fully paid
        if self.buy_in_paid_total >= self.buy_in_required_total:
            self.buy_in_paid = True
            if not self.buy_in_paid_date:
                self.buy_in_paid_date = datetime.utcnow()
        
        # Update payment history
        payment_record = {
            'amount': float(amount),
            'date': datetime.utcnow().isoformat(),
            'method': payment_method,
            'notes': notes
        }
        
        if self.payment_history:
            history = json.loads(self.payment_history)
        else:
            history = []
        
        history.append(payment_record)
        self.payment_history = json.dumps(history)
        
        self.updated_at = datetime.utcnow()
    
    def get_payment_history(self):
        """Get payment history as list of dicts"""
        import json
        
        if self.payment_history:
            return json.loads(self.payment_history)
        return []
    
    def can_send_welcome_email(self):
        """Check if welcome email can be sent (must be fully paid)"""
        return self.buy_in_paid and not self.welcome_email_sent
    
    def record_terms_acceptance(self):
        """Record terms acceptance timestamp (only once)"""
        if not self.terms_understood_timestamp:
            self.terms_understood_timestamp = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False