#!/usr/bin/env python3
"""
HuggingFace Model Client

Client implementation for HuggingFace Inference API integration.
"""

import time
import requests
from typing import Dict, Any, Optional, List
from .base_client import BaseModelClient


class HuggingFaceClient(BaseModelClient):
    """Client for HuggingFace Inference API integration."""
    
    def __init__(self, api_key: str):
        """
        Initialize HuggingFace client.
        
        Args:
            api_key: HuggingFace API key
        """
        super().__init__(api_key, "huggingface")
        
    def _init_client(self):
        """Initialize the HuggingFace client."""
        if not self.validate_api_key():
            raise ValueError("Invalid HuggingFace API key")
        
        self.base_url = "https://api-inference.huggingface.co/models"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.logger.info("HuggingFace client initialized successfully")
    
    def validate_api_key(self) -> bool:
        """Validate HuggingFace API key format."""
        if not self.api_key:
            return False
        
        # HuggingFace keys start with 'hf_' and are typically long
        return self.api_key.startswith('hf_') and len(self.api_key) >= 10
    
    def generate_response(self, user_input: str, model_name: str, session_id: Optional[str] = None) -> str:
        """
        Generate response using HuggingFace API.
        
        Args:
            user_input: User's message
            model_name: HuggingFace model name (e.g., 'falcon-7b', 'gpt2')
            session_id: Optional session ID for context
            
        Returns:
            AI-generated response
        """
        try:
            start_time = time.time()
            
            # Prepare the payload
            payload = {
                "inputs": user_input,
                "options": {
                    "use_cache": True,
                    "wait_for_model": True
                },
                "parameters": {
                    "max_new_tokens": 250,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True
                }
            }
            
            # Make the API call
            url = f"{self.base_url}/{model_name}"
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            # Handle the response
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list) and len(data) > 0:
                    if 'generated_text' in data[0]:
                        response_text = data[0]['generated_text']
                    else:
                        response_text = str(data[0])
                elif isinstance(data, dict):
                    if 'generated_text' in data:
                        response_text = data['generated_text']
                    else:
                        response_text = str(data)
                else:
                    response_text = str(data)
                
                # Clean up response (remove input echo if present)
                if response_text.startswith(user_input):
                    response_text = response_text[len(user_input):].strip()
                
                # Track metrics
                tokens_used = self._estimate_tokens(user_input + response_text)
                cost = self._estimate_cost(tokens_used, model_name)
                
                self._track_request(tokens_used=tokens_used, cost=cost)
                
                # Log success
                elapsed_time = time.time() - start_time
                self.logger.info(f"HuggingFace response generated in {elapsed_time:.2f}s using {model_name}")
                
                return response_text
            else:
                error_msg = f"HuggingFace API error: {response.status_code} - {response.text}"
                raise ValueError(error_msg)
            
        except Exception as e:
            return self._handle_api_error(e, "inference")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available HuggingFace models."""
        return [
            {
                'id': 'falcon-7b',
                'name': 'Falcon 7B',
                'provider': 'huggingface',
                'max_tokens': 2000,
                'context_window': 4000,
                'cost_per_1k_tokens': 0.001
            },
            {
                'id': 'microsoft/DialoGPT-medium',
                'name': 'DialoGPT Medium',
                'provider': 'huggingface',
                'max_tokens': 1000,
                'context_window': 2000,
                'cost_per_1k_tokens': 0.0005
            }
        ]
    
    def _estimate_cost(self, tokens: int, model_name: str) -> float:
        """
        Estimate cost for HuggingFace API call.
        
        Args:
            tokens: Number of tokens used
            model_name: Name of the model used
            
        Returns:
            Estimated cost in USD (HuggingFace is often free/low cost)
        """
        # HuggingFace inference API is often free for smaller models
        # Estimate very low costs
        costs = {
            'falcon-7b': 0.001,
            'microsoft/DialoGPT-medium': 0.0005,
            'gpt2': 0.0001
        }
        
        cost_per_1k = costs.get(model_name, 0.001)  # Default to low cost
        return (tokens / 1000) * cost_per_1k 