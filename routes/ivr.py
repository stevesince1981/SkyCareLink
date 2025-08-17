"""
AI IVR (Interactive Voice Response) System with Twilio Integration
Feature-flagged implementation for voice-based quote intake and affiliate routing.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, Response, jsonify, url_for
from twilio.twiml import VoiceResponse
from twilio.twiml.voice_response import Gather, Dial, Number, Say
from app import db
from models import Quote, Affiliate

# Create blueprint
ivr_bp = Blueprint('ivr', __name__, url_prefix='/ivr')

# Feature flag from environment
ENABLE_IVR = os.environ.get('ENABLE_IVR', 'false').lower() == 'true'

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# Business hours configuration (EST)
BUSINESS_HOURS = {
    'start': 8,  # 8 AM
    'end': 18,   # 6 PM
    'days': [0, 1, 2, 3, 4]  # Monday-Friday (0=Monday)
}

def is_business_hours():
    """Check if current time is within business hours"""
    now = datetime.now()
    if now.weekday() in BUSINESS_HOURS['days']:
        return BUSINESS_HOURS['start'] <= now.hour < BUSINESS_HOURS['end']
    return False

def log_ivr_call(phone_number, step, data=None):
    """Log IVR call progress for debugging and analytics"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'phone_number': phone_number[-4:] if phone_number else 'unknown',  # Only last 4 digits for privacy
        'step': step,
        'data': data or {}
    }
    logging.info(f"IVR Call Log: {json.dumps(log_entry)}")

