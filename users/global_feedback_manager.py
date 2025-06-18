"""
Global Feedback Manager

This module manages the centralized collection, storage, and distribution of user feedback across
all AI components in Minerva. It ensures that feedback and preferences are synchronized
across all AI instances in real-time.
"""

import os
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from pathlib import Path
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import path fix
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock for UserPreferenceManager - this would normally be imported
class UserPreferenceManager:
    """Mock implementation of UserPreferenceManager for testing"""
    
    def __init__(self, preferences_dir=None):
        self.preferences = {}
    
    def get_user_preferences(self, user_id):
        if user_id not in self.preferences:
            self.preferences[user_id] = {
                'retrieval_depth': 'standard',
                'response_tone': 'neutral',
                'response_structure': 'paragraph',
                'response_length': 'medium'
            }
        return self.preferences[user_id]
    
    def record_feedback(self, user_id, message_id, is_positive, feedback_type):
        return True
    
    def set_retrieval_depth(self, user_id, value):
        self.get_user_preferences(user_id)['retrieval_depth'] = value
        return True
    
    def set_response_tone(self, user_id, value):
        self.get_user_preferences(user_id)['response_tone'] = value
        return True
    
    def set_response_structure(self, user_id, value):
        self.get_user_preferences(user_id)['response_structure'] = value
        return True
    
    def set_response_length(self, user_id, value):
        self.get_user_preferences(user_id)['response_length'] = value
        return True
    
    def set_user_preference(self, user_id, preference_type, value):
        self.get_user_preferences(user_id)[preference_type] = value
        return True

class GlobalFeedbackManager:
    """
    Centralized manager for collecting, distributing, and synchronizing feedback across AI components.
    Handles preference updates and ensures all AI models have consistent user preference information.
    """
    
    def __init__(self, preferences_dir: Optional[Path] = None):
        """
        Initialize the global feedback manager.
        
        Args:
            preferences_dir: Directory to store feedback and preference data
        """
        # Initialize the user preference manager for backend storage
        self.user_preference_manager = UserPreferenceManager(preferences_dir)
        
        # Cache for active AI instances
        self.ai_instances = set()
        
        # In-memory notification queue for real-time updates
        self.update_queue = queue.Queue()
        
        # Flag to indicate if the update thread is running
        self.is_running = False
        
        # Thread for handling async updates
        self.update_thread = None
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Start the update distribution thread
        self.start_update_thread()
    
    def start_update_thread(self) -> None:
        """Start the background thread for distributing updates."""
        if not self.is_running:
            self.is_running = True
            self.update_thread = threading.Thread(
                target=self._process_updates,
                daemon=True
            )
            self.update_thread.start()
            logger.info("Global feedback update thread started")
    
    def stop_update_thread(self) -> None:
        """Stop the background update thread."""
        if self.is_running:
            self.is_running = False
            if self.update_thread:
                self.update_thread.join(timeout=2.0)
            logger.info("Global feedback update thread stopped")
    
    def _process_updates(self) -> None:
        """Background thread that processes preference updates and distributes them."""
        while self.is_running:
            try:
                # Get the next update from the queue (with timeout to allow checking is_running)
                try:
                    update = self.update_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the update
                user_id = update.get('user_id')
                update_type = update.get('type')
                
                if not user_id or not update_type:
                    logger.warning(f"Invalid update format: {update}")
                    continue
                
                logger.info(f"Processing {update_type} update for user {user_id}")
                
                # Distribute the update to all registered AI instances
                # In a real implementation, this would notify AI models
                # For now, we'll just log it
                logger.info(f"Notifying {len(self.ai_instances)} AI instances about update")
                
                # Mark as done
                self.update_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing update: {str(e)}")
                time.sleep(1.0)  # Prevent tight loop in case of persistent errors
    
    def register_ai_instance(self, instance_id: str) -> None:
        """
        Register an AI instance to receive feedback and preference updates.
        
        Args:
            instance_id: Unique identifier for the AI instance
        """
        with self.lock:
            self.ai_instances.add(instance_id)
            logger.info(f"AI instance {instance_id} registered with Global Feedback Manager")
    
    def unregister_ai_instance(self, instance_id: str) -> None:
        """
        Unregister an AI instance from receiving updates.
        
        Args:
            instance_id: Unique identifier for the AI instance
        """
        with self.lock:
            if instance_id in self.ai_instances:
                self.ai_instances.remove(instance_id)
                logger.info(f"AI instance {instance_id} unregistered from Global Feedback Manager")
    
    def record_feedback(self, user_id: str, message_id: str, is_positive: bool, 
                        feedback_type: str = "general", ai_instance_id: Optional[str] = None) -> bool:
        """
        Record user feedback and distribute it to all relevant AI instances.
        
        Args:
            user_id: Unique identifier for the user
            message_id: Identifier for the message being rated
            is_positive: Whether the feedback is positive (True) or negative (False)
            feedback_type: Type of feedback (general, tone, structure, length)
            ai_instance_id: Optional identifier of the AI that generated the response
            
        Returns:
            success: Whether the operation was successful
        """
        try:
            # Record the feedback using the user preference manager
            success = self.user_preference_manager.record_feedback(
                user_id, message_id, is_positive, feedback_type
            )
            
            if not success:
                return False
            
            # Queue the update for distribution
            update = {
                'user_id': user_id, 
                'type': 'feedback',
                'message_id': message_id,
                'is_positive': is_positive,
                'feedback_type': feedback_type,
                'ai_instance_id': ai_instance_id,
                'timestamp': datetime.now().isoformat()
            }
            
            self.update_queue.put(update)
            logger.info(f"Feedback from user {user_id} queued for distribution to AI instances")
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording feedback from user {user_id}: {str(e)}")
            return False
    
    def update_user_preference(self, user_id: str, preference_type: str, value: Any) -> bool:
        """
        Update a user preference and sync it across all AI instances.
        
        Args:
            user_id: Unique identifier for the user
            preference_type: Type of preference (e.g., 'retrieval_depth', 'response_tone')
            value: The preference value to set
            
        Returns:
            success: Whether the operation was successful
        """
        try:
            # Set the preference using the user preference manager
            if preference_type == 'retrieval_depth':
                success = self.user_preference_manager.set_retrieval_depth(user_id, value)
            elif preference_type == 'response_tone':
                success = self.user_preference_manager.set_response_tone(user_id, value)
            elif preference_type == 'response_structure':
                success = self.user_preference_manager.set_response_structure(user_id, value)
            elif preference_type == 'response_length':
                success = self.user_preference_manager.set_response_length(user_id, value)
            else:
                success = self.user_preference_manager.set_user_preference(user_id, preference_type, value)
            
            if not success:
                return False
            
            # Queue the update for distribution
            update = {
                'user_id': user_id,
                'type': 'preference_update',
                'preference_type': preference_type,
                'value': value,
                'timestamp': datetime.now().isoformat()
            }
            
            self.update_queue.put(update)
            logger.info(f"Preference update for user {user_id} queued for distribution to AI instances")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating preference for user {user_id}: {str(e)}")
            return False
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get all preferences for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            preferences: Dictionary of user preferences
        """
        return self.user_preference_manager.get_user_preferences(user_id)
    
    def get_ai_decision_parameters(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Determine parameters for AI model selection and coordination based on user preferences
        and message characteristics.
        
        Args:
            user_id: Unique identifier for the user
            message: The user's message
            
        Returns:
            parameters: Dictionary of decision parameters for AI coordination
        """
        # Get user preferences
        preferences = self.get_user_preferences(user_id)
        
        # Calculate message complexity (simple heuristic)
        complexity = min(10, max(1, len(message.split()) / 20))
        
        # Determine priority level based on retrieval depth and message complexity
        retrieval_depth = preferences.get('retrieval_depth', 'standard')
        if retrieval_depth == 'concise':
            priority = 'fast'
        elif retrieval_depth == 'deep_dive':
            priority = 'comprehensive'
        else:  # standard
            priority = 'balanced'
        
        # For complex queries with deep dive, use all available models
        use_multiple_models = (retrieval_depth == 'deep_dive' and complexity > 5) or complexity > 8
        
        # Return decision parameters
        return {
            'priority': priority,
            'complexity': complexity,
            'use_multiple_models': use_multiple_models,
            'retrieval_depth': retrieval_depth,
            'response_formatting': {
                'tone': preferences.get('response_tone', 'neutral'),
                'structure': preferences.get('response_structure', 'paragraph'),
                'length': preferences.get('response_length', 'medium')
            }
        }


