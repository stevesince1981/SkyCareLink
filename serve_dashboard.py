#!/usr/bin/env python3
import http.server
import socketserver
import os
import mimetypes

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="medifly-dashboard-sandbox/dist", **kwargs)
        
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_GET(self):
        # For SPA routing, serve index.html for routes that don't exist as files
        if self.path.startswith('/phase-1') or (self.path == '/' or self.path == ''):
            self.path = '/index.html'
        super().do_GET()

PORT = 3000
Handler = DashboardHandler

print(f"Starting MediFly Dashboard Preview Server on port {PORT}")
print(f"Visit: http://localhost:{PORT}")
print("Available routes:")
print("  /          - Home page with Test button")
print("  /phase-1   - Dashboard with role toggle (Affiliate/Provider/Individual)")

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()