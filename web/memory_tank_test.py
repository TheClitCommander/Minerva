#!/usr/bin/env python3
"""
Simplified Memory-Enabled Think Tank Server
This minimal server demonstrates the integration between conversation memory and Think Tank
"""

import os
import json
import time
import uuid
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("memory_tank")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory storage (would be replaced by proper database in production)
conversation_history = {}
memory_store = {}

# Configuration
MAX_CONVERSATION_HISTORY = 20
MEMORY_ENABLED = True

@app.route('/')
def index():
    """Serve the main chat interface"""
    return send_from_directory('.', 'simplest_test.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """Process chat messages with memory integration and Think Tank"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        store_in_memory = data.get('store_in_memory', True)
        
        logger.info(f"[CHAT] Processing message: {user_message[:30]}... for conversation {conversation_id}")
        
        # Initialize conversation if needed
        if conversation_id not in conversation_history:
            conversation_history[conversation_id] = []
        
        # Add message to conversation history
        conversation_history[conversation_id].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get relevant memories for this conversation
        relevant_memories = []
        if MEMORY_ENABLED:
            relevant_memories = get_relevant_memories(user_message)
            if relevant_memories:
                logger.info(f"[MEMORY] Found {len(relevant_memories)} relevant memories")
        
        # Process with Think Tank simulation
        response, memory_details = process_with_memory_tank(
            message=user_message,
            conversation_id=conversation_id,
            conversation_history=conversation_history[conversation_id],
            relevant_memories=relevant_memories
        )
        
        # Store user information if requested
        memory_id = None
        if store_in_memory and MEMORY_ENABLED:
            # Extract facts from message (simplified)
            extracted_facts = extract_facts(user_message)
            if extracted_facts:
                fact = extracted_facts[0]
                memory_id = save_memory(
                    content=fact,
                    source='conversation', 
                    tags=['user_info'],
                    importance=7
                )
                logger.info(f"[MEMORY] Saved fact with ID {memory_id}: {fact}")
        
        # Add AI response to conversation history
        response_id = str(uuid.uuid4())
        conversation_history[conversation_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "message_id": response_id
        })
        
        # Trim conversation if needed
        if len(conversation_history[conversation_id]) > MAX_CONVERSATION_HISTORY:
            conversation_history[conversation_id] = conversation_history[conversation_id][-MAX_CONVERSATION_HISTORY:]
        
        # Return response with memory details
        return jsonify({
            "status": "success",
            "response": response,
            "conversation_id": conversation_id,
            "message_id": response_id,
            "memory_id": memory_id,
            "memory_info": memory_details,
            "think_tank_result": {
                "blended_response": response,
                "model_info": {
                    "models_used": ["gpt-4o", "claude-3-sonnet"],
                    "primary_model": "think_tank"
                }
            }
        })
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

def get_relevant_memories(query, max_count=3):
    """Simple semantic search simulation for relevant memories"""
    # In a real implementation, this would use vector similarity search
    results = []
    for memory_id, memory in memory_store.items():
        # Simulate relevance (would use vector similarity in real implementation)
        if query.lower() in memory['content'].lower():
            # Create a copy with a simulated relevance score
            memory_copy = memory.copy()
            memory_copy['relevance'] = 0.85
            results.append(memory_copy)
    
    # Sort by last_accessed and limit results
    results = sorted(results, key=lambda x: x.get('last_accessed', 0), reverse=True)
    return results[:max_count]

def extract_facts(message):
    """Extract potential facts from user message (simplified)"""
    # In a real implementation, this would use LLM or NLP techniques
    # For demo, if message is long enough, treat it as a potential fact
    if len(message) > 15:
        return [message]
    return []

def save_memory(content, source='user', tags=None, category=None, importance=5):
    """Save a memory to storage"""
    memory_id = str(uuid.uuid4())
    memory = {
        'id': memory_id,
        'content': content,
        'source': source,
        'category': category or 'general',
        'tags': tags or [],
        'importance': importance,
        'created_at': time.time(),
        'last_accessed': time.time(),
        'access_count': 1
    }
    memory_store[memory_id] = memory
    logger.info(f"[MEMORY] Saved new memory: {content[:30]}...")
    return memory_id

def format_memories_for_context(memories):
    """Format memories for inclusion in AI context"""
    if not memories:
        return ""
    
    memory_text = "Here are some relevant memories that might help with your response:\n\n"
    for i, memory in enumerate(memories):
        memory_text += f"{i+1}. {memory['content']}\n"
    
    return memory_text

def process_with_memory_tank(message, conversation_id, conversation_history, relevant_memories):
    """Process a message with the Think Tank and memory integration"""
    # In a real implementation, this would call the actual Think Tank
    # For demo, simulate a response that incorporates memories
    
    # Prepare conversation context
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]])
    
    # Format memories for inclusion
    memory_context = format_memories_for_context(relevant_memories)
    
    # Log what we're processing
    logger.info(f"[THINK_TANK] Processing message with {len(relevant_memories)} memories")
    if memory_context:
        logger.info(f"[THINK_TANK] Memory context: {memory_context[:100]}...")
    
    # Simulate response generation
    if relevant_memories:
        memory_used = relevant_memories[0]['content']
        response = f"Based on our previous conversations, I remember that {memory_used}. "
        response += f"Regarding your question about '{message}', here's what I think..."
        memory_details = {
            "memories_used": len(relevant_memories),
            "memory_influence": 0.85
        }
    else:
        response = f"I don't have specific memories about '{message}', but I can help you with that. "
        response += "Here's my response based on my general knowledge..."
        memory_details = {
            "memories_used": 0,
            "memory_influence": 0
        }
    
    # Add some variation to make it look more natural
    if "project" in message.lower():
        response += "\n\nWould you like me to help you organize this into a new project?"
    elif "remember" in message.lower():
        response += "\n\nI've stored this information in my memory system and will remember it for our future conversations."
    
    return response, memory_details

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run the memory-enabled Think Tank server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the server on')
    args = parser.parse_args()
    
    logger.info(f"Starting Memory-Enabled Think Tank Server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True)
