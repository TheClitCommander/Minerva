#!/usr/bin/env python3
"""
Minerva API Server Test Script
This simple test server helps diagnose connectivity issues with the ThinkTank API.
"""

import http.server
import socketserver
import json
import sys
from datetime import datetime

# Configuration
PORT = 7070  # Run on a different port from the main server

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add comprehensive CORS headers to fix browser issues
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 
                         'Content-Type, X-Session-ID, X-API-Version, Origin, X-Requested-With, Accept')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Max-Age', '3600')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests properly
        print('Received OPTIONS request from', self.client_address)
        self.send_response(200)
        self.end_headers()
        # Return empty body for OPTIONS
        self.wfile.write(b'')
    
    def do_GET(self):
        # Simplified API for status checks
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'status': 'ok',
                'server': 'Minerva Test Server',
                'time': datetime.now().isoformat(),
                'message': 'The test server is working correctly'
            }
            
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Default to serving static files
        return super().do_GET()
    
    def do_POST(self):
        # Handle API requests
        if self.path == '/api/think-tank' or self.path == '/api/chat/message':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                request = json.loads(post_data)
                print(f"Received request: {request}")
                
                # Create a response with model info to properly simulate ThinkTank
                response = {
                    'status': 'success',
                    'message': f"Received: {request.get('message', '[No message]')}",
                    'conversation_id': request.get('conversation_id', 'test-session'),
                    'server_timestamp': datetime.now().isoformat(),
                    'response': f"This is a test response to: '{request.get('message', '[No message]')}'. The ThinkTank connection is working properly. Your conversation is being remembered.",
                    'model_info': {
                        'model_used': 'test_model',
                        'reasoning': 'This is a test response from the server',
                        'rankings': [
                            {'model': 'GPT-4', 'score': 0.9, 'quality_score': 0.92, 'relevance_score': 0.88, 'technical_score': 0.91, 'selected': True},
                            {'model': 'Claude', 'score': 0.85, 'quality_score': 0.86, 'relevance_score': 0.84, 'technical_score': 0.85, 'selected': False}
                        ],
                        'blending': {'enabled': True, 'method': 'weighted'}
                    }
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                print(f"Error processing request: {e}")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'error',
                    'message': str(e)
                }).encode())
            
            return
        
        # Default response for other POST requests
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'status': 'error',
            'message': 'Not found'
        }).encode())

def run_server():
    try:
        with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
            print(f"Starting Minerva test server on port {PORT}...")
            print(f"Test server at: http://localhost:{PORT}/")
            print("Test API endpoints:")
            print(f"  - GET:  http://localhost:{PORT}/api/status")
            print(f"  - POST: http://localhost:{PORT}/api/think-tank")
            print(f"  - POST: http://localhost:{PORT}/api/chat/message")
            print("\nPress Ctrl+C to stop the server")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_server())
