#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dummy OpenAI module for development environments where the official OpenAI Python library is not installed.
This module provides minimal functionality to allow the application to run without requiring the full OpenAI library.
"""

import logging
import time
import json
import os
import random
import uuid

# Configure logging
logger = logging.getLogger('openai')
logger.warning("Using dummy OpenAI implementation - development mode only")

# Constants
DUMMY_MODELS = {
    "gpt-4": {
        "id": "gpt-4",
        "object": "model",
        "name": "gpt-4",
        "version": "dev-dummy",
        "capabilities": {
            "creative": 0.95,
            "technical": 0.90,
            "reasoning": 0.92,
            "context_window": 8192
        }
    },
    "gpt-4o": {
        "id": "gpt-4o",
        "object": "model",
        "name": "gpt-4o",
        "version": "dev-dummy",
        "capabilities": {
            "creative": 0.97,
            "technical": 0.93,
            "reasoning": 0.95,
            "context_window": 128000
        }
    },
    "gpt-3.5-turbo": {
        "id": "gpt-3.5-turbo",
        "object": "model",
        "name": "gpt-3.5-turbo",
        "version": "dev-dummy",
        "capabilities": {
            "creative": 0.85,
            "technical": 0.80,
            "reasoning": 0.78,
            "context_window": 4096
        }
    }
}

# Dummy responses based on message types
DUMMY_RESPONSES = {
    "greeting": [
        "Hello! I'm the Minerva Assistant running in development mode. How can I help you today?",
        "Hi there! I'm here to assist with your Minerva projects. What would you like to discuss?",
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
    "technical": [
        "I can analyze technical problems and provide solutions. In development mode, I'd normally connect to GPT-4 for advanced technical reasoning.",
        "For technical questions, I would typically use specialized AI models to generate detailed answers. I'm currently running in development mode.",
        "Technical assistance is one of my core capabilities. With proper API keys, I could provide more detailed technical guidance."
    ],
    "general": [
        "I understand your request. This is a simulated response from the OpenAI GPT-4 model in development mode.",
        "I'm processing your message in development mode. With proper API keys, I would connect to OpenAI's servers for enhanced responses.",
        "Thank you for your message. I'm currently operating with a dummy OpenAI implementation, providing simulated responses."
    ]
}

def get_response_type(message):
    """Determine the type of response based on message content"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
        return "greeting"
    elif any(word in message_lower for word in ["help", "assist", "support", "?"]):
        return "help"
    elif any(word in message_lower for word in ["project", "organize", "structure"]):
        return "project"
    elif any(word in message_lower for word in ["code", "program", "develop", "technical", "fix", "debug"]):
        return "technical"
    else:
        return "general"

def generate_dummy_response(messages, model="gpt-4"):
    """Generate a dummy response for the given messages"""
    # Extract the latest user message
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break
    
    # Determine response type
    response_type = get_response_type(user_message)
    
    # Get appropriate responses for this type
    possible_responses = DUMMY_RESPONSES.get(response_type, DUMMY_RESPONSES["general"])
    
    # Select a response randomly
    response = random.choice(possible_responses)
    
    # Add development mode note
    response += "\n\n[Note: This is a simulated response in development mode. Connect real API keys for production use.]"
    
    return response

# OpenAI Client class
class OpenAI:
    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "sk-dummy-development-key")
        self.chat = ChatCompletion()
        self.models = Models()
        logger.info("Initialized dummy OpenAI client")

# Chat completion module
class ChatCompletion:
    @staticmethod
    def create(model="gpt-4", messages=None, **kwargs):
        """Simulate chat completion API call"""
        start_time = time.time()
        
        # Log the request
        logger.info(f"Dummy chat completion request with model: {model}")
        
        # Generate response
        content = generate_dummy_response(messages, model)
        
        # Create response structure matching OpenAI API
        completion_id = f"chatcmpl-{str(uuid.uuid4())[:8]}"
        created = int(time.time())
        
        # Calculate tokens (approximate)
        prompt_tokens = sum(len(msg.get("content", "")) // 4 for msg in messages)
        completion_tokens = len(content) // 4
        
        # Create response object
        response = {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }
        
        # Log timing
        elapsed = time.time() - start_time
        logger.info(f"Dummy completion generated in {elapsed:.2f}s")
        
        return DummyResponse(response)

# Models module
class Models:
    @staticmethod
    def list():
        """Return list of dummy models"""
        return {
            "object": "list",
            "data": list(DUMMY_MODELS.values())
        }
    
    @staticmethod
    def retrieve(model_id):
        """Return info about a specific model"""
        if model_id in DUMMY_MODELS:
            return DUMMY_MODELS[model_id]
        else:
            raise ValueError(f"Model '{model_id}' not found")

# Helper class to make response behave like the real thing
class DummyResponse:
    def __init__(self, data):
        self._data = data
        
    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'DummyResponse' has no attribute '{name}'")
    
    def json(self):
        return self._data
    
    def __str__(self):
        return json.dumps(self._data)
        
# Create an instance for direct imports
client = OpenAI()

# Expose top-level functions and classes used by the application
__all__ = ['OpenAI', 'ChatCompletion', 'Models', 'client']
