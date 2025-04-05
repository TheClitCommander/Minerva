#!/usr/bin/env python3
"""
Minimal Chat Server for Minerva

This is a simplified version of the app.py that only serves the chat interface
and basic API endpoints without eventlet or websockets.
"""

import os
import sys
import uuid
import json
import time
import logging
import requests
import traceback
import random
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect
from dotenv import load_dotenv
import openai

# Add Minerva root directory to Python path to fix import errors
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
print(f"[STARTUP] ✅ Added project root to Python path: {project_root}")

# Import Think Tank components
try:
    from processor.ai_router import route_request, get_query_tags
    from processor.think_tank import process_with_think_tank
    from processor.ensemble_validator import rank_responses
    from processor.response_blender import blend_responses
    print("[STARTUP] ✅ Think Tank components successfully imported!")
    has_think_tank = True
except ImportError as e:
    print(f"[ERROR] ❌ Failed to import Think Tank components: {e}")
    has_think_tank = False

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"[STARTUP] ✅ Environment variables loaded from {env_path}")

# Define path for analytics storage
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"[STARTUP] ✅ Created data directory at {data_dir}")

analytics_file = os.path.join(data_dir, 'api_usage.json')

# Debug configuration
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
DEBUG_MEMORY_SYSTEM = os.environ.get('DEBUG_MEMORY', 'false').lower() == 'true'
DEBUG_MEMORY_DETAIL = os.environ.get('DEBUG_MEMORY_DETAIL', 'false').lower() == 'true'
USE_LOCAL_HISTORY = os.environ.get('USE_LOCAL_HISTORY', 'true').lower() == 'true'
TRACK_API_USAGE = os.environ.get('TRACK_API_USAGE', 'true').lower() == 'true'

# Get API key from environment
openai_api_key = os.environ.get('OPENAI_API_KEY')
if openai_api_key:
    print(f"[STARTUP] ✅ OpenAI API key found in environment variables")
else:
    print(f"[STARTUP] ⚠️ OpenAI API key not found in environment variables")
# Enable real API calls since we have a valid key
os.environ['USE_API'] = 'true'

# Debug and simulation configuration
os.environ['DEV_MODE'] = 'true'  # Enable development mode by default
os.environ['DETAILED_LOGGING'] = 'true'  # Enable detailed logging

# Extract debug mode setting
dev_mode = os.environ.get('DEV_MODE', 'true').lower() == 'true'

print(f"[STARTUP] ✅ Development mode enabled with detailed logging")
print(f"[STARTUP] {'✅ API calls ENABLED' if os.environ.get('USE_API', 'false').lower() == 'true' else '⚠️ API calls disabled'}")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('minerva-minimal')

# Initialize Flask app
app = Flask(__name__,
            static_folder='static',
            template_folder='templates',
            static_url_path='/static')

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'minerva_default_secret')

# Store active conversations and message history
active_conversations = {}
conversation_history = {}  # Stores message history for each conversation
MAX_CONVERSATION_HISTORY = 20  # Maximum number of messages to store per conversation

# Initialize logs directory
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Add file handler for detailed logging
file_handler = logging.FileHandler(os.path.join(logs_dir, 'minerva_chat.log'))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s'))
logger.addHandler(file_handler)

