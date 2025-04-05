#!/usr/bin/env python3
"""
Minerva Working Server - Minimal version to get the site back up
"""

import os
import sys
import json
import logging
import uuid
import traceback
import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("minerva_working")

# Initialize conversation memory storage
conversation_memory = {}
MEMORY_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conversation_memory.json')

def save_memory_to_file():
    """Save the conversation memory to a JSON file"""
    try:
        if not conversation_memory:
            logger.warning("No conversations to save, skipping memory save")
            return False
        
        with open(MEMORY_FILE_PATH, 'w') as f:
            json.dump(conversation_memory, f, indent=2)
        
        logger.info(f"Saved {len(conversation_memory)} conversations to memory file")
        return True
    except Exception as e:
        logger.error(f"Error saving memory to file: {str(e)}")
        return False

def load_memory_from_file():
    """Load conversation memory from JSON file if it exists"""
    global conversation_memory
    try:
        if os.path.exists(MEMORY_FILE_PATH):
            with open(MEMORY_FILE_PATH, 'r') as f:
                loaded_memory = json.load(f)
                conversation_memory.update(loaded_memory)
            logger.info(f"Loaded {len(conversation_memory)} conversations from memory file")
            return True
        else:
            logger.info("No memory file found, starting with empty memory")
            return False
    except Exception as e:
        logger.error(f"Error loading memory from file: {str(e)}")
        return False

def process_message(message, conversation_id=None):
    """Simple message processor that works without dependencies"""
    if not conversation_id:
        conversation_id = f"conv-{uuid.uuid4()}"
    
    logger.info(f"Processing message: {message[:50]}...")
    
    # Generate a simple response
    response_text = f"I understand your message about '{message[:30]}...'. This is a simplified version of Minerva that maintains conversation memory and core functionality."
    
    return {
        "response": response_text,
        "conversation_id": conversation_id,
        "model_info": {
            "model_used": "simple_model",
            "processing_time": 0.1,
            "models_used": ["simple_model"]
        },
        "status": "success"
    }

class MinervaHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for Minerva with minimal functionality"""
    
    def _set_headers(self, status_code=200, content_type="application/json"):
        """Set common headers for responses"""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests for static files"""
        # Default to index.html if accessing root
        if self.path == '/':
            self.path = '/index.html'
        
        # Handle static files as normal
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        """Handle POST requests for API endpoints"""
        parsed_path = urlparse(self.path)
        
        # Process ThinkTank API request
        if parsed_path.path == "/api/think-tank":
            self.handle_think_tank_request()
        # Process project conversion request
        elif parsed_path.path == "/api/convert-to-project":
            self.handle_simple_response("Project conversion functionality is available in the full version")
        else:
            self.send_error(404, "API endpoint not found")
    
    def handle_simple_response(self, message):
        """Handle a simple response to any endpoint"""
        self._set_headers()
        response = {
            "status": "success",
            "message": message
        }
        self.wfile.write(json.dumps(response).encode())
    
    def handle_think_tank_request(self):
        """Handle direct requests to the ThinkTank API with memory integration"""
        try:
            # Get request body size
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read and parse request body
            request_body = self.rfile.read(content_length).decode('utf-8')
            request_data = json.loads(request_body)
            
            # Extract message and other data from request
            message = request_data.get("message", "")
            conversation_id = request_data.get("conversation_id", f"conv-{uuid.uuid4()}")
            store_in_memory = request_data.get("store_in_memory", True)
            
            logger.info(f"Received ThinkTank request: {message[:50]}...")
            logger.info(f"Conversation ID: {conversation_id}")
            
            # Initialize memory for this conversation if needed
            if conversation_id not in conversation_memory:
                conversation_memory[conversation_id] = []
            
            # Add current message to memory
            if store_in_memory:
                conversation_memory[conversation_id].append({
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                save_memory_to_file()
            
            # Process message with simple processor
            result = process_message(message, conversation_id)
            
            # Add response to memory storage
            if store_in_memory and "response" in result:
                conversation_memory[conversation_id].append({
                    "role": "assistant",
                    "content": result["response"],
                    "timestamp": datetime.datetime.now().isoformat()
                })
                save_memory_to_file()
                
                # Add memory info to response
                result["memory_info"] = {
                    "conversation_id": conversation_id,
                    "message_count": len(conversation_memory[conversation_id])
                }
            
            # Add project conversion capability flag
            result["canCreateProject"] = True
            
            # Send response
            self._set_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error handling ThinkTank request: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Send error response
            self._set_headers(500)
            error_response = {
                "status": "error",
                "message": "An error occurred while processing your request",
                "error_details": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

def run_server(port=8080):
    """Start the Minerva Working server"""
    # Set the current directory to the location of this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Load existing conversation memory on startup
    load_memory_from_file()
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, MinervaHandler)
    
    logger.info(f"Starting Minerva Working server on port {port}")
    logger.info(f"Open your browser to http://localhost:{port}/")
    logger.info("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down, saving memory...")
        save_memory_to_file()
        logger.info("Memory saved. Goodbye!")

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port: {sys.argv[1]}, using default port 8080")
    
    run_server(port)
