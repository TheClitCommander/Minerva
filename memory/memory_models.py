#!/usr/bin/env python3
"""
Memory Models for Minerva

Clean data models for memory items and conversations.
Extracted and simplified from various memory managers.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator


class MemoryItem(BaseModel):
    """Model for a single memory item."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    source: str  # 'user', 'system', 'inference', etc.
    importance: int = 1  # 1-10 scale, higher is more important
    category: str  # 'preference', 'fact', 'instruction', 'context', etc.
    tags: List[str] = []
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    access_count: int = 0
    metadata: Dict[str, Any] = {}
    contexts: Dict[str, float] = {}  # context_reference -> relevance_score
    
    @validator('importance')
    def importance_range(cls, v):
        """Validate importance is in range 1-10."""
        if not 1 <= v <= 10:
            raise ValueError('Importance must be between 1 and 10')
        return v
    
    @property
    def is_expired(self) -> bool:
        """Check if the memory has expired."""
        return self.expires_at is not None and self.expires_at < datetime.now()
    
    @property
    def age_days(self) -> int:
        """Get age of memory in days."""
        return (datetime.now() - self.created_at).days
    
    @property
    def days_since_last_access(self) -> int:
        """Get days since last access."""
        return (datetime.now() - self.last_accessed).days
    
    def update_access(self):
        """Update access timestamp and count."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def add_context(self, context_reference: str, score: float = 1.0):
        """Add a context reference with relevance score."""
        self.contexts[context_reference] = score
    
    def add_tag(self, tag: str):
        """Add a tag if not already present."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag if present."""
        if tag in self.tags:
            self.tags.remove(tag)
    
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
                try:
                    data[key] = datetime.fromisoformat(data[key])
                except ValueError:
                    # Handle legacy formats
                    data[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
        return cls(**data)


class ConversationMessage(BaseModel):
    """Model for a single conversation message."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with date formatting."""
        data = self.dict()
        data['timestamp'] = data['timestamp'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create from dictionary."""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            try:
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        return cls(**data)


class ConversationMemory(BaseModel):
    """Model for conversation history."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ConversationMessage] = []
    summary: Optional[str] = None
    context: Dict[str, Any] = {}
    start_time: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    @property
    def message_count(self) -> int:
        """Get total number of messages."""
        return len(self.messages)
    
    @property
    def user_message_count(self) -> int:
        """Get number of user messages."""
        return len([m for m in self.messages if m.role == "user"])
    
    @property
    def assistant_message_count(self) -> int:
        """Get number of assistant messages."""
        return len([m for m in self.messages if m.role == "assistant"])
    
    @property
    def duration_minutes(self) -> float:
        """Get conversation duration in minutes."""
        return (self.last_updated - self.start_time).total_seconds() / 60
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation."""
        if metadata is None:
            metadata = {}
        
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata
        )
        
        self.messages.append(message)
        self.last_updated = datetime.now()
    
    def get_messages_by_role(self, role: str) -> List[ConversationMessage]:
        """Get all messages with a specific role."""
        return [m for m in self.messages if m.role == role]
    
    def get_recent_messages(self, count: int = 5) -> List[ConversationMessage]:
        """Get the most recent messages."""
        return self.messages[-count:] if count < len(self.messages) else self.messages
    
    def extract_keywords(self) -> List[str]:
        """Extract keywords from conversation content (simple implementation)."""
        keywords = set()
        
        # Common stop words to ignore
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'this', 'that', 'these', 'those', 'what', 'where', 'when', 'why', 'how'
        }
        
        for message in self.messages:
            if message.role == "user":
                # Simple keyword extraction from user messages
                words = message.content.lower().split()
                for word in words:
                    # Clean word and check if significant
                    clean_word = ''.join(c for c in word if c.isalnum())
                    if len(clean_word) > 3 and clean_word not in stop_words:
                        keywords.add(clean_word)
        
        return list(keywords)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with date formatting."""
        data = self.dict()
        # Convert datetime objects to ISO format strings
        for key in ['start_time', 'last_updated']:
            if data[key]:
                data[key] = data[key].isoformat()
        
        # Convert messages to dictionaries
        data['messages'] = [msg.to_dict() for msg in self.messages]
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMemory':
        """Create a ConversationMemory from a dictionary."""
        # Convert ISO format strings back to datetime objects
        for key in ['start_time', 'last_updated']:
            if data.get(key) and isinstance(data[key], str):
                try:
                    data[key] = datetime.fromisoformat(data[key])
                except ValueError:
                    data[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
        
        # Convert messages from dictionaries
        if 'messages' in data:
            messages = []
            for msg_data in data['messages']:
                if isinstance(msg_data, dict):
                    try:
                        message = ConversationMessage.from_dict(msg_data)
                        messages.append(message)
                    except Exception:
                        # Handle legacy message format
                        message = ConversationMessage(
                            id=msg_data.get('id', str(uuid.uuid4())),
                            role=msg_data.get('role', 'user'),
                            content=msg_data.get('content', ''),
                            metadata=msg_data.get('metadata', {})
                        )
                        messages.append(message)
            data['messages'] = messages
        
        return cls(**data)


class MemoryContext(BaseModel):
    """Model for memory context tracking."""
    
    reference: str  # Context identifier
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    relevance_scores: Dict[str, float] = {}  # memory_id -> score
    metadata: Dict[str, Any] = {}
    
    def add_memory_relevance(self, memory_id: str, score: float):
        """Add relevance score for a memory."""
        self.relevance_scores[memory_id] = max(0.0, min(1.0, score))
    
    def get_relevant_memories(self, min_score: float = 0.1) -> List[str]:
        """Get memory IDs with relevance above threshold."""
        return [
            memory_id for memory_id, score in self.relevance_scores.items()
            if score >= min_score
        ]


# Export all models
__all__ = [
    'MemoryItem',
    'ConversationMessage', 
    'ConversationMemory',
    'MemoryContext'
] 