#!/usr/bin/env python3
"""
Simple HTTP server for the lightweight 3D Orbital UI.
Uses Python's built-in HTTP server to serve the orbital_lite.html file.
"""

import http.server
import socketserver
import os
import webbrowser

PORT = 8888

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Serve the lightweight orbital UI"""
        if self.path == '/' or self.path == '/index.html':
            self.path = '/web/orbital_lite.html'
            
        # Add CORS headers to prevent access denied issues
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
            
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

print(f"[INFO] Starting lightweight orbital UI server at http://localhost:{PORT}")
print(f"[INFO] This version uses canvas-based rendering instead of Three.js for faster loading")
print(f"[INFO] Press Ctrl+C to stop the server")

Handler = SimpleHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        # Open browser automatically
        webbrowser.open(f"http://localhost:{PORT}")
    except:
        pass
        
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[INFO] Server stopped")
        httpd.server_close()
