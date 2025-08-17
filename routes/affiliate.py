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
def old_confirm_booking_deprecated(quote_ref):
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

# Affiliate Dashboard Routes
@affiliate_bp.route('/dashboard')
def dashboard():
    """Affiliate dashboard with quote queue"""
    try:
        # Get pending and recent quotes
        quotes = []
        stats = {
            'pending_quotes': 0,
            'completed_today': 0,
            'urgent_requests': 0,
            'revenue_today': 0
        }
        
        if DB_AVAILABLE:
            from datetime import datetime, timedelta
            from models import Quote
            
            # Get quotes for this affiliate (simplified - in production would filter by affiliate ID)
            all_quotes = Quote.query.filter(
                Quote.status.in_(['pending', 'quoted', 'confirmed'])
            ).order_by(Quote.created_at.desc()).limit(20).all()
            
            for quote in all_quotes:
                # Calculate age in hours
                age_delta = datetime.utcnow() - quote.created_at
                age_hours = int(age_delta.total_seconds() / 3600)
                
                quote_data = {
                    'ref_id': quote.ref_id,
                    'status': quote.status,
                    'severity_level': quote.severity_level,
                    'age_hours': age_hours,
                    'from_city': quote.from_city,
                    'from_state': quote.from_state,
                    'to_city': quote.to_city,
                    'to_state': quote.to_state,
                    'flight_date': quote.flight_date,
                    'contact_name': quote.contact_name,
                    'contact_phone': quote.contact_phone,
                    'contact_email': quote.contact_email,
                    'ground_transport_needed': quote.ground_transport_needed,
                    'quoted_price': quote.quoted_price
                }
                quotes.append(quote_data)
                
                # Update statistics
                if quote.status == 'pending':
                    stats['pending_quotes'] += 1
                    if quote.severity_level == 3:
                        stats['urgent_requests'] += 1
                
                # Today's completed quotes
                today = datetime.utcnow().date()
                if quote.quote_submitted_at and quote.quote_submitted_at.date() == today:
                    stats['completed_today'] += 1
                    if quote.quoted_price:
                        stats['revenue_today'] += float(quote.quoted_price)
        
        # Demo quotes if no database
        if not quotes and not DB_AVAILABLE:
            from datetime import datetime, timedelta
            quotes = [
                {
                    'ref_id': 'QT-20250817-001',
                    'status': 'pending',
                    'severity_level': 2,
                    'age_hours': 2,
                    'from_city': 'Miami',
                    'from_state': 'FL',
                    'to_city': 'Atlanta',
                    'to_state': 'GA',
                    'flight_date': datetime.now() + timedelta(days=1),
                    'contact_name': 'John Smith',
                    'contact_phone': '(305) 555-0123',
                    'contact_email': 'john.smith@example.com',
                    'ground_transport_needed': True,
                    'quoted_price': None
                }
            ]
            stats = {
                'pending_quotes': 1,
                'completed_today': 3,
                'urgent_requests': 0,
                'revenue_today': 15750
            }
        
        return render_template('affiliate/dashboard.html', quotes=quotes, stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading affiliate dashboard: {str(e)}")
        flash('Error loading dashboard. Please try again.', 'error')
        return render_template('affiliate/dashboard.html', quotes=[], stats={})

@affiliate_bp.route('/submit-quote/<quote_ref>')
def submit_quote_form(quote_ref):
    """Display quote submission form"""
    try:
        quote = None
        
        if DB_AVAILABLE:
            quote = Quote.query.filter_by(ref_id=quote_ref).first()
        
        if not quote:
            # Demo quote for testing
            from datetime import datetime, timedelta
            quote = type('Quote', (), {
                'ref_id': quote_ref,
                'severity_level': 2,
                'age_hours': 2,
                'from_city': 'Miami',
                'from_state': 'FL',
                'to_city': 'Atlanta',
                'to_state': 'GA',
                'flight_date': datetime.now() + timedelta(days=1),
                'contact_name': 'John Smith',
                'contact_phone': '(305) 555-0123',
                'ground_transport_needed': True
            })
        else:
            # Calculate age for database quote
            from datetime import datetime
            age_delta = datetime.utcnow() - quote.created_at
            quote.age_hours = int(age_delta.total_seconds() / 3600)
        
        return render_template('affiliate/submit_quote.html', quote=quote)
        
    except Exception as e:
        logger.error(f"Error loading quote submission form for {quote_ref}: {str(e)}")
        flash('Quote not found.', 'error')
        return redirect(url_for('affiliate.dashboard'))

@affiliate_bp.route('/submit-quote/<quote_ref>', methods=['POST'])
def submit_quote(quote_ref):
    """Process quote submission"""
    try:
        # Get quote
        quote = None
        if DB_AVAILABLE:
            quote = Quote.query.filter_by(ref_id=quote_ref).first()
        
        if not quote:
            flash('Quote not found.', 'error')
            return redirect(url_for('affiliate.dashboard'))
        
        # Extract form data
        quoted_price = request.form.get('quoted_price', '').strip()
        aircraft_type = request.form.get('aircraft_type', '').strip()
        flight_time = request.form.get('flight_time', '').strip()
        include_ground = 'include_ground' in request.form
        provider_notes = request.form.get('provider_notes', '').strip()
        
        # Validate price
        try:
            price_value = float(quoted_price)
            if price_value <= 0:
                raise ValueError("Price must be positive")
        except (ValueError, TypeError):
            flash('Please enter a valid price amount.', 'error')
            return render_template('affiliate/submit_quote.html', quote=quote)
        
        # Add ground transport cost if included
        if include_ground:
            price_value += 750  # Standard ground transport fee
        
        # Update quote
        quote.quoted_price = price_value
        quote.aircraft_type = aircraft_type
        quote.estimated_flight_time = flight_time
        quote.provider_notes = provider_notes
        quote.status = 'quoted'
        quote.quote_submitted_at = datetime.utcnow()
        
        if DB_AVAILABLE:
            db.session.commit()
        
        # Send notifications
        try:
            send_quote_ready_notifications(quote)
            logger.info(f"Quote submitted for {quote_ref} - Price: ${price_value}")
        except Exception as e:
            logger.error(f"Failed to send quote ready notifications: {e}")
        
        flash('Quote submitted successfully! Customer has been notified.', 'success')
        return redirect(url_for('affiliate.dashboard'))
        
    except Exception as e:
        logger.error(f"Error submitting quote for {quote_ref}: {str(e)}")
        flash('Error submitting quote. Please try again.', 'error')
        return redirect(url_for('affiliate.submit_quote_form', quote_ref=quote_ref))

@affiliate_bp.route('/pass/<quote_ref>', methods=['POST'])
def pass_quote(quote_ref):
    """Pass on a quote to next affiliate"""
    try:
        quote = None
        if DB_AVAILABLE:
            quote = Quote.query.filter_by(ref_id=quote_ref).first()
            
            if quote:
                # Log the pass action
                logger.info(f"Quote {quote_ref} passed by affiliate")
                # In production, this would rotate to next affiliate
                # For now, just keep status as pending
                pass
        
        flash('Quote passed to next affiliate successfully.', 'info')
        
    except Exception as e:
        logger.error(f"Error passing quote {quote_ref}: {str(e)}")
        flash('Error processing request.', 'error')
    
    return redirect(url_for('affiliate.dashboard'))

@affiliate_bp.route('/confirm/<quote_ref>', methods=['POST'])
def confirm_booking(quote_ref):
    """Confirm booking for a quote"""
    try:
        quote = None
        if DB_AVAILABLE:
            quote = Quote.query.filter_by(ref_id=quote_ref).first()
        
        if not quote:
            flash('Quote not found.', 'error')
            return redirect(url_for('affiliate.dashboard'))
        
        if not quote.quoted_price:
            flash('Cannot confirm booking without a quoted price.', 'error')
            return redirect(url_for('affiliate.dashboard'))
        
        # Update quote status
        quote.status = 'confirmed'
        quote.booking_confirmed_at = datetime.utcnow()
        quote.booking_reference = f"BK{datetime.utcnow().strftime('%Y%m%d')}{quote_ref[-4:]}"
        
        if DB_AVAILABLE:
            db.session.commit()
        
        # Send booking confirmation
        try:
            send_booking_confirmed_notifications(quote)
            logger.info(f"Booking confirmed for {quote_ref} - Ref: {quote.booking_reference}")
        except Exception as e:
            logger.error(f"Failed to send booking confirmation notifications: {e}")
        
        flash(f'Booking confirmed! Reference: {quote.booking_reference}', 'success')
        
    except Exception as e:
        logger.error(f"Error confirming booking for {quote_ref}: {str(e)}")
        flash('Error confirming booking. Please try again.', 'error')
    
    return redirect(url_for('affiliate.dashboard'))

@affiliate_bp.route('/call-center-options', methods=['GET', 'POST'])
def call_center_options():
    """Call center options configuration"""
    if request.method == 'GET':
        # Load existing options
        options = session.get('affiliate_call_center_options', {
            'day_phone': '',
            'after_hours_phone': '',
            'hours_start': 8,
            'hours_end': 18,
            'after_hours_opt_in': False,
            'severity_l1': True,
            'severity_l2': True,
            'severity_l3': False,
            'emergency_outreach': False,
            'ground_transport_capable': False,
            'coverage_radius': 150,
            'coverage_regions': ''
        })
        
        return render_template('affiliate/call_center_options.html', options=options)
    
    # Handle POST submission
    try:
        options = {
            'day_phone': request.form.get('day_phone', '').strip(),
            'after_hours_phone': request.form.get('after_hours_phone', '').strip(),
            'hours_start': int(request.form.get('hours_start', 8)),
            'hours_end': int(request.form.get('hours_end', 18)),
            'after_hours_opt_in': 'after_hours_opt_in' in request.form,
            'severity_l1': 'severity_l1' in request.form,
            'severity_l2': 'severity_l2' in request.form,
            'severity_l3': 'severity_l3' in request.form,
            'emergency_outreach': 'emergency_outreach' in request.form,
            'ground_transport_capable': 'ground_transport_capable' in request.form,
            'coverage_radius': int(request.form.get('coverage_radius', 150)),
            'coverage_regions': request.form.get('coverage_regions', '').strip()
        }
        
        # Validation
        if not options['day_phone']:
            flash('Day phone number is required.', 'error')
            return render_template('affiliate/call_center_options.html', options=options)
        
        if not (options['severity_l1'] or options['severity_l2'] or options['severity_l3']):
            flash('You must accept at least one severity level.', 'error')
            return render_template('affiliate/call_center_options.html', options=options)
        
        # Store options
        session['affiliate_call_center_options'] = options
        
        flash('Call center options saved successfully!', 'success')
        logger.info(f"Call center options updated: {options}")
        
        return redirect(url_for('affiliate.call_center_options'))
        
    except ValueError as e:
        flash('Invalid input values. Please check your entries.', 'error')
        return render_template('affiliate/call_center_options.html', options=request.form)
    except Exception as e:
        logger.error(f"Error updating call center options: {str(e)}")
        flash('An error occurred while saving options.', 'error')
        return render_template('affiliate/call_center_options.html', options=request.form)