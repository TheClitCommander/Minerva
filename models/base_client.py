#!/usr/bin/env python3
"""
Base Model Client

Abstract base class for all AI model clients in Minerva.
Provides common interface and functionality.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BaseModelClient(ABC):
    """
    Abstract base class for AI model clients.
    
    All AI provider clients should inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, api_key: str, provider_name: str):
        """
        Initialize the base client.
        
        Args:
            api_key: API key for the service
            provider_name: Name of the AI provider (e.g., 'openai', 'anthropic')
        """
        self.api_key = api_key
        self.provider_name = provider_name
        self.logger = logging.getLogger(f"{__name__}.{provider_name}")
        
        # Initialize metrics tracking
        self.request_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.error_count = 0
        
        # Client initialization (to be implemented by subclasses)
        self._init_client()
    
    @abstractmethod
    def _init_client(self):
        """Initialize the specific AI client. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def generate_response(self, user_input: str, model_name: str, session_id: Optional[str] = None) -> str:
        """
        Generate a response using the AI model.
        
        Args:
            user_input: The user's message
            model_name: Name of the specific model to use
            session_id: Optional session ID for context tracking
            
        Returns:
            The AI-generated response
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models for this provider.
        
        Returns:
            List of model information dictionaries
        """
        pass
    
    def validate_api_key(self) -> bool:
        """
        Validate the API key format and availability.
        
        Returns:
            True if API key appears valid
        """
        if not self.api_key:
            return False
        
        # Basic length check
        if len(self.api_key) < 8:
            return False
            
        return True
    
    def _track_request(self, tokens_used: int = 0, cost: float = 0.0, error: bool = False):
        """
        Track metrics for a request.
        
        Args:
            tokens_used: Number of tokens used in the request
            cost: Estimated cost of the request
            error: Whether the request resulted in an error
        """
        self.request_count += 1
        self.total_tokens += tokens_used
        self.total_cost += cost
        
        if error:
            self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get usage metrics for this client.
        
        Returns:
            Dictionary of usage statistics
        """
        return {
            'provider': self.provider_name,
            'request_count': self.request_count,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1)
        }
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4
    
    def _handle_api_error(self, error: Exception, context: str = "API call") -> str:
        """
        Handle API errors and return user-friendly message.
        
        Args:
            error: The exception that occurred
            context: Context of where the error occurred
            
        Returns:
            User-friendly error message
        """
        error_msg = f"{self.provider_name} {context} failed: {str(error)}"
        self.logger.error(error_msg)
        self._track_request(error=True)
        
        # Return user-friendly message
        return f"I apologize, but I'm having trouble connecting to {self.provider_name}. Please try again later."
    
    def _validate_model_name(self, model_name: str) -> bool:
        """
        Validate that the model name is supported.
        
        Args:
            model_name: Name of the model to validate
            
        Returns:
            True if model is supported
        """
        available_models = [model['id'] for model in self.get_available_models()]
        return model_name in available_models
    
    def __str__(self) -> str:
        """String representation of the client."""
        return f"{self.provider_name.title()}Client(requests={self.request_count}, errors={self.error_count})"
    
    def __repr__(self) -> str:
        """Detailed representation of the client."""
        return f"{self.__class__.__name__}(provider='{self.provider_name}', api_key='***{self.api_key[-4:] if self.api_key else 'None'}')" 