#!/usr/bin/env python3
"""
Memory Priority System for Minerva

This module handles memory prioritization, ranking, and decay algorithms.
It determines which memories are most important and should be retained.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from .memory_models import MemoryItem, ConversationMemory


class MemoryPriority:
    """
    System for calculating and managing memory priorities.
    
    Priority is calculated based on multiple factors:
    - Base importance (1-10 scale)
    - Recency (how recently created/accessed)
    - Access frequency (how often retrieved)
    - Context relevance (how relevant to current context)
    - Content significance (type of information)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the priority system.
        
        Args:
            config: Configuration parameters for priority calculation
        """
        # Default configuration
        self.config = {
            'importance_weight': 0.35,      # Base importance influence
            'recency_weight': 0.25,         # Recent access influence  
            'frequency_weight': 0.20,       # Access frequency influence
            'age_weight': 0.10,             # Age factor (newer = better)
            'context_weight': 0.10,         # Context relevance
            
            # Decay parameters
            'recency_decay_days': 30,       # Days for recency to decay by half
            'frequency_boost_cap': 2.0,     # Maximum frequency multiplier
            'context_boost_cap': 1.5,       # Maximum context multiplier
            
            # Category importance multipliers
            'category_multipliers': {
                'preference': 1.2,          # User preferences are important
                'instruction': 1.1,         # Instructions should be remembered
                'fact': 1.0,               # Regular facts
                'context': 0.9,            # Context is less permanent
                'temporary': 0.7,          # Temporary info decays faster
            },
            
            # Source reliability multipliers
            'source_multipliers': {
                'user': 1.2,               # User input is highly valued
                'system': 1.0,             # System generated
                'inference': 0.9,          # Inferred information
                'external': 0.8,           # External sources
            }
        }
        
        # Update with provided config
        if config:
            self.config.update(config)
    
    def calculate_priority_score(self, memory: MemoryItem, current_context: str = None) -> float:
        """
        Calculate comprehensive priority score for a memory.
        
        Args:
            memory: Memory item to score
            current_context: Current context for relevance calculation
            
        Returns:
            Priority score (0.0 to 10.0+)
        """
        if memory.is_expired:
            return 0.0
        
        # Base importance (1-10)
        base_score = memory.importance
        
        # Calculate individual components
        recency_factor = self._calculate_recency_factor(memory)
        frequency_factor = self._calculate_frequency_factor(memory)
        age_factor = self._calculate_age_factor(memory)
        context_factor = self._calculate_context_factor(memory, current_context)
        
        # Apply category multiplier
        category_multiplier = self.config['category_multipliers'].get(
            memory.category, 1.0
        )
        
        # Apply source multiplier
        source_multiplier = self.config['source_multipliers'].get(
            memory.source, 1.0
        )
        
        # Weighted combination
        weighted_score = (
            base_score * self.config['importance_weight'] +
            recency_factor * self.config['recency_weight'] * 10 +
            frequency_factor * self.config['frequency_weight'] * 10 +
            age_factor * self.config['age_weight'] * 10 +
            context_factor * self.config['context_weight'] * 10
        )
        
        # Apply multipliers
        final_score = weighted_score * category_multiplier * source_multiplier
        
        return max(0.0, final_score)
    
    def _calculate_recency_factor(self, memory: MemoryItem) -> float:
        """Calculate factor based on how recently the memory was accessed."""
        days_since_access = memory.days_since_last_access
        decay_constant = math.log(2) / self.config['recency_decay_days']
        
        # Exponential decay: recent access = higher score
        recency_factor = math.exp(-decay_constant * days_since_access)
        
        return recency_factor
    
    def _calculate_frequency_factor(self, memory: MemoryItem) -> float:
        """Calculate factor based on access frequency."""
        if memory.access_count <= 1:
            return 0.5  # Base level for new memories
        
        # Logarithmic scaling to prevent unlimited growth
        frequency_factor = 1 + math.log(memory.access_count) / 10
        
        # Cap the frequency boost
        return min(frequency_factor, self.config['frequency_boost_cap'])
    
    def _calculate_age_factor(self, memory: MemoryItem) -> float:
        """Calculate factor based on memory age (newer is generally better)."""
        age_days = memory.age_days
        
        if age_days <= 1:
            return 1.0  # Very new
        elif age_days <= 7:
            return 0.9  # Recent
        elif age_days <= 30:
            return 0.8  # Somewhat recent
        elif age_days <= 90:
            return 0.7  # Older
        else:
            return 0.6  # Old but may still be relevant
    
    def _calculate_context_factor(self, memory: MemoryItem, current_context: str) -> float:
        """Calculate factor based on relevance to current context."""
        if not current_context or not memory.contexts:
            return 0.5  # Neutral when no context
        
        # Check if current context matches any stored contexts
        max_relevance = 0.0
        for context_ref, score in memory.contexts.items():
            if current_context.lower() in context_ref.lower() or context_ref.lower() in current_context.lower():
                max_relevance = max(max_relevance, score)
        
        # Apply context boost cap
        context_factor = min(max_relevance * 1.5, self.config['context_boost_cap'])
        
        return context_factor if context_factor > 0 else 0.5
    
    def rank_memories(self, memories: List[MemoryItem], 
                     current_context: str = None, 
                     max_results: int = None) -> List[Tuple[MemoryItem, float]]:
        """
        Rank memories by priority score.
        
        Args:
            memories: List of memory items to rank
            current_context: Current context for relevance
            max_results: Maximum number of results to return
            
        Returns:
            List of (memory, score) tuples, sorted by priority
        """
        scored_memories = []
        
        for memory in memories:
            if not memory.is_expired:
                score = self.calculate_priority_score(memory, current_context)
                scored_memories.append((memory, score))
        
        # Sort by score (highest first)
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # Limit results if specified
        if max_results:
            scored_memories = scored_memories[:max_results]
        
        return scored_memories
    
    def identify_candidates_for_cleanup(self, memories: List[MemoryItem], 
                                      cleanup_threshold: float = 2.0) -> List[MemoryItem]:
        """
        Identify memories that are candidates for cleanup/deletion.
        
        Args:
            memories: List of memory items
            cleanup_threshold: Minimum score to keep (below this = cleanup candidate)
            
        Returns:
            List of memories that could be cleaned up
        """
        cleanup_candidates = []
        
        for memory in memories:
            score = self.calculate_priority_score(memory)
            
            # Add to cleanup if below threshold or expired
            if score < cleanup_threshold or memory.is_expired:
                cleanup_candidates.append(memory)
        
        return cleanup_candidates
    
    def suggest_memory_importance(self, content: str, source: str, category: str) -> int:
        """
        Suggest importance level for new memory based on content analysis.
        
        Args:
            content: Memory content
            source: Memory source
            category: Memory category
            
        Returns:
            Suggested importance (1-10)
        """
        base_importance = 5  # Default middle importance
        
        content_lower = content.lower()
        
        # High importance indicators
        high_importance_indicators = [
            'important', 'critical', 'urgent', 'must', 'always', 'never',
            'remember', 'don\'t forget', 'essential', 'required', 'necessary',
            'password', 'secret', 'private', 'confidential'
        ]
        
        # Low importance indicators  
        low_importance_indicators = [
            'maybe', 'perhaps', 'sometimes', 'occasionally', 'might',
            'could be', 'not sure', 'temporarily', 'for now'
        ]
        
        # Adjust based on content analysis
        for indicator in high_importance_indicators:
            if indicator in content_lower:
                base_importance = min(10, base_importance + 2)
                break
        
        for indicator in low_importance_indicators:
            if indicator in content_lower:
                base_importance = max(1, base_importance - 1)
                break
        
        # Adjust based on category
        category_adjustments = {
            'preference': +1,      # User preferences are important
            'instruction': +1,     # Instructions should be remembered
            'fact': 0,            # Neutral
            'context': -1,        # Context is less permanent
            'temporary': -2,      # Temporary info is low importance
        }
        
        base_importance += category_adjustments.get(category, 0)
        
        # Adjust based on source
        source_adjustments = {
            'user': +1,           # User input is valued
            'system': 0,          # Neutral
            'inference': -1,      # Inferred is less certain
            'external': -1,       # External sources less trusted
        }
        
        base_importance += source_adjustments.get(source, 0)
        
        # Ensure within valid range
        return max(1, min(10, base_importance))
    
    def calculate_memory_decay(self, memory: MemoryItem, days_passed: int) -> float:
        """
        Calculate how much a memory's effective importance has decayed.
        
        Args:
            memory: Memory item
            days_passed: Number of days since creation
            
        Returns:
            Decay factor (0.0 to 1.0, where 1.0 = no decay)
        """
        if memory.category == 'preference':
            # Preferences decay very slowly
            half_life = 180  # 6 months
        elif memory.category == 'instruction':
            # Instructions decay slowly  
            half_life = 90   # 3 months
        elif memory.category == 'fact':
            # Facts decay moderately
            half_life = 60   # 2 months
        elif memory.category == 'context':
            # Context decays faster
            half_life = 30   # 1 month
        elif memory.category == 'temporary':
            # Temporary info decays very fast
            half_life = 7    # 1 week
        else:
            # Default decay
            half_life = 45   # ~1.5 months
        
        # Exponential decay formula
        decay_constant = math.log(2) / half_life
        decay_factor = math.exp(-decay_constant * days_passed)
        
        return decay_factor
    
    def get_memory_statistics(self, memories: List[MemoryItem]) -> Dict[str, any]:
        """
        Get statistics about memory collection.
        
        Args:
            memories: List of memory items
            
        Returns:
            Dictionary with various statistics
        """
        if not memories:
            return {'total': 0}
        
        total_memories = len(memories)
        active_memories = [m for m in memories if not m.is_expired]
        
        # Calculate average scores
        scores = [self.calculate_priority_score(m) for m in active_memories]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Category distribution
        categories = {}
        for memory in memories:
            categories[memory.category] = categories.get(memory.category, 0) + 1
        
        # Source distribution
        sources = {}
        for memory in memories:
            sources[memory.source] = sources.get(memory.source, 0) + 1
        
        # Age distribution
        age_buckets = {'new': 0, 'recent': 0, 'old': 0, 'ancient': 0}
        for memory in memories:
            age = memory.age_days
            if age <= 7:
                age_buckets['new'] += 1
            elif age <= 30:
                age_buckets['recent'] += 1
            elif age <= 90:
                age_buckets['old'] += 1
            else:
                age_buckets['ancient'] += 1
        
        return {
            'total': total_memories,
            'active': len(active_memories),
            'expired': total_memories - len(active_memories),
            'average_score': round(avg_score, 2),
            'categories': categories,
            'sources': sources,
            'age_distribution': age_buckets,
            'cleanup_candidates': len(self.identify_candidates_for_cleanup(memories))
        }


# Export the priority system
__all__ = ['MemoryPriority'] 