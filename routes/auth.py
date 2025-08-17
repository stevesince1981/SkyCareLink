import os
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import logging

from models.audit import AuditLog
from services.mailer import email_service

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Password reset token storage (in production, use Redis or database)
password_reset_tokens = {}

def generate_reset_token():
    """Generate a secure password reset token"""
    return secrets.token_urlsafe(32)

def hash_token(token):
    """Hash token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def is_token_valid(token, email):
    """Check if password reset token is valid"""
    token_hash = hash_token(token)
    if token_hash not in password_reset_tokens:
        return False
    
    stored_data = password_reset_tokens[token_hash]
    if stored_data['email'] != email:
        return False
    
    # Check expiration (2 hours)
    expiry = datetime.fromisoformat(stored_data['expires'])
    if datetime.now() > expiry:
        # Clean up expired token
        del password_reset_tokens[token_hash]
        return False
    
    return True

def cleanup_expired_tokens():
    """Remove expired tokens from storage"""
    current_time = datetime.now()
    expired_tokens = []
    
    for token_hash, data in password_reset_tokens.items():
        expiry = datetime.fromisoformat(data['expires'])
        if current_time > expiry:
            expired_tokens.append(token_hash)
    
    for token_hash in expired_tokens:
        del password_reset_tokens[token_hash]

@auth_bp.route('/password-reset', methods=['GET', 'POST'])
def password_reset_request():
    """Password reset request form"""
    if request.method == 'GET':
        return render_template('auth/password_reset_request.html')
    
    # Handle POST request
    email = request.form.get('email', '').strip().lower()
    
    if not email:
        flash('Please enter your email address.', 'error')
        return render_template('auth/password_reset_request.html')
    
    # In production, verify email exists in database
    # For demo, accept any email that looks like a demo account
    valid_emails = ['admin@demo.com', 'family@demo.com', 'hospital@demo.com', 'affiliate@demo.com']
    
    if email not in valid_emails and not email.endswith('@demo.com'):
        flash('If an account exists with that email, a reset link has been sent.', 'info')
        return redirect(url_for('auth.password_reset_request'))
    
    try:
        # Generate reset token
        reset_token = generate_reset_token()
        token_hash = hash_token(reset_token)
        
        # Store token with expiration
        expiry = datetime.now() + timedelta(hours=2)
        password_reset_tokens[token_hash] = {
            'email': email,
            'expires': expiry.isoformat(),
            'created': datetime.now().isoformat()
        }
        
        # Generate reset URL
        reset_url = url_for('auth.password_reset_verify', token=reset_token, email=email, _external=True)
        
        # Send reset email
        success = email_service.send_password_reset_email(email, reset_url, expiry)
        
        if success:
            # Log the reset request
            AuditLog.log_event(
                event_type='password_reset_request',
                entity_type='user',
                entity_id=email,
                action='requested',
                description=f'Password reset requested for {email}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500]
            )
            
            flash('If an account exists with that email, a reset link has been sent.', 'info')
            logger.info(f"Password reset email sent to {email}")
        else:
            flash('Error sending reset email. Please try again later.', 'error')
            logger.error(f"Failed to send password reset email to {email}")
        
    except Exception as e:
        logger.error(f"Password reset request error for {email}: {str(e)}")
        flash('Error processing reset request. Please try again later.', 'error')
    
    return redirect(url_for('auth.password_reset_request'))

@auth_bp.route('/password-reset/verify')
def password_reset_verify():
    """Verify reset token and show reset form"""
    token = request.args.get('token')
    email = request.args.get('email')
    
    if not token or not email:
        flash('Invalid reset link.', 'error')
        return redirect(url_for('auth.password_reset_request'))
    
    # Clean up expired tokens
    cleanup_expired_tokens()
    
    # Verify token
    if not is_token_valid(token, email):
        flash('Reset link has expired or is invalid. Please request a new one.', 'error')
        return redirect(url_for('auth.password_reset_request'))
    
    return render_template('auth/password_reset_form.html', token=token, email=email)

@auth_bp.route('/password-reset/confirm', methods=['POST'])
def password_reset_confirm():
    """Process password reset with new password"""
    token = request.form.get('token')
    email = request.form.get('email')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([token, email, new_password, confirm_password]):
        flash('All fields are required.', 'error')
        return render_template('auth/password_reset_form.html', token=token, email=email)
    
    if new_password != confirm_password:
        flash('Passwords do not match.', 'error')
        return render_template('auth/password_reset_form.html', token=token, email=email)
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return render_template('auth/password_reset_form.html', token=token, email=email)
    
    # Clean up expired tokens
    cleanup_expired_tokens()
    
    # Verify token one more time
    if not is_token_valid(token, email):
        flash('Reset link has expired or is invalid.', 'error')
        return redirect(url_for('auth.password_reset_request'))
    
    try:
        # In production, update password in database
        # For demo, we'll simulate the password update
        password_hash = generate_password_hash(new_password)
        
        # Remove used token
        token_hash = hash_token(token)
        if token_hash in password_reset_tokens:
            del password_reset_tokens[token_hash]
        
        # Send confirmation email
        email_service.send_password_reset_confirmation(email)
        
        # Log the password reset completion
        AuditLog.log_event(
            event_type='password_reset',
            entity_type='user',
            entity_id=email,
            action='completed',
            description=f'Password reset completed for {email}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500],
            new_values={'password_changed': True, 'reset_method': 'email_token'}
        )
        
        flash('Your password has been reset successfully. You can now log in with your new password.', 'success')
        logger.info(f"Password reset completed for {email}")
        
        return redirect('/')
        
    except Exception as e:
        logger.error(f"Password reset confirmation error for {email}: {str(e)}")
        flash('Error resetting password. Please try again.', 'error')
        return render_template('auth/password_reset_form.html', token=token, email=email)

@auth_bp.route('/audit-test')
def audit_test():
    """Test endpoint to demonstrate audit logging"""
    try:
        # Log a test audit event
        AuditLog.log_event(
            event_type='system_test',
            entity_type='audit',
            entity_id='test_audit_001',
            action='test_performed',
            description='Audit logging system test',
            user_id=session.get('username', 'anonymous'),
            user_role=session.get('user_role', 'unknown'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500],
            new_values={'test_data': True, 'timestamp': datetime.now().isoformat()}
        )
        
        return jsonify({
            'success': True,
            'message': 'Audit event logged successfully',
            'event_id': 'test_audit_001'
        })
        
    except Exception as e:
        logger.error(f"Audit test error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Helper function to log sensitive actions
def log_sensitive_action(event_type, entity_type, entity_id, action, description=None, old_values=None, new_values=None):
    """Helper function to log sensitive actions with consistent format"""
    try:
        AuditLog.log_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            description=description,
            user_id=session.get('username'),
            user_role=session.get('user_role'),
            session_id=session.get('session_id'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500],
            old_values=old_values,
            new_values=new_values,
            request_id=request.headers.get('X-Request-ID')
        )
        return True
    except Exception as e:
        logger.error(f"Failed to log sensitive action: {str(e)}")
        return False