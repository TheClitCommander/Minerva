#!/usr/bin/env python3
"""
Simple HTTP server for Minerva Think Tank UI
"""
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

class MinervaHandler(SimpleHTTPRequestHandler):
    """Custom handler that serves the Think Tank UI HTML file"""
    
    def do_GET(self):
        """Handle GET requests"""
        # Default to minerva_central.html if accessing root
        if self.path == '/' or self.path == '/index.html':
            self.path = '/minerva_central.html'
        
        # Handle static files
        return SimpleHTTPRequestHandler.do_GET(self)

def run_server(port=8091):
    """Run the HTTP server"""
    # Change to the web directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, MinervaHandler)
    print(f"Starting Minerva Think Tank UI server on port {port}...")
    print(f"Open your browser to http://localhost:{port}/")
    print("Press Ctrl+C to stop the server.")
    httpd.serve_forever()

if __name__ == "__main__":
    port = 8091
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}, using default port 8091")
    
    run_server(port)
