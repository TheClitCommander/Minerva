"""
Multi-AI Context Synchronization

This module ensures cohesive memory state and context sharing between multiple AI models,
preventing context fragmentation and ensuring seamless knowledge recall.
"""

import os
import sys
import json
import time
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix import paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from memory.real_time_memory_manager import real_time_memory_manager
from ai_decision.real_time_adaptation import adaptation_engine
from web.multi_ai_coordinator import multi_ai_coordinator

class SharedContext:
    """Model for shared context between AI models."""
    
    def __init__(self, context_id: str = None):
        """
        Initialize a shared context instance.
        
        Args:
            context_id: Optional ID for this context
        """
        self.context_id = context_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.last_updated = self.created_at
        self.access_count = 0
        self.data = {}
        self.source_models = set()
        self.target_models = set()
        self.priority = 1  # 1-5 scale, higher is more important
    
    def update(self, key: str, value: Any, source_model: str = None):
        """
        Update a specific context key.
        
        Args:
            key: Context key to update
            value: New value
            source_model: Model that provided this update
        """
        self.data[key] = value
        self.last_updated = datetime.now()
        
        if source_model:
            self.source_models.add(source_model)
    
    def merge(self, other_context: Dict[str, Any], source_model: str = None):
        """
        Merge another context into this one.
        
        Args:
            other_context: Context to merge
            source_model: Model that provided this context
        """
        self.data.update(other_context)
        self.last_updated = datetime.now()
        
        if source_model:
            self.source_models.add(source_model)
    
    def add_target_model(self, model_name: str):
        """Add a model to receive this context."""
        self.target_models.add(model_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission."""
        return {
            "context_id": self.context_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "access_count": self.access_count,
            "data": self.data,
            "source_models": list(self.source_models),
            "target_models": list(self.target_models),
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedContext':
        """Create a SharedContext from a dictionary."""
        context = cls(context_id=data.get("context_id"))
        context.created_at = datetime.fromisoformat(data["created_at"])
        context.last_updated = datetime.fromisoformat(data["last_updated"])
        context.access_count = data["access_count"]
        context.data = data["data"]
        context.source_models = set(data["source_models"])
        context.target_models = set(data["target_models"])
        context.priority = data["priority"]
        return context


class MultiAIContextSync:
    """
    Maintains synchronized context between multiple AI models to ensure
    cohesive memory state and prevent context fragmentation.
    """
    
    def __init__(self):
        """Initialize the multi-AI context synchronization system."""
        # Dictionary of active contexts by user ID
        self.active_contexts = defaultdict(dict)
        
        # Reference to memory manager
        self.memory_manager = real_time_memory_manager
        
        # Reference to adaptation engine
        self.adaptation_engine = adaptation_engine
        
        # Reference to multi-AI coordinator
        self.coordinator = multi_ai_coordinator
        
        # Recently synchronized contexts
        self.recent_syncs = defaultdict(list)
        
        # Maximum contexts to keep per user
        self.max_contexts_per_user = 5
        
        logger.info("Multi-AI Context Synchronization system initialized")
    
    def create_shared_context(self, user_id: str, 
                             initial_data: Optional[Dict[str, Any]] = None,
                             source_model: Optional[str] = None,
                             priority: int = 1) -> SharedContext:
        """
        Create a new shared context for a user.
        
        Args:
            user_id: User ID
            initial_data: Initial context data
            source_model: Source model
            priority: Context priority (1-5)
            
        Returns:
            The created shared context
        """
        # Create new context
        context = SharedContext()
        context.priority = priority
        
        # Add initial data if provided
        if initial_data:
            context.merge(initial_data, source_model)
        
        # Add to active contexts
        self.active_contexts[user_id][context.context_id] = context
        
        # Prune contexts if needed
        self._prune_contexts(user_id)
        
        logger.info(f"Created new shared context {context.context_id} for user {user_id}")
        
        return context
    
    def _prune_contexts(self, user_id: str):
        """Prune contexts if we have too many for a user."""
        contexts = self.active_contexts[user_id]
        
        if len(contexts) <= self.max_contexts_per_user:
            return
            
        # Sort by priority, then by last_updated (newest first)
        sorted_contexts = sorted(
            contexts.items(),
            key=lambda x: (-x[1].priority, -time.mktime(x[1].last_updated.timetuple()))
        )
        
        # Keep only the max number of contexts
        contexts_to_keep = sorted_contexts[:self.max_contexts_per_user]
        
        # Update active contexts
        self.active_contexts[user_id] = {k: v for k, v in contexts.items() if k in [c[0] for c in contexts_to_keep]}
    
    def update_shared_context(self, user_id: str, context_id: str, 
                            updates: Dict[str, Any], 
                            source_model: Optional[str] = None) -> Optional[SharedContext]:
        """
        Update a shared context with new data.
        
        Args:
            user_id: User ID
            context_id: Context ID
            updates: Updates to apply
            source_model: Source model
            
        Returns:
            Updated context or None if not found
        """
        # Check if context exists
        if context_id not in self.active_contexts[user_id]:
            logger.warning(f"Shared context {context_id} not found for user {user_id}")
            return None
        
        # Get context
        context = self.active_contexts[user_id][context_id]
        
        # Apply updates
        context.merge(updates, source_model)
        
        logger.info(f"Updated shared context {context_id} for user {user_id}")
        
        return context
    
    def get_shared_context(self, user_id: str, context_id: str) -> Optional[SharedContext]:
        """
        Get a shared context by ID.
        
        Args:
            user_id: User ID
            context_id: Context ID
            
        Returns:
            The shared context or None if not found
        """
        # Check if context exists
        if context_id not in self.active_contexts[user_id]:
            return None
        
        # Get context
        context = self.active_contexts[user_id][context_id]
        
        # Update access count
        context.access_count += 1
        
        return context
    
    def get_active_contexts(self, user_id: str) -> Dict[str, SharedContext]:
        """
        Get all active contexts for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of active contexts
        """
        return self.active_contexts[user_id]
    
    def sync_context_to_models(self, user_id: str, context_id: str, 
                              target_models: List[str]) -> bool:
        """
        Synchronize a context to multiple models.
        
        Args:
            user_id: User ID
            context_id: Context ID
            target_models: Models to sync to
            
        Returns:
            True if successful, False otherwise
        """
        # Check if context exists
        if context_id not in self.active_contexts[user_id]:
            logger.warning(f"Shared context {context_id} not found for user {user_id}")
            return False
        
        # Get context
        context = self.active_contexts[user_id][context_id]
        
        # Add target models
        for model in target_models:
            context.add_target_model(model)
        
        # Sync to memory manager
        for model in target_models:
            self.memory_manager.set_model_context(model, context.data)
        
        # Record sync event
        self.recent_syncs[user_id].append({
            "context_id": context_id,
            "target_models": target_models,
            "timestamp": datetime.now()
        })
        
        # Limit recent syncs
        if len(self.recent_syncs[user_id]) > 10:
            self.recent_syncs[user_id] = self.recent_syncs[user_id][-10:]
        
        logger.info(f"Synchronized context {context_id} to models: {target_models}")
        
        return True
    
    def create_model_override(self, user_id: str, message: str, 
                             context_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a model selection override based on context.
        
        Args:
            user_id: User ID
            message: User message
            context_id: Optional context ID to use
            
        Returns:
            Model selection override parameters
        """
        # Start with empty override
        override = {}
        
        # Get context data
        context_data = {}
        
        if context_id:
            # Use specific context
            context = self.get_shared_context(user_id, context_id)
            if context:
                context_data = context.data
        else:
            # Use all active contexts
            contexts = self.get_active_contexts(user_id)
            
            # Merge contexts by priority
            for _, context in sorted(contexts.items(), key=lambda x: -x[1].priority):
                context_data.update(context.data)
        
        # Get user adaptations
        adaptations = self.adaptation_engine.get_adaptations(user_id)
        
        # Create override parameters
        models_to_use = []
        
        # Determine models based on context
        detail_level = context_data.get("detail_level", adaptations.get("detail_level", "balanced"))
        
        if detail_level == "technical":
            # Technical content needs comprehensive model
            models_to_use.append("claude-opus")
            timeout = 30.0
        elif detail_level == "detailed":
            # Detailed content uses balanced model
            models_to_use.append("claude-sonnet")
            timeout = 20.0
        else:
            # Standard or concise content uses light model
            models_to_use.append("claude-light")
            timeout = 10.0
        
        # Create formatting parameters
        formatting_params = {
            "length": context_data.get("length", adaptations.get("length", "standard")),
            "tone": context_data.get("tone", adaptations.get("tone", "neutral")),
            "structure": context_data.get("structure", "paragraph")
        }
        
        # Build override
        override = {
            "models_to_use": models_to_use,
            "timeout": timeout,
            "formatting_params": formatting_params,
            "retrieval_depth": context_data.get("retrieval_depth", "standard")
        }
        
        return override
    
    def apply_model_override(self, user_id: str, message: str, 
                            message_id: Optional[str] = None,
                            context_id: Optional[str] = None):
        """
        Apply model selection override to the coordinator.
        
        Args:
            user_id: User ID
            message: User message
            message_id: Optional message ID
            context_id: Optional context ID
        """
        # Create override
        override = self.create_model_override(user_id, message, context_id)
        
        # Apply to coordinator
        self.coordinator._override_model_selection = override
        
        # Start adaptation
        if message_id:
            self.adaptation_engine.start_response_adaptation(
                user_id=user_id,
                message_id=message_id,
                original_context=override.get("formatting_params", {})
            )
        
        logger.info(f"Applied model override for user {user_id}: {override}")
        
        return override
    
    def clear_model_override(self):
        """Clear model selection override from coordinator."""
        self.coordinator._override_model_selection = None
        logger.info("Cleared model override")
    
    def save_contexts(self, user_id: str):
        """
        Save all active contexts for a user to the memory manager.
        
        Args:
            user_id: User ID
        """
        contexts = self.get_active_contexts(user_id)
        
        for context_id, context in contexts.items():
            # Save to memory
            self.memory_manager.add_memory_with_context(
                content=f"AI context state: {len(context.data)} items",
                source="context_sync",
                category="ai_context",
                context=f"user:{user_id}",
                importance=context.priority,
                tags=["ai_context", "multi_model"],
                metadata={
                    "context_id": context_id,
                    "context_data": context.to_dict()
                }
            )
        
        logger.info(f"Saved {len(contexts)} contexts for user {user_id}")


# Create a singleton instance
context_sync = MultiAIContextSync()


def test_multi_ai_context_sync():
    """Test the MultiAIContextSync functionality."""
    print("\nTesting Multi-AI Context Synchronization...\n")
    
    user_id = "test_user_2"
    
    # Test creating a shared context
    print("Creating shared context...")
    context = context_sync.create_shared_context(
        user_id=user_id,
        initial_data={
            "skill_level": "technical",
            "interests": ["AI", "machine learning"],
            "detail_level": "technical"
        },
        source_model="claude",
        priority=3
    )
    
    print(f"Created context with ID: {context.context_id}")
    
    # Test synchronizing to multiple models
    print("\nSynchronizing context to multiple models...")
    success = context_sync.sync_context_to_models(
        user_id=user_id,
        context_id=context.context_id,
        target_models=["gpt", "bard", "claude-light"]
    )
    
    print(f"Sync successful: {success}")
    
    # Test creating model override
    print("\nCreating model selection override...")
    override = context_sync.create_model_override(
        user_id=user_id,
        message="Tell me about transformer models",
        context_id=context.context_id
    )
    
    print(f"Model override: {override}")
    
    # Test applying model override
    print("\nApplying model override...")
    applied_override = context_sync.apply_model_override(
        user_id=user_id,
        message="Tell me about transformer models",
        message_id=f"msg_{int(time.time())}",
        context_id=context.context_id
    )
    
    print(f"Applied override: {applied_override}")
    
    # Test clearing model override
    print("\nClearing model override...")
    context_sync.clear_model_override()
    
    # Test saving contexts to memory
    print("\nSaving contexts to memory...")
    context_sync.save_contexts(user_id)
    
    print("\nMulti-AI Context Synchronization tests completed!")


if __name__ == "__main__":
    test_multi_ai_context_sync()
