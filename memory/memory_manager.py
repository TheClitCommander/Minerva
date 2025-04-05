"""
Memory Manager for Minerva

This module provides a persistent memory system for Minerva,
allowing it to remember information across sessions and conversations.
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from loguru import logger
from pydantic import BaseModel, Field, validator

class MemoryItem(BaseModel):
    """Model for a single memory item."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    source: str
    importance: int = 1  # 1-10 scale, higher is more important
    category: str
    tags: List[str] = []
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    access_count: int = 0
    metadata: Dict[str, Any] = {}
    
    @validator('importance')
    def importance_range(cls, v):
        """Validate importance is in range 1-10."""
        if not 1 <= v <= 10:
            raise ValueError('Importance must be between 1 and 10')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with date formatting."""
        data = self.dict()
        # Convert datetime objects to ISO format strings
        for key in ['expires_at', 'created_at', 'last_accessed']:
            if data[key]:
                data[key] = data[key].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """Create a MemoryItem from a dictionary."""
        # Convert ISO format strings back to datetime objects
        for key in ['expires_at', 'created_at', 'last_accessed']:
            if data.get(key) and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)

class ConversationMemory(BaseModel):
    """Model for conversation history."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Dict[str, Any]] = []
    summary: Optional[str] = None
    context: Dict[str, Any] = {}
    start_time: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation."""
        if metadata is None:
            metadata = {}
        
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        self.messages.append(message)
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with date formatting."""
        data = self.dict()
        # Convert datetime objects to ISO format strings
        for key in ['start_time', 'last_updated']:
            if data[key]:
                data[key] = data[key].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMemory':
        """Create a ConversationMemory from a dictionary."""
        # Convert ISO format strings back to datetime objects
        for key in ['start_time', 'last_updated']:
            if data.get(key) and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)