# Minerva Think Tank with proper integration and fallback
def get_ai_response(message, conversation_id, user_id, message_history=None):
    """Get a response using Minerva's Think Tank architecture with robust fallback."""
    try:
        # Log the incoming message
        logger.info(f"[USER_MESSAGE] Processing message from user {user_id}: {message}")
        
        # Use real Think Tank components if available
        if has_think_tank:
            logger.info(f"[THINK_TANK] 🧠 Using real Think Tank for message processing")
            
            # Step 1: Use the AI router to determine message characteristics
            routing_info = route_request(message)
            message_type = routing_info.get('message_type', 'general')
            logger.info(f"[AI_ROUTER] Message type detected: {message_type}")
            logger.info(f"[AI_ROUTER] Routing info: {routing_info}")
            
            # Include conversation context in logs for debugging
            if message_history:
                logger.info(f"[CONTEXT] Processing with {len(message_history)} previous messages in context")
            
            # Step 2: Process the message with the Think Tank architecture
            logger.info(f"[THINK_TANK] 🧠 Processing message: {message[:50]}...")
            # Extract routing info from the router
            model_priority = routing_info.get('model_priority', ['gpt-4o', 'claude-3-opus'])
            complexity = routing_info.get('complexity_score', 0.7)
            query_tags = routing_info.get('query_tags', {})
            
            # Prepare conversation context by retrieving relevant memories
            conversation_context = None
            if message_history and CONVERSATION_MEMORY_ENABLED:
                # Format the message history for use by AI models
                logger.info(f"[MEMORY] Including {len(message_history)} messages from conversation history")
                conversation_context = message_history
                
                # Get relevant facts and memories for this conversation
                if conversation_id:
                    relevant_memories = get_relevant_memories(
                        query=message,
                        max_results=5,
                        conversation_history=message_history
                    )
                    if relevant_memories:
                        logger.info(f"[MEMORY] Found {len(relevant_memories)} relevant memories for this conversation")
                        # Format memories for inclusion in the context
                        memory_context = format_memories_for_response(relevant_memories, message)
                        # Add memory context to query tags for Think Tank awareness
                        query_tags['memory_context'] = memory_context
                        # Update memory access statistics
                        update_memory_access(relevant_memories)
            
            # Call the Think Tank processor with the correct parameters
            think_tank_response = process_with_think_tank(
                message=message,
                model_priority=model_priority,
                complexity=complexity,
                query_tags=query_tags,
                conversation_id=conversation_id
            )
            
            # Extract responses from the Think Tank
            model_responses = think_tank_response.get('responses', {})
            logger.info(f"[THINK_TANK] 🧠 Successfully received responses from {len(model_responses)} models")
            
            # Convert model responses to the format expected by rank_responses
            # The ensemble_validator.rank_responses expects a dictionary of model_name -> response_text strings
            formatted_responses = {}
            for model_name, response_data in model_responses.items():
                # Extract the text from the response data
                if isinstance(response_data, str):
                    response_text = response_data
                elif isinstance(response_data, dict):
                    response_text = response_data.get('text', '')
                else:
                    response_text = str(response_data)
                    
                # Add to formatted responses dict
                formatted_responses[model_name] = response_text
            
            # Step 3: Rank and validate the responses
            ranked_responses = rank_responses(formatted_responses, message)
            logger.info(f"[ENSEMBLE] Ranked {len(ranked_responses)} responses")
            
            # Step 4: Blend the responses for the final output
            # Create proper query_tags dictionary based on message_type
            query_tags = {'request_types': [message_type] if message_type else []}
            blended_response = blend_responses(formatted_responses, ranked_responses, query_tags)
            api_response = blended_response.get('blended_response', '')
            logger.info(f"[BLENDER] Successfully blended responses, length: {len(api_response)}")
            
            # Use the real Think Tank response
            enhanced_response = api_response
            model_info = {
                "primary_model": "think_tank",
                "models_used": [model.get('model', 'unknown') for model in ranked_responses],
                "blending_method": "weighted"
            }
        else:
            # Fallback to simulation mode if Think Tank is not available
            logger.warning(f"[WARNING] 🚨 Think Tank not available, using simulation mode")
            
            # Step 1: Analyze the message to determine its characteristics (simulated)
            message_type = analyze_message_type(message)
            logger.info(f"[AI_ROUTER] Message type detected: {message_type}")
            
            # Step 2: Select the appropriate model based on the message type (simulated)
            selected_model = select_model_for_query(message, message_type)
            logger.info(f"[AI_ROUTER] Selected Model: {selected_model} for query: \"{message}\"")
            
            # Step 3: Attempt to call the OpenAI API but handle quota errors gracefully
            try:
                if openai_api_key and os.environ.get('USE_API', 'false').lower() == 'true':
                    # Try to use the real API if available and enabled
                    logger.info(f"[API_ROUTER] Attempting to use real OpenAI API")
                    api_response = call_openai_api(message, selected_model, message_history)
                    logger.info(f"[API_ROUTER] Successfully received API response")
                else:
                    # Use simulated response if API is not enabled
                    logger.info(f"[API_ROUTER] Using simulated response (API disabled or no key)")
                    raise Exception("Simulated response mode active - API disabled")
            except Exception as api_error:
                # Log more details about the API error for debugging
                error_type = type(api_error).__name__
                error_details = str(api_error)
                logger.warning(f"[API_ROUTER] API error ({error_type}): {error_details}")
                
                # Handle API failure gracefully with a high-quality simulation
                logger.warning(f"[API_ROUTER] Falling back to simulated response")
                api_response = generate_simulated_response(message, message_type, selected_model, message_history)
                logger.info(f"[API_ROUTER] Generated simulated response of length {len(api_response)}")
                
            # Process and enhance the response (would use ensemble_validator in real system)
            enhanced_response = process_ai_response(api_response, message_type, selected_model)
            
            # Create model info with rankings and blending info
            model_info = generate_model_info(message_type, selected_model)
        
        # Add debug information to model_info in dev mode
        if os.environ.get('DEV_MODE', 'true').lower() == 'true':
            model_info['debug'] = {
                'message_type': message_type,
                'api_status': 'simulated' if 'simulated' in str(api_response).lower() else 'real',
                'processing_time': f"{time.time() - time.time():.2f}s"
            }
        
        # Return a fully structured response
        return {
            "response": enhanced_response,
            "message_id": str(uuid.uuid4()),
            "model_info": model_info
        }
        
    except Exception as e:
        logger.error(f"[ERROR] AI request failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a fallback response with diagnostics
        fallback_response = "I apologize, but I'm having trouble processing your request right now. This may be due to high demand or a temporary system issue. Please try again in a moment."
        
        return {
            "response": fallback_response,
            "message_id": str(uuid.uuid4()),
            "model_info": {
                "primary_model": "fallback", 
                "error": str(e),
                "debug_info": {
                    "exception_type": type(e).__name__,
                    "trace": str(traceback.format_exc())[:200] + "..."
                }
            }
        }

def analyze_message_type(message):
    """Analyze message to determine its type (technical, creative, comparison, etc.)"""
    message = message.lower()
    
    # Simple keyword matching for demonstration
    if any(word in message for word in ['code', 'program', 'function', 'class', 'bug', 'error']):
        return "technical"
    elif any(word in message for word in ['compare', 'difference', 'versus', 'vs', 'better', 'pros and cons']):
        return "comparison"
    elif any(word in message for word in ['create', 'generate', 'write', 'story', 'poem', 'imagine']):
        return "creative"
    else:
        return "general"

def select_model_for_query(message, message_type):
    """Select the best model based on the query type."""
    # This mimics Minerva's model selection system
    model_capabilities = {
        "technical": ["gpt-4", "claude-3", "gemini-pro"],
        "comparison": ["claude-3", "gpt-4", "gemini-pro"],
        "creative": ["claude-3", "gpt-4", "gemini-pro"],
        "general": ["gpt-4", "claude-3", "gemini-pro"]
    }
    
    # Return the top model for this message type
    # In a full implementation, this would consider model availability
    return model_capabilities.get(message_type, ["gpt-4"])[0]

def call_openai_api(message, model, message_history=None):
    """Call OpenAI API with the provided message using the official Python library."""
    try:
        # Set the API key for the OpenAI client
        openai.api_key = openai_api_key
        
        # Start timing the API call for tracking usage
        start_time = time.time()
        
        # Map Minerva model names to OpenAI model names that are available with the current API key
        # Now using gpt-4 as it should be available with the backup API key
        model_mapping = {
            "gpt-4": "gpt-4",  # Use GPT-4 since we should have access with the backup key
            "claude-3": "gpt-4",  # Fallback to GPT-4 since Claude is not available
            "gemini-pro": "gpt-3.5-turbo"  # Fallback to GPT-3.5 for less complex queries
        }
        
        openai_model = model_mapping.get(model, "gpt-3.5-turbo")
        logger.info(f"[OPENAI_API] Using model: {openai_model}")
        
        # Create a system message to guide the AI's behavior
        system_message = {
            "role": "system", 
            "content": "You are Minerva, a helpful and knowledgeable AI assistant with extensive expertise in science, mathematics, coding, and general knowledge. Remember to reference previous parts of the conversation when relevant. Maintain context across interactions."
        }
        
        # Create message list starting with system message
        messages = [system_message]
        
        # Extract conversation topic and context for better memory retrieval
        conversation_topic = extract_conversation_topic(message, message_history)
        
        # Look up relevant long-term memories using semantic search with context
        relevant_memories = get_relevant_memories(
            query=message, 
            max_results=5,  # Increased from 3 to 5 for better context
            context=conversation_topic,
            conversation_history=message_history
        )
        
        if relevant_memories:
            # Group memories by category for better organization
            memory_by_category = {}
            for memory in relevant_memories:
                category = memory.get('category', 'general')
                if category not in memory_by_category:
                    memory_by_category[category] = []
                memory_by_category[category].append(memory)
            
            # Format memories by category in the context
            memory_context = "\n\nImportant context from my memory:\n"
            for category, memories in memory_by_category.items():
                memory_context += f"\n{category.capitalize()}:\n"
                for mem in memories:
                    memory_context += f"- {mem['content']}\n"
            
            messages.append({"role": "system", "content": memory_context})
            logger.info(f"[MEMORY] Including {len(relevant_memories)} relevant memory items across {len(memory_by_category)} categories")
        
        # Add conversation history if available
        if message_history and len(message_history) > 0:
            # Only include the messages themselves, not the metadata
            for msg in message_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            logger.info(f"[CONTEXT] Including {len(message_history)} previous messages in API request")
        
        # Add the current message
        messages.append({"role": "user", "content": message})
        
        # Estimate input tokens for tracking (rough approximation)
        input_text = ""
        for msg in messages:
            input_text += msg["content"]
        estimated_input_tokens = len(input_text) // 4  # Approximate: ~4 chars per token
        
        # Create a completion with the OpenAI API
        completion = openai.chat.completions.create(
            model=openai_model,
            messages=messages,
            temperature=0.7,
        )
        
        # End timing the API call
        end_time = time.time()
        response_time = end_time - start_time
        
        # Extract the response
        ai_response = completion.choices[0].message.content
        logger.info(f"[OPENAI_API] Response received (length: {len(ai_response)})")
        
        # Get token usage from the response if available
        total_tokens = 0
        if hasattr(completion, 'usage') and completion.usage is not None:
            total_tokens = completion.usage.total_tokens
        else:
            # Fallback to estimation if actual token count not available
            estimated_output_tokens = len(ai_response) // 4
            total_tokens = estimated_input_tokens + estimated_output_tokens
        
        # Track API usage for analytics
        if TRACK_API_USAGE:
            track_api_call(
                model=openai_model,
                tokens=total_tokens,
                response_time=response_time
            )
            logger.info(f"[ANALYTICS] Tracked API call: {openai_model}, {total_tokens} tokens, {response_time:.2f}s")
        
        # Opportunistically extract new facts for long-term memory
        detect_and_save_important_facts(message, ai_response)
        
        return ai_response
        
    except openai.APIError as e:
        logger.error(f"[OPENAI_API] OpenAI API error: {str(e)}")
        raise Exception(f"OpenAI API error: {str(e)}")
    except Exception as e:
        logger.error(f"[OPENAI_API] Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Error connecting to OpenAI API: {str(e)}")

def generate_simulated_response(message, message_type, model, message_history=None):
    """Generate a high-quality simulated response based on message type and complexity.
    This simulates Minerva's Think Tank architecture with multiple models and blending.
    
    Features enhanced memory integration for more personalized and contextually relevant responses:
    - Improved memory categorization (preferences, facts, experiences, instructions, relationships, health)
    - Priority-based memory retrieval using relevance, recency, and access frequency
    - Seamless incorporation of multiple relevant memories in conversational format
    - Automatic fact extraction and learning from conversations
    
    Args:
        message (str): The user message to respond to
        message_type (str): The type of message (technical, creative, factual, etc.)
        model (str): The selected model to use
        message_history (list, optional): Previous messages in the conversation
    
    Returns:
        str or dict: A simulated high-quality response, potentially with memory metadata
    """
    # Start timing for the simulated API call
    start_time = time.time()
    
    # Create base responses for different message types
    responses = {
        "technical": {
            "intro": "Here's a technical explanation:",
            "templates": [
                "This is a complex technical topic that involves several key concepts. First, {concept_1} refers to {explanation_1}. Second, {concept_2} involves {explanation_2}. The relationship between these concepts is important because {relationship}.",
                "From a technical perspective, we can break this down into components: {component_1}, {component_2}, and {component_3}. Each plays a crucial role in {overall_function}.",
                """When implementing this in code, you would typically follow these steps:
1. {step_1}
2. {step_2}
3. {step_3}

This approach ensures {benefit}."""
            ]
        },
        "comparison": {
            "intro": "Let me compare these concepts:",
            "templates": [
                """When comparing {item_1} and {item_2}, we need to consider several factors:

**Similarities:**
- {similarity_1}
- {similarity_2}

**Differences:**
- {difference_1}
- {difference_2}

**Which is better?** {conclusion}""",
                """There are important distinctions between {item_1} and {item_2}:

{item_1}:
- {attribute_1_1}
- {attribute_1_2}

{item_2}:
- {attribute_2_1}
- {attribute_2_2}

In conclusion, {conclusion}"""
            ]
        },
        "creative": {
            "intro": "Here's a creative response:",
            "templates": [
                "Imagine a world where {creative_element_1}. In this reality, {creative_element_2} would be commonplace, and people would {creative_element_3}.",
                "The story begins with {character} who discovers {discovery}. This leads to an adventure where {plot_development}, ultimately resulting in {conclusion}."
            ]
        },
        "general": {
            "intro": "Here's what you should know:",
            "templates": [
                "This question has several important aspects to consider. First, {point_1}. Additionally, {point_2}. It's also worth noting that {point_3}.",
                "The answer has both theoretical and practical components. From a theoretical standpoint, {theory}. In practice, this means {practical_application}.",
                """There are multiple perspectives on this topic:

1. {perspective_1}: {explanation_1}
2. {perspective_2}: {explanation_2}
3. {perspective_3}: {explanation_3}

Considering all these viewpoints, {conclusion}."""
            ]
        }
    }
    
    # Extract conversation topic for better context
    conversation_topic = extract_conversation_topic(message, message_history)
    logger.info(f"[TOPIC] Detected conversation topic: {conversation_topic}")
    
    # Get relevant memories for more personalized response
    # Include conversation context and history to improve memory relevance
    # Increase max_results to get a broader set of memories for better categorization
    relevant_memories = get_relevant_memories(
        query=message, 
        max_results=10, 
        context=conversation_topic,
        conversation_history=message_history
    )
    
    # Determine if automatic fact extraction should happen for this message
    should_extract_facts = True
    lower_message = message.lower()
    
    # Don't extract facts from very short messages or questions
    if len(message.split()) < 5 or message.endswith('?') or any(word in lower_message for word in ['who', 'what', 'when', 'where', 'why', 'how']):
        should_extract_facts = False
    
    # Extract potential facts from user message for memory learning
    memory_pending_confirmation = None
    if should_extract_facts:
        extracted_facts = extract_facts_from_message(message, confidence_threshold=0.6)
        if extracted_facts:
            logger.info(f"[MEMORY] Extracted {len(extracted_facts)} potential facts from message")
            # For medium confidence facts, we'll confirm with the user
            medium_confidence_facts = [f for f in extracted_facts 
                                     if f.get('confidence', 0) >= 0.6 and f.get('confidence', 0) < 0.85]
            
            # High confidence facts get automatically stored
            high_confidence_facts = [f for f in extracted_facts if f.get('confidence', 0) >= 0.85]
            
            # Store high confidence facts without confirmation
            for fact in high_confidence_facts:
                memory_id = str(uuid.uuid4())
                memory = {
                    'id': memory_id,
                    'content': fact['content'],
                    'category': fact['category'],
                    'source': 'conversation_auto',
                    'confidence': fact['confidence'],
                    'created_at': time.time(),
                    'last_accessed': time.time(),
                    'access_count': 1,
                    'tags': ['auto_extracted', fact['category']]
                }
                # Check if it's too similar to existing memories
                similar_memories = get_relevant_memories(fact['content'], max_results=1)
                if not similar_memories or similar_memories[0].get('relevance', 0) < 0.9:
                    add_memory(memory)
                    logger.info(f"[MEMORY] Automatically saved high-confidence fact: {fact['content']}")
            
            # Save one medium confidence fact for confirmation
            if medium_confidence_facts:
                memory_pending_confirmation = medium_confidence_facts[0]
                logger.info(f"[MEMORY] Requesting confirmation for fact: {memory_pending_confirmation['content']}")
    
    # Format memory context to naturally include in responses with enhanced categorization
    # This uses our improved format_memories_for_response function with better prioritization
    memory_info = format_memories_for_response(relevant_memories, message, message_type)
    
    # Log retrieved memory categories for debugging
    if memory_info['has_memories']:
        logger.info(f"[MEMORY] Retrieved {len(memory_info['all_memories'])} memories")
        for category in ['preferences', 'facts', 'experiences', 'instructions', 'relationships', 'health']:
            if memory_info.get(category):
                logger.info(f"[MEMORY] {category.capitalize()}: {len(memory_info[category])}")
    
    # Process explicit memory commands using the handle_memory_command function
    processed_message, command_response, command_detected = handle_memory_command(message)
    memory_command = None
    
    # If a memory command was detected and processed
    if command_detected:
        # Set memory_command for inclusion in the response
        if command_response:
            # Create a memory command response object for the client
            memory_command = {
                'action': 'command_processed',
                'is_command': True,
                'response': command_response
            }
            logger.info(f"[MEMORY] Processed memory command: {message[:50]}...")
            
        # If the command completely handled the message, we'll use the command response
        # as the primary response
        if not processed_message:  # The command consumed the entire message
            # Create a response that acknowledges the memory command
            generated_response = command_response
            
            # Return both the generated response and memory metadata
            return {
                'response': generated_response,
                'memory_info': {
                    'command_processed': True,
                    'command_response': command_response
                }
            }
        
        # Otherwise, continue processing with the processed message
        # (which might have had the command removed)
        message = processed_message
    
    # Identify key terms in the user's message for more relevant responses
    lower_message = message.lower()
    
    # Extract potential topics and concepts from the user message
    words = re.findall(r'\b\w+\b', lower_message)
    potential_topics = [w for w in words if len(w) > 3 and w not in 
                        ['what', 'when', 'where', 'which', 'would', 'could', 'should', 'this', 'that',
                         'these', 'those', 'with', 'from', 'about', 'they', 'their', 'there', 'here']]
    
    # Select relevant topics
    topics = potential_topics[:3] if potential_topics else ["the subject", "this topic", "the concept"]
    
    # Common placeholders for all response types
    placeholders = {
        # Technical placeholders
        "concept_1": f"{topics[0] if topics else 'this concept'}",
        "explanation_1": "a fundamental principle that governs how the system operates",
        "concept_2": f"{topics[1] if len(topics) > 1 else 'the implementation'}",
        "explanation_2": "the practical application of theoretical principles",
        "relationship": "they work together to create a coherent system",
        "component_1": "the input processing layer",
        "component_2": "the transformation logic",
        "component_3": "the output generation mechanism",
        "overall_function": "ensuring optimal performance",
        "step_1": "Initialize the environment and configure parameters",
        "step_2": "Process the input data through the transformation pipeline",
        "step_3": "Validate and optimize the output for the specific use case",
        "benefit": "a robust and maintainable solution",
        
        # Comparison placeholders
        "item_1": f"{topics[0] if topics else 'the first approach'}",
        "item_2": f"{topics[1] if len(topics) > 1 else 'the alternative approach'}",
        "similarity_1": "Both serve similar core functions in their respective domains",
        "similarity_2": "Both require similar underlying infrastructure",
        "difference_1": "Their implementation approaches differ significantly",
        "difference_2": "They optimize for different performance characteristics",
        "conclusion": "the best choice depends on your specific requirements and constraints",
        "attribute_1_1": "Optimized for performance and scalability",
        "attribute_1_2": "Requires more initial setup and configuration",
        "attribute_2_1": "Easier to implement and maintain",
        "attribute_2_2": "May have limitations for complex use cases",
        
        # Creative placeholders
        "creative_element_1": "technology and nature have perfectly merged",
        "creative_element_2": "instant knowledge transfer",
        "creative_element_3": "experience life through multiple perspectives simultaneously",
        "character": "a curious explorer",
        "discovery": "a hidden pattern that changes everything",
        "plot_development": "unexpected alliances form and new possibilities emerge",
        
        # General placeholders
        "point_1": "the historical context provides important background",
        "point_2": "current trends indicate a shift in approach",
        "point_3": "future developments may change our understanding",
        "theory": "established principles suggest certain patterns will emerge",
        "practical_application": "implementations need to account for real-world constraints",
        "perspective_1": "Traditional view",
        "explanation_1": "follows established patterns and proven approaches",
        "perspective_2": "Modern interpretation",
        "explanation_2": "incorporates recent innovations and research findings",
        "perspective_3": "Future-focused approach",
        "explanation_3": "anticipates emerging trends and adaptive requirements",
        "conclusion": "a balanced approach that draws from multiple viewpoints often yields the best results"
    }
    
    # Specific customizations based on message content
    if "quantum" in lower_message:
        placeholders["concept_1"] = "quantum superposition"
        placeholders["explanation_1"] = "the ability of quantum systems to exist in multiple states simultaneously"
        placeholders["concept_2"] = "quantum entanglement"
        placeholders["explanation_2"] = "a phenomenon where entangled particles remain connected regardless of distance"
        
    elif "python" in lower_message or "code" in lower_message or "program" in lower_message:
        placeholders["concept_1"] = "efficient algorithms"
        placeholders["explanation_1"] = "code that minimizes computational complexity and resource usage"
        placeholders["concept_2"] = "clean architecture"
        placeholders["explanation_2"] = "organizing code for maintainability, testability, and scalability"
        placeholders["step_1"] = "Define your class structure and interfaces"
        placeholders["step_2"] = "Implement the core logic with appropriate error handling"
        placeholders["step_3"] = "Add tests to verify functionality and prevent regressions"
        
    elif "ai" in lower_message or "machine learning" in lower_message:
        placeholders["concept_1"] = "neural networks"
        placeholders["explanation_1"] = "computational models inspired by the human brain's structure"
        placeholders["concept_2"] = "training methodologies"
        placeholders["explanation_2"] = "processes for optimizing model parameters with data"
    
    # Select the appropriate response type based on message_type
    response_type = responses.get(message_type, responses["general"])
    
    # Select a template randomly from the available templates for variety
    template = random.choice(response_type["templates"])
    
    # Fill in the template with the placeholders
    response = template
    for key, value in placeholders.items():
        response = response.replace("{" + key + "}", value)
    
    # Prepare the final response
    memory_acknowledgment = ""
    
    # Handle explicit memory commands
    if memory_command:
        if memory_command['action'] == 'add':
            memory_acknowledgment = f"\n\nI've saved this to my memory: '{memory_command['content']}'"
        elif memory_command['action'] == 'delete':
            if memory_command['count'] > 0:
                memory_acknowledgment = f"\n\nI've removed {memory_command['count']} memories related to '{memory_command['content']}'"
            else:
                memory_acknowledgment = f"\n\nI couldn't find any memories related to '{memory_command['content']}'"
    
    # Integrate memory data more effectively into responses
    context_prefix = ""
    memory_body = ""
    
    # Check if we have memories to incorporate
    if memory_info and memory_info['has_memories']:
        # Add the primary memory context as a natural prefix
        if memory_info['context']:
            context_prefix = f"{memory_info['context']}\n\n"
        
        # Enhance response with category-specific memory incorporation based on message type
        memory_references = []
        
        # Technical queries can benefit from remembered technical preferences or instructions
        if message_type == 'technical':
            if memory_info['preferences']:
                tech_prefs = [p for p in memory_info['preferences'] if any(word in p.lower() for word in ['prefer', 'like', 'use', 'code', 'program', 'develop'])][:2]
                if tech_prefs:
                    memory_references.append(f"Based on your preferences, I know you {' and you '.join(tech_prefs)}")
                    
            if memory_info['instructions']:
                tech_instructions = memory_info['instructions'][:1]
                if tech_instructions:
                    memory_references.append(f"You've previously asked me to {tech_instructions[0]}")
        
        # Comparison queries benefit from past preferences for context
        elif message_type == 'comparison':
            if memory_info['preferences']:
                memory_references.append(f"Considering your previously stated preferences (you {memory_info['preferences'][0]}), here's my comparison")
        
        # Creative queries can be enhanced with personal experiences and facts
        elif message_type == 'creative':
            if memory_info['experiences']:
                memory_references.append(f"Drawing inspiration from your experience where you {memory_info['experiences'][0]}")
        
        # General queries get broader memory context
        elif message_type == 'general':
            # Mix memories from different categories for a well-rounded context
            priority_memories = []
            
            # Create a representative sample across categories
            for category in ['preferences', 'facts', 'experiences', 'instructions', 'relationships', 'health']:
                if memory_info.get(category) and len(memory_info[category]) > 0:
                    priority_memories.append((category, memory_info[category][0]))
            
            # Convert top 2 memories to natural language references
            for i, (category, content) in enumerate(priority_memories[:2]):
                if category == 'preferences':
                    memory_references.append(f"you've mentioned that you {content}")
                elif category == 'facts':
                    memory_references.append(f"I recall that you {content}")
                elif category == 'experiences':
                    memory_references.append(f"you've previously {content}")
                elif category == 'instructions':
                    memory_references.append(f"you've asked me to {content}")
                elif category == 'relationships':
                    memory_references.append(f"you've told me about {content}")
                elif category == 'health':
                    memory_references.append(f"you've shared that {content}")
        
        # Format additional memory references for the body of the response if appropriate
        if memory_references and not context_prefix:  # Only use these if we don't already have a context prefix
            if len(memory_references) == 1:
                memory_body = f"\n\nI've taken into account that {memory_references[0]}."
            elif len(memory_references) >= 2:
                memory_body = f"\n\nI've considered what I know about you: {memory_references[0]} and {memory_references[1]}."
    
    
    # Add an introduction for context
    base_response = f"{context_prefix}{response_type['intro']}\n\n{response}{memory_body}{memory_acknowledgment}"
    
    # Add a simulated model attribution for transparency
    base_response += f"\n\n[Simulated response using the Minerva Think Tank architecture]"
    
    # If we have a memory pending confirmation, add it to the response metadata
    if memory_pending_confirmation:
        fact_content = memory_pending_confirmation['content']
        fact_category = memory_pending_confirmation['category']
        
        # Add the confirmation request to the response text
        # Make the memory confirmation more natural and conversational
        confirmation_phrases = [
            f"\n\nBy the way, would you like me to remember that you {fact_content}? This helps me provide more personalized responses in the future.",
            f"\n\nI noticed that you {fact_content}. Would you like me to remember this for future conversations?",
            f"\n\nShould I add to my memory that you {fact_content}? I can use this to better personalize our future interactions."
        ]
        confirmation_message = random.choice(confirmation_phrases)
        response_with_confirmation = base_response + confirmation_message
        
        # Return the response with memory confirmation metadata for the frontend
        return {
            'text': response_with_confirmation,
            'memory_confirmation': {
                'id': str(uuid.uuid4()),  # Confirmation ID for frontend to reference
                'fact': fact_content,
                'category': fact_category,
                'confidence': memory_pending_confirmation['confidence']
            }
        }
    
    # Otherwise, just return the text response
    
    # End timing for the simulated API call
    end_time = time.time()
    response_time = end_time - start_time
    
    # Estimate token usage based on input and output lengths
    input_tokens = len(message) // 4  # Approximate: ~4 chars per token
    output_tokens = len(base_response) // 4 if isinstance(base_response, str) else 0
    total_tokens = input_tokens + output_tokens
    
    # Track the API call for analytics
    if TRACK_API_USAGE:
        # Use simulated-{model} format to distinguish from real API calls
        track_api_call(
            model=f"simulated-{model}",
            tokens=total_tokens,
            response_time=response_time
        )
        logger.info(f"[ANALYTICS] Tracked simulated API call: {model}, {total_tokens} tokens, {response_time:.2f}s")
    
    return base_response

def process_ai_response(response, message_type, model):
    """Process and enhance the AI response based on message type."""
    # In a full implementation, this would use ensemble_validator.py for blending
    # For now, just log that we would apply enhancements
    logger.info(f"[RESPONSE_PROCESSOR] Enhancing response for message type: {message_type}")
    
    # For simulated responses, add model-specific formatting enhancements
    if "[Simulated response" in response:
        if message_type == "technical" and "code" in response.lower():
            # Ensure code blocks are properly formatted
            response = re.sub(r'```(?!\w)', '```python', response)
        
        # Add paragraph breaks for better readability if needed
        if len(response) > 500 and response.count('\n\n') < 3:
            parts = response.split('. ')
            if len(parts) > 5:
                # Insert paragraph breaks every few sentences for readability
                for i in range(3, len(parts), 3):
                    if i < len(parts):
                        parts[i] = '\n\n' + parts[i]
                response = '. '.join(parts)
    
    return response

def generate_model_info(message_type, primary_model):
    """Generate model info with rankings and blending data."""
    # This mimics Minerva's model_info structure
    # In a full implementation, this would come from ensemble_validator.py
    
    # Model confidence scores based on message type
    confidence_scores = {
        "technical": {"gpt-4": 0.95, "claude-3": 0.92, "gemini-pro": 0.88},
        "comparison": {"claude-3": 0.94, "gpt-4": 0.91, "gemini-pro": 0.85},
        "creative": {"claude-3": 0.93, "gpt-4": 0.90, "gemini-pro": 0.87},
        "general": {"gpt-4": 0.92, "claude-3": 0.90, "gemini-pro": 0.89}
    }
    
    # Get scores for this message type
    scores = confidence_scores.get(message_type, {"gpt-4": 0.90, "claude-3": 0.85, "gemini-pro": 0.80})
    
    # Generate reasoning for each model
    reasoning = {
        "gpt-4": "Provided the most comprehensive and accurate technical details.",
        "claude-3": "Good response with clear explanations but missing some technical depth.",
        "gemini-pro": "Solid response but less detailed than the other models."
    }
    
    # Different reasoning based on message type
    if message_type == "comparison":
        reasoning = {
            "gpt-4": "Strong comparative analysis with balanced perspective.",
            "claude-3": "Excellent at highlighting key differences and providing balanced evaluation.",
            "gemini-pro": "Good comparison but not as nuanced as the other models."
        }
    elif message_type == "creative":
        reasoning = {
            "gpt-4": "Creative and engaging response with good structure.",
            "claude-3": "Highly creative with excellent narrative quality and originality.",
            "gemini-pro": "Creative but less developed than the other models."
        }
    
    # Create rankings based on the scores
    rankings = []
    for model, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        rankings.append({
            "model": model,
            "score": score,
            "reasoning": reasoning.get(model, "Provided a standard response.")
        })
    
    # Generate blending information
    blend_strategy = "technical" if message_type == "technical" else \
                    "comparison" if message_type == "comparison" else \
                    "creative" if message_type == "creative" else "general"
    
    # Based on the message type, determine model contributions
    if message_type == "technical":
        contributions = {"gpt-4": 60, "claude-3": 30, "gemini-pro": 10}
    elif message_type == "comparison":
        contributions = {"claude-3": 60, "gpt-4": 30, "gemini-pro": 10}
    elif message_type == "creative":
        contributions = {"claude-3": 50, "gpt-4": 40, "gemini-pro": 10}
    else:  # general
        contributions = {"gpt-4": 50, "claude-3": 40, "gemini-pro": 10}
    
    return {
        "primary_model": primary_model,
        "rankings": rankings,
        "blending": {
            "strategy": blend_strategy,
            "contributions": contributions
        }
    }

# Routes
@app.route('/')
def index():
    """Redirect to chat interface."""
    return redirect('/chat')

@app.route('/memories')
def memories():
    """API endpoint for memories - returns empty array for minimal server."""
    return jsonify({"status": "success", "memories": []})

@app.route('/api/memories')
def api_memories():
    """API endpoint for all memories."""
    memories = get_all_memories()
    return jsonify({"status": "success", "memories": memories})

@app.route('/api/memories/list', methods=['GET'])
def list_memories():
    """Advanced API endpoint to list memories with filtering and sorting options.
    
    Supported query parameters:
    - category: Filter by memory category (preference, fact, experience, etc.)
    - source: Filter by where the memory came from (user_explicit, conversation_auto, etc.)
    - sort_by: Field to sort by (created_at, last_accessed, access_count)
    - sort_order: asc or desc (default: desc)
    - limit: Maximum number of memories to return (default: 50)
    - tags: Comma-separated list of tags to filter by
    - search: Text search within memory content
    
    Returns:
        JSON: Filtered, sorted list of memories with metadata
    """
    try:
        # Get all memories and prepare for filtering
        all_memories = get_all_memories()
        
        # Get query parameters for filtering
        category = request.args.get('category')
        source = request.args.get('source')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        limit = int(request.args.get('limit', 50))
        tags_param = request.args.get('tags')
        search_text = request.args.get('search')
        
        # Parse tags if provided
        tags = tags_param.split(',') if tags_param else []
        
        # Filter memories based on parameters
        filtered_memories = all_memories
        
        if category:
            filtered_memories = [m for m in filtered_memories if m.get('category') == category]
        
        if source:
            filtered_memories = [m for m in filtered_memories if m.get('source') == source]
        
        if tags:
            filtered_memories = [m for m in filtered_memories if 
                               any(tag in m.get('tags', []) for tag in tags)]
        
        if search_text:
            search_lower = search_text.lower()
            filtered_memories = [m for m in filtered_memories if 
                               search_lower in m.get('content', '').lower()]
        
        # Sort memories based on parameters
        if sort_by in ['created_at', 'last_accessed', 'access_count']:
            reverse = (sort_order.lower() == 'desc')
            filtered_memories.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        
        # Apply limit
        limited_memories = filtered_memories[:limit]
        
        # Add metadata to response
        response = {
            'status': 'success',
            'memories': limited_memories,
            'total_count': len(all_memories),
            'filtered_count': len(filtered_memories),
            'returned_count': len(limited_memories)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error listing memories: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/memories/search')
def api_memories_search():
    """API endpoint for searching memories."""
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    tags = request.args.getlist('tag')
    max_results = int(request.args.get('max_results', 50))
    
    memories = get_all_memories()
    
    # Filter memories based on search parameters
    if query:
        memories = [m for m in memories if query.lower() in m.get('content', '').lower()]
    
    if category:
        memories = [m for m in memories if m.get('category', '') == category]
        
    if tags:
        memories = [m for m in memories if any(tag in m.get('tags', []) for tag in tags)]
    
    # Limit the number of results
    memories = memories[:max_results]
    
    return jsonify({"status": "success", "memories": memories})

@app.route('/api/memories/add', methods=['POST'])
def api_memories_add():
    """API endpoint for adding a new memory."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        content = data.get('content')
        if not content:
            return jsonify({"status": "error", "message": "Content is required"}), 400
            
        category = data.get('category', 'general')
        tags_string = data.get('tags', '')
        importance = int(data.get('importance', 5))
        
        # Convert tags string to list
        tags = [tag.strip() for tag in tags_string.split(',')] if tags_string else []
        
        # Save the memory
        memory_id = save_memory(
            content=content,
            source='ui_added',
            tags=tags,
            category=category,
            importance=importance
        )
        
        return jsonify({
            "status": "success", 
            "message": "Memory added successfully",
            "memory_id": memory_id
        })
    except Exception as e:
        logger.error(f"Error adding memory: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
        
@app.route('/api/memories/delete/<memory_id>', methods=['DELETE'])
def api_memories_delete(memory_id):
    """API endpoint for deleting a memory."""
    try:
        # Load existing memories
        memories = get_all_memories()
        
        # Find the memory to delete
        memory_index = None
        for i, memory in enumerate(memories):
            if memory.get('id') == memory_id:
                memory_index = i
                break
                
        if memory_index is None:
            return jsonify({"status": "error", "message": "Memory not found"}), 404
            
        # Remove the memory
        deleted_memory = memories.pop(memory_index)
        
        # Save the updated memories list
        with open(memory_file, 'w') as f:
            json.dump(memories, f, indent=2)
            
        return jsonify({
            "status": "success", 
            "message": "Memory deleted successfully",
            "memory_id": memory_id
        })
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/api/memories/update/<memory_id>', methods=['PUT'])
def api_memories_update(memory_id):
    """API endpoint for updating an existing memory.
    
    This allows users to edit their stored memories, providing full control over
    their memory database.
    
    Args:
        memory_id (str): The ID of the memory to update
        
    Returns:
        JSON: Status message indicating success or failure
    """    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        # Create update data dictionary
        update_data = {}
        
        # Only include fields that are provided in the request
        if 'content' in data:
            update_data['content'] = data['content']
            
        if 'category' in data:
            update_data['category'] = data['category']
            
        if 'tags' in data:
            # Handle tags as either string or list
            tags = data['tags']
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')] if tags else []
            update_data['tags'] = tags
            
        if 'importance' in data:
            update_data['importance'] = int(data['importance'])
            
        if 'confidence' in data:
            update_data['confidence'] = float(data['confidence'])
        
        # Always add modified timestamp
        update_data['modified_at'] = time.time()
        
        # Update the memory
        success = update_memory(memory_id, update_data)
        
        if success:
            return jsonify({
                "status": "success", 
                "message": "Memory updated successfully",
                "memory_id": memory_id
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"Memory with ID {memory_id} not found"
            }), 404
    
    except Exception as e:
        logger.error(f"Error updating memory: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
            
        return jsonify({
            "status": "success",
            "message": "Memory deleted successfully",
            "deleted": deleted_memory
        })
    except Exception as e:
        logger.error(f"Error deleting memory: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/analytics')
def analytics():
    """Display the analytics dashboard page.
    
    This page shows comprehensive API usage statistics, including:
    - API calls per model with detailed charts
    - Token usage tracking with cost estimates
    - Response time analytics
    - Usage trends over time
    """
    if not TRACK_API_USAGE:
        return render_template('message.html', 
                               title='Analytics Disabled',
                               message='API usage tracking is disabled. Enable TRACK_API_USAGE to view analytics.')
    
    # Get analytics data directly rather than via API request
    analytics_data = get_api_usage_stats()
    
    # Separate real and simulated API calls
    real_models = {}
    simulated_models = {}
    
    for model, stats in analytics_data.items():
        if model.startswith('simulated-'):
            simulated_models[model] = stats
        else:
            real_models[model] = stats
    
    # Process data for templates
    return render_template('analytics.html', 
                          real_models=real_models,
                          simulated_models=simulated_models,
                          total_calls=sum(stats.get('calls', 0) for stats in analytics_data.values()),
                          total_tokens=sum(stats.get('tokens', 0) for stats in analytics_data.values()))
    real_model_usage = []
    for model, stats in real_models.items():
        real_model_usage.append({
            "model": model,
            "count": stats.get('count', 0),
            "tokens": stats.get('total_tokens', 0),
            "avg_time": round(stats.get('avg_response_time', 0), 2),
            "estimated_cost": round(stats.get('estimated_cost', 0), 4),
            "last_used": datetime.fromtimestamp(stats.get('last_used', time.time())).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    simulated_model_usage = []
    for model, stats in simulated_models.items():
        # Clean up the model name by removing the 'simulated-' prefix
        display_name = model.replace('simulated-', '') + ' (Simulated)'
        simulated_model_usage.append({
            "model": display_name,
            "count": stats.get('count', 0),
            "tokens": stats.get('total_tokens', 0),
            "avg_time": round(stats.get('avg_response_time', 0), 2),
            "estimated_cost": round(stats.get('estimated_cost', 0), 4),
            "last_used": datetime.fromtimestamp(stats.get('last_used', time.time())).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # Sort by usage count (descending)
    real_model_usage.sort(key=lambda x: x["count"], reverse=True)
    simulated_model_usage.sort(key=lambda x: x["count"], reverse=True)
    
    # Calculate metrics for real API calls
    real_total_calls = sum(item["count"] for item in real_model_usage)
    real_total_tokens = sum(item["tokens"] for item in real_model_usage)
    real_total_cost = sum(item["estimated_cost"] for item in real_model_usage)
    
    # Calculate metrics for simulated API calls
    sim_total_calls = sum(item["count"] for item in simulated_model_usage)
    sim_total_tokens = sum(item["tokens"] for item in simulated_model_usage)
    
    # Get response quality metrics if available
    quality_metrics = get_response_quality_metrics()
    
    # Prepare JSON data for charts
    import json
    chart_data = {
        # Real API data
        'realLabels': [model['model'] for model in real_model_usage],
        'realCallCounts': [model['count'] for model in real_model_usage],
        'realTokenCounts': [model['tokens'] for model in real_model_usage],
        'realResponseTimes': [model['avg_time'] for model in real_model_usage],
        'realCosts': [model['estimated_cost'] for model in real_model_usage],
        
        # Simulated API data
        'simLabels': [model['model'] for model in simulated_model_usage],
        'simCallCounts': [model['count'] for model in simulated_model_usage],
        'simTokenCounts': [model['tokens'] for model in simulated_model_usage],
        'simResponseTimes': [model['avg_time'] for model in simulated_model_usage],
        
        # Summary data
        'totalRealCalls': real_total_calls,
        'totalSimCalls': sim_total_calls
    }
    
    return render_template(
        'analytics.html',
        real_model_usage=real_model_usage,
        simulated_model_usage=simulated_model_usage,
        real_total_calls=real_total_calls,
        real_total_tokens=real_total_tokens,
        real_total_cost=round(real_total_cost, 2),
        sim_total_calls=sim_total_calls,
        sim_total_tokens=sim_total_tokens,
        response_quality=quality_metrics.get('avg_quality', 4.7),
        avg_response_time=quality_metrics.get('avg_response_time', 2.1),
        feedback_count=quality_metrics.get('feedback_count', 0),
        page_title="Minerva Analytics",
        chart_data_json=json.dumps(chart_data)
    )

@app.route('/api/analytics')
def api_analytics():
    """API endpoint for analytics data.
    
    Returns detailed analytics about API usage, including:
    - Total API calls per model
    - Token usage by model
    - Estimated cost (if pricing info available)
    - Average response times
    - Response quality metrics
    """
    # Get actual usage statistics
    usage_stats = get_api_usage_stats()
    
    # Format for the frontend display
    model_usage = []
    for model, stats in usage_stats.items():
        model_usage.append({
            "model": model,
            "count": stats.get('count', 0),
            "tokens": stats.get('total_tokens', 0),
            "avg_time": round(stats.get('avg_response_time', 0), 2),
            "estimated_cost": round(stats.get('estimated_cost', 0), 4)
        })
    
    # Sort by usage count (descending)
    model_usage.sort(key=lambda x: x["count"], reverse=True)
    
    # Calculate overall metrics
    total_calls = sum(item["count"] for item in model_usage)
    total_tokens = sum(item["tokens"] for item in model_usage)
    total_cost = sum(item["estimated_cost"] for item in model_usage)
    
    # Get response quality metrics if available
    quality_metrics = get_response_quality_metrics()
    
    return jsonify({
        "status": "success",
        "data": {
            "model_usage": model_usage,
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 2),
            "response_quality": quality_metrics.get('avg_quality', 4.7),
            "avg_response_time": quality_metrics.get('avg_response_time', 2.1)
        }
    })

@app.route('/settings')
def settings():
    """Placeholder route for settings page."""
    return jsonify({"status": "success", "message": "Settings page not available in minimal server"})

@app.route('/knowledge')
def knowledge():
    """Memory management page."""
    # Get all memories to display
    memories = get_all_memories()
    # Group memories by category
    memories_by_category = {}
    for memory in memories:
        category = memory.get('category', 'general')
        if category not in memories_by_category:
            memories_by_category[category] = []
        memories_by_category[category].append(memory)
    
    # Get total count
    total_memories = len(memories)
    return render_template('memories.html', 
                          memories=memories, 
                          memories_by_category=memories_by_category,
                          total_memories=total_memories)

@app.route('/api/knowledge')
def api_knowledge():
    """API endpoint for getting all knowledge data."""
    memories = get_all_memories()
    return jsonify({"status": "success", "memories": memories})

@app.route('/api/knowledge/search', methods=['GET'])
def api_knowledge_search():
    """API endpoint for searching memories."""
    query = request.args.get('query', '')
    if not query:
        return jsonify({"status": "error", "message": "No query provided"})
    
    # Get context from search parameters
    context = request.args.get('context', '')
    max_results = int(request.args.get('max_results', 10))
    
    # Use our semantic search with context
    memories = get_relevant_memories(query, max_results, context)
    
    # Add relevance score for UI visualization
    for memory in memories:
        # Add a relevance score if not already present
        if 'relevance' not in memory:
            memory['relevance'] = round(random.uniform(0.7, 1.0), 2)  # Placeholder for demo
    
    return jsonify({
        "status": "success", 
        "memories": memories,
        "query": query,
        "context": context
    })

@app.route('/api/knowledge/add', methods=['POST'])
def api_knowledge_add():
    """API endpoint for adding a new memory."""
    data = request.json
    if not data or 'content' not in data:
        return jsonify({"status": "error", "message": "No content provided"})
    
    # Extract memory fields
    content = data.get('content', '').strip()
    category = data.get('category', 'general')
    source = data.get('source', 'user')
    confidence = float(data.get('confidence', 1.0))
    
    if not content:
        return jsonify({"status": "error", "message": "Content cannot be empty"})
    
    # Check if similar memory already exists using semantic search
    similar_memories = get_relevant_memories(content, max_results=1)
    is_duplicate = False
    
    if similar_memories and similar_memories[0].get('relevance', 0) > 0.8:
        # Found very similar memory, update it instead of creating new one
        memory_id = similar_memories[0]['id']
        update_memory(memory_id, {
            'content': content,  # Use new content
            'category': category,
            'source': source,
            'confidence': confidence,
            'last_accessed': time.time(),
            'access_count': similar_memories[0].get('access_count', 0) + 1
        })
        is_duplicate = True
        memory = get_memory_by_id(memory_id)
        status_message = "Memory updated due to similarity with existing memory"
    else:
        # Create new memory
        memory_id = str(uuid.uuid4())
        memory = {
            'id': memory_id,
            'content': content,
            'category': category,
            'source': source,
            'confidence': confidence,
            'created_at': time.time(),
            'last_accessed': time.time(),
            'access_count': 1
        }
        add_memory(memory)
        status_message = "Memory added successfully"
    
    return jsonify({
        "status": "success", 
        "message": status_message,
        "memory": memory,
        "is_duplicate": is_duplicate
    })

@app.route('/api/knowledge/delete/<memory_id>', methods=['DELETE'])
def api_knowledge_delete(memory_id):
    """API endpoint for deleting a memory."""
    if not memory_id:
        return jsonify({"status": "error", "message": "No memory ID provided"})
    
    # Check if memory exists
    memory = get_memory_by_id(memory_id)
    if not memory:
        return jsonify({"status": "error", "message": "Memory not found"})
    
    # Delete the memory
    delete_memory(memory_id)
    
    return jsonify({"status": "success", "message": "Memory deleted successfully"})

@app.route('/api/knowledge/update/<memory_id>', methods=['PUT'])
def api_knowledge_update(memory_id):
    """API endpoint for updating a memory."""
    data = request.json
    if not memory_id or not data:
        return jsonify({"status": "error", "message": "Missing memory ID or update data"})
    
    # Check if memory exists
    memory = get_memory_by_id(memory_id)
    if not memory:
        return jsonify({"status": "error", "message": "Memory not found"})
    
    # Update the memory
    update_memory(memory_id, data)
    updated_memory = get_memory_by_id(memory_id)
    
    return jsonify({
        "status": "success", 
        "message": "Memory updated successfully",
        "memory": updated_memory
    })

@app.route('/think-tank')
def think_tank():
    """Placeholder route for think tank page."""
    return jsonify({"status": "success", "message": "Think Tank page not available in minimal server"})

@app.route('/api/think-tank', methods=['GET', 'POST'])
def api_think_tank():
    """API endpoint for Think Tank data with enhanced model information.
    
    This endpoint processes messages using a simulated Think Tank mode that includes
    enhanced model information with rankings, blending data, and model contributions.
    
    For POST requests, expects JSON with:
    - message: The user message
    - conversation_id: Optional conversation ID
    
    Returns:
        JSON with the AI response and enhanced model_info
    """
    if request.method == 'POST':
        try:
            data = request.json
            message = data.get('message', '')
            conversation_id = data.get('conversation_id')
            
            if not message:
                return jsonify({
                    "status": "error",
                    "message": "No message provided"
                }), 400
                
            # Get message history if provided
            message_history = data.get('message_history', [])
            use_memory = data.get('use_memory', True)
            
            # Check if we have access to the real Think Tank
            if has_think_tank:
                print("[THINK TANK] Using real Think Tank for response generation")
                # Get query tags from message for routing
                query_tags = get_query_tags(message)
                
                # Process with the real Think Tank using all its capabilities
                start_time = time.time()
                think_tank_result = process_with_think_tank(
                    message=message,
                    model_priority=['gpt-4o', 'claude-3-opus', 'gpt-4', 'gemini-pro'],
                    query_tags=query_tags,
                    conversation_id=conversation_id
                )
                
                # Extract the model responses
                model_responses = think_tank_result.get('responses', {})
                
                # Rank the responses for quality
                ranked_responses = rank_responses(model_responses, message)
                
                # Blend for the final response
                blended_result = blend_responses(model_responses, ranked_responses, query_tags)
                response = blended_result.get('blended_response', '')
                
                # Create model info for frontend
                model_info = {
                    'primary_model': 'think_tank',
                    'response_time': time.time() - start_time,
                    'model_count': len(model_responses),
                    'models_used': list(model_responses.keys()),
                    'blending_info': blended_result.get('blend_weights', {}),
                    'query_tags': query_tags
                }
                print(f"[THINK TANK] Successfully generated response with {len(model_responses)} models")
            else:
                # Fall back to simulation if Think Tank components aren't available
                print("[SIMULATION] Using simulated Think Tank (real components not available)")
                message_type = analyze_message_type(message)
                model = select_model_for_query(message, message_type)
                response = generate_simulated_response(message, message_type, model)
                model_info = generate_model_info(message_type, model)
                print("[SIMULATION] Generated simulated response")
            
            # Track simulated API usage
            if TRACK_API_USAGE:
                # Estimate tokens based on message and response length
                estimated_tokens = len(message.split()) + len(response.split())
                track_api_call(model, estimated_tokens, response_time)
            
            return jsonify({
                "response": response,
                "model_info": model_info,
                "using_real_think_tank": has_think_tank
            })
            
        except Exception as e:
            print(f"Error in Think Tank API: {e}")
            traceback.print_exc()
            return jsonify({
                "status": "error",
                "message": "Error processing request"
            }), 500
    
    # For GET requests, return placeholder data
    return jsonify({"status": "success", "data": {}})

@app.route('/chat')
def chat():
    """Render the chat interface."""
    # Ensure user has an ID and conversation
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    user_id = session['user_id']
    if user_id not in active_conversations:
        active_conversations[user_id] = f'test_conversation_{int(time.time())}'
    
    try:
        return render_template('chat.html', 
                               user_id=user_id,
                               conversation_id=active_conversations[user_id])
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return f"Chat interface unavailable: {str(e)}", 500

# API routes for chat functionality
@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """REST API endpoint for chat messages."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Log the incoming message for debugging
        logger.info(f"[CHAT_API] Received message: {data.get('message', '')}")
        logger.info(f"[CHAT_API] Think Tank enabled: {has_think_tank}")
        
        # Check if this is a memory confirmation response
        if data.get('memory_confirmation'):
            memory_data = data.get('memory_confirmation')
            confirmed = memory_data.get('confirmed', False)
            fact = memory_data.get('fact')
            category = memory_data.get('category', 'general')
            
            if confirmed and fact:
                # User confirmed the memory, add it
                memory_id = str(uuid.uuid4())
                memory = {
                    'id': memory_id,
                    'content': fact,
                    'category': category,
                    'source': 'conversation_confirmed',
                    'confidence': 1.0,  # User confirmation gives 100% confidence
                    'created_at': time.time(),
                    'last_accessed': time.time(),
                    'access_count': 1
                }
                add_memory(memory)
                
                response_data = {
                    'status': 'success',
                    'message': f"I've remembered that you {fact}.",
                    'memory_added': True,
                    'conversation_id': data.get('conversation_id')
                }
                return jsonify(response_data)
            else:
                # User declined to save the memory
                response_data = {
                    'status': 'success',
                    'message': "I won't remember that.",
                    'memory_added': False,
                    'conversation_id': data.get('conversation_id')
                }
                return jsonify(response_data)
        
        user_message = data.get('message', '')
        conversation_id = data.get('conversation_id', f'rest-api-{int(datetime.now().timestamp())}')
        user_id = data.get('user_id', 'anonymous')
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
        
        # Initialize conversation history if this is a new conversation
        if conversation_id not in conversation_history:
            conversation_history[conversation_id] = []
        
        # Log the incoming message
        logger.info(f"[CHAT_API] Processing message from user {user_id}: {user_message}")
        
        # Check if OpenAI API key is available
        if not openai_api_key:
            # Fallback to simulated response if no API key
            logger.warning("[CHAT_API] No OpenAI API key available. Using fallback response.")
            return jsonify({
                'status': 'error',
                'message': 'No OpenAI API key configured. Please add your API key to the .env file.',
                'conversation_id': conversation_id
            }), 500
        
        # Check for special commands before processing
        is_command, command_response = process_special_commands(user_message, conversation_id, user_id)
        if is_command:
            return jsonify({
                'status': 'success',
                'response': command_response,
                'is_command': True,
                'conversation_id': conversation_id
            })
            
        # Add user message to conversation history
        conversation_history[conversation_id].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Extract potential facts worth remembering from user message
        extracted_facts = extract_facts_from_message(user_message)
        automatically_stored_facts = []
        confirm_facts = []
        
        if extracted_facts:
            logger.info(f"[MEMORY] Extracted {len(extracted_facts)} potential facts from message")
            
            # Process extracted facts
            for fact in extracted_facts:
                # Check for similar existing memories to avoid duplication
                similar_memories = get_relevant_memories(fact['content'], max_results=1)
                is_duplicate = False
                
                if similar_memories and similar_memories[0].get('relevance', 0) > 0.85:
                    # Very similar memory exists, update access count but don't store duplicate
                    memory_id = similar_memories[0]['id']
                    update_memory(memory_id, {
                        'last_accessed': time.time(),
                        'access_count': similar_memories[0].get('access_count', 0) + 1
                    })
                    is_duplicate = True
                    logger.info(f"[MEMORY] Fact '{fact['content']}' is similar to existing memory, updated access count")
                
                if not is_duplicate:
                    # Decide whether to store automatically or ask for confirmation
                    if fact['confidence'] > 0.85:
                        # High confidence facts are stored automatically
                        # Use the existing save_memory function
                        memory_id = save_memory(
                            content=fact['content'],
                            source='conversation_auto',
                            tags=['auto_extracted', fact['category']],
                            category=fact['category'],
                            importance=8  # High importance for auto-extracted facts
                        )
                        automatically_stored_facts.append(fact['content'])
                        logger.info(f"[MEMORY] Automatically stored high-confidence fact: {fact['content']}")
                    elif fact['confidence'] > 0.75:
                        # Medium confidence facts need confirmation
                        confirm_facts.append(fact)
                        logger.info(f"[MEMORY] Queued fact for confirmation: {fact['content']}")
        
        # Limit conversation history to MAX_CONVERSATION_HISTORY messages
        if len(conversation_history[conversation_id]) > MAX_CONVERSATION_HISTORY:
            conversation_history[conversation_id] = conversation_history[conversation_id][-MAX_CONVERSATION_HISTORY:]
        
        # Call the real AI response function that uses OpenAI API with conversation history
        response_data = get_ai_response(
            user_message, 
            conversation_id, 
            user_id, 
            conversation_history[conversation_id]
        )
        
        # Add memory confirmation if needed
        if confirm_facts:
            # Choose the highest confidence fact to confirm
            fact_to_confirm = max(confirm_facts, key=lambda x: x['confidence'])
            confirm_message = f"\n\nI noticed you mentioned that you {fact_to_confirm['content']}. Would you like me to remember this?"
            response_data["response"] += confirm_message
            response_data["memory_confirmation"] = {
                "fact": fact_to_confirm['content'],
                "category": fact_to_confirm['category'],
                "confidence": fact_to_confirm['confidence']
            }
            
        # Add memory info for UI feedback if memories were automatically stored
        if automatically_stored_facts:
            response_data["automatic_memories"] = automatically_stored_facts
        
        # Add the assistant's response to conversation history
        conversation_history[conversation_id].append({
            "role": "assistant",
            "content": response_data["response"],
            "timestamp": datetime.now().isoformat(),
            "message_id": response_data["message_id"]
        })
        
        # Add conversation_id to the response for client tracking
        response_data['conversation_id'] = conversation_id
        response_data['status'] = 'success'
        
        # Log successful response
        logger.info(f"[CHAT_API] Successfully processed message. Response length: {len(response_data['response'])}")
        logger.info(f"[MEMORY] Conversation {conversation_id} now has {len(conversation_history[conversation_id])} messages")
        
        # Return the processed response
        return jsonify(response_data)
            
    except Exception as e:
        logger.error(f"Error in chat_message endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': f"Server error: {str(e)}"
        }), 500

@app.route('/api/model_info/<message_id>', methods=['GET'])
def get_model_info(message_id):
    """Get information about the model used for a specific message."""
    # Return simulated model info
    return jsonify({
        'status': 'success',
        'message_id': message_id,
        'model_info': {
            'primary_model': 'gpt-4',
            'rankings': [
                {
                    'model': 'gpt-4', 
                    'score': 0.95,
                    'reasoning': 'Provided the most comprehensive and accurate response.'
                },
                {
                    'model': 'claude-3', 
                    'score': 0.92,
                    'reasoning': 'Good response but missing some nuance.'
                },
                {
                    'model': 'gemini-pro', 
                    'score': 0.88,
                    'reasoning': 'Solid response but less detailed.'
                }
            ],
            'blending': {
                'strategy': 'technical',
                'contributions': {
                    'gpt-4': 60,
                    'claude-3': 30,
                    'gemini-pro': 10
                }
            }
        }
    })

@app.route('/api/feedback', methods=['POST'])
def handle_feedback():
    """API endpoint to handle user feedback on responses."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        message_id = data.get('message_id')
        feedback_type = data.get('feedback_type')
        
        logger.info(f"Received {feedback_type} feedback for message {message_id}")
        
        # Return success
        return jsonify({'status': 'success', 'message': 'Feedback recorded'})
        
    except Exception as e:
        logger.error(f"Error handling feedback: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/memory/confirm', methods=['POST'])
def handle_memory_confirmation():
    """Handle user confirmation of a memory that Minerva proposed to remember.
    
    This endpoint processes the user's response to a memory confirmation request.
    If the user confirms, the memory is added to Minerva's memory system.
    If the user rejects, the memory is discarded.
    
    Returns:
        JSON: Status message indicating success or failure
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        confirmation_id = data.get('confirmation_id')
        confirmed = data.get('confirmed', False)  # Boolean indicating user's choice
        memory_content = data.get('content')
        category = data.get('category', 'fact')
        modified_content = data.get('modified_content')  # If user edited the memory
        
        # Log the confirmation request
        action = "confirmed" if confirmed else "rejected"
        logger.info(f"Memory confirmation {action} for ID {confirmation_id}: {memory_content}")
        
        # If user confirmed, save the memory
        if confirmed:
            # Use modified content if provided, otherwise use original
            final_content = modified_content if modified_content else memory_content
            
            # Create memory object
            memory_id = str(uuid.uuid4())
            memory = {
                'id': memory_id,
                'content': final_content,
                'category': category,
                'source': 'user_confirmed',
                'confidence': 1.0,  # User confirmed, so 100% confidence
                'created_at': time.time(),
                'last_accessed': time.time(),
                'access_count': 1,
                'tags': ['user_confirmed', category]
            }
            
            # Add to memory system
            add_memory(memory)
            
            return jsonify({
                "status": "success",
                "message": "Memory saved successfully",
                "memory_id": memory_id
            })
        
        # If rejected, just return success status
        return jsonify({
            "status": "success",
            "message": "Memory confirmation rejected"
        })
        
    except Exception as e:
        logger.error(f"Error handling memory confirmation: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Memory system implementation
# Store memories in a simple JSON file
import json
import os

# File path for memory storage
memory_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'memories.json')

# Create data directory if it doesn't exist
os.makedirs(os.path.dirname(memory_file), exist_ok=True)

# Initialize memory storage
def initialize_memory_storage():
    """Initialize the memory storage system."""
    if not os.path.exists(memory_file):
        with open(memory_file, 'w') as f:
            json.dump([], f)
        logger.info(f"[MEMORY] Created new memory storage file: {memory_file}")
    else:
        logger.info(f"[MEMORY] Using existing memory storage file: {memory_file}")

# Save a memory to storage
def save_memory(content, source='user', tags=None, category=None, importance=5):
    """Save a new memory to the storage system.
    
    Args:
        content (str): The memory content
        source (str): Source of the memory (user, ai, etc)
        tags (list): List of tags for categorization
        category (str): Category for the memory (preference, fact, instruction)
        importance (int): Importance rating from 1-10
    
    Returns:
        str: The ID of the saved memory
    """
    if tags is None:
        tags = []
    
    # Determine category from tags if not specified
    if category is None:
        if 'preference' in tags:
            category = 'preference'
        elif 'user_info' in tags:
            category = 'fact'
        elif 'instruction' in tags:
            category = 'instruction'
        else:
            category = 'general'
    
    # Load existing memories
    memories = []
    try:
        with open(memory_file, 'r') as f:
            memories = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is empty or invalid, start with empty list
        memories = []
    
    # Generate a unique ID for the memory
    memory_id = str(uuid.uuid4())
    
    # Create memory object with fields expected by the template
    memory = {
        'id': memory_id,
        'content': content,
        'source': source,
        'category': category,
        'importance': importance,
        'tags': tags,
        'created_at': datetime.now().isoformat(),
        'accessed_count': 0,
        'last_accessed': None
    }
    
    # Add memory to storage
    memories.append(memory)
    
    # Save updated memories
    with open(memory_file, 'w') as f:
        json.dump(memories, f, indent=2)
    
    logger.info(f"[MEMORY] Saved new memory: {memory_id[:8]}...")
    return memory_id

# Get all memories
def get_all_memories():
    """Get all stored memories."""
    try:
        with open(memory_file, 'r') as f:
            memories = json.load(f)
        return memories
    except (json.JSONDecodeError, FileNotFoundError):
        return []

# Import required libraries for semantic search
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    logger.warning("Sentence Transformers not available. Falling back to keyword matching.")
    SEMANTIC_SEARCH_AVAILABLE = False

# Embedding model - lazy loaded when needed
embedding_model = None

# Memory embedding cache to avoid recomputing embeddings
memory_embedding_cache = {}

def get_embedding_model():
    """Get or initialize the sentence embedding model."""
    global embedding_model
    if embedding_model is None and SEMANTIC_SEARCH_AVAILABLE:
        try:
            # Use a smaller model for efficiency
            logger.info("Loading sentence embedding model...")
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            return None
    return embedding_model

# Process special commands like memory management
def process_special_commands(message, conversation_id, user_id):
    """Process special commands that modify Minerva's behavior or access special functions.
    
    Returns a tuple of (is_command, response_message) where is_command is boolean,
    and response_message is the response if command was detected, None otherwise.
    """
    lower_message = message.lower().strip()
    
    # Command pattern matching
    if lower_message.startswith('/help') or lower_message == 'help':
        return True, """
Available commands:
- /help - Show this help message
- /clear - Clear the current conversation history
- /status - Show system status
- /remember [fact] - Save something to my memory
- /forget [fact or ID] - Remove something from my memory
- /memories - Show what I remember about you
        """
    
    elif lower_message.startswith('/clear'):
        # Clear conversation history if it exists
        if conversation_id in conversation_history:
            conversation_history[conversation_id] = []
        return True, "Conversation history cleared. How can I help you now?"
    
    elif lower_message.startswith('/status'):
        # Display system status
        memory_count = len(get_all_memories())
        
        status_message = f"""
System Status:
- Server: Running
- Memory Items: {memory_count}
- API Status: {'Available' if openai_api_key else 'Not Configured'}
        """
        return True, status_message
    
    elif lower_message.startswith('/remember'):
        # Extract the fact to remember
        fact = message[len('/remember'):].strip()
        if not fact:
            return True, "Please specify what you'd like me to remember. For example: /remember I like chocolate."
        
        # Create new memory
        memory_id = str(uuid.uuid4())
        memory = {
            'id': memory_id,
            'content': fact,
            'category': 'instruction' if 'when' in fact or 'always' in fact or 'never' in fact else 'fact',
            'source': 'explicit',
            'confidence': 1.0,  # Explicit memories have 100% confidence
            'created_at': time.time(),
            'last_accessed': time.time(),
            'access_count': 1
        }
        
        # Check for similar existing memories
        similar_memories = get_relevant_memories(fact, max_results=1)
        if similar_memories and similar_memories[0].get('relevance', 0) > 0.9:
            # Update existing memory instead
            update_memory(similar_memories[0]['id'], {
                'content': fact,  # Use the newer formulation
                'last_accessed': time.time(),
                'access_count': similar_memories[0].get('access_count', 0) + 1,
                'confidence': 1.0  # Explicit confirmation increases confidence
            })
            return True, f"I've updated my memory about this. I'll remember that {fact}."
        
        # Add the new memory
        add_memory(memory)
        return True, f"I'll remember that {fact}."
    
    elif lower_message.startswith('/forget'):
        # Extract the fact to forget
        fact_or_id = message[len('/forget'):].strip()
        if not fact_or_id:
            return True, "Please specify what you'd like me to forget, either by providing the exact fact or its ID."
        
        # Check if it's a memory ID first
        memory = get_memory_by_id(fact_or_id)
        if memory:
            delete_memory(fact_or_id)
            return True, f"I've forgotten that {memory['content']}."
        
        # Otherwise, search for similar memories
        similar_memories = get_relevant_memories(fact_or_id, max_results=5)
        if not similar_memories:
            return True, "I couldn't find any memories matching what you want me to forget."
        
        # Delete the most relevant memory
        memory_to_delete = similar_memories[0]
        delete_memory(memory_to_delete['id'])
        return True, f"I've forgotten that {memory_to_delete['content']}."
    
    elif lower_message.startswith('/memories'):
        # Show all memories relevant to the user
        memories = get_all_memories()
        if not memories:
            return True, "I don't have any memories stored yet."
        
        # Group memories by category for better organization
        memories_by_category = {}
        for memory in memories:
            category = memory.get('category', 'general')
            if category not in memories_by_category:
                memories_by_category[category] = []
            memories_by_category[category].append(memory)
        
        # Format memories by category
        response = "Here's what I remember:\n\n"
        for category, category_memories in memories_by_category.items():
            response += f"**{category.capitalize()}**:\n"
            for memory in category_memories:
                response += f"- {memory['content']}\n"
            response += "\n"
        
        return True, response
    
    # Special command to answer memory-related questions
    elif any(q in lower_message for q in ["what do you remember", "what have i told you", "what do you know about me"]):
        # Find memories relevant to this question
        relevant_memories = get_relevant_memories(message, max_results=10)
        
        if not relevant_memories:
            return True, "I don't have any specific memories relevant to that question yet."
        
        # Group memories by category
        memories_by_category = {}
        for memory in relevant_memories:
            category = memory.get('category', 'general')
            if category not in memories_by_category:
                memories_by_category[category] = []
            memories_by_category[category].append(memory)
        
        # Format grouped memories
        response = "Based on our conversations, here's what I remember:\n\n"
        for category, memories in memories_by_category.items():
            if category == 'preference':
                response += "**Your Preferences**:\n"
            elif category == 'personal':
                response += "**About You**:\n"
            elif category == 'experience':
                response += "**Your Experiences**:\n"
            else:
                response += f"**{category.capitalize()}**:\n"
                
            for memory in memories:
                response += f"- {memory['content']}\n"
            response += "\n"
        
        return True, response
    
    # Check for explicit remember/forget instructions without command prefix
    elif lower_message.startswith("remember that") or lower_message.startswith("please remember"):
        # Extract the fact to remember
        fact = re.sub(r'^(?:remember that|please remember|remember)', '', message, flags=re.IGNORECASE).strip()
        if not fact:
            return False, None  # Not a valid remember instruction
            
        # Create new memory
        memory_id = str(uuid.uuid4())
        memory = {
            'id': memory_id,
            'content': fact,
            'category': 'instruction' if 'when' in fact or 'always' in fact or 'never' in fact else 'fact',
            'source': 'explicit',
            'confidence': 1.0,
            'created_at': time.time(),
            'last_accessed': time.time(),
            'access_count': 1
        }
        
        # Add the new memory
        add_memory(memory)
        return True, f"I'll remember that {fact}."
    
    elif lower_message.startswith("forget that") or lower_message.startswith("please forget"):
        # Extract the fact to forget
        fact = re.sub(r'^(?:forget that|please forget|forget)', '', message, flags=re.IGNORECASE).strip()
        if not fact:
            return False, None  # Not a valid forget instruction
        
        # Search for similar memories
        similar_memories = get_relevant_memories(fact, max_results=3)
        if not similar_memories:
            return True, "I don't have any memories about that to forget."
        
        # Delete the most relevant memory
        memory_to_delete = similar_memories[0]
        delete_memory(memory_to_delete['id'])
        return True, f"I've forgotten that {memory_to_delete['content']}."
        
    # No command detected
    return False, None

# Automatic fact extraction and learning from conversations
def handle_memory_command(message):
    """Handle explicit and natural language memory commands.
    
    This function identifies and processes memory commands from users in various formats:
    - Explicit commands: '/remember', '/r', '/forget', '/f', '/memories'
    - Natural language: 'remember that...', 'forget about...', 'Minerva remember...'
    
    Args:
        message (str): The user's message
        
    Returns:
        tuple: (processed_message, command_response, command_detected)
            - processed_message: Message with command removed or empty if fully processed
            - command_response: Response to the command, or None if no command
            - command_detected: Boolean indicating if a memory command was found
    """
    # Initialize return values
    processed_message = message
    command_response = None
    command_detected = False
    
    # Normalize message for easier processing
    message_lower = message.lower()
    
    # Define regex patterns for command detection
    remember_patterns = [
        r'^/remember\s+(.+)',             # /remember command
        r'^/r\s+(.+)',                   # /r shorthand
        r'^remember\s+that\s+(.+)',      # remember that...
        r'^minerva[,]?\s+remember\s+(.+)'  # Minerva remember...
    ]
    
    forget_patterns = [
        r'^/forget\s+(.+)',              # /forget command
        r'^/f\s+(.+)',                   # /f shorthand
        r'^forget\s+(?:about|that)\s+(.+)',  # forget about/that...
        r'^minerva[,]?\s+forget\s+(.+)'     # Minerva forget...
    ]
    
    # Check for remember commands
    memory_content = None
    for pattern in remember_patterns:
        match = re.match(pattern, message_lower)
        if match:
            command_detected = True
            memory_content = match.group(1).strip()
            break
            
    if command_detected and memory_content:
        # Check if this memory or very similar one already exists
        similar_memories = get_relevant_memories(memory_content, max_results=1)
        if similar_memories and similar_memories[0].get('relevance', 0) > 0.92:
            # Very similar memory exists - inform the user
            existing_memory = similar_memories[0]
            command_response = f"I already remember something similar: '{existing_memory.get('content')}'"
        else:
            # Attempt to categorize the memory
            category = 'fact'  # Default category
            
            # Basic categorization based on content
            if any(word in memory_content.lower() for word in ['like', 'love', 'enjoy', 'prefer', 'favorite', 'hate', 'dislike']):
                category = 'preference'
            elif any(word in memory_content.lower() for word in ['visited', 'went', 'traveled', 'saw', 'experienced']):
                category = 'experience'
            elif any(word in memory_content.lower() for word in ['plan', 'going to', 'will', 'want to', 'intend']):
                category = 'plan'
            
            # Generate a memory ID
            memory_id = str(uuid.uuid4())
            
            # Create and store the memory
            memory = {
                'id': memory_id,
                'content': memory_content,
                'category': category,
                'source': 'user_explicit',
                'confidence': 1.0,  # User explicitly asked to remember, so 100% confidence
                'created_at': time.time(),
                'last_accessed': time.time(),
                'access_count': 1,
                'tags': ['user_explicit', 'command', category]
            }
            
            # Add to memory system
            add_memory(memory)
            
            # Provide confirmation response
            command_response = f"I'll remember that: {memory_content}"
            
        # Remove command from message for further processing
        processed_message = ""
        return processed_message, command_response, command_detected
    
    # Reset command detected flag since we're now checking for forget commands
    command_detected = False
    
    # Check for forget commands
    forget_content = None
    for pattern in forget_patterns:
        match = re.match(pattern, message_lower)
        if match:
            command_detected = True
            forget_content = match.group(1).strip()
            break
    
    if command_detected and forget_content:
        # Search for memories matching the query
        memories = get_all_memories()
        matching_memories = []
        
        # Find memories that match the query using semantic search if available
        if SEMANTIC_SEARCH_AVAILABLE:
            matching_memories = get_relevant_memories(forget_content, max_results=3)
            matching_memories = [m for m in matching_memories if m.get('relevance', 0) > 0.7]
        else:
            # Fallback to text matching
            query_lower = forget_content.lower()
            for memory in memories:
                if query_lower in memory.get('content', '').lower():
                    matching_memories.append(memory)
        
        if matching_memories:
            # If multiple memories match, show them to the user
            if len(matching_memories) > 1:
                memory_list = "\n".join([f"• {i+1}: {memory.get('content')}" 
                                    for i, memory in enumerate(matching_memories)])
                command_response = f"I found multiple memories that match. Which one would you like me to forget?\n{memory_list}\n\nPlease specify by saying 'forget memory 1' or similar."
                processed_message = ""
                return processed_message, command_response, command_detected
            
            # Single memory match - delete it
            memory_to_forget = matching_memories[0]
            memory_id = memory_to_forget.get('id')
            
            # Use the proper delete function
            success = delete_memory_by_id(memory_id)
            
            if success:
                command_response = f"I've forgotten: {memory_to_forget.get('content')}"
            else:
                command_response = "I had trouble forgetting that memory. Please try again."
        else:
            command_response = f"I couldn't find any memories matching '{forget_content}'."
        
        # Remove command from message for further processing
        processed_message = ""
        return processed_message, command_response, command_detected
    
    # Check for /memories command (list memories)
    if message_lower.strip() in ['/memories', 'show memories', 'what do you remember', 'list memories']:
        command_detected = True
        
        # Check for category filters in the message
        category_filter = None
        for category in ['preferences', 'facts', 'experiences', 'plans']:
            if category in message_lower:
                category_filter = category[:-1]  # Remove 's' to get singular form
                break
        
        # Get all memories
        memories = get_all_memories()
        
        # Apply category filter if specified
        if category_filter:
            memories = [m for m in memories if m.get('category') == category_filter]
            filter_text = f" ({category_filter}s)"
        else:
            filter_text = ""
        
        if memories:
            # Sort by recency
            sorted_memories = sorted(memories, key=lambda x: x.get('created_at', 0), reverse=True)
            
            # Format memories for display, limit to most recent
            memory_list = "\n".join([f"• {memory.get('content')}" for memory in sorted_memories[:10]])
            command_response = f"Here are some things I remember about you{filter_text}:\n{memory_list}"
            
            if len(memories) > 10:
                command_response += f"\n\nPlus {len(memories) - 10} more memories. Use more specific filters to see others."
        else:
            if category_filter:
                command_response = f"I don't have any {category_filter} memories stored yet."
            else:
                command_response = "I don't have any memories stored yet."
        
        # Remove command from message for further processing
        processed_message = ""
        return processed_message, command_response, command_detected
    
    # If we reach here, no memory command was detected
    return processed_message, command_response, command_detected

def extract_facts_from_message(message, confidence_threshold=0.7):
    """Extract potential facts from a user message that might be worth remembering.
    
    This function analyzes user messages to identify personal information, preferences,
    experiences, plans, and other meaningful facts that are worth remembering for future
    personalized interactions.
    
    Args:
        message (str): The user message to extract facts from
        confidence_threshold (float): Minimum confidence score to consider a fact worth remembering
        
    Returns:
        list: List of dictionaries containing extracted facts with their category and confidence
    """
    # Skip extraction for very short messages or questions
    if len(message.split()) < 5 or message.strip().endswith('?'):
        return []
        
    # Patterns for personal facts detection with comprehensive categories
    fact_patterns = {
        'preference': [
            # Likes and preferences
            r"(?:I|my|we)\s+(?:like|love|enjoy|prefer|favorite|am fond of)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Dislikes
            r"(?:I|my|we)\s+(?:hate|dislike|don't like|do not like|can't stand|am not a fan of)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Preferences with more context
            r"(?:I|my|we)\s+would rather\s+(.+?)\s+than\s+(.+?)(?:\.|,|$)",
            r"(?:I|my|we)\s+prefer\s+(.+?)\s+over\s+(.+?)(?:\.|,|$)"
        ],
        'personal': [
            # Background information
            r"(?:I|my|we)\s+(?:am|are|was|were)\s+(?:from|in|at|born in)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Possessions
            r"(?:I|my|we)\s+(?:have|own|possess)\s+(?:a|an|the)?\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Names
            r"(?:my|our)\s+name\s+(?:is|was)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Occupation/study
            r"(?:I|we)\s+(?:work|study|teach|learn|am|are)\s+(?:at|in|for|as)\s+(?:a|an|the)?\s*(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Age and characteristics
            r"(?:I|we)\s+am\s+([0-9]+)\s+years\s+old(?:\.|,|$|\s+and\s+|\s+but\s+)",
            r"(?:I|we)\s+(?:am|are)\s+(?:a|an)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)"
        ],
        'experience': [
            # Travel/visits
            r"(?:I|we)\s+(?:visited|went to|traveled to|saw|have been to)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Creations
            r"(?:I|we)\s+(?:wrote|created|made|built|developed|designed)\s+(?:a|an|the)?\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Activities
            r"(?:I|we)\s+(?:played|participated in|joined|attended)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Learning/skills
            r"(?:I|we)\s+(?:learned|studied|mastered|practiced)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Life events
            r"(?:I|we)\s+(?:got married|had a child|graduated|moved)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)"
        ],
        'plan': [
            # Future intentions
            r"(?:I|we)\s+(?:plan to|will|going to|want to|intend to|would like to|hope to)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Scheduled events
            r"(?:I|we)\s+(?:have|am|are)\s+(?:scheduled|planning|going to)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Goals
            r"(?:my|our)\s+(?:goal|aim|objective|target)\s+is\s+(?:to|for)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)"
        ],
        'relationship': [
            # Family
            r"(?:my|our)\s+(?:spouse|partner|wife|husband|child|son|daughter|mom|dad|mother|father|parent|sibling|brother|sister)\s+(?:is|was|are|has|have|likes|enjoys)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Friends/coworkers
            r"(?:my|our)\s+(?:friend|colleague|coworker|roommate|neighbor)\s+(?:is|was|are|has|have|likes|enjoys)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)"
        ],
        'health': [
            # Conditions
            r"(?:I|we)\s+(?:have|suffer from|was diagnosed with|am allergic to)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)",
            # Diet
            r"(?:I|we)\s+(?:am|are)\s+(?:vegetarian|vegan|gluten-free|dairy-free|on a|following a)\s+(.+?)(?:\.|,|$|\s+and\s+|\s+but\s+)"
        ]
    }
    
    extracted_facts = []
    
    # Process each category and its patterns
    for category, patterns in fact_patterns.items():
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                # Handle if match is a tuple (for patterns with multiple capture groups)
                if isinstance(match, tuple):
                    fact_parts = [part.strip() for part in match if part.strip()]
                    fact_content = ' over '.join(fact_parts) if len(fact_parts) > 1 else (fact_parts[0] if fact_parts else '')
                else:
                    fact_content = match.strip()
                    
                if fact_content and len(fact_content) > 3:  # Minimum length for meaningful facts
                    # Assign confidence based on pattern clarity and category
                    if category == 'preference':
                        if any(keyword in pattern.lower() for keyword in ['like', 'love', 'enjoy', 'prefer', 'favorite']):
                            memory_content = f"like {fact_content}"
                            confidence = 0.9  # High confidence for clear preferences
                        elif any(keyword in pattern.lower() for keyword in ['would rather', 'prefer over']):
                            memory_content = f"prefer {fact_content}"
                            confidence = 0.92  # Very high for comparative preferences
                        else:
                            memory_content = f"dislike {fact_content}"
                            confidence = 0.88  # Still high for clear dislikes
                            
                    elif category == 'personal':
                        if 'name' in pattern.lower():
                            memory_content = f"named {fact_content}"
                            confidence = 0.95  # Very high confidence for names
                        elif 'years old' in pattern.lower():
                            memory_content = f"{fact_content} years old"
                            confidence = 0.93  # Very high for age
                        elif any(keyword in pattern.lower() for keyword in ['from', 'born in']):
                            memory_content = f"from {fact_content}"
                            confidence = 0.9
                        elif 'work' in pattern.lower() or 'as a' in pattern.lower():
                            memory_content = f"work as {fact_content}"
                            confidence = 0.9
                        else:
                            memory_content = f"{fact_content}"
                            confidence = 0.85
                            
                    elif category == 'experience':
                        if any(keyword in pattern.lower() for keyword in ['wrote', 'created', 'made', 'built', 'developed', 'designed']):
                            memory_content = f"created {fact_content}"
                            confidence = 0.85
                        elif any(keyword in pattern.lower() for keyword in ['visited', 'went to', 'traveled']):
                            memory_content = f"visited {fact_content}"
                            confidence = 0.88
                        elif any(keyword in pattern.lower() for keyword in ['married', 'child', 'graduated']):
                            memory_content = f"experienced {fact_content}"
                            confidence = 0.9  # Higher for important life events
                        else:
                            memory_content = f"experienced {fact_content}"
                            confidence = 0.8
                            
                    elif category == 'plan':
                        memory_content = f"plan to {fact_content}"
                        confidence = 0.75  # Lower confidence for future plans
                        
                    elif category == 'relationship':
                        if any(family_term in pattern.lower() for family_term in ['spouse', 'partner', 'wife', 'husband', 'child', 'son', 'daughter']):
                            memory_content = f"has family member who {fact_content}"
                            confidence = 0.85
                        else:
                            memory_content = f"knows someone who {fact_content}"
                            confidence = 0.75
                    
                    elif category == 'health':
                        if 'allergic' in pattern.lower():
                            memory_content = f"allergic to {fact_content}"
                            confidence = 0.95  # Very high for allergies (safety)
                        else:
                            memory_content = f"health note: {fact_content}"
                            confidence = 0.85
                    
                    else:
                        memory_content = fact_content
                        confidence = 0.7
                    
                    # Only include facts with confidence above the threshold
                    if confidence >= confidence_threshold:
                        extracted_facts.append({
                            'content': memory_content,
                            'category': category,
                            'source': 'conversation_auto',
                            'confidence': confidence,
                            'original_text': message,  # Store original message for context
                            'extracted_at': time.time()
                        })
    
    # Deduplicate similar facts - more sophisticated approach
    unique_facts = []
    content_set = set()
    
    # Sort by confidence so we keep higher confidence duplicates
    sorted_facts = sorted(extracted_facts, key=lambda x: x['confidence'], reverse=True)
    
    for fact in sorted_facts:
        # Create simplified version for deduplication
        simplified_content = re.sub(r'[^\w\s]', '', fact['content'].lower())
        words = simplified_content.split()
        
        # Create a more lenient deduplication key (just the key words)
        # This helps avoid nearly identical facts
        if len(words) > 3:
            # For longer content, use the most significant words
            # Remove common words and keep the most distinctive ones
            significant_words = [w for w in words if len(w) > 3 and w not in ['like', 'have', 'from', 'with', 'that', 'this', 'also']]
            dedup_key = ' '.join(sorted(significant_words)[:3])
        else:
            dedup_key = simplified_content
            
        if dedup_key and dedup_key not in content_set:
            content_set.add(dedup_key)
            unique_facts.append(fact)
    
    return unique_facts

# Format memories for natural integration in responses
def format_memories_for_response(memories, message, message_type='general'):
    """Format relevant memories for natural inclusion in responses.
    
    This function organizes retrieved memories into categories and creates natural language
    context phrases that can be incorporated into responses to make them more personalized.
    
    Args:
        memories (list): List of memory dictionaries
        message (str): The user's message
        message_type (str): Type of message for context
        
    Returns:
        dict: Memory information organized for response generation
    """
    # If no memories, return empty structure
    if not memories:
        return {
            'has_memories': False,
            'context': "",
            'preferences': [],
            'facts': [],
            'experiences': [],
            'instructions': [],
            'all_memories': []
        }
    
    # Update access statistics for retrieved memories
    update_memory_access(memories)
    
    # STEP 1: Group memories by category
    preferences = []
    facts = []
    experiences = []
    instructions = []
    general = []
    relationships = []
    health = []
    
    # Sort memories by relevance first
    sorted_memories = sorted(memories, key=lambda x: x.get('relevance', 0.5), reverse=True)
    
    # Categorize memories
    for memory in sorted_memories:
        # Skip very low-relevance memories
        if memory.get('relevance', 0) < 0.5:
            continue
            
        category = memory.get('category', 'general')
        content = memory.get('content', '')
        time_created = memory.get('created_at', 0)
        access_count = memory.get('access_count', 0)
        
        # Calculate a priority score that combines relevance, recency and frequency
        priority_score = (
            memory.get('relevance', 0.5) * 0.6 +  # Relevance is most important
            min(access_count / 10, 1.0) * 0.2 +    # Frequently accessed memories get a boost
            min(time_created / (time.time() + 1), 1.0) * 0.2  # Newer memories get a boost
        )
        
        memory_item = {
            'content': content, 
            'memory': memory,
            'priority': priority_score
        }
        
        # Categorize the memory
        if category == 'preference':
            preferences.append(memory_item)
        elif category in ['fact', 'personal']:
            facts.append(memory_item)
        elif category == 'experience':
            experiences.append(memory_item)
        elif category in ['instruction', 'plan']:
            instructions.append(memory_item)
        elif category == 'relationship':
            relationships.append(memory_item)
        elif category == 'health':
            health.append(memory_item)
        else:
            general.append(memory_item)
    
    # STEP 2: Analyze message keywords to find especially relevant memories
    message_words = set(re.findall(r'\b\w+\b', message.lower()))
    # Remove common stop words to focus on meaningful terms
    stop_words = {'the', 'and', 'this', 'that', 'what', 'how', 'when', 'where', 'why', 
                  'is', 'are', 'was', 'were', 'do', 'does', 'did', 'to', 'from', 'with',
                  'about', 'for', 'of', 'by', 'on', 'at', 'in'}
    message_words = message_words.difference(stop_words)
    
    # STEP 3: Create prioritized memory pool from all categories
    all_categorized_memories = [
        ('preference', preferences),
        ('fact', facts),
        ('experience', experiences),
        ('instruction', instructions),
        ('relationship', relationships),
        ('health', health),
        ('general', general)
    ]
    
    # STEP 4: Build memory references based on query type and relevance
    memory_references = []
    memory_context = ""
    
    # Match message words with memory content to boost scores
    keyword_boost = 0.3  # Boost amount for keyword matches
    
    # Apply keyword boosting
    for category_name, category_memories in all_categorized_memories:
        for item in category_memories:
            memory_text = item['content'].lower()
            keyword_matches = sum(1 for word in message_words if word in memory_text)
            if keyword_matches > 0:
                item['priority'] += keyword_boost * min(keyword_matches / len(message_words), 1.0)
    
    # Sort each category by the updated priority scores
    for category_name, category_memories in all_categorized_memories:
        category_memories.sort(key=lambda x: x['priority'], reverse=True)
    
    # STEP 5: Format memory references based on message type
    # For health-related queries, prioritize health memories
    if any(word in message.lower() for word in ['health', 'medical', 'allergy', 'allergic', 'diet']):
        if health:
            top_health = health[0]['content']
            memory_references.append(f"you've mentioned that you have {top_health}")
    
    # For personal questions, include more personal details
    elif message_type in ['personal', 'about_user', 'preferences']:
        # Add top preferences, facts, and experiences
        if preferences and len(preferences) > 0:
            pref = preferences[0]['content']
            memory_references.append(f"you've mentioned that you {pref}")
            # Include a second preference if available and relevant
            if len(preferences) > 1 and preferences[1]['priority'] > 0.7:
                memory_references.append(f"you also {preferences[1]['content']}")
                
        if facts and len(facts) > 0:
            fact = facts[0]['content']
            memory_references.append(f"you're {fact}")
            
        if experiences and len(experiences) > 0:
            exp = experiences[0]['content']
            memory_references.append(f"you've {exp}")
            
    # For technical queries, reference relevant technical memories
    elif message_type in ['technical', 'code', 'programming']:
        technical_memories = [m for m in memories if any(tag in m.get('tags', []) 
                            for tag in ['code', 'technical', 'programming'])]
        if technical_memories:
            tech_content = technical_memories[0].get('content', '')
            memory_references.append(f"we've discussed technical topics like {tech_content}")
    
    # For relationship queries, prioritize relationship memories
    elif any(word in message.lower() for word in ['family', 'friend', 'spouse', 'partner', 'child']):
        if relationships and len(relationships) > 0:
            rel = relationships[0]['content']
            memory_references.append(f"you've mentioned that you {rel}")
    
    # STEP 6: If we don't have specific context references yet, use the highest priority memories
    if not memory_references:
        # Collect high-priority memories from all categories
        top_memories = []
        for category_name, category_memories in all_categorized_memories:
            if category_memories and len(category_memories) > 0:
                top_memories.append((category_name, category_memories[0]))
        
        # Sort collected memories by priority
        top_memories.sort(key=lambda x: x[1]['priority'], reverse=True)
        
        # Use the top 2-3 memories across all categories
        for i, (category, memory_item) in enumerate(top_memories[:3]):
            content = memory_item['content']
            
            if category == 'preference':
                memory_references.append(f"you've told me you {content}")
            elif category in ['fact', 'personal']:
                memory_references.append(f"I recall that you {content}")
            elif category == 'experience':
                memory_references.append(f"you've previously {content}")
            elif category in ['instruction', 'plan']:
                memory_references.append(f"you've asked me to {content}")
            elif category == 'relationship':
                memory_references.append(f"you've mentioned your {content}")
            elif category == 'health':
                memory_references.append(f"you've told me about your {content}")
            else:
                memory_references.append(f"I remember you mentioned {content}")
            
            # Limit to 3 memories to avoid overwhelming responses
            if i >= 2:
                break
    
    # STEP 7: Format the final memory context string for natural inclusion in responses
    if memory_references:
        # Different formats based on number of memories
        if len(memory_references) == 1:
            memory_context = f"I remember that {memory_references[0]}. "
        elif len(memory_references) == 2:
            memory_context = f"From our previous conversations, I recall that {memory_references[0]} and {memory_references[1]}. "
        else:  # 3 or more memories
            # Format with commas and 'and' for the last item
            context_start = "Based on what you've shared with me before, I know that "
            context_parts = []
            
            for i, ref in enumerate(memory_references):
                if i < len(memory_references) - 1:
                    context_parts.append(ref)
                else:
                    context_parts.append(f"and {ref}")
            
            memory_context = context_start + ", ".join(context_parts) + ". "
    
    # STEP 8: Extract just the content strings for the return value
    preference_contents = [item['content'] for item in preferences[:3]]  # Limit to top 3
    fact_contents = [item['content'] for item in facts[:3]]
    experience_contents = [item['content'] for item in experiences[:3]]
    instruction_contents = [item['content'] for item in instructions[:3]]
    relationship_contents = [item['content'] for item in relationships[:3]]
    health_contents = [item['content'] for item in health[:3]]
    
    # Return enhanced structured memory information
    return {
        'has_memories': bool(memories),
        'context': memory_context,
        'preferences': preference_contents,
        'facts': fact_contents,
        'experiences': experience_contents,
        'instructions': instruction_contents,
        'relationships': relationship_contents,
        'health': health_contents,
        'all_memories': memories
    }

# Topic detection for conversation context
def extract_conversation_topic(message, message_history=None):
    """Extract the main topic from the current message and conversation history.
    
    Args:
        message (str): The current user message
        message_history (list): Previous messages in the conversation
        
    Returns:
        str: The detected conversation topic
    """
    # Topic keywords for different domains
    topic_keywords = {
        'personal': ['i', 'me', 'my', 'mine', 'myself', 'name', 'live', 'work', 'job', 'hobby', 'family', 'birthday'],
        'preferences': ['like', 'prefer', 'favorite', 'enjoy', 'hate', 'dislike', 'love', 'want', 'wish', 'rather'],
        'technical': ['code', 'programming', 'software', 'function', 'class', 'bug', 'error', 'fix', 'data', 'algorithm'],
        'location': ['city', 'country', 'place', 'address', 'location', 'region', 'area', 'where', 'near', 'around', 'live'],
        'educational': ['learn', 'study', 'school', 'university', 'college', 'degree', 'course', 'knowledge', 'skill', 'teach'],
        'entertainment': ['movie', 'game', 'book', 'music', 'song', 'film', 'show', 'series', 'play', 'sport', 'hobby'],
        'health': ['health', 'medical', 'doctor', 'symptom', 'disease', 'exercise', 'diet', 'medication', 'treatment', 'wellness'],
        'food': ['food', 'eat', 'cooking', 'recipe', 'meal', 'drink', 'restaurant', 'cuisine', 'dish', 'taste', 'flavor'],
        'travel': ['travel', 'trip', 'vacation', 'journey', 'flight', 'hotel', 'visit', 'destination', 'tourist', 'abroad'],
        'finance': ['money', 'finance', 'budget', 'cost', 'price', 'investment', 'income', 'expense', 'save', 'spend', 'bank']
    }
    
    # Clean the message by removing punctuation and converting to lowercase
    def clean_text(text):
        return re.sub(r'[^\w\s]', '', text.lower())
    
    # Get words from the current message
    words = clean_text(message).split()
    
    # Add words from recent message history (up to 5 messages)
    if message_history:
        # Get the last 5 messages
        recent_messages = message_history[-5:] if len(message_history) > 5 else message_history
        for msg in recent_messages:
            if msg.get('role') == 'user':
                words.extend(clean_text(msg.get('content', '')).split())
    
    # Count topic matches
    topic_scores = {topic: 0 for topic in topic_keywords}
    for word in words:
        for topic, keywords in topic_keywords.items():
            if word in keywords:
                topic_scores[topic] += 1
    
    # Get the topic with the highest score
    max_score = 0
    main_topic = 'general'
    for topic, score in topic_scores.items():
        if score > max_score:
            max_score = score
            main_topic = topic
    
    # Try to extract named entities for additional context
    # Look for capitalized words as a simple entity detection
    entities = re.findall(r'\b[A-Z][a-zA-Z]*\b', message)
    entity_context = ''
    if entities:
        entity_context = f" about {', '.join(entities)}"
    
    # If we have a topic with significant score, return it
    if max_score >= 2:
        return f"{main_topic} topic{entity_context}"
    elif max_score == 1:
        return f"possible {main_topic} topic{entity_context}"
    else:
        return f"general conversation{entity_context}"

def get_text_embedding(text):
    """Get embedding vector for a text string."""
    model = get_embedding_model()
    if model is None:
        return None
    
    try:
        # Generate embedding
        embedding = model.encode(text)
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None

# Get relevant memories for a given query
def get_relevant_memories(query, max_results=3, context=None, conversation_history=None):
    """Find memories relevant to the given query using enhanced semantic search or fallback to keyword matching.
    
    Enhanced with:
    - Intelligent query expansion
    - Better context integration
    - Temporal awareness (recency and frequency prioritization)
    - Improved relevance scoring
    
    Args:
        query (str): The user's query or message
        max_results (int): Maximum number of memories to return
        context (str, optional): Additional context like current topic
        conversation_history (list, optional): Recent conversation history
        
    Returns:
        list: Relevant memories sorted by relevance
    """
    memories = get_all_memories()
    if not memories:
        return []
    
    # Perform query expansion with key terms and variations
    expanded_query = expand_query(query)
    logger.info(f"[MEMORY] Original query: '{query}' expanded to include related terms")
    
    # Build a rich context from multiple sources
    search_text = expanded_query
    
    # Add the current conversation context if available
    if context:
        search_text = f"{context}. {search_text}"
    
    # Integrate conversation history with recency weighting
    if conversation_history and len(conversation_history) > 0:
        # Prioritize the most recent messages with diminishing weights
        weighted_history = []
        for i, msg in enumerate(conversation_history[-5:]):
            if msg.get('role') == 'user':
                # More recent messages get higher weight
                weight = 1.0 - (i * 0.15)  # Diminishing weight for older messages
                if weight > 0:
                    weighted_history.append(msg['content'])
        
        if weighted_history:
            # Join with weights applied (most recent messages first)
            search_text = f"{' '.join(weighted_history)} {search_text}"
    
    # Extract key entities and important terms for additional emphasis
    key_terms = extract_key_terms(query)
    if key_terms:
        search_text = f"{search_text} {' '.join(key_terms)}"
        logger.info(f"[MEMORY] Emphasized key terms: {key_terms}")
    
    # Try enhanced semantic search if available
    if SEMANTIC_SEARCH_AVAILABLE:
        try:
            relevant_memories = semantic_memory_search(search_text, memories, max_results*2, context)  # Get more candidates for post-processing
            
            # Log memory retrieval for debugging and analysis
            debug_log_memory_retrieval(query, expanded_query, relevant_memories, 'semantic_search')
            
            # Apply additional post-retrieval ranking
            processed_memories = post_process_memories(relevant_memories, query, max_results)
            
            # Log final selected memories after post-processing
            debug_log_memory_retrieval(query, expanded_query, processed_memories, 'final_selection', 
                                      original_count=len(relevant_memories))
            
            return processed_memories
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}, falling back to keyword matching")
    
    # Fallback to enhanced keyword matching
    return keyword_memory_search(search_text, memories, max_results)


