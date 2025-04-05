#!/usr/bin/env python3
"""
Minerva Central Server - Direct ThinkTank Integration

This server combines static file serving with direct ThinkTank API handling,
eliminating the need for a separate bridge server.
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
logger = logging.getLogger("minerva_central")

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Initialize conversation memory storage
conversation_memory = {}
debug_request_count = 0

# Memory file paths
MEMORY_FILE_PATH = os.path.join(current_dir, 'conversation_memory.json')
PROJECT_MEMORY_PATH = os.path.join(current_dir, 'project_memory.json')

def save_memory_to_file():
    """Save the conversation memory to a JSON file"""
    try:
        # Only save if we have actual conversations
        if not conversation_memory:
            logger.warning("No conversations to save, skipping memory save")
            return False
        
        # Debug log to see what's being saved
        conversation_count = len(conversation_memory)
        conversation_ids = list(conversation_memory.keys())
        logger.info(f"💾 Saving {conversation_count} conversations: {conversation_ids}")
        
        # Make sure directory exists
        os.makedirs(os.path.dirname(MEMORY_FILE_PATH), exist_ok=True)
        
        # Save the file with human-readable formatting
        with open(MEMORY_FILE_PATH, 'w') as f:
            json.dump(conversation_memory, f, indent=2)
        
        # Verify the file was written
        if os.path.exists(MEMORY_FILE_PATH):
            file_size = os.path.getsize(MEMORY_FILE_PATH)
            logger.info(f"✅ Saved {conversation_count} conversations to {MEMORY_FILE_PATH} ({file_size} bytes)")
            return True
        else:
            logger.error(f"❌ Failed to create memory file at {MEMORY_FILE_PATH}")
            return False
    except Exception as e:
        logger.error(f"❌ Error saving memory to file: {str(e)}")
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

def load_projects_from_file():
    """Load project memory from a JSON file"""
    try:
        if os.path.exists(PROJECT_MEMORY_PATH):
            with open(PROJECT_MEMORY_PATH, 'r') as f:
                loaded_projects = json.load(f)
                logger.info(f"Loaded {len(loaded_projects)} projects from project memory file")
                return loaded_projects
        else:
            logger.info(f"Project memory file not found at {PROJECT_MEMORY_PATH}, starting with empty projects")
            return {}
    except Exception as e:
        logger.error(f"Error loading projects from file: {str(e)}")
        return {}

def save_project_to_file(project_data):
    """Save project data to a JSON file"""
    try:
        # Load existing projects
        existing_projects = load_projects_from_file()
        
        # Update with new project data
        existing_projects.update(project_data)
        
        # Make sure directory exists
        os.makedirs(os.path.dirname(PROJECT_MEMORY_PATH), exist_ok=True)
        
        # Save to file
        with open(PROJECT_MEMORY_PATH, 'w') as f:
            json.dump(existing_projects, f, indent=2)
            
        logger.info(f"✅ Saved project to {PROJECT_MEMORY_PATH}")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving project to file: {str(e)}")
        return False

def convert_conversation_to_project(conversation_id, project_name, project_description=""):
    """Convert a conversation into a project and store it separately"""
    try:
        if conversation_id in conversation_memory:
            # Create project metadata
            creation_time = datetime.datetime.now().isoformat()
            
            # Format project data
            project_data = {
                project_name: {
                    "id": f"proj-{uuid.uuid4()}",
                    "name": project_name,
                    "description": project_description or f"Project created from conversation {conversation_id}",
                    "created_at": creation_time,
                    "updated_at": creation_time,
                    "conversation_source": conversation_id,
                    "conversations": [conversation_memory[conversation_id]],
                    "status": "active"
                }
            }
            
            # Save project to file
            success = save_project_to_file(project_data)
            
            if success:
                return f"✅ Conversation {conversation_id} converted into project '{project_name}'"
            else:
                return "❌ Failed to save project data"
        else:
            return f"❌ Conversation {conversation_id} not found in memory"
    except Exception as e:
        logger.error(f"Error converting conversation to project: {str(e)}")
        return f"❌ Error: {str(e)}"

# Handle environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    logger.info("Loaded environment variables from .env file")
except ImportError:
    logger.warning("dotenv package not found, continuing without loading .env file")

# Create a simple fallback processor since we might not have the enhanced_fallback module
def simple_fallback_processor(message, conversation_id=None):
    """Simplified fallback processor for when other processors fail"""
    logger.info(f"Using simple fallback processor for message: {message[:50]}...")
    
    response_text = f"I understand your message about '{message[:30]}...'. I'm currently operating in a simplified mode."
    
    return {
        "response": response_text,
        "conversation_id": conversation_id or str(uuid.uuid4()),
        "model_info": {
            "model_used": "simple_fallback",
            "processing_time": 0
        },
        "status": "success"
    }

# No external API call dependencies needed

# Define a direct Think Tank connector function that uses our consolidated module
def direct_think_tank_processor(message, conversation_id=None, test_mode=False):
    """Direct connection to Think Tank processor without making a recursive API call"""
    # Generate a conversation ID if none was provided
    if not conversation_id:
        conversation_id = f"conv-{uuid.uuid4()}"
        
    # Log the direct processing call
    logger.info(f"Directly calling Think Tank processor for message: {message[:50]}...")
    logger.info(f"Using conversation ID: {conversation_id}")
    
    try:
        # Import the processing function if available
        from think_tank_consolidated import process_with_think_tank as think_tank_processor
        
        # Use the imported processor directly (no API call)
        logger.info("Using process_with_think_tank from the consolidated module")
        result = think_tank_processor(
            message=message,
            conversation_id=conversation_id,
            test_mode=test_mode
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in direct Think Tank processor: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a fallback result
        return simple_fallback_processor(message, conversation_id)

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
        logger.error("Using direct API fallback response mode")
        
        # Use our fallback processor as the process_with_think_tank function
        process_with_think_tank = simple_fallback_processor
        logger.info("Using simple fallback processor for Think Tank processing")

class MinervaCentralHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for Minerva Central with direct ThinkTank integration"""
    
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
            self.handle_project_conversion()
        else:
            self.send_error(404, "API endpoint not found")
            
    def handle_project_conversion(self):
        """Handle project conversion requests from conversations"""
        try:
            # Get request body size
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read and parse request body
            request_body = self.rfile.read(content_length).decode('utf-8')
            request_data = json.loads(request_body)
            
            # Extract required parameters
            conversation_id = request_data.get("conversation_id", "")
            project_name = request_data.get("project_name", "")
            project_description = request_data.get("project_description", "")
            
            # Validate parameters
            if not conversation_id or not project_name:
                self._set_headers(400)  # Bad request
                response = {
                    "status": "error",
                    "message": "Missing required parameters: conversation_id and project_name are required"
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Convert conversation to project
            result = convert_conversation_to_project(conversation_id, project_name, project_description)
            
            # Set headers and return response
            self._set_headers()
            response = {
                "status": "success" if "✅" in result else "error",
                "message": result,
                "conversation_id": conversation_id,
                "project_name": project_name
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error handling project conversion: {str(e)}")
            traceback.print_exc()
            
            # Set headers for error response
            self._set_headers(500)  # Internal server error
            response = {
                "status": "error",
                "message": f"Server error: {str(e)}"
            }
            self.wfile.write(json.dumps(response).encode())
    
    def handle_think_tank_request(self):
        """Handle direct requests to the ThinkTank API with memory and conversation integration"""
        try:
            # Get request body size
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read and parse request body
            request_body = self.rfile.read(content_length).decode('utf-8')
            request_data = json.loads(request_body)
            
            # Extract message and other data from request
            message = request_data.get("message", "")
            conversation_id = request_data.get("conversation_id", f"conv-{uuid.uuid4()}")
            project_id = request_data.get("project_id", "default")
            use_memory = request_data.get("use_memory", True)
            store_in_memory = request_data.get("store_in_memory", True)
            message_history = request_data.get("message_history", [])
            user_id = request_data.get("user_id", f"user-{uuid.uuid4()}")
            
            logger.info(f"Received ThinkTank request: {message[:50]}...")
            logger.info(f"Conversation ID: {conversation_id}, Project ID: {project_id}")
            
            # Initialize memory for this conversation if needed
            if conversation_id not in conversation_memory:
                conversation_memory[conversation_id] = []
            
            # Add message history to memory if we don't have it yet
            if use_memory and message_history and len(conversation_memory[conversation_id]) == 0:
                logger.info(f"Adding message history to memory: {len(message_history)} messages")
                conversation_memory[conversation_id] = message_history
                
            # Add current message to memory
            if store_in_memory:
                conversation_memory[conversation_id].append({
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                # Force save memory after each user message
                logger.info(f"Saving user message to memory for conversation {conversation_id}")
                save_memory_to_file()
            
            # Check if force_real_think_tank flag is set
            force_real_think_tank = request_data.get("force_real_think_tank", False)
            
            # Log the model selection strategy
            if force_real_think_tank:
                logger.info("Force real Think Tank flag is set to True - will use direct API call")
            else:
                logger.info("Using standard Think Tank processing with fallback options")
            
            # Process with real Think Tank API or fallback based on settings
            try:
                # Use the direct processor first for forced real model call
                if force_real_think_tank:
                    logger.info("Using direct_think_tank_processor for forced real model call")
                    result = direct_think_tank_processor(
                        message=message,
                        conversation_id=conversation_id,
                        test_mode=False
                    )
                    logger.info(f"Direct processor call successful. Models used: {result.get('model_info', {}).get('models_used', ['unknown'])}")                
                else:
                    # Use the standard process_with_think_tank which might already be our direct API function
                    logger.info("Using standard process_with_think_tank function")
                    result = process_with_think_tank(
                        message=message,
                        conversation_id=conversation_id,
                        test_mode=False
                    )
                    
                # Log successful response and model info
                model_info = result.get('model_info', {})
                models_used = model_info.get('models_used', ['unknown'])
                logger.info(f"Think Tank processing successful. Models used: {models_used}")
                
            except Exception as e:
                # If ThinkTank processing fails, log detailed error
                logger.error(f"Error in ThinkTank processing: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                logger.info("Using enhanced fallback processor instead")
                
                # Process with simple fallback
                try:
                    result = simple_fallback_processor(message, conversation_id)
                    logger.info("Simple fallback processor used successfully")
                except Exception as fallback_error:
                    logger.error(f"Error in fallback processor: {str(fallback_error)}")
                    logger.error(f"Fallback traceback: {traceback.format_exc()}")
                    
                    # Last resort emergency fallback
                    response_text = f"I understand your message about '{message[:30]}...'. I'm currently operating in emergency fallback mode due to a technical issue."
                    result = {
                        "response": response_text,
                        "conversation_id": conversation_id,
                        "model_info": {
                            "model_used": "emergency_fallback",
                            "processing_time": 0,
                            "error": str(e)
                        },
                        "status": "success"
                    }
                    logger.warning("Using emergency fallback mode")
            
            # Ensure we have required fields in the response
            if "conversation_id" not in result and conversation_id:
                result["conversation_id"] = conversation_id
            
            # Add memory to storage if we have a response
            if store_in_memory and "response" in result:
                conversation_memory[conversation_id].append({
                    "role": "assistant",
                    "content": result["response"],
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
                # Force save memory after each assistant response
                logger.info(f"💾 Saving assistant response to memory for conversation {conversation_id}")
                save_memory_to_file()
                
                # Update memory information in the response
                result["memory_id"] = f"mem-{conversation_id}"
                result["memory_updates"] = {
                    "id": f"mem-{conversation_id}",
                    "type": "conversation",
                    "title": f"Conversation {conversation_id}",
                    "content": result["response"],
                    "source": "minerva_core",
                    "timestamp": "current",
                    "projectId": project_id,
                    "conversation_id": conversation_id,
                    "tags": ["conversation", project_id]
                }
                
                result["memory_info"] = {
                    "summary": "Message processed and stored",
                    "status": "active",
                    "project_id": project_id,
                    "conversation_id": conversation_id,
                    "message_count": len(conversation_memory[conversation_id])
                }
            
            # Send response
            self._set_headers()
            
            # Add project conversion flag
            result["canCreateProject"] = True
            
            # Send the JSON response
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
    """Start the Minerva Central server"""
    # Ensure we're in the web directory
    os.chdir(current_dir)
    
    # Load existing conversation memory on startup
    load_memory_from_file()
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, MinervaCentralHandler)
    
    logger.info(f"Starting Minerva Central server on port {port}")
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
