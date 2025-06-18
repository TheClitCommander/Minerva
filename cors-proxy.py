#!/usr/bin/env python3
"""
CORS Proxy for Minerva Think Tank API
This script creates a simple proxy server that adds CORS headers to requests
going to the Think Tank API server on port 8090.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import json
import sys
from datetime import datetime

# Configuration
PROXY_PORT = 7075  # Port for our proxy
TARGET_API = "http://localhost:8090/api/think-tank"  # The Think Tank API we're proxying to

class CORSProxyHandler(http.server.BaseHTTPRequestHandler):
    def add_cors_headers(self):
        """Add CORS headers to the response."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 
                         'Content-Type, X-Session-ID, X-API-Version, Origin')
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.add_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        """Forward POST requests to the target API and return the response."""
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read request body
            request_body = self.rfile.read(content_length)
            
            if self.path == '/api/think-tank' or self.path == '/api/chat/message':
                # Forward to real API
                target_url = TARGET_API
                print(f"Forwarding request to: {target_url}")
                
                # Prepare headers
                headers = {
                    'Content-Type': 'application/json'
                }
                
                # Copy important headers from original request
                for header in ['X-Session-ID', 'X-API-Version']:
                    if header in self.headers:
                        headers[header] = self.headers[header]
                
                # Create request
                req = urllib.request.Request(
                    target_url, 
                    data=request_body,
                    headers=headers,
                    method='POST'
                )
                
                try:
                    # Forward the request
                    with urllib.request.urlopen(req) as response:
                        response_data = response.read()
                        status_code = response.status
                        
                        # Send response back to client
                        self.send_response(status_code)
                        self.send_header('Content-type', 'application/json')
                        self.add_cors_headers()
                        self.end_headers()
                        self.wfile.write(response_data)
                        
                        # Log successful response
                        print(f"Successfully forwarded request, response status: {status_code}")
                        
                except urllib.error.HTTPError as e:
                    # Handle HTTP errors from the target API
                    self.send_response(e.code)
                    self.send_header('Content-type', 'application/json')
                    self.add_cors_headers()
                    self.end_headers()
                    self.wfile.write(e.read())
                    print(f"Forwarding error: {e}")
                    
                except urllib.error.URLError as e:
                    # Handle connection errors
                    self.send_response(502)  # Bad Gateway
                    self.send_header('Content-type', 'application/json')
                    self.add_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'error',
                        'message': f"Error connecting to Think Tank API: {str(e)}",
                        'error': str(e)
                    }).encode())
                    print(f"Connection error: {e}")
            
            else:
                # For other paths, return 404
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.add_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'error',
                    'message': 'Invalid API endpoint'
                }).encode())
        
        except Exception as e:
            # Handle any other errors
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.add_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'error',
                'message': f"Internal proxy error: {str(e)}"
            }).encode())
            print(f"Proxy error: {e}")
    
    def do_GET(self):
        """Handle GET requests for status checks."""
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.add_cors_headers()
            self.end_headers()
            
            # Try to connect to target API to check if it's up
            try:
                urllib.request.urlopen(TARGET_API, timeout=2)
                api_status = "reachable"
            except:
                api_status = "unreachable"
            
            response = {
                'status': 'ok',
                'server': 'Minerva CORS Proxy',
                'target_api': TARGET_API,
                'target_status': api_status,
                'time': datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response).encode())
        else:
            # Default 404 for other GET requests
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.add_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'error',
                'message': 'Not found'
            }).encode())

def run_proxy():
    try:
        with socketserver.TCPServer(("", PROXY_PORT), CORSProxyHandler) as httpd:
            print(f"Starting Minerva CORS Proxy on port {PROXY_PORT}...")
            print(f"Forwarding requests to {TARGET_API}")
            print(f"Test the proxy at: http://localhost:{PROXY_PORT}/status")
            print("\nPress Ctrl+C to stop the proxy")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped")
    except Exception as e:
        print(f"Error starting proxy: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_proxy())
