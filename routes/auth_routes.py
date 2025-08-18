"""
Authentication routes for email verification and login
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from services.auth_utils import (
    create_user_with_verification, verify_email_token, 
    resend_verification_email, authenticate_user
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration with email verification"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        role = request.form.get('role', 'individual')  # individual, affiliate, admin
        
        # Basic validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('unified_registration.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('unified_registration.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('unified_registration.html')
        
        # Create user with verification
        success, message = create_user_with_verification(username, email, password, role)
        
        if success:
            flash(message, 'success')
            return render_template('registration_success.html', email=email)
        else:
            flash(message, 'error')
            return render_template('unified_registration.html')
    
    return render_template('unified_registration.html')

@auth_bp.route('/verify')
def verify_email():
    """Handle email verification"""
    token = request.args.get('token')
    if not token:
        flash('Invalid verification link', 'error')
        return redirect(url_for('auth.login'))
    
    success, message = verify_email_token(token)
    
    if success:
        flash(message, 'success')
        return redirect(url_for('auth.login'))
    else:
        flash(message, 'error')
        return redirect(url_for('auth.register'))

@auth_bp.route('/resend_verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    email = request.form.get('email', '').strip()
    if not email:
        flash('Email address is required', 'error')
        return redirect(url_for('auth.login'))
    
    success, message = resend_verification_email(email)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not all([username_or_email, password]):
            flash('Username/email and password are required', 'error')
            return render_template('login.html')
        
        success, message, user = authenticate_user(username_or_email, password)
        
        if success:
            # Set session
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_type'] = user.role
            session['email'] = user.email
            
            # Redirect based on user type
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'affiliate':
                return redirect(url_for('affiliate.dashboard'))
            else:
                # Check for post-login action
                post_login_action = session.pop('postLoginAction', None)
                if post_login_action == 'requestQuote':
                    return redirect(url_for('consumer_intake_authenticated'))
                return redirect(url_for('home'))
        else:
            flash(message, 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('consumer.home'))