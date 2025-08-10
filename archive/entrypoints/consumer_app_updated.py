import os
import logging
import json
import uuid
from datetime import datetime, timedelta
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
    'provider': {'password': 'demo123', 'role': 'provider', 'name': 'Captain Lisa Martinez'},
    'mvp': {'password': 'demo123', 'role': 'mvp', 'name': 'Alex Thompson'},
    'admin': {'password': 'demo123', 'role': 'admin', 'name': 'Admin User'},
    'demo': {'password': 'demo123', 'role': 'admin', 'name': 'Demo User'},
    'demo123': {'password': 'demo123', 'role': 'family', 'name': 'Test User'}  # Additional fallback
}

# Equipment pricing (dynamic)
EQUIPMENT_PRICING = {
    'ventilator': 5000,
    'ecmo': 10000,
    'incubator': 3000,
    'escort': 2000,
    'oxygen': 1000,
    'other': 0  # Custom pricing
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

# Subscription pricing
SUBSCRIPTION_PRICING = {
    'monthly': {'price': 49, 'type': 'month'},
    'yearly': {'price': 499, 'type': 'year', 'savings': 89}
}

# Mock provider database
MOCK_PROVIDERS = [
    {'name': 'AirMed Response', 'base_price': 128000, 'capabilities': ['ventilator', 'ecmo'], 'priority': True},
    {'name': 'LifeFlight Elite', 'base_price': 135000, 'capabilities': ['incubator', 'escort'], 'priority': True},
    {'name': 'CriticalCare Jets', 'base_price': 142000, 'capabilities': ['ventilator', 'oxygen'], 'priority': True},
    {'name': 'MedEvac Solutions', 'base_price': 125000, 'capabilities': ['oxygen', 'escort'], 'priority': False},
    {'name': 'Emergency Wings', 'base_price': 138000, 'capabilities': ['ventilator', 'incubator'], 'priority': False}
]

# Referral tracking
REFERRAL_TIERS = {
    'bronze': {'min_referrals': 10, 'badge': 'bronze'},
    'silver': {'min_referrals': 25, 'badge': 'silver'},
    'gold': {'min_referrals': 50, 'badge': 'gold'},
    'platinum': {'min_referrals': 100, 'badge': 'platinum'}
}

# Priority partner providers
PRIORITY_PARTNERS = ['AirMed Response', 'LifeFlight Elite', 'CriticalCare Jets']

# Authentication helper
def authenticate_user(username, password):
    if username in DEMO_USERS and DEMO_USERS[username]['password'] == password:
        return DEMO_USERS[username]
    return None

# Revenue calculations: $1,000 deposit + 5% commission
def calculate_revenue_metrics():
    total_service_value = 847500
    deposits_collected = 7 * 1000
    commission_earned = total_service_value * 0.05
    actual_revenue = deposits_collected + commission_earned
    return {
        'total_bookings': 7,
        'total_service_value': total_service_value,
        'actual_revenue': actual_revenue,
        'deposits_collected': deposits_collected,
        'commission_earned': commission_earned
    }

# Routes
@consumer_app.route('/')
def consumer_index():
    """Landing page with Critical/Non-Critical/MVP toggle"""
    return render_template('consumer_index.html')

@consumer_app.route('/intake')
def consumer_intake():
    """Enhanced intake form with type selector and dynamic pricing"""
    from datetime import datetime
    transport_type = request.args.get('type', 'critical')  # critical, non-critical, mvp
    return render_template('consumer_intake.html', 
                         transport_type=transport_type,
                         equipment_pricing=EQUIPMENT_PRICING,
                         datetime=datetime)

def generate_quote_session():
    """Generate unique quote session with 24-hour expiry"""
    quote_id = str(uuid.uuid4())
    session['quote_id'] = quote_id
    session['quote_expiry'] = (datetime.now() + timedelta(hours=24)).isoformat()
    session['slots_remaining'] = 2  # Soft urgency mechanism
    return quote_id

def get_provider_quotes(origin, destination, equipment_list, transport_type):
    """Generate mock provider quotes based on parameters"""
    import random
    
    # Filter providers based on availability (geographic simulation)
    available_providers = MOCK_PROVIDERS.copy()
    
    # Simulate geographic limitations
    if 'pakistan' in destination.lower() or 'international' in transport_type.lower():
        available_providers = [p for p in available_providers if p['priority']]  # Only priority partners for international
    
    # Random availability simulation
    num_quotes = min(random.randint(0, 5), len(available_providers))
    
    if num_quotes == 0:
        return []
    
    selected_providers = random.sample(available_providers, num_quotes)
    quotes = []
    
    for i, provider in enumerate(selected_providers):
        # Calculate equipment costs
        equipment_cost = sum(EQUIPMENT_PRICING.get(eq, 0) for eq in equipment_list)
        
        # Add random variation
        variation = random.uniform(0.9, 1.1)
        total_cost = int((provider['base_price'] + equipment_cost) * variation)
        
        # Apply same-day upcharge for critical
        if transport_type == 'critical':
            total_cost = int(total_cost * 1.2)
        
        quotes.append({
            'provider_id': f"provider_{chr(65 + i)}",
            'provider_name': provider['name'],
            'masked_name': f"Provider {chr(65 + i)}****",
            'total_cost': total_cost,
            'equipment_cost': equipment_cost,
            'capabilities': provider['capabilities'],
            'priority': provider['priority'],
            'eta_hours': random.randint(2, 8)
        })
    
    return sorted(quotes, key=lambda x: x['total_cost'])

def send_urgency_alert(user_contact, hours_remaining, quote_data):
    """Stub for sending SMS/email urgency alerts"""
    alert_messages = {
        12: "Your quote expires in 12 hours—secure now?",
        6: "6 hours remaining—act soon",
        1: "1 hour left—finalize payment!"
    }
    
    message = alert_messages.get(hours_remaining, "Quote expiring soon!")
    
    # Mock Twilio/SendGrid integration
    logging.info(f"ALERT STUB - To: {user_contact}, Message: {message}")
    logging.info(f"Quote Data: {quote_data}")
    
    # In production, implement actual Twilio/SendGrid calls here
    return True

@consumer_app.route('/intake', methods=['POST'])
def consumer_intake_post():
    """Process intake form with equipment pricing calculations"""
    # Store form data in session
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
    
    # Calculate equipment costs
    equipment_cost = 0
    for item in session['patient_data']['equipment']:
        if item in EQUIPMENT_PRICING:
            equipment_cost += EQUIPMENT_PRICING[item]
    
    # Same-day upcharge (20%)
    if session['patient_data']['same_day']:
        equipment_cost *= 1.2
    
    session['equipment_cost'] = equipment_cost
    
    return redirect(url_for('consumer_quotes'))

@consumer_app.route('/results')
def consumer_results():
    """Provider results with blurred names and priority partners"""
    if 'patient_data' not in session:
        flash('Please complete the intake form first.', 'warning')
        return redirect(url_for('consumer_intake'))
    
    # Generate providers with blurred names and dynamic pricing
    base_cost = 95000
    equipment_cost = session.get('equipment_cost', 0)
    same_day_multiplier = 1.2 if session.get('patient_data', {}).get('same_day') else 1.0
    
    providers = [
        {
            'id': 'provider_a',
            'name': 'Provider A****',
            'actual_name': 'AirMed Response',
            'blurred_name': 'Provider A**** (Name revealed after booking)',
            'cost': int((base_cost + 30000 + equipment_cost) * same_day_multiplier),
            'eta': '2.5 hours',
            'aircraft': 'Fixed-wing jet',
            'capabilities': ['ICU Support', 'Neonatal', 'Cardiac'],
            'rating': 4.9,
            'is_priority': True,
            'priority_note': 'Priority Partner - Featured placement'
        },
        {
            'id': 'provider_b', 
            'name': 'Provider B****',
            'actual_name': 'LifeFlight Elite',
            'blurred_name': 'Provider B**** (Name revealed after booking)',
            'cost': int((base_cost + 23000 + equipment_cost) * same_day_multiplier),
            'eta': '3.0 hours',
            'aircraft': 'Helicopter',
            'capabilities': ['Emergency', 'Rural Access', 'Weather Ready'],
            'rating': 4.8,
            'is_priority': True,
            'priority_note': 'Priority Partner - Enhanced service'
        },
        {
            'id': 'provider_c',
            'name': 'Provider C****',
            'actual_name': 'SkyMed Standard',
            'blurred_name': 'Provider C**** (Name revealed after booking)',
            'cost': int((base_cost + equipment_cost) * same_day_multiplier),
            'eta': '4.0 hours',
            'aircraft': 'Fixed-wing',
            'capabilities': ['Standard Care', 'Long Distance'],
            'rating': 4.6,
            'is_priority': False,
            'priority_note': None
        }
    ]
    
    # Add provider modification note
    modification_note = "Provider may recommend additional life-saving equipment during pre-flight assessment. You'll be notified of any changes before departure."
    
    return render_template('consumer_results.html', 
                         providers=providers,
                         equipment_cost=equipment_cost,
                         same_day_upcharge=same_day_multiplier > 1,
                         modification_note=modification_note,
                         patient_data=session.get('patient_data', {}))

@consumer_app.route('/quotes')
def consumer_quotes():
    """Enhanced quote results with urgency timer and subscription options"""
    if 'patient_data' not in session:
        flash('Please complete the intake form first.', 'warning')
        return redirect(url_for('consumer_intake'))
    
    # Generate quote session if not exists
    if 'quote_id' not in session:
        generate_quote_session()
    
    # Get quotes from providers
    patient_data = session['patient_data']
    quotes = get_provider_quotes(
        patient_data['origin'],
        patient_data['destination'],
        patient_data['equipment'],
        patient_data['transport_type']
    )
    
    # Handle no availability case
    if not quotes:
        return render_template('consumer_no_availability.html', 
                             patient_data=patient_data,
                             search_params={
                                 'origin': patient_data['origin'],
                                 'destination': patient_data['destination']
                             })
    
    # Check subscription status for unmasked names
    user_subscription = session.get('subscription_status', None)
    show_names = user_subscription in ['monthly', 'yearly'] or session.get('user_role') in ['mvp', 'hospital']
    
    # Calculate urgency timing
    quote_expiry = datetime.fromisoformat(session['quote_expiry'])
    time_remaining = quote_expiry - datetime.now()
    hours_remaining = max(0, int(time_remaining.total_seconds() // 3600))
    
    return render_template('consumer_quotes.html',
                         quotes=quotes,
                         patient_data=patient_data,
                         show_names=show_names,
                         quote_expiry=session['quote_expiry'],
                         hours_remaining=hours_remaining,
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
    # Validate account creation
    email = request.form.get('email')
    password = request.form.get('password')
    contact_name = request.form.get('contact_name')
    
    if not all([email, password, contact_name]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('subscribe', plan=plan))
    
    # Store subscription in session (in production, save to database)
    session['subscription_status'] = plan
    session['subscription_start'] = datetime.now().isoformat()
    session['user_email'] = email
    session['contact_name'] = contact_name
    
    flash(f'Successfully subscribed to {plan} plan! You now have access to unmasked provider names and 10% discounts.', 'success')
    return redirect(url_for('consumer_quotes'))

@consumer_app.route('/confirm')
def consumer_confirm():
    """Enhanced confirmation with account creation requirement and fee breakdown"""
    provider_id = request.args.get('provider')
    
    if not provider_id or 'patient_data' not in session:
        flash('Invalid booking session. Please start over.', 'error')
        return redirect(url_for('consumer_intake'))
    
    # Find selected quote
    quotes = get_provider_quotes(
        session['patient_data']['origin'],
        session['patient_data']['destination'],
        session['patient_data']['equipment'],
        session['patient_data']['transport_type']
    )
    
    selected_quote = None
    for quote in quotes:
        if quote['provider_id'] == provider_id:
            selected_quote = quote
            break
    
    if not selected_quote:
        flash('Selected provider not found. Please choose again.', 'error')
        return redirect(url_for('consumer_quotes'))
    
    # Store selected provider in session
    session['selected_quote'] = selected_quote
    
    # Calculate fee breakdown
    medfly_fee = MEDFLY_CONFIG['non_refundable_fee']
    provider_payment = selected_quote['total_cost'] - medfly_fee
    
    fee_breakdown = {
        'total_cost': selected_quote['total_cost'],
        'medfly_fee': medfly_fee,
        'provider_payment': provider_payment,
        'refundable_amount': provider_payment
    }
    
    return render_template('consumer_confirm.html',
                         quote=selected_quote,
                         patient_data=session['patient_data'],
                         fee_breakdown=fee_breakdown,
                         subscription_discount=session.get('subscription_status') is not None)

@consumer_app.route('/create_account_confirm', methods=['POST'])
def create_account_confirm():
    """Create account during confirmation process"""
    # Collect account data
    contact_name = request.form.get('contact_name')
    email = request.form.get('email')
    password = request.form.get('password')
    patient_gender = request.form.get('patient_gender')
    
    if not all([contact_name, email, password]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('consumer_confirm', provider=session.get('selected_quote', {}).get('provider_id')))
    
    # Store account data in session (transient only)
    session['user_email'] = email
    session['contact_name'] = contact_name
    session['patient_gender'] = patient_gender
    session['account_created'] = datetime.now().isoformat()
    
    # Mock email verification
    logging.info(f"EMAIL VERIFICATION STUB - To: {email}, Activation code: DEMO123")
    
    flash('Account created successfully! Email verification sent (check console for demo code).', 'success')
    return redirect(url_for('consumer_tracking'))

@consumer_app.route('/tracking')
def consumer_tracking():
    """Enhanced tracking with virtual map and AI delay prediction"""
    if 'selected_quote' not in session:
        flash('No active booking found.', 'warning')
        return redirect(url_for('consumer_intake'))
    
    # Simulate tracking stages
    tracking_stages = [
        {'stage': 'Booking Confirmed', 'time': '10:00 AM', 'status': 'completed', 'icon': 'check-circle'},
        {'stage': 'Aircraft Preparation', 'time': '10:30 AM', 'status': 'completed', 'icon': 'tools'},
        {'stage': 'Medical Team Briefing', 'time': '11:00 AM', 'status': 'active', 'icon': 'user-md'},
        {'stage': 'Departure', 'time': '11:30 AM', 'status': 'pending', 'icon': 'plane-departure'},
        {'stage': 'In Transit', 'time': 'TBD', 'status': 'pending', 'icon': 'route'},
        {'stage': 'Arrival', 'time': 'TBD', 'status': 'pending', 'icon': 'map-marker-alt'}
    ]
    
    # Mock weather data (in production, use OpenWeatherMap API)
    weather_data = {
        'origin_weather': {'condition': 'Clear', 'temp': 75, 'wind': '5 mph'},
        'destination_weather': {'condition': 'Partly Cloudy', 'temp': 68, 'wind': '10 mph'},
        'route_weather': 'Favorable conditions expected'
    }
    
    # AI delay prediction (mock)
    delay_prediction = {
        'probability': 15,  # 15% chance of delay
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
    
    return render_template('consumer_confirm.html',
                         base_cost=base_cost,
                         equipment_cost=equipment_cost,
                         family_seat_cost=family_seat_cost,
                         vip_description=vip_description,
                         carecredit_info=carecredit_info,
                         patient_data=session.get('patient_data', {}))

@consumer_app.route('/confirm', methods=['POST'])
def consumer_confirm_post():
    """Process confirmation with add-ons"""
    session['booking_confirmed'] = True
    session['family_seat'] = 'family_seat' in request.form
    session['vip_cabin'] = 'vip_cabin' in request.form
    session['confirmation_id'] = f"MF-{datetime.now().strftime('%Y%m%d')}-{datetime.now().microsecond // 1000:03d}"
    
    return redirect(url_for('consumer_tracking'))

@consumer_app.route('/tracking')
def consumer_tracking():
    """Enhanced tracking with family updates"""
    if not session.get('booking_confirmed'):
        return redirect(url_for('consumer_index'))
    
    # Mock provider data for tracking
    provider = {
        'name': 'AirMed Response',
        'aircraft': 'Helicopter EC-145',
        'pilot': 'Captain Smith',
        'crew': 'Nurse Johnson, Paramedic Davis'
    }
    return render_template('consumer_tracking.html', provider=provider)

@consumer_app.route('/partner_dashboard')
def partner_dashboard():
    """Partner dashboard with bookings and revenue"""
    if not session.get('logged_in') or session.get('user_role') != 'provider':
        flash('Provider access required.', 'error')
        return redirect(url_for('login'))
    
    # Sample partner bookings
    bookings = [
        {
            'id': 'MF-001',
            'date': '2025-08-01',
            'route': 'Orlando → NYC',
            'revenue': 6000,
            'priority': True,
            'status': 'Completed'
        },
        {
            'id': 'MF-002',
            'date': '2025-08-02', 
            'route': 'Miami → Boston',
            'revenue': 5500,
            'priority': False,
            'status': 'In Progress'
        }
    ]
    
    return render_template('partner_dashboard.html', bookings=bookings)

@consumer_app.route('/mvp_incentive')
def mvp_incentive():
    """MVP/Hospital membership perks"""
    return render_template('mvp_hospital_incentive.html')

@consumer_app.route('/mou')
def mou():
    """MOU document display"""
    return render_template('mou.html')

@consumer_app.route('/ai_chat', methods=['POST'])
def ai_chat():
    """AI command processing stub"""
    data = request.get_json() or {}
    command = data.get('command', '').lower()
    
    # Simple command parsing (NLTK stub)
    if 'orlando' in command and 'nyc' in command:
        response = {
            'action': 'fill_form',
            'data': {
                'origin': 'Orlando, FL',
                'destination': 'New York, NY',
                'suggestion': 'I have filled in Orlando to NYC for you. What severity level is this transport?'
            }
        }
    elif 'grandma' in command or 'grandmother' in command:
        response = {
            'action': 'suggest_options',
            'data': {
                'family_seat': True,
                'vip_cabin': True,
                'suggestion': 'For elderly patients, I recommend adding a family seat and considering VIP cabin for comfort.'
            }
        }
    else:
        response = {
            'action': 'clarify',
            'data': {
                'suggestion': 'I can help you plan a transport. Try saying "help me build a flight from Orlando to NYC" or "what options are good for my grandmother?"'
            }
        }
    
    return jsonify(response)

# Login routes
@consumer_app.route('/login', methods=['GET', 'POST'])
def login():
    """Fixed login with proper authentication"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Debug logging
        print(f"Login attempt: username='{username}', password='{password}'")
        print(f"Available users: {list(DEMO_USERS.keys())}")
        
        user_data = authenticate_user(username, password)
        if user_data:
            session['logged_in'] = True
            session['user_role'] = user_data['role']
            session['user_name'] = user_data['name']
            session['username'] = username
            
            print(f"Login successful for {username} as {user_data['role']}")
            flash(f'Welcome, {user_data["name"]}!', 'success')
            
            # Role-based redirection
            if user_data['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user_data['role'] == 'provider':
                return redirect(url_for('partner_dashboard'))
            elif user_data['role'] == 'hospital':
                return redirect(url_for('hospital_dashboard'))
            elif user_data['role'] == 'mvp':
                return redirect(url_for('mvp_dashboard'))
            else:  # family
                return redirect(url_for('family_dashboard'))
        else:
            print(f"Login failed for {username}")
            flash('Invalid username or password. Try: family, hospital, provider, mvp, or admin (password: demo123)', 'error')
    
    return render_template('login_simple.html')

@consumer_app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('consumer_index'))

# Dashboard routes
@consumer_app.route('/family_dashboard')
def family_dashboard():
    """Family dashboard"""
    if not session.get('logged_in') or session.get('user_role') != 'family':
        flash('Family access required.', 'error')
        return redirect(url_for('login'))
    
    return render_template('family_dashboard.html', user_name=session.get('user_name'))

@consumer_app.route('/admin_dashboard')
def admin_dashboard():
    """Admin dashboard with revenue metrics"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    metrics = calculate_revenue_metrics()
    return render_template('consumer_admin_dashboard.html', **metrics)

if __name__ == '__main__':
    consumer_app.run(host='0.0.0.0', port=5001, debug=True)