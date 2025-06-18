#!/usr/bin/env python3
"""
Ultra-simple HTTP server that just serves the orbital_standalone.html file.
"""

import http.server
import socketserver
import os
import webbrowser

PORT = 8080

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Serve the standalone orbital UI"""
        if self.path == '/' or self.path == '/index.html':
            self.path = '/web/orbital_standalone.html'
            
        # Add CORS headers to prevent access denied issues
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
            
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

Handler = SimpleHandler

print(f"[INFO] Starting server at http://localhost:{PORT}")
print(f"[INFO] Press Ctrl+C to stop the server")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except:
        pass
        
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[INFO] Server stopped")
        httpd.server_close()
