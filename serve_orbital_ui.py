#!/usr/bin/env python3
"""
Simple HTTP server for testing the 3D Orbital UI.
This uses Python's built-in HTTP server, which doesn't require Flask.
"""

import http.server
import socketserver
import os
import webbrowser
from urllib.parse import parse_qs, urlparse

PORT = 8090

# Change directory to the static files location
os.chdir("web")

class OrbitalUIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        # Redirect root to orbital_home_3d.html
        if self.path == '/' or self.path == '/orbital/3d':
            self.path = '/templates/orbital_home_3d.html'
        elif self.path == '/orbital':
            self.path = '/templates/orbital_home.html'
            
        # Add CORS headers
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
            
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

Handler = OrbitalUIHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("[INFO] Serving 3D Orbital UI at port", PORT)
    print(f"[INFO] Open http://localhost:{PORT} or http://localhost:{PORT}/orbital/3d in your browser")
    
    # Try to open the browser automatically
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except:
        pass
        
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[INFO] Server stopped by user")
        httpd.server_close()
