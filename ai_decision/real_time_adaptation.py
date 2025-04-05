"""
Real-Time Adaptation Engine

This module provides real-time feedback injection and dynamic response adaptation
based on user engagement signals and conversation context.
"""

import os
import sys
import json
import time
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix import paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from users.feedback_analysis import feedback_analyzer
from users.adaptive_response_optimizer import response_optimizer
from memory.real_time_memory_manager import real_time_memory_manager
from ai_decision.context_decision_tree import decision_tree

class EngagementSignal:
    """Model for user engagement signals."""
    
    def __init__(self, 
                 signal_type: str, 
                 value: Any, 
                 timestamp: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an engagement signal.
        
        Args:
            signal_type: Type of signal (e.g., message_length, expansion_click)
            value: Signal value
            timestamp: When the signal was recorded
            metadata: Additional signal metadata
        """
        self.signal_type = signal_type
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}


class RealTimeAdaptationEngine:
    """
    Real-time adaptation engine for dynamically adjusting responses
    based on user engagement signals and feedback.
    """
    
    def __init__(self):
        """Initialize the real-time adaptation engine."""
        # Maximum number of signals to keep per user/type
        self.max_signals = 50
        
        # Signal history by user and type
        self.signal_history = defaultdict(lambda: defaultdict(deque))
        
        # Adaptation rules and patterns
        self.adaptation_rules = {
            "message_length": {
                "increasing": {
                    "pattern": [("message_length", "increasing", 3)],
                    "adaptation": {"length": "longer"}
                },
                "decreasing": {
                    "pattern": [("message_length", "decreasing", 3)],
                    "adaptation": {"length": "shorter"}
                }
            },
            "expansion_clicks": {
                "frequent": {
                    "pattern": [("expansion_click", True, 2)],
                    "adaptation": {"length": "longer", "detail_level": "detailed"}
                }
            },
            "follow_up_questions": {
                "repeated": {
                    "pattern": [("follow_up_question", "related", 2)],
                    "adaptation": {"detail_level": "detailed"}
                }
            }
        }
        
        # Active adaptations by user
        self.active_adaptations = defaultdict(dict)
        
        # In-flight response adaptations
        self.in_flight_adaptations = {}
        
        # Reference to memory manager
        self.memory_manager = real_time_memory_manager
        
        logger.info("Real-Time Adaptation Engine initialized")
    
    def record_signal(self, user_id: str, signal: EngagementSignal):
        """
        Record a new engagement signal for a user.
        
        Args:
            user_id: User ID
            signal: The engagement signal to record
        """
        # Add signal to history
        signal_queue = self.signal_history[user_id][signal.signal_type]
        
        # Check if queue is at max capacity
        if len(signal_queue) >= self.max_signals:
            signal_queue.popleft()  # Remove oldest signal
            
        signal_queue.append(signal)
        
        # Check if this signal should trigger an adaptation
        self.check_for_adaptations(user_id)
        
        logger.info(f"Recorded {signal.signal_type} signal for user {user_id}")
    
    def check_for_adaptations(self, user_id: str):
        """
        Check if recent signals match any adaptation patterns.
        
        Args:
            user_id: User ID to check signals for
        """
        # Check each adaptation rule
        for category, rules in self.adaptation_rules.items():
            for rule_name, rule_config in rules.items():
                if self._pattern_matches(user_id, rule_config["pattern"]):
                    # Pattern matches, apply adaptation
                    for param, value in rule_config["adaptation"].items():
                        self.active_adaptations[user_id][param] = value
                    
                    logger.info(f"Applied adaptation for user {user_id}: {rule_config['adaptation']}")
    
    def _pattern_matches(self, user_id: str, pattern) -> bool:
        """Check if user signals match a specific pattern."""
        for signal_type, trend, count in pattern:
            signals = list(self.signal_history[user_id][signal_type])
            
            if len(signals) < count:
                return False
                
            # Get the most recent signals
            recent_signals = signals[-count:]
            
            # Check for specific trends
            if trend == "increasing":
                # Check if values are increasing
                values = [s.value for s in recent_signals if isinstance(s.value, (int, float))]
                if len(values) < count or not all(values[i] <= values[i+1] for i in range(len(values)-1)):
                    return False
            
            elif trend == "decreasing":
                # Check if values are decreasing
                values = [s.value for s in recent_signals if isinstance(s.value, (int, float))]
                if len(values) < count or not all(values[i] >= values[i+1] for i in range(len(values)-1)):
                    return False
            
            elif trend == "related":
                # For follow-up questions, check if they're related
                # This would require more sophisticated analysis
                pass
            
            elif isinstance(trend, bool):
                # Check if last count signals all have the same boolean value
                values = [s.value for s in recent_signals]
                if not all(v == trend for v in values):
                    return False
        
        return True
    
    def get_adaptations(self, user_id: str) -> Dict[str, Any]:
        """
        Get current adaptations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of active adaptations
        """
        return self.active_adaptations.get(user_id, {})
    
    def start_response_adaptation(self, user_id: str, message_id: str, 
                                 original_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start real-time adaptation for a response.
        
        Args:
            user_id: User ID
            message_id: Message ID
            original_context: Original context parameters
            
        Returns:
            Adapted context parameters
        """
        # Create a deep copy of original context
        adapted_context = {**original_context}
        
        # Apply any active adaptations for this user
        user_adaptations = self.get_adaptations(user_id)
        adapted_context.update(user_adaptations)
        
        # Store in-flight adaptation for later reference
        self.in_flight_adaptations[message_id] = {
            "user_id": user_id,
            "original_context": original_context,
            "adapted_context": adapted_context,
            "start_time": datetime.now()
        }
        
        logger.info(f"Started response adaptation for message {message_id} with context: {adapted_context}")
        
        return adapted_context
    
    def inject_feedback(self, message_id: str, feedback_type: str, feedback_value: Any) -> Dict[str, Any]:
        """
        Inject real-time feedback into an in-flight adaptation.
        
        Args:
            message_id: Message ID
            feedback_type: Type of feedback
            feedback_value: Feedback value
            
        Returns:
            Updated adaptation context or None if message not found
        """
        if message_id not in self.in_flight_adaptations:
            logger.warning(f"No in-flight adaptation found for message {message_id}")
            return {}
        
        adaptation = self.in_flight_adaptations[message_id]
        
        # Add feedback to adapted context
        if "feedback" not in adaptation["adapted_context"]:
            adaptation["adapted_context"]["feedback"] = {}
            
        adaptation["adapted_context"]["feedback"][feedback_type] = feedback_value
        
        # Update in-flight adaptation
        self.in_flight_adaptations[message_id] = adaptation
        
        logger.info(f"Injected {feedback_type} feedback into adaptation for message {message_id}")
        
        return adaptation["adapted_context"]
    
    def complete_adaptation(self, message_id: str, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete an in-flight adaptation and record results.
        
        Args:
            message_id: Message ID
            result: Optional results data
            
        Returns:
            Completed adaptation data or empty dict if not found
        """
        if message_id not in self.in_flight_adaptations:
            logger.warning(f"No in-flight adaptation found for message {message_id}")
            return {}
        
        adaptation = self.in_flight_adaptations[message_id]
        
        # Add completion info
        adaptation["end_time"] = datetime.now()
        adaptation["duration"] = (adaptation["end_time"] - adaptation["start_time"]).total_seconds()
        
        if result:
            adaptation["result"] = result
        
        # Record insights to memory
        user_id = adaptation["user_id"]
        self._record_adaptation_insights(user_id, message_id, adaptation)
        
        # Clean up in-flight adaptation
        del self.in_flight_adaptations[message_id]
        
        logger.info(f"Completed adaptation for message {message_id}")
        
        return adaptation
    
    def _record_adaptation_insights(self, user_id: str, message_id: str, adaptation: Dict[str, Any]):
        """
        Record adaptation insights to memory.
        
        Args:
            user_id: User ID
            message_id: Message ID
            adaptation: Adaptation data
        """
        # Extract changes made by adaptation
        changes = {}
        original = adaptation["original_context"]
        adapted = adaptation["adapted_context"]
        
        for key, value in adapted.items():
            if key not in original or original[key] != value:
                changes[key] = value
        
        # Only record if we actually made changes
        if changes:
            # Create a summary of changes
            change_summary = ", ".join(f"{k}={v}" for k, v in changes.items())
            
            # Record to memory
            self.memory_manager.add_memory_with_context(
                content=f"Adapted response with: {change_summary}",
                source="adaptation_engine",
                category="adaptation",
                context=f"user:{user_id}",
                importance=3,
                tags=["adaptation", "response_adjustment"],
                metadata={
                    "message_id": message_id,
                    "changes": changes,
                    "adaptation_data": adaptation
                }
            )
    
    def sync_to_multi_ai(self, user_id: str, model_names: List[str]):
        """
        Synchronize user adaptations to multiple AI models.
        
        Args:
            user_id: User ID
            model_names: List of model names to sync to
        """
        # Get current adaptations
        adaptations = self.get_adaptations(user_id)
        
        if not adaptations:
            return
        
        # Create context data from adaptations
        context_data = {
            "adaptations": adaptations,
            "last_updated": datetime.now().isoformat()
        }
        
        # Set context for each model
        for model_name in model_names:
            self.memory_manager.set_model_context(model_name, context_data)
        
        logger.info(f"Synchronized adaptations for user {user_id} to models: {model_names}")


# Create a singleton instance
adaptation_engine = RealTimeAdaptationEngine()


def test_real_time_adaptation():
    """Test the RealTimeAdaptationEngine functionality."""
    print("\nTesting Real-Time Adaptation Engine...\n")
    
    user_id = "test_user_1"
    
    # Test recording signals
    print("Recording engagement signals...")
    
    # Record increasing message length signals
    adaptation_engine.record_signal(user_id, EngagementSignal(
        signal_type="message_length",
        value=50
    ))
    
    adaptation_engine.record_signal(user_id, EngagementSignal(
        signal_type="message_length",
        value=75
    ))
    
    adaptation_engine.record_signal(user_id, EngagementSignal(
        signal_type="message_length",
        value=120
    ))
    
    # Check adaptations
    adaptations = adaptation_engine.get_adaptations(user_id)
    print(f"Active adaptations after message length signals: {adaptations}")
    
    # Test response adaptation
    message_id = f"msg_{int(time.time())}"
    
    original_context = {
        "length": "standard",
        "tone": "neutral",
        "detail_level": "balanced"
    }
    
    print("\nStarting response adaptation...")
    adapted_context = adaptation_engine.start_response_adaptation(
        user_id=user_id,
        message_id=message_id,
        original_context=original_context
    )
    
    print(f"Adapted context: {adapted_context}")
    
    # Test feedback injection
    print("\nInjecting real-time feedback...")
    updated_context = adaptation_engine.inject_feedback(
        message_id=message_id,
        feedback_type="expansion_request",
        feedback_value=True
    )
    
    print(f"Context after feedback injection: {updated_context}")
    
    # Test completing adaptation
    print("\nCompleting adaptation...")
    result = {
        "response_accepted": True,
        "user_satisfaction": "high"
    }
    
    completed = adaptation_engine.complete_adaptation(
        message_id=message_id,
        result=result
    )
    
    print(f"Adaptation duration: {completed.get('duration', 0):.2f} seconds")
    
    # Test multi-AI synchronization
    print("\nSynchronizing to multiple AI models...")
    adaptation_engine.sync_to_multi_ai(
        user_id=user_id,
        model_names=["claude", "gpt", "bard"]
    )
    
    # Check memory for recorded insights
    print("\nChecking memory for adaptation insights...")
    memories = real_time_memory_manager.get_relevant_context_memories(f"user:{user_id}")
    
    for i, memory in enumerate(memories, 1):
        print(f"  {i}. {memory.content}")
    
    print("\nReal-Time Adaptation Engine tests completed!")


if __name__ == "__main__":
    test_real_time_adaptation()
