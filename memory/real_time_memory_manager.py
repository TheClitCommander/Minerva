"""
Real-Time Memory Manager

This module enhances Minerva's memory system with real-time adaptation capabilities,
layered memory (short-term vs. long-term), and efficient context persistence.
"""

import os
import sys
import json
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix import paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from memory.memory_manager import MemoryManager, MemoryItem, ConversationMemory

class MemoryLayerConfig:
    """Configuration for memory layers with retention and priority settings."""
    
    def __init__(self, 
                 retention_period: Optional[int] = None,  # in seconds
                 importance_threshold: int = 1,
                 max_items: Optional[int] = None,
                 retrieval_priority: int = 1):
        """
        Initialize memory layer configuration.
        
        Args:
            retention_period: How long to retain memories in this layer (None = permanent)
            importance_threshold: Minimum importance score for this layer
            max_items: Maximum number of items in this layer (None = unlimited)
            retrieval_priority: Priority for retrieval (higher values retrieved first)
        """
        self.retention_period = retention_period
        self.importance_threshold = importance_threshold
        self.max_items = max_items
        self.retrieval_priority = retrieval_priority


class RealTimeMemoryManager:
    """
    Enhanced memory manager with real-time adaptation capabilities.
    Implements layered memory architecture (short-term vs. long-term),
    context persistence scoring, and context synchronization across AI models.
    """
    
    def __init__(self):
        """Initialize the real-time memory manager."""
        # Core memory manager
        self.memory_manager = MemoryManager()
        
        # Memory layers configuration
        self.layers = {
            "working": MemoryLayerConfig(
                retention_period=60*60,     # 1 hour retention
                importance_threshold=1,     # All items
                max_items=50,               # Limited capacity
                retrieval_priority=3        # Highest priority
            ),
            "short_term": MemoryLayerConfig(
                retention_period=60*60*24,  # 1 day retention
                importance_threshold=3,     # Somewhat important
                max_items=100,              # Medium capacity
                retrieval_priority=2        # Medium priority
            ),
            "long_term": MemoryLayerConfig(
                retention_period=None,      # Permanent
                importance_threshold=5,     # Important items only
                max_items=None,             # Unlimited capacity
                retrieval_priority=1        # Lowest priority
            )
        }
        
        # Cache for frequently accessed memories
        self.memory_cache = {}
        self.cache_hit_counter = defaultdict(int)
        self.cache_last_access = {}
        self.max_cache_size = 50
        
        # Context persistence scoring
        self.context_scores = {}
        self.context_references = defaultdict(set)
        
        # Model-specific contexts
        self.model_contexts = {}
        
        logger.info("Real-Time Memory Manager initialized")

    def assign_to_layers(self, memory_item: MemoryItem) -> List[str]:
        """
        Assign a memory item to appropriate layers based on importance and other factors.
        
        Args:
            memory_item: The memory item to assign
            
        Returns:
            List of layer names the item was assigned to
        """
        assigned_layers = []
        
        for layer_name, config in self.layers.items():
            if memory_item.importance >= config.importance_threshold:
                # Check if layer has capacity
                if config.max_items is not None:
                    layer_items = self.get_memories_in_layer(layer_name)
                    if len(layer_items) >= config.max_items:
                        # Only add if more important than least important item in layer
                        least_important = min(layer_items, key=lambda x: x.importance)
                        if memory_item.importance <= least_important.importance:
                            continue
                        # Remove least important item from this layer
                        self._remove_from_layer(least_important.id, layer_name)
                
                # Add to layer
                self._add_to_layer(memory_item.id, layer_name)
                assigned_layers.append(layer_name)
        
        logger.info(f"Memory item {memory_item.id} assigned to layers: {assigned_layers}")
        return assigned_layers

    def _add_to_layer(self, memory_id: str, layer_name: str) -> bool:
        """Add a memory item to a specific layer."""
        memory_item = self.memory_manager.get_memory(memory_id)
        if not memory_item:
            return False
            
        # Add layer to metadata
        if "layers" not in memory_item.metadata:
            memory_item.metadata["layers"] = []
        
        if layer_name not in memory_item.metadata["layers"]:
            memory_item.metadata["layers"].append(layer_name)
            self.memory_manager.update_memory(
                memory_id, 
                metadata=memory_item.metadata
            )
            return True
        
        return False
    
    def _remove_from_layer(self, memory_id: str, layer_name: str) -> bool:
        """Remove a memory item from a specific layer."""
        memory_item = self.memory_manager.get_memory(memory_id)
        if not memory_item or "layers" not in memory_item.metadata:
            return False
            
        if layer_name in memory_item.metadata["layers"]:
            memory_item.metadata["layers"].remove(layer_name)
            self.memory_manager.update_memory(
                memory_id, 
                metadata=memory_item.metadata
            )
            return True
        
        return False
    
    def get_memories_in_layer(self, layer_name: str) -> List[MemoryItem]:
        """Get all memory items in a specific layer."""
        all_memories = []
        
        # This could be optimized with an index, but this implementation is simpler
        for memory_id, memory_item in self.memory_manager.memory_items.items():
            if "layers" in memory_item.metadata and layer_name in memory_item.metadata["layers"]:
                all_memories.append(memory_item)
                
        return all_memories
    
    def add_memory_with_context(self, 
                               content: str, 
                               source: str, 
                               category: str,
                               context: str,
                               importance: int = 1, 
                               tags: List[str] = None,
                               expires_at: Optional[datetime] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """
        Add a new memory with context reference tracking.
        
        Args:
            content: Memory content
            source: Memory source
            category: Memory category
            context: The context this memory is related to
            importance: Importance score (1-10)
            tags: Tags for search/retrieval
            expires_at: Expiration date
            metadata: Additional metadata
            
        Returns:
            The created memory item
        """
        if metadata is None:
            metadata = {}
        
        # Add context reference to metadata
        metadata["context_references"] = [context]
        
        # Create the memory
        memory_item = self.memory_manager.add_memory(
            content=content,
            source=source,
            category=category,
            importance=importance,
            tags=tags or [],
            expires_at=expires_at,
            metadata=metadata
        )
        
        # Update context references
        self.context_references[memory_item.id].add(context)
        
        # Assign to appropriate layers
        self.assign_to_layers(memory_item)
        
        # Add to cache for faster retrieval
        self.add_to_cache(memory_item)
        
        return memory_item
    
    def update_context_score(self, memory_id: str, context: str, score_increment: float = 0.1):
        """
        Update the context persistence score for a memory item.
        
        Args:
            memory_id: Memory item ID
            context: Context string this item is relevant to
            score_increment: Amount to increase the score
        """
        if memory_id not in self.context_scores:
            self.context_scores[memory_id] = {}
            
        if context not in self.context_scores[memory_id]:
            self.context_scores[memory_id][context] = 0.0
            
        # Increment score
        self.context_scores[memory_id][context] += score_increment
        
        # Ensure score doesn't exceed 1.0
        self.context_scores[memory_id][context] = min(1.0, self.context_scores[memory_id][context])
        
        # Add context reference
        self.context_references[memory_id].add(context)
    
    def get_relevant_context_memories(self, context: str, max_results: int = 10) -> List[MemoryItem]:
        """
        Get memories relevant to the given context using context persistence scoring.
        
        Args:
            context: Current context to find relevant memories for
            max_results: Maximum number of results
            
        Returns:
            List of relevant memory items
        """
        scored_items = []
        
        # First, check cache for relevant items
        for memory_id in self.memory_cache:
            if memory_id in self.context_scores and context in self.context_scores[memory_id]:
                score = self.context_scores[memory_id][context]
                memory_item = self.memory_manager.get_memory(memory_id)
                if memory_item:
                    scored_items.append((memory_item, score))
                    # Update cache hit counter
                    self.cache_hit_counter[memory_id] += 1
                    self.cache_last_access[memory_id] = datetime.now()
        
        # Then, look for items with context references
        potential_items = []
        for memory_id, contexts in self.context_references.items():
            if context in contexts and memory_id not in self.memory_cache:
                memory_item = self.memory_manager.get_memory(memory_id)
                if memory_item:
                    score = self.context_scores.get(memory_id, {}).get(context, 0.1)
                    potential_items.append((memory_item, score))
        
        # Combine, sort by score, and return top results
        scored_items.extend(potential_items)
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        # Get top items
        top_items = [item for item, _ in scored_items[:max_results]]
        
        # Add frequently accessed items to cache
        for memory_item, _ in potential_items:
            if memory_item.id not in self.memory_cache:
                self.add_to_cache(memory_item)
        
        return top_items
    
    def add_to_cache(self, memory_item: MemoryItem):
        """
        Add a memory item to the cache.
        
        Args:
            memory_item: Memory item to cache
        """
        # Check if cache is full
        if len(self.memory_cache) >= self.max_cache_size:
            # Remove least recently used item
            lru_id = min(self.cache_last_access.items(), key=lambda x: x[1])[0]
            del self.memory_cache[lru_id]
            del self.cache_hit_counter[lru_id]
            del self.cache_last_access[lru_id]
        
        # Add to cache
        self.memory_cache[memory_item.id] = memory_item
        self.cache_last_access[memory_item.id] = datetime.now()
        self.cache_hit_counter[memory_item.id] = 0
    
    def set_model_context(self, model_name: str, context_data: Dict[str, Any]):
        """
        Set context data for a specific AI model.
        
        Args:
            model_name: Name of the AI model
            context_data: Context data to store
        """
        self.model_contexts[model_name] = context_data
        logger.info(f"Updated context for model {model_name}")
    
    def get_model_context(self, model_name: str) -> Dict[str, Any]:
        """
        Get context data for a specific AI model.
        
        Args:
            model_name: Name of the AI model
            
        Returns:
            Context data for the model or empty dict if not found
        """
        return self.model_contexts.get(model_name, {})
    
    def sync_contexts(self, source_model: str, target_models: List[str]):
        """
        Synchronize context between AI models.
        
        Args:
            source_model: Source model to sync from
            target_models: Target models to sync to
        """
        source_context = self.get_model_context(source_model)
        
        for target_model in target_models:
            # Get existing context for target model
            target_context = self.get_model_context(target_model)
            
            # Update with source context
            target_context.update(source_context)
            
            # Set updated context
            self.set_model_context(target_model, target_context)
        
        logger.info(f"Synchronized context from {source_model} to {target_models}")
    
    def cleanup_expired_memories(self):
        """Clean up expired memories and update layer assignments."""
        current_time = datetime.now()
        
        # Check all memory items
        for memory_id, memory_item in list(self.memory_manager.memory_items.items()):
            # Check if memory has expired
            if memory_item.expires_at and memory_item.expires_at < current_time:
                logger.info(f"Memory {memory_id} has expired, removing")
                self.memory_manager.delete_memory(memory_id)
                continue
            
            # Check layer retention periods
            if "layers" in memory_item.metadata:
                for layer_name in list(memory_item.metadata["layers"]):
                    layer_config = self.layers.get(layer_name)
                    if not layer_config:
                        continue
                        
                    # Check if memory has exceeded retention period for this layer
                    if layer_config.retention_period:
                        retention_limit = current_time - timedelta(seconds=layer_config.retention_period)
                        if memory_item.created_at < retention_limit:
                            # Memory has exceeded retention period for this layer
                            self._remove_from_layer(memory_id, layer_name)
                            logger.info(f"Memory {memory_id} removed from layer {layer_name} due to retention period")


# Create a singleton instance
real_time_memory_manager = RealTimeMemoryManager()


def test_real_time_memory_manager():
    """Test the RealTimeMemoryManager functionality."""
    print("\nTesting Real-Time Memory Manager...\n")
    
    # Test adding memories to different layers
    memory1 = real_time_memory_manager.add_memory_with_context(
        content="User prefers concise responses",
        source="system",
        category="preference",
        context="user_preferences",
        importance=7,
        tags=["preference", "response_length"]
    )
    
    memory2 = real_time_memory_manager.add_memory_with_context(
        content="User asked about Python programming",
        source="user",
        category="interest",
        context="conversation_topics",
        importance=3,
        tags=["python", "programming"]
    )
    
    memory3 = real_time_memory_manager.add_memory_with_context(
        content="User mentioned they're a beginner",
        source="inference",
        category="user_profile",
        context="skill_level",
        importance=6,
        tags=["beginner", "skill_level"]
    )
    
    # Check layer assignments
    working_memories = real_time_memory_manager.get_memories_in_layer("working")
    short_term_memories = real_time_memory_manager.get_memories_in_layer("short_term")
    long_term_memories = real_time_memory_manager.get_memories_in_layer("long_term")
    
    print(f"Working memory layer: {len(working_memories)} items")
    print(f"Short-term memory layer: {len(short_term_memories)} items")
    print(f"Long-term memory layer: {len(long_term_memories)} items")
    
    # Test context relevance
    real_time_memory_manager.update_context_score(memory1.id, "user_preferences", 0.5)
    real_time_memory_manager.update_context_score(memory3.id, "user_preferences", 0.3)
    
    relevant_memories = real_time_memory_manager.get_relevant_context_memories("user_preferences")
    print(f"\nRelevant memories for 'user_preferences': {len(relevant_memories)} items")
    for i, mem in enumerate(relevant_memories, 1):
        print(f"  {i}. {mem.content} (importance: {mem.importance})")
    
    # Test model context synchronization
    real_time_memory_manager.set_model_context("claude", {
        "skill_level": "beginner",
        "interests": ["python", "programming"]
    })
    
    real_time_memory_manager.sync_contexts("claude", ["gpt", "bard"])
    
    claude_context = real_time_memory_manager.get_model_context("claude")
    gpt_context = real_time_memory_manager.get_model_context("gpt")
    
    print("\nContext synchronization:")
    print(f"  Claude context: {claude_context}")
    print(f"  GPT context: {gpt_context}")
    
    print("\nReal-Time Memory Manager tests completed!")


if __name__ == "__main__":
    test_real_time_memory_manager()
