#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced fallback processor for Minerva Think Tank.
This module provides simulated responses when the full AI integration is unavailable.
"""

import logging
import uuid
import time
import json
import os
import random
import datetime

# Configure logging
logger = logging.getLogger("enhanced_fallback")

# Sample responses for different query types
FALLBACK_RESPONSES = {
    "greeting": [
        "Hello! I'm Minerva Assistant. How can I help you today?",
        "Hi there! I'm here to assist with your projects. What would you like to discuss?",
        "Welcome to Minerva. I'm here to help organize your thoughts and projects."
    ],
    "help": [
        "I can help you organize ideas, create projects, and answer questions. What would you like assistance with?",
        "Minerva offers several features including conversation memory, project organization, and idea development. How can I assist you today?",
        "I'm designed to help with project organization, brainstorming, and information retrieval. What do you need help with?"
    ],
    "project": [
        "Would you like to create a new project based on our conversation? I can help organize your ideas into a structured format.",
        "Projects in Minerva help organize related conversations and ideas. Would you like to create one now?",
        "I can convert this conversation into a project to keep track of the ideas we've discussed. Would that be helpful?"
    ],
    "error": [
        "I notice there's an issue with my connection to external AI services. I'm operating in local mode right now.",
        "I'm currently running in fallback mode without external AI connections. I can still help with basic tasks.",
        "My external AI connections aren't available right now, but I'm still here to help with what I can."
    ],
    "general": [
        "I understand your request. In full operation mode, I would connect to multiple AI models for a comprehensive response.",
        "I've processed your request. With external AI services, I could provide more specialized assistance for this topic.",
        "Thank you for your message. When fully configured with API keys, I'll provide enhanced responses through multiple AI models."
    ]
}

def get_response_type(message):
    """Determine the type of response based on the message content."""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
        return "greeting"
    elif any(word in message_lower for word in ["help", "assist", "support", "?"]):
        return "help"
    elif any(word in message_lower for word in ["project", "organize", "structure"]):
        return "project"
    elif any(word in message_lower for word in ["error", "issue", "problem", "not working"]):
        return "error"
    else:
        return "general"

def generate_fallback_response(message, conversation_id=None):
    """
    Generate a fallback response when AI services are unavailable.
    
    Args:
        message: The user's message
        conversation_id: Optional conversation ID
        
    Returns:
        dict: A response object mimicking the format of the full ThinkTank response
    """
    start_time = time.time()
    
    if not conversation_id:
        conversation_id = f"conv-{uuid.uuid4()}"
    
    # Determine response type
    response_type = get_response_type(message)
    
    # Get appropriate responses for this type
    possible_responses = FALLBACK_RESPONSES.get(response_type, FALLBACK_RESPONSES["general"])
    
    # Select a response randomly
    response = random.choice(possible_responses)
    
    # Add a note about fallback mode for transparency
    response += "\n\n[Note: I'm currently operating in local mode without external AI connections.]"
    
    # Calculate processing time
    elapsed_time = time.time() - start_time
    
    # Create response object in the same format as the ThinkTank
    current_time = datetime.datetime.now().isoformat()
    
    return {
        "response": response,
        "conversation_id": conversation_id,
        "model_info": {
            "model": "enhanced_fallback",
            "fallback_mode": True,
            "response_type": response_type
        },
        "processing_stats": {
            "time_taken": elapsed_time,
            "fallback": True,
            "timestamp": time.time()
        },
        "memory_updates": {
            "id": f"mem-{conversation_id}",
            "type": "conversation",
            "title": f"Conversation {conversation_id}",
            "content": response,
            "source": "minerva_fallback",
            "timestamp": current_time,
            "projectId": "default",
            "conversation_id": conversation_id,
            "tags": ["conversation", "fallback"] 
        }
    }

def process_message(message, conversation_id=None):
    """
    Process a message with the enhanced fallback processor.
    This function mimics the interface of process_with_think_tank.
    
    Args:
        message: The user's message
        conversation_id: Optional conversation ID
        
    Returns:
        dict: A response object
    """
    logger.info(f"Processing message with enhanced fallback: {message[:30]}...")
    return generate_fallback_response(message, conversation_id)
