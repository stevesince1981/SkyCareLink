import os
import logging
from datetime import datetime
from flask import request, session
import json

logger = logging.getLogger(__name__)

class AuditLog:
    """Simple file-based audit logging system for sensitive actions"""
    
    AUDIT_FILE = 'data/audit_logs.json'
    
    @classmethod
    def _ensure_data_dir(cls):
        """Ensure data directory exists"""
        os.makedirs('data', exist_ok=True)
    
    @classmethod
    def _load_audit_logs(cls):
        """Load existing audit logs"""
        cls._ensure_data_dir()
        try:
            if os.path.exists(cls.AUDIT_FILE):
                with open(cls.AUDIT_FILE, 'r') as f:
                    return json.load(f)
            return {'logs': []}
        except Exception as e:
            logger.error(f"Error loading audit logs: {e}")
            return {'logs': []}
    
    @classmethod
    def _save_audit_logs(cls, logs):
        """Save audit logs to file"""
        cls._ensure_data_dir()
        try:
            with open(cls.AUDIT_FILE, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Error saving audit logs: {e}")
            return False
    
    @classmethod
    def log_event(cls, event_type, entity_type, entity_id, action, 
                  description=None, user_id=None, user_role=None, 
                  session_id=None, ip_address=None, user_agent=None,
                  old_values=None, new_values=None, request_id=None):
        """Log a sensitive action to the audit trail"""
        
        try:
            # Load existing logs
            logs_data = cls._load_audit_logs()
            
            # Create audit log entry
            audit_entry = {
                'id': len(logs_data['logs']) + 1,
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'entity_type': entity_type,
                'entity_id': str(entity_id),
                'action': action,
                'description': description or f"{action} on {entity_type} {entity_id}",
                'user_id': user_id,
                'user_role': user_role,
                'session_id': session_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'old_values': old_values,
                'new_values': new_values,
                'request_id': request_id
            }
            
            # Add to logs
            logs_data['logs'].append(audit_entry)
            
            # Keep only last 10000 entries to prevent file from growing too large
            if len(logs_data['logs']) > 10000:
                logs_data['logs'] = logs_data['logs'][-10000:]
            
            # Save logs
            success = cls._save_audit_logs(logs_data)
            
            if success:
                logger.info(f"Audit log created: {event_type} - {action} on {entity_type} {entity_id}")
            else:
                logger.error(f"Failed to save audit log for: {event_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            return False
    
    @classmethod
    def get_recent_logs(cls, limit=100, event_type=None):
        """Get recent audit logs with optional filtering"""
        try:
            logs_data = cls._load_audit_logs()
            logs = logs_data['logs']
            
            # Filter by event type if specified
            if event_type:
                logs = [log for log in logs if log.get('event_type') == event_type]
            
            # Sort by timestamp descending and limit
            logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return logs[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []
    
    @classmethod
    def get_entity_logs(cls, entity_type, entity_id, limit=50):
        """Get audit logs for a specific entity"""
        try:
            logs_data = cls._load_audit_logs()
            logs = logs_data['logs']
            
            # Filter by entity
            entity_logs = [
                log for log in logs 
                if log.get('entity_type') == entity_type and 
                   log.get('entity_id') == str(entity_id)
            ]
            
            # Sort by timestamp descending and limit
            entity_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return entity_logs[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving entity logs: {e}")
            return []


# Helper functions for common audit scenarios

def log_email_change(user_id, old_email, new_email):
    """Log email address change"""
    return AuditLog.log_event(
        event_type='email_change',
        entity_type='user',
        entity_id=user_id,
        action='email_updated',
        description=f'Email address changed from {old_email} to {new_email}',
        user_id=session.get('username'),
        user_role=session.get('user_role'),
        session_id=session.get('session_id'),
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get('User-Agent', '')[:500] if request else None,
        old_values={'email': old_email},
        new_values={'email': new_email}
    )

def log_role_change(user_id, old_role, new_role):
    """Log user role change"""
    return AuditLog.log_event(
        event_type='role_change',
        entity_type='user',
        entity_id=user_id,
        action='role_updated',
        description=f'User role changed from {old_role} to {new_role}',
        user_id=session.get('username'),
        user_role=session.get('user_role'),
        session_id=session.get('session_id'),
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get('User-Agent', '')[:500] if request else None,
        old_values={'role': old_role},
        new_values={'role': new_role}
    )

def log_affiliate_payment_action(affiliate_id, action, amount=None, payment_type=None):
    """Log affiliate payment related actions"""
    description = f'Affiliate payment {action}'
    if amount:
        description += f' - Amount: ${amount}'
    if payment_type:
        description += f' - Type: {payment_type}'
    
    return AuditLog.log_event(
        event_type='affiliate_payment',
        entity_type='affiliate',
        entity_id=affiliate_id,
        action=action,
        description=description,
        user_id=session.get('username'),
        user_role=session.get('user_role'),
        session_id=session.get('session_id'),
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get('User-Agent', '')[:500] if request else None,
        new_values={
            'amount': amount,
            'payment_type': payment_type
        }
    )

def log_quote_submit(quote_ref, quote_data):
    """Log quote submission"""
    return AuditLog.log_event(
        event_type='quote_submit',
        entity_type='quote',
        entity_id=quote_ref,
        action='submitted',
        description=f'Quote {quote_ref} submitted for {quote_data.get("service_type", "unknown")} service',
        user_id=session.get('username'),
        user_role=session.get('user_role'),
        session_id=session.get('session_id'),
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get('User-Agent', '')[:500] if request else None,
        new_values={
            'service_type': quote_data.get('service_type'),
            'severity_level': quote_data.get('severity_level'),
            'from_location': f"{quote_data.get('from_city', '')}, {quote_data.get('from_state', '')}",
            'to_location': f"{quote_data.get('to_city', '')}, {quote_data.get('to_state', '')}"
        }
    )

def log_booking_confirm(booking_ref, provider_name, amount):
    """Log booking confirmation"""
    return AuditLog.log_event(
        event_type='booking_confirm',
        entity_type='booking',
        entity_id=booking_ref,
        action='confirmed',
        description=f'Booking {booking_ref} confirmed with {provider_name} for ${amount}',
        user_id=session.get('username'),
        user_role=session.get('user_role'),
        session_id=session.get('session_id'),
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get('User-Agent', '')[:500] if request else None,
        new_values={
            'provider_name': provider_name,
            'amount': amount,
            'booking_status': 'confirmed'
        }
    )