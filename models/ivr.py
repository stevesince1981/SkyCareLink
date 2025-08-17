"""
IVR Call Record Model
Stores call logs and state for Twilio voice interactions
"""

from datetime import datetime
from app import db

class IVRCall(db.Model):
    """Model for tracking IVR call sessions"""
    __tablename__ = 'ivr_calls'
    
    id = db.Column(db.Integer, primary_key=True)
    call_sid = db.Column(db.String(64), unique=True, nullable=True)  # Twilio Call SID
    phone_number = db.Column(db.String(20), nullable=False)  # Caller's number (last 4 digits for privacy)
    session_id = db.Column(db.String(64), nullable=False, unique=True)  # Internal session ID
    
    # Call metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='started')  # started, in_progress, completed, failed
    
    # Collected information
    transport_date = db.Column(db.String(100), nullable=True)  # Raw speech input
    origin_location = db.Column(db.String(200), nullable=True)  # Raw speech input
    destination_location = db.Column(db.String(200), nullable=True)  # Raw speech input
    severity_level = db.Column(db.Integer, nullable=True)  # 1, 2, or 3
    ground_transport_needed = db.Column(db.Boolean, nullable=True)
    
    # Provider connection attempts
    providers_attempted = db.Column(db.Integer, nullable=False, default=0)
    providers_contacted = db.Column(db.Text, nullable=True)  # JSON list of provider IDs
    final_provider_id = db.Column(db.Integer, nullable=True)  # ID of accepting provider
    
    # Outcome
    outcome = db.Column(db.String(50), nullable=True)  # connected, fallback_ticket, support_transfer, abandoned
    fallback_quote_id = db.Column(db.String(50), nullable=True)  # Reference to auto-generated quote
    
    # Raw call log for debugging
    call_log = db.Column(db.Text, nullable=True)  # JSON log of all call events
    
    def __repr__(self):
        return f'<IVRCall {self.session_id}: {self.phone_number} - {self.status}>'
    
    def add_log_entry(self, step, data=None):
        """Add an entry to the call log"""
        import json
        
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'step': step,
            'data': data or {}
        }
        
        if self.call_log:
            log_data = json.loads(self.call_log)
            log_data.append(entry)
        else:
            log_data = [entry]
        
        self.call_log = json.dumps(log_data)
        self.updated_at = datetime.utcnow()
    
    def get_log_entries(self):
        """Get all log entries as a list"""
        import json
        if self.call_log:
            return json.loads(self.call_log)
        return []
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'phone_number': self.phone_number,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'transport_date': self.transport_date,
            'origin_location': self.origin_location,
            'destination_location': self.destination_location,
            'severity_level': self.severity_level,
            'ground_transport_needed': self.ground_transport_needed,
            'providers_attempted': self.providers_attempted,
            'outcome': self.outcome,
            'fallback_quote_id': self.fallback_quote_id
        }

class IVRProviderAttempt(db.Model):
    """Model for tracking individual provider connection attempts during IVR calls"""
    __tablename__ = 'ivr_provider_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    ivr_call_id = db.Column(db.Integer, db.ForeignKey('ivr_calls.id'), nullable=False)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliate.id'), nullable=True)
    
    # Attempt details
    attempted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    phone_number = db.Column(db.String(20), nullable=True)  # Provider's phone number used
    call_duration = db.Column(db.Integer, nullable=True)  # Duration in seconds
    
    # Response
    response = db.Column(db.String(20), nullable=True)  # accepted, declined, no_response
    response_time = db.Column(db.Integer, nullable=True)  # Time to respond in seconds
    
    # Twilio call details
    provider_call_sid = db.Column(db.String(64), nullable=True)
    call_status = db.Column(db.String(20), nullable=True)
    
    # Relationships
    ivr_call = db.relationship('IVRCall', backref=db.backref('provider_attempts', lazy=True))
    affiliate = db.relationship('Affiliate', backref=db.backref('ivr_attempts', lazy=True))
    
    def __repr__(self):
        return f'<IVRProviderAttempt {self.id}: Call {self.ivr_call_id} -> Affiliate {self.affiliate_id} - {self.response}>'