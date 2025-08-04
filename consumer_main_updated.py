#!/usr/bin/env python3
"""
MediFly Consumer MVP - Enhanced Version
Updated with all new features from requirements:
- Critical/Non-Critical/MVP transport types
- Dynamic equipment pricing
- Address validation (Google Places API stub)
- Priority partner animations
- AI command processing
- Same-day upcharge handling
- Provider name blurring
- Partnership integration (CareCredit)
- Enhanced VIP cabin descriptions
- HIPAA-compliant data handling
"""

from consumer_app_updated import consumer_app

if __name__ == '__main__':
    consumer_app.run(host='0.0.0.0', port=5001, debug=True)