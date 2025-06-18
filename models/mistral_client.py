#!/usr/bin/env python3
"""
Mistral Model Client

Client implementation for Mistral AI API integration.
"""

import time
from typing import Dict, Any, Optional, List
from .base_client import BaseModelClient

try:
    import mistralai
    from mistralai.client import MistralClient as MistralSDK
    from mistralai.models.chat_completion import ChatMessage
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False


class MistralClient(BaseModelClient):
    """Client for Mistral AI API integration."""
    
    def __init__(self, api_key: str):
        """
        Initialize Mistral client.
        
        Args:
            api_key: Mistral API key
        """
        if not MISTRAL_AVAILABLE:
            raise ImportError("Mistral package not available. Install with: pip install mistralai")
        
        super().__init__(api_key, "mistral")
        
    def _init_client(self):
        """Initialize the Mistral client."""
        if not self.validate_api_key():
            raise ValueError("Invalid Mistral API key")
        
        self.client = MistralSDK(api_key=self.api_key)
        self.logger.info("Mistral client initialized successfully")
    
    def validate_api_key(self) -> bool:
        """Validate Mistral API key format."""
        if not self.api_key:
            return False
        
        # Mistral keys are typically long strings
        return len(self.api_key) >= 20
    
    def generate_response(self, user_input: str, model_name: str, session_id: Optional[str] = None) -> str:
        """
        Generate response using Mistral API.
        
        Args:
            user_input: User's message
            model_name: Mistral model name (e.g., 'mistral-large', 'mistral-small')
            session_id: Optional session ID for context
            
        Returns:
            AI-generated response
        """
        try:
            start_time = time.time()
            
            # Map model names to Mistral model IDs
            model_map = {
                'mistral-large': 'mistral-large-latest',
                'mistral-medium': 'mistral-medium-latest',
                'mistral-small': 'mistral-small-latest'
            }
            
            # Get the actual model ID
            model_id = model_map.get(model_name, 'mistral-large-latest')
            
            # Create the messages
            messages = [ChatMessage(role="user", content=user_input)]
            
            # Make API call
            response = self.client.chat(
                model=model_id,
                messages=messages
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Track metrics
            tokens_used = self._estimate_tokens(user_input + response_text)
            cost = self._estimate_cost(tokens_used, model_name)
            
            self._track_request(tokens_used=tokens_used, cost=cost)
            
            # Log success
            elapsed_time = time.time() - start_time
            self.logger.info(f"Mistral response generated in {elapsed_time:.2f}s using {model_name}")
            
            return response_text
            
        except Exception as e:
            return self._handle_api_error(e, "chat completion")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available Mistral models."""
        return [
            {
                'id': 'mistral-large',
                'name': 'Mistral Large',
                'provider': 'mistral',
                'max_tokens': 4000,
                'context_window': 32000,
                'cost_per_1k_tokens': 0.008
            },
            {
                'id': 'mistral-small',
                'name': 'Mistral Small',
                'provider': 'mistral',
                'max_tokens': 4000,
                'context_window': 32000,
                'cost_per_1k_tokens': 0.003
            }
        ]
    
    def _estimate_cost(self, tokens: int, model_name: str) -> float:
        """
        Estimate cost for Mistral API call.
        
        Args:
            tokens: Number of tokens used
            model_name: Name of the model used
            
        Returns:
            Estimated cost in USD
        """
        # Cost per 1K tokens for different models
        costs = {
            'mistral-large': 0.008,
            'mistral-medium': 0.005,
            'mistral-small': 0.003
        }
        
        cost_per_1k = costs.get(model_name, 0.008)  # Default to Large pricing
        return (tokens / 1000) * cost_per_1k 