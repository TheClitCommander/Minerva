#!/usr/bin/env python3
"""
Minerva Framework System

Consolidated framework management for AI integrations.
Provides unified interface for discovering, loading, and executing AI frameworks.
"""

from .framework_manager import (
    FrameworkManager,
    get_framework_manager,
    get_all_frameworks,
    get_framework_by_name
)

# Create default framework manager instance
framework_manager = None

def get_default_manager():
    """Get the default framework manager instance."""
    global framework_manager
    if framework_manager is None:
        framework_manager = get_framework_manager()
    return framework_manager

# Convenience functions for common operations
def load_framework(framework_id: str) -> bool:
    """Load a framework by ID."""
    return get_default_manager().load_framework(framework_id)

def execute_with_capability(capability: str, method: str, *args, **kwargs):
    """Execute a method using the best framework for a capability."""
    return get_default_manager().execute_with_capability(capability, method, *args, **kwargs)

def get_frameworks_by_capability(capability: str):
    """Get frameworks that support a specific capability."""
    return get_default_manager().get_frameworks_by_capability(capability)

def get_available_frameworks():
    """Get list of all available frameworks."""
    return get_default_manager().get_available_frameworks()

def perform_health_check():
    """Perform health checks on all frameworks."""
    return get_default_manager().perform_health_check()

# Export main interface
__all__ = [
    # Main classes
    'FrameworkManager',
    
    # Instance getters
    'get_framework_manager',
    'get_default_manager',
    
    # Convenience functions
    'load_framework',
    'execute_with_capability',
    'get_frameworks_by_capability', 
    'get_available_frameworks',
    'perform_health_check',
    
    # Legacy compatibility
    'get_all_frameworks',
    'get_framework_by_name'
]

# Version info
__version__ = '2.0.0' 