"""
Audit service for tracking system actions
"""
import logging
from datetime import datetime, timezone
from flask import request, session
from models import AuditLog
from app import db

logger = logging.getLogger(__name__)

def log_audit(action, details=None, user_id=None):
    """Log an audit event"""
    try:
        # Get IP and user agent from request context
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            user_agent = request.environ.get('HTTP_USER_AGENT', '')[:500]  # Truncate long user agents
        
        audit_log = AuditLog(
            action=action,
            details=details,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
        logger.info(f"Audit logged: {action} - User: {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to log audit event {action}: {e}")
        # Don't let audit failures break the application
        try:
            db.session.rollback()
        except:
            pass

def log_user_registered(user_id, username):
    """Log user registration"""
    log_audit("user_registered", f"New user registered: {username}", user_id)

def log_email_verification_sent(user_id, email):
    """Log verification email sent"""
    log_audit("email_verification_sent", f"Verification email sent to: {email}", user_id)

def log_email_verified(user_id, username):
    """Log email verification completed"""
    log_audit("email_verified", f"Email verified for user: {username}", user_id)

def log_email_verified_admin_override(user_id, admin_user_id, username):
    """Log admin override of email verification"""
    log_audit("email_verified_admin_override", f"Admin {admin_user_id} verified email for user: {username}", user_id)

def log_login_failed(username, reason):
    """Log failed login attempt"""
    log_audit("login_failed", f"Failed login for {username}: {reason}")

def log_login_rate_limited(username):
    """Log rate limited login"""
    log_audit("login_rate_limited", f"Rate limited login for {username}")

def log_login_success(user_id, username):
    """Log successful login"""
    log_audit("login_success", f"Successful login for user: {username}", user_id)

def log_quote_created(user_id, booking_id, pickup, destination):
    """Log quote request creation"""
    log_audit("quote_created", f"Quote created: {booking_id} from {pickup} to {destination}", user_id)

def log_quote_submitted_by_affiliate(affiliate_id, booking_id, price):
    """Log affiliate quote submission"""
    log_audit("quote_submitted_by_affiliate", f"Quote submitted for {booking_id}: ${price}", affiliate_id)

def log_quote_confirmed(user_id, booking_id, price):
    """Log quote confirmation by individual"""
    log_audit("quote_confirmed", f"Quote confirmed: {booking_id} for ${price}", user_id)

def log_email_sent(email_type, recipient, status):
    """Log email sending events"""
    log_audit(f"email_sent_{email_type}", f"Email to {recipient}: {status}")