def expand_query(query):
    """Expand the query with synonyms and related terms for better memory matching.
    
    Args:
        query (str): Original query string
        
    Returns:
        str: Expanded query with additional related terms
    """
    # Lowercase for consistent processing
    query_lower = query.lower()
    expanded_terms = []
    
    # 1. Add synonyms for common query terms
    term_expansions = {
        'like': ['enjoy', 'prefer', 'favorite'],
        'dislike': ['hate', 'don\'t like', 'avoid'],
        'want': ['need', 'desire', 'wish for'],
        'hobby': ['interest', 'pastime', 'activity'],
        'job': ['work', 'career', 'profession', 'occupation'],
        'family': ['relatives', 'parents', 'siblings', 'children'],
        'travel': ['trip', 'journey', 'vacation', 'visit'],
        'house': ['home', 'residence', 'apartment', 'living space'],
        'remember': ['recall', 'memorize', 'note'],
        'forget': ['delete', 'remove', 'don\'t remember'],
        'always': ['consistently', 'regularly', 'every time'],
        'never': ['not ever', 'don\'t ever']
    }
    
    # Add relevant synonyms based on what's in the query
    for term, expansions in term_expansions.items():
        if term in query_lower:
            expanded_terms.extend(expansions)
    
    # 2. Handle common query patterns with expansions
    if any(w in query_lower for w in ['what do i like', 'what are my preferences', 'what do i enjoy']):
        expanded_terms.extend(['preference', 'like', 'enjoy', 'favorite'])
    
    if any(w in query_lower for w in ['what did i do', 'what happened', 'when did i']):
        expanded_terms.extend(['experience', 'event', 'happened', 'occurred'])
        
    if any(w in query_lower for w in ['who is', 'who are', 'relationship']):
        expanded_terms.extend(['person', 'relationship', 'friend', 'family', 'colleague'])
    
    if any(w in query_lower for w in ['where', 'location', 'place']):
        expanded_terms.extend(['located', 'location', 'place', 'address'])
        
    # 3. Handle time-related queries with temporal terms
    if any(w in query_lower for w in ['recently', 'lately', 'last time', 'when']):
        expanded_terms.extend(['recent', 'latest', 'last time', 'previously'])
    
    # Combine original query with unique expansion terms
    if expanded_terms:
        return f"{query} {' '.join(set(expanded_terms))}"
    return query


