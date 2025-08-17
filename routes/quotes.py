from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import os
from services.email_service import email_service, EmailTemplates
from routes.auth import login_required, log_audit_event

quotes_bp = Blueprint('quotes', __name__)

@quotes_bp.route('/quote/request', methods=['GET', 'POST'])
@login_required
def request_quote():
    if request.method == 'POST':
        # Get form data
        pickup_location = request.form.get('pickup_location', '').strip()
        destination = request.form.get('destination', '').strip()
        transport_date_str = request.form.get('transport_date', '')
        patient_condition = request.form.get('patient_condition', '').strip()
        special_requirements = request.form.get('special_requirements', '').strip()
        
        # Validate required fields
        if not all([pickup_location, destination, transport_date_str]):
            flash('Please fill in all required fields', 'error')
            return render_template('quotes/request.html')
        
        try:
            transport_date = datetime.strptime(transport_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format', 'error')
            return render_template('quotes/request.html')
        
        # Create quote
        from quote_app import db, Quote
        quote = Quote(
            reference_number=Quote.generate_reference(),
            individual_id=session['user_id'],
            pickup_location=pickup_location,
            destination=destination,
            transport_date=transport_date,
            patient_condition=patient_condition,
            special_requirements=special_requirements
        )
        
        db.session.add(quote)
        db.session.commit()
        
        # Log quote creation
        log_audit_event('quote_created', 
                       f'Quote created: {quote.reference_number} from {pickup_location} to {destination}',
                       session['user_id'])
        
        # Send confirmation email to individual
        portal_base = os.environ.get('PORTAL_BASE', 'http://localhost:5000')
        individual_email = session['user_email']
        
        confirmation_html = EmailTemplates.quote_request_confirmation(
            quote.reference_number, quote.id, portal_base
        )
        
        email_service.send_email(
            individual_email,
            f'Quote request received – Ref #{quote.reference_number}',
            confirmation_html,
            'quote_confirmation',
            quote.id
        )
        
        # Send notification emails to all affiliates
        from quote_app import User
        affiliates = User.query.filter_by(user_type='affiliate', is_verified=True).all()
        for affiliate in affiliates:
            affiliate_html = EmailTemplates.affiliate_quote_request(
                quote.reference_number,
                quote.id,
                pickup_location,
                destination,
                transport_date.strftime('%Y-%m-%d'),
                portal_base
            )
            
            email_service.send_email(
                affiliate.email,
                f'New SkyCareLink quote – Ref #{quote.reference_number}',
                affiliate_html,
                'affiliate_quote_notification',
                quote.id
            )
        
        flash(f'Quote request submitted successfully! Reference: {quote.reference_number}', 'success')
        return redirect(url_for('quotes.quote_results', quote_id=quote.id))
    
    return render_template('quotes/request.html')

@quotes_bp.route('/quote/<int:quote_id>/results')
@login_required
def quote_results(quote_id):
    from quote_app import Quote
    quote = Quote.query.get_or_404(quote_id)
    
    # Only allow individual who created the quote to view it
    if quote.individual_id != session['user_id']:
        flash('You can only view your own quotes', 'error')
        return redirect(url_for('quotes.request_quote'))
    
    return render_template('quotes/results.html', quote=quote)

@quotes_bp.route('/quote/<int:quote_id>/confirm', methods=['POST'])
@login_required
def confirm_booking(quote_id):
    from quote_app import db, Quote, User
    quote = Quote.query.get_or_404(quote_id)
    
    # Only allow individual who created the quote to confirm it
    if quote.individual_id != session['user_id']:
        flash('You can only confirm your own quotes', 'error')
        return redirect(url_for('quotes.request_quote'))
    
    if quote.status != 'quoted':
        flash('This quote cannot be confirmed', 'error')
        return redirect(url_for('quotes.quote_results', quote_id=quote_id))
    
    # Update quote status
    quote.status = 'confirmed'
    quote.confirmed_at = datetime.utcnow()
    db.session.commit()
    
    # Log confirmation
    log_audit_event('quote_confirmed', 
                   f'Quote confirmed: {quote.reference_number}',
                   session['user_id'])
    
    # Send confirmation emails
    individual_email = session['user_email']
    affiliate = User.query.get(quote.affiliate_id)
    
    # Email to individual
    individual_html = EmailTemplates.booking_confirmed_individual(quote.reference_number)
    email_service.send_email(
        individual_email,
        f'Booking confirmed – Ref #{quote.reference_number}',
        individual_html,
        'booking_confirmed_individual',
        quote.id
    )
    
    # Email to affiliate
    if affiliate:
        affiliate_html = EmailTemplates.booking_confirmed_affiliate(quote.reference_number)
        email_service.send_email(
            affiliate.email,
            f'Quote accepted – Ref #{quote.reference_number}',
            affiliate_html,
            'booking_confirmed_affiliate',
            quote.id
        )
    
    flash('Booking confirmed successfully! You will be contacted shortly.', 'success')
    return redirect(url_for('quotes.quote_results', quote_id=quote_id))

@quotes_bp.route('/my-quotes')
@login_required
def my_quotes():
    from quote_app import Quote
    quotes = Quote.query.filter_by(individual_id=session['user_id']).order_by(Quote.created_at.desc()).all()
    return render_template('quotes/my_quotes.html', quotes=quotes)