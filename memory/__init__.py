#!/usr/bin/env python3
"""
Minerva Memory System

Unified memory management system for Minerva AI Assistant.
Provides persistent memory, conversation tracking, and priority-based retrieval.
"""

# Import new unified system
from .memory_models import MemoryItem, ConversationMemory, ConversationMessage, MemoryContext
from .priority_system import MemoryPriority
from .unified_memory_manager import UnifiedMemoryManager

# Legacy compatibility - import from old managers if needed
try:
    from .memory_manager import MemoryManager as LegacyMemoryManager
except ImportError:
    LegacyMemoryManager = None

try:
    from .enhanced_memory_manager import EnhancedMemoryManager
except ImportError:
    EnhancedMemoryManager = None

# Create default memory manager instance
memory_manager = None

def get_memory_manager(storage_dir=None, config=None):
    """
    Get the default memory manager instance.
    
    Args:
        storage_dir: Storage directory (optional)
        config: Configuration dictionary (optional)
        
    Returns:
        UnifiedMemoryManager instance
    """
    global memory_manager
    if memory_manager is None:
        memory_manager = UnifiedMemoryManager(storage_dir, config)
    return memory_manager

# Main interface exports
__all__ = [
    # Models
    'MemoryItem',
    'ConversationMemory', 
    'ConversationMessage',
    'MemoryContext',
    
    # Systems
    'MemoryPriority',
    'UnifiedMemoryManager',
    
    # Main interface
    'get_memory_manager',
    
    # Legacy compatibility
    'LegacyMemoryManager',
    'EnhancedMemoryManager'
]

# Version info
__version__ = '2.0.0'
