"""
User Preference Manager

This module handles the storage and retrieval of user preferences,
especially for personalized knowledge retrieval depth and response formatting.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any, Literal, List, Union
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Base directory for user preferences storage
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_PREFERENCES_DIR = BASE_DIR / "users" / "preferences"

# Ensure default directories exist
DEFAULT_PREFERENCES_DIR.mkdir(parents=True, exist_ok=True)

# Preference types
RetrievalDepth = Literal["concise", "standard", "deep_dive"]
ResponseTone = Literal["formal", "casual", "neutral"]
ResponseStructure = Literal["paragraph", "bullet_points", "numbered_list", "summary"]
ResponseLength = Literal["short", "medium", "long"]


class UserPreferenceManager:
    """
    Manages user preferences for knowledge retrieval settings and response formatting.
    """
    
    def __init__(self, preferences_dir: Optional[Path] = None):
        """
        Initialize the user preference manager.
        
        Args:
            preferences_dir: Directory to store user preferences
        """
        self.preferences_dir = preferences_dir or DEFAULT_PREFERENCES_DIR
        self.preferences_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of user preferences
        self.user_preferences_cache = {}
        
        # Create feedback directory if it doesn't exist
        self.feedback_dir = self.preferences_dir / "feedback"
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized UserPreferenceManager with preferences_dir={self.preferences_dir}")
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get preferences for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            preferences: Dictionary of user preferences
        """
        # Check if preferences are in memory cache
        if user_id in self.user_preferences_cache:
            return self.user_preferences_cache[user_id]
        
        # Load from file if not in cache
        preferences_file = self.preferences_dir / f"{user_id}.json"
        
        if preferences_file.exists():
            try:
                with open(preferences_file, 'r') as f:
                    preferences = json.load(f)
                    
                    # Add default values if missing
                    if 'retrieval_depth' not in preferences:
                        preferences['retrieval_depth'] = "standard"
                    if 'response_tone' not in preferences:
                        preferences['response_tone'] = "neutral"
                    if 'response_structure' not in preferences:
                        preferences['response_structure'] = "paragraph"
                    if 'response_length' not in preferences:
                        preferences['response_length'] = "medium"
                    if 'feedback' not in preferences:
                        preferences['feedback'] = {
                            'positive_count': 0,
                            'negative_count': 0,
                            'last_adjustments': []
                        }
                    
                    # Update cache
                    self.user_preferences_cache[user_id] = preferences
                    return preferences
            except Exception as e:
                logger.error(f"Error loading preferences for user {user_id}: {str(e)}")
        
        # Return default preferences if file doesn't exist
        default_preferences = {
            'retrieval_depth': "standard",
            'response_tone': "neutral",
            'response_structure': "paragraph",
            'response_length': "medium",
            'feedback': {
                'positive_count': 0,
                'negative_count': 0,
                'last_adjustments': []
            },
            'created_at': datetime.now().isoformat()
        }
        
        # Update cache with defaults
        self.user_preferences_cache[user_id] = default_preferences
        return default_preferences
    
    def set_user_preference(self, user_id: str, key: str, value: Any) -> bool:
        """
        Set a preference for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            key: Preference key
            value: Preference value
            
        Returns:
            success: Whether the operation was successful
        """
        # Get current preferences
        preferences = self.get_user_preferences(user_id)
        
        # Update preference
        preferences[key] = value
        preferences['updated_at'] = datetime.now().isoformat()
        
        # Update cache
        self.user_preferences_cache[user_id] = preferences
        
        # Save to file
        preferences_file = self.preferences_dir / f"{user_id}.json"
        try:
            with open(preferences_file, 'w') as f:
                json.dump(preferences, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving preferences for user {user_id}: {str(e)}")
            return False
    
    def set_retrieval_depth(self, user_id: str, depth: RetrievalDepth) -> bool:
        """
        Set the retrieval depth preference for a user.
        
        Args:
            user_id: Unique identifier for the user
            depth: Retrieval depth (concise, standard, deep_dive)
            
        Returns:
            success: Whether the operation was successful
        """
        # Validate depth
        if depth not in ["concise", "standard", "deep_dive"]:
            logger.warning(f"Invalid retrieval depth: {depth}. Using 'standard' instead.")
            depth = "standard"
        
        return self.set_user_preference(user_id, 'retrieval_depth', depth)
    
    def get_retrieval_depth(self, user_id: str) -> RetrievalDepth:
        """
        Get the retrieval depth preference for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            depth: The retrieval depth preference
        """
        preferences = self.get_user_preferences(user_id)
        return preferences.get('retrieval_depth', "standard")
    
    def set_response_tone(self, user_id: str, tone: ResponseTone) -> bool:
        """
        Set the response tone preference for a user.
        
        Args:
            user_id: Unique identifier for the user
            tone: Response tone (formal, casual, neutral)
            
        Returns:
            success: Whether the operation was successful
        """
        # Validate tone
        if tone not in ["formal", "casual", "neutral"]:
            logger.warning(f"Invalid response tone: {tone}. Using 'neutral' instead.")
            tone = "neutral"
        
        return self.set_user_preference(user_id, 'response_tone', tone)
    
    def get_response_tone(self, user_id: str) -> ResponseTone:
        """
        Get the response tone preference for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            tone: The response tone preference
        """
        preferences = self.get_user_preferences(user_id)
        return preferences.get('response_tone', "neutral")
    
    def set_response_structure(self, user_id: str, structure: ResponseStructure) -> bool:
        """
        Set the response structure preference for a user.
        
        Args:
            user_id: Unique identifier for the user
            structure: Response structure (paragraph, bullet_points, numbered_list, summary)
            
        Returns:
            success: Whether the operation was successful
        """
        # Validate structure
        if structure not in ["paragraph", "bullet_points", "numbered_list", "summary"]:
            logger.warning(f"Invalid response structure: {structure}. Using 'paragraph' instead.")
            structure = "paragraph"
        
        return self.set_user_preference(user_id, 'response_structure', structure)
    
    def get_response_structure(self, user_id: str) -> ResponseStructure:
        """
        Get the response structure preference for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            structure: The response structure preference
        """
        preferences = self.get_user_preferences(user_id)
        return preferences.get('response_structure', "paragraph")
    
    def get_retrieval_params(self, user_id: str) -> Dict[str, Any]:
        """
        Get retrieval parameters based on the user's retrieval depth preference.
        
        Args:
            user_id: User ID to get retrieval parameters for
            
        Returns:
            Dict containing retrieval parameters
        """
        depth = self.get_retrieval_depth(user_id)
        
        # Define parameters for each depth
        if depth == "concise":
            return {
                "max_chunk_count": 2,
                "chunk_limit": 1000,
                "recent_chunk_bonus": 1.2
            }
        elif depth == "deep_dive":
            return {
                "max_chunk_count": 5,
                "chunk_limit": 2500,
                "recent_chunk_bonus": 1.0
            }
        else:  # standard
            return {
                "max_chunk_count": 3,
                "chunk_limit": 1500,
                "recent_chunk_bonus": 1.1
            }
    
    def get_formatting_params(self, user_id: str) -> Dict[str, Any]:
        """
        Get formatting parameters based on the user's preferences for response tone, structure, and length.
        
        Args:
            user_id: User ID to get formatting parameters for
            
        Returns:
            Dict containing formatting parameters
        """
        # Get user preferences
        preferences = self.get_user_preferences(user_id)
        tone = preferences.get('response_tone', 'neutral')
        structure = preferences.get('response_structure', 'paragraph')
        depth = preferences.get('retrieval_depth', 'standard')
        length = preferences.get('response_length', 'medium')
        
        # Tone markers for different tones
        tone_markers = {
            'formal': [
                "Upon analysis",
                "It is important to note that",
                "According to the available information",
                "The data suggests that",
                "Research indicates that"
            ],
            'casual': [
                "Hey there",
                "Just so you know",
                "Here's the thing",
                "I'd say that",
                "Basically"
            ],
            'neutral': [
                "It appears that",
                "Based on the information",
                "I can see that",
                "It seems that",
                "From what I understand"
            ]
        }
        
        # Base parameters
        params = {
            'structure_type': structure,
            'tone_markers': tone_markers.get(tone, []),
            'truncation_enabled': True,
            'response_length': length
        }
        
        # First, adjust parameters based on response length
        length_params = {}
        if length == "short":
            length_params = {
                'max_paragraphs': 1,
                'truncation_length': 300,
                'use_headings': False,
                'intro_style': 'minimal',
                'conclusion': False,
                'section_breaks': False,
                'bullet_count': 3,
                'expand_details': True
            }
        elif length == "long":
            length_params = {
                'max_paragraphs': 5,
                'truncation_length': 1500,
                'use_headings': True,
                'intro_style': 'detailed',
                'conclusion': True,
                'section_breaks': True,
                'bullet_count': 8,
                'expand_details': False
            }
        else:  # medium (default)
            length_params = {
                'max_paragraphs': 3,
                'truncation_length': 800,
                'use_headings': False,
                'intro_style': 'brief',
                'conclusion': True,
                'section_breaks': True,
                'bullet_count': 5,
                'expand_details': True
            }
        
        params.update(length_params)
        
        # Then, adjust parameters based on retrieval depth
        # These adjustments will override length parameters where conflicts exist
        if depth == "concise":
            # For concise mode, reduce length-based parameters
            params.update({
                'max_paragraphs': max(1, params.get('max_paragraphs', 3) - 1),
                'truncation_length': int(params.get('truncation_length', 800) * 0.7),
                'use_headings': False,
                'intro_style': 'minimal',
                'conclusion': False,
                'section_breaks': False,
                'bullet_count': max(2, params.get('bullet_count', 5) - 2)
            })
        elif depth == "deep_dive":
            # For deep dive mode, increase length-based parameters
            params.update({
                'max_paragraphs': params.get('max_paragraphs', 3) + 1,
                'truncation_length': int(params.get('truncation_length', 800) * 1.5),
                'use_headings': True,
                'intro_style': 'detailed',
                'conclusion': True,
                'section_breaks': True,
                'bullet_count': params.get('bullet_count', 5) + 2
            })
        
        return params
    
    def clear_cache(self) -> None:
        """Clear the user preferences cache."""
        self.user_preferences_cache.clear()
        logger.info("User preferences cache cleared")


# For convenience in importing
user_preference_manager = UserPreferenceManager()


def main():
    """Test the UserPreferenceManager with sample data."""
    logging.basicConfig(level=logging.INFO)
    
    # Create manager
    manager = UserPreferenceManager()
    
    # Test user ID
    test_user_id = "test_user_123"
    
    # Test setting and getting preferences
    manager.set_retrieval_depth(test_user_id, "deep_dive")
    manager.set_response_tone(test_user_id, "formal")
    manager.set_response_structure(test_user_id, "bullet_points")
    
    # Get and print preferences
    prefs = manager.get_user_preferences(test_user_id)
    
    # Print retrieval and formatting parameters
    retrieval_params = manager.get_retrieval_params(test_user_id)
    formatting_params = manager.get_formatting_params(test_user_id)
    
    print(f"User Preferences: {prefs}")
    print(f"Retrieval Parameters: {retrieval_params}")
    print(f"Formatting Parameters: {formatting_params}")


    def set_response_length(self, user_id: str, length: ResponseLength) -> bool:
        """
        Set the response length preference for a user.
        
        Args:
            user_id: Unique identifier for the user
            length: Response length (short, medium, long)
            
        Returns:
            success: Whether the operation was successful
        """
        # Validate length
        if length not in ["short", "medium", "long"]:
            logger.warning(f"Invalid response length: {length}. Using 'medium' instead.")
            length = "medium"
        
        return self.set_user_preference(user_id, 'response_length', length)
    
    def get_response_length(self, user_id: str) -> ResponseLength:
        """
        Get the response length preference for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            length: The response length preference
        """
        preferences = self.get_user_preferences(user_id)
        return preferences.get('response_length', "medium")
    
    def record_feedback(self, user_id: str, message_id: str, is_positive: bool, feedback_type: str = "general") -> bool:
        """
        Record user feedback for a response.
        
        Args:
            user_id: Unique identifier for the user
            message_id: Identifier for the message being rated
            is_positive: Whether the feedback is positive (True) or negative (False)
            feedback_type: Type of feedback (general, tone, structure, length)
            
        Returns:
            success: Whether the operation was successful
        """
        try:
            # Get current preferences
            preferences = self.get_user_preferences(user_id)
            
            # Update feedback counts
            if 'feedback' not in preferences:
                preferences['feedback'] = {
                    'positive_count': 0,
                    'negative_count': 0,
                    'last_adjustments': []
                }
            
            if is_positive:
                preferences['feedback']['positive_count'] += 1
            else:
                preferences['feedback']['negative_count'] += 1
            
            # Record feedback details to a separate file for analysis
            feedback_file = self.feedback_dir / f"{user_id}_feedback.json"
            
            feedback_entry = {
                'timestamp': datetime.now().isoformat(),
                'message_id': message_id,
                'is_positive': is_positive,
                'feedback_type': feedback_type,
                'current_preferences': {
                    'retrieval_depth': preferences.get('retrieval_depth'),
                    'response_tone': preferences.get('response_tone'),
                    'response_structure': preferences.get('response_structure'),
                    'response_length': preferences.get('response_length')
                }
            }
            
            # Load existing feedback or create new file
            if feedback_file.exists():
                try:
                    with open(feedback_file, 'r') as f:
                        feedback_data = json.load(f)
                except Exception:
                    feedback_data = {'feedback': []}
            else:
                feedback_data = {'feedback': []}
            
            # Add new feedback and save
            feedback_data['feedback'].append(feedback_entry)
            with open(feedback_file, 'w') as f:
                json.dump(feedback_data, f, indent=2)
            
            # Analyze feedback and potentially adjust preferences automatically
            self._analyze_and_adjust_preferences(user_id, feedback_type, is_positive)
            
            # Update preferences file
            preferences['updated_at'] = datetime.now().isoformat()
            self.user_preferences_cache[user_id] = preferences
            
            preferences_file = self.preferences_dir / f"{user_id}.json"
            with open(preferences_file, 'w') as f:
                json.dump(preferences, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording feedback for user {user_id}: {str(e)}")
            return False
    
    def _analyze_and_adjust_preferences(self, user_id: str, feedback_type: str, is_positive: bool) -> None:
        """
        Analyze recent feedback and adjust preferences if needed.
        
        This implements simple adaptive preference tuning based on feedback patterns.
        
        Args:
            user_id: Unique identifier for the user
            feedback_type: Type of feedback received
            is_positive: Whether the feedback was positive
        """
        try:
            # Get current preferences
            preferences = self.get_user_preferences(user_id)
            feedback = preferences.get('feedback', {})
            
            # Add this adjustment to the history
            if 'last_adjustments' not in feedback:
                feedback['last_adjustments'] = []
                
            # Only keep last 5 adjustments
            if len(feedback['last_adjustments']) >= 5:
                feedback['last_adjustments'].pop(0)
            
            # If negative feedback, consider adjusting the corresponding preference
            if not is_positive:
                adjustment = None
                
                # Adjust based on feedback type
                if feedback_type == "tone":
                    current_tone = preferences.get('response_tone', "neutral")
                    # Simple rotation of tones on negative feedback
                    if current_tone == "formal":
                        adjustment = {"response_tone": "neutral"}
                    elif current_tone == "neutral":
                        adjustment = {"response_tone": "casual"}
                    elif current_tone == "casual":
                        adjustment = {"response_tone": "formal"}
                
                elif feedback_type == "structure":
                    current_structure = preferences.get('response_structure', "paragraph")
                    # Simple rotation of structures on negative feedback
                    if current_structure == "paragraph":
                        adjustment = {"response_structure": "bullet_points"}
                    elif current_structure == "bullet_points":
                        adjustment = {"response_structure": "numbered_list"}
                    elif current_structure == "numbered_list":
                        adjustment = {"response_structure": "summary"}
                    elif current_structure == "summary":
                        adjustment = {"response_structure": "paragraph"}
                
                elif feedback_type == "length":
                    current_length = preferences.get('response_length', "medium")
                    # If current response is too long, make it shorter, and vice versa
                    # We assume negative feedback on 'long' means it's too long, etc.
                    if current_length == "long":
                        adjustment = {"response_length": "medium"}
                    elif current_length == "medium":
                        # More complex logic could be implemented here based on previous feedback
                        # For now, we'll just try the short length
                        adjustment = {"response_length": "short"}
                    elif current_length == "short":
                        adjustment = {"response_length": "medium"}
                
                # Apply the adjustment if any
                if adjustment:
                    for key, value in adjustment.items():
                        self.set_user_preference(user_id, key, value)
                    
                    # Record this adjustment
                    adjustment['timestamp'] = datetime.now().isoformat()
                    adjustment['feedback_type'] = feedback_type
                    adjustment['is_positive'] = is_positive
                    feedback['last_adjustments'].append(adjustment)
                    
                    # Update feedback in preferences
                    preferences['feedback'] = feedback
                    self.user_preferences_cache[user_id] = preferences
                    
                    # Save to file
                    preferences_file = self.preferences_dir / f"{user_id}.json"
                    with open(preferences_file, 'w') as f:
                        json.dump(preferences, f, indent=2)
                    
                    logger.info(f"Automatically adjusted preferences for user {user_id} based on feedback: {adjustment}")
        
        except Exception as e:
            logger.error(f"Error analyzing feedback for user {user_id}: {str(e)}")


# For convenience in importing
user_preference_manager = UserPreferenceManager()


def main():
    """Test the UserPreferenceManager with sample data."""
    # Create a test instance
    manager = UserPreferenceManager()
    
    # Test user ID
    test_user = "test_user_123"
    
    # Set and get retrieval depth
    print(f"Setting retrieval depth to 'deep_dive' for user {test_user}")
    manager.set_retrieval_depth(test_user, "deep_dive")
    
    # Set and get response tone
    print(f"Setting response tone to 'formal' for user {test_user}")
    manager.set_response_tone(test_user, "formal")
    
    # Set and get response structure
    print(f"Setting response structure to 'bullet_points' for user {test_user}")
    manager.set_response_structure(test_user, "bullet_points")
    
    # Set and get response length
    print(f"Setting response length to 'short' for user {test_user}")
    manager.set_response_length(test_user, "short")
    
    # Get all preferences
    preferences = manager.get_user_preferences(test_user)
    print(f"\nUser preferences: {json.dumps(preferences, indent=2)}")
    
    # Get formatting parameters
    formatting_params = manager.get_formatting_params(test_user)
    print(f"\nFormatting parameters: {json.dumps(formatting_params, indent=2)}")
    
    # Record feedback
    print(f"\nRecording positive feedback for user {test_user}")
    manager.record_feedback(test_user, "msg_123", True, "general")
    
    # Record negative feedback
    print(f"\nRecording negative feedback for user {test_user}")
    manager.record_feedback(test_user, "msg_456", False, "tone")
    
    # Get updated preferences
    updated_preferences = manager.get_user_preferences(test_user)
    print(f"\nUpdated user preferences: {json.dumps(updated_preferences, indent=2)}")


if __name__ == "__main__":
    main()
