#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced fallback module for Minerva

This module provides enhanced fallback responses when real AI models are unavailable.
"""

import logging
import uuid
import time
import json
import os
import random
import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Define response types
RESPONSE_TYPES = {
    "greeting": ["hello", "hi", "hey", "greetings", "howdy", "morning", "afternoon", "evening"],
    "inquiry": ["what", "how", "why", "when", "where", "who", "tell me about", "explain", "describe"],
    "farewell": ["bye", "goodbye", "see you", "later", "farewell"],
    "gratitude": ["thanks", "thank you", "appreciate", "grateful"],
    "general": []
}

# Define fallback responses for each type
FALLBACK_RESPONSES = {
    "greeting": [
        "Hello! I'm Minerva, your AI assistant. How can I help you today?",
        "Hi there! I'm Minerva. What can I assist you with?",
        "Greetings! I'm Minerva, ready to help with your questions."
    ],
    "inquiry": [
        "That's an interesting question. In enhanced simulation mode, I can provide general information, but I may not have the most current or detailed data on specific topics.",
        "I'd be happy to help with that question. In simulation mode, I can offer general guidance on this topic.",
        "I understand you're asking about this topic. While operating in simulation mode, I can provide a general perspective."
    ],
    "farewell": [
        "Goodbye! Feel free to return if you have more questions.",
        "See you later! I'll be here when you need assistance again.",
        "Until next time! Have a great day."
    ],
    "gratitude": [
        "You're welcome! I'm glad I could help.",
        "Happy to assist! Is there anything else you'd like to know?",
        "My pleasure! Feel free to ask if you need anything else."
    ],
    "general": [
        "I understand you're interested in this topic. In simulation mode, I can provide general information but may not have all the specific details.",
        "That's something I'd like to help with. While I'm running in simulation mode without connection to external AI services, I can offer some general thoughts.",
        "I appreciate your question. I'm currently operating in simulation mode, but I'll do my best to provide a helpful response."
    ]
}

def get_response_type(message):
    """
    Determine the type of response needed based on the message content.
    
    Args:
        message: The user's message
        
    Returns:
        str: The response type
    """
    message_lower = message.lower()
    
    for response_type, keywords in RESPONSE_TYPES.items():
        if any(keyword in message_lower for keyword in keywords):
            return response_type
    
    return "general"

def generate_fallback_response(message, conversation_id=None):
    """
    Generate a fallback response when AI services are unavailable.
    
    Args:
        message: The user's message
        conversation_id: Optional conversation ID
        
    Returns:
        dict: A response object mimicking the format of the full AI response
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
