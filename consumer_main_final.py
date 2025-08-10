import os
import logging
import json
import uuid
# import requests  # Will install if Google Places API is needed
from datetime import datetime, timedelta
import random
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
consumer_app = Flask(__name__, template_folder='consumer_templates', static_folder='consumer_static', static_url_path='/consumer_static')
consumer_app.secret_key = os.environ.get("SESSION_SECRET", "consumer-demo-key-change-in-production")

# Demo user accounts - Fixed login credentials
DEMO_USERS = {
    'family': {'password': 'demo123', 'role': 'family', 'name': 'Sarah Johnson'},
    'hospital': {'password': 'demo123', 'role': 'hospital', 'name': 'Dr. Michael Chen'},
    'affiliate': {'password': 'demo123', 'role': 'affiliate', 'name': 'Captain Lisa Martinez'},
    'mvp': {'password': 'demo123', 'role': 'mvp', 'name': 'Alex Thompson'},
    'admin': {'password': 'demo123', 'role': 'admin', 'name': 'Admin User'}
}

# Global configuration - adjustable non-refundable fee
MEDFLY_CONFIG = {
    'non_refundable_fee': int(os.environ.get("MEDFLY_FEE", "1000")),
    'openweather_api_key': os.environ.get("OPENWEATHER_API_KEY", "demo-key"),
    'google_places_api_key': os.environ.get("GOOGLE_PLACES_API_KEY", "demo-key"),
    'twilio_account_sid': os.environ.get("TWILIO_ACCOUNT_SID", "demo-sid"),
    'twilio_auth_token': os.environ.get("TWILIO_AUTH_TOKEN", "demo-token"),
    'sendgrid_api_key': os.environ.get("SENDGRID_API_KEY", "demo-key")
}

# Equipment pricing (dynamic)
EQUIPMENT_PRICING = {
    'ventilator': 5000,
    'ecmo': 10000,
    'incubator': 3000,
    'escort': 2000,
    'oxygen': 1000,
    'other': 0
}

# Subscription pricing
SUBSCRIPTION_PRICING = {
    'monthly': {'price': 49, 'type': 'month'},
    'yearly': {'price': 499, 'type': 'year', 'savings': 89}
}

# Mock affiliate database (air operators)
MOCK_AFFILIATES = [
    {'name': 'AirMed Response', 'base_price': 128000, 'capabilities': ['ventilator', 'ecmo'], 'priority': True},
    {'name': 'LifeFlight Elite', 'base_price': 135000, 'capabilities': ['incubator', 'escort'], 'priority': True},
    {'name': 'CriticalCare Jets', 'base_price': 142000, 'capabilities': ['ventilator', 'oxygen'], 'priority': True},
    {'name': 'MedEvac Solutions', 'base_price': 125000, 'capabilities': ['oxygen', 'escort'], 'priority': False},
    {'name': 'Emergency Wings', 'base_price': 138000, 'capabilities': ['ventilator', 'incubator'], 'priority': False}
]

# Training/Dummy mode configuration
TRAINING_CONFIG = {
    'enabled': True,  # Per-organization toggle
    'case_limit': 50,  # 50-case cap
    'auto_quote_delay': 30,  # ~30s auto-quotes
    'purge_days': 7,  # 7-day purge
    'dummy_label': 'DUMMY DATA - TRAINING MODE'
}

# Drafts system configuration
DRAFTS_CONFIG = {
    'auto_save_interval': 30,  # seconds
    'draft_expiry_days': 7,
    'max_drafts_per_user': 10
}

# Provider Search System - JSON-based cache with upgrade path
PROVIDERS_INDEX_PATH = 'data/providers_index.json'
SEARCH_METRICS_PATH = 'data/search_metrics.json'

def load_index():
    """Load providers index from JSON file"""
    try:
        with open(PROVIDERS_INDEX_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"providers": []}

def save_index(index_data):
    """Save providers index to JSON file"""
    os.makedirs('data', exist_ok=True)
    with open(PROVIDERS_INDEX_PATH, 'w') as f:
        json.dump(index_data, f, indent=2)

def load_metrics():
    """Load search metrics from JSON file"""
    try:
        with open(SEARCH_METRICS_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "period_start": datetime.utcnow().isoformat() + "Z",
            "internal_hits": 0,
            "external_hits": 0,
            "manual_entries": 0
        }

def save_metrics(metrics_data):
    """Save search metrics to JSON file"""
    os.makedirs('data', exist_ok=True)
    with open(SEARCH_METRICS_PATH, 'w') as f:
        json.dump(metrics_data, f, indent=2)

