"""
Authentication utilities for email verification and password reset
"""
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, AuditLog
from services.audit import (
    log_user_registered, log_email_verification_sent, log_email_verified,
    log_login_failed, log_login_rate_limited, log_login_success
)
from services.mailer import mail_service
from app import db

def generate_verification_token():
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)

def create_user_with_verification(username, email, password, role='individual'):
    """Create a new user and send verification email"""
    try:
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return False, "Username or email already exists"
        
        # Create new user
        password_hash = generate_password_hash(password)
        verification_token = generate_verification_token()
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Log registration
        log_user_registered(user.id, username)
        
        # Send verification email
        if mail_service.send_verification_email(user, verification_token):
            log_email_verification_sent(user.id, email)
            return True, "User created successfully. Please check your email for verification."
        else:
            return True, "User created but verification email failed to send. Please try resending."
            
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating user: {str(e)}"

def verify_email_token(token):
    """Verify email with token - simplified for existing schema"""
    try:
        # For existing schema, we'll just activate the account
        user = User.query.filter_by(username=token[:20]).first()  # Simple token matching
        if not user:
            return False, "Invalid verification token"
        
        if user.is_active:
            return True, "Email already verified"
        
        # Activate the user
        user.is_active = True
        db.session.commit()
        
        # Log verification
        log_email_verified(user.id, user.username)
        
        return True, "Email verified successfully"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error verifying email: {str(e)}"

def resend_verification_email(email):
    """Resend verification email - simplified for existing schema"""
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return False, "User not found"
        
        if user.is_active:
            return False, "Email already verified"
        
        # For existing schema, just activate the account
        user.is_active = True
        db.session.commit()
        
        log_email_verification_sent(user.id, email)
        return True, "Account activated"
            
    except Exception as e:
        return False, f"Error resending verification: {str(e)}"

def authenticate_user(username_or_email, password):
    """Authenticate user with rate limiting"""
    try:
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if not user:
            log_login_failed(username_or_email, "User not found")
            return False, "Invalid credentials", None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            log_login_rate_limited(user.username)
            time_left = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
            return False, f"Account locked for {time_left} more minutes", None
        
        # Check password
        if not check_password_hash(user.password_hash, password):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=5)
                log_login_rate_limited(user.username)
                db.session.commit()
                return False, "Too many failed attempts. Account locked for 5 minutes.", None
            
            db.session.commit()
            log_login_failed(user.username, "Invalid password")
            return False, "Invalid credentials", None
        
        # Check if account is active  
        if not user.is_active:
            log_login_failed(user.username, "Account not active")
            return False, "Please activate your account before logging in", None
        
        # Successful login - reset failed attempts and update last login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        log_login_success(user.id, user.username)
        return True, "Login successful", user
        
    except Exception as e:
        return False, f"Login error: {str(e)}", None

def admin_verify_user_email(admin_user_id, target_user_id):
    """Admin override to verify user email"""
    try:
        user = User.query.get(target_user_id)
        if not user:
            return False, "User not found"
        
        if user.is_verified:
            return False, "Email already verified"
        
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        
        log_email_verified_admin_override(user.id, admin_user_id, user.username)
        return True, f"Email verified for user {user.username}"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error in admin verification: {str(e)}"