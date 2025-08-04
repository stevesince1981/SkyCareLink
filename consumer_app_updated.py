import os
import logging
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
    
    return redirect(url_for('consumer_results'))

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

@consumer_app.route('/confirm')
def consumer_confirm():
    """Confirmation with family seat options, VIP upgrades, and payment links"""
    provider_id = request.args.get('provider')
    if not provider_id:
        flash('Please select a provider first.', 'warning')
        return redirect(url_for('consumer_results'))
    
    # Store selected provider
    session['selected_provider'] = provider_id
    
    # Calculate final pricing
    base_cost = session.get('base_cost', 95000)
    equipment_cost = session.get('equipment_cost', 0)
    family_seat_cost = 5000
    vip_cabin_cost = 10000
    
    # VIP cabin description
    vip_description = {
        'title': 'VIP Luxury Medical Cabin',
        'price': vip_cabin_cost,
        'features': [
            'Premium leather seating with full recline',
            'IV hydration and wellness treatments during flight',
            'Champagne service (when medically appropriate)',
            'Priority boarding and departure',
            'Enhanced privacy with luxury amenities',
            'Dedicated cabin attendant for comfort needs'
        ],
        'note': 'VIP cabin provides ultimate comfort while maintaining all medical safety standards.'
    }
    
    # CareCredit partnership info
    carecredit_info = {
        'available': True,
        'interest_rate': '0% for 12 months',
        'minimum_amount': 5000,
        'approval_time': '5 minutes online',
        'link': 'https://www.carecredit.com/apply'  # External link
    }
    
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