def search_internal(query):
    """Search internal providers index - case insensitive substring match"""
    index = load_index()
    query_lower = query.lower()
    
    results = []
    for provider in index['providers']:
        if not provider.get('approved', False):
            continue
            
        name_match = query_lower in provider['name'].lower()
        address_match = query_lower in provider['address'].lower()
        
        if name_match or address_match:
            results.append(provider)
    
    # Sort by search_count_90d (popularity) and return top 5
    results.sort(key=lambda x: x.get('search_count_90d', 0), reverse=True)
    return results[:5]

def promote_or_increment(provider_id):
    """Increment search count for selected internal provider"""
    index = load_index()
    
    for provider in index['providers']:
        if provider['id'] == provider_id:
            provider['search_count_90d'] = provider.get('search_count_90d', 0) + 1
            provider['updated_at'] = datetime.utcnow().isoformat() + "Z"
            break
    
    save_index(index)

def submit_manual_entry(name, address, provider_type):
    """Add manual provider entry for admin approval"""
    index = load_index()
    
    new_provider = {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": provider_type,
        "address": address,
        "lat": None,
        "lng": None,
        "source": "manual",
        "approved": False,
        "search_count_90d": 0,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    index['providers'].append(new_provider)
    save_index(index)
    
    # Update metrics
    metrics = load_metrics()
    metrics['manual_entries'] += 1
    save_metrics(metrics)
    
    return new_provider

def record_hit_ratio(source):
    """Record search hit by source type"""
    metrics = load_metrics()
    
    # Check if period is > 90 days old, reset if needed
    period_start = datetime.fromisoformat(metrics['period_start'].replace('Z', '+00:00'))
    if datetime.utcnow() - period_start.replace(tzinfo=None) > timedelta(days=90):
        metrics = {
            "period_start": datetime.utcnow().isoformat() + "Z",
            "internal_hits": 0,
            "external_hits": 0,
            "manual_entries": 0
        }
    
    if source == 'internal':
        metrics['internal_hits'] += 1
    elif source == 'external':
        metrics['external_hits'] += 1
    
    save_metrics(metrics)

def search_google_places(query, api_key):
    """Search Google Places API for providers - stub implementation"""
    if not api_key or api_key == "demo-key":
        return []
    
    # Return mock results for demonstration (Google Places would be enabled with real API key)
    logging.info(f"Google Places API stub called for query: {query}")
    return []

def authenticate_user(username, password):
    if username in DEMO_USERS and DEMO_USERS[username]['password'] == password:
        return DEMO_USERS[username]
    return None

def generate_quote_session():
    """Generate unique quote session with 24-hour expiry"""
    quote_id = str(uuid.uuid4())
    session['quote_id'] = quote_id
    session['quote_expiry'] = (datetime.now() + timedelta(hours=24)).isoformat()
    session['slots_remaining'] = 2
    return quote_id

def get_affiliate_quotes(origin, destination, equipment_list, transport_type, is_training_mode=False):
    """Generate mock affiliate quotes based on parameters"""
    import random
    
    available_affiliates = MOCK_AFFILIATES.copy()
    
    # Training mode simulation
    if is_training_mode:
        # Simulate faster response in training mode
        import time
        time.sleep(TRAINING_CONFIG['auto_quote_delay'])
    
    # Simulate geographic limitations
    if 'pakistan' in destination.lower() or 'international' in transport_type.lower():
        available_affiliates = [p for p in available_affiliates if p['priority']]
    
    # Ensure compact quote display (3-5 items)
    num_quotes = min(random.randint(3, 5), len(available_affiliates))
    
    if num_quotes == 0:
        return []
    
    selected_affiliates = random.sample(available_affiliates, num_quotes)
    quotes = []
    
    for i, affiliate in enumerate(selected_affiliates):
        equipment_cost = sum(EQUIPMENT_PRICING.get(eq, 0) for eq in equipment_list)
        variation = random.uniform(0.9, 1.1)
        total_cost = int((affiliate['base_price'] + equipment_cost) * variation)
        
        if transport_type == 'critical':
            total_cost = int(total_cost * 1.2)
        
        quotes.append({
            'affiliate_id': f"affiliate_{chr(65 + i)}",
            'affiliate_name': affiliate['name'],
            'masked_name': f"Affiliate {chr(65 + i)}****",
            'total_cost': total_cost,
            'equipment_cost': equipment_cost,
            'capabilities': affiliate['capabilities'],
            'priority': affiliate['priority'],
            'eta_hours': random.randint(2, 8),
            'is_training': is_training_mode
        })
    
    return sorted(quotes, key=lambda x: x['total_cost'])

def save_draft(session_data, draft_id=None):
    """Auto-save draft functionality"""
    if not draft_id:
        draft_id = str(uuid.uuid4())
    
    draft_data = {
        'id': draft_id,
        'data': session_data,
        'status': 'draft',
        'created_at': datetime.now().isoformat(),
        'last_modified': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(days=DRAFTS_CONFIG['draft_expiry_days'])).isoformat()
    }
    
    # In production, save to database
    # For demo, store in session
    if 'drafts' not in session:
        session['drafts'] = {}
    session['drafts'][draft_id] = draft_data
    session.modified = True
    
    logging.info(f"Draft saved: {draft_id}")
    return draft_id

