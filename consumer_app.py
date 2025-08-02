import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
consumer_app = Flask(__name__, template_folder='consumer_templates', static_folder='consumer_static')
consumer_app.secret_key = os.environ.get("SESSION_SECRET", "consumer-demo-key-change-in-production")

# Mock provider data
PROVIDERS = {
    'airmed': {
        'name': 'AirMed Response',
        'price': 128500,
        'eta': '3 hours',
        'description': 'ICU Certified Team',
        'details': 'Full ICU capabilities with certified critical care team. Advanced life support equipment onboard.',
        'capabilities': ['ICU Certified', 'Advanced Life Support', '24/7 Available']
    },
    'reva': {
        'name': 'REVA CriticalCare',
        'price': 112000,
        'eta': '5 hours',
        'description': 'Doctor On Board',
        'details': 'Licensed physician accompanies all flights. Specialized in critical care transport.',
        'capabilities': ['Doctor Onboard', 'Critical Care', 'Rapid Response']
    },
    'mercywings': {
        'name': 'MercyWings Global',
        'price': 102000,
        'eta': '6 hours',
        'description': 'Compassionate Care',
        'details': 'Experienced medical team focused on patient comfort and family support.',
        'capabilities': ['Family Friendly', 'Basic Life Support', 'Cost Effective']
    }
}

# Tracking stages
TRACKING_STAGES = [
    "Flight team dispatched",
    "En route to pickup location", 
    "Arrived and preparing patient",
    "Transport complete"
]

@consumer_app.route('/')
def landing():
    """Landing page with family/hospital toggle"""
    return render_template('consumer_index.html')

@consumer_app.route('/hospital')
def hospital_redirect():
    """Redirect to hospital version"""
    # In production, this would redirect to the hospital app URL
    return redirect('http://medtransportlink-prototype.replit.app')

@consumer_app.route('/intake')
def intake():
    """Family-friendly intake form"""
    session.clear()  # Start fresh
    return render_template('consumer_intake.html')

@consumer_app.route('/results', methods=['POST'])
def results():
    """Show provider options"""
    # Store form data in session
    session['pickup_location'] = request.form.get('pickup_location', '')
    session['destination'] = request.form.get('destination', '')
    session['severity'] = int(request.form.get('severity', 1))
    session['equipment'] = request.form.getlist('equipment')
    session['travel_date'] = request.form.get('travel_date', '')
    
    # Log for admin notification
    logging.info(f"Consumer quote requested: {session['pickup_location']} to {session['destination']}")
    print(f"Notification sent to admin@medifly.com: Consumer quote requested for {session['pickup_location']} to {session['destination']}")
    
    return render_template('consumer_results.html', providers=PROVIDERS)

@consumer_app.route('/confirm')
def confirm():
    """Booking confirmation"""
    provider_id = request.args.get('provider_id')
    if not provider_id or provider_id not in PROVIDERS:
        flash('Please select a valid provider.', 'error')
        return redirect(url_for('results'))
    
    session['selected_provider'] = provider_id
    provider = PROVIDERS[provider_id]
    
    return render_template('consumer_confirm.html', 
                         provider=provider, 
                         provider_id=provider_id)

@consumer_app.route('/tracking', methods=['POST'])
def tracking():
    """Flight tracking simulation"""
    # Store add-ons
    session['family_seat'] = 'family_seat' in request.form
    session['vip_cabin'] = 'vip_cabin' in request.form
    session['consent'] = 'consent' in request.form
    
    if not session.get('consent'):
        flash('Please agree to the consent terms to proceed.', 'error')
        return redirect(url_for('confirm'))
    
    # Calculate total cost
    provider = PROVIDERS[session['selected_provider']]
    total_cost = provider['price']
    if session.get('family_seat'):
        total_cost += 5000
    if session.get('vip_cabin'):
        total_cost += 10000
    
    session['total_cost'] = total_cost
    session['booking_time'] = datetime.now().isoformat()
    
    # Log booking confirmation
    logging.info(f"Consumer booking confirmed with {provider['name']}")
    print(f"Notification sent to admin@medifly.com: Consumer booking confirmed with {provider['name']}")
    
    # Initialize tracking
    session['current_stage'] = 0
    session['start_time'] = datetime.now().isoformat()
    
    return render_template('consumer_tracking.html', 
                         provider=provider,
                         stages=TRACKING_STAGES,
                         current_stage=0,
                         progress_percentage=25)

@consumer_app.route('/tracking_update')
def tracking_update():
    """AJAX endpoint for tracking updates"""
    current_stage = session.get('current_stage', 0)
    
    # Auto-advance every request (simulating 10-second intervals)
    if current_stage < len(TRACKING_STAGES) - 1:
        current_stage += 1
        session['current_stage'] = current_stage
    
    progress_percentage = min((current_stage + 1) * 25, 100)
    
    return {
        'current_stage': current_stage,
        'progress_percentage': progress_percentage,
        'status': TRACKING_STAGES[current_stage] if current_stage < len(TRACKING_STAGES) else 'Complete'
    }

@consumer_app.route('/summary')
def summary():
    """Booking completion summary"""
    if not session.get('selected_provider'):
        return redirect(url_for('landing'))
    
    provider = PROVIDERS[session['selected_provider']]
    
    # Prepare summary data
    summary_data = {
        'provider': provider,
        'pickup_location': session.get('pickup_location'),
        'destination': session.get('destination'),
        'travel_date': session.get('travel_date'),
        'total_cost': session.get('total_cost'),
        'family_seat': session.get('family_seat', False),
        'vip_cabin': session.get('vip_cabin', False),
        'booking_time': session.get('booking_time')
    }
    
    return render_template('consumer_summary.html', summary=summary_data)

@consumer_app.route('/summary_complete', methods=['POST'])
def summary_complete():
    """Handle feedback submission and clear session"""
    feedback = request.form.get('feedback', '')
    if feedback:
        logging.info(f"Consumer feedback received: {feedback}")
    
    # Clear session data
    session.clear()
    flash('Thank you for choosing MediFly! Your session data has been cleared for privacy.', 'success')
    
    return redirect(url_for('landing'))

@consumer_app.route('/admin')
def admin():
    """Admin panel for debugging"""
    return render_template('consumer_admin.html')

@consumer_app.route('/admin_login', methods=['POST'])
def admin_login():
    """Handle admin login"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'admin' and password == 'demo123':
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid credentials', 'error')
        return redirect(url_for('admin'))

@consumer_app.route('/admin_dashboard')
def admin_dashboard():
    """Admin dashboard with session data"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    # Get current session data (excluding admin flag)
    session_data = {k: v for k, v in session.items() if k != 'admin_logged_in'}
    
    return render_template('consumer_admin_dashboard.html', session_data=session_data)

if __name__ == '__main__':
    consumer_app.run(host='0.0.0.0', port=5001, debug=True)