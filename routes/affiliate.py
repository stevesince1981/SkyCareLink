from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import os
from services.email_service import email_service, EmailTemplates
from routes.auth import login_required, log_audit_event

affiliate_bp = Blueprint('affiliate', __name__, url_prefix='/affiliate')

def affiliate_required(f):
    """Decorator to require affiliate privileges"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'affiliate':
            flash('Affiliate access required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@affiliate_bp.route('/dashboard')
@login_required
@affiliate_required
def dashboard():
    # Get pending quotes (not yet responded to by this affiliate)
    from quote_app import Quote
    pending_quotes = Quote.query.filter_by(status='pending').order_by(Quote.created_at.desc()).all()
    
    # Get quotes this affiliate has responded to
    my_quotes = Quote.query.filter_by(affiliate_id=session['user_id']).order_by(Quote.created_at.desc()).all()
    
    return render_template('affiliate/dashboard.html', 
                         pending_quotes=pending_quotes, 
                         my_quotes=my_quotes)

@affiliate_bp.route('/quote/<int:quote_id>')
@login_required
@affiliate_required
def view_quote(quote_id):
    from quote_app import Quote
    quote = Quote.query.get_or_404(quote_id)
    
    # Allow viewing if quote is pending or if this affiliate already quoted it
    if quote.status != 'pending' and quote.affiliate_id != session['user_id']:
        flash('This quote is no longer available', 'error')
        return redirect(url_for('affiliate.dashboard'))
    
    return render_template('affiliate/quote_detail.html', quote=quote)

@affiliate_bp.route('/quote/<int:quote_id>/submit', methods=['POST'])
@login_required
@affiliate_required
def submit_quote(quote_id):
    from quote_app import db, Quote, User
    quote = Quote.query.get_or_404(quote_id)
    
    # Check if quote is still pending
    if quote.status != 'pending':
        flash('This quote is no longer available', 'error')
        return redirect(url_for('affiliate.dashboard'))
    
    # Get form data
    quoted_price_str = request.form.get('quoted_price', '').strip()
    quote_details = request.form.get('quote_details', '').strip()
    
    if not quoted_price_str:
        flash('Please enter a quoted price', 'error')
        return render_template('affiliate/quote_detail.html', quote=quote)
    
    try:
        quoted_price = float(quoted_price_str)
        if quoted_price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        flash('Please enter a valid price', 'error')
        return render_template('affiliate/quote_detail.html', quote=quote)
    
    # Update quote
    quote.affiliate_id = session['user_id']
    quote.quoted_price = quoted_price
    quote.quote_details = quote_details
    quote.status = 'quoted'
    quote.quoted_at = datetime.utcnow()
    
    db.session.commit()
    
    # Log quote submission
    log_audit_event('quote_submitted_by_affiliate', 
                   f'Quote submitted for {quote.reference_number}: ${quoted_price:,.2f}',
                   session['user_id'])
    
    # Send notification email to individual
    individual = User.query.get(quote.individual_id)
    if individual:
        portal_base = os.environ.get('PORTAL_BASE', 'http://localhost:5000')
        quote_ready_html = EmailTemplates.quote_ready_notification(
            quote.reference_number, quote.id, quoted_price, portal_base
        )
        
        email_service.send_email(
            individual.email,
            f'Your quote is ready – Ref #{quote.reference_number}',
            quote_ready_html,
            'quote_ready',
            quote.id
        )
    
    flash(f'Quote submitted successfully for ${quoted_price:,.2f}', 'success')
    return redirect(url_for('affiliate.dashboard'))

@affiliate_bp.route('/my-quotes')
@login_required
@affiliate_required
def my_quotes():
    from quote_app import Quote
    quotes = Quote.query.filter_by(affiliate_id=session['user_id']).order_by(Quote.created_at.desc()).all()
    return render_template('affiliate/my_quotes.html', quotes=quotes)