def extract_key_terms(query):
    """Extract important terms from the query for additional emphasis.
    
    Args:
        query (str): The query to extract terms from
        
    Returns:
        list: List of important terms
    """
    important_terms = []
    
    # Extract potential names (capitalized words)
    names = re.findall(r'\b[A-Z][a-z]+\b', query)
    important_terms.extend(names)
    
    # Extract potential entities (locations, dates, etc.)
    # This is a simplified approach - in a full implementation, 
    # you would use a more sophisticated NER system
    entities = []
    
    # Common locations
    locations = re.findall(r'\b(?:in|at|to|from)\s+([A-Z][a-zA-Z\s]+)\b', query)
    entities.extend(locations)
    
    # Date patterns
    dates = re.findall(r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*\d{4})?\b', query)
    entities.extend(dates)
    
    # Numbers that might be important
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', query)
    entities.extend(numbers)
    
    important_terms.extend(entities)
    
    return list(set(important_terms))


def post_process_memories(memories, original_query, max_results):
    """Apply additional ranking and filtering to retrieved memories.
    
    Args:
        memories (list): List of retrieved memories with relevance scores
        original_query (str): The user's original query
        max_results (int): Maximum number of memories to return
        
    Returns:
        list: Re-ranked memories
    """
    if not memories:
        return []
    
    # 1. Apply additional boosting based on memory metadata
    for memory in memories:
        base_score = memory.get('relevance', 0.5)
        
        # Boost frequently accessed memories
        access_count = memory.get('access_count', 0)
        if access_count > 0:
            freq_boost = min(0.1 * math.log(1 + access_count), 0.2)  # Logarithmic scaling
            memory['relevance'] = min(0.99, base_score + freq_boost)
            
        # Boost very recent memories (created in the last 24 hours)
        created_at = memory.get('created_at', 0)
        time_diff = time.time() - created_at
        if time_diff < 86400:  # Last 24 hours
            recency_boost = 0.15
            memory['relevance'] = min(0.99, memory.get('relevance', 0.5) + recency_boost)
    
    # 2. Re-sort based on the updated scores
    sorted_memories = sorted(memories, key=lambda x: x.get('relevance', 0), reverse=True)
    
    # 3. Apply diversity filtering for top results
    # Ensure we don't return too many memories of the same category
    diverse_results = []
    category_counts = {}
    
    for memory in sorted_memories:
        category = memory.get('category', 'general')
        # Limit to 2 memories per category for diversity
        if category not in category_counts:
            category_counts[category] = 0
        
        if category_counts[category] < 2:
            diverse_results.append(memory)
            category_counts[category] += 1
            
            # Stop once we have enough diverse results
            if len(diverse_results) >= max_results:
                break
    
    # If we don't have enough diverse results, add more from the top scoring ones
    if len(diverse_results) < max_results:
        remaining_slots = max_results - len(diverse_results)
        already_included = set(m.get('id') for m in diverse_results)
        
        for memory in sorted_memories:
            if memory.get('id') not in already_included and remaining_slots > 0:
                diverse_results.append(memory)
                remaining_slots -= 1
                
            if remaining_slots <= 0:
                break
    
    # Update access statistics for final selected memories
    update_memory_access(diverse_results)
    
    # Log the diversity filtering process
    logger.debug(f"Memory diversity filtering: {len(sorted_memories)} candidates → {len(diverse_results)} selected memories")
    
    return diverse_results


