from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
from services.email_service import email_service, EmailTemplates

auth_bp = Blueprint('auth', __name__)

def log_audit_event(action, details, user_id=None):
    """Helper function to log audit events"""
    try:
        from quote_app import db, AuditLog
        audit_log = AuditLog(
            action=action,
            details=details,
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        print(f"Failed to log audit event: {e}")
        try:
            from quote_app import db
            db.session.rollback()
        except:
            pass

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user_type = request.form.get('user_type', 'individual')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        from quote_app import db, User
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            email=email,
            user_type=user_type,
            is_verified=False
        )
        user.set_password(password)
        user.generate_verification_token()
        
        db.session.add(user)
        db.session.commit()
        
        # Log registration
        log_audit_event('user_registered', f'New {user_type} user registered: {email}', user.id)
        
        # Send verification email
        portal_base = os.environ.get('PORTAL_BASE', 'http://localhost:5000')
        email_html = EmailTemplates.verification_email(user.verification_token, portal_base)
        
        if email_service.send_email(
            email,
            'Verify your SkyCareLink account',
            email_html,
            'verification',
            quote_id=None
        ):
            log_audit_event('email_verification_sent', f'Verification email sent to {email}', user.id)
            flash('Registration successful! Please check your email to verify your account.', 'success')
        else:
            flash('Registration successful! However, we could not send the verification email. Please contact support.', 'warning')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/verify')
def verify():
    token = request.args.get('token')
    if not token:
        flash('Invalid verification link', 'error')
        return redirect(url_for('auth.login'))
    
    from quote_app import db, User
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash('Invalid or expired verification link', 'error')
        return redirect(url_for('auth.login'))
    
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    
    log_audit_event('email_verified', f'Email verified for user: {user.email}', user.id)
    
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
        from quote_app import db, User
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            if user:
                user.increment_failed_login()
                db.session.commit()
                log_audit_event('login_failed', f'Invalid password for user: {email}', user.id)
            else:
                log_audit_event('login_failed', f'Login attempt for non-existent user: {email}')
            
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html')
        
        # Check if account is locked
        if user.is_locked():
            log_audit_event('login_failed', f'Account locked for user: {email}', user.id)
            flash('Account temporarily locked due to too many failed attempts. Please try again in 5 minutes.', 'error')
            return render_template('auth/login.html')
        
        # Check if user is verified
        if not user.is_verified:
            log_audit_event('login_failed', f'Unverified user attempted login: {email}', user.id)
            flash('Please verify your email before logging in.', 'error')
            return render_template('auth/login.html', show_resend=True, user_email=email)
        
        # Successful login
        user.reset_failed_login()
        db.session.commit()
        
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_type'] = user.user_type
        
        log_audit_event('login_success', f'User logged in: {email}', user.id)
        
        # Redirect based on user type
        if user.user_type == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.user_type == 'affiliate':
            return redirect(url_for('affiliate.dashboard'))
        else:
            return redirect(url_for('quotes.request_quote'))
    
    return render_template('auth/login.html')

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    email = request.form.get('email', '').strip().lower()
    
    user = User.query.filter_by(email=email, is_verified=False).first()
    if not user:
        flash('No unverified account found with this email', 'error')
        return redirect(url_for('auth.login'))
    
    # Generate new token if needed
    if not user.verification_token:
        user.generate_verification_token()
        db.session.commit()
    
    # Send verification email
    portal_base = os.environ.get('PORTAL_BASE', 'http://localhost:5000')
    email_html = EmailTemplates.verification_email(user.verification_token, portal_base)
    
    if email_service.send_email(
        email,
        'Verify your SkyCareLink account',
        email_html,
        'verification_resend',
        quote_id=None
    ):
        log_audit_event('email_verification_sent', f'Verification email resent to {email}', user.id)
        flash('Verification email sent! Please check your inbox.', 'success')
    else:
        flash('Could not send verification email. Please try again later.', 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_audit_event('user_logout', 'User logged out', user_id)
    
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function