# Create a singleton instance
global_feedback_manager = GlobalFeedbackManager()


def test_global_feedback_manager():
    """Test the GlobalFeedbackManager functionality."""
    # Create a test instance
    manager = GlobalFeedbackManager()
    
    # Test user ID
    test_user = "test_global_user"
    
    # Register mock AI instances
    manager.register_ai_instance("claude-instance-1")
    manager.register_ai_instance("openai-instance-1")
    
    # Update preferences
    print(f"Setting preferences for user {test_user}...")
    manager.update_user_preference(test_user, "retrieval_depth", "deep_dive")
    manager.update_user_preference(test_user, "response_tone", "formal")
    manager.update_user_preference(test_user, "response_structure", "bullet_points")
    
    # Record feedback
    print(f"Recording feedback from user {test_user}...")
    manager.record_feedback(test_user, "msg_123", True, "general", "claude-instance-1")
    manager.record_feedback(test_user, "msg_456", False, "tone", "openai-instance-1")
    
    # Get AI decision parameters
    simple_message = "What time is it?"
    complex_message = "Can you explain the differences between quantum computing and classical computing, including the implications for cryptography and machine learning?"
    
    simple_params = manager.get_ai_decision_parameters(test_user, simple_message)
    complex_params = manager.get_ai_decision_parameters(test_user, complex_message)
    
    print(f"\nAI decision for simple message: {simple_params}")
    print(f"\nAI decision for complex message: {complex_params}")
    
    # Sleep briefly to allow updates to be processed
    time.sleep(2)
    
    # Clean up
    manager.stop_update_thread()
    print("Test completed.")


if __name__ == "__main__":
    test_global_feedback_manager()
