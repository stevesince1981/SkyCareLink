from datetime import datetime
from consumer_main_final import consumer_app as app, db

class AuditLog(db.Model):
    """System audit log for tracking actions and changes"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Event information
    event_type = db.Column(db.String(50), nullable=False, index=True)  # document_upload, payment_added, etc.
    entity_type = db.Column(db.String(50), nullable=False)  # quote, affiliate, document, etc.
    entity_id = db.Column(db.String(100), nullable=False, index=True)  # ID or reference
    
    # Action details
    action = db.Column(db.String(100), nullable=False)  # created, updated, deleted, uploaded, etc.
    description = db.Column(db.Text)  # Human-readable description
    
    # User and session information
    user_id = db.Column(db.String(100))
    user_role = db.Column(db.String(50))
    session_id = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    
    # Change data
    old_values = db.Column(db.Text)  # JSON string of old values
    new_values = db.Column(db.Text)  # JSON string of new values
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    request_id = db.Column(db.String(100))  # For tracing requests
    
    def __repr__(self):
        return f'<AuditLog {self.event_type}:{self.action} for {self.entity_type}:{self.entity_id}>'
    
    @staticmethod
    def log_event(event_type, entity_type, entity_id, action, description=None, 
                  user_id=None, user_role=None, old_values=None, new_values=None,
                  ip_address=None, user_agent=None, session_id=None, request_id=None):
        """Create an audit log entry"""
        import json
        
        audit_entry = AuditLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            description=description,
            user_id=user_id,
            user_role=user_role,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None
        )
        
        db.session.add(audit_entry)
        return audit_entry
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        import json
        
        return {
            'id': self.id,
            'event_type': self.event_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'action': self.action,
            'description': self.description,
            'user_id': self.user_id,
            'user_role': self.user_role,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'request_id': self.request_id,
            'old_values': json.loads(self.old_values) if self.old_values else None,
            'new_values': json.loads(self.new_values) if self.new_values else None
        }