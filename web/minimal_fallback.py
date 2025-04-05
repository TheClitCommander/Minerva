#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal Fallback Processor

This module provides a simple fallback implementation for the Think Tank processing
when external dependencies or API connections aren't available.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger("minimal_fallback")

def process_message(message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple fallback implementation that works without external dependencies.
    
    Args:
        message: The user message to process
        conversation_id: Optional conversation ID for tracking
        
    Returns:
        Dict containing a simple response
    """
    logger.info(f"Using minimal fallback implementation for: {message[:30]}...")
    start_time = time.time()
    
    # Generate a simple response based on the message
    if not message.strip():
        response_text = "I didn't receive a message. How can I help you?"
    else:
        # Simple pattern matching for basic functionality
        message_lower = message.lower()
        
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
            response_text = "Hello! I'm operating in a simplified mode right now. How can I assist you?"
        elif "help" in message_lower or "how can you" in message_lower:
            response_text = "I can help answer questions and have conversations, though I'm currently operating in a simplified mode."
        elif any(word in message_lower for word in ["thank", "thanks", "appreciated"]):
            response_text = "You're welcome! Let me know if there's anything else I can help with."
        elif "?" in message:
            response_text = f"That's an interesting question about '{message[:30]}...'. While I'm operating in a simplified mode, I'll do my best to assist you. Could you provide more details?"
        else:
            response_text = f"I understand your message about '{message[:30]}...'. I'm currently operating in a simplified mode due to technical constraints, but I'm still here to assist you. Could you tell me more about what you need?"
    
    processing_time = time.time() - start_time
    
    # Format response 
    return {
        "response": response_text,
        "conversation_id": conversation_id or str(uuid.uuid4()),
        "model_info": {
            "model_used": "minimal_fallback",
            "processing_time": processing_time,
            "simplified_mode": True
        },
        "status": "success"
    }

if __name__ == "__main__":
    # Test the fallback processor
    test_messages = [
        "Hello there!",
        "How can you help me?",
        "What is the meaning of life?",
        "Thanks for your help",
        "Can you explain how neural networks work?",
        ""
    ]
    
    for test_message in test_messages:
        result = process_message(test_message)
        print(f"\nTEST: {test_message}")
        print(f"RESPONSE: {result['response']}")
