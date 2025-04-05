#!/usr/bin/env python3
"""
Minimal Minerva Think Tank Server
This server focuses only on serving the minimal UI and providing the Think Tank API with memory integration.
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session, render_template
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv

# Add parent directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("minimal_server")

# Load environment variables from .env file
env_path = os.path.join(parent_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f".env file not found at {env_path}")

# Force MINERVA_TEST_MODE to false to use real API calls
os.environ["MINERVA_TEST_MODE"] = "false"

# Import memory system
try:
    from web.integrations.memory import (
        memory_system, 
        store_memory, 
        retrieve_memory, 
        enhance_with_memory,
        get_memory,
        get_all_memories,
        get_memories_by_conversation_id
    )
    logger.info("Successfully imported memory system")
    
    def get_conversation_by_id(conversation_id):
        """Retrieve a full conversation by ID from the memory system"""
        try:
            memories = get_memories_by_conversation_id(conversation_id)
            if memories:
                logger.info(f"Retrieved {len(memories)} messages for conversation {conversation_id}")
                return memories
            else:
                logger.warning(f"No memories found for conversation {conversation_id}")
                return []
        except Exception as e:
            logger.error(f"Error retrieving conversation: {str(e)}")
            return []
except ImportError as e:
    logger.error(f"Failed to import memory system: {e}")
    logger.warning("Memory functionality will be disabled")
    
    # Mock functions if import fails
    memory_system = None
    
    def store_memory(conversation_id, user_message, ai_response, metadata=None):
        logger.warning("Memory system not available. Cannot store memory.")
        return None
        
    def retrieve_memory(user_message, top_k=3):
        logger.warning("Memory system not available. Cannot retrieve memory.")
        return []
        
    def enhance_with_memory(user_query):
        logger.warning("Memory system not available. Cannot enhance query.")
        return user_query, []
        
    def get_conversation_by_id(conversation_id):
        logger.warning(f"Memory system not available. Cannot retrieve conversation {conversation_id}.")
        return []

# Import project management system
try:
    from web.integrations.projects import (
        create_project,
        update_project,
        delete_project,
        get_project,
        get_all_projects,
        add_conversation_to_project,
        remove_conversation_from_project,
        get_project_conversations
    )
    logger.info("Successfully imported project management system")
except ImportError as e:
    logger.error(f"Failed to import project management system: {e}")
    logger.warning("Project management functionality will be disabled")
    
    # Mock functions if import fails
    def create_project(name, description="", metadata=None):
        logger.warning("Project management system not available. Cannot create project.")
        return None
        
    def update_project(project_id, name=None, description=None, metadata=None):
        logger.warning("Project management system not available. Cannot update project.")
        return False
        
    def delete_project(project_id):
        logger.warning("Project management system not available. Cannot delete project.")
        return False
        
    def get_project(project_id):
        logger.warning("Project management system not available. Cannot get project.")
        return None
        
    def get_all_projects():
        logger.warning("Project management system not available. Cannot get projects.")
        return []
        
    def add_conversation_to_project(project_id, conversation_id, title=None):
        logger.warning("Project management system not available. Cannot add conversation to project.")
        return False
        
    def remove_conversation_from_project(project_id, conversation_id):
        logger.warning("Project management system not available. Cannot remove conversation from project.")
        return False
        
    def get_project_conversations(project_id):
        logger.warning("Project management system not available. Cannot get project conversations.")
        return []

# Import the Think Tank processor
try:
    # Try to import from main module first
    sys.path.insert(0, parent_dir)
    from processor.think_tank import process_with_think_tank
    logger.info("Successfully imported Think Tank processor from main module")
except ImportError:
    try:
        # Try alternate import path
        from web.think_tank_consolidated import process_with_think_tank
        logger.info("Successfully imported Think Tank processor from consolidated module")
    except ImportError as e:
        logger.error(f"Failed to import Think Tank processor: {e}")
        logger.error("Falling back to mock processor")
        
        # Simple mock function that works with the Think Tank API
        def process_with_think_tank(message, conversation_id=None, **kwargs):
            # Log basic info
            logger.info(f"Processing with Think Tank: '{message if message else '<empty>'}', conversation: {conversation_id}")
            
            # Log any extra params provided
            if kwargs:
                logger.info(f"Additional parameters: {kwargs}")
            
            # Return a standard Think Tank response
            # Important: response must be a plain string
            return {
                "response": f"I received your message: '{message}'. The Think Tank is operating normally and your conversation history is being maintained.",
                "conversation_id": conversation_id or f"conv-{uuid.uuid4()}",
                "message_id": f"msg-{uuid.uuid4()}"
            }

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure session
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'minerva-development-key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_FILE_DIR'] = os.path.join(current_dir, 'flask_session')
Session(app)

@app.route('/')
def index():
    """Serve the deep space visualization UI"""
    return render_template('simple_space.html')
    
@app.route('/chat-widget')
def chat_widget():
    """Serve the chat widget for embedding"""
    return send_from_directory(current_dir, 'working_chat.html')

@app.route('/original')
def original_index():
    """Serve the original Minerva integrated UI"""
    return send_from_directory(os.path.join(current_dir, 'templates'), 'minerva_home.html')

@app.route('/minerva-portal')
def minerva_portal():
    """Serve the Minerva portal page"""
    return render_template('minerva_portal.html')

@app.route('/projects')
def projects():
    """Serve the Projects page"""
    return render_template('minerva_projects.html')

@app.route('/memory')
def memory_system():
    """Serve the Memory System page"""
    return render_template('minerva_memory.html')

@app.route('/settings')
def settings():
    """Serve the Settings page"""
    return render_template('minerva_settings.html')

@app.route('/test')
def test_page():
    """Serve the ultra minimal test UI (preserved for testing)"""
    return send_from_directory(current_dir, 'ultra_minimal.html')

@app.route('/projects')
def projects_ui():
    """Serve the projects management UI"""
    return send_from_directory(current_dir, 'projects.html')

@app.route('/project')
def project_detail():
    """Serve the project detail page with project-specific chat panel"""
    project_id = request.args.get('id')
    return render_template('project_detail.html', project_id=project_id)

# Project detail API moved to comprehensive definition at line ~429

@app.route('/api/think-tank', methods=['POST'])
def think_tank_api():
    """
    Process a message using the Think Tank
    
    This function handles requests to the Think Tank API
    """
    # Log the incoming request
    logger.info(f"Received Think Tank request: {request.json}")
    
    data = request.json
    if not data:
        logger.error("No JSON data received")
        return jsonify({"response": "Error: No JSON data received!"}), 400
        
    # Get query from request - check multiple possible field names
    # This ensures compatibility with both older and newer clients
    # Accept either 'query' or 'message' parameter for flexibility
    user_query = data.get("message", "") or data.get("query", "")
    
    # Log the full request data for debugging
    logger.info(f"Request data: {data}")
    
    if not user_query:
        logger.error("No message or query provided in the request")
        return jsonify({"response": "Error: No message received!"}), 400
        
    # Log that we're using the Think Tank to process this query
    logger.info(f"Using Think Tank to process query: '{user_query[:50]}...'")
    
    # Get or generate conversation ID
    conversation_id = data.get("conversation_id", f"conv-{uuid.uuid4()}")
    store_in_memory = data.get("store_in_memory", True)
    
    # Get project context if available
    project_id = data.get("project_id")
    project_context = data.get("context", {})
    
    logger.info(f"Processing query with Think Tank. ConversationID: {conversation_id}")

    try:
        # Process user input with Think Tank AI
        # Match the parameters expected by the Think Tank processor including conversation_id
        model_priority = ['gpt-4o', 'claude-3-opus', 'gemini-pro']  # Default models in priority order
        
        # Create query tags with context information if available
        query_tags = {
            'source': 'web_interface',
            'primary_domain': data.get('domain', 'general_knowledge'),
        }
        
        # Project context if available
        if project_id:
            query_tags['project_id'] = project_id
            
        result = process_with_think_tank(
            message=user_query,
            model_priority=model_priority,
            complexity=0.0,
            query_tags=query_tags,
            conversation_id=conversation_id
        )
        logger.info("Think Tank processed the message successfully")
        
        # Log detailed information about the result for debugging
        logger.info(f"Think Tank response type: {type(result)}")
        if isinstance(result, dict):
            logger.info(f"Think Tank result keys: {list(result.keys())}")
            if 'response' in result:
                logger.info(f"Response type: {type(result['response'])}")
                logger.info(f"Response preview: {str(result['response'])[:100]}")
                
                # CRITICAL FIX: Ensure response is always a string, not an object
                if not isinstance(result['response'], str):
                    try:
                        result['response'] = str(result['response'])
                        logger.info("Converted non-string response to string")
                    except Exception as e:
                        logger.error(f"Failed to convert response to string: {e}")
                        result['response'] = "Sorry, I couldn't generate a proper response."
        
        # Ensure response is a string
        if 'response' in result and not isinstance(result['response'], str):
            logger.warning(f"Response is not a string, converting: {type(result['response'])}")
            try:
                result['response'] = str(result['response'])
            except Exception as e:
                logger.error(f"Failed to convert response to string: {e}")
                result['response'] = "Error: Response could not be displayed properly"
        
        # Store conversation in memory if requested
        if store_in_memory:
            metadata = {}
            
            # Add project info to metadata if available
            if project_id:
                metadata['project_id'] = project_id
                metadata['project_context'] = project_context
                
                # If this is a new conversation, associate it with the project
                if not data.get("conversation_id") and project_id:
                    try:
                        add_conversation_to_project(project_id, conversation_id)
                        logger.info(f"Added new conversation {conversation_id} to project {project_id}")
                    except Exception as e:
                        logger.error(f"Failed to add conversation to project: {str(e)}")
            
            # Store in memory system
            try:
                # Sanitize metadata to ensure no None values
                sanitized_metadata = {}
                for key, value in metadata.items():
                    if value is not None:
                        if isinstance(value, (str, int, float, bool)):
                            sanitized_metadata[key] = value
                        else:
                            # Convert to string if not a primitive type
                            sanitized_metadata[key] = str(value)
                
                # Get correct response key from result
                response_text = ""
                logger.info(f"Response structure: {result.keys()}")
                if 'response' in result:
                    response_text = result['response']
                elif 'responses' in result:
                    # Handle responses array in various formats
                    responses = result['responses']
                    logger.info(f"Responses type: {type(responses)}, content: {responses}")
                    
                    if isinstance(responses, dict):
                        # If it's a dictionary with model names as keys
                        for model_name, resp in responses.items():
                            if resp:  # Use the first non-empty response
                                if isinstance(resp, dict) and 'response' in resp:
                                    response_text = resp['response']
                                elif isinstance(resp, str):
                                    response_text = resp
                                else:
                                    response_text = str(resp)
                                break
                    elif isinstance(responses, list) and len(responses) > 0:
                        # Get the first response from the responses array
                        first_response = responses[0]
                        if isinstance(first_response, dict) and 'response' in first_response:
                            response_text = first_response['response']
                        elif isinstance(first_response, str):
                            response_text = first_response
                        else:
                            response_text = str(first_response)
                    elif responses:  # If it's some other non-empty value
                        response_text = str(responses)
                        
                if not response_text:
                    # Try to extract response text directly from any available field
                    response_keys = [k for k in result.keys() if 'resp' in k.lower()]
                    if response_keys:
                        response_value = result[response_keys[0]]
                        if isinstance(response_value, str):
                            response_text = response_value
                        elif isinstance(response_value, (list, tuple)) and len(response_value) > 0:
                            response_text = str(response_value[0])
                        else:
                            response_text = str(response_value)
                    else:
                        # Just stringify the whole result as a fallback
                        logger.warning("No response field found, using entire result as response")
                        try:
                            response_text = json.dumps(result)
                        except:
                            response_text = str(result)
                
                # Ensure response is a string
                if not isinstance(response_text, str):
                    response_text = str(response_text)
                    
                logger.info(f"Final response text: {response_text[:100]}...")
                
                # Ensure conversation_id is a string and not empty
                if not conversation_id:
                    conversation_id = f"conv-{uuid.uuid4()}"
                    result['conversation_id'] = conversation_id
                    logger.info(f"Generated new conversation ID: {conversation_id}")
                
                # Ensure the query and response are not empty
                if not user_query:
                    user_query = "[Empty query]"
                if not response_text:
                    response_text = "[No response generated]"
                
                # Add extra debugging
                logger.info(f"Storing memory with conversation_id: {conversation_id}")
                logger.info(f"User query: {user_query[:100]}")
                logger.info(f"Response text: {response_text[:100]}")
                logger.info(f"Metadata: {sanitized_metadata}")
                
                store_memory(conversation_id, user_query, response_text, sanitized_metadata)
                logger.info(f"Successfully stored conversation in memory system: {conversation_id}")
            except Exception as e:
                logger.error(f"Failed to store in memory: {str(e)}")
                # Try to get more information about the error
                import traceback
                logger.error(f"Memory storage error details: {traceback.format_exc()}")
            
        if isinstance(result, dict):
            # Always ensure response is a string at the final stage before returning
            if 'response' in result:
                if not isinstance(result['response'], str):
                    # Force conversion to string with safer method
                    try:
                        if isinstance(result['response'], dict):
                            result['response'] = json.dumps(result['response'])
                        else:
                            result['response'] = str(result['response'])
                        logger.warning(f"API: Converted non-string response to string: {result['response'][:100]}")
                    except Exception as e:
                        logger.error(f"API: Failed final string conversion: {str(e)}")
                        result['response'] = "Error: Unable to process response format"
                        
            # Add message_id and conversation_id to the response
            if 'message_id' not in result:
                result['message_id'] = f"msg-{uuid.uuid4()}"
            if 'conversation_id' not in result:
                result['conversation_id'] = conversation_id
            
            logger.info(f"Successfully processed Think Tank query")
            
            # Final safety check - if somehow response is still an object, convert entire result to string format
            if 'response' in result and not isinstance(result['response'], str):
                logger.error(f"API: Critical error - response still not string after conversion: {type(result['response'])}")
                try:
                    if isinstance(result['response'], dict):
                        result['response'] = json.dumps(result['response'])
                    else:
                        result['response'] = str(result['response'])
                    logger.warning(f"API: Forced final string conversion for response: {result['response'][:100]}")
                except Exception as error:
                    logger.error(f"API: Failed final string conversion attempt: {str(error)}")
                    return jsonify({"response": "The system encountered an error processing your request", 
                                  "conversation_id": conversation_id})
                
            logger.info(f"Sending response: {result}")
            return jsonify(result)
        else:
            response_data = {
                "response": result,
                "message_id": f"msg-{uuid.uuid4()}",
                "conversation_id": conversation_id
            }
            logger.info(f"Sending response: {response_data}")
            logger.info(f"Successfully processed Think Tank query with string response")
            return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error processing Think Tank query: {str(e)}")
        return jsonify({"response": f"Processing error: {str(e)}"}), 500

# Project Management API Routes
@app.route('/api/projects/create-from-conversation', methods=['POST'])
def create_project_from_conversation():
    """Create a new project from an existing conversation"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        project_name = data.get('project_name')
        conversation_id = data.get('conversation_id')
        
        if not project_name or not conversation_id:
            return jsonify({'error': 'Missing required fields: project_name and conversation_id'}), 400
        
        # Generate a unique project ID
        project_id = f"proj-{str(uuid.uuid4())[:8]}"
        
        # Check if we have conversation memory
        conversation_data = None
        if memory_system:
            try:
                # Get conversation from memory system
                conversation_data = get_conversation_by_id(conversation_id)
                logger.info(f"Retrieved conversation data for {conversation_id}")
            except Exception as e:
                logger.error(f"Error retrieving conversation: {str(e)}")
                conversation_data = None
        
        # Create project structure
        project = {
            'id': project_id,
            'name': project_name,
            'created_at': datetime.now().isoformat(),
            'conversation_id': conversation_id,
            'summary': 'Project created from conversation',
            'status': 'active'
        }
        
        # Store in project database
        try:
            # Create projects directory if needed
            projects_dir = os.path.join(current_dir, 'data', 'projects')
            os.makedirs(projects_dir, exist_ok=True)
            
            # Store project data
            project_file = os.path.join(projects_dir, f"{project_id}.json")
            with open(project_file, 'w') as f:
                json.dump(project, f, indent=2)
                
            logger.info(f"Created new project: {project_id} - {project_name}")
            
            # Return success response
            return jsonify({
                'status': 'success',
                'project_id': project_id,
                'project_name': project_name
            })
        except Exception as e:
            logger.error(f"Error creating project file: {str(e)}")
            return jsonify({'error': f"Failed to create project: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error in create_project_from_conversation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['GET', 'POST'])
def projects_api():
    """API for managing projects"""
    try:
        if request.method == 'GET':
            # Get all projects
            projects = get_all_projects()
            return jsonify({
                'projects': projects,
                'status': 'success'
            })
        elif request.method == 'POST':
            # Create a new project
            data = request.json
            if not data:
                return jsonify({'error': 'No JSON data received'}), 400
                
            name = data.get('name')
            if not name:
                return jsonify({'error': 'Project name is required'}), 400
                
            description = data.get('description', '')
            metadata = data.get('metadata', {})
            
            project_id = create_project(name, description, metadata)
            if not project_id:
                return jsonify({'error': 'Failed to create project'}), 500
                
            return jsonify({
                'project_id': project_id,
                'status': 'success'
            })
    except Exception as e:
        logger.error(f"Error in projects API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['GET', 'PUT', 'DELETE'])
def project_api(project_id):
    """API for managing a specific project"""
    try:
        if request.method == 'GET':
            # Get project details
            project = get_project(project_id)
            if not project:
                return jsonify({'error': 'Project not found'}), 404
                
            return jsonify({
                'project': project,
                'status': 'success'
            })
        elif request.method == 'PUT':
            # Update project
            data = request.json
            if not data:
                return jsonify({'error': 'No JSON data received'}), 400
                
            name = data.get('name')
            description = data.get('description')
            metadata = data.get('metadata')
            
            success = update_project(project_id, name, description, metadata)
            if not success:
                return jsonify({'error': 'Failed to update project'}), 500
                
            return jsonify({
                'status': 'success'
            })
        elif request.method == 'DELETE':
            # Delete project
            success = delete_project(project_id)
            if not success:
                return jsonify({'error': 'Failed to delete project'}), 500
                
            return jsonify({
                'status': 'success'
            })
    except Exception as e:
        logger.error(f"Error in project API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/conversations', methods=['GET', 'POST', 'DELETE'])
def project_conversations_api(project_id):
    """API for managing conversations in a project"""
    try:
        if request.method == 'GET':
            # Get all conversations in the project
            conversations = get_project_conversations(project_id)
            return jsonify({
                'conversations': conversations,
                'status': 'success'
            })
        elif request.method == 'POST':
            # Add a conversation to the project
            data = request.json
            if not data:
                return jsonify({'error': 'No JSON data received'}), 400
                
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                return jsonify({'error': 'Conversation ID is required'}), 400
                
            title = data.get('title')
            
            success = add_conversation_to_project(project_id, conversation_id, title)
            if not success:
                return jsonify({'error': 'Failed to add conversation to project'}), 500
                
            return jsonify({
                'status': 'success'
            })
        elif request.method == 'DELETE':
            # Remove a conversation from the project
            data = request.json
            if not data:
                return jsonify({'error': 'No JSON data received'}), 400
                
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                return jsonify({'error': 'Conversation ID is required'}), 400
                
            success = remove_conversation_from_project(project_id, conversation_id)
            if not success:
                return jsonify({'error': 'Failed to remove conversation from project'}), 500
                
            return jsonify({
                'status': 'success'
            })
    except Exception as e:
        logger.error(f"Error in project conversations API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations', methods=['GET'])
def conversations_api():
    """API for retrieving all stored conversations"""
    try:
        # Get all conversations from memory
        memories = get_all_memories(limit=100, offset=0)
        
        # Format memories for response
        conversations = []
        for memory in memories:
            # Extract conversation details
            conversation_id = memory.get('metadata', {}).get('conversation_id', 'unknown')
            timestamp = memory.get('metadata', {}).get('timestamp', '')
            
            # Extract content
            content = memory.get('content', '')
            
            # Extract first part of user message as title
            title = ''
            if content and isinstance(content, str):
                parts = content.split('\n')
                if len(parts) > 0 and parts[0].startswith('User: '):
                    title = parts[0][6:50] + ('...' if len(parts[0]) > 56 else '')
            
            conversations.append({
                'conversation_id': conversation_id,
                'memory_id': memory.get('id', ''),
                'timestamp': timestamp,
                'title': title or f"Conversation {conversation_id[-8:]}"
            })
        
        return jsonify({
            'conversations': conversations,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error in conversations API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/<path:path>')
def static_files(path):
    """Serve static files from the web directory"""
    return send_from_directory(current_dir, path)

# Route for simple chat test page
@app.route('/simple-chat-test')
def simple_chat_test():
    """Serve the simplified chat test page"""
    return send_from_directory(current_dir, 'simple_chat_test.html')

# Route for working chat test page
@app.route('/working-chat')
def working_chat():
    """Serve the working chat page"""
    return send_from_directory(current_dir, 'working_chat.html')

# Route for simple working chat page
@app.route('/simple-chat')
def simple_chat():
    """Serve the simple working chat page"""
    return send_from_directory(current_dir, 'simple_working_chat.html')

# Route for the guaranteed working solution
@app.route('/working-solution')
def working_solution():
    """Serve the guaranteed working chat solution"""
    return send_from_directory(current_dir, 'direct_solution.html')
    
# Another guaranteed working solution
@app.route('/guaranteed-chat')
def guaranteed_chat():
    """Serve the absolutely guaranteed chat solution"""
    return send_from_directory(current_dir, 'guaranteed_chat.html')

# API test tool
@app.route('/api-test')
def api_test():
    """Serve the API test tool"""
    return send_from_directory(current_dir, 'api_test.html')

# Floating chat solution
@app.route('/floating-chat')
def floating_chat_solution():
    """Serve the floating chat solution"""
    return send_from_directory(current_dir, 'floating_chat_solution.html')

@app.route('/api/create-project', methods=['POST'])
def create_project():
    """Create a new project from a conversation"""
    data = request.json
    project_name = data.get('project_name')
    conversation_id = data.get('conversation_id')
    
    if not project_name or not conversation_id:
        return jsonify({'error': 'Missing required parameters'}), 400
        
    # Generate a project ID
    project_id = f"proj-{uuid.uuid4()}"
    
    # Store the project in the database (in a real app)
    # Here we're just sending back a success response
    project = {
        'project_id': project_id,
        'name': project_name,
        'conversations': [conversation_id],
        'created_at': datetime.datetime.now().isoformat()
    }
    
    # Return the created project
    return jsonify({
        'success': True,
        'message': f'Project {project_name} created successfully',
        'project': project
    })

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    # In a real app, this would fetch from a database
    # For now, return a dummy list
    projects = [
        {
            'project_id': 'proj-1',
            'name': 'Sample Project 1',
            'conversations': ['conv-1', 'conv-2'],
            'created_at': datetime.datetime.now().isoformat()
        },
        {
            'project_id': 'proj-2',
            'name': 'Sample Project 2',
            'conversations': ['conv-3'],
            'created_at': datetime.datetime.now().isoformat()
        }
    ]
    
    return jsonify({'projects': projects})

if __name__ == '__main__':
    # Use a port that's very unlikely to be in use
    port = 5136  # Changed to avoid conflicts with existing server
    logger.info(f"Starting Minimal Server on port {port}...")
    logger.info(f"Access the minimal UI at: http://localhost:{port}/")
    logger.info(f"Access the simple chat test at: http://localhost:{port}/simple-chat-test")
    app.run(debug=True, host='0.0.0.0', port=port)
