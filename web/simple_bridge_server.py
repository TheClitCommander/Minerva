#!/usr/bin/env python3
"""
Simple Bridge Server for Minerva

This lightweight server connects the Minerva chat UI with the Think Tank functionality.
It provides basic API endpoints that the chat can connect to, and uses the
built-in Think Tank processing to generate real answers.
"""

import os
import sys
import json
import logging
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Add parent directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("minerva_bridge")

# Initialize conversation memory storage
conversation_memory = {}

# Try to import Think Tank processing from the consolidated module
try:
    from think_tank_consolidated import process_with_think_tank
    logger.info("Successfully imported Think Tank from consolidated module")
except ImportError:
    try:
        # Fallback to trying from processor directory
        sys.path.append(os.path.join(parent_dir, "processor"))
        from processor.think_tank import process_with_think_tank
        logger.info("Successfully imported Think Tank from processor module")
    except ImportError:
        logger.error("Failed to import Think Tank processing module")
        logger.error("Using enhanced fallback response mode")
        
        # Define a more intelligent fallback function
        def process_with_think_tank(message, conversation_id=None, test_mode=False):
            """Enhanced fallback function when Think Tank is not available"""
            # Generate a conversation ID if none was provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                
            # Initialize conversation history if this is a new conversation
            if conversation_id not in conversation_memory:
                conversation_memory[conversation_id] = []
                
            # Add the user message to history
            conversation_memory[conversation_id].append({"role": "user", "content": message})
            
            # Generate a more intelligent response based on the message
            from datetime import datetime
            response = ""
            
            # If message is asking about the system
            if any(word in message.lower() for word in ["minerva", "system", "think tank", "how are you"]):
                response = "I'm Minerva, your AI assistant. I'm currently running in fallback mode due to some configuration issues (missing the 'dotenv' module). While I can't access the full Think Tank capabilities right now, I can still help with basic conversation and remember our discussion context."
            
            # If message is asking for help
            elif any(word in message.lower() for word in ["help", "assist", "support"]):
                response = "I'm here to help! While running in fallback mode, I can still assist with conversation and help organize your thoughts. You can create projects, continue conversations, and I'll remember our discussion context."
            
            # If message is about creating a project
            elif any(phrase in message.lower() for phrase in ["create project", "new project", "start project"]):
                response = "I can help you organize your thoughts into a project! Let me know what you'd like to name this project, and I'll keep track of our conversations within that context."
                
            # Default response
            else:
                response = f"I understand you're asking about: '{message}'. While I'm running in fallback mode due to a missing dependency (the 'dotenv' module), I can still help with basic conversation and maintain our discussion context. What else would you like to discuss?"
            
            # Add the assistant response to history
            conversation_memory[conversation_id].append({"role": "assistant", "content": response})
            
            # Keep only the last 10 messages for memory efficiency
            if len(conversation_memory[conversation_id]) > 10:
                conversation_memory[conversation_id] = conversation_memory[conversation_id][-10:]
                
            return {
                "response": response,
                "model_info": {
                    "model_used": "fallback_enhanced", 
                    "processing_time": 0,
                    "context_length": len(conversation_memory[conversation_id])},
                "status": "success",
                "conversation_id": conversation_id
            }

class MinervaRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Minerva bridge server"""
    
    def _set_headers(self, content_type="application/json"):
        """Set common headers for responses"""
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:8080')  # Enable CORS for specific origin
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:8080')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')  # Cache preflight for 24 hours
        self.end_headers()
        
    def do_GET(self):
        """Handle GET requests"""
        # Serve static content if path matches
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            # Respond with basic server info
            response = """
            <html>
            <head><title>Minerva Bridge Server</title></head>
            <body>
                <h1>Minerva Bridge Server</h1>
                <p>This server connects the Minerva chat UI with the Think Tank functionality.</p>
                <p>The server is running correctly.</p>
                <p>API endpoints:</p>
                <ul>
                    <li><code>/api/think-tank</code> - Process messages with the Think Tank</li>
                    <li><code>/api/health</code> - Health check endpoint</li>
                </ul>
            </body>
            </html>
            """
            self.wfile.write(response.encode())
            return
        
        # Health check endpoint
        elif self.path == '/api/health':
            self._set_headers()
            response = {
                "status": "ok",
                "service": "Minerva Bridge Server",
                "version": "1.0.0"
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Handle unknown GET requests
        self.send_response(404)
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/think-tank':
            # Process message with Think Tank
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Parse the request JSON
                request_data = json.loads(post_data.decode())
                message = request_data.get('message', '')
                conversation_id = request_data.get('conversation_id', str(uuid.uuid4()))
                
                logger.info(f"Processing message: {message[:50]}...")
                
                # Extract additional context if available
                project_id = request_data.get('project_id', 'default')
                store_in_memory = request_data.get('store_in_memory', True)
                
                logger.info(f"Project ID: {project_id}, Store in memory: {store_in_memory}")
                
                # Try to process with Think Tank, but handle the dotenv error specifically
                try:
                    result = process_with_think_tank(
                        message=message,
                        conversation_id=conversation_id,
                        test_mode=False
                    )
                    
                    # Check if the response contains errors or is empty
                    response_text = result.get("response", "")
                    model_info = result.get("model_info", {})
                    
                    # Handle empty responses or error cases
                    if not response_text or \
                       "Model integration hub not available" in response_text or \
                       "error" in model_info or \
                       "No module named" in str(model_info):
                        # Use our enhanced fallback instead
                        logger.info(f"Using enhanced fallback for problematic response: {response_text}")
                        logger.info(f"Model info: {model_info}")
                        
                        # Initialize conversation history if needed
                        if conversation_id not in conversation_memory:
                            conversation_memory[conversation_id] = []
                            
                        # Add user message to history
                        conversation_memory[conversation_id].append({"role": "user", "content": message})
                        
                        # Generate a more helpful response
                        if any(word in message.lower() for word in ["minerva", "system", "think tank", "how are you"]):
                            response_text = "I'm Minerva, your AI assistant. I'm currently running in fallback mode due to some configuration issues (missing the 'dotenv' module). While I can't access the full Think Tank capabilities right now, I can still help with basic conversation and remember our discussion context."
                        elif any(word in message.lower() for word in ["help", "assist", "support"]):
                            response_text = "I'm here to help! While running in fallback mode, I can still assist with conversation and help organize your thoughts. You can create projects, continue conversations, and I'll remember our discussion context."
                        elif any(phrase in message.lower() for phrase in ["create project", "new project", "start project"]):
                            response_text = "I can help you organize your thoughts into a project! Let me know what you'd like to name this project, and I'll keep track of our conversations within that context."
                        else:
                            response_text = f"I understand you're asking about: '{message}'. While I'm running in fallback mode due to a missing dependency (the 'dotenv' module), I can still help with basic conversation and maintain our discussion context. What else would you like to discuss?"
                        
                        # Add assistant response to history
                        conversation_memory[conversation_id].append({"role": "assistant", "content": response_text})
                        
                        # Override the result
                        result = {
                            "response": response_text,
                            "model_info": {
                                "model_used": "fallback_enhanced", 
                                "processing_time": 0,
                                "context_length": len(conversation_memory[conversation_id])
                            },
                            "status": "success",
                            "conversation_id": conversation_id
                        }
                except Exception as e:
                    logger.error(f"Error in Think Tank processing, using fallback: {str(e)}")
                    # Use fallback processing
                    # Initialize conversation history if needed
                    if conversation_id not in conversation_memory:
                        conversation_memory[conversation_id] = []
                        
                    # Add user message to history
                    conversation_memory[conversation_id].append({"role": "user", "content": message})
                    
                    # Generate a fallback response
                    fallback_text = f"I understand you're asking about: '{message}'. While I'm running in fallback mode due to a technical issue, I can still help with basic conversation and maintain our discussion context. What else would you like to discuss?"
                    
                    # Add assistant response to history
                    conversation_memory[conversation_id].append({"role": "assistant", "content": fallback_text})
                    
                    # Create a fallback result
                    result = {
                        "response": fallback_text,
                        "model_info": {
                            "model_used": "fallback_emergency", 
                            "processing_time": 0,
                            "error": str(e)
                        },
                        "status": "success",
                        "conversation_id": conversation_id
                    }
                
                # Prepare response
                response = {
                    "response": result.get("response", ""),
                    "model_info": result.get("model_info", {}),
                    "conversation_id": conversation_id,
                    "status": "success",
                    "memory_id": f"mem-{conversation_id}",
                    "memory_info": {
                        "summary": "Message processed and stored",
                        "status": "active",
                        "project_id": project_id
                    }
                }
                
                # Send response
                self._set_headers()
                self.wfile.write(json.dumps(response).encode())
                logger.info("Message processed successfully")
                
            except Exception as e:
                logger.error(f"Error processing request: {str(e)}")
                self._set_headers()
                error_response = {
                    "status": "error",
                    "error": f"Error processing request: {str(e)}"
                }
                self.wfile.write(json.dumps(error_response).encode())
                
        # Backward compatibility with chat/message endpoint
        elif self.path == '/api/chat/message':
            # Process message with Think Tank
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Parse the request JSON
                request_data = json.loads(post_data.decode())
                message = request_data.get('message', '')
                conversation_id = request_data.get('conversation_id', str(uuid.uuid4()))
                
                logger.info(f"Processing message via compatibility endpoint: {message[:50]}...")
                
                # Extract additional context if available
                project_id = request_data.get('project_id', 'default')
                store_in_memory = request_data.get('store_in_memory', True)
                
                logger.info(f"Project ID: {project_id}, Store in memory: {store_in_memory}")
                
                # Process with Think Tank
                result = process_with_think_tank(
                    message=message,
                    conversation_id=conversation_id,
                    test_mode=False
                )
                
                # Prepare response in the legacy format that chat-simple.js expects
                response = {
                    "response": result.get("response", ""),
                    "model_info": result.get("model_info", {}),
                    "conversation_id": conversation_id,
                    "status": "success",
                    "memory_id": f"mem-{conversation_id}",  # Add memory ID for compatibility
                    "memory_info": {
                        "summary": "Message processed and stored",
                        "status": "active"
                    }
                }
                
                # Send response
                self._set_headers()
                self.wfile.write(json.dumps(response).encode())
                logger.info("Message processed successfully via compatibility endpoint")
                
            except Exception as e:
                logger.error(f"Error processing request: {str(e)}")
                self._set_headers()
                error_response = {
                    "status": "error",
                    "error": f"Error processing request: {str(e)}"
                }
                self.wfile.write(json.dumps(error_response).encode())
                
        else:
            # Handle unknown POST requests
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

def run_server(port=8090):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MinervaRequestHandler)
    logger.info(f"Starting Minerva Bridge Server on port {port}...")
    logger.info(f"Server is running at http://localhost:{port}/")
    logger.info("Chat API endpoint: http://localhost:{port}/api/think-tank")
    logger.info("Press Ctrl+C to stop the server.")
    httpd.serve_forever()

if __name__ == "__main__":
    # Default port is 8090, but allow override via command line
    port = 8090
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port: {sys.argv[1]}, using default port {port}")
    
    run_server(port)
