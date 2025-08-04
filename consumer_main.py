from consumer_app_updated import consumer_app as app

if __name__ == '__main__':
    print("Starting MediFly Consumer MVP with Enhanced Features...")
    print("Features: AI Commands, Dynamic Pricing, Provider Blurring, VIP Upgrades, Same-day Upcharge")
    app.run(host='0.0.0.0', port=5001, debug=True)