class MemoryManager:
    """Manager for Minerva's memory system."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the memory manager.
        
        Args:
            storage_dir: Directory to store memory files. If None, uses default location.
        """
        # Set up storage directory
        if storage_dir is None:
            home_dir = str(Path.home())
            self.storage_dir = os.path.join(home_dir, ".minerva", "memory")
        else:
            self.storage_dir = storage_dir
        
        # Create directories if they don't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "items"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "conversations"), exist_ok=True)
        
        # Initialize memory caches
        self.memory_items: Dict[str, MemoryItem] = {}
        self.conversations: Dict[str, ConversationMemory] = {}
        
        # Load existing memories
        self.load_all_memories()
        
        logger.info(f"Memory system initialized with storage at: {self.storage_dir}")
        logger.info(f"Loaded {len(self.memory_items)} memory items and {len(self.conversations)} conversations")
    
    def load_all_memories(self):
        """Load all existing memories from storage."""
        # Load memory items
        items_dir = os.path.join(self.storage_dir, "items")
        for filename in os.listdir(items_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(items_dir, filename), 'r') as f:
                        data = json.load(f)
                        memory_item = MemoryItem.from_dict(data)
                        self.memory_items[memory_item.id] = memory_item
                except Exception as e:
                    logger.error(f"Error loading memory item {filename}: {str(e)}")
        
        # Load conversations
        conv_dir = os.path.join(self.storage_dir, "conversations")
        for filename in os.listdir(conv_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(conv_dir, filename), 'r') as f:
                        data = json.load(f)
                        conversation = ConversationMemory.from_dict(data)
                        self.conversations[conversation.id] = conversation
                except Exception as e:
                    logger.error(f"Error loading conversation {filename}: {str(e)}")
    
    def save_memory_item(self, item: MemoryItem):
        """Save a memory item to storage."""
        filename = os.path.join(self.storage_dir, "items", f"{item.id}.json")
        with open(filename, 'w') as f:
            json.dump(item.to_dict(), f, indent=2)
    
    def save_conversation(self, conversation: ConversationMemory):
        """Save a conversation to storage."""
        filename = os.path.join(self.storage_dir, "conversations", f"{conversation.id}.json")
        with open(filename, 'w') as f:
            json.dump(conversation.to_dict(), f, indent=2)
    
    def add_memory(self, content: str, source: str, category: str, 
                  importance: int = 1, tags: List[str] = None, 
                  expires_at: Optional[datetime] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """
        Add a new memory item.
        
        Args:
            content: The content of the memory
            source: Where the memory came from (e.g., 'user', 'system', 'inference')
            category: Category of the memory (e.g., 'preference', 'fact', 'instruction')
            importance: Importance score (1-10)
            tags: List of tags for search/retrieval
            expires_at: When the memory should expire (or None for never)
            metadata: Additional metadata
            
        Returns:
            The created MemoryItem
        """
        if tags is None:
            tags = []
            
        if metadata is None:
            metadata = {}
            
        # Create new memory item
        memory_item = MemoryItem(
            content=content,
            source=source,
            category=category,
            importance=importance,
            tags=tags,
            expires_at=expires_at,
            metadata=metadata
        )
        
        # Add to cache
        self.memory_items[memory_item.id] = memory_item
        
        # Save to disk
        self.save_memory_item(memory_item)
        
        logger.info(f"Added new memory: {memory_item.id} ({category})")
        return memory_item
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID.
        
        Args:
            memory_id: ID of the memory item
            
        Returns:
            The memory item or None if not found
        """
        if memory_id not in self.memory_items:
            return None
            
        memory_item = self.memory_items[memory_id]
        
        # Update access information
        memory_item.last_accessed = datetime.now()
        memory_item.access_count += 1
        
        # Save updated item
        self.save_memory_item(memory_item)
        
        return memory_item
    
    def update_memory(self, memory_id: str, **kwargs) -> Optional[MemoryItem]:
        """
        Update a memory item.
        
        Args:
            memory_id: ID of the memory to update
            **kwargs: Fields to update
            
        Returns:
            Updated memory item or None if not found
        """
        if memory_id not in self.memory_items:
            return None
            
        memory_item = self.memory_items[memory_id]
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(memory_item, key):
                setattr(memory_item, key, value)
        
        # Save updated item
        self.save_memory_item(memory_item)
        
        logger.info(f"Updated memory: {memory_id}")
        return memory_item
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            True if deleted, False if not found
        """
        if memory_id not in self.memory_items:
            return False
            
        # Remove from cache
        del self.memory_items[memory_id]
        
        # Remove from disk
        filename = os.path.join(self.storage_dir, "items", f"{memory_id}.json")
        if os.path.exists(filename):
            os.remove(filename)
        
        logger.info(f"Deleted memory: {memory_id}")
        return True
    
    def search_memories(self, query: str = None, category: str = None, 
                      tags: List[str] = None, source: str = None,
                      min_importance: int = None, max_results: int = 10,
                      include_expired: bool = False) -> List[MemoryItem]:
        """
        Search for memory items based on criteria.
        
        Args:
            query: Text to search for in content
            category: Category to filter by
            tags: Tags to filter by
            source: Source to filter by
            min_importance: Minimum importance score
            max_results: Maximum number of results
            include_expired: Whether to include expired memories
            
        Returns:
            List of matching memory items
        """
        results = []
        now = datetime.now()
        
        for item in self.memory_items.values():
            # Skip expired items unless explicitly included
            if not include_expired and item.expires_at and item.expires_at < now:
                continue
                
            # Apply filters
            if category and item.category != category:
                continue
                
            if source and item.source != source:
                continue
                
            if min_importance and item.importance < min_importance:
                continue
                
            if tags:
                if not all(tag in item.tags for tag in tags):
                    continue
            
            if query:
                if query.lower() not in item.content.lower():
                    continue
            
            # Add to results
            results.append(item)
            
            # Update access information
            item.last_accessed = now
            item.access_count += 1
            self.save_memory_item(item)
            
            # Limit results
            if len(results) >= max_results:
                break
        
        # Sort by importance and last accessed
        results.sort(key=lambda x: (x.importance, x.last_accessed), reverse=True)
        
        return results
    
    def create_conversation(self, user_id: str) -> ConversationMemory:
        """
        Create a new conversation.
        
        Args:
            user_id: ID of the user
            
        Returns:
            New conversation object
        """
        conversation = ConversationMemory(user_id=user_id)
        
        # Add to cache
        self.conversations[conversation.id] = conversation
        
        # Save to disk
        self.save_conversation(conversation)
        
        logger.info(f"Created new conversation: {conversation.id} for user {user_id}")
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationMemory]:
        """
        Retrieve a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            The conversation or None if not found
        """
        if conversation_id not in self.conversations:
            return None
            
        return self.conversations[conversation_id]
    
    def add_message_to_conversation(self, conversation_id: str, role: str, 
                                  content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            role: Role of the message sender (e.g., 'user', 'assistant')
            content: Content of the message
            metadata: Additional metadata
            
        Returns:
            True if added, False if conversation not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
            
        # Add message
        conversation.add_message(role, content, metadata)
        
        # Save updated conversation
        self.save_conversation(conversation)
        
        return True
    
    def get_recent_conversations(self, user_id: Optional[str] = None, 
                               max_results: int = 5) -> List[ConversationMemory]:
        """
        Get recent conversations.
        
        Args:
            user_id: Filter by user ID
            max_results: Maximum number of results
            
        Returns:
            List of recent conversations
        """
        conversations = list(self.conversations.values())
        
        # Filter by user ID if provided
        if user_id:
            conversations = [c for c in conversations if c.user_id == user_id]
        
        # Sort by last updated
        conversations.sort(key=lambda x: x.last_updated, reverse=True)
        
        # Limit results
        return conversations[:max_results]
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if deleted, False if not found
        """
        if conversation_id not in self.conversations:
            return False
            
        # Remove from cache
        del self.conversations[conversation_id]
        
        # Remove from disk
        filename = os.path.join(self.storage_dir, "conversations", f"{conversation_id}.json")
        if os.path.exists(filename):
            os.remove(filename)
        
        logger.info(f"Deleted conversation: {conversation_id}")
        return True
    
    def extract_memories_from_conversation(self, conversation_id: str) -> List[MemoryItem]:
        """
        Extract important information from a conversation and create memory items.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of created memory items
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
            
        # This would typically use an LLM to analyze the conversation
        # and extract important information
        # For now, we'll use a simple rule-based approach
        
        created_memories = []
        user_messages = [m for m in conversation.messages if m['role'] == 'user']
        
        # Look for preferences in user messages
        for message in user_messages:
            content = message['content'].lower()
            
            # Check for preference indicators
            preference_indicators = ["i prefer", "i like", "i want", "i need", "i don't like", "i hate"]
            for indicator in preference_indicators:
                if indicator in content:
                    # Extract the preference
                    preference = content.split(indicator, 1)[1].strip()
                    
                    # Create a memory item
                    memory_item = self.add_memory(
                        content=f"User preference: {indicator} {preference}",
                        source="conversation",
                        category="preference",
                        importance=5,
                        tags=["preference", "user_input"],
                        metadata={"conversation_id": conversation_id, "message_id": message['id']}
                    )
                    
                    created_memories.append(memory_item)
        
        return created_memories
    
    def get_relevant_memories(self, context: str, max_results: int = 5) -> List[MemoryItem]:
        """
        Get memories relevant to the given context.
        
        Args:
            context: Current context to find relevant memories for
            max_results: Maximum number of results
            
        Returns:
            List of relevant memory items
        """
        # This would ideally use vector embeddings and semantic search
        # For now, we'll use simple keyword matching
        
        # Extract potential keywords from context
        lower_context = context.lower()
        
        # Score each memory based on relevance to context
        scored_memories = []
        for item in self.memory_items.values():
            score = 0
            
            # Check for direct content matches
            if item.content.lower() in lower_context:
                score += 5
            
            # Check for tag matches
            for tag in item.tags:
                if tag.lower() in lower_context:
                    score += 2
            
            # Check for category match
            if item.category.lower() in lower_context:
                score += 3
            
            # Factor in importance
            score *= item.importance
            
            # Skip memories with no relevance
            if score > 0:
                scored_memories.append((item, score))
        
        # Sort by score
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # Extract memory items
        relevant_memories = [item for item, score in scored_memories[:max_results]]
        
        # Update access information for retrieved items
        now = datetime.now()
        for item in relevant_memories:
            item.last_accessed = now
            item.access_count += 1
            self.save_memory_item(item)
        
        return relevant_memories
