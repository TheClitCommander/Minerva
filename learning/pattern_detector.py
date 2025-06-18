"""
Pattern Detector Module

This module provides functionality to detect patterns in user interactions,
including recurring topics, frequently asked questions, and common themes.
It uses natural language processing to identify topics and tracks their
frequency and confidence over time.

The PatternDetector class maintains an internal record of detected patterns
and can suggest high-confidence patterns for storage in Minerva's memory system.
"""

import re
import time
import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatternDetector:
    """
    Detects recurring patterns in user interactions and learns from them.
    
    This class analyzes user messages to identify topics, tracks their frequency,
    and builds confidence scores based on repetition and context. It implements
    threshold-based learning to avoid storing one-off mentions.
    """
    
    def __init__(self, 
                 confidence_threshold: float = 0.85,
                 min_occurrences: int = 3,
                 max_patterns: int = 100,
                 decay_factor: float = 0.95):
        """
        Initialize the pattern detector with configuration parameters.
        
        Args:
            confidence_threshold: Minimum confidence required to consider a pattern valid
            min_occurrences: Minimum number of occurrences before a pattern is considered
            max_patterns: Maximum number of patterns to track
            decay_factor: Factor to decay old pattern scores over time
        """
        self.confidence_threshold = confidence_threshold
        self.min_occurrences = min_occurrences
        self.max_patterns = max_patterns
        self.decay_factor = decay_factor
        
        # Pattern storage: {topic_key: {occurrences, last_seen, confidence, examples}}
        self.patterns = {}
        
        # Simple keyword-based topic detection (would be replaced with more sophisticated NLP)
        self.topic_keywords = {
            "coding": ["code", "programming", "function", "algorithm", "developer"],
            "finance": ["money", "invest", "finance", "budget", "stock"],
            "health": ["health", "exercise", "diet", "workout", "nutrition"],
            "technology": ["tech", "computer", "software", "hardware", "device"],
            "science": ["science", "physics", "chemistry", "biology", "experiment"]
            # Add more topics as needed
        }
        
        logger.info(f"PatternDetector initialized with threshold={confidence_threshold}, "
                   f"min_occurrences={min_occurrences}")
    
    def detect_topics(self, text: str) -> List[str]:
        """
        Detect topics in a text using simple keyword matching.
        
        Args:
            text: User message or query
            
        Returns:
            List of detected topics
        """
        text_lower = text.lower()
        detected_topics = []
        
        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    detected_topics.append(topic)
                    break
        
        return list(set(detected_topics))  # Remove duplicates
    
    def process_message(self, message: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Process a user message to detect and update patterns.
        
        Args:
            message: The user's message
            user_id: Optional user identifier for personalized patterns
            
        Returns:
            Dict with detected patterns and their confidence scores
        """
        # Apply periodic decay to existing patterns
        self._apply_decay()
        
        # Extract topics from message
        topics = self.detect_topics(message)
        
        # Process each detected topic
        detected_patterns = {}
        for topic in topics:
            topic_key = f"{user_id}:{topic}"
            
            # Initialize if this is a new topic
            if topic_key not in self.patterns:
                self.patterns[topic_key] = {
                    "topic": topic,
                    "occurrences": 0,
                    "first_seen": time.time(),
                    "last_seen": time.time(),
                    "confidence": 0.0,
                    "examples": []
                }
            
            # Update pattern data
            pattern = self.patterns[topic_key]
            pattern["occurrences"] += 1
            pattern["last_seen"] = time.time()
            
            # Store example (up to 5 examples)
            if len(pattern["examples"]) < 5:
                pattern["examples"].append(message[:100])  # Truncate long messages
            
            # Calculate confidence based on occurrences and time factors
            time_factor = min(1.0, (time.time() - pattern["first_seen"]) / (3600 * 24))  # Scale up over 24 hours
            occurrence_factor = min(1.0, pattern["occurrences"] / self.min_occurrences)
            pattern["confidence"] = 0.3 + (0.7 * occurrence_factor * time_factor)
            
            # Add to detected patterns if confidence is sufficient
            if pattern["confidence"] > 0.5:  # Lower threshold for detection vs. learning
                detected_patterns[topic] = {
                    "confidence": pattern["confidence"],
                    "occurrences": pattern["occurrences"]
                }
        
        # Prune patterns if we exceed the maximum
        if len(self.patterns) > self.max_patterns:
            self._prune_patterns()
            
        return detected_patterns
    
    def get_learnable_patterns(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """
        Get patterns that exceed the confidence threshold and minimum occurrences
        for learning and storage in the memory system.
        
        Args:
            user_id: Optional user identifier for personalized patterns
            
        Returns:
            List of patterns that should be learned
        """
        learnable = []
        
        for pattern_key, pattern in self.patterns.items():
            if (pattern_key.startswith(f"{user_id}:") and 
                pattern["confidence"] >= self.confidence_threshold and
                pattern["occurrences"] >= self.min_occurrences):
                
                learnable.append({
                    "topic": pattern["topic"],
                    "confidence": pattern["confidence"],
                    "occurrences": pattern["occurrences"],
                    "examples": pattern["examples"],
                    "last_seen": pattern["last_seen"]
                })
                
        return sorted(learnable, key=lambda x: x["confidence"], reverse=True)
    
    def clear_pattern(self, topic: str, user_id: str = "default") -> bool:
        """
        Clear a specific pattern from tracking.
        
        Args:
            topic: The topic to clear
            user_id: Optional user identifier
            
        Returns:
            True if pattern was found and cleared, False otherwise
        """
        pattern_key = f"{user_id}:{topic}"
        if pattern_key in self.patterns:
            del self.patterns[pattern_key]
            return True
        return False
    
    def clear_all_patterns(self, user_id: str = "default") -> int:
        """
        Clear all patterns for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of patterns cleared
        """
        pattern_keys = [k for k in self.patterns.keys() if k.startswith(f"{user_id}:")]
        for key in pattern_keys:
            del self.patterns[key]
        return len(pattern_keys)
    
    def _apply_decay(self) -> None:
        """Apply time-based decay to pattern confidence scores."""
        current_time = time.time()
        for pattern in self.patterns.values():
            # Calculate days since last seen
            days_since = (current_time - pattern["last_seen"]) / (3600 * 24)
            
            # Apply decay if pattern hasn't been seen in over a day
            if days_since > 1:
                decay = self.decay_factor ** int(days_since)
                pattern["confidence"] *= decay
    
    def _prune_patterns(self) -> None:
        """Remove lowest confidence patterns when we exceed the maximum."""
        if len(self.patterns) <= self.max_patterns:
            return
            
        # Sort patterns by confidence
        sorted_patterns = sorted(
            self.patterns.items(), 
            key=lambda x: x[1]["confidence"]
        )
        
        # Remove patterns with lowest confidence
        patterns_to_remove = len(self.patterns) - self.max_patterns
        for i in range(patterns_to_remove):
            del self.patterns[sorted_patterns[i][0]]
            
        logger.info(f"Pruned {patterns_to_remove} low-confidence patterns")
    
    def save_state(self, filepath: str) -> bool:
        """
        Save the current pattern state to a file.
        
        Args:
            filepath: Path to save the state
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.patterns, f)
            return True
        except Exception as e:
            logger.error(f"Failed to save pattern state: {str(e)}")
            return False
    
    def load_state(self, filepath: str) -> bool:
        """
        Load pattern state from a file.
        
        Args:
            filepath: Path to load the state from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                self.patterns = json.load(f)
            return True
        except Exception as e:
            logger.error(f"Failed to load pattern state: {str(e)}")
            return False
