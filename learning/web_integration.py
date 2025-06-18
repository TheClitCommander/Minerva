"""
Web Integration for Self-Learning System

This module integrates Minerva's self-learning framework with the web interface
and messaging system, enabling real-time learning from user interactions.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import learning components
from learning.learning_integration import LearningIntegration, learning_integration
from learning.pattern_detector import PatternDetector
from learning.preference_tracker import PreferenceTracker

class LearningWebIntegration:
    """
    Integrates the self-learning framework with Minerva's web interface.
    
    This class provides methods to process messages from the web interface,
    learn from user interactions, and generate appropriate responses including
    confirmation prompts when needed. Also provides methods to apply learned context
    to enhance model selection and response quality.
    """
    
    def __init__(self, learning_integration_instance=None):
        """
        Initialize the web integration.
        
        Args:
            learning_integration_instance: Optional instance of LearningIntegration
        """
        # Use provided instance or global singleton
        self.learning = learning_integration_instance or learning_integration
        logger.info("Learning Web Integration initialized")
        
    def process_user_message(self, 
                           message: str, 
                           user_id: str, 
                           session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message for learning opportunities.
        
        Args:
            message: The user's message
            user_id: User identifier
            session_id: Optional session identifier
            
        Returns:
            Dict with learning results and any confirmation requests
        """
        # Process with learning integration
        learning_results = self.learning.process_message(message, user_id, session_id)
        
        # Format confirmation requests if any
        confirmation_requests = []
        
        for req in learning_results.get('confirmation_requests', []):
            confirmation_requests.append({
                'request_id': f"learn_{int(time.time())}",
                'message': self.learning.get_confirmation_message(req),
                'learning_item': req,
                'type': 'learning_confirmation'
            })
            
        return {
            'has_learning_content': bool(learning_results.get('patterns') or 
                                       learning_results.get('preferences')),
            'confirmation_requests': confirmation_requests,
            'patterns_detected': learning_results.get('patterns', {}),
            'preferences_detected': learning_results.get('preferences', {})
        }
        
    def handle_confirmation_response(self, 
                                   confirmation_data: Dict[str, Any], 
                                   confirmed: bool,
                                   user_id: str) -> Dict[str, Any]:
        """
        Handle a user's response to a learning confirmation request.
        
        Args:
            confirmation_data: The confirmation request data
            confirmed: Whether the user confirmed the learning
            user_id: User identifier
            
        Returns:
            Dict with result information
        """
        learning_item = confirmation_data.get('learning_item')
        
        if not learning_item:
            return {'success': False, 'error': 'Invalid confirmation data'}
            
        result = self.learning.handle_confirmation(learning_item, confirmed, user_id)
            
        return {
            'success': True,
            'confirmed': confirmed,
            'memory_created': result is not None,
            'memory_id': result.get('id') if result else None
        }
        
    def enhance_response_with_learning(self, 
                                     response_data: Dict[str, Any],
                                     user_query: str = None, 
                                     user_id: str = None,
                                     learning_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhance Minerva's response with learning data.
        
        This method accepts either a user_query + user_id to process a new message,
        or pre-computed learning_results to directly enhance the response.
        
        Args:
            response_data: The original response data
            user_query: The user's query (optional if learning_results provided)
            user_id: User identifier (optional if learning_results provided)
            learning_results: Pre-computed learning results (optional)
            
        Returns:
            Enhanced response data with learning information
        """
        logger.info(f"Enhancing response with learning data for user {user_id if user_id else 'unknown'}")
        
        try:
            # Either use provided learning results or process the message
            if learning_results is None:
                if not user_query or not user_id:
                    logger.warning("Missing user_query or user_id for learning enhancement")
                    return response_data
                    
                learning_results = self.process_user_message(user_query, user_id)
            
            # Create a copy to avoid modifying the original
            enhanced_response = response_data.copy()
            
            # Add learning information to the response
            if 'metadata' not in enhanced_response:
                enhanced_response['metadata'] = {}
                
            enhanced_response['metadata']['learning'] = {
                'has_learning_content': learning_results.get('has_learning_content', False),
                'confirmation_requests': learning_results.get('confirmation_requests', [])
            }
            
            # If there are confirmation requests, add them to the response actions
            if learning_results.get('confirmation_requests', []):
                if 'actions' not in enhanced_response:
                    enhanced_response['actions'] = []
                    
                for req in learning_results.get('confirmation_requests', []):
                    enhanced_response['actions'].append({
                        'type': 'learning_confirmation',
                        'request_id': req.get('request_id', f"learn_{int(time.time())}"),
                        'message': req.get('message', 'Would you like Minerva to learn from this?'),
                        'data': {
                            'learning_item': req.get('learning_item', {})
                        }
                    })
            
            # Add learning stats
            if 'learning' not in enhanced_response:
                enhanced_response['learning'] = {}
                
            enhanced_response['learning'] = {
                'patterns_detected': len(learning_results.get('patterns_detected', {})),
                'preferences_detected': len(learning_results.get('preferences_detected', {})),
                'confirmation_needed': bool(learning_results.get('confirmation_requests', [])),
                'learning_active': True
            }
            
            logger.info(f"Enhanced response with {len(learning_results.get('confirmation_requests', []))} learning confirmations")
            return enhanced_response
                
        except Exception as e:
            logger.error(f"Error enhancing response with learning: {str(e)}")
            # Return original response if there's an error
            return response_data
        
    def apply_learned_context(self, 
                           user_id: str,
                           user_query: str = None,
                           context_data: Dict[str, Any] = None, 
                           session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve user context information from the learning system and apply it to context data.
        
        This method can either be called with existing context_data to enhance it,
        or without context_data to just retrieve the user context information.
        
        Args:
            user_id: User identifier
            user_query: Optional user query for query-specific context
            context_data: Optional existing context data to enhance
            session_id: Optional session identifier for contextual filtering
            
        Returns:
            Dictionary containing user context information (preferences, patterns, topics)
        """
        logger.info(f"Retrieving learned context for user {user_id}")
        
        try:
            # Initialize context_data if not provided
            if context_data is None:
                context_data = {}
                
            # Initialize user_context if not present
            if 'user_context' not in context_data:
                context_data['user_context'] = {}
            
            # Get user preferences from learning system
            preferences = self.learning.get_user_preferences(user_id)
            if preferences:
                context_data['user_context']['preferences'] = preferences[:10]  # Limit to top 10
                logger.info(f"Added {len(preferences[:10])} user preferences to context")
            
            # Get user patterns from learning system
            patterns = self.learning.get_user_patterns(user_id)
            if patterns:
                context_data['user_context']['patterns'] = patterns[:5]  # Limit to top 5
                logger.info(f"Added {len(patterns[:5])} user patterns to context")
            
            # Get user topic interests from learning system
            topics = self.learning.get_user_topics(user_id)
            if topics:
                context_data['user_context']['topics'] = topics[:10]  # Limit to top 10
                logger.info(f"Added {len(topics[:10])} user topic interests to context")
            
            # If we have a user query, get query-specific relevant memories
            if user_query:
                relevant_memories = self.learning.memory_manager.get_memories(
                    query=user_query, 
                    max_results=5
                )
                
                if relevant_memories:
                    context_data['user_context']['relevant_memories'] = [
                        memory.get('content') for memory in relevant_memories
                    ]
                    logger.info(f"Added {len(relevant_memories)} query-relevant memories to context")
            
            # Flag that learning has been applied
            context_data['learning_applied'] = True
            context_data['user_context']['timestamp'] = time.time()
            
            return context_data
            
        except Exception as e:
            logger.error(f"Error retrieving learned context: {str(e)}")
            # Return original or empty context if there's an error
            return context_data if context_data else {}
                
            



            
            return context_data
            
        except Exception as e:
            logger.error(f"Error applying learned context: {str(e)}")
            # Return original context if there's an error
            return context_data



    

            }
            
            logger.info(f"Retrieved user context: {len(preferences)} preferences, {len(patterns)} patterns, {len(topics)} topics")
            return context
            
        except Exception as e:
            logger.error(f"Error applying learned context: {str(e)}")
            # Return empty context on error
            return {
                'user_id': user_id,
                'session_id': session_id,
                'preferences': [],
                'patterns': [],
                'topics': [],
                'error': str(e),
                'timestamp': time.time()
            }

# Create a singleton instance
learning_web_integration = LearningWebIntegration()
