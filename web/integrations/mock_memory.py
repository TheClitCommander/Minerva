"""
Mock Memory System for Minerva

Provides a simplified in-memory implementation of Minerva's memory system
for testing and environments where ChromaDB is not available.
"""

import logging
import time
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockMemorySystem:
    """Simple in-memory implementation of Minerva's memory system."""
    
    def __init__(self):
        """Initialize the mock memory system."""
        self.memories = {}
        self.knowledge_base = []
        logger.info("Initialized Mock Memory System (ChromaDB replacement)")
    
    def store(self, 
             conversation_id: str, 
             user_message: str, 
             ai_response: str, 
             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a memory in the mock system.
        
        Args:
            conversation_id: Unique identifier for the conversation
            user_message: The user's message
            ai_response: The AI's response
            metadata: Additional metadata about the interaction
            
        Returns:
            success: Whether the storage operation was successful
        """
        if conversation_id not in self.memories:
            self.memories[conversation_id] = []
        
        self.memories[conversation_id].append({
            "timestamp": time.time(),
            "user_message": user_message,
            "ai_response": ai_response,
            "metadata": metadata or {}
        })
        
        logger.debug(f"Stored memory for conversation {conversation_id}")
        return True
    
    def retrieve(self, 
                query: str, 
                conversation_id: Optional[str] = None, 
                limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve memories based on a query.
        
        Args:
            query: Query string to search for
            conversation_id: Optional filter for a specific conversation
            limit: Maximum number of results to return
            
        Returns:
            List of matching memories
        """
        results = []
        
        # If conversation_id is provided, only search in that conversation
        conversations = [conversation_id] if conversation_id else self.memories.keys()
        
        for conv_id in conversations:
            if conv_id not in self.memories:
                continue
                
            for memory in self.memories[conv_id]:
                # Simple keyword matching
                if (query.lower() in memory["user_message"].lower() or 
                    query.lower() in memory["ai_response"].lower()):
                    results.append({
                        "conversation_id": conv_id,
                        "user_message": memory["user_message"],
                        "ai_response": memory["ai_response"],
                        "metadata": memory["metadata"],
                        "similarity": 0.8  # Mock similarity score
                    })
                    
                    if len(results) >= limit:
                        break
        
        logger.debug(f"Retrieved {len(results)} memories for query: {query}")
        return results
    
    def add_knowledge(self, 
                    title: str, 
                    content: str, 
                    source: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Add a knowledge entry to the knowledge base.
        
        Args:
            title: Title of the knowledge entry
            content: Content of the knowledge entry
            source: Source of the knowledge
            metadata: Additional metadata
            
        Returns:
            knowledge_id: ID of the added knowledge entry
        """
        knowledge_id = len(self.knowledge_base)
        
        self.knowledge_base.append({
            "id": knowledge_id,
            "title": title,
            "content": content,
            "source": source,
            "metadata": metadata or {},
            "timestamp": time.time()
        })
        
        logger.debug(f"Added knowledge entry {knowledge_id}: {title}")
        return knowledge_id
    
    def retrieve_knowledge(self, 
                         query: str, 
                         limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve knowledge entries based on a query.
        
        Args:
            query: Query string to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching knowledge entries
        """
        results = []
        
        for entry in self.knowledge_base:
            # Simple keyword matching
            if (query.lower() in entry["title"].lower() or 
                query.lower() in entry["content"].lower()):
                results.append({
                    "id": entry["id"],
                    "title": entry["title"],
                    "content": entry["content"],
                    "source": entry["source"],
                    "metadata": entry["metadata"],
                    "similarity": 0.8  # Mock similarity score
                })
                
                if len(results) >= limit:
                    break
        
        logger.debug(f"Retrieved {len(results)} knowledge entries for query: {query}")
        return results

# Initialize mock memory system
mock_memory_system = MockMemorySystem()

# Exported functions that match the real memory system's interface
def store_memory(conversation_id: str, 
                user_message: str, 
                ai_response: str, 
                metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Store a memory in the mock system."""
    return mock_memory_system.store(
        conversation_id=conversation_id,
        user_message=user_message,
        ai_response=ai_response,
        metadata=metadata
    )

def retrieve_memory(query: str, 
                   conversation_id: Optional[str] = None, 
                   limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieve memories based on a query."""
    return mock_memory_system.retrieve(
        query=query,
        conversation_id=conversation_id,
        limit=limit
    )

def add_knowledge(title: str, 
                 content: str, 
                 source: str, 
                 metadata: Optional[Dict[str, Any]] = None) -> int:
    """Add a knowledge entry to the knowledge base."""
    return mock_memory_system.add_knowledge(
        title=title,
        content=content,
        source=source,
        metadata=metadata
    )

def retrieve_knowledge(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieve knowledge entries based on a query."""
    return mock_memory_system.retrieve_knowledge(
        query=query,
        limit=limit
    )

# For compatibility with the real memory system
memory_system = mock_memory_system
enhance_with_memory = lambda query, conversation_id=None: (query, [])
