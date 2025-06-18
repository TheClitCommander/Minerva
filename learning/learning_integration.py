"""
Learning Integration Module

This module integrates Minerva's self-learning components with its memory system,
providing a unified interface for learning from user interactions, storing learned
information, and applying that knowledge to enhance user experiences.

It coordinates between the PatternDetector, PreferenceTracker, and the
EnhancedMemoryManager to ensure that learned information is appropriately
stored and retrieved when needed.
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix import paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import learning components
from learning.pattern_detector import PatternDetector
from learning.preference_tracker import PreferenceTracker

# Import memory components
try:
    from memory.enhanced_memory_manager import EnhancedMemoryManager
except ImportError:
    # For testing, use the mock memory manager
    from learning.mock_memory_manager import MockMemoryManager as EnhancedMemoryManager

class LearningIntegration:
    """
    Integrates Minerva's learning components with its memory system.
    
    This class coordinates the learning process, applying thresholds and user
    confirmation rules, and manages the storage of learned information in
    Minerva's long-term memory.
    """
    
    def __init__(self, 
                 memory_manager: Optional[EnhancedMemoryManager] = None,
                 user_confirmation_threshold: float = 0.9,
                 auto_learning_threshold: float = 0.95,
                 learning_dir: Optional[str] = None):
        """
        Initialize the learning integration system.
        
        Args:
            memory_manager: Instance of EnhancedMemoryManager
            user_confirmation_threshold: Confidence threshold above which to request user confirmation
            auto_learning_threshold: Confidence threshold above which to learn automatically
            learning_dir: Directory for storing learning component states
        """
        # Initialize or use provided memory manager
        self.memory_manager = memory_manager or EnhancedMemoryManager()
        
        # Configure learning thresholds
        self.user_confirmation_threshold = user_confirmation_threshold
        self.auto_learning_threshold = auto_learning_threshold
        
        # Set up learning directory
        self.learning_dir = learning_dir or os.path.join(
            os.path.expanduser("~"), ".minerva", "learning"
        )
        os.makedirs(self.learning_dir, exist_ok=True)
        
        # Initialize learning components
        self.pattern_detector = PatternDetector()
        self.preference_tracker = PreferenceTracker()
        
        # Load saved state if available
        self._load_state()
        
        logger.info(f"LearningIntegration initialized with confirmation_threshold={user_confirmation_threshold}, "
                  f"auto_learning_threshold={auto_learning_threshold}")
    
    def process_message(self, 
                       message: str, 
                       user_id: str, 
                       session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message to detect patterns and preferences.
        
        Args:
            message: The user message
            user_id: User identifier
            session_id: Optional session identifier for context tracking
            
        Returns:
            Dict with detected patterns, preferences, and learning suggestions
        """
        results = {
            'patterns': {},
            'preferences': {},
            'learning_suggestions': [],
            'confirmation_requests': []
        }
        
        # Process with pattern detector
        patterns = self.pattern_detector.process_message(message, user_id)
        results['patterns'] = patterns
        
        # Process with preference tracker
        preferences = self.preference_tracker.process_message(message, user_id)
        results['preferences'] = preferences
        
        # Check for items that should be learned
        learnable_patterns = self.pattern_detector.get_learnable_patterns(user_id)
        learnable_preferences = self.preference_tracker.get_learnable_preferences(user_id)
        
        # Process learnable patterns
        for pattern in learnable_patterns:
            learning_item = {
                'type': 'pattern',
                'topic': pattern['topic'],
                'confidence': pattern['confidence'],
                'content': f"User frequently asks about {pattern['topic']}",
                'metadata': {
                    'occurrences': pattern['occurrences'],
                    'examples': pattern['examples'],
                    'detected_by': 'pattern_detector',
                    'last_seen': pattern['last_seen']
                }
            }
            
            # Determine if this should be auto-learned, confirmed, or suggested
            if pattern['confidence'] >= self.auto_learning_threshold:
                # Auto-learn high-confidence patterns
                self._store_in_memory(learning_item, user_id)
                # Clear from pattern detector since it's now in memory
                self.pattern_detector.clear_pattern(pattern['topic'], user_id)
                
            elif pattern['confidence'] >= self.user_confirmation_threshold:
                # Request user confirmation for medium-confidence patterns
                results['confirmation_requests'].append(learning_item)
                
            else:
                # Just track as a suggestion for now
                results['learning_suggestions'].append(learning_item)
        
        # Process learnable preferences
        for pref in learnable_preferences:
            learning_item = {
                'type': 'preference',
                'category': pref['category'],
                'value': pref['value'],
                'sentiment': pref['sentiment'],
                'confidence': pref['confidence'],
                'content': self._format_preference_for_memory(pref),
                'metadata': {
                    'source': pref['source'],
                    'contexts': pref.get('contexts', []),
                    'observations': pref.get('observations', 1),
                    'detected_by': 'preference_tracker',
                    'last_observed': pref.get('last_observed', time.time())
                }
            }
            
            # Determine if this should be auto-learned, confirmed, or suggested
            if pref['confidence'] >= self.auto_learning_threshold:
                # Auto-learn high-confidence preferences
                self._store_in_memory(learning_item, user_id)
                # Clear from preference tracker since it's now in memory
                self.preference_tracker.clear_preference(user_id, pref['key'])
                
            elif pref['confidence'] >= self.user_confirmation_threshold:
                # Request user confirmation for medium-confidence preferences
                results['confirmation_requests'].append(learning_item)
                
            else:
                # Just track as a suggestion for now
                results['learning_suggestions'].append(learning_item)
        
        # Periodically save state (could be optimized to save less frequently)
        self._save_state()
        
        return results
    
    def handle_confirmation(self, 
                           learning_item: Dict[str, Any], 
                           confirmed: bool, 
                           user_id: str) -> Optional[Dict[str, Any]]:
        """
        Handle user confirmation for a learning suggestion.
        
        Args:
            learning_item: The learning item that was presented to the user
            confirmed: Whether the user confirmed the learning
            user_id: User identifier
            
        Returns:
            Memory item if stored, None otherwise
        """
        result = None
        
        if confirmed:
            # User confirmed - store in memory
            result = self._store_in_memory(learning_item, user_id)
            
            # Clean up from tracking
            if learning_item['type'] == 'pattern':
                self.pattern_detector.clear_pattern(learning_item['topic'], user_id)
            elif learning_item['type'] == 'preference':
                key = f"{learning_item['category']}:{learning_item['value']}"
                self.preference_tracker.clear_preference(user_id, key)
        else:
            # User rejected - clear from tracking and reduce confidence
            if learning_item['type'] == 'pattern':
                self.pattern_detector.clear_pattern(learning_item['topic'], user_id)
            elif learning_item['type'] == 'preference':
                key = f"{learning_item['category']}:{learning_item['value']}"
                self.preference_tracker.clear_preference(user_id, key)
        
        # Save state after confirmation handling
        self._save_state()
        
        return result
    
    def get_confirmation_message(self, learning_item: Dict[str, Any]) -> str:
        """
        Generate a natural language confirmation message for a learning item.
        
        Args:
            learning_item: The learning item to generate a message for
            
        Returns:
            User-friendly confirmation message
        """
        if learning_item['type'] == 'pattern':
            return (f"I've noticed you frequently ask about {learning_item['topic']}. "
                    f"Would you like me to remember this for future conversations?")
                    
        elif learning_item['type'] == 'preference':
            if learning_item['sentiment'] == 'positive':
                return (f"I've noticed you seem to prefer {learning_item['value']} "
                        f"for {learning_item['category']}. Should I remember this preference?")
            else:
                return (f"I've noticed you don't seem to like {learning_item['value']} "
                        f"for {learning_item['category']}. Should I remember this preference?")
        
        # Generic fallback
        return "I've noticed something that might be important. Would you like me to remember this?"
    
    def _store_in_memory(self, 
                       learning_item: Dict[str, Any], 
                       user_id: str) -> Dict[str, Any]:
        """
        Store a learning item in Minerva's memory system.
        
        Args:
            learning_item: The learning item to store
            user_id: User identifier
            
        Returns:
            The stored memory item
        """
        # Check if a similar memory already exists
        existing_memories = []
        if learning_item['type'] == 'pattern':
            # Check for existing pattern memories
            existing_memories = self.memory_manager.get_memories(
                query=learning_item['topic'],
                category='learned_pattern'
            )
        elif learning_item['type'] == 'preference':
            # Check for existing preference memories
            existing_memories = self.memory_manager.get_memories(
                query=learning_item['value'],
                category='preference'
            )
        
        # If similar memory exists, update it instead of creating a new one
        for memory in existing_memories:
            # Simple similarity check - could be more sophisticated
            if learning_item['content'].lower() in memory['content'].lower():
                # Update existing memory
                logger.info(f"Updating existing memory: {memory['id']}")
                
                # Update confidence if metadata exists
                metadata = memory.get('metadata', {})
                if 'confidence' in metadata:
                    metadata['confidence'] = min(1.0, metadata['confidence'] + 0.1)
                else:
                    metadata['confidence'] = learning_item.get('confidence', 0.9)
                
                # Update observation count
                if 'observations' in metadata:
                    metadata['observations'] += 1
                else:
                    metadata['observations'] = learning_item.get('metadata', {}).get('observations', 1)
                
                # Update last updated timestamp
                metadata['last_updated'] = time.time()
                
                # Append new examples if available
                examples = metadata.get('examples', [])
                new_examples = learning_item.get('metadata', {}).get('examples', [])
                if new_examples:
                    combined_examples = examples + new_examples
                    metadata['examples'] = combined_examples[:5]  # Keep up to 5 examples
                
                # Update the memory
                updated_memory = self.memory_manager.update_memory(
                    memory_id=memory['id'],
                    content=memory['content'],  # Keep original content
                    metadata=metadata
                )
                
                return updated_memory
        
        # No similar memory found, create a new one
        logger.info(f"Creating new memory from learning item: {learning_item['type']}")
        
        # Determine memory category
        if learning_item['type'] == 'pattern':
            category = 'learned_pattern'
        elif learning_item['type'] == 'preference':
            category = 'preference'
        else:
            category = 'learned_fact'
        
        # Generate tags
        tags = [learning_item['type']]
        if learning_item['type'] == 'pattern':
            tags.append(learning_item['topic'])
        elif learning_item['type'] == 'preference':
            tags.extend([learning_item['category'], learning_item['sentiment']])
        
        # Create new memory
        memory = self.memory_manager.add_memory(
            content=learning_item['content'],
            source='self_learning',
            category=category,
            importance=2,  # Medium importance for learned items
            tags=tags,
            metadata=learning_item.get('metadata', {})
        )
        
        logger.info(f"Created new memory: {memory['id']}")
        return memory
    
    def _format_preference_for_memory(self, preference: Dict[str, Any]) -> str:
        """
        Format a preference object into a natural language statement for memory storage.
        
        Args:
            preference: Preference object
            
        Returns:
            Formatted natural language statement
        """
        category = preference['category']
        value = preference['value']
        sentiment = preference['sentiment']
        
        if sentiment == 'positive':
            if category == 'general':
                return f"You prefer {value}"
            else:
                return f"You prefer {value} for {category}"
        else:
            if category == 'general':
                return f"You don't like {value}"
            else:
                return f"You don't like {value} for {category}"
    
    def _save_state(self) -> None:
        """Save the state of all learning components."""
        try:
            pattern_path = os.path.join(self.learning_dir, "pattern_detector.json")
            preference_path = os.path.join(self.learning_dir, "preference_tracker.json")
            
            self.pattern_detector.save_state(pattern_path)
            self.preference_tracker.save_state(preference_path)
            
            logger.debug("Learning system state saved successfully")
        except Exception as e:
            logger.error(f"Failed to save learning system state: {str(e)}")
    
    def _load_state(self) -> None:
        """Load the state of all learning components if available."""
        try:
            pattern_path = os.path.join(self.learning_dir, "pattern_detector.json")
            preference_path = os.path.join(self.learning_dir, "preference_tracker.json")
            
            # Load states if files exist
            if os.path.exists(pattern_path):
                self.pattern_detector.load_state(pattern_path)
                
            if os.path.exists(preference_path):
                self.preference_tracker.load_state(preference_path)
    
    def get_user_preferences(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve learned user preferences for use in context enhancement.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of preference objects with category, value, and sentiment
        """
        try:
            # Get preferences from memory system
            memories = self.memory_manager.get_memories(
                user_id=user_id,
                category='preference',
                limit=10  # Limit to most relevant preferences
            )
            
            # Format preferences from memories
            preferences = []
            for memory in memories:
                # Extract metadata
                metadata = memory.get('metadata', {})
                category = next((tag for tag in memory.get('tags', []) 
                               if tag not in ['preference', 'positive', 'negative']), 
                              'general')
                sentiment = 'positive' if 'positive' in memory.get('tags', []) else 'negative'
                
                # Extract value from content using simple parsing
                content = memory.get('content', '')
                if 'prefer' in content:
                    parts = content.split('prefer')[1].split('for')
                    value = parts[0].strip()
                    if len(parts) > 1:
                        category = parts[1].strip()
                elif "don't like" in content:
                    parts = content.split("don't like")[1].split('for')
                    value = parts[0].strip()
                    if len(parts) > 1:
                        category = parts[1].strip()
                else:
                    # Skip if we can't parse the preference
                    continue
                
                preferences.append({
                    'category': category,
                    'value': value,
                    'sentiment': sentiment,
                    'confidence': metadata.get('confidence', 0.8),
                    'observations': metadata.get('observations', 1)
                })
            
            # Also get active preferences from tracker
            active_prefs = self.preference_tracker.get_active_preferences(user_id)
            for key, pref in active_prefs.items():
                if pref.get('confidence', 0) >= self.auto_learning_threshold:
                    preferences.append({
                        'category': pref.get('category', 'general'),
                        'value': pref.get('value', ''),
                        'sentiment': pref.get('sentiment', 'positive'),
                        'confidence': pref.get('confidence', 0.8),
                        'observations': pref.get('observations', 1),
                        'active': True
                    })
            
            # Sort by confidence and return
            return sorted(preferences, key=lambda x: x.get('confidence', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Error retrieving user preferences: {str(e)}")
            return []
    
    def get_user_patterns(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve learned user patterns for use in context enhancement.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of pattern objects with topics and examples
        """
        try:
            # Get patterns from memory system
            memories = self.memory_manager.get_memories(
                user_id=user_id,
                category='learned_pattern',
                limit=10  # Limit to most relevant patterns
            )
            
            # Format patterns from memories
            patterns = []
            for memory in memories:
                # Extract metadata
                metadata = memory.get('metadata', {})
                topic = next((tag for tag in memory.get('tags', []) 
                              if tag != 'pattern'), '')
                
                patterns.append({
                    'topic': topic,
                    'content': memory.get('content', ''),
                    'confidence': metadata.get('confidence', 0.8),
                    'observations': metadata.get('observations', 1),
                    'examples': metadata.get('examples', [])
                })
            
            # Also get active patterns from detector
            active_patterns = self.pattern_detector.get_active_patterns(user_id)
            for topic, pattern in active_patterns.items():
                if pattern.get('confidence', 0) >= self.auto_learning_threshold:
                    patterns.append({
                        'topic': topic,
                        'content': pattern.get('context', ''),
                        'confidence': pattern.get('confidence', 0.8),
                        'observations': pattern.get('count', 1),
                        'examples': pattern.get('examples', []),
                        'active': True
                    })
            
            # Sort by confidence and return
            return sorted(patterns, key=lambda x: x.get('confidence', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Error retrieving user patterns: {str(e)}")
            return []
    
    def get_user_topics(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve learned user topic interests for context enhancement.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of topic objects with interest scores
        """
        try:
            # Combine topics from patterns and preferences
            topics = {}
            
            # Get topics from patterns
            patterns = self.get_user_patterns(user_id)
            for pattern in patterns:
                topic = pattern.get('topic')
                if topic and len(topic) > 2:  # Skip very short topics
                    if topic in topics:
                        topics[topic]['score'] += pattern.get('confidence', 0.5)
                        topics[topic]['count'] += 1
                    else:
                        topics[topic] = {
                            'score': pattern.get('confidence', 0.5),
                            'count': 1,
                            'source': 'pattern'
                        }
            
            # Get topics from preferences
            preferences = self.get_user_preferences(user_id)
            for pref in preferences:
                category = pref.get('category')
                value = pref.get('value')
                
                # Use both category and value as potential topics
                for topic in [category, value]:
                    if topic and len(topic) > 2:  # Skip very short topics
                        if topic in topics:
                            topics[topic]['score'] += pref.get('confidence', 0.5)
                            topics[topic]['count'] += 1
                        else:
                            topics[topic] = {
                                'score': pref.get('confidence', 0.5),
                                'count': 1,
                                'source': 'preference'
                            }
            
            # Format and normalize scores
            result = []
            for topic, data in topics.items():
                avg_score = data['score'] / data['count'] if data['count'] > 0 else 0
                result.append({
                    'topic': topic,
                    'interest_score': min(1.0, avg_score),
                    'observations': data['count'],
                    'source': data['source']
                })
            
            # Sort by interest score and return
            return sorted(result, key=lambda x: x.get('interest_score', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Error retrieving user topics: {str(e)}")
            return []
            
    def _load_state(self) -> None:
        """Load the state of all learning components if available."""
        try:
            pattern_path = os.path.join(self.learning_dir, "pattern_detector.json")
            preference_path = os.path.join(self.learning_dir, "preference_tracker.json")
            
            # Load states if files exist
            if os.path.exists(pattern_path):
                self.pattern_detector.load_state(pattern_path)
                
            if os.path.exists(preference_path):
                self.preference_tracker.load_state(preference_path)
    
            logger.info("Learning system state loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load learning system state: {str(e)}")
            
            
# Create a singleton instance
learning_integration = LearningIntegration()
