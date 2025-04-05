"""
Framework Manager for Minerva

This module manages different AI frameworks and provides a unified interface for the Minerva system.
It's crucial for the proper functioning of the Think Tank and conversation memory persistence.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Setup logging
logger = logging.getLogger(__name__)

class FrameworkManager:
    """
    Manages integration between different AI frameworks and provides a unified 
    interface for the Minerva system to use various models and capabilities.
    """
    
    def __init__(self, config=None):
        """
        Initialize the FrameworkManager with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.active_frameworks = {}
        self.memory_enabled = True
        self.logger = logger
        self.logger.info("FrameworkManager initialized")
    
    def register_framework(self, name: str, framework_instance):
        """
        Register a framework with the manager.
        
        Args:
            name: Name of the framework
            framework_instance: Instance of the framework
        """
        self.active_frameworks[name] = framework_instance
        self.logger.info(f"Registered framework: {name}")
    
    def get_framework(self, name: str):
        """
        Get a registered framework by name.
        
        Args:
            name: Name of the framework to retrieve
            
        Returns:
            The framework instance if found, None otherwise
        """
        if name in self.active_frameworks:
            return self.active_frameworks[name]
        self.logger.warning(f"Framework not found: {name}")
        return None
    
    def list_frameworks(self) -> List[str]:
        """
        List all registered frameworks.
        
        Returns:
            List of framework names
        """
        return list(self.active_frameworks.keys())
    
    def process_request(self, request_data: Dict[str, Any], framework_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a request using a specified framework or the default one.
        
        Args:
            request_data: Dictionary containing request data
            framework_name: Optional name of the framework to use
            
        Returns:
            Response dictionary from the framework
        """
        if framework_name and framework_name in self.active_frameworks:
            framework = self.active_frameworks[framework_name]
        elif self.active_frameworks:
            # Use the first available framework if none specified
            framework_name = next(iter(self.active_frameworks))
            framework = self.active_frameworks[framework_name]
        else:
            self.logger.error("No frameworks registered")
            return {"error": "No frameworks available to process request"}
        
        self.logger.info(f"Processing request with framework: {framework_name}")
        
        try:
            response = framework.process(request_data)
            
            # Ensure conversation_id is maintained for memory persistence
            if 'conversation_id' in request_data and self.memory_enabled:
                response['conversation_id'] = request_data['conversation_id']
            elif self.memory_enabled and 'conversation_id' not in response:
                # Generate a new conversation ID if needed
                response['conversation_id'] = f"conv-{os.urandom(4).hex()}"
                
            return response
        except Exception as e:
            self.logger.error(f"Error processing request with {framework_name}: {e}")
            return {"error": f"Error processing request: {str(e)}"}
    
    def configure(self, config_data: Dict[str, Any]) -> bool:
        """
        Update configuration for the manager and all registered frameworks.
        
        Args:
            config_data: Dictionary containing configuration data
            
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            self.config.update(config_data)
            
            # Apply relevant config to each framework
            for name, framework in self.active_frameworks.items():
                if hasattr(framework, 'configure') and callable(framework.configure):
                    framework_config = config_data.get(name, {})
                    framework.configure(framework_config)
            
            return True
        except Exception as e:
            self.logger.error(f"Error configuring frameworks: {e}")
            return False
    
    def enable_memory(self, enabled: bool = True):
        """
        Enable or disable conversation memory persistence.
        
        Args:
            enabled: True to enable memory, False to disable
        """
        self.memory_enabled = enabled
        self.logger.info(f"Memory persistence {'enabled' if enabled else 'disabled'}")