@ivr_bp.route('/voice', methods=['POST'])
def voice_webhook():
    """Main Twilio voice webhook - entry point for IVR system"""
    
    if not ENABLE_IVR:
        response = VoiceResponse()
        response.say("IVR system is currently disabled. Please visit our website or contact support.")
        return Response(str(response), mimetype='application/xml')
    
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        logging.warning("IVR enabled but Twilio credentials not configured")
        response = VoiceResponse()
        response.say("Voice system temporarily unavailable. Please contact support or visit our website.")
        return Response(str(response), mimetype='application/xml')
    
    # Get caller information
    caller_number = request.form.get('From', 'Unknown')
    log_ivr_call(caller_number, 'call_started')
    
    response = VoiceResponse()
    
    # Initial greeting with AI introduction
    response.say(
        "Hello! I'm your SkyCareLink AI assistant. I'll collect a few details about your medical transport needs, "
        "then connect you with a live provider for immediate assistance. "
        "Press 0 at any time to speak directly with a live person, or stay on the line to continue with me.",
        voice='alice',
        rate='medium'
    )
    
    # Gather for live person option
    gather = Gather(
        input='dtmf',
        timeout=3,
        num_digits=1,
        action=url_for('ivr.process_initial_choice', _external=True),
        method='POST'
    )
    response.append(gather)
    
    # If no response, continue with AI intake
    response.redirect(url_for('ivr.collect_date', _external=True))
    
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/process_initial_choice', methods=['POST'])
def process_initial_choice():
    """Process initial choice - live person (0) or continue with AI"""
    caller_number = request.form.get('From', 'Unknown')
    digits = request.form.get('Digits', '')
    
    response = VoiceResponse()
    
    if digits == '0':
        log_ivr_call(caller_number, 'requested_live_person')
        response.say("Connecting you to our live support team. Please hold.", voice='alice')
        # In production, this would dial the support number
        response.say("Support is currently unavailable. Please visit our website at skycarelink.com or try again during business hours, 8 AM to 6 PM Eastern time.")
        return Response(str(response), mimetype='application/xml')
    
    # Continue with AI intake
    response.redirect(url_for('ivr.collect_date', _external=True))
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/collect_date', methods=['POST'])
def collect_date():
    """Collect transport date from caller"""
    caller_number = request.form.get('From', 'Unknown')
    log_ivr_call(caller_number, 'collecting_date')
    
    response = VoiceResponse()
    response.say("First, when do you need transport? Say today for same-day service, or tomorrow, or the specific date.", voice='alice')
    
    # Gather speech input for date
    gather = Gather(
        input='speech',
        timeout=5,
        speech_timeout='auto',
        action=url_for('ivr.process_date', _external=True),
        method='POST'
    )
    response.append(gather)
    
    # Fallback if no response
    response.say("I didn't hear a response. Let me connect you to our support team.")
    response.redirect(url_for('ivr.fallback_to_support', _external=True))
    
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/process_date', methods=['POST'])
def process_date():
    """Process the transport date and move to origin collection"""
    caller_number = request.form.get('From', 'Unknown')
    speech_result = request.form.get('SpeechResult', '').lower()
    
    log_ivr_call(caller_number, 'date_processed', {'speech': speech_result})
    
    # Store date in call context (simplified for demo)
    # In production, this would be stored in a database call record
    
    response = VoiceResponse()
    response.say("Thank you. Now, where is the patient located? Please say the city and state.", voice='alice')
    
    gather = Gather(
        input='speech',
        timeout=5,
        speech_timeout='auto',
        action=url_for('ivr.process_origin', _external=True),
        method='POST'
    )
    response.append(gather)
    
    response.say("I didn't catch that. Let me connect you to our support team.")
    response.redirect(url_for('ivr.fallback_to_support', _external=True))
    
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/process_origin', methods=['POST'])
def process_origin():
    """Process origin location and collect destination"""
    caller_number = request.form.get('From', 'Unknown')
    speech_result = request.form.get('SpeechResult', '')
    
    log_ivr_call(caller_number, 'origin_processed', {'speech': speech_result})
    
    response = VoiceResponse()
    response.say("Got it. And where does the patient need to go? Please say the destination city and state.", voice='alice')
    
    gather = Gather(
        input='speech',
        timeout=5,
        speech_timeout='auto',
        action=url_for('ivr.process_destination', _external=True),
        method='POST'
    )
    response.append(gather)
    
    response.say("I didn't hear that clearly. Transferring to support.")
    response.redirect(url_for('ivr.fallback_to_support', _external=True))
    
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/process_destination', methods=['POST'])
def process_destination():
    """Process destination and collect severity level"""
    caller_number = request.form.get('From', 'Unknown')
    speech_result = request.form.get('SpeechResult', '')
    
    log_ivr_call(caller_number, 'destination_processed', {'speech': speech_result})
    
    response = VoiceResponse()
    response.say(
        "Thank you. Now, what is the patient's condition level? "
        "Press 1 for stable condition, "
        "Press 2 for moderate care needs, "
        "or Press 3 for critical care requirements.",
        voice='alice'
    )
    
    gather = Gather(
        input='dtmf',
        timeout=5,
        num_digits=1,
        action=url_for('ivr.process_severity', _external=True),
        method='POST'
    )
    response.append(gather)
    
    response.say("No selection made. Connecting to support.")
    response.redirect(url_for('ivr.fallback_to_support', _external=True))
    
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/process_severity', methods=['POST'])
def process_severity():
    """Process severity level and ask about ground transport"""
    caller_number = request.form.get('From', 'Unknown')
    digits = request.form.get('Digits', '')
    
    severity_map = {'1': 'Stable', '2': 'Moderate', '3': 'Critical'}
    severity = severity_map.get(digits, 'Unknown')
    
    log_ivr_call(caller_number, 'severity_processed', {'level': digits, 'description': severity})
    
    response = VoiceResponse()
    response.say(
        f"Understood, {severity.lower()} condition. "
        "Is ground ambulance transport to the airport required? Press 1 for yes, 2 for no.",
        voice='alice'
    )
    
    gather = Gather(
        input='dtmf',
        timeout=5,
        num_digits=1,
        action=url_for('ivr.process_ground_transport', _external=True),
        method='POST'
    )
    response.append(gather)
    
    response.redirect(url_for('ivr.fallback_to_support', _external=True))
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/process_ground_transport', methods=['POST'])
def process_ground_transport():
    """Process ground transport needs and collect contact info"""
    caller_number = request.form.get('From', 'Unknown')
    digits = request.form.get('Digits', '')
    
    ground_needed = 'Yes' if digits == '1' else 'No'
    log_ivr_call(caller_number, 'ground_transport_processed', {'needed': ground_needed})
    
    response = VoiceResponse()
    response.say(
        "Perfect. I have all the transport details. "
        "Now I'll connect you with up to 3 available providers who can help immediately. "
        "When connected, press 1 to accept their service or press 2 to try the next provider.",
        voice='alice'
    )
    
    # Start provider connection process
    response.redirect(url_for('ivr.connect_providers', _external=True))
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/connect_providers', methods=['POST'])
def connect_providers():
    """Connect caller to available providers"""
    caller_number = request.form.get('From', 'Unknown')
    log_ivr_call(caller_number, 'connecting_providers')
    
    # In production, this would query the database for available affiliates
    # based on location, severity, and business hours
    
    response = VoiceResponse()
    
    # Mock provider connection for demo
    response.say("Connecting you to Provider 1. Please wait.", voice='alice')
    
    # In production, this would be a real Dial to affiliate number
    gather = Gather(
        input='dtmf',
        timeout=30,
        num_digits=1,
        action=url_for('ivr.process_provider_response', _external=True),
        method='POST'
    )
    
    # Mock provider message
    gather.say(
        "Hello, this is SkyCareLink connecting a medical transport request. "
        "Press 1 to accept this request and speak with the caller, or press 2 to decline.",
        voice='alice'
    )
    
    response.append(gather)
    
    # If no provider response, try next or fallback
    response.redirect(url_for('ivr.try_next_provider', _external=True))
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/process_provider_response', methods=['POST'])
def process_provider_response():
    """Process provider's accept/decline response"""
    caller_number = request.form.get('From', 'Unknown')
    digits = request.form.get('Digits', '')
    
    if digits == '1':
        log_ivr_call(caller_number, 'provider_accepted')
        response = VoiceResponse()
        response.say("Great! The provider has accepted your request. You'll be connected now.", voice='alice')
        # In production, this would bridge the call
        response.say("Please hold while we connect you.")
        return Response(str(response), mimetype='application/xml')
    
    elif digits == '2':
        log_ivr_call(caller_number, 'provider_declined')
        # Try next provider
        response = VoiceResponse()
        response.redirect(url_for('ivr.try_next_provider', _external=True))
        return Response(str(response), mimetype='application/xml')
    
    # No valid response, try next provider
    response = VoiceResponse()
    response.redirect(url_for('ivr.try_next_provider', _external=True))
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/try_next_provider', methods=['POST'])
def try_next_provider():
    """Try connecting to next available provider"""
    caller_number = request.form.get('From', 'Unknown')
    
    # Get attempt count from session or assume this is attempt 2 for demo
    attempt = 2  # In production, track this in call state
    
    if attempt >= 3:
        log_ivr_call(caller_number, 'all_providers_exhausted')
        response = VoiceResponse()
        response.redirect(url_for('ivr.fallback_create_ticket', _external=True))
        return Response(str(response), mimetype='application/xml')
    
    log_ivr_call(caller_number, f'trying_provider_{attempt + 1}')
    
    response = VoiceResponse()
    response.say(f"Trying provider {attempt + 1}. Please wait.", voice='alice')
    
    # Mock next provider attempt
    gather = Gather(
        input='dtmf',
        timeout=20,
        num_digits=1,
        action=url_for('ivr.process_provider_response', _external=True),
        method='POST'
    )
    
    gather.say(
        "Hello, this is SkyCareLink with a medical transport request. "
        "Press 1 to accept and speak with the caller, or press 2 to decline.",
        voice='alice'
    )
    
    response.append(gather)
    response.redirect(url_for('ivr.fallback_create_ticket', _external=True))
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/fallback_create_ticket', methods=['POST'])
def fallback_create_ticket():
    """Create auto-quote ticket when no providers accept"""
    caller_number = request.form.get('From', 'Unknown')
    log_ivr_call(caller_number, 'creating_fallback_ticket')
    
    response = VoiceResponse()
    
    # Create quote record in database
    try:
        if is_business_hours():
            response_time = "same day"
            expected_response = datetime.now() + timedelta(hours=4)
        else:
            response_time = "next business day"
            expected_response = datetime.now() + timedelta(days=1)
            expected_response = expected_response.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Create auto-quote record (simplified for demo)
        ref_id = f"AUTO-{datetime.now().strftime('%Y%m%d')}-{caller_number[-4:]}"
        
        log_ivr_call(caller_number, 'ticket_created', {
            'ref_id': ref_id,
            'expected_response': expected_response.isoformat()
        })
        
        response.say(
            f"I apologize that we couldn't connect you immediately. "
            f"I've created priority quote request {ref_id} for you. "
            f"Our team will call you back with quotes and options within {response_time}. "
            f"You can also visit skycarelink.com and reference {ref_id}. "
            f"Thank you for choosing SkyCareLink.",
            voice='alice'
        )
        
    except Exception as e:
        logging.error(f"Error creating fallback ticket: {e}")
        response.say(
            "I apologize for the technical difficulty. Please visit our website at skycarelink.com "
            "or call back during business hours for immediate assistance. Thank you.",
            voice='alice'
        )
    
    return Response(str(response), mimetype='application/xml')

@ivr_bp.route('/fallback_to_support', methods=['POST'])
def fallback_to_support():
    """General fallback to support when IVR fails"""
    caller_number = request.form.get('From', 'Unknown')
    log_ivr_call(caller_number, 'fallback_to_support')
    
    response = VoiceResponse()
    response.say(
        "I'm having trouble processing your request. Please visit skycarelink.com "
        "or call back during business hours, 8 AM to 6 PM Eastern time, for immediate assistance. "
        "Thank you for choosing SkyCareLink.",
        voice='alice'
    )
    
    return Response(str(response), mimetype='application/xml')

# Status and testing endpoints
@ivr_bp.route('/status')
def ivr_status():
    """Check IVR system status"""
    status = {
        'enabled': ENABLE_IVR,
        'twilio_configured': all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]),
        'business_hours': is_business_hours(),
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status)

@ivr_bp.route('/test_twiml')
def test_twiml():
    """Test endpoint to verify TwiML generation"""
    if not ENABLE_IVR:
        response = VoiceResponse()
        response.say("IVR system is currently disabled.")
        return Response(str(response), mimetype='application/xml')
    
    response = VoiceResponse()
    response.say("IVR system test successful. This is a test message.", voice='alice')
    return Response(str(response), mimetype='application/xml')