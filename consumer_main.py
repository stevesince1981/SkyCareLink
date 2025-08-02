from consumer_app import consumer_app as app

if __name__ == '__main__':
    print("Starting MediFly Consumer MVP...")
    app.run(host='0.0.0.0', port=5001, debug=True)