def update_memory_access(memories):
    """Update memory access statistics for the provided memories.
    
    This function performs the following updates to the memory metadata:
    1. Increments the access_count for each memory
    2. Updates the last_accessed timestamp to the current time
    3. Calculates and updates access frequency patterns
    
    These statistics are used for temporal relevance scoring in future queries.
    
    Args:
        memories (list): List of memory objects to update
    """
    if not memories:
        return
    
    current_time = time.time()
    updated_memories = []
    
    for memory in memories:
        memory_id = memory.get('id')
        if not memory_id:
            continue
            
        # 1. Increment access count
        current_count = memory.get('access_count', 0)
        memory['access_count'] = current_count + 1
        
        # 2. Update last accessed timestamp
        memory['last_accessed'] = current_time
        
        # 3. Track access patterns
        access_history = memory.get('access_history', [])
        # Keep only the last 10 access times to avoid excessive growth
        if len(access_history) >= 10:
            access_history = access_history[-9:]
        access_history.append(current_time)
        memory['access_history'] = access_history
        
        # 4. Calculate the access frequency (accesses per day)
        if len(access_history) > 1:
            first_tracked = access_history[0]
            days_tracked = max(1, (current_time - first_tracked) / 86400)  # Convert to days
            memory['access_frequency'] = len(access_history) / days_tracked
        
        # 5. Update the memory in the database
        updated_memories.append(memory)
    
    # Batch update memories to minimize database operations
    if updated_memories:
        update_memories(updated_memories)
        logger.debug(f"Updated access statistics for {len(updated_memories)} memories")

