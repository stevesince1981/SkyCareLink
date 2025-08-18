"""
Quote workflow routes for individuals and affiliates
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timezone, timedelta
from models import QuoteRequest, User
from services.mailer import mail_service
from services.audit import log_quote_created, log_quote_submitted_by_affiliate, log_quote_confirmed
from app import db

quote_bp = Blueprint('quote', __name__)

def generate_booking_id():
    """Generate unique booking ID in format BKYYYYMMDDHHMMSS"""
    now = datetime.now(timezone.utc)
    return f"BK{now.strftime('%Y%m%d%H%M%S')}"

@quote_bp.route('/submit_quote', methods=['POST'])
def submit_quote():
    """Handle quote submission from individuals (from existing intake form)"""
    try:
        # Check if user is logged in
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to submit a quote request', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(user_id)
        if not user or not user.is_verified:
            flash('Please verify your email before submitting quotes', 'error')
            return redirect(url_for('auth.login'))
        
        # Get form data (adapting to existing intake form fields)
        pickup_location = f"{request.form.get('from_city', '')}, {request.form.get('from_state', '')}"
        destination = f"{request.form.get('to_city', '')}, {request.form.get('to_state', '')}"
        
        # Parse transport date
        flight_date_str = request.form.get('flight_date', '')
        if not flight_date_str:
            flash('Transport date is required', 'error')
            return redirect(request.referrer or url_for('consumer.intake'))
        
        transport_date = datetime.strptime(flight_date_str, '%Y-%m-%d')
        
        # Generate booking ID
        booking_id = generate_booking_id()
        
        # Create quote request
        quote_request = QuoteRequest(
            booking_id=booking_id,
            individual_id=user.id,
            pickup_location=pickup_location,
            destination=destination,
            transport_date=transport_date,
            patient_condition=request.form.get('specialized_care'),
            special_requirements=request.form.get('additional_medical_info'),
            status='incoming',
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(quote_request)
        db.session.commit()
        
        # Log the quote creation
        log_quote_created(user.id, booking_id, pickup_location, destination)
        
        # Send confirmation email to individual
        mail_service.send_quote_request_confirmation(user, quote_request)
        
        # Send notification to test affiliates (for now, just admin users with affiliate type)
        affiliate_users = User.query.filter_by(user_type='affiliate', is_verified=True).all()
        for affiliate_user in affiliate_users[:3]:  # Limit to first 3 affiliates for testing
            mail_service.send_new_quote_notification(affiliate_user, quote_request)
        
        flash(f'Quote request submitted successfully! Reference: {booking_id}', 'success')
        return redirect(url_for('quote.quote_results', booking_id=booking_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting quote: {str(e)}', 'error')
        return redirect(request.referrer or url_for('consumer.intake'))

@quote_bp.route('/quote_results/<booking_id>')
def quote_results(booking_id):
    """Show quote results to individual"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view quote results', 'error')
        return redirect(url_for('auth.login'))
    
    quote_request = QuoteRequest.query.filter_by(booking_id=booking_id, individual_id=user_id).first()
    if not quote_request:
        flash('Quote request not found', 'error')
        return redirect(url_for('consumer.home'))
    
    return render_template('consumer_templates/quote_results.html', quote=quote_request)

@quote_bp.route('/affiliate/quote/<booking_id>')
def affiliate_quote_form(booking_id):
    """Show quote form to affiliate"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to provide quotes', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user or user.user_type != 'affiliate':
        flash('Access denied. Affiliate account required.', 'error')
        return redirect(url_for('consumer.home'))
    
    quote_request = QuoteRequest.query.filter_by(booking_id=booking_id).first()
    if not quote_request:
        flash('Quote request not found', 'error')
        return redirect(url_for('consumer.home'))
    
    if quote_request.status != 'incoming':
        flash('This quote request has already been processed', 'error')
        return redirect(url_for('consumer.home'))
    
    return render_template('affiliate_templates/provide_quote.html', quote=quote_request)

@quote_bp.route('/affiliate/submit_quote/<booking_id>', methods=['POST'])
def affiliate_submit_quote(booking_id):
    """Handle affiliate quote submission"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        user = User.query.get(user_id)
        if not user or user.user_type != 'affiliate':
            return jsonify({'success': False, 'message': 'Access denied'})
        
        quote_request = QuoteRequest.query.filter_by(booking_id=booking_id).first()
        if not quote_request:
            return jsonify({'success': False, 'message': 'Quote request not found'})
        
        if quote_request.status != 'incoming':
            return jsonify({'success': False, 'message': 'Quote already processed'})
        
        # Get quote details
        quoted_price = float(request.form.get('quoted_price', 0))
        ground_included = request.form.get('ground_included') == 'on'
        notes = request.form.get('notes', '').strip()
        
        if quoted_price <= 0:
            return jsonify({'success': False, 'message': 'Please enter a valid price'})
        
        # Update quote request
        quote_request.affiliate_id = user.id
        quote_request.quoted_price = quoted_price
        quote_request.quote_details = {
            'ground_included': ground_included,
            'notes': notes,
            'affiliate_company': user.username
        }
        quote_request.status = 'submitted'
        quote_request.quoted_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        # Log the quote submission
        log_quote_submitted_by_affiliate(user.id, booking_id, quoted_price)
        
        # Send notification to individual
        individual = User.query.get(quote_request.individual_id)
        if individual:
            mail_service.send_quote_ready_notification(individual, quote_request)
        
        return jsonify({'success': True, 'message': 'Quote submitted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@quote_bp.route('/confirm_booking/<booking_id>', methods=['POST'])
def confirm_booking(booking_id):
    """Handle booking confirmation by individual"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Please log in'})
        
        quote_request = QuoteRequest.query.filter_by(booking_id=booking_id, individual_id=user_id).first()
        if not quote_request:
            return jsonify({'success': False, 'message': 'Quote request not found'})
        
        if quote_request.status != 'submitted':
            return jsonify({'success': False, 'message': 'Quote not ready for confirmation'})
        
        # Confirm the booking
        quote_request.status = 'confirmed'
        quote_request.confirmed_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        # Log the confirmation
        log_quote_confirmed(user_id, booking_id, quote_request.quoted_price)
        
        # Send confirmation emails
        individual = User.query.get(user_id)
        affiliate = User.query.get(quote_request.affiliate_id) if quote_request.affiliate_id else None
        
        if individual:
            mail_service.send_booking_confirmation(individual, quote_request)
        
        if affiliate:
            mail_service.send_quote_accepted_notification(affiliate, quote_request)
        
        return jsonify({'success': True, 'message': 'Booking confirmed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@quote_bp.route('/admin/email_log')
def admin_email_log():
    """Admin view for email logs"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user or user.user_type != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('consumer.home'))
    
    from models import EmailLog
    from services.mailer import mail_service
    email_logs = EmailLog.query.order_by(EmailLog.created_at.desc()).limit(100).all()
    
    return render_template('admin_templates/email_log.html', 
                         email_logs=email_logs, 
                         mail_disabled=not mail_service.enabled)