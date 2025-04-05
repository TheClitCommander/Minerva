"""
Base Integration Class for Jarvis AI Assistant

This module defines the base integration class that all framework integrations will inherit from.
"""

import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from loguru import logger

class BaseIntegration(ABC):
    """Abstract base class for all AI framework integrations."""
    
    def __init__(self, framework_name: str, framework_path: str):
        """
        Initialize the base integration.
        
        Args:
            framework_name: Name of the framework
            framework_path: Path to the framework installation
        """
        self.framework_name = framework_name
        self.framework_path = framework_path
        self.capabilities = []  # Default empty capabilities list to be populated by subclasses
        
        # Set up logging
        logger.info(f"{framework_name} integration initialized at {framework_path}")
        
        # Add the framework to the Python path
        sys.path.append(framework_path)
        logger.info(f"Added {framework_path} to system path")
    
    @property
    def name(self) -> str:
        """
        Get the name of the framework.
        
        Returns:
            Framework name
        """
        return self.framework_name
    
    def get_capabilities(self) -> List[str]:
        """
        Get a list of capabilities provided by this framework.
        
        Returns:
            List of capability strings
        """
        return self.capabilities
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this framework.
        
        Returns:
            Dictionary of framework information
        """
        return {
            "name": self.framework_name,
            "path": self.framework_path,
            "capabilities": self.get_capabilities(),
            "version": self._get_version(),
            "description": f"{self.framework_name} Integration"
        }
    
    def _get_version(self) -> str:
        """
        Get the version of the framework.
        
        Returns:
            Version string
        """
        # Default implementation, can be overridden by subclasses
        return "0.1.0"
    
    @abstractmethod
    def generate_code(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate code using this framework.
        
        Args:
            prompt: The code generation prompt
            context: Optional context information
            
        Returns:
            Dict containing the generated code and metadata
        """
        pass
    
    @abstractmethod
    def execute_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task using this framework.
        
        Args:
            task: The task description
            context: Optional context information
            
        Returns:
            Dict containing the execution results and metadata
        """
        pass
        
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the framework is healthy and functioning.
        
        Returns:
            Dict containing health status information
        """
        return {
            "status": "healthy",
            "framework": self.framework_name,
            "details": "Basic health check passed"
        }
    
    def setup_environment(self) -> bool:
        """
        Set up any environment requirements for this framework.
        
        Returns:
            True if setup was successful
        """
        return True
    
    def cleanup_environment(self) -> bool:
        """
        Clean up any environment changes made by this framework.
        
        Returns:
            True if cleanup was successful
        """
        return True
