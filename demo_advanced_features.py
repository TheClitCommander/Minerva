#!/usr/bin/env python3
"""
Minerva Demo - Advanced Features

This script demonstrates the advanced features of Minerva,
including the new framework integrations and memory system.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Set up graceful imports
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)

# Import Minerva components
try:
    from minerva_main import MinervaAI
    from memory.memory_manager import MemoryManager
except ImportError as e:
    logger.error(f"Failed to import Minerva components: {str(e)}")
    logger.error("Make sure you have installed the required dependencies.")
    logger.error("Run: pip install -r requirements.txt")
    sys.exit(1)

def print_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)

def demonstrate_framework_integrations(minerva):
    """Demonstrate the framework integrations."""
    print_header("FRAMEWORK INTEGRATIONS")
    
    # Get available AI frameworks
    framework_manager = minerva.framework_manager
    
    # List all available frameworks
    print("\nAVAILABLE FRAMEWORKS:")
    frameworks = framework_manager.get_all_frameworks()
    for name in frameworks:
        print(f" - {name}")
    
    # List capabilities
    print("\nAVAILABLE CAPABILITIES:")
    capabilities = framework_manager.get_all_capabilities()
    for capability, frameworks in capabilities.items():
        frameworks_str = ", ".join(frameworks)
        print(f" - {capability} (provided by: {frameworks_str})")
    
    # Framework health checks
    print("\nFRAMEWORK HEALTH CHECKS:")
    health_checks = framework_manager.perform_health_check()
    for framework_name, status in health_checks.items():
        status_str = status.get('status', 'unknown')
        print(f" - {framework_name}: {status_str}")

def demonstrate_memory_system(minerva):
    """Demonstrate the memory system."""
    print_header("MEMORY SYSTEM")
    
    memory_manager = minerva.get_memory_manager()
    
    # Add some sample memories
    print("\nADDING SAMPLE MEMORIES:")
    
    # User preference
    memory1 = minerva.add_memory(
        content="User prefers dark mode in all applications",
        category="preference",
        tags=["ui", "dark_mode", "preference"],
        importance=7,
        source="user"
    )
    print(f" - Added memory: {memory1['id']}")
    
    # Fact
    memory2 = minerva.add_memory(
        content="User is located in New York, USA",
        category="fact",
        tags=["location", "user_info"],
        importance=5,
        source="inference"
    )
    print(f" - Added memory: {memory2['id']}")
    
    # Instruction
    memory3 = minerva.add_memory(
        content="Always respond with concise answers unless user requests detail",
        category="instruction",
        tags=["style", "communication"],
        importance=8,
        source="user"
    )
    print(f" - Added memory: {memory3['id']}")
    
    # Search for memories
    print("\nSEARCHING MEMORIES:")
    
    # Search by category
    print("\nPreferences:")
    preferences = minerva.search_memories(category="preference")
    for memory in preferences['memories']:
        print(f" - {memory['content']} (importance: {memory['importance']})")
    
    # Search by tag
    print("\nUI-related memories:")
    ui_memories = minerva.search_memories(tags=["ui"])
    for memory in ui_memories['memories']:
        print(f" - {memory['content']} (tags: {', '.join(memory['tags'])})")
    
    # Search by content
    print("\nMemories about user:")
    user_memories = minerva.search_memories(query="user")
    for memory in user_memories['memories']:
        print(f" - {memory['content']}")

def demonstrate_conversation(minerva):
    """Demonstrate conversation memory."""
    print_header("CONVERSATION MEMORY")
    
    # Start a new conversation
    conv_result = minerva.start_conversation(user_id="demo_user")
    conversation_id = conv_result['conversation_id']
    print(f"\nStarted conversation: {conversation_id}")
    
    # Add messages to the conversation
    print("\nAdding messages to conversation:")
    
    # User message
    minerva.add_message(
        conversation_id=conversation_id,
        role="user",
        content="Hello, I need help with a Python project."
    )
    print(" - Added user message")
    
    # Assistant message
    minerva.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content="I'd be happy to help with your Python project. What specific aspects are you working on?"
    )
    print(" - Added assistant message")
    
    # User message with preference
    minerva.add_message(
        conversation_id=conversation_id,
        role="user",
        content="I prefer to use object-oriented programming for structure."
    )
    print(" - Added user message with preference")
    
    # Extract memories from conversation
    print("\nExtracting memories from conversation:")
    memories = minerva.memory_manager.extract_memories_from_conversation(conversation_id)
    for memory in memories:
        print(f" - Extracted: {memory.content} (category: {memory.category})")

def main():
    """Main function to run the demonstration."""
    try:
        # Initialize Minerva
        print_header("INITIALIZING MINERVA")
        minerva = MinervaAI()
        print("Minerva initialized successfully")
        
        # Demonstrate framework integrations
        demonstrate_framework_integrations(minerva)
        
        # Demonstrate memory system
        demonstrate_memory_system(minerva)
        
        # Demonstrate conversation memory
        demonstrate_conversation(minerva)
        
        print_header("DEMONSTRATION COMPLETE")
        print("\nMinerva advanced features are ready to use!")
        
    except Exception as e:
        logger.error(f"Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