# Semantic search using embeddings
def semantic_memory_search(query, memories, max_results=3, context=None, conversation_history=None):
    """Search memories using semantic similarity with embeddings.
    
    Args:
        query (str): The search query
        memories (list): List of memory dictionaries to search through
        max_results (int): Maximum number of results to return
        context (str, optional): Additional context information (like current topic)
        conversation_history (list, optional): Recent conversation history
    
    Returns:
        list: Relevant memories with added relevance scores and metadata
    """
    model = get_embedding_model()
    if not model:
        return keyword_memory_search(query, memories, max_results)
    
    # Get query embedding
    query_embedding = get_text_embedding(query)
    if query_embedding is None:
        return keyword_memory_search(query, memories, max_results)
    
    # Extract context topics if available
    context_topics = set()
    if context:
        # Extract key terms from context
        context_topics = set(re.findall(r'\b[a-zA-Z]{3,}\b', context.lower()))
    
    # Extract topics from recent conversation history
    conversation_topics = set()
    if conversation_history and len(conversation_history) > 0:
        # Get the last few user messages
        recent_messages = [msg['content'] for msg in conversation_history[-3:] 
                          if msg.get('role') == 'user']
        for msg in recent_messages:
            conversation_topics.update(re.findall(r'\b[a-zA-Z]{3,}\b', msg.lower()))
    
    # Combined topics for relevance boosting
    all_topics = context_topics.union(conversation_topics)
    
    relevance_scores = []
    
    # Process memories
    for memory in memories:
        memory_id = memory.get('id')
        content = memory.get('content', '')
        
        # Skip memories with empty content
        if not content.strip():
            continue
        
        # Use cached embedding if available
        if memory_id in memory_embedding_cache:
            memory_embedding = memory_embedding_cache[memory_id]
        else:
            memory_embedding = get_text_embedding(content)
            if memory_embedding is not None and memory_id:
                memory_embedding_cache[memory_id] = memory_embedding
        
        if memory_embedding is not None:
            # Calculate base semantic similarity
            similarity = cosine_similarity([query_embedding], [memory_embedding])[0][0]
            
            # Apply contextual boosting with enhanced context
            boosted_score, boost_factors = apply_contextual_boost(
                similarity, 
                memory, 
                query,
                context_topics=all_topics
            )
            
            # Create an enhanced memory object with scoring metadata
            enhanced_memory = memory.copy()
            enhanced_memory['relevance'] = round(boosted_score, 3)  # Overall relevance
            enhanced_memory['base_similarity'] = round(similarity, 3)  # Raw similarity
            enhanced_memory['boost_factors'] = boost_factors  # Breakdown of boosts applied
            
            relevance_scores.append((enhanced_memory, boosted_score))
    
    # Sort by relevance score (highest to lowest)
    relevance_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Get top results
    result_memories = [memory for memory, _ in relevance_scores[:max_results]]
    
    # Update access statistics for retrieved memories
    update_memory_access(result_memories)
    
    return result_memories