def load_draft(draft_id):
    """Load saved draft data"""
    if 'drafts' in session and draft_id in session['drafts']:
        return session['drafts'][draft_id]
    return None

def delete_draft(draft_id):
    """Delete a draft (only for draft status)"""
    if 'drafts' in session and draft_id in session['drafts']:
        draft = session['drafts'][draft_id]
        if draft['status'] == 'draft':
            del session['drafts'][draft_id]
            session.modified = True
            return True
    return False

def cancel_active_request(request_id):
    """Cancel an active quoted request (cannot delete, only cancel)"""
    # In production, update status in database
    logging.info(f"Request cancelled: {request_id}")
    return True

def send_urgency_alert(user_contact, hours_remaining, quote_data):
    """Stub for sending SMS/email urgency alerts"""
    alert_messages = {
        12: "Your quote expires in 12 hours—secure now?",
        6: "6 hours remaining—act soon",
        1: "1 hour left—finalize payment!"
    }
    
    message = alert_messages.get(hours_remaining, "Quote expiring soon!")
    logging.info(f"ALERT STUB - To: {user_contact}, Message: {message}")
    return True

# Routes
@consumer_app.route('/')
def consumer_index():
    """Bubble-inspired landing page with popup forms and enhanced UI"""
    return render_template('consumer_index_enhanced.html')

@consumer_app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@consumer_app.route('/login', methods=['POST'])
def login_post():
    """Process login"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = authenticate_user(username, password)
    if user:
        session['logged_in'] = True
        session['user_role'] = user['role']
        session['contact_name'] = user['name']
        flash(f'Welcome, {user["name"]}!', 'success')
        return redirect(url_for('consumer_index'))
    else:
        flash('Invalid credentials. Try: family, hospital, provider, mvp, or admin with password: demo123', 'error')
        return redirect(url_for('login'))

@consumer_app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('consumer_index'))

@consumer_app.route('/signup', methods=['POST'])
def signup_post():
    """Process signup form with email verification"""
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')
    role = request.form.get('role')
    
    # In production, this would:
    # 1. Hash password
    # 2. Store in database
    # 3. Send verification email
    # 4. Generate activation token
    
    # For demo, simulate email verification
    verification_code = "DEMO123"
    logging.info(f"EMAIL VERIFICATION STUB - To: {email}, Activation code: {verification_code}")
    
    session['pending_signup'] = {
        'name': name,
        'email': email,
        'role': role,
        'phone': phone,
        'verification_code': verification_code
    }
    
    flash(f'Account created! Check your email ({email}) for verification code: {verification_code}', 'success')
    return redirect(url_for('consumer_index'))

@consumer_app.route('/referrals')
def consumer_referrals():
    """Referral program page"""
    return render_template('consumer_referrals.html')

@consumer_app.route('/requests')
def consumer_requests():
    """Unified request/quote management page with historical data"""
    return render_template('consumer_requests.html')

@consumer_app.route('/portal-views')
def portal_views():
    """Portal dashboard views without login requirement"""
    return render_template('portal_views.html')

@consumer_app.route('/admin-dashboard')
def admin_dashboard():
    """Enhanced admin dashboard with comprehensive controls"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('consumer_index'))
    
    # Admin dashboard data
    admin_data = {
        'total_revenue': 847500,
        'monthly_revenue': 127000,
        'total_users': 1247,
        'new_users_week': 89,
        'flight_requests': 342,
        'completed_flights': 156,
        'active_quotes': 67,
        'paid_quotes_today': 23,
        'providers': [
            {'name': 'AeroMed Services', 'flights': 45, 'revenue': 234500},
            {'name': 'SkyLife Medical', 'flights': 38, 'revenue': 198750},
            {'name': 'CriticalCare Air', 'flights': 42, 'revenue': 215600},
            {'name': 'MedTransport Plus', 'flights': 31, 'revenue': 167200}
        ]
    }
    
    return render_template('admin_dashboard_enhanced.html', admin_data=admin_data)

