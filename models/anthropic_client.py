#!/usr/bin/env python3
"""
Anthropic Model Client

Client implementation for Anthropic Claude API integration.
"""

import time
from typing import Dict, Any, Optional, List
from .base_client import BaseModelClient

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicClient(BaseModelClient):
    """Client for Anthropic Claude API integration."""
    
    def __init__(self, api_key: str):
        """
        Initialize Anthropic client.
        
        Args:
            api_key: Anthropic API key
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package not available. Install with: pip install anthropic")
        
        super().__init__(api_key, "anthropic")
        
    def _init_client(self):
        """Initialize the Anthropic client."""
        if not self.validate_api_key():
            raise ValueError("Invalid Anthropic API key")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.logger.info("Anthropic client initialized successfully")
    
    def validate_api_key(self) -> bool:
        """Validate Anthropic API key format."""
        if not self.api_key:
            return False
        
        # Anthropic keys start with 'sk-ant-' and are long
        return self.api_key.startswith('sk-ant-') and len(self.api_key) >= 20
    
    def generate_response(self, user_input: str, model_name: str, session_id: Optional[str] = None) -> str:
        """
        Generate response using Anthropic API.
        
        Args:
            user_input: User's message
            model_name: Anthropic model name (e.g., 'claude-3-opus', 'claude-3-sonnet')
            session_id: Optional session ID for context
            
        Returns:
            AI-generated response
        """
        try:
            start_time = time.time()
            
            # Make API call
            response = self.client.messages.create(
                model=model_name,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": user_input}
                ]
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Track metrics
            tokens_used = response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else self._estimate_tokens(user_input + response_text)
            cost = self._estimate_cost(tokens_used, model_name)
            
            self._track_request(tokens_used=tokens_used, cost=cost)
            
            # Log success
            elapsed_time = time.time() - start_time
            self.logger.info(f"Anthropic response generated in {elapsed_time:.2f}s using {model_name}")
            
            return response_text
            
        except Exception as e:
            return self._handle_api_error(e, "message creation")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available Anthropic models."""
        return [
            {
                'id': 'claude-3-opus',
                'name': 'Claude 3 Opus',
                'provider': 'anthropic',
                'max_tokens': 4000,
                'context_window': 200000,
                'cost_per_1k_tokens': 0.015
            },
            {
                'id': 'claude-3-sonnet',
                'name': 'Claude 3 Sonnet',
                'provider': 'anthropic',
                'max_tokens': 4000,
                'context_window': 180000,
                'cost_per_1k_tokens': 0.008
            }
        ]
    
    def _estimate_cost(self, tokens: int, model_name: str) -> float:
        """
        Estimate cost for Anthropic API call.
        
        Args:
            tokens: Number of tokens used
            model_name: Name of the model used
            
        Returns:
            Estimated cost in USD
        """
        # Cost per 1K tokens for different models
        costs = {
            'claude-3-opus': 0.015,
            'claude-3-sonnet': 0.008,
            'claude-3-haiku': 0.0025
        }
        
        cost_per_1k = costs.get(model_name, 0.008)  # Default to Sonnet pricing
        return (tokens / 1000) * cost_per_1k 