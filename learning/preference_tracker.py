"""
Preference Tracker Module

This module provides functionality to detect and track user preferences,
both explicit (directly stated) and implicit (inferred from behavior).
It implements confidence scoring to ensure reliable preference learning
and integrates with Minerva's memory system for long-term storage.
"""

import re
import time
import logging
import json
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PreferenceTracker:
    """
    Detects and tracks user preferences from explicit statements and implicit behavior.
    
    This class identifies preferences using linguistic pattern matching and behavioral
    analysis, tracks their confidence scores, and provides mechanisms to store
    validated preferences in Minerva's memory system.
    """
    
    def __init__(self, 
                 explicit_threshold: float = 0.9,
                 implicit_threshold: float = 0.85,
                 min_observations: int = 3,
                 max_preferences: int = 200):
        """
        Initialize the preference tracker with configuration parameters.
        
        Args:
            explicit_threshold: Confidence threshold for explicitly stated preferences
            implicit_threshold: Confidence threshold for implicitly inferred preferences
            min_observations: Minimum observations before considering implicit preferences
            max_preferences: Maximum number of preferences to track per user
        """
        self.explicit_threshold = explicit_threshold
        self.implicit_threshold = implicit_threshold
        self.min_observations = min_observations
        self.max_preferences = max_preferences
        
        # Preference storage: {user_id: {preference_key: {value, confidence, source, etc}}}
        self.preferences = defaultdict(dict)
        
        # Explicit preference detection patterns
        self.explicit_patterns = [
            # "I prefer X" patterns
            r"I prefer (?P<value>[^.,;!?]+)",
            r"I like (?P<value>[^.,;!?]+)",
            r"I enjoy (?P<value>[^.,;!?]+)",
            r"I love (?P<value>[^.,;!?]+)",
            
            # "I don't like X" patterns
            r"I (don't|do not|dislike|hate) (?P<value>[^.,;!?]+)",
            
            # "My favorite X is Y" patterns
            r"[Mm]y favorite (?P<category>[^.,;!?]+) (is|are) (?P<value>[^.,;!?]+)",
            
            # "I want X" patterns
            r"I want (?P<value>[^.,;!?]+)",
            r"I need (?P<value>[^.,;!?]+)",
            
            # Settings/mode preferences
            r"I (prefer|like|want) (?P<category>dark|light) mode",
            r"I (prefer|like|want) (?P<value>[^.,;!?]+) (setting|option|configuration)"
        ]
        
        self.explicit_patterns = [re.compile(p, re.IGNORECASE) for p in self.explicit_patterns]
        
        logger.info(f"PreferenceTracker initialized with explicit_threshold={explicit_threshold}, "
                   f"implicit_threshold={implicit_threshold}")
    
    def detect_explicit_preferences(self, message: str) -> List[Dict[str, Any]]:
        """
        Detect explicitly stated preferences in a user message.
        
        Args:
            message: User message text
            
        Returns:
            List of detected preference dictionaries
        """
        detected_preferences = []
        
        for pattern in self.explicit_patterns:
            matches = pattern.finditer(message)
            for match in matches:
                preference = {}
                
                # Extract the value (required)
                if 'value' in match.groupdict():
                    preference['value'] = match.group('value').strip()
                else:
                    continue  # Skip if no value found
                
                # Extract category if available
                if 'category' in match.groupdict() and match.group('category'):
                    preference['category'] = match.group('category').strip()
                else:
                    # Try to infer category from context
                    preference['category'] = self._infer_category(preference['value'], message)
                
                # Determine if this is a positive or negative preference
                if any(neg in match.group(0).lower() for neg in ["don't", "do not", "dislike", "hate"]):
                    preference['sentiment'] = 'negative'
                else:
                    preference['sentiment'] = 'positive'
                
                # Add metadata
                preference['confidence'] = 0.95  # High confidence for explicit statements
                preference['source'] = 'explicit'
                preference['timestamp'] = time.time()
                preference['context'] = message[:100] + "..." if len(message) > 100 else message
                
                # Generate a unique key
                category = preference.get('category', 'general')
                value = preference['value']
                preference['key'] = f"{category}:{value}"
                
                detected_preferences.append(preference)
        
        return detected_preferences
    
    def track_implicit_preference(self, 
                                 topic: str, 
                                 user_id: str, 
                                 context: str,
                                 strength: float = 0.2) -> Dict[str, Any]:
        """
        Track an implicitly inferred preference based on user behavior.
        
        Args:
            topic: The topic or item the user has shown interest in
            user_id: User identifier
            context: Context in which the preference was inferred
            strength: Strength of the signal (0.0-1.0)
            
        Returns:
            Updated preference data
        """
        # Generate a preference key
        preference_key = f"interest:{topic}"
        
        # Initialize if this is a new preference
        if preference_key not in self.preferences[user_id]:
            self.preferences[user_id][preference_key] = {
                'key': preference_key,
                'category': 'interest',
                'value': topic,
                'sentiment': 'positive',
                'observations': 0,
                'first_observed': time.time(),
                'last_observed': time.time(),
                'confidence': 0.0,
                'source': 'implicit',
                'contexts': []
            }
        
        # Update preference data
        preference = self.preferences[user_id][preference_key]
        preference['observations'] += 1
        preference['last_observed'] = time.time()
        
        # Update confidence based on number of observations and time span
        time_factor = min(1.0, (time.time() - preference['first_observed']) / (3600 * 24 * 7))  # Scale up over 7 days
        observation_factor = min(1.0, preference['observations'] / self.min_observations)
        preference['confidence'] = 0.3 + (0.6 * observation_factor * time_factor)
        
        # Store context sample (up to 5)
        if len(preference['contexts']) < 5 and context:
            preference['contexts'].append(context[:100] + "..." if len(context) > 100 else context)
        
        # Prune preferences if we exceed the maximum
        if len(self.preferences[user_id]) > self.max_preferences:
            self._prune_preferences(user_id)
            
        return preference
    
    def update_preference(self, 
                         user_id: str, 
                         preference_key: str, 
                         confidence_delta: float,
                         context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Update the confidence of an existing preference.
        
        Args:
            user_id: User identifier
            preference_key: Key of the preference to update
            confidence_delta: Change in confidence (-1.0 to 1.0)
            context: Optional context for the update
            
        Returns:
            Updated preference data or None if not found
        """
        if preference_key not in self.preferences[user_id]:
            return None
            
        preference = self.preferences[user_id][preference_key]
        
        # Update confidence, keeping it within 0.0-1.0 range
        preference['confidence'] = max(0.0, min(1.0, preference['confidence'] + confidence_delta))
        
        # Add confirmation context if provided
        if context and len(preference.get('contexts', [])) < 5:
            preference['contexts'].append(context[:100] + "..." if len(context) > 100 else context)
            
        preference['last_observed'] = time.time()
        
        return preference
    
    def get_learnable_preferences(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get preferences that exceed the confidence threshold for learning.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of preferences that should be learned
        """
        learnable = []
        
        for preference in self.preferences[user_id].values():
            # Check if preference meets threshold criteria
            if ((preference['source'] == 'explicit' and 
                 preference['confidence'] >= self.explicit_threshold) or
                (preference['source'] == 'implicit' and 
                 preference['confidence'] >= self.implicit_threshold and
                 preference.get('observations', 0) >= self.min_observations)):
                
                learnable.append(preference)
                
        return sorted(learnable, key=lambda x: x['confidence'], reverse=True)
    
    def clear_preference(self, user_id: str, preference_key: str) -> bool:
        """
        Clear a specific preference from tracking.
        
        Args:
            user_id: User identifier
            preference_key: Key of the preference to clear
            
        Returns:
            True if preference was found and cleared, False otherwise
        """
        if preference_key in self.preferences[user_id]:
            del self.preferences[user_id][preference_key]
            return True
        return False
    
    def process_message(self, message: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Process a user message to detect preferences and update tracking.
        
        Args:
            message: User message text
            user_id: User identifier
            
        Returns:
            Dictionary of detected preferences
        """
        results = {
            'explicit_preferences': [],
            'implicit_preferences': []
        }
        
        # Detect explicit preferences
        explicit_prefs = self.detect_explicit_preferences(message)
        
        # Update our tracking for each detected preference
        for pref in explicit_prefs:
            pref_key = pref['key']
            
            # If this preference already exists, update it
            if pref_key in self.preferences[user_id]:
                # Existing preference - update with higher confidence
                self.update_preference(
                    user_id, 
                    pref_key, 
                    confidence_delta=0.1,  # Increase confidence incrementally
                    context=message
                )
            else:
                # New preference - add it to tracking
                self.preferences[user_id][pref_key] = pref
            
            results['explicit_preferences'].append(pref)
            
        return results
    
    def _infer_category(self, value: str, context: str) -> str:
        """
        Attempt to infer a preference category from context.
        
        Args:
            value: The preference value
            context: The message context
            
        Returns:
            Inferred category or 'general' if none can be determined
        """
        # Simple category inference based on keywords
        # This would be replaced with more sophisticated NLP in production
        
        context_lower = context.lower()
        value_lower = value.lower()
        
        category_keywords = {
            'ui': ['interface', 'ui', 'design', 'theme', 'mode', 'dark', 'light', 'color'],
            'programming': ['code', 'programming', 'language', 'framework', 'library'],
            'communication': ['writing', 'tone', 'style', 'formality', 'communication'],
            'content': ['content', 'information', 'detail', 'brevity', 'format'],
            'schedule': ['time', 'schedule', 'appointment', 'meeting', 'reminder']
        }
        
        for category, keywords in category_keywords.items():
            # Check if value contains category keywords
            if any(kw in value_lower for kw in keywords):
                return category
                
            # Check if surrounding context contains category keywords
            context_matches = sum(1 for kw in keywords if kw in context_lower)
            if context_matches >= 2:  # Require at least 2 matches for confidence
                return category
                
        return 'general'
    
    def _prune_preferences(self, user_id: str) -> None:
        """
        Remove lowest confidence preferences when we exceed the maximum.
        
        Args:
            user_id: User identifier
        """
        if len(self.preferences[user_id]) <= self.max_preferences:
            return
            
        # Sort preferences by confidence
        sorted_prefs = sorted(
            self.preferences[user_id].items(), 
            key=lambda x: x[1].get('confidence', 0)
        )
        
        # Remove preferences with lowest confidence
        prefs_to_remove = len(self.preferences[user_id]) - self.max_preferences
        for i in range(prefs_to_remove):
            del self.preferences[user_id][sorted_prefs[i][0]]
            
        logger.info(f"Pruned {prefs_to_remove} low-confidence preferences for user {user_id}")
    
    def save_state(self, filepath: str) -> bool:
        """
        Save the current preference state to a file.
        
        Args:
            filepath: Path to save the state
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(dict(self.preferences), f)
            return True
        except Exception as e:
            logger.error(f"Failed to save preference state: {str(e)}")
            return False
    
    def load_state(self, filepath: str) -> bool:
        """
        Load preference state from a file.
        
        Args:
            filepath: Path to load the state from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                loaded_prefs = json.load(f)
                self.preferences = defaultdict(dict)
                
                # Convert back to defaultdict
                for user_id, prefs in loaded_prefs.items():
                    self.preferences[user_id] = prefs
                    
            return True
        except Exception as e:
            logger.error(f"Failed to load preference state: {str(e)}")
            return False
