"""
Test module for Enhanced Memory Manager

This script tests the functionality of the EnhancedMemoryManager class,
including adding, retrieving, updating, and deleting memories.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the EnhancedMemoryManager
from memory.enhanced_memory_manager import EnhancedMemoryManager


def test_enhanced_memory_manager():
    """
    Test the EnhancedMemoryManager functionality.
    """
    print("Testing EnhancedMemoryManager...")
    
    # Use a test database file
    test_db_path = "test_memories.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    memory_manager = EnhancedMemoryManager(db_path=test_db_path)
    
    # Test adding memories
    print("\nAdding test memories...")
    memory1 = memory_manager.add_memory(
        content="I enjoy eating sushi, especially salmon nigiri",
        source="user",
        category="preference",
        importance=8,
        tags=["food", "preference", "sushi"],
        metadata={"confidence": 0.95}
    )
    
    memory2 = memory_manager.add_memory(
        content="My favorite color is blue",
        source="user",
        category="preference",
        importance=5,
        tags=["color", "preference"],
        metadata={"confidence": 0.9}
    )
    
    memory3 = memory_manager.add_memory(
        content="I grew up in Boston",
        source="user",
        category="fact",
        importance=7,
        tags=["location", "background"],
        metadata={"confidence": 0.85}
    )
    
    # Test adding memory with context
    memory_with_context = memory_manager.add_memory_with_context(
        content="I prefer to receive detailed technical explanations",
        source="user",
        category="instruction",
        context="conversation_about_ai",
        importance=9,
        tags=["preference", "communication_style"],
        metadata={"confidence": 0.98}
    )
    
    # Test deduplication - should update existing memory instead of creating a new one
    duplicate = memory_manager.add_memory(
        content="I enjoy eating sushi, especially salmon nigiri",
        source="user",
        category="preference"
    )
    
    print(f"Added memories. Original ID: {memory1['id']}, Duplicate check ID: {duplicate['id']}")
    print(f"Deduplication working: {memory1['id'] == duplicate['id']}")
    
    # Test memory retrieval by ID
    print("\nTesting memory retrieval by ID...")
    retrieved = memory_manager.get_memory_by_id(memory2['id'])
    print(f"Retrieved memory: {retrieved['content']}")
    
    # Test memory retrieval by query
    print("\nTesting memory retrieval by query...")
    memories = memory_manager.get_memories(query="food")
    print(f"Found {len(memories)} memories matching 'food'")
    for memory in memories:
        print(f" - {memory['content']} (relevance: {memory.get('relevance', 'N/A')})")
    
    # Test memory by category
    print("\nTesting category filtering...")
    preferences = memory_manager.get_memories(category="preference")
    print(f"Found {len(preferences)} preference memories")
    for memory in preferences:
        print(f" - {memory['content']}")
    
    # Test tag filtering
    print("\nTesting tag filtering...")
    color_memories = memory_manager.get_memories(tags=["color"])
    print(f"Found {len(color_memories)} memories with tag 'color'")
    for memory in color_memories:
        print(f" - {memory['content']}")
    
    # Test context filtering
    print("\nTesting context filtering...")
    context_memories = memory_manager.get_memories(context="conversation_about_ai")
    print(f"Found {len(context_memories)} memories with context 'conversation_about_ai'")
    for memory in context_memories:
        print(f" - {memory['content']}")
    
    # Test updating memories
    print("\nTesting memory updates...")
    updated = memory_manager.update_memory(
        memory_id=memory2['id'],
        content="My favorite color is navy blue",
        importance=6
    )
    
    print(f"Updated memory: {updated['content']} (importance: {updated['importance']})")
    
    # Test memory deletion
    print("\nTesting memory deletion...")
    deleted = memory_manager.delete_memory(memory3['id'])
    print(f"Deleted memory: {deleted}")
    
    # Test bulk deletion by query
    print("\nTesting bulk memory deletion...")
    memory_manager.add_memory(
        content="Test memory for deletion 1",
        source="system",
        category="test",
        tags=["test", "deletion"]
    )
    memory_manager.add_memory(
        content="Test memory for deletion 2",
        source="system",
        category="test",
        tags=["test", "deletion"]
    )
    
    deleted_count = memory_manager.delete_memories_by_query(
        query="Test memory for deletion",
        category="test"
    )
    print(f"Bulk deleted {deleted_count} test memories")
    
    # Verify all memories
    all_memories = memory_manager.get_memories()
    print(f"\nRemaining memories: {len(all_memories)}")
    for memory in all_memories:
        print(f" - {memory['content']}")
    
    print("\nEnhancedMemoryManager tests completed!")


if __name__ == "__main__":
    test_enhanced_memory_manager()