# Apply contextual boosting based on memory type and content
def apply_contextual_boost(base_score, memory, query, context_topics=None):
    """Boost relevance scores based on memory metadata and query context.
    
    Enhanced with:
    - More sophisticated category matching
    - Improved keyword analysis with partial matching
    - Better temporal relevance scoring
    - Named entity recognition and matching
    - Sentiment alignment between query and memory
    - Reinforcement from user interaction patterns
    
    Args:
        base_score (float): The base semantic similarity score
        memory (dict): The memory object with metadata
        query (str): The user's query
        context_topics (set, optional): Set of important topics from context
        
    Returns:
        tuple: (final_score, boost_factors) - the boosted score and a dictionary 
               explaining which factors contributed to the boost
    """
    boost = 0.0
    boost_factors = {}  # Track what contributed to boosting for explainability
    query_lower = query.lower()
    
    # Extract memory features
    category = memory.get('category', 'general')
    content = memory.get('content', '').lower()
    source = memory.get('source', 'unknown')
    confidence = memory.get('confidence', 0.5)
    tags = memory.get('tags', [])
    created_at = memory.get('created_at', 0)
    last_accessed = memory.get('last_accessed', 0)
    access_count = memory.get('access_count', 0)
    
    # 1. Enhanced category-query relevance boost with expanded matching
    category_boost = 0.0
    
    # Preference category matching with expanded terms
    if category == 'preference':
        if any(word in query_lower for word in ['prefer', 'like', 'favorite', 'want', 'enjoy', 'love', 
                                               'interested in', 'fond of', 'preference', 'opinion']):
            category_boost = 0.25  # Increased from 0.2
            
    # Fact category matching with question patterns
    elif category in ['fact', 'personal']:
        if any(word in query_lower for word in ['know', 'tell', 'what', 'who', 'where', 'when', 'why', 'how', 
                                               'explain', 'information', 'detail']):
            category_boost = 0.2  # Increased from 0.15
    
    # Instruction category matching with imperative patterns
    elif category in ['instruction', 'plan']:
        if any(pattern in query_lower for pattern in ['should', 'always', 'never', 'how to', 'remember to', 
                                                     'need to', 'have to', 'must', 'don\'t forget', 'make sure']):
            category_boost = 0.3  # Increased from 0.25
    
    # Personal category matching with self-references
    elif category == 'personal':
        if any(pattern in query_lower for pattern in ['i am', 'i\'m', 'my', 'me', 'myself', 'about me', 
                                                     'mine', 'i have', 'i\'ve', 'i was', 'i were']):
            category_boost = 0.25  # Increased from 0.2
    
    # Experience category matching with event patterns
    elif category == 'experience':
        if any(word in query_lower for word in ['happened', 'experienced', 'occurred', 'event', 'past', 
                                               'remember when', 'that time', 'when i', 'history']):
            category_boost = 0.25  # Increased from 0.2
    
    # Relationship category matching
    elif category == 'relationship':
        if any(word in query_lower for word in ['friend', 'family', 'partner', 'spouse', 'colleague', 
                                               'relationship', 'mother', 'father', 'brother', 'sister']):
            category_boost = 0.25
    
    # Health category matching
    elif category == 'health':
        if any(word in query_lower for word in ['health', 'medical', 'doctor', 'condition', 'allergy', 
                                               'diet', 'fitness', 'medication', 'symptom', 'wellness']):
            category_boost = 0.3
            
    if category_boost > 0:
        boost += category_boost
        boost_factors['category_match'] = round(category_boost, 2)
    
    # 2. Advanced keyword matching with partial matching and word importance weighting
    query_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query_lower))
    memory_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', content))
    
    # Remove common stop words for more meaningful matching
    stop_words = {'the', 'and', 'is', 'in', 'to', 'a', 'an', 'of', 'for', 'that', 'this', 'it', 'with', 'as', 'be', 'on', 'not'}
    filtered_query_words = query_words.difference(stop_words)
    filtered_memory_words = memory_words.difference(stop_words)
    
    # Direct keyword overlap (now with stop words removed)
    keyword_overlap = filtered_query_words.intersection(filtered_memory_words)
    if keyword_overlap:
        # More sophisticated boost based on ratio of matches to query length
        match_ratio = len(keyword_overlap) / max(1, len(filtered_query_words))
        keyword_boost = min(0.3 * match_ratio, 0.3)  # Up to 0.3 boost
        boost += keyword_boost
        boost_factors['keyword_match'] = round(keyword_boost, 2)
    
    # 3. Enhanced context relevance with topic weighting
    if context_topics and len(context_topics) > 0:
        context_overlap = filtered_memory_words.intersection(context_topics)
        if context_overlap:
            # Higher boost for memories that match multiple context topics
            overlap_ratio = len(context_overlap) / len(context_topics)
            context_boost = min(0.25 * overlap_ratio, 0.25)  # Up to 0.25 boost
            boost += context_boost
            boost_factors['context_relevance'] = round(context_boost, 2)
    
    # 4. Improved memory confidence boost with graduated scaling
    if confidence > 0.5:  # Lowered threshold from 0.8
        # Graduated scaling: more boost as confidence increases
        confidence_factor = (confidence - 0.5) / 0.5  # Scale from 0 to 1
        confidence_boost = 0.15 * confidence_factor  # Up to 0.15 boost
        boost += confidence_boost
        boost_factors['confidence_level'] = round(confidence_boost, 2)
    
    # 5. Enhanced source reliability boost
    source_boost = 0.0
    if source == 'user_explicit':  # User explicitly asked to remember
        source_boost = 0.25  # Highest boost for explicit user requests
    elif source == 'user_confirmed':  # User confirmed a detected fact
        source_boost = 0.2
    elif source == 'explicit':  # Other explicit sources
        source_boost = 0.15
    elif source == 'conversation_auto' and confidence > 0.8:  # High confidence auto-detection
        source_boost = 0.1
        
    if source_boost > 0:
        boost += source_boost
        boost_factors['source_reliability'] = round(source_boost, 2)
    
    # 6. Enhanced tag matching with partial matching
    if tags:
        tag_matches = sum(1 for tag in tags if any(tag.lower() in query_word for query_word in query_lower.split()))
        if tag_matches > 0:
            tag_boost = min(0.1 * tag_matches, 0.25)  # Up to 0.25 boost
            boost += tag_boost
            boost_factors['tag_relevance'] = round(tag_boost, 2)
    
    # 7. Advanced temporal relevance scoring
    
    # a) Frequency boost with logarithmic scaling for diminishing returns
    if access_count > 0:
        # Logarithmic scaling gives diminishing returns for very high access counts
        frequency_boost = min(0.15 * math.log(1 + access_count/2), 0.2)  # Up to 0.2 boost
        boost += frequency_boost
        boost_factors['usage_frequency'] = round(frequency_boost, 2)
    
    # b) Recency of access boost with graduated time decay
    if last_accessed > 0:
        time_diff = time.time() - last_accessed
        hours_diff = time_diff / 3600  # Convert to hours
        
        recency_boost = 0.0
        if hours_diff < 1:  # Accessed within the last hour
            recency_boost = 0.2
        elif hours_diff < 24:  # Accessed within the last day
            recency_boost = 0.15
        elif hours_diff < 168:  # Accessed within the last week
            recency_boost = 0.1 * max(0, (168 - hours_diff) / 168)
            
        if recency_boost > 0:
            boost += recency_boost
            boost_factors['recent_access'] = round(recency_boost, 2)
    
    # c) Memory age relevance (newer memories might be more relevant)
    if created_at > 0:
        memory_age = time.time() - created_at
        days_old = memory_age / 86400  # Convert to days
        
        # Boost newer memories (less than 30 days old)
        if days_old < 30:
            age_factor = max(0, (30 - days_old) / 30)  # Scale from 0 to 1
            age_boost = 0.1 * age_factor  # Up to 0.1 boost
            boost += age_boost
            boost_factors['recent_creation'] = round(age_boost, 2)
    
    # 8. Named entity matching (simplified version)
    query_entities = re.findall(r'\b[A-Z][a-z]+\b', query)  # Capitalized words as potential entities
    memory_entities = re.findall(r'\b[A-Z][a-z]+\b', memory.get('content', ''))
    
    entity_matches = set(q.lower() for q in query_entities).intersection(set(m.lower() for m in memory_entities))
    if entity_matches:
        entity_boost = min(0.2 * len(entity_matches), 0.3)  # Up to 0.3 boost
        boost += entity_boost
        boost_factors['entity_match'] = round(entity_boost, 2)
    
    # Apply the total boost (cap at 0.99 to avoid perfect 1.0)
    final_score = min(0.99, base_score + boost)
    
    # Add debugging for top boost factors
    top_factors = sorted(boost_factors.items(), key=lambda x: x[1], reverse=True)[:3]
    logger.debug(f"Memory boost factors for '{memory.get('content', '')[:30]}...': {top_factors}")
    
    return final_score, boost_factors