# Draft Management Routes
@consumer_app.route('/api/save-draft', methods=['POST'])
def api_save_draft():
    """Auto-save draft endpoint"""
    try:
        data = request.get_json()
        draft_id = save_draft(data)
        return jsonify({'success': True, 'draft_id': draft_id})
    except Exception as e:
        logging.error(f"Draft save error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@consumer_app.route('/api/load-draft/<draft_id>')
def api_load_draft(draft_id):
    """Load draft endpoint"""
    try:
        draft = load_draft(draft_id)
        if draft:
            return jsonify({'success': True, 'draft': draft})
        return jsonify({'success': False, 'error': 'Draft not found'}), 404
    except Exception as e:
        logging.error(f"Draft load error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@consumer_app.route('/api/delete-draft/<draft_id>', methods=['DELETE'])
def api_delete_draft(draft_id):
    """Delete draft endpoint (only for draft status)"""
    try:
        success = delete_draft(draft_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Cannot delete active request'}), 400
    except Exception as e:
        logging.error(f"Draft delete error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@consumer_app.route('/api/cancel-request/<request_id>', methods=['POST'])
def api_cancel_request(request_id):
    """Cancel active request endpoint (cannot delete, only cancel)"""
    try:
        success = cancel_active_request(request_id)
        return jsonify({'success': success})
    except Exception as e:
        logging.error(f"Request cancel error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@consumer_app.route('/toggle-training-mode', methods=['POST'])
def toggle_training_mode():
    """Toggle training/dummy mode for organization"""
    if session.get('user_role') not in ['admin', 'hospital']:
        flash('Admin access required.', 'error')
        return redirect(url_for('consumer_index'))
    
    session['training_mode'] = not session.get('training_mode', False)
    mode_status = "enabled" if session['training_mode'] else "disabled"
    flash(f'Training mode {mode_status}. All data will be clearly labeled as DUMMY DATA.', 'info')
    return redirect(request.referrer or url_for('consumer_index'))

@consumer_app.route('/confirm')
def confirm_account():
    """Account confirmation page with email verification"""
    pending = session.get('pending_signup', {})
    if not pending:
        flash('No pending account found. Your quotes will be available within 24-48 hours after account creation.', 'warning')
        return redirect(url_for('consumer_index'))
    
    return render_template('consumer_confirm.html', pending_signup=pending)

@consumer_app.route('/booking')
def consumer_booking():
    """Booking confirmation page"""
    quote_id = request.args.get('quote')
    provider = request.args.get('provider', 'Selected Provider')
    
    # In production, this would process the actual booking
    booking_ref = f"BK-{random.randint(100000, 999999)}"
    
    return render_template('consumer_booking.html', 
                         quote_id=quote_id,
                         provider=provider,
                         booking_ref=booking_ref)

@consumer_app.route('/intake')
def consumer_intake():
    """Enhanced intake form with type selector and dynamic pricing"""
    transport_type = request.args.get('type', 'critical')
    return render_template('consumer_intake.html', 
                         transport_type=transport_type,
                         equipment_pricing=EQUIPMENT_PRICING,
                         datetime=datetime)

@consumer_app.route('/intake', methods=['POST'])
def consumer_intake_post():
    """Process intake form with equipment pricing calculations"""
    session['patient_data'] = {
        'transport_type': request.form.get('transport_type'),
        'patient_name': request.form.get('patient_name'),
        'patient_age': request.form.get('patient_age'),
        'origin': request.form.get('origin'),
        'destination': request.form.get('destination'),
        'severity': int(request.form.get('severity', 1)),
        'equipment': request.form.getlist('equipment'),
        'same_day': 'same_day' in request.form,
        'date_time': request.form.get('date_time'),
        'additional_notes': request.form.get('additional_notes'),
        'passport_confirmed': 'passport_confirmed' in request.form
    }
    
    equipment_cost = 0
    for item in session['patient_data']['equipment']:
        if item in EQUIPMENT_PRICING:
            equipment_cost += EQUIPMENT_PRICING[item]
    
    if session['patient_data']['same_day']:
        equipment_cost *= 1.2
    
    session['equipment_cost'] = equipment_cost
    return redirect(url_for('consumer_quotes'))

@consumer_app.route('/quotes')
def consumer_quotes():
    """Enhanced quote results with urgency timer and subscription options"""
    if 'patient_data' not in session:
        flash('Please complete the intake form first.', 'warning')
        return redirect(url_for('consumer_intake'))
    
    if 'quote_id' not in session:
        generate_quote_session()
    
    patient_data = session['patient_data']
    quotes = get_affiliate_quotes(
        patient_data['origin'],
        patient_data['destination'],
        patient_data['equipment'],
        patient_data['transport_type']
    )
    
    if not quotes:
        return render_template('consumer_no_availability.html', 
                             patient_data=patient_data,
                             search_params={
                                 'origin': patient_data['origin'],
                                 'destination': patient_data['destination']
                             })
    
    user_subscription = session.get('subscription_status', None)
    show_names = user_subscription in ['monthly', 'yearly'] or session.get('user_role') in ['mvp', 'hospital']
    
    quote_expiry = datetime.fromisoformat(session['quote_expiry'])
    time_remaining = quote_expiry - datetime.now()
    hours_remaining = max(0, int(time_remaining.total_seconds() // 3600))
    
    # Add early adopter status and enhanced data for professional display
    for i, quote in enumerate(quotes):
        quote['early_adopter'] = i < 2  # First 2 affiliates are early adopters
        quote['rating'] = random.randint(4, 5)
        quote['flight_time'] = f"{random.randint(2, 4)} hours"
        quote['aircraft_type'] = random.choice(['Medical Helicopter', 'Fixed Wing Aircraft', 'Medical Jet'])
        quote['crew_size'] = '2 Medical Professionals'
        quote['certifications'] = 'FAA Part 135 + Medical'
        quote['name'] = quote.get('affiliate_name', f"Affiliate {chr(65 + i)}")
        quote['base_price'] = quote['total_cost'] - quote.get('equipment_cost', 0)
    
    return render_template('consumer_quotes_enhanced.html',
                         quotes=quotes,
                         patient_data=patient_data,
                         show_names=show_names,
                         quote_expiry=session.get('quote_expiry'),
                         hours_remaining=hours_remaining,
                         urgency_deadline=quote_expiry,
                         slots_remaining=session.get('slots_remaining', 2),
                         subscription_pricing=SUBSCRIPTION_PRICING,
                         medfly_fee=MEDFLY_CONFIG['non_refundable_fee'])

@consumer_app.route('/subscribe/<plan>')
def subscribe(plan):
    """Subscription signup page"""
    if plan not in ['monthly', 'yearly']:
        flash('Invalid subscription plan.', 'error')
        return redirect(url_for('consumer_quotes'))
    
    pricing = SUBSCRIPTION_PRICING[plan]
    return render_template('consumer_subscribe.html', plan=plan, pricing=pricing)

@consumer_app.route('/subscribe/<plan>', methods=['POST'])
def subscribe_post(plan):
    """Process subscription signup"""
    email = request.form.get('email')
    password = request.form.get('password')
    contact_name = request.form.get('contact_name')
    
    if not all([email, password, contact_name]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('subscribe', plan=plan))
    
    session['subscription_status'] = plan
    session['subscription_start'] = datetime.now().isoformat()
    session['user_email'] = email
    session['contact_name'] = contact_name
    
    flash(f'Successfully subscribed to {plan} plan! You now have access to unmasked provider names and 10% discounts.', 'success')
    return redirect(url_for('consumer_quotes'))

@consumer_app.route('/confirm')
def consumer_confirm():
    """Enhanced confirmation with account creation requirement and fee breakdown"""
    affiliate_id = request.args.get('affiliate')
    
    if not affiliate_id or 'patient_data' not in session:
        flash('Invalid booking session. Please start over.', 'error')
        return redirect(url_for('consumer_intake'))
    
    patient_data = session['patient_data']
    quotes = get_affiliate_quotes(
        patient_data['origin'],
        patient_data['destination'],
        patient_data['equipment'],
        patient_data['transport_type']
    )
    
    selected_quote = None
    for quote in quotes:
        if quote['affiliate_id'] == affiliate_id:
            selected_quote = quote
            break
    
    if not selected_quote:
        flash('Selected affiliate not found. Please choose again.', 'error')
        return redirect(url_for('consumer_quotes'))
    
    session['selected_quote'] = selected_quote
    
    medfly_fee = MEDFLY_CONFIG['non_refundable_fee']
    affiliate_payment = selected_quote['total_cost'] - medfly_fee
    
    fee_breakdown = {
        'total_cost': selected_quote['total_cost'],
        'medfly_fee': medfly_fee,
        'affiliate_payment': affiliate_payment,
        'refundable_amount': affiliate_payment
    }
    
    return render_template('consumer_confirm.html',
                         quote=selected_quote,
                         patient_data=session['patient_data'],
                         fee_breakdown=fee_breakdown,
                         subscription_discount=session.get('subscription_status') is not None)

@consumer_app.route('/create_account_confirm', methods=['POST'])
def create_account_confirm():
    """Create account during confirmation process"""
    contact_name = request.form.get('contact_name')
    email = request.form.get('email')
    password = request.form.get('password')
    patient_gender = request.form.get('patient_gender')
    
    if not all([contact_name, email, password]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('consumer_confirm', affiliate=session.get('selected_quote', {}).get('affiliate_id')))
    
    session['user_email'] = email
    session['contact_name'] = contact_name
    session['patient_gender'] = patient_gender
    session['account_created'] = datetime.now().isoformat()
    
    logging.info(f"EMAIL VERIFICATION STUB - To: {email}, Activation code: DEMO123")
    
    flash('Account created successfully! Email verification sent (check console for demo code).', 'success')
    return redirect(url_for('consumer_tracking'))

@consumer_app.route('/tracking')
def consumer_tracking():
    """Enhanced tracking with virtual map and AI delay prediction"""
    if 'selected_quote' not in session:
        flash('No active booking found.', 'warning')
        return redirect(url_for('consumer_intake'))
    
    tracking_stages = [
        {'stage': 'Booking Confirmed', 'time': '10:00 AM', 'status': 'completed', 'icon': 'check-circle'},
        {'stage': 'Aircraft Preparation', 'time': '10:30 AM', 'status': 'completed', 'icon': 'tools'},
        {'stage': 'Medical Team Briefing', 'time': '11:00 AM', 'status': 'active', 'icon': 'user-md'},
        {'stage': 'Departure', 'time': '11:30 AM', 'status': 'pending', 'icon': 'plane-departure'},
        {'stage': 'In Transit', 'time': 'TBD', 'status': 'pending', 'icon': 'route'},
        {'stage': 'Arrival', 'time': 'TBD', 'status': 'pending', 'icon': 'map-marker-alt'}
    ]
    
    weather_data = {
        'origin_weather': {'condition': 'Clear', 'temp': 75, 'wind': '5 mph'},
        'destination_weather': {'condition': 'Partly Cloudy', 'temp': 68, 'wind': '10 mph'},
        'route_weather': 'Favorable conditions expected'
    }
    
    delay_prediction = {
        'probability': 15,
        'potential_delay': '30 minutes',
        'reason': 'Minor air traffic congestion possible',
        'alternatives': 'Alternative routes prepared'
    }
    
    return render_template('consumer_tracking.html',
                         quote=session['selected_quote'],
                         patient_data=session['patient_data'],
                         tracking_stages=tracking_stages,
                         weather_data=weather_data,
                         delay_prediction=delay_prediction)

@consumer_app.route('/referrals')
def referrals_page():
    """Referral member page with engaging visuals"""
    testimonials = [
        {'name': 'Sarah M.', 'text': 'MediFly saved precious time during our emergency. Professional and caring.', 'rating': 5},
        {'name': 'Dr. Johnson', 'text': 'As a hospital partner, their service consistently exceeds expectations.', 'rating': 5},
        {'name': 'Mike T.', 'text': 'The family support and communication was outstanding during a difficult time.', 'rating': 5}
    ]
    
    stats = {
        'average_savings': '20%',
        'response_time': '< 2 hours',
        'success_rate': '99.8%',
        'family_satisfaction': '4.9/5'
    }
    
    return render_template('consumer_referrals.html', testimonials=testimonials, stats=stats)

@consumer_app.route('/partners')
def partners_page():
    """Partner referral page with infographics and stats"""
    partner_benefits = [
        {'title': 'Free Lead Generation', 'description': 'No cost referrals from our platform', 'icon': 'users'},
        {'title': 'Volume Growth', 'description': 'Access to expanded patient network', 'icon': 'chart-line'},
        {'title': 'Efficiency Tools', 'description': 'Streamlined booking and management', 'icon': 'cogs'},
        {'title': 'Market Expansion', 'description': 'Geographic reach beyond current service area', 'icon': 'globe'}
    ]
    
    partner_stats = {
        'cost_reduction': '50%',
        'volume_increase': '35%',
        'partner_count': '150+',
        'success_stories': '500+'
    }
    
    return render_template('consumer_partners.html', benefits=partner_benefits, stats=partner_stats)

@consumer_app.route('/admin/fee_adjustment')
def admin_fee_adjustment():
    """Admin dashboard for adjusting non-refundable fee"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    current_fee = MEDFLY_CONFIG['non_refundable_fee']
    
    return render_template('admin_fee_adjustment.html', current_fee=current_fee)

@consumer_app.route('/admin/fee_adjustment', methods=['POST'])
def admin_fee_adjustment_post():
    """Update non-refundable fee"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    new_fee = request.form.get('new_fee', type=int)
    if new_fee and new_fee > 0:
        MEDFLY_CONFIG['non_refundable_fee'] = new_fee
        flash(f'Non-refundable fee updated to ${new_fee:,}', 'success')
        logging.info(f"ADMIN: Fee updated to ${new_fee} by {session.get('contact_name', 'admin')}")
    else:
        flash('Please enter a valid fee amount.', 'error')
    
    return redirect(url_for('admin_fee_adjustment'))

# AI Command Processing and Chat Integration
@consumer_app.route('/ai_command', methods=['POST'])
def ai_command():
    """Process AI commands for smart form filling"""
    command = request.form.get('command', '').lower()
    response = {'status': 'success', 'suggestions': {}}
    
    # AI command patterns (stub implementation)
    if 'grandma' in command and 'orlando' in command and 'nyc' in command:
        response['suggestions'] = {
            'origin': 'Orlando International Airport (MCO)',
            'destination': 'LaGuardia Airport (LGA)',
            'transport_type': 'non-critical',
            'equipment': ['oxygen', 'escort'],
            'message': 'I suggest comfortable transport with oxygen support and medical escort for elderly patient.'
        }
    elif 'emergency' in command or 'urgent' in command:
        response['suggestions'] = {
            'transport_type': 'critical',
            'same_day': True,
            'message': 'Emergency transport recommended with same-day priority.'
        }
    elif 'family' in command:
        response['suggestions'] = {
            'equipment': ['escort'],
            'message': 'Family accommodation options available.'
        }
    else:
        response = {
            'status': 'info',
            'message': 'Try commands like: "Help me build a flight for grandma from Orlando to NYC" or "Emergency transport needed"'
        }
    
    return jsonify(response)

# Partner Dashboard (for providers)
@consumer_app.route('/partner_dashboard')
def partner_dashboard():
    """Partner dashboard with bookings and revenue"""
    if not session.get('logged_in') or session.get('user_role') != 'affiliate':
        flash('Affiliate access required.', 'error')
        return redirect(url_for('login'))
    
    # Mock partner data
    partner_bookings = [
        {'date': '2025-08-01', 'origin': 'Orlando', 'destination': 'NYC', 'revenue': 128000, 'status': 'completed'},
        {'date': '2025-08-03', 'origin': 'Miami', 'destination': 'Atlanta', 'revenue': 135000, 'status': 'active'},
        {'date': '2025-08-04', 'origin': 'Tampa', 'destination': 'Boston', 'revenue': 142000, 'status': 'pending'}
    ]
    
    total_revenue = sum(booking['revenue'] for booking in partner_bookings)
    partner_stats = {
        'total_bookings': len(partner_bookings),
        'total_revenue': total_revenue,
        'success_rate': '98.5%',
        'priority_status': True
    }
    
    return render_template('partner_dashboard.html', 
                         bookings=partner_bookings, 
                         stats=partner_stats)

@consumer_app.route('/join_affiliate')
def join_affiliate():
    """Join as Affiliate (Air Operator)"""
    return render_template('join_affiliate.html')

# Provider Search API Endpoints
@consumer_app.route('/api/providers/search')
def api_providers_search():
    """Hybrid search: internal cache first, then Google Places, then manual fallback"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'ok': True, 'results': []})
    
    # Step 1: Try internal search first
    internal_results = search_internal(query)
    
    if internal_results:
        # Record internal hit and return
        record_hit_ratio('internal')
        
        # Format results for frontend
        results = []
        for provider in internal_results:
            results.append({
                'id': provider['id'],
                'name': provider['name'],
                'address': provider['address'],
                'type': provider['type'],
                'source': 'internal',
                'lat': provider.get('lat'),
                'lng': provider.get('lng'),
                'search_count': provider.get('search_count_90d', 0)
            })
        
        return jsonify({
            'ok': True,
            'results': results,
            'source': 'internal',
            'message': f'Found {len(results)} internal matches'
        })
    
    # Step 2: Try Google Places if API key is available
    api_key = MEDFLY_CONFIG.get('google_places_api_key')
    if api_key and api_key != "demo-key":
        google_results = search_google_places(query, api_key)
        
        if google_results:
            record_hit_ratio('external')
            return jsonify({
                'ok': True,
                'results': google_results,
                'source': 'google',
                'message': f'Found {len(google_results)} Google Places matches'
            })
    
    # Step 3: No results - return empty with manual entry suggestion
    return jsonify({
        'ok': True,
        'results': [],
        'source': 'none',
        'message': 'No matches found. Please add manually if needed.'
    })

@consumer_app.route('/api/providers/manual', methods=['POST'])
def api_providers_manual():
    """Submit manual provider entry for admin approval"""
    data = request.get_json()
    
    name = data.get('name', '').strip()
    address = data.get('address', '').strip()
    provider_type = data.get('type', 'unknown').strip()
    
    if not name or not address:
        return jsonify({'ok': False, 'error': 'Name and address are required'}), 400
    
    # Valid types
    valid_types = ['hospital', 'clinic', 'airport', 'address', 'unknown']
    if provider_type not in valid_types:
        provider_type = 'unknown'
    
    try:
        new_provider = submit_manual_entry(name, address, provider_type)
        
        return jsonify({
            'ok': True,
            'provider': {
                'id': new_provider['id'],
                'name': new_provider['name'],
                'address': new_provider['address'],
                'type': new_provider['type'],
                'source': 'manual',
                'approved': False
            },
            'message': 'Manual entry submitted for admin approval'
        })
    
    except Exception as e:
        logging.error(f"Manual entry error: {e}")
        return jsonify({'ok': False, 'error': 'Failed to save manual entry'}), 500

@consumer_app.route('/api/providers/select', methods=['POST'])
def api_providers_select():
    """Record provider selection and increment usage stats"""
    data = request.get_json()
    provider_id = data.get('provider_id')
    source = data.get('source', 'unknown')
    
    if not provider_id:
        return jsonify({'ok': False, 'error': 'Provider ID required'}), 400
    
    # If internal provider, increment usage count
    if source == 'internal':
        promote_or_increment(provider_id)
    
    return jsonify({'ok': True, 'message': 'Selection recorded'})

# Admin Facilities Management
@consumer_app.route('/admin/facilities')
def admin_facilities():
    """Admin page for managing facilities and approval queue"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    index = load_index()
    metrics = load_metrics()
    
    # Separate approved and pending providers
    approved_providers = [p for p in index['providers'] if p.get('approved', False)]
    pending_providers = [p for p in index['providers'] if not p.get('approved', False)]
    
    # Calculate hit ratio for cost control KPI
    total_hits = metrics['internal_hits'] + metrics['external_hits']
    internal_percentage = (metrics['internal_hits'] / total_hits * 100) if total_hits > 0 else 0
    
    hit_ratio_stats = {
        'internal_hits': metrics['internal_hits'],
        'external_hits': metrics['external_hits'],
        'manual_entries': metrics['manual_entries'],
        'internal_percentage': round(internal_percentage, 1),
        'period_start': metrics['period_start']
    }
    
    return render_template('admin_facilities.html',
                         approved_providers=approved_providers,
                         pending_providers=pending_providers,
                         hit_ratio_stats=hit_ratio_stats)

@consumer_app.route('/admin/facilities/approve/<provider_id>', methods=['POST'])
def admin_approve_provider(provider_id):
    """Approve a manual provider entry"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return jsonify({'ok': False, 'error': 'Admin access required'}), 403
    
    index = load_index()
    
    for provider in index['providers']:
        if provider['id'] == provider_id:
            provider['approved'] = True
            provider['source'] = 'internal'  # Promote to internal once approved
            provider['updated_at'] = datetime.utcnow().isoformat() + "Z"
            break
    
    save_index(index)
    flash('Provider approved and added to internal index.', 'success')
    return redirect(url_for('admin_facilities'))

@consumer_app.route('/admin/facilities/reject/<provider_id>', methods=['POST'])
def admin_reject_provider(provider_id):
    """Reject and remove a manual provider entry"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return jsonify({'ok': False, 'error': 'Admin access required'}), 403
    
    index = load_index()
    index['providers'] = [p for p in index['providers'] if p['id'] != provider_id]
    save_index(index)
    
    flash('Provider rejected and removed.', 'success')
    return redirect(url_for('admin_facilities'))

# Duplicate route removed - keeping original join_affiliate route above

@consumer_app.route('/join_hospital')
def join_hospital():
    """Join as Hospital/Clinic"""
    return render_template('join_hospital.html')

if __name__ == '__main__':
    consumer_app.run(host='0.0.0.0', port=5000, debug=True)