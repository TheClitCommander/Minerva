"""
Minerva Chat API
Provides endpoints for the chat interface, leveraging the Think Tank capabilities
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify
from datetime import datetime

# Import the chat handler to process messages with project context and intent detection
from minerva.chat.chat_handler import process_message_with_intent_detection, INTENT_SUGGEST_TASKS

# Import the memory system
from integrations.memory import store_memory, retrieve_memory, enhance_with_memory, get_memory

# Import the feedback system
from integrations.feedback import track_conversation, enhance_query, record_user_feedback, get_user_preferences, check_fine_tuning_readiness

# Create blueprint for chat API
chat_api = Blueprint('chat_api', __name__)
logger = logging.getLogger(__name__)

# Import Think Tank components
try:
    from processor.ai_router import route_request, get_query_tags
    from processor.think_tank import process_with_think_tank
    from processor.ensemble_validator import rank_responses
    from processor.response_blender import blend_responses
    has_think_tank = True
except ImportError:
    logger.warning("Think Tank components not available, using simulation mode")
    has_think_tank = False

# Project storage - would use a database in production
projects = {}
conversations = {}

@chat_api.route('/message', methods=['POST'])
def process_chat_message():
    """
    Process a chat message using Think Tank capabilities
    Returns a response with model rankings and blending information
    """
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing message in request'}), 400
            
        user_message = data['message']
        project_id = data.get('project_id')
        branch_id = data.get('branch_id', 'main')
        
        # Check memory for relevant past conversations
        relevant_memories = retrieve_memory(user_message, top_k=3)
        memory_enhanced_message = user_message
        memory_context = None
        
        # If we found relevant memories, enhance the query with context
        if relevant_memories:
            enhanced_message, memories = enhance_with_memory(user_message)
            memory_enhanced_message = enhanced_message
            memory_context = {
                'memories_used': [mem['id'] for mem in memories],
                'memory_count': len(memories),
                'top_relevance': memories[0]['relevance_score'] if memories else 0
            }
            logger.info(f"Enhanced user query with {len(memories)} relevant memories")
        
        # Process with Think Tank (or simulation if not available)
        if has_think_tank:
            # Get routing information based on message content
            routing_info = route_request(memory_enhanced_message)
            query_tags = get_query_tags(memory_enhanced_message)
            
            # Log the detailed routing decision for analytics
            logger.info(f"Routing decision for message: {routing_info}")
            
            # Process with project context and intent detection
            session_data = {}
            if project_id:
                session_data['active_project'] = project_id
                
            # First check for project intents like task suggestions
            enhanced_message_data = process_message_with_intent_detection(
                message=user_message,
                user_id=data.get('user_id', 'anonymous'),
                session_data=session_data
            )
            
            # Check if we have a task suggestion intent
            task_suggestion_content = None
            detected_intent = enhanced_message_data.get('detected_intent', {})
            if detected_intent.get('action') == INTENT_SUGGEST_TASKS and 'task_suggestions' in enhanced_message_data:
                task_suggs = enhanced_message_data['task_suggestions']
                if task_suggs.get('success') and task_suggs.get('suggestions'):
                    # Format task suggestions for display
                    task_suggestion_content = {
                        'type': 'task_suggestions',
                        'message': task_suggs['message'],
                        'suggestions': task_suggs['suggestions']
                    }
            
            # Process with Think Tank to get responses from multiple models
            think_tank_result = process_with_think_tank(
                memory_enhanced_message, 
                routing_info['model_priority'], 
                complexity=routing_info['complexity_score'],
                query_tags=query_tags
            )
            
            # Get detailed rankings with reasoning
            ranked_responses = rank_responses(
                think_tank_result['responses'], 
                user_message,
                query_tags
            )
            
            # Blend responses based on query type and rankings
            blended_result = blend_responses(
                think_tank_result['responses'],
                ranked_responses, 
                query_tags
            )
            
            # Format response with detailed model info
            response_content = blended_result['blended_response']
            model_info = {
                'models_used': [model for model in think_tank_result['responses']],
                'rankings': ranked_responses,
                'blending': {
                    'method': blended_result['blend_method'],
                    'contributing_models': blended_result['contributing_models'],
                    'sections': blended_result['sections']
                }
            }
            
            # If we have task suggestions, inject them into the response
            if task_suggestion_content:
                # Add task suggestions to the response
                response = {
                    'response': response_content,
                    'model_info': model_info,
                    'task_suggestions': task_suggestion_content
                }
            else:
                # Regular response without task suggestions
                response = {
                    'response': response_content,
                    'model_info': model_info
                }
            
            # Include memory information if it was used
            if memory_context:
                model_info['memory'] = memory_context
        else:
            # No Think Tank functionality available - this is an error state
            logger.error("Think Tank components not available - cannot process message")
            return jsonify({
                'error': 'AI processing components unavailable. Please check server configuration.'
            }), 500
        
        # Save to conversation history (simplified version - would use DB in production)
        timestamp = datetime.now().isoformat()
        conversation_id = f"{project_id}_{branch_id}" if project_id else f"default_{str(uuid.uuid4())[:8]}"
        user_id = data.get('user_id', 'default')
        
        if conversation_id not in conversations:
            conversations[conversation_id] = []
            
        conversations[conversation_id].append({
            'role': 'user',
            'content': user_message,
            'timestamp': timestamp
        })
        
        conversations[conversation_id].append({
            'role': 'assistant',
            'content': response_content,
            'model_info': model_info,
            'timestamp': timestamp
        })
        
        # Store the conversation in the memory system
        memory_metadata = {
            'project_id': project_id,
            'branch_id': branch_id,
            'model_info': model_info,
            'timestamp': timestamp,
            'user_id': user_id
        }
        
        memory_id = store_memory(
            conversation_id=conversation_id,
            user_message=user_message,
            ai_response=response_content,
            metadata=memory_metadata
        )
        
        # Track this conversation turn for context awareness and future learning
        track_conversation(
            conversation_id=conversation_id,
            user_query=user_message,
            ai_response=response_content
        )
        
        logger.info(f"Stored conversation in memory system with ID: {memory_id}")
        
        # Return formatted response
        response = {
            'message': response_content,  # Keep for backward compatibility
            'response': response_content,  # Add this field for frontend consistency
            'timestamp': timestamp,
            'model_info': model_info,
            'conversation_id': conversation_id,
            'memory_id': memory_id  # Add memory_id for potential feedback
        }
        
        # Add memory info to the response if it was used
        if memory_context:
            response['memory_info'] = {
                'used': True,
                'count': memory_context['memory_count'],
                'relevance': memory_context['top_relevance'],
                'memory_ids': memory_context['memories_used']
            }
        else:
            response['memory_info'] = {'used': False}
            
        # Include user preferences if available
        user_preferences = get_user_preferences(user_id)
        if user_preferences and user_preferences.get('preferences_detected', False):
            response['user_preferences'] = user_preferences
            
        # Add task suggestions if available
        if task_suggestion_content:
            response['task_suggestions'] = task_suggestion_content
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        return jsonify({
            'error': f"Failed to process message: {str(e)}",
            'message': "I'm sorry, I encountered an error processing your request."
        }), 500

@chat_api.route('/projects', methods=['GET', 'POST'])
def manage_projects():
    """
    Create or retrieve projects
    GET: List all projects
    POST: Create a new project
    """
    if request.method == 'GET':
        return jsonify({
            'projects': list(projects.values())
        })
    else:  # POST
        try:
            data = request.json
            project_name = data.get('name', f"Project {len(projects) + 1}")
            description = data.get('description', '')
            
            project_id = f"proj_{len(projects) + 1}"
            projects[project_id] = {
                'id': project_id,
                'name': project_name,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'branches': ['main']  # Default branch
            }
            
            # Initialize conversation history for the main branch
            conversation_id = f"{project_id}_main"
            conversations[conversation_id] = []
            
            return jsonify(projects[project_id])
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return jsonify({'error': f"Failed to create project: {str(e)}"}), 500

@chat_api.route('/projects/<project_id>/branches', methods=['GET', 'POST'])
def manage_branches(project_id):
    """
    Create or retrieve project branches
    GET: List all branches for a project
    POST: Create a new branch
    """
    if project_id not in projects:
        return jsonify({'error': 'Project not found'}), 404
        
    if request.method == 'GET':
        return jsonify({
            'branches': projects[project_id]['branches']
        })
    else:  # POST
        try:
            data = request.json
            branch_name = data.get('name', f"Branch {len(projects[project_id]['branches']) + 1}")
            parent_branch = data.get('parent_branch', 'main')
            
            # Add branch to project
            if branch_name not in projects[project_id]['branches']:
                projects[project_id]['branches'].append(branch_name)
            
            # Copy conversation history from parent branch to new branch
            parent_conversation_id = f"{project_id}_{parent_branch}"
            new_conversation_id = f"{project_id}_{branch_name}"
            
            if parent_conversation_id in conversations:
                conversations[new_conversation_id] = conversations[parent_conversation_id].copy()
            else:
                conversations[new_conversation_id] = []
            
            return jsonify({
                'branch': branch_name,
                'project_id': project_id
            })
            
        except Exception as e:
            logger.error(f"Error creating branch: {str(e)}")
            return jsonify({'error': f"Failed to create branch: {str(e)}"}), 500

@chat_api.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation_history(conversation_id):
    """
    Retrieve conversation history for a specific project/branch
    """
    if conversation_id in conversations:
        return jsonify({
            'conversation_id': conversation_id,
            'messages': conversations[conversation_id]
        })
    else:
        return jsonify({
            'conversation_id': conversation_id,
            'messages': []
        })

def simulate_think_tank_response(user_message: str) -> tuple:
    """
    Process a message using Think Tank components when available, with fallback to simulation
    Serves as a bridge between the old simulated system and the new real implementation
    """
    # Check for simple greetings first (preserve this helpful functionality)
    user_message_lower = user_message.lower()
    
    # Simple greeting detection
    is_greeting = any(greeting in user_message_lower for greeting in [
        'hi', 'hello', 'hey', 'greetings', 'howdy', 'what\'s up', 'sup'
    ])
    
    if is_greeting:
        return generate_greeting_response(), {
            'models_used': ['gpt-4'],
            'rankings': [{'model': 'gpt-4', 'score': 1.0, 'reason': 'Simple greeting response'}],
            'blending': {
                'method': 'direct',
                'contributing_models': ['gpt-4'],
                'sections': []
            }
        }
    
    # Try to use real Think Tank components if they're partially available
    routing_info = None
    query_tags = None
    think_tank_result = None
    
    try:
        # Try to use real routing if available
        if 'route_request' in globals():
            routing_info = route_request(user_message)
            logger.info(f"Using real routing: {routing_info}")
        
        if 'get_query_tags' in globals():
            query_tags = get_query_tags(user_message)
            logger.info(f"Using real query tagging: {query_tags}")
            
        # If we have routing but not the full Think Tank, we can still do better simulation
        if routing_info and query_tags:
            logger.info("Using enhanced simulation with real routing and query tags")
    except Exception as e:
        logger.warning(f"Error using Think Tank components: {str(e)}")
    
    # Fallback to basic content detection if routing failed
    if query_tags is None:
        # Basic content detection
        is_code_related = any(term in user_message_lower 
                             for term in ['code', 'function', 'programming', 'algorithm', 'bug'])
        is_comparison = any(term in user_message_lower 
                           for term in ['compare', 'difference', 'versus', 'vs'])
        is_factual = any(term in user_message_lower 
                        for term in ['what is', 'how does', 'explain', 'define'])
        
        # Create simplified query tags
        query_tags = {
            'domains': ['code'] if is_code_related else [],
            'request_types': []
        }
        
        if is_comparison:
            query_tags['request_types'].append('comparison')
        if is_factual:
            query_tags['request_types'].append('explanation')
    
    # Generate appropriate response based on detected or inferred query type
    domains = query_tags.get('domains', [])
    request_types = query_tags.get('request_types', [])
    
    # Use appropriate response generation based on query type
    if 'code' in domains or any(tech in domains for tech in ['programming', 'technical']):
        response = generate_code_response()
        model_info = {
            'models_used': ['gpt-4', 'claude-3', 'gemini'],
            'rankings': [
                {'model': 'gpt-4', 'score': 0.92, 'reason': 'Best code structure and explanation'},
                {'model': 'claude-3', 'score': 0.88, 'reason': 'Good explanation but suboptimal code'},
                {'model': 'gemini', 'score': 0.79, 'reason': 'Missing edge case handling'}
            ],
            'blending': {
                'method': 'technical_blending',
                'contributing_models': ['gpt-4', 'claude-3'],
                'sections': [
                    {'title': 'Code Implementation', 'source_model': 'gpt-4'},
                    {'title': 'Explanation', 'source_model': 'claude-3'}
                ]
            }
        }
    elif 'comparison' in request_types:
        response = generate_comparison_response()
        model_info = {
            'models_used': ['claude-3', 'gpt-4', 'llama-3'],
            'rankings': [
                {'model': 'claude-3', 'score': 0.94, 'reason': 'Most balanced comparison'},
                {'model': 'gpt-4', 'score': 0.91, 'reason': 'Detailed but slightly biased'},
                {'model': 'llama-3', 'score': 0.82, 'reason': 'Less comprehensive'}
            ],
            'blending': {
                'method': 'comparison_blending',
                'contributing_models': ['claude-3', 'gpt-4'],
                'sections': [
                    {'title': 'Pros and Cons', 'source_model': 'claude-3'},
                    {'title': 'Detailed Analysis', 'source_model': 'gpt-4'}
                ]
            }
        }
    elif 'explanation' in request_types or 'factual' in domains:
        response = generate_factual_response()
        model_info = {
            'models_used': ['gpt-4', 'gemini', 'llama-3'],
            'rankings': [
                {'model': 'gemini', 'score': 0.89, 'reason': 'Most up-to-date information'},
                {'model': 'gpt-4', 'score': 0.87, 'reason': 'Well-structured explanation'},
                {'model': 'llama-3', 'score': 0.76, 'reason': 'Limited detail'}
            ],
            'blending': {
                'method': 'explanation_blending',
                'contributing_models': ['gemini', 'gpt-4'],
                'sections': [
                    {'title': 'Core Facts', 'source_model': 'gemini'},
                    {'title': 'Detailed Explanation', 'source_model': 'gpt-4'}
                ]
            }
        }
    else:
        response = generate_general_response()
        model_info = {
            'models_used': ['gpt-4', 'claude-3', 'gemini', 'llama-3'],
            'rankings': [
                {'model': 'claude-3', 'score': 0.90, 'reason': 'Most helpful response'},
                {'model': 'gpt-4', 'score': 0.88, 'reason': 'Well-structured but less specific'},
                {'model': 'gemini', 'score': 0.79, 'reason': 'Good but less detailed'},
                {'model': 'llama-3', 'score': 0.72, 'reason': 'Basic response'}
            ],
            'blending': {
                'method': 'general_blending',
                'contributing_models': ['claude-3', 'gpt-4'],
                'sections': [
                    {'title': 'Primary Response', 'source_model': 'claude-3'},
                    {'title': 'Additional Details', 'source_model': 'gpt-4'}
                ]
            }
        }
    
    # Ensure response has proper structure
    return response, model_info

# Removed mock code response generator - system now uses real AI models only

# Removed mock comparison response generator - system now uses real AI models only

@chat_api.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit feedback on an AI response for self-learning
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Missing data in request'}), 400
            
        # Required fields
        required_fields = ['conversation_id', 'memory_id', 'query', 'response', 'feedback_level']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        conversation_id = data['conversation_id']
        memory_id = data['memory_id']
        query = data['query']
        response = data['response']
        feedback_level = data['feedback_level']
        
        # Optional fields
        comments = data.get('comments', '')
        user_id = data.get('user_id', 'default')
        project_id = data.get('project_id')
        branch_id = data.get('branch_id', 'main')
        
        # Verify the memory exists
        memory = get_memory(memory_id)
        if not memory:
            return jsonify({'error': f'Memory not found: {memory_id}'}), 404
            
        # Additional metadata
        metadata = {
            'user_id': user_id,
            'project_id': project_id,
            'branch_id': branch_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Record the feedback
        feedback_id = record_user_feedback(
            conversation_id=conversation_id,
            query=query,
            response=response,
            feedback_level=feedback_level,
            comments=comments,
            metadata=metadata
        )
        
        logger.info(f"Recorded feedback {feedback_id} for memory {memory_id} with level {feedback_level}")
        
        return jsonify({
            'status': 'success',
            'feedback_id': feedback_id,
            'message': 'Feedback recorded successfully'
        })
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}", exc_info=True)
        return jsonify({
            'error': f"Failed to record feedback: {str(e)}",
            'message': "I'm sorry, I encountered an error processing your feedback."
        }), 500

@chat_api.route('/user_preferences', methods=['GET'])
def get_user_preference_data():
    """
    Get the learned preferences for a user based on their feedback history
    """
    try:
        user_id = request.args.get('user_id', 'default')
        
        # Get the preferences
        preferences = get_user_preferences(user_id)
        
        return jsonify(preferences)
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}", exc_info=True)
        return jsonify({
            'error': f"Failed to get user preferences: {str(e)}",
            'message': "I'm sorry, I encountered an error retrieving your preferences."
        }), 500

@chat_api.route('/fine_tuning/status', methods=['GET'])
def check_fine_tuning_readiness_status():
    """
    Check if there's enough data for fine-tuning and get the dataset status
    """
    try:
        min_entries = int(request.args.get('min_entries', 100))
        
        # Check for fine-tuning readiness
        dataset_path = check_fine_tuning_readiness(min_entries)
        
        if dataset_path:
            return jsonify({
                'ready': True,
                'dataset_path': dataset_path,
                'message': 'Fine-tuning dataset is ready',
                'entries': min_entries
            })
        else:
            return jsonify({
                'ready': False,
                'message': 'Not enough data for fine-tuning yet'
            })
    except Exception as e:
        logger.error(f"Error checking fine-tuning status: {str(e)}", exc_info=True)
        return jsonify({
            'error': f"Failed to check fine-tuning status: {str(e)}",
            'message': "I'm sorry, I encountered an error checking the fine-tuning status."
        }), 500

# Removed mock factual response generator - system now uses real AI models only

# Removed mock general response generator - system now uses real AI models only

# Removed mock greeting response generator - system now uses real AI models only
