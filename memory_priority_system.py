#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Memory Priority System for Minerva

This module implements a memory ranking and priority system to help track 
important project information, user preferences, and system requirements
with clear importance levels and categories.
"""

import json
import os
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Union

# Define priority levels
class PriorityLevel(Enum):
    CRITICAL = 5    # Must-have, project-breaking if forgotten
    HIGH = 4        # Very important, significant impact
    MEDIUM = 3      # Important but not critical
    LOW = 2         # Nice to have
    INFO = 1        # General information
    
    def __str__(self):
        return self.name

# Define memory categories
class MemoryCategory(Enum):
    PROJECT_REQUIREMENT = "project_requirement"  # Core project requirements
    USER_PREFERENCE = "user_preference"          # User's specific preferences
    IMPLEMENTATION_DETAIL = "implementation_detail"  # How something is implemented
    TECHNICAL_CONSTRAINT = "technical_constraint"    # Technical limitations
    FUTURE_ENHANCEMENT = "future_enhancement"        # Planned future work
    GENERAL_KNOWLEDGE = "general_knowledge"          # General information
    
    def __str__(self):
        return self.name

@dataclass
class PrioritizedMemory:
    """A memory with priority information."""
    title: str
    content: str
    priority: PriorityLevel
    category: MemoryCategory
    tags: List[str]
    timestamp: float = None
    memory_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.memory_id is None:
            import uuid
            self.memory_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        result = asdict(self)
        result['priority'] = self.priority.value
        result['category'] = self.category.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PrioritizedMemory':
        """Create a PrioritizedMemory from a dictionary."""
        # Convert priority and category from values to enum members
        data = data.copy()
        data['priority'] = PriorityLevel(data['priority'])
        data['category'] = MemoryCategory(data['category'])
        return cls(**data)


class MemoryPrioritySystem:
    """System for managing prioritized memories."""
    
    def __init__(self, storage_path: str = None):
        """Initialize the memory system.
        
        Args:
            storage_path: Path to store memory files. If None, uses default location.
        """
        self.memories: List[PrioritizedMemory] = []
        
        if storage_path is None:
            # Get directory of this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.storage_path = os.path.join(base_dir, "data", "memories")
        else:
            self.storage_path = storage_path
            
        # Ensure directory exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing memories
        self.load_memories()
    
    def add_memory(self, memory: PrioritizedMemory) -> str:
        """Add a new memory to the system.
        
        Args:
            memory: The memory to add
            
        Returns:
            The ID of the added memory
        """
        self.memories.append(memory)
        self.save_memories()
        return memory.memory_id
    
    def create_memory(self, title: str, content: str, 
                     priority: Union[PriorityLevel, int, str], 
                     category: Union[MemoryCategory, str],
                     tags: List[str] = None) -> str:
        """Create and add a new memory.
        
        Args:
            title: Memory title
            content: Memory content
            priority: Priority level (enum, int value, or string name)
            category: Memory category (enum or string value)
            tags: List of tags for the memory
            
        Returns:
            The ID of the created memory
        """
        # Convert priority if needed
        if isinstance(priority, str):
            priority = PriorityLevel[priority.upper()]
        elif isinstance(priority, int):
            priority = PriorityLevel(priority)
            
        # Convert category if needed
        if isinstance(category, str):
            for cat in MemoryCategory:
                if cat.value == category or cat.name.lower() == category.lower():
                    category = cat
                    break
            else:
                # If no match found, default to general knowledge
                category = MemoryCategory.GENERAL_KNOWLEDGE
        
        if tags is None:
            tags = []
            
        memory = PrioritizedMemory(
            title=title,
            content=content,
            priority=priority,
            category=category,
            tags=tags
        )
        
        return self.add_memory(memory)
    
    def get_memory(self, memory_id: str) -> Optional[PrioritizedMemory]:
        """Get a memory by ID."""
        for memory in self.memories:
            if memory.memory_id == memory_id:
                return memory
        return None
    
    def update_memory(self, memory_id: str, **kwargs) -> bool:
        """Update a memory by ID.
        
        Args:
            memory_id: ID of the memory to update
            **kwargs: Attributes to update
            
        Returns:
            True if successful, False otherwise
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return False
            
        # Handle special conversions
        if 'priority' in kwargs:
            priority = kwargs['priority']
            if isinstance(priority, str):
                kwargs['priority'] = PriorityLevel[priority.upper()]
            elif isinstance(priority, int):
                kwargs['priority'] = PriorityLevel(priority)
                
        if 'category' in kwargs:
            category = kwargs['category']
            if isinstance(category, str):
                for cat in MemoryCategory:
                    if cat.value == category or cat.name.lower() == category.lower():
                        kwargs['category'] = cat
                        break
                else:
                    # If no match found, don't update
                    del kwargs['category']
        
        # Update memory
        for key, value in kwargs.items():
            if hasattr(memory, key):
                setattr(memory, key, value)
                
        self.save_memories()
        return True
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID.
        
        Returns:
            True if successful, False otherwise
        """
        for i, memory in enumerate(self.memories):
            if memory.memory_id == memory_id:
                del self.memories[i]
                self.save_memories()
                return True
        return False
    
    def get_memories_by_priority(self, min_priority: PriorityLevel = None) -> List[PrioritizedMemory]:
        """Get memories filtered and sorted by priority.
        
        Args:
            min_priority: Minimum priority level to include
            
        Returns:
            List of memories sorted by priority (highest first)
        """
        result = self.memories
        
        if min_priority is not None:
            if isinstance(min_priority, int):
                min_priority = PriorityLevel(min_priority)
            result = [m for m in result if m.priority.value >= min_priority.value]
            
        # Sort by priority (highest first)
        return sorted(result, key=lambda m: m.priority.value, reverse=True)
    
    def get_memories_by_category(self, category: MemoryCategory) -> List[PrioritizedMemory]:
        """Get memories filtered by category."""
        if isinstance(category, str):
            for cat in MemoryCategory:
                if cat.value == category or cat.name.lower() == category.lower():
                    category = cat
                    break
            else:
                return []
                
        return [m for m in self.memories if m.category == category]
    
    def get_memories_by_tags(self, tags: List[str], require_all: bool = False) -> List[PrioritizedMemory]:
        """Get memories filtered by tags.
        
        Args:
            tags: List of tags to filter by
            require_all: If True, requires all tags to match; if False, any tag matches
            
        Returns:
            List of matching memories
        """
        if not tags:
            return []
            
        if require_all:
            return [m for m in self.memories 
                   if all(tag.lower() in [t.lower() for t in m.tags] for tag in tags)]
        else:
            return [m for m in self.memories 
                   if any(tag.lower() in [t.lower() for t in m.tags] for tag in tags)]
    
    def save_memories(self):
        """Save all memories to storage."""
        memory_file = os.path.join(self.storage_path, "prioritized_memories.json")
        
        # Convert to dictionaries
        memory_dicts = [m.to_dict() for m in self.memories]
        
        with open(memory_file, 'w') as f:
            json.dump(memory_dicts, f, indent=2)
    
    def load_memories(self):
        """Load memories from storage."""
        memory_file = os.path.join(self.storage_path, "prioritized_memories.json")
        
        if not os.path.exists(memory_file):
            self.memories = []
            return
            
        try:
            with open(memory_file, 'r') as f:
                memory_dicts = json.load(f)
                
            self.memories = [PrioritizedMemory.from_dict(m) for m in memory_dicts]
        except Exception as e:
            print(f"Error loading memories: {e}")
            self.memories = []
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the memory system state."""
        if not self.memories:
            return {
                "total_memories": 0,
                "by_priority": {},
                "by_category": {}
            }
            
        # Count by priority
        priority_counts = {}
        for p in PriorityLevel:
            count = len([m for m in self.memories if m.priority == p])
            if count > 0:
                priority_counts[str(p)] = count
                
        # Count by category
        category_counts = {}
        for c in MemoryCategory:
            count = len([m for m in self.memories if m.category == c])
            if count > 0:
                category_counts[str(c)] = count
                
        return {
            "total_memories": len(self.memories),
            "by_priority": priority_counts,
            "by_category": category_counts
        }
    
    def print_summary(self):
        """Print a readable summary of the memory system."""
        summary = self.get_summary()
        
        print(f"\n{'='*60}")
        print(f"MEMORY SYSTEM SUMMARY")
        print(f"{'='*60}")
        print(f"Total Memories: {summary['total_memories']}")
        
        if summary['total_memories'] > 0:
            print("\nMemories by Priority:")
            for priority, count in summary['by_priority'].items():
                print(f"  {priority}: {count}")
                
            print("\nMemories by Category:")
            for category, count in summary['by_category'].items():
                print(f"  {category}: {count}")
                
        print(f"{'='*60}\n")
    
    def print_critical_memories(self):
        """Print all CRITICAL priority memories."""
        critical_memories = self.get_memories_by_priority(PriorityLevel.CRITICAL)
        
        if not critical_memories:
            print("\nNo CRITICAL priority memories.")
            return
            
        print(f"\n{'='*60}")
        print(f"CRITICAL PRIORITY MEMORIES")
        print(f"{'='*60}")
        
        for i, memory in enumerate(critical_memories, 1):
            print(f"{i}. {memory.title}")
            print(f"   Category: {memory.category}")
            print(f"   Tags: {', '.join(memory.tags)}")
            print(f"   {'-'*40}")
            print(f"   {memory.content[:200]}...")
            if i < len(critical_memories):
                print()
                
        print(f"{'='*60}\n")


# Example usage
if __name__ == "__main__":
    # Initialize the memory system
    memory_system = MemoryPrioritySystem()
    
    # Example: Add some memories with different priorities
    memory_system.create_memory(
        title="Performance Optimization Requirements",
        content="The system must prioritize speed for simple queries by using fewer models.",
        priority=PriorityLevel.CRITICAL,
        category=MemoryCategory.PROJECT_REQUIREMENT,
        tags=["performance", "think_tank", "requirements"]
    )
    
    memory_system.create_memory(
        title="User Preference: Parallel Processing",
        content="User prefers parallel processing for complex queries.",
        priority=PriorityLevel.HIGH,
        category=MemoryCategory.USER_PREFERENCE,
        tags=["user_preference", "performance", "parallel_processing"]
    )
    
    memory_system.create_memory(
        title="Implementation Detail: Query Complexity Algorithm",
        content="Query complexity is calculated based on length and keyword matching.",
        priority=PriorityLevel.MEDIUM,
        category=MemoryCategory.IMPLEMENTATION_DETAIL,
        tags=["implementation", "algorithm", "complexity"]
    )
    
    # Print a summary of the memory system
    memory_system.print_summary()
    
    # Print critical memories
    memory_system.print_critical_memories()
