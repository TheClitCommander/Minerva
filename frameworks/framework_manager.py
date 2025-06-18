#!/usr/bin/env python3
"""
Framework Manager for Minerva

Consolidated framework management system that handles discovery, loading,
and execution of AI frameworks. Moved from integrations/ to frameworks/
as part of the refactoring plan.
"""

import os
import sys
import json
import importlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)


class FrameworkManager:
    """
    Consolidated framework manager for Minerva.
    
    Manages the discovery, loading, and execution of AI frameworks
    with improved organization and cleaner interfaces.
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize the framework manager.
        
        Args:
            registry_path: Path to framework registry file (default: frameworks/registry.json)
        """
        # Set registry path
        if registry_path is None:
            self.registry_path = Path(__file__).parent / "registry.json"
        else:
            self.registry_path = Path(registry_path)
        
        # Initialize data structures
        self.frameworks = {}                    # Framework definitions from registry
        self.loaded_frameworks = {}             # Actually loaded framework instances
        self.capability_scores = {}             # Performance scores by capability
        self.configuration = {}                 # Global configuration
        
        # Load registry
        self._load_registry()
        
        # Set up logging
        self.logger = logger
        self.logger.info("Framework Manager initialized")
    
    def _load_registry(self):
        """Load the framework registry from JSON file."""
        try:
            if self.registry_path.exists():
                with open(self.registry_path, 'r') as f:
                    registry_data = json.load(f)
                
                self.frameworks = registry_data.get('frameworks', {})
                self.capability_scores = registry_data.get('capability_scores', {})
                self.configuration = registry_data.get('configuration', {})
                
                self.logger.info(f"Loaded {len(self.frameworks)} frameworks from registry")
            else:
                self.logger.warning(f"Registry file not found: {self.registry_path}")
                self._create_empty_registry()
                
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading registry: {e}")
            self._create_empty_registry()
    
    def _create_empty_registry(self):
        """Create an empty registry if none exists."""
        empty_registry = {
            "version": "2.0.0",
            "last_updated": datetime.now().isoformat(),
            "frameworks": {},
            "capability_scores": {},
            "configuration": {
                "auto_discovery_enabled": True,
                "health_check_interval": 300,
                "max_concurrent_frameworks": 5,
                "fallback_framework": "huggingface"
            }
        }
        
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(empty_registry, f, indent=2)
        
        self.frameworks = {}
        self.capability_scores = {}
        self.configuration = empty_registry["configuration"]
        
        self.logger.info(f"Created empty registry at {self.registry_path}")
    
    def _save_registry(self):
        """Save the current registry to disk."""
        registry_data = {
            "version": "2.0.0",
            "last_updated": datetime.now().isoformat(),
            "frameworks": self.frameworks,
            "capability_scores": self.capability_scores,
            "configuration": self.configuration
        }
        
        with open(self.registry_path, 'w') as f:
            json.dump(registry_data, f, indent=2)
        
        self.logger.info("Registry saved to disk")
    
    def get_available_frameworks(self) -> List[Dict[str, Any]]:
        """Get list of all available frameworks."""
        return [
            {
                "id": framework_id,
                "name": framework_data.get("name", framework_id),
                "type": framework_data.get("type", "unknown"),
                "enabled": framework_data.get("enabled", False),
                "capabilities": framework_data.get("capabilities", []),
                "loaded": framework_id in self.loaded_frameworks
            }
            for framework_id, framework_data in self.frameworks.items()
        ]
    
    def get_frameworks_by_capability(self, capability: str) -> List[str]:
        """Get frameworks that support a specific capability."""
        matching_frameworks = []
        
        for framework_id, framework_data in self.frameworks.items():
            if capability in framework_data.get("capabilities", []):
                matching_frameworks.append(framework_id)
        
        # Sort by capability score if available
        if capability in self.capability_scores:
            scores = self.capability_scores[capability]
            matching_frameworks.sort(
                key=lambda f: scores.get(f, 0.0), 
                reverse=True
            )
        
        return matching_frameworks
    
    def get_best_framework(self, capability: str) -> Optional[str]:
        """Get the best framework for a specific capability."""
        frameworks = self.get_frameworks_by_capability(capability)
        
        # Return the highest-scoring available framework
        for framework_id in frameworks:
            if (self.frameworks[framework_id].get("enabled", False) and
                self._is_framework_available(framework_id)):
                return framework_id
        
        return None
    
    def _is_framework_available(self, framework_id: str) -> bool:
        """Check if a framework is available for use."""
        if framework_id not in self.frameworks:
            return False
        
        framework_data = self.frameworks[framework_id]
        
        # Check if it's API-based (always available if configured)
        if framework_data.get("api_based", False):
            return True
        
        # Check if primary path exists
        primary_path = framework_data.get("primary_path")
        if primary_path and Path(primary_path).exists():
            return True
        
        # Check alternative paths
        for path in framework_data.get("paths", []):
            if Path(path).exists():
                return True
        
        return False
    
    def load_framework(self, framework_id: str) -> bool:
        """
        Load a framework into memory.
        
        Args:
            framework_id: ID of the framework to load
            
        Returns:
            True if loading was successful
        """
        if framework_id in self.loaded_frameworks:
            self.logger.debug(f"Framework {framework_id} already loaded")
            return True
        
        if framework_id not in self.frameworks:
            self.logger.error(f"Framework {framework_id} not found in registry")
            return False
        
        framework_data = self.frameworks[framework_id]
        
        if not framework_data.get("enabled", False):
            self.logger.warning(f"Framework {framework_id} is disabled")
            return False
        
        try:
            # Try to load the integration module
            integration_module_name = framework_data.get("integration_module")
            
            if integration_module_name:
                # Try importing from integrations directory
                integration_module = importlib.import_module(f"integrations.{integration_module_name}")
                
                # Get the integration class
                class_name = f"{framework_id.title()}Integration"
                integration_class = getattr(integration_module, class_name, None)
                
                if integration_class:
                    # Initialize with primary path
                    primary_path = framework_data.get("primary_path")
                    if primary_path:
                        integration_instance = integration_class(primary_path)
                    else:
                        integration_instance = integration_class()
                    
                    # Store loaded framework
                    self.loaded_frameworks[framework_id] = integration_instance
                    
                    self.logger.info(f"Successfully loaded framework: {framework_id}")
                    return True
                else:
                    self.logger.error(f"Integration class not found for {framework_id}")
            else:
                self.logger.error(f"No integration module specified for {framework_id}")
                
        except ImportError as e:
            self.logger.error(f"Failed to import integration for {framework_id}: {e}")
        except Exception as e:
            self.logger.error(f"Error loading framework {framework_id}: {e}")
        
        return False
    
    def execute_with_framework(self, framework_id: str, method: str, *args, **kwargs) -> Any:
        """
        Execute a method using a specific framework.
        
        Args:
            framework_id: ID of the framework to use
            method: Method name to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result from the framework method
        """
        # Load framework if not already loaded
        if framework_id not in self.loaded_frameworks:
            if not self.load_framework(framework_id):
                raise RuntimeError(f"Failed to load framework: {framework_id}")
        
        framework_instance = self.loaded_frameworks[framework_id]
        
        # Check if method exists
        if not hasattr(framework_instance, method):
            raise AttributeError(f"Framework {framework_id} does not have method {method}")
        
        # Execute the method
        framework_method = getattr(framework_instance, method)
        return framework_method(*args, **kwargs)
    
    def execute_with_capability(self, capability: str, method: str, *args, **kwargs) -> Any:
        """
        Execute a method using the best framework for a capability.
        
        Args:
            capability: Required capability
            method: Method name to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result from the framework method
        """
        best_framework = self.get_best_framework(capability)
        
        if not best_framework:
            raise RuntimeError(f"No available framework for capability: {capability}")
        
        return self.execute_with_framework(best_framework, method, *args, **kwargs)
    
    def register_framework(self, framework_id: str, name: str, framework_type: str,
                         paths: List[str], capabilities: List[str],
                         integration_module: str, requirements: List[str] = None,
                         enabled: bool = True) -> bool:
        """
        Register a new framework.
        
        Args:
            framework_id: Unique framework identifier
            name: Human-readable name
            framework_type: Type of framework (e.g., 'autonomous_agent')
            paths: List of filesystem paths
            capabilities: List of capabilities
            integration_module: Integration module name
            requirements: List of required packages
            enabled: Whether framework is enabled
            
        Returns:
            True if registration was successful
        """
        framework_data = {
            "name": name,
            "type": framework_type,
            "enabled": enabled,
            "paths": paths,
            "primary_path": paths[0] if paths else None,
            "capabilities": capabilities,
            "integration_module": integration_module,
            "requirements": requirements or [],
            "health_check_enabled": True
        }
        
        self.frameworks[framework_id] = framework_data
        self._save_registry()
        
        self.logger.info(f"Registered framework: {framework_id}")
        return True
    
    def unregister_framework(self, framework_id: str) -> bool:
        """
        Unregister a framework.
        
        Args:
            framework_id: Framework to unregister
            
        Returns:
            True if successful
        """
        if framework_id in self.frameworks:
            # Remove from loaded frameworks if present
            self.loaded_frameworks.pop(framework_id, None)
            
            # Remove from registry
            del self.frameworks[framework_id]
            
            # Remove from capability scores
            for capability_scores in self.capability_scores.values():
                capability_scores.pop(framework_id, None)
            
            self._save_registry()
            
            self.logger.info(f"Unregistered framework: {framework_id}")
            return True
        
        return False
    
    def update_capability_score(self, capability: str, framework_id: str, score: float):
        """
        Update the performance score for a framework capability.
        
        Args:
            capability: Capability name
            framework_id: Framework identifier
            score: Performance score (0.0 - 10.0)
        """
        if capability not in self.capability_scores:
            self.capability_scores[capability] = {}
        
        self.capability_scores[capability][framework_id] = score
        self._save_registry()
        
        self.logger.info(f"Updated score for {framework_id}.{capability}: {score}")
    
    def perform_health_check(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health checks on all frameworks.
        
        Returns:
            Dictionary of health check results
        """
        results = {}
        
        for framework_id, framework_data in self.frameworks.items():
            if not framework_data.get("health_check_enabled", False):
                continue
            
            result = {
                "framework_id": framework_id,
                "name": framework_data.get("name", framework_id),
                "available": self._is_framework_available(framework_id),
                "loaded": framework_id in self.loaded_frameworks,
                "enabled": framework_data.get("enabled", False)
            }
            
            # Check requirements
            requirements_met = True
            missing_requirements = []
            
            for requirement in framework_data.get("requirements", []):
                try:
                    importlib.import_module(requirement)
                except ImportError:
                    requirements_met = False
                    missing_requirements.append(requirement)
            
            result["requirements_met"] = requirements_met
            result["missing_requirements"] = missing_requirements
            
            # Overall health
            result["healthy"] = (
                result["available"] and 
                result["enabled"] and 
                result["requirements_met"]
            )
            
            results[framework_id] = result
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get framework manager statistics."""
        total_frameworks = len(self.frameworks)
        enabled_frameworks = sum(1 for f in self.frameworks.values() if f.get("enabled", False))
        loaded_frameworks = len(self.loaded_frameworks)
        available_frameworks = sum(1 for f_id in self.frameworks.keys() if self._is_framework_available(f_id))
        
        # Count by type
        type_counts = {}
        for framework_data in self.frameworks.values():
            framework_type = framework_data.get("type", "unknown")
            type_counts[framework_type] = type_counts.get(framework_type, 0) + 1
        
        # Count capabilities
        all_capabilities = set()
        for framework_data in self.frameworks.values():
            all_capabilities.update(framework_data.get("capabilities", []))
        
        return {
            "total_frameworks": total_frameworks,
            "enabled_frameworks": enabled_frameworks,
            "loaded_frameworks": loaded_frameworks,
            "available_frameworks": available_frameworks,
            "framework_types": type_counts,
            "total_capabilities": len(all_capabilities),
            "capabilities": sorted(list(all_capabilities)),
            "registry_path": str(self.registry_path)
        }


# Global instance
_framework_manager = None

def get_framework_manager() -> FrameworkManager:
    """Get the global framework manager instance."""
    global _framework_manager
    if _framework_manager is None:
        _framework_manager = FrameworkManager()
    return _framework_manager


# Legacy compatibility functions
def get_all_frameworks():
    """Legacy compatibility function."""
    return get_framework_manager().get_available_frameworks()


def get_framework_by_name(name: str):
    """Legacy compatibility function."""
    manager = get_framework_manager()
    if name in manager.loaded_frameworks:
        return manager.loaded_frameworks[name]
    return None


# Export main classes and functions
__all__ = [
    'FrameworkManager',
    'get_framework_manager',
    'get_all_frameworks',
    'get_framework_by_name'
] 