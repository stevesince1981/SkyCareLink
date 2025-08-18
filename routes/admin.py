from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from routes.auth import login_required, admin_required, log_audit_event
from services.email_service import email_service

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get summary statistics
    from quote_app import User, Quote
    total_users = User.query.count()
    pending_users = User.query.filter_by(is_verified=False).count()
    total_quotes = Quote.query.count()
    pending_quotes = Quote.query.filter_by(status='pending').count()
    confirmed_bookings = Quote.query.filter_by(status='confirmed').count()
    
    # Recent activity
    recent_quotes = Quote.query.order_by(Quote.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Email status check
    email_enabled = email_service.is_enabled()
    
    return render_template('consumer_admin_dashboard.html',
                         session_data=session)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    from quote_app import User
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:user_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_user(user_id):
    from quote_app import db, User
    user = User.query.get_or_404(user_id)
    
    if user.is_verified:
        flash('User is already verified', 'info')
    else:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        
        log_audit_event('admin_verified_user', 
                       f'Admin manually verified user: {user.email}',
                       session['user_id'])
        
        flash(f'User {user.email} has been verified', 'success')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/quotes')
@login_required
@admin_required
def quotes():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    from quote_app import Quote
    quotes = Quote.query.order_by(Quote.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/quotes.html', quotes=quotes)

@admin_bp.route('/email-log')
@login_required
@admin_required
def email_log():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    from quote_app import EmailLog
    email_logs = EmailLog.query.order_by(EmailLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/email_log.html', email_logs=email_logs)

@admin_bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    from quote_app import AuditLog
    audit_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/audit_log.html', audit_logs=audit_logs)

@admin_bp.route('/email-status')
@login_required
@admin_required
def email_status():
    """API endpoint to check email service status"""
    return {
        'enabled': email_service.is_enabled(),
        'config_check': email_service._check_config()
    }