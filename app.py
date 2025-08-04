import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "medifly_demo_key_2025")

# Simple user accounts for demo
DEMO_USERS = {
    'family_user': {'password': 'demo123', 'role': 'family', 'name': 'Sarah Johnson'},
    'hospital_staff': {'password': 'demo123', 'role': 'hospital', 'name': 'Dr. Michael Chen'},
    'provider': {'password': 'demo123', 'role': 'provider', 'name': 'Captain Lisa Martinez'},
    'mvp_user': {'password': 'demo123', 'role': 'mvp', 'name': 'Alex Thompson'},
    'admin': {'password': 'demo123', 'role': 'admin', 'name': 'Admin User'}
}

# Mock provider data
PROVIDERS = {
    'provider_1': {
        'name': 'AirMed Response',
        'price': 128500,
        'eta': '3h',
        'description': 'ICU Certified',
        'details': 'Full ICU-level care with certified critical care team'
    },
    'provider_2': {
        'name': 'REVA CriticalCare Jet',
        'price': 112000,
        'eta': '5h', 
        'description': 'Doctor onboard',
        'details': 'Medical doctor and nurse team available for transport'
    },
    'provider_3': {
        'name': 'MercyWings Global',
        'price': 102000,
        'eta': '6h',
        'description': 'Basic evac',
        'details': 'Standard medical evacuation with basic life support'
    }
}

# Tracking stages
TRACKING_STAGES = ['Dispatched', 'En Route', 'Arrived', 'Complete']

