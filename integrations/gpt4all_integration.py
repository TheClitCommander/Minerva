"""
GPT4All Integration for Minerva AI Assistant

This module provides integration with the GPT4All framework.
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any
from loguru import logger

from .base_integration import BaseIntegration

class GPT4AllIntegration(BaseIntegration):
    """Integration with GPT4All framework."""
    
    def __init__(self, framework_path: str):
        """
        Initialize the GPT4All integration.
        
        Args:
            framework_path: Path to the GPT4All installation
        """
        super().__init__("GPT4All", framework_path)
        
        self.api_available = False
        self.models_path = os.path.join(os.path.expanduser("~"), ".cache", "gpt4all")
        
        # Add these capabilities
        self.capabilities = ["text_generation", "chat", "local_execution"]
        
        try:
            # Check if GPT4All is installed via pip
            try:
                import gpt4all
                self.api_available = True
                self.gpt4all_module = gpt4all
                self.model = None
                logger.info("GPT4All package is installed")
            except ImportError:
                logger.warning("GPT4All package is not installed, attempting to install...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "gpt4all"])
                    import gpt4all
                    self.api_available = True
                    self.gpt4all_module = gpt4all
                    self.model = None
                    logger.info("Successfully installed GPT4All package")
                except Exception as e:
                    logger.error(f"Failed to install GPT4All: {str(e)}")
            
            logger.info(f"GPT4All API available: {self.api_available}")
            
        except Exception as e:
            logger.error(f"Error initializing GPT4All integration: {str(e)}")
    
    def load_model(self, model_name="gpt4all-j-v1.3-groovy"):
        """
        Load a GPT4All model.
        
        Args:
            model_name: Name of the model to load
        
        Returns:
            True if model was loaded successfully, False otherwise
        """
        if not self.api_available:
            logger.error("GPT4All API is not available")
            return False
        
        try:
            logger.info(f"Loading GPT4All model: {model_name}")
            self.model = self.gpt4all_module.GPT4All(model_name, model_path=self.models_path)
            logger.info(f"Successfully loaded model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error loading GPT4All model: {str(e)}")
            return False
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Process a message using GPT4All.
        
        Args:
            message: The message to process
            context: Optional context for processing
        
        Returns:
            Response from GPT4All
        """
        if not self.api_available:
            return "GPT4All is not available"
        
        if not self.model:
            logger.info("Model not loaded, attempting to load default model")
            if not self.load_model():
                return "Failed to load GPT4All model"
        
        try:
            logger.info(f"Sending message to GPT4All: {message[:50]}...")
            
            # Process system prompt if provided in context
            system_prompt = ""
            if context and "system_prompt" in context:
                system_prompt = context["system_prompt"]
            
            # Generate response
            response = self.model.generate(
                message, 
                max_tokens=200,
                temp=0.7,
                system_prompt=system_prompt
            )
            
            logger.info(f"GPT4All response: {response[:50]}...")
            return response
        except Exception as e:
            logger.error(f"Error processing message with GPT4All: {str(e)}")
            return f"Error: {str(e)}"
    
    def generate_response(self, message: str) -> str:
        """
        Generate a response to a message.
        
        Args:
            message: The message to respond to
        
        Returns:
            Response from GPT4All
        """
        return self.process_message(message)