# Debug logging for memory retrieval analysis
def debug_log_memory_retrieval(query, expanded_query, memories, stage, original_count=None):
    """Log detailed information about memory retrieval for analysis and debugging.
    
    This function tracks every step of the memory retrieval process with detailed metrics
    to help analyze and fine-tune the memory system.
    
    Args:
        query (str): The original user query
        expanded_query (str): The expanded query after processing
        memories (list): The retrieved memory objects
        stage (str): Current processing stage (e.g., 'semantic_search', 'keyword_search', 'final_selection')
        original_count (int, optional): Original number of memories before filtering
    """
    if not DEBUG_MEMORY_SYSTEM:
        return
        
    try:
        log_parts = []
        memory_count = len(memories) if memories else 0
        
        # Basic retrieval stats
        log_parts.append(f"=== MEMORY DEBUG [{stage.upper()}] ===")
        log_parts.append(f"Query: '{query[:50]}{'...' if len(query) > 50 else ''}' ")
        log_parts.append(f"Expanded: '{expanded_query[:70]}{'...' if len(expanded_query) > 70 else ''}' ")
        log_parts.append(f"Retrieved: {memory_count} memories")
        
        if original_count is not None:
            log_parts.append(f"Filtered: {original_count} → {memory_count} memories")
            
        # Category distribution
        if memory_count > 0:
            categories = {}
            for memory in memories:
                cat = memory.get('category', 'unknown')
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += 1
                
            log_parts.append("\nCategory Distribution:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                log_parts.append(f"  - {cat}: {count} memories")
        
        # Individual memory details (for final selections only)
        if stage == 'final_selection' and memory_count > 0:
            log_parts.append("\nSelected Memories:")
            for i, memory in enumerate(memories):
                # Basic memory info
                content_preview = memory.get('content', '')[:50]
                content_preview = f"{content_preview}..." if len(memory.get('content', '')) > 50 else content_preview
                
                # Relevance scoring details
                relevance = memory.get('relevance', 0)
                boost_factors = memory.get('boost_factors', {})
                top_boosts = sorted(boost_factors.items(), key=lambda x: x[1], reverse=True)[:3]
                
                log_parts.append(f"\n  [{i+1}] {memory.get('category', 'unknown').upper()} (score: {relevance:.2f})")
                log_parts.append(f"      Content: {content_preview}")
                
                # Metadata that affected ranking
                metadata = []
                if top_boosts:
                    boost_str = ", ".join([f"{k}: +{v:.2f}" for k, v in top_boosts])
                    metadata.append(f"Boost factors: {boost_str}")
                
                if memory.get('access_count'):
                    metadata.append(f"Access count: {memory.get('access_count')}")
                    
                if memory.get('last_accessed'):
                    last_access = time.time() - memory.get('last_accessed')
                    if last_access < 86400:
                        hours = last_access / 3600
                        metadata.append(f"Last accessed: {hours:.1f} hours ago")
                    else:
                        days = last_access / 86400
                        metadata.append(f"Last accessed: {days:.1f} days ago")
                        
                log_parts.append(f"      Metadata: {', '.join(metadata)}")
        
        # Combine all log parts
        full_log = "\n".join(log_parts)
        logger.debug(full_log)
        
        # In high-detail mode, also output to a file for analysis
        if DEBUG_MEMORY_DETAIL and stage == 'final_selection':
            log_file = os.path.join(os.path.dirname(memory_file), 'memory_analysis.log')
            with open(log_file, 'a') as f:
                f.write(f"\n{'-'*80}\n")
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {full_log}\n")
                
    except Exception as e:
        logger.error(f"Error in memory debug logging: {e}")


# Keyword-based memory search (fallback method)
def keyword_memory_search(query, memories, max_results=3):
    """Search memories using simple keyword matching as a fallback."""
    query_words = set(query.lower().split())
    relevance_scores = []
    
    for memory in memories:
        content = memory['content'].lower()
        # Count how many query words appear in the memory
        matching_words = sum(1 for word in query_words if word in content)
        if matching_words > 0:
            # Calculate a simple relevance score
            score = matching_words / len(query_words)
            # Apply contextual boosting
            boosted_score = apply_contextual_boost(score, memory, query)
            relevance_scores.append((memory, boosted_score))
    
    # Sort by relevance score (highest to lowest)
    relevance_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return the top N most relevant memories
    result_memories = [memory for memory, score in relevance_scores[:max_results]]
    
    # Update access statistics for retrieved memories
    update_memory_access(result_memories)
    
    return result_memories

# Update a memory by its ID
def update_memories(memories_to_update):
    """Update multiple memories in a single batch operation.
    
    This function efficiently updates multiple memories at once,
    reducing file I/O operations and improving performance when
    updating access statistics or other metadata for multiple memories.
    
    Args:
        memories_to_update (list): List of memory objects with updated fields
        
    Returns:
        int: Number of memories successfully updated
    """
    if not memories_to_update:
        return 0
        
    try:
        all_memories = get_all_memories()
        updated_count = 0
        current_time = time.time()
        
        # Create a memory ID lookup for faster matching
        memory_map = {memory['id']: i for i, memory in enumerate(all_memories)}        
        
        # Process each memory to update
        for updated_memory in memories_to_update:
            memory_id = updated_memory.get('id')
            if not memory_id or memory_id not in memory_map:
                logger.warning(f"Cannot update memory - ID {memory_id} not found")
                continue
                
            # Get index of memory to update
            idx = memory_map[memory_id]
            
            # Update memory fields
            for key, value in updated_memory.items():
                # Skip the ID field since we shouldn't change it
                if key != 'id':
                    all_memories[idx][key] = value
            
            # Add modification timestamp
            all_memories[idx]['modified_at'] = current_time
            updated_count += 1
        
        # Save all memories if any were updated
        if updated_count > 0:
            with open(memory_file, 'w') as f:
                json.dump(all_memories, f, indent=2)
            logger.info(f"Batch updated {updated_count} memories")
        
        return updated_count
            
    except Exception as e:
        logger.error(f"Error in batch memory update: {e}")
        return 0


def update_memory(memory_id, update_data):
    """Update a memory with new data.
    
    Args:
        memory_id (str): The ID of the memory to update
        update_data (dict): Dictionary containing fields to update
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        # Create a complete memory object with ID and update data
        memory_with_id = {'id': memory_id}
        memory_with_id.update(update_data)
        
        # Use the batch update function for consistency
        updated_count = update_memories([memory_with_id])
        success = updated_count > 0
        
        if success:
            logger.info(f"Updated memory {memory_id}")
        else:
            logger.warning(f"Memory {memory_id} not found for update")
        
        return success
            
    except Exception as e:
        logger.error(f"Error updating memory {memory_id}: {e}")
        return False

# Update memory access statistics
def update_memory_access(memories):
    """Update access statistics for memories that were retrieved.
    
    Args:
        memories (list): List of memory objects that were accessed
    """
    for memory in memories:
        if 'id' in memory:
            try:
                # Update the memory in the storage using our update_memory function
                memory_id = memory['id']
                access_count = memory.get('access_count', 0) + 1
                
                # Use timestamp for consistency with other memory operations
                update_memory_data = {
                    'last_accessed': time.time(),  # Use timestamp instead of ISO format
                    'access_count': access_count   # Use consistent field name
                }
                
                # Update the memory in storage
                update_memory(memory_id, update_memory_data)
                
                # Also update the memory object directly for immediate use
                memory['last_accessed'] = time.time()
                memory['access_count'] = access_count
                
                logger.debug(f"Updated access statistics for memory {memory_id}, count: {access_count}")
            except Exception as e:
                logger.error(f"Error updating memory access statistics: {e}")

# Delete a memory by ID
def delete_memory_by_id(memory_id):
    """Delete a memory by its ID."""
    memories = get_all_memories()
    initial_count = len(memories)
    
    # Filter out the memory with the given ID
    memories = [m for m in memories if m['id'] != memory_id]
    
    if len(memories) < initial_count:
        # Memory was found and removed
        with open(memory_file, 'w') as f:
            json.dump(memories, f, indent=2)
        logger.info(f"[MEMORY] Deleted memory: {memory_id[:8]}...")
        return True
    else:
        # Memory not found
        logger.warning(f"[MEMORY] Memory not found for deletion: {memory_id[:8]}...")
        return False

# Detect and save important facts from conversations
def detect_and_save_important_facts(user_message, ai_response):
    """Automatically detect and save important facts from conversations.
    This is a simplified implementation - in reality you'd use an LLM to identify key facts.
    """
    # Skip if either message is empty
    if not user_message or not ai_response:
        return False
    
    # Pattern 1: Direct remember/learn commands
    remember_patterns = [
        # Basic remember patterns
        r'^remember\s+that\s+(.+)$',
        r'^remember\s+(.+)$',
        r'^minerva[,\s]+remember\s+that\s+(.+)$',
        r'^minerva[,\s]+remember\s+(.+)$',
        # Learn patterns
        r'^learn\s+that\s+(.+)$', 
        r'^please\s+remember\s+that\s+(.+)$',
        r'^please\s+learn\s+(.+)$'
    ]
    
    lower_msg = user_message.lower()
    
    # Check for explicit commands first
    for pattern in remember_patterns:
        match = re.search(pattern, lower_msg)
        if match:
            fact = match.group(1).strip()
            if fact and len(fact) > 3 and not fact.endswith('?'):
                logger.info(f"[MEMORY] Detected explicit remember command: {fact}")
                memory_id = save_memory(fact, source='user_explicit', tags=['remember_command'])
                logger.info(f"[MEMORY] Saved with ID: {memory_id[:8]}...")
                return True
    
    # Pattern 2: Check for forget/delete commands
    forget_patterns = [
        r'^forget\s+that\s+(.+)$',
        r'^forget\s+(.+)$',
        r'^minerva[,\s]+forget\s+(.+)$',
        r'^delete\s+memory\s+about\s+(.+)$'
    ]
    
    for pattern in forget_patterns:
        match = re.search(pattern, lower_msg)
        if match:
            # This is simplified - in a real implementation, you'd use semantic search
            # to find the memory to delete based on the content
            topic = match.group(1).strip()
            logger.info(f"[MEMORY] Detected forget command for topic: {topic}")
            # Find memories that might match this topic
            memories = get_all_memories()
            deleted_count = 0
            for memory in memories:
                if topic.lower() in memory['content'].lower():
                    if delete_memory_by_id(memory['id']):
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"[MEMORY] Deleted {deleted_count} memories related to '{topic}'")
            return True
    
    # Pattern 3: User information patterns - personal facts worth remembering
    info_patterns = {
        'name': r'my\s+name\s+is\s+([\w\s]+)',
        'location': r'i\s+live\s+in\s+([\w\s,]+)',
        'job': r'i\s+(work|am\s+employed)\s+(at|as|with)\s+([\w\s,&]+)',
        'preference': r'i\s+(like|love|prefer|enjoy)\s+([\w\s,]+)',
        'dislike': r'i\s+(dislike|hate|don\'t\s+like)\s+([\w\s,]+)',
        'family': r'my\s+(wife|husband|partner|son|daughter|child|children|family)\s+(is|are)\s+([\w\s,]+)'
    }
    
    for category, pattern in info_patterns.items():
        match = re.search(pattern, lower_msg)
        if match:
            # The last group contains the relevant information
            info = match.group(match.lastindex).strip()
            if info and len(info) > 2:
                fact = user_message.strip()
                logger.info(f"[MEMORY] Auto-detected {category} info: {info}")
                memory_id = save_memory(fact, source='auto_detected', tags=['user_info', category])
                logger.info(f"[MEMORY] Saved user info with ID: {memory_id[:8]}...")
                return True
    
    # Pattern 4: Check for important facts in AI responses that might be worth saving
    # This simulates the AI learning from its own responses
    if len(ai_response) > 50:
        # Extract sentences that might contain factual information
        sentences = re.split(r'(?<=[.!?])\s+', ai_response)
        for sentence in sentences:
            # Only consider sentences of appropriate length
            if 20 <= len(sentence) <= 150:
                # Check for patterns that often indicate factual information
                if any(pattern in sentence.lower() for pattern in 
                       ['is defined as', 'refers to', 'is a type of', 'is characterized by']):
                    logger.info(f"[MEMORY] Auto-detected knowledge fact from AI response: {sentence}")
                    memory_id = save_memory(sentence, source='ai_learning', tags=['knowledge'])
                    logger.info(f"[MEMORY] Saved knowledge with ID: {memory_id[:8]}...")
                    return True
    
    return False

# API tracking functions
def track_api_call(model, tokens=0, response_time=0):
    """Track an API call to a specific model.
    
    Args:
        model (str): The model name (e.g., 'gpt-4', 'claude-3-opus')
        tokens (int): Number of tokens used in the request and response
        response_time (float): Time taken for the API call to complete
    """
    if not TRACK_API_USAGE:
        return
        
    try:
        # Load current stats
        usage_stats = get_api_usage_stats()
        
        # Initialize model entry if not exists
        if model not in usage_stats:
            usage_stats[model] = {
                'count': 0,
                'total_tokens': 0,
                'total_response_time': 0,
                'avg_response_time': 0,
                'estimated_cost': 0,
                'last_used': time.time()
            }
        
        # Update stats
        usage_stats[model]['count'] += 1
        usage_stats[model]['total_tokens'] += tokens
        usage_stats[model]['total_response_time'] += response_time
        usage_stats[model]['avg_response_time'] = (
            usage_stats[model]['total_response_time'] / usage_stats[model]['count']
        )
        usage_stats[model]['last_used'] = time.time()
        
        # Update estimated cost based on model and tokens
        price_per_1k = get_model_price(model)
        if price_per_1k > 0:
            token_cost = (tokens / 1000) * price_per_1k
            usage_stats[model]['estimated_cost'] += token_cost
        
        # Save updated stats
        save_api_usage_stats(usage_stats)
        
        logger.debug(f"Tracked API call: {model}, tokens: {tokens}, time: {response_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Error tracking API call: {e}")


def get_api_usage_stats():
    """Get the current API usage statistics.
    
    Returns:
        dict: Dictionary with model usage statistics
    """
    try:
        if os.path.exists(analytics_file):
            with open(analytics_file, 'r') as f:
                return json.load(f)
        return {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_api_usage_stats(usage_stats):
    """Save API usage statistics to disk.
    
    Args:
        usage_stats (dict): Dictionary with model usage statistics
    """
    try:
        with open(analytics_file, 'w') as f:
            json.dump(usage_stats, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving API usage stats: {e}")


def get_model_price(model):
    """Get the price per 1000 tokens for a specific model.
    
    Args:
        model (str): The model name
        
    Returns:
        float: Price per 1000 tokens in USD
    """
    # Approximate pricing for different models (USD per 1000 tokens)
    # These are simplifications and should be updated with actual pricing
    pricing = {
        # OpenAI models
        'gpt-4': 0.03,
        'gpt-4-turbo': 0.01,
        'gpt-4-0125-preview': 0.01,
        'gpt-4-1106-preview': 0.01,
        'gpt-4-vision-preview': 0.01,
        'gpt-3.5-turbo': 0.002,
        'gpt-3.5-turbo-0125': 0.002,
        'gpt-3.5-turbo-16k': 0.003,
        
        # Anthropic models
        'claude-3-opus': 0.015,
        'claude-3-sonnet': 0.008,
        'claude-3-haiku': 0.003,
        'claude-2': 0.008,
        'claude-instant': 0.002,
        
        # Google models
        'gemini-pro': 0.0,  # Currently free
        'gemini-ultra': 0.0,  # Currently free
        
        # Mistral models
        'mistral-small': 0.002,
        'mistral-medium': 0.007,
        'mistral-large': 0.015,
    }
    
    # Return the price for the model, or 0 if not known
    return pricing.get(model.lower(), 0.0)


def get_response_quality_metrics():
    """Get metrics about response quality from user feedback.
    
    Returns:
        dict: Dictionary with quality metrics
    """
    # This would ideally read from a feedback database
    # For now, return placeholder metrics
    return {
        'avg_quality': 4.7,  # Average rating out of 5
        'avg_response_time': 2.1,  # Average response time in seconds
        'feedback_count': 24,  # Number of feedback responses received
    }


# Initialize memory system on startup
initialize_memory_storage()

# Main entry point
if __name__ == '__main__':
    from flask import redirect  # Import here to avoid circular imports
    import argparse
    
    # Parse command line arguments for port
    parser = argparse.ArgumentParser(description='Start the Minerva minimal chat server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()
    
    # Run the Flask app
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = args.port or int(os.environ.get('FLASK_PORT', 5000))  # Command line overrides env var
    
    print(f"[STARTUP] Starting Minerva minimal chat server on {host}:{port}")
    print(f"[STARTUP] Access the chat interface at http://{host}:{port}/chat")
    print(f"[STARTUP] REST API endpoints available at http://{host}:{port}/api/...")
    print(f"[STARTUP] Press Ctrl+C to stop the server")
    
    try:
        app.run(host=host, port=port, debug=dev_mode)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\nError: Port {port} is already in use.")
            print(f"Try using a different port with: python {sys.argv[0]} --port <port_number>")
            print("Suggested ports: 5001, 8000, 8080, 8888")
        else:
            print(f"\nError starting server: {e}")
        sys.exit(1)