@app.route('/')
def index():
    """Landing page with hero content, chatbot widget and login access"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with role selection"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username in DEMO_USERS and DEMO_USERS[username]['password'] == password:
            session['logged_in'] = True
            session['user_role'] = DEMO_USERS[username]['role']
            session['user_name'] = DEMO_USERS[username]['name']
            session['username'] = username
            
            flash(f'Welcome, {DEMO_USERS[username]["name"]}!', 'success')
            
            # Redirect based on role
            if DEMO_USERS[username]['role'] == 'admin':
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    """Handle login authentication from homepage form"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if username in DEMO_USERS and DEMO_USERS[username]['password'] == password:
        session['logged_in'] = True
        session['user_role'] = DEMO_USERS[username]['role']
        session['user_name'] = DEMO_USERS[username]['name']
        session['username'] = username
        
        flash(f'Welcome, {DEMO_USERS[username]["name"]}!', 'success')
        
        # Redirect based on role
        if DEMO_USERS[username]['role'] == 'admin':
            return redirect(url_for('admin_panel'))
        else:
            return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password.', 'error')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Role-based dashboard"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_role = session.get('user_role')
    user_name = session.get('user_name')
    
    dashboard_data = {
        'user_name': user_name,
        'user_role': user_role,
        'total_bookings': 7,
        'total_revenue': 847500,
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    return render_template('dashboard.html', **dashboard_data)

@app.route('/admin_panel')
def admin_panel():
    """Admin panel with comprehensive data"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    # Accurate revenue metrics for 7 bookings
    stats = {
        'total_bookings': 7,
        'total_revenue': 847500,  # $128.5k + $112k + $102k + $95k + $118k + $145k + $147k
        'unique_visits': 245,
        'conversion_rate': 0.029,  # 7/245 = 2.9%
        'customer_satisfaction': 0.98
    }
    
    return render_template('admin_panel.html', stats=stats)

@app.route('/admin_storyboard')
def admin_storyboard():
    """Admin feature storyboard demonstration"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    booking_stats = {
        'total_bookings': 7,
        'total_revenue': 847500,
        'goal_revenue': 1000000,
        'conversion_rate': 0.029
    }
    
    return render_template('admin_storyboard.html', booking_stats=booking_stats)

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/intake', methods=['GET', 'POST'])
def intake():
    """Multi-step intake form for patient transport details"""
    if request.method == 'POST':
        # Store form data in session
        session['patient_data'] = {
            'current_location': request.form.get('current_location'),
            'destination': request.form.get('destination'),
            'severity': request.form.get('severity'),
            'equipment': request.form.getlist('equipment'),
            'departure_date': request.form.get('departure_date'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Console logging for admin notification
        print(f"Notification sent to admin@medifly.com: Quote requested for {session['patient_data']['current_location']} to {session['patient_data']['destination']}")
        
        return redirect(url_for('results'))
    
    return render_template('intake.html')

@app.route('/results')
def results():
    """Display quote options from mock providers"""
    if 'patient_data' not in session:
        flash('Please complete the intake form first.', 'warning')
        return redirect(url_for('intake'))
    
    return render_template('results.html', providers=PROVIDERS)

@app.route('/confirm')
def confirm():
    """Confirmation page with provider details and add-ons"""
    provider_id = request.args.get('provider_id')
    
    if not provider_id or provider_id not in PROVIDERS:
        flash('Invalid provider selection.', 'error')
        return redirect(url_for('results'))
    
    if 'patient_data' not in session:
        flash('Please complete the intake form first.', 'warning')
        return redirect(url_for('intake'))
    
    session['selected_provider'] = provider_id
    provider = PROVIDERS[provider_id]
    
    return render_template('confirm.html', provider=provider, patient_data=session['patient_data'])

@app.route('/finalize', methods=['POST'])
def finalize():
    """Process final booking confirmation"""
    # Store add-ons and consent
    session['add_ons'] = {
        'family_seat': 'family_seat' in request.form,
        'vip_cabin': 'vip_cabin' in request.form,
        'consent_given': 'consent' in request.form
    }
    
    if not session['add_ons']['consent_given']:
        flash('Consent is required to proceed with booking.', 'error')
        return redirect(url_for('confirm'))
    
    # Initialize tracking
    session['tracking'] = {
        'stage': 0,  # Index in TRACKING_STAGES
        'start_time': datetime.now().isoformat(),
        'last_update': datetime.now().isoformat()
    }
    
    # Console logging for admin notification
    provider_name = PROVIDERS[session['selected_provider']]['name']
    print(f"Notification sent to admin@medifly.com: Booking confirmed with {provider_name}")
    
    return redirect(url_for('tracking'))

@app.route('/tracking')
def tracking():
    """Mock flight tracker with progress updates"""
    if 'tracking' not in session:
        flash('No active booking found.', 'warning')
        return redirect(url_for('index'))
    
    # Auto-advance tracking stage based on time elapsed
    start_time = datetime.fromisoformat(session['tracking']['start_time'])
    elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
    
    # Advance stage every 2 minutes for demo purposes
    new_stage = min(len(TRACKING_STAGES) - 1, int(elapsed_minutes / 2))
    if new_stage > session['tracking']['stage']:
        session['tracking']['stage'] = new_stage
        session['tracking']['last_update'] = datetime.now().isoformat()
    
    current_stage = session['tracking']['stage']
    progress_percentage = (current_stage / (len(TRACKING_STAGES) - 1)) * 100
    
    return render_template('tracking.html', 
                         stages=TRACKING_STAGES,
                         current_stage=current_stage,
                         progress_percentage=progress_percentage,
                         provider=PROVIDERS[session['selected_provider']])

@app.route('/complete_flight')
def complete_flight():
    """Mark flight as complete and redirect to summary"""
    if 'tracking' in session:
        session['tracking']['stage'] = len(TRACKING_STAGES) - 1
    return redirect(url_for('summary'))

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    """Final summary page with feedback option"""
    if request.method == 'POST':
        feedback = request.form.get('feedback')
        if feedback:
            # Console logging for admin notification
            print(f"Notification sent to admin@medifly.com: Feedback received - {feedback[:50]}...")
            flash('Thank you for your feedback!', 'success')
    
    # Calculate total cost including add-ons
    base_cost = PROVIDERS[session.get('selected_provider', 'provider_1')]['price']
    add_on_cost = 0
    
    if session.get('add_ons', {}).get('family_seat'):
        add_on_cost += 5000
    if session.get('add_ons', {}).get('vip_cabin'):
        add_on_cost += 10000
    
    total_cost = base_cost + add_on_cost
    
    return render_template('summary.html', 
                         provider=PROVIDERS[session.get('selected_provider', 'provider_1')],
                         patient_data=session.get('patient_data', {}),
                         add_ons=session.get('add_ons', {}),
                         total_cost=total_cost)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Password-protected admin route for debugging"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'demo123':
            session['admin_authenticated'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials', 'error')
    
    if not session.get('admin_authenticated'):
        return render_template('admin.html', authenticated=False)
    
    # Show session data for debugging
    return render_template('admin.html', 
                         authenticated=True,
                         session_data=dict(session))

@app.route('/logout_admin')
def logout_admin():
    """Logout from admin panel"""
    session.pop('admin_authenticated', None)
    return redirect(url_for('index'))

@app.route('/clear_session')
def clear_session():
    """Clear all session data"""
    session.clear()
    flash('Session cleared successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/api/tracking_status')
def tracking_status():
    """API endpoint for real-time tracking updates"""
    if 'tracking' not in session:
        return jsonify({'error': 'No active tracking'})
    
    # Auto-advance tracking stage
    start_time = datetime.fromisoformat(session['tracking']['start_time'])
    elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
    
    new_stage = min(len(TRACKING_STAGES) - 1, int(elapsed_minutes / 2))
    if new_stage > session['tracking']['stage']:
        session['tracking']['stage'] = new_stage
        session['tracking']['last_update'] = datetime.now().isoformat()
    
    return jsonify({
        'stage': session['tracking']['stage'],
        'stage_name': TRACKING_STAGES[session['tracking']['stage']],
        'progress': (session['tracking']['stage'] / (len(TRACKING_STAGES) - 1)) * 100
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
