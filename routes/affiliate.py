"""
Affiliate routes for quote management and notifications
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, session
import logging
from datetime import datetime, timedelta
import uuid

from models import db, Quote, User
from services.mailer import email_service
from services.sms import sms_service

logger = logging.getLogger(__name__)

affiliate_bp = Blueprint('affiliate', __name__, url_prefix='/affiliate')

@affiliate_bp.route('/quote/<quote_ref>', methods=['GET', 'POST'])
def provide_quote(quote_ref):
    """Affiliate quote submission page"""
    # Find the quote request
    quote = Quote.query.filter_by(ref_id=quote_ref).first()
    
    if not quote:
        flash('Quote request not found.', 'error')
        return render_template('affiliate_quote_not_found.html'), 404
    
    if request.method == 'GET':
        return render_template('affiliate_provide_quote.html', quote=quote)
    
    # Handle quote submission
    try:
        # Extract quote data from form
        provider_name = request.form.get('provider_name', '').strip()
        quoted_price = request.form.get('quoted_price', '').strip()
        aircraft_type = request.form.get('aircraft_type', '').strip()
        flight_time = request.form.get('flight_time', '').strip()
        additional_notes = request.form.get('additional_notes', '').strip()
        
        # Basic validation
        if not provider_name or not quoted_price:
            flash('Provider name and quoted price are required.', 'error')
            return render_template('affiliate_provide_quote.html', quote=quote)
        
        # Try to parse price (remove currency symbols)
        try:
            price_clean = quoted_price.replace('$', '').replace(',', '')
            price_value = float(price_clean)
            if price_value <= 0:
                raise ValueError("Price must be positive")
        except ValueError:
            flash('Please enter a valid price (numbers only, no currency symbols).', 'error')
            return render_template('affiliate_provide_quote.html', quote=quote)
        
        # Update quote with affiliate response
        quote.provider_name = provider_name
        quote.quoted_price = price_value
        quote.aircraft_type = aircraft_type
        quote.estimated_flight_time = flight_time
        quote.provider_notes = additional_notes
        quote.quote_status = 'quoted'
        quote.quote_submitted_at = datetime.utcnow()
        quote.quote_expires_at = datetime.utcnow() + timedelta(days=7)  # 7 day expiry
        
        db.session.commit()
        
        # Send notifications to caller
        try:
            send_quote_ready_notifications(quote)
        except Exception as e:
            logger.error(f"Failed to send quote ready notifications: {e}")
        
        logger.info(f"Quote submitted for {quote_ref} by {provider_name}")
        flash('Quote submitted successfully! The customer will be notified.', 'success')
        
        return render_template('affiliate_quote_submitted.html', 
                             quote=quote, 
                             provider_name=provider_name)
    
    except Exception as e:
        logger.error(f"Error submitting quote for {quote_ref}: {str(e)}")
        db.session.rollback()
        flash('An error occurred while submitting your quote. Please try again.', 'error')
        return render_template('affiliate_provide_quote.html', quote=quote)

@affiliate_bp.route('/booking/<quote_ref>/confirm', methods=['POST'])
def confirm_booking(quote_ref):
    """Handle booking confirmation from affiliate"""
    try:
        quote = Quote.query.filter_by(ref_id=quote_ref).first()
        
        if not quote:
            return jsonify({'success': False, 'message': 'Quote not found'}), 404
        
        if quote.quote_status != 'quoted':
            return jsonify({'success': False, 'message': 'Quote is not in correct status for booking'}), 400
        
        # Update quote status to booked
        quote.quote_status = 'booked'
        quote.booking_confirmed_at = datetime.utcnow()
        quote.booking_reference = f"BK{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        db.session.commit()
        
        # Send booking confirmation notifications
        send_booking_confirmed_notifications(quote)
        
        logger.info(f"Booking confirmed for {quote_ref}, booking ref: {quote.booking_reference}")
        
        return jsonify({
            'success': True, 
            'booking_reference': quote.booking_reference,
            'message': 'Booking confirmed successfully!'
        })
    
    except Exception as e:
        logger.error(f"Error confirming booking for {quote_ref}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

def send_affiliate_quote_request(quote):
    """Send new quote request notification to affiliate"""
    try:
        # For demo purposes, send to a test affiliate email
        # In production, this would route to the appropriate affiliate based on location/criteria
        affiliate_email = "affiliate-test@example.com"  # This should come from affiliate database
        
        # Build location strings
        from_location = f"{quote.from_city}, {quote.from_state}" if quote.from_city and quote.from_state else "Location TBD"
        to_location = f"{quote.to_city}, {quote.to_state}" if quote.to_city and quote.to_state else "Destination TBD"
        
        # Build quote URL - fix field name
        quote_url = f"{request.url_root}affiliate/quote/{quote.ref_id}"
        
        # Format flight date
        flight_date_str = quote.flight_date.strftime('%B %d, %Y') if quote.flight_date else "TBD"
        
        # Send email notification - fix field names
        success = email_service.send_affiliate_new_quote(
            affiliate_email=affiliate_email,
            quote_ref=quote.ref_id,
            flight_date=flight_date_str,
            from_location=from_location,
            to_location=to_location,
            quote_url=quote_url
        )
        
        if success:
            quote.affiliate_notified_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"Affiliate notification sent for quote {quote.ref_id}")
        else:
            logger.error(f"Failed to send affiliate notification for quote {quote.ref_id}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error sending affiliate notification: {str(e)}")
        return False

def send_quote_ready_notifications(quote):
    """Send quote ready notifications to caller via email and SMS"""
    try:
        # Build results URL - fix field name
        results_url = f"{request.url_root}quotes/results/{quote.ref_id}"
        
        # Format price
        formatted_price = f"${quote.quoted_price:,.2f}" if quote.quoted_price else "Price TBD"
        
        # Send email notification
        if quote.contact_email:
            email_success = email_service.send_caller_quote_ready(
                caller_email=quote.contact_email,
                quote_ref=quote.ref_id,
                provider_name=quote.provider_name or "Your Provider",
                quoted_price=formatted_price,
                results_url=results_url
            )
        else:
            email_success = False
        
        # Send SMS notification
        if quote.contact_phone:
            sms_message = f"SkyCareLink: Your quote is ready! ${quote.quoted_price:,.0f} from {quote.provider_name or 'provider'}. View details: {results_url}"
            sms_success = sms_service.send_sms(quote.contact_phone, sms_message)
        else:
            sms_success = False
        
        logger.info(f"Quote ready notifications sent for {quote.ref_id} - Email: {email_success}, SMS: {sms_success}")
        return email_success or sms_success
        
    except Exception as e:
        logger.error(f"Error sending quote ready notifications: {str(e)}")
        return False

def send_booking_confirmed_notifications(quote):
    """Send booking confirmation notifications to caller"""
    try:
        # Build results URL
        results_url = f"{request.url_root}quotes/results/{quote.ref_id}"
        
        # Format price
        formatted_price = f"${quote.quoted_price:,.2f}" if quote.quoted_price else "Price TBD"
        
        # Send email notification
        if quote.contact_email:
            email_success = email_service.send_caller_booking_confirmed(
                caller_email=quote.contact_email,
                booking_reference=quote.booking_reference or quote.ref_id,
                provider_name=quote.provider_name or "Your Provider",
                quoted_price=formatted_price,
                flight_date=quote.flight_date.strftime('%B %d, %Y') if quote.flight_date else "TBD"
            )
        else:
            email_success = False
        
        # Send SMS notification
        if quote.contact_phone:
            sms_message = f"SkyCareLink: Booking confirmed! Ref: {quote.booking_reference or quote.ref_id}. {quote.provider_name or 'Provider'} will contact you with flight details."
            sms_success = sms_service.send_sms(quote.contact_phone, sms_message)
        else:
            sms_success = False
        
        logger.info(f"Booking confirmation sent for {quote.ref_id} - Email: {email_success}, SMS: {sms_success}")
        return email_success or sms_success
        
    except Exception as e:
        logger.error(f"Error sending booking confirmation: {str(e)}")
        return False

# Call Center Options Management for IVR Integration
@affiliate_bp.route('/call-center-settings', methods=['GET', 'POST'])
def call_center_settings():
    """Affiliate call center configuration for IVR routing"""
    # This would typically require affiliate authentication
    # For demo purposes, we'll use session-based simple auth
    
    if request.method == 'GET':
        # Load existing settings (in production, from database)
        settings = session.get('affiliate_call_center_settings', {
            'day_phone': '',
            'after_hours_phone': '',
            'business_hours_start': 8,
            'business_hours_end': 18,
            'timezone': 'EST',
            'accepts_level_1': True,
            'accepts_level_2': True,
            'accepts_level_3': False,
            'ivr_consent': False,
            'max_concurrent_calls': 2
        })
        
        return render_template('affiliate_call_center_settings.html', settings=settings)
    
    # Handle POST submission
    try:
        settings = {
            'day_phone': request.form.get('day_phone', '').strip(),
            'after_hours_phone': request.form.get('after_hours_phone', '').strip(),
            'business_hours_start': int(request.form.get('business_hours_start', 8)),
            'business_hours_end': int(request.form.get('business_hours_end', 18)),
            'timezone': request.form.get('timezone', 'EST'),
            'accepts_level_1': 'accepts_level_1' in request.form,
            'accepts_level_2': 'accepts_level_2' in request.form,
            'accepts_level_3': 'accepts_level_3' in request.form,
            'ivr_consent': 'ivr_consent' in request.form,
            'max_concurrent_calls': int(request.form.get('max_concurrent_calls', 2))
        }
        
        # Basic validation
        if not settings['day_phone']:
            flash('Day-time phone number is required.', 'error')
            return render_template('affiliate_call_center_settings.html', settings=settings)
        
        if not (settings['accepts_level_1'] or settings['accepts_level_2'] or settings['accepts_level_3']):
            flash('You must accept at least one severity level.', 'error')
            return render_template('affiliate_call_center_settings.html', settings=settings)
        
        # Store settings (in production, save to database)
        session['affiliate_call_center_settings'] = settings
        
        flash('Call center settings updated successfully!', 'success')
        logger.info(f"Call center settings updated: {settings}")
        
        return redirect(url_for('affiliate.call_center_settings'))
        
    except ValueError as e:
        flash('Invalid input values. Please check your entries.', 'error')
        return render_template('affiliate_call_center_settings.html', settings=request.form)
    except Exception as e:
        logger.error(f"Error updating call center settings: {str(e)}")
        flash('An error occurred while updating settings.', 'error')
        return render_template('affiliate_call_center_settings.html', settings=request.form)

def get_available_affiliates_for_ivr(severity_level, origin_location=None):
    """Get list of affiliates available for IVR routing based on criteria"""
    try:
        # In production, this would query the actual affiliate database
        # with proper geographic matching and real-time availability
        
        # For demo, use session-stored settings
        settings = session.get('affiliate_call_center_settings', {})
        
        if not settings.get('ivr_consent'):
            return []
        
        # Check severity level acceptance
        level_key = f'accepts_level_{severity_level}'
        if not settings.get(level_key, False):
            return []
        
        # Check business hours
        from datetime import datetime
        now = datetime.now()
        current_hour = now.hour
        
        is_business_hours = (
            settings.get('business_hours_start', 8) <= current_hour < settings.get('business_hours_end', 18)
            and now.weekday() < 5  # Monday-Friday
        )
        
        phone_number = settings.get('day_phone' if is_business_hours else 'after_hours_phone')
        
        if not phone_number:
            return []
        
        return [{
            'affiliate_id': 'demo_affiliate_1',
            'name': 'Demo Medical Transport LLC',
            'phone': phone_number,
            'max_concurrent': settings.get('max_concurrent_calls', 2),
            'severity_levels': [
                level for level in [1, 2, 3] 
                if settings.get(f'accepts_level_{level}', False)
            ]
        }]
        
    except Exception as e:
        logger.error(f"Error getting available affiliates for IVR: {str(e)}")
        return []
    """Send booking confirmation notifications to caller via email and SMS"""
    try:
        # Build booking URL (reuse results page)
        booking_url = f"{request.url_root}quotes/results/{quote.reference_number}"
        
        # Format flight date
        flight_date_str = quote.flight_date.strftime('%B %d, %Y') if quote.flight_date else "TBD"
        
        # Send email notification
        if quote.contact_email:
            email_success = email_service.send_caller_booking_confirmed(
                caller_email=quote.contact_email,
                booking_ref=quote.booking_reference,
                provider_name=quote.provider_name or "Your Provider",
                flight_date=flight_date_str,
                booking_url=booking_url
            )
            
            if email_success:
                logger.info(f"Booking confirmation email sent to {quote.contact_email}")
        
        # Send SMS notification if phone number provided
        if quote.contact_phone:
            sms_success = sms_service.send_booking_confirmed_sms(
                to_phone=quote.contact_phone,
                booking_ref=quote.booking_reference,
                provider_name=quote.provider_name or "Your Provider",
                flight_date=flight_date_str,
                booking_url=booking_url
            )
            
            if sms_success:
                logger.info(f"Booking confirmation SMS sent to {quote.contact_phone}")
        
    except Exception as e:
        logger.error(f"Error sending booking confirmation notifications: {str(e)}")