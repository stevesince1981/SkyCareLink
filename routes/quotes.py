"""
Quote routes for handling quote requests and results
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, session
import logging
from datetime import datetime
import uuid

from models import db, Quote
from routes.affiliate import send_affiliate_quote_request
from services.mailer import email_service
from services.sms import sms_service

logger = logging.getLogger(__name__)

quotes_bp = Blueprint('quotes', __name__, url_prefix='/quotes')

@quotes_bp.route('/submit', methods=['POST'])
def submit_quote_request():
    """Handle quote request submission and send to affiliate"""
    try:
        # Extract form data (this integrates with the existing intake form)
        contact_name = request.form.get('contact_name', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        
        if not contact_name:
            flash('Contact name is required.', 'error')
            return redirect(url_for('intake_pancake'))
        
        # Generate reference number
        ref_id = f"QR{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        # Create quote record
        quote = Quote(
            ref_id=ref_id,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            relation_to_patient=request.form.get('relation_to_patient', ''),
            service_type=request.form.get('service_type', ''),
            severity_level=request.form.get('severity_level', ''),
            flight_date=datetime.strptime(request.form.get('flight_date'), '%Y-%m-%d') if request.form.get('flight_date') else None,
            return_date=datetime.strptime(request.form.get('return_date'), '%Y-%m-%d') if request.form.get('return_date') else None,
            return_flight_needed=bool(request.form.get('return_flight')),
            from_hospital=request.form.get('from_hospital', ''),
            from_address=request.form.get('from_address', ''),
            from_city=request.form.get('from_city', ''),
            from_state=request.form.get('from_state', ''),
            to_hospital=request.form.get('to_hospital', ''),
            to_address=request.form.get('to_address', ''),
            to_city=request.form.get('to_city', ''),
            to_state=request.form.get('to_state', ''),
            preferred_time=request.form.get('preferred_time', ''),
            family_seats=int(request.form.get('family_seats', 0)),
            patient_gender=request.form.get('patient_gender', ''),
            patient_age_range=request.form.get('patient_age_range', ''),
            patient_weight=request.form.get('patient_weight', ''),
            covid_tested=request.form.get('covid_tested', ''),
            covid_result=request.form.get('covid_result', ''),
            additional_info=request.form.get('additional_info', ''),
            quote_status='pending',
            created_at=datetime.utcnow()
        )
        
        # Handle medical equipment (stored as JSON)
        equipment_list = []
        for key, value in request.form.items():
            if key.startswith('eq_') and value == 'on':
                equipment_id = key[3:]  # Remove 'eq_' prefix
                equipment_list.append(equipment_id)
        
        quote.medical_equipment = equipment_list
        
        # Set equipment flags based on selections
        quote.oxygen_required = 'oxygen' in equipment_list
        quote.cardiac_monitor_required = 'cardiac_monitor' in equipment_list
        quote.stretcher_required = 'stretcher' in equipment_list
        quote.iv_pump_required = 'iv_pump' in equipment_list
        quote.defibrillator_required = 'defibrillator' in equipment_list
        quote.ventilator_required = 'ventilator' in equipment_list
        quote.balloon_pump_required = 'balloon_pump' in equipment_list
        quote.ecmo_required = 'ecmo' in equipment_list
        quote.suction_required = 'suction' in equipment_list
        quote.incubator_required = 'incubator' in equipment_list
        
        db.session.add(quote)
        db.session.commit()
        
        # Send notification to affiliate
        send_affiliate_quote_request(quote)
        
        logger.info(f"Quote request submitted: {ref_id}")
        
        # Store reference for results page
        session['quote_reference'] = ref_id
        
        flash(f'Quote request submitted successfully! Reference: {ref_id}', 'success')
        return redirect(url_for('quotes.quote_submitted', ref=ref_id))
    
    except Exception as e:
        logger.error(f"Error submitting quote request: {str(e)}")
        db.session.rollback()
        flash('An error occurred while submitting your quote request. Please try again.', 'error')
        return redirect(url_for('intake_pancake'))

@quotes_bp.route('/submitted/<ref>')
def quote_submitted(ref):
    """Quote submission confirmation page"""
    quote = Quote.query.filter_by(ref_id=ref).first()
    
    if not quote:
        flash('Quote reference not found.', 'error')
        return redirect(url_for('consumer_home'))
    
    return render_template('quote_submitted.html', quote=quote)

@quotes_bp.route('/results/<ref>')
def quote_results(ref):
    """Display quote results and booking options"""
    quote = Quote.query.filter_by(ref_id=ref).first()
    
    if not quote:
        flash('Quote reference not found.', 'error')
        return redirect(url_for('consumer_home'))
    
    # Determine page content based on quote status
    if quote.quote_status == 'pending':
        return render_template('quote_pending.html', quote=quote)
    elif quote.quote_status == 'quoted':
        return render_template('quote_ready.html', quote=quote)
    elif quote.quote_status == 'booked':
        return render_template('booking_confirmed.html', quote=quote)
    elif quote.quote_status == 'expired':
        return render_template('quote_expired.html', quote=quote)
    else:
        return render_template('quote_error.html', quote=quote)

@quotes_bp.route('/book/<ref>', methods=['POST'])
def book_quote(ref):
    """Handle quote booking confirmation"""
    try:
        quote = Quote.query.filter_by(ref_id=ref).first()
        
        if not quote:
            return jsonify({'success': False, 'message': 'Quote not found'}), 404
        
        if quote.quote_status != 'quoted':
            return jsonify({'success': False, 'message': 'Quote is not available for booking'}), 400
        
        # Check if quote has expired
        if quote.quote_expires_at and datetime.utcnow() > quote.quote_expires_at:
            quote.quote_status = 'expired'
            db.session.commit()
            return jsonify({'success': False, 'message': 'Quote has expired'}), 400
        
        # Update quote status to booked
        quote.quote_status = 'booked'
        quote.booking_confirmed_at = datetime.utcnow()
        quote.booking_reference = f"BK{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        db.session.commit()
        
        # Send booking confirmation notifications (imported from affiliate routes)
        from routes.affiliate import send_booking_confirmed_notifications
        send_booking_confirmed_notifications(quote)
        
        logger.info(f"Quote {ref} booked successfully, booking ref: {quote.booking_reference}")
        
        return jsonify({
            'success': True,
            'booking_reference': quote.booking_reference,
            'redirect_url': url_for('quotes.quote_results', ref=ref)
        })
    
    except Exception as e:
        logger.error(f"Error booking quote {ref}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while booking'}), 500

@quotes_bp.route('/test-notifications/<ref>')
def test_notifications(ref):
    """Test endpoint for sending notifications (development only)"""
    if not request.args.get('test_key') == 'dev123':
        return "Access denied", 403
    
    quote = Quote.query.filter_by(ref_id=ref).first()
    if not quote:
        return f"Quote {ref} not found", 404
    
    # Test affiliate notification
    from routes.affiliate import send_affiliate_quote_request
    affiliate_result = send_affiliate_quote_request(quote)
    
    # Test quote ready notification
    from routes.affiliate import send_quote_ready_notifications
    quote_ready_result = send_quote_ready_notifications(quote)
    
    # Test booking confirmation
    from routes.affiliate import send_booking_confirmed_notifications
    booking_result = send_booking_confirmed_notifications(quote)
    
    return f"""
    <h3>Notification Test Results for {ref}</h3>
    <p>Affiliate notification: {'Success' if affiliate_result else 'Failed'}</p>
    <p>Quote ready notification: Sent (check logs)</p>
    <p>Booking confirmation: Sent (check logs)</p>
    <p>Check server logs for detailed results.</p>
    """