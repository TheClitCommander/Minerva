#!/usr/bin/env python3
"""
Minerva Chat Bridge

This lightweight bridge connects the Minerva chat interface to the Think Tank system.
It creates a simple server that handles API requests from the chat interface and
forwards them to the Think Tank processor.

This implementation respects the existing Think Tank infrastructure and adds
compatibility for the floating chat component.
"""

import os
import sys
import json
import logging
import uuid
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("minerva_chat_bridge")

# Add the current directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Try to import Think Tank processing
try:
    from think_tank_consolidated import process_with_think_tank
    logger.info("Successfully imported Think Tank from consolidated module")
except ImportError:
    try:
        # Fallback to trying directly from processor module
        sys.path.append(os.path.join(os.path.dirname(current_dir), "processor"))
        from processor.think_tank import process_with_think_tank
        logger.info("Successfully imported Think Tank from processor module")
    except ImportError:
        logger.error("Failed to import Think Tank processing module")
        logger.error("Using simple echo response mode")
        
        # Define a simple echo function as fallback
        def process_with_think_tank(message, conversation_id=None, test_mode=False):
            """Simple echo function when Think Tank is not available"""
            return {
                "response": f"Echo: {message}\n\nNote: This is a fallback response because the Think Tank module could not be loaded.",
                "model_info": {"model_used": "fallback", "processing_time": 0},
                "status": "fallback"
            }

class MinervaChatRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Minerva chat bridge"""
    
    def _set_response_headers(self, content_type="application/json", status_code=200):
        """Set common headers for responses"""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')  # Enable CORS for development
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Session-ID')
        self.end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self._set_response_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        # Basic info page at the root path
        if self.path == '/' or self.path == '/index.html':
            self._set_response_headers(content_type="text/html")
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Minerva Chat Bridge</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }
                    .container { max-width: 800px; margin: 0 auto; }
                    h1 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }
                    h2 { color: #3498db; margin-top: 20px; }
                    code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
                    .endpoint { margin: 10px 0; padding: 10px; background: #f9f9f9; border-left: 4px solid #3498db; }
                    .status { padding: 10px; background: #dff0d8; color: #3c763d; border-radius: 4px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Minerva Chat Bridge</h1>
                    <div class="status">
                        <strong>Status:</strong> Running successfully
                    </div>
                    <p>
                        This server connects the Minerva chat interface with the Think Tank processing system.
                        It provides API endpoints that the chat component can use to send messages and receive
                        responses from the Think Tank.
                    </p>
                    
                    <h2>Available Endpoints:</h2>
                    <div class="endpoint">
                        <code>POST /api/think-tank</code> - Process messages with Think Tank
                    </div>
                    <div class="endpoint">
                        <code>POST /api/chat/message</code> - Legacy endpoint for chat messages (compatibility)
                    </div>
                    <div class="endpoint">
                        <code>GET /api/health</code> - Health check endpoint
                    </div>
                    
                    <h2>Server Information:</h2>
                    <p>
                        <strong>Server Port:</strong> 8080<br>
                        <strong>Version:</strong> 1.0.0<br>
                        <strong>Started:</strong> {start_time}
                    </p>
                </div>
            </body>
            </html>
            """.format(start_time=time.strftime("%Y-%m-%d %H:%M:%S"))
            
            self.wfile.write(html_content.encode())
            return
        
        # Health check endpoint
        elif self.path == '/api/health':
            self._set_response_headers()
            health_data = {
                "status": "ok",
                "service": "Minerva Chat Bridge",
                "version": "1.0.0",
                "api_endpoints": [
                    "/api/think-tank",
                    "/api/chat/message"
                ]
            }
            self.wfile.write(json.dumps(health_data).encode())
            return
        
        # Handle unknown GET requests
        self._set_response_headers(status_code=404)
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests for chat messages"""
        # Support both think-tank and chat/message endpoints for flexibility
        if self.path == '/api/think-tank' or self.path == '/api/chat/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Parse the request JSON
                request_data = json.loads(post_data.decode())
                message = request_data.get('message', '')
                conversation_id = request_data.get('conversation_id', str(uuid.uuid4()))
                
                # Get session ID from header if available
                session_id = self.headers.get('X-Session-ID', conversation_id)
                
                logger.info(f"Processing message for session {session_id[:8]}: {message[:50]}...")
                
                # Process with Think Tank
                start_time = time.time()
                result = process_with_think_tank(
                    message=message,
                    conversation_id=conversation_id,
                    test_mode=False
                )
                processing_time = time.time() - start_time
                
                # Prepare response
                response = {
                    "response": result.get("response", ""),
                    "model_info": result.get("model_info", {}),
                    "conversation_id": conversation_id,
                    "processing_time": processing_time,
                    "status": "success",
                    # Include memory info for compatibility
                    "memory_id": f"mem-{conversation_id}",
                    "memory_info": {
                        "summary": "Message processed through Think Tank",
                        "status": "active"
                    }
                }
                
                logger.info(f"Response generated in {processing_time:.2f}s")
                
                # Send response
                self._set_response_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                logger.error(f"Error processing request: {str(e)}")
                logger.error(f"Request data: {post_data.decode()[:200]}...")
                
                self._set_response_headers(status_code=500)
                error_response = {
                    "status": "error",
                    "error": str(e),
                    "message": "An error occurred while processing your request"
                }
                self.wfile.write(json.dumps(error_response).encode())
        else:
            # Handle unknown POST endpoints
            self._set_response_headers(status_code=404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

def run_server(port=8080):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MinervaChatRequestHandler)
    logger.info(f"Starting Minerva Chat Bridge on port {port}...")
    logger.info(f"Chat will connect to http://localhost:{port}/api/think-tank")
    logger.info("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        httpd.server_close()
        logger.info("Server shutdown complete")

if __name__ == "__main__":
    # Use port 8080 by default (matching the regular server)
    port = 8080
    
    # Allow custom port via command line
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port number: {sys.argv[1]}, using default port {port}")
    
    run_server(port)
