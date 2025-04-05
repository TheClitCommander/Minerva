#!/usr/bin/env python3
"""
Think Tank API Handler for Minerva Central

This module implements a simplified API handler for the Think Tank functionality
that can be integrated directly into Minerva Central's server.
"""

import os
import sys
import json
import logging
import uuid
from http.server import BaseHTTPRequestHandler
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
logger = logging.getLogger("think_tank_api")

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
                conversation_id = f"conv-{uuid.uuid4()}"
                
            # Initialize memory for this conversation if needed
            if conversation_id not in conversation_memory:
                conversation_memory[conversation_id] = []
                
            # Add current message to memory
            conversation_memory[conversation_id].append({
                "role": "user",
                "message": message,
                "timestamp": "simulated"
            })
            
            # Generate a response based on the type of query
            if "help" in message.lower() or "?" in message:
                response = "I'm here to help with your Minerva projects. What would you like to know?"
            elif "project" in message.lower():
                response = "I can help you organize your ideas into projects. Would you like to create a new project based on this conversation?"
            elif "features" in message.lower() or "capabilities" in message.lower():
                response = "Minerva offers several features including conversation memory, project organization, and natural language processing."
            else:
                response = "I understand your message and would normally process it through the Think Tank. However, I'm currently in fallback mode. The development team is working to fully integrate the Think Tank functionality."
            
            # Add response to memory
            conversation_memory[conversation_id].append({
                "role": "assistant",
                "message": response,
                "timestamp": "simulated"
            })
            
            # Return structured response
            return {
                "response": response,
                "conversation_id": conversation_id,
                "model_info": {
                    "model_used": "fallback_enhanced", 
                    "processing_time": 0,
                    "context_length": len(conversation_memory[conversation_id])
                },
                "status": "success"
            }

def handle_think_tank_request(request_handler, post_data):
    """Handle a Think Tank API request"""
    try:
        # Parse request data
        request_data = json.loads(post_data)
        message = request_data.get('message', '')
        conversation_id = request_data.get('conversation_id')
        
        logger.info(f"Received Think Tank request: {message[:50]}...")
        
        # Process with Think Tank
        result = process_with_think_tank(
            message=message,
            conversation_id=conversation_id
        )
        
        # Return the response
        response_data = {
            "response": result.get("response", ""),
            "model_info": result.get("model_info", {}),
            "conversation_id": result.get("conversation_id", conversation_id),
            "status": "success",
            "canCreateProject": True  # Enable project conversion functionality
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error processing Think Tank request: {str(e)}")
        return {
            "response": f"I apologize, but there was an error processing your request. Error: {str(e)}",
            "status": "error",
            "error": str(e)
        }
