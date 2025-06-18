#!/usr/bin/env python3
"""
OpenAI Model Client

Client implementation for OpenAI API integration.
"""

import time
from typing import Dict, Any, Optional, List
from .base_client import BaseModelClient

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIClient(BaseModelClient):
    """Client for OpenAI API integration."""
    
    def __init__(self, api_key: str):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")
        
        super().__init__(api_key, "openai")
        
    def _init_client(self):
        """Initialize the OpenAI client."""
        if not self.validate_api_key():
            raise ValueError("Invalid OpenAI API key")
        
        self.client = OpenAI(api_key=self.api_key)
        self.logger.info("OpenAI client initialized successfully")
    
    def validate_api_key(self) -> bool:
        """Validate OpenAI API key format."""
        if not self.api_key:
            return False
        
        # OpenAI keys start with 'sk-' and are at least 20 characters
        return self.api_key.startswith('sk-') and len(self.api_key) >= 20
    
    def generate_response(self, user_input: str, model_name: str, session_id: Optional[str] = None) -> str:
        """
        Generate response using OpenAI API.
        
        Args:
            user_input: User's message
            model_name: OpenAI model name (e.g., 'gpt-4o', 'gpt-3.5-turbo')
            session_id: Optional session ID for context
            
        Returns:
            AI-generated response
        """
        try:
            start_time = time.time()
            
            # Prepare messages
            messages = [{"role": "user", "content": user_input}]
            
            # Make API call
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Track metrics
            tokens_used = response.usage.total_tokens if response.usage else self._estimate_tokens(user_input + response_text)
            cost = self._estimate_cost(tokens_used, model_name)
            
            self._track_request(tokens_used=tokens_used, cost=cost)
            
            # Log success
            elapsed_time = time.time() - start_time
            self.logger.info(f"OpenAI response generated in {elapsed_time:.2f}s using {model_name}")
            
            return response_text
            
        except Exception as e:
            return self._handle_api_error(e, "chat completion")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available OpenAI models."""
        return [
            {
                'id': 'gpt-4o',
                'name': 'GPT-4o',
                'provider': 'openai',
                'max_tokens': 8000,
                'context_window': 128000,
                'cost_per_1k_tokens': 0.01
            },
            {
                'id': 'gpt-3.5-turbo',
                'name': 'GPT-3.5 Turbo',
                'provider': 'openai',
                'max_tokens': 4000,
                'context_window': 16000,
                'cost_per_1k_tokens': 0.002
            }
        ]
    
    def _estimate_cost(self, tokens: int, model_name: str) -> float:
        """
        Estimate cost for OpenAI API call.
        
        Args:
            tokens: Number of tokens used
            model_name: Name of the model used
            
        Returns:
            Estimated cost in USD
        """
        # Cost per 1K tokens for different models
        costs = {
            'gpt-4o': 0.01,
            'gpt-3.5-turbo': 0.002,
            'gpt-4': 0.03,
            'gpt-4-turbo': 0.015
        }
        
        cost_per_1k = costs.get(model_name, 0.01)  # Default to GPT-4o pricing
        return (tokens / 1000) * cost_per_1k 