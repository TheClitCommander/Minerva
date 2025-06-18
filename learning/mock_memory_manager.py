"""
Mock Memory Manager for Testing

A simplified implementation of the memory manager for testing purposes,
providing the same interface as the real EnhancedMemoryManager but without
requiring external dependencies or database access.
"""

import os
import uuid
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockMemoryManager:
    """
    Mock implementation of the EnhancedMemoryManager for testing.
    
    This provides the same interface as the real memory manager but stores
    memories in-memory rather than in a database.
    """
    
    def __init__(self):
        """Initialize the mock memory manager with an in-memory store."""
        self.memories = {}
        logger.info("MockMemoryManager initialized")
    
    def add_memory(self, content: str, source: str, category: str, 
                  importance: int = 1, tags: List[str] = None, 
                  context: str = None,
                  expires_at: Optional[datetime] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a new memory item.
        
        Args:
            content: The content of the memory
            source: Where the memory came from (e.g., 'user', 'system', 'inference')
            category: Category of the memory (e.g., 'preference', 'fact', 'instruction')
            importance: Importance score (1-10)
            tags: List of tags for search/retrieval
            context: Optional context reference for context-sensitive memories
            expires_at: When the memory should expire (or None for never)
            metadata: Additional metadata as key-value pairs
            
        Returns:
            The created memory item as a dictionary
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Create the memory item
        memory = {
            'id': memory_id,
            'content': content,
            'source': source,
            'category': category,
            'importance': importance,
            'tags': tags or [],
            'context': context,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat() if expires_at else None,
            'metadata': metadata or {},
            'access_count': 0
        }
        
        # Store the memory
        self.memories[memory_id] = memory
        
        logger.info(f"Added memory: {memory_id[:8]}... - {content[:30]}...")
        return memory
    
    def update_memory(self, memory_id: str, content: str = None, category: str = None, 
                     importance: int = None, tags: List[str] = None, 
                     expires_at: Optional[datetime] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing memory item.
        
        Args:
            memory_id: ID of the memory to update
            content: New content for the memory (or None to leave unchanged)
            category: New category (or None to leave unchanged)
            importance: New importance score (or None to leave unchanged)
            tags: New tags (or None to leave unchanged)
            expires_at: New expiration date (or None to leave unchanged)
            metadata: New metadata (or None to leave unchanged)
            
        Returns:
            Updated memory item or None if not found
        """
        if memory_id not in self.memories:
            return None
            
        memory = self.memories[memory_id]
        
        # Update fields if provided
        if content is not None:
            memory['content'] = content
        if category is not None:
            memory['category'] = category
        if importance is not None:
            memory['importance'] = importance
        if tags is not None:
            memory['tags'] = tags
        if expires_at is not None:
            memory['expires_at'] = expires_at.isoformat()
        if metadata is not None:
            # Merge with existing metadata
            memory['metadata'].update(metadata)
        
        # Update modified timestamp
        memory['updated_at'] = datetime.now().isoformat()
        
        logger.info(f"Updated memory: {memory_id[:8]}...")
        return memory
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            True if deleted, False if not found
        """
        if memory_id not in self.memories:
            return False
            
        del self.memories[memory_id]
        logger.info(f"Deleted memory: {memory_id[:8]}...")
        return True
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory item by ID.
        
        Args:
            memory_id: ID of the memory item
            
        Returns:
            The memory item as a dictionary or None if not found
        """
        if memory_id not in self.memories:
            return None
            
        memory = self.memories[memory_id]
        
        # Increment access count
        memory['access_count'] += 1
        
        return memory
    
    def get_memories(self, query: str = None, category: str = None, 
                    tags: List[str] = None, source: str = None,
                    context: str = None,
                    min_importance: int = None, max_results: int = 10,
                    include_expired: bool = False) -> List[Dict[str, Any]]:
        """
        Search for memory items based on criteria.
        
        Args:
            query: Text to search for in content
            category: Category to filter by
            tags: Tags to filter by
            source: Source to filter by
            context: Context reference to filter by
            min_importance: Minimum importance score
            max_results: Maximum number of results
            include_expired: Whether to include expired memories
            
        Returns:
            List of matching memory items
        """
        results = []
        now = datetime.now().isoformat()
        
        for memory in self.memories.values():
            # Check expiration
            if not include_expired and memory.get('expires_at') and memory['expires_at'] < now:
                continue
                
            # Apply filters
            if query and query.lower() not in memory['content'].lower():
                continue
            if category and memory['category'] != category:
                continue
            if tags and not all(tag in memory['tags'] for tag in tags):
                continue
            if source and memory['source'] != source:
                continue
            if context and memory.get('context') != context:
                continue
            if min_importance and memory['importance'] < min_importance:
                continue
                
            results.append(memory)
            
        # Sort by importance and limit results
        results.sort(key=lambda x: x['importance'], reverse=True)
        return results[:max_results]
    
    def get_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all memories in the system.
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of memory items
        """
        # Convert memories to list and sort by creation time (newest first)
        memories = list(self.memories.values())
        memories.sort(key=lambda x: x['created_at'], reverse=True)
        
        return memories[:limit]

# Create a singleton instance
mock_memory_manager = MockMemoryManager()
