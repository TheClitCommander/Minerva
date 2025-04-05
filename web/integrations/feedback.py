"""
Feedback System for Minerva

This module implements a comprehensive feedback collection and processing system
that works alongside the memory system to enable self-learning capabilities.

Features:
- Feedback collection on AI responses
- Response quality tracking
- Context-aware memory enhancement
- Preparation of datasets for future fine-tuning
"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

# Import memory system
from integrations.memory import memory_system, enhance_with_memory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define feedback quality levels
FEEDBACK_LEVELS = {
    "excellent": 5,
    "good": 4,
    "adequate": 3,
    "poor": 2,
    "incorrect": 1
}

class FeedbackSystem:
    """Manages feedback collection, storage, and processing for Minerva."""
    
    def __init__(self, data_dir: str = "./data/feedback"):
        """
        Initialize the feedback system.
        
        Args:
            data_dir: Directory to store feedback data
        """
        self.data_dir = data_dir
        self.feedback_file = os.path.join(data_dir, "user_feedback.jsonl")
        self.fine_tuning_dataset = os.path.join(data_dir, "fine_tuning_data.jsonl")
        self.context_history = {}  # Stores conversation context by conversation_id
        
        # Create the data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing feedback if the file exists
        self._load_feedback()
        
        logger.info(f"Feedback system initialized with data directory: {data_dir}")
    
    def _load_feedback(self):
        """Load existing feedback data from disk."""
        self.feedback_data = []
        
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, "r") as f:
                    for line in f:
                        if line.strip():
                            self.feedback_data.append(json.loads(line))
                logger.info(f"Loaded {len(self.feedback_data)} feedback entries")
            except Exception as e:
                logger.error(f"Error loading feedback data: {str(e)}")
    
    def record_feedback(self, 
                       conversation_id: str, 
                       query: str, 
                       response: str, 
                       feedback_level: str, 
                       comments: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Record user feedback on an AI response.
        
        Args:
            conversation_id: Unique identifier for the conversation
            query: The user's query that prompted the response
            response: The AI response being rated
            feedback_level: Quality rating from FEEDBACK_LEVELS
            comments: Optional user comments about the response
            metadata: Optional additional metadata
            
        Returns:
            feedback_id: Unique identifier for this feedback entry
        """
        if feedback_level not in FEEDBACK_LEVELS:
            raise ValueError(f"Invalid feedback level: {feedback_level}. Must be one of {list(FEEDBACK_LEVELS.keys())}")
        
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        feedback_entry = {
            "id": feedback_id,
            "conversation_id": conversation_id,
            "timestamp": timestamp,
            "query": query,
            "response": response,
            "feedback_level": feedback_level,
            "feedback_score": FEEDBACK_LEVELS[feedback_level],
            "comments": comments,
            "metadata": metadata or {}
        }
        
        # Store the feedback
        self.feedback_data.append(feedback_entry)
        
        # Write to the file
        try:
            with open(self.feedback_file, "a") as f:
                f.write(json.dumps(feedback_entry) + "\n")
            
            # If the feedback is excellent or good, add it to the fine-tuning dataset
            if FEEDBACK_LEVELS[feedback_level] >= 4:
                self._add_to_fine_tuning_dataset(feedback_entry)
                
            logger.info(f"Recorded feedback {feedback_id} with level: {feedback_level}")
        except Exception as e:
            logger.error(f"Error storing feedback: {str(e)}")
        
        return feedback_id
    
    def _add_to_fine_tuning_dataset(self, feedback_entry: Dict[str, Any]):
        """
        Add high-quality responses to the fine-tuning dataset.
        
        Args:
            feedback_entry: The feedback entry to add
        """
        # Format the data for fine-tuning
        fine_tuning_entry = {
            "instruction": feedback_entry["query"],
            "output": feedback_entry["response"],
            "source": "user_feedback",
            "quality_score": feedback_entry["feedback_score"],
            "timestamp": feedback_entry["timestamp"]
        }
        
        try:
            with open(self.fine_tuning_dataset, "a") as f:
                f.write(json.dumps(fine_tuning_entry) + "\n")
            logger.info(f"Added entry to fine-tuning dataset from feedback {feedback_entry['id']}")
        except Exception as e:
            logger.error(f"Error adding to fine-tuning dataset: {str(e)}")
    
    def track_conversation_context(self, 
                                 conversation_id: str, 
                                 user_query: str, 
                                 ai_response: str,
                                 context_window: int = 5):
        """
        Track conversation context for multi-turn awareness.
        
        Args:
            conversation_id: Unique identifier for the conversation
            user_query: The user's query
            ai_response: Minerva's response
            context_window: Number of turns to maintain in context
        """
        if conversation_id not in self.context_history:
            self.context_history[conversation_id] = []
        
        # Add this turn to the context
        turn = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "ai_response": ai_response
        }
        
        self.context_history[conversation_id].append(turn)
        
        # Keep only the most recent turns based on context_window
        if len(self.context_history[conversation_id]) > context_window:
            self.context_history[conversation_id] = self.context_history[conversation_id][-context_window:]
        
        logger.debug(f"Updated context for conversation {conversation_id}, now has {len(self.context_history[conversation_id])} turns")
    
    def get_conversation_context(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Get the tracked context for a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            List of conversation turns
        """
        return self.context_history.get(conversation_id, [])
    
    def enhance_query_with_context(self, 
                                 conversation_id: str, 
                                 user_query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Enhance a query with both conversation context and memory.
        
        This combines the immediate conversation context with relevant memories
        to provide a comprehensive context for responding.
        
        Args:
            conversation_id: Unique identifier for the conversation
            user_query: The user's current query
            
        Returns:
            Tuple of (enhanced_query, memories_used)
        """
        # First, get the conversation context
        context = self.get_conversation_context(conversation_id)
        context_str = ""
        
        if context:
            context_turns = []
            for i, turn in enumerate(context):
                context_turns.append(f"Turn {i+1}:")
                context_turns.append(f"User: {turn['user_query']}")
                context_turns.append(f"Minerva: {turn['ai_response']}\n")
            
            context_str = "Recent conversation history:\n" + "\n".join(context_turns)
        
        # Then, enhance with memory
        memories_query = user_query
        if context_str:
            # Include the last query from context to help find relevant memories
            if context and context[-1]['user_query']:
                memories_query = context[-1]['user_query'] + " " + user_query
        
        # Get memory-enhanced query and memories used
        memory_enhanced_query, memories = enhance_with_memory(memories_query)
        
        # Combine both enhancements
        if context_str and memories:
            enhanced_query = f"""
            {context_str}
            
            {memory_enhanced_query}
            """
        elif context_str:
            enhanced_query = f"""
            {context_str}
            
            Current query: {user_query}
            """
        else:
            enhanced_query = memory_enhanced_query
        
        logger.info(f"Enhanced query with {len(context)} context turns and {len(memories)} memories")
        return enhanced_query, memories
    
    def analyze_user_preferences(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Analyze feedback to determine user preferences.
        
        Args:
            user_id: Identifier for the user
            
        Returns:
            Dictionary of user preferences and patterns
        """
        # Filter feedback for this user
        user_feedback = [f for f in self.feedback_data if f.get("metadata", {}).get("user_id") == user_id]
        
        if not user_feedback:
            logger.info(f"No feedback found for user {user_id}")
            return {"preferences_detected": False}
        
        # Calculate average feedback score
        avg_score = sum(f["feedback_score"] for f in user_feedback) / len(user_feedback)
        
        # Analyze common topics
        topics = {}
        for feedback in user_feedback:
            topic = feedback.get("metadata", {}).get("topic")
            if topic:
                topics[topic] = topics.get(topic, 0) + 1
        
        # Determine response length preference
        length_scores = {}
        for feedback in user_feedback:
            response_length = len(feedback["response"])
            length_category = "short" if response_length < 500 else "medium" if response_length < 1500 else "long"
            
            if length_category not in length_scores:
                length_scores[length_category] = {"count": 0, "total_score": 0}
            
            length_scores[length_category]["count"] += 1
            length_scores[length_category]["total_score"] += feedback["feedback_score"]
        
        # Calculate average score per length category
        for category in length_scores:
            if length_scores[category]["count"] > 0:
                length_scores[category]["avg_score"] = length_scores[category]["total_score"] / length_scores[category]["count"]
        
        # Determine preferred length based on highest average score
        preferred_length = max(length_scores.items(), key=lambda x: x[1].get("avg_score", 0))[0] if length_scores else "medium"
        
        # Identify top topics
        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:3] if topics else []
        
        preferences = {
            "preferences_detected": True,
            "avg_feedback_score": avg_score,
            "feedback_count": len(user_feedback),
            "preferred_response_length": preferred_length,
            "top_topics": top_topics,
            "length_preferences": length_scores
        }
        
        logger.info(f"Analyzed preferences for user {user_id}: {json.dumps(preferences)}")
        return preferences
    
    def prepare_fine_tuning_batch(self, min_entries: int = 100) -> Optional[str]:
        """
        Prepare a batch of data for fine-tuning when sufficient examples exist.
        
        Args:
            min_entries: Minimum number of entries needed for fine-tuning
            
        Returns:
            Path to the prepared dataset or None if insufficient data
        """
        # Count how many entries we have
        if not os.path.exists(self.fine_tuning_dataset):
            logger.info("No fine-tuning dataset exists yet")
            return None
        
        # Count entries
        with open(self.fine_tuning_dataset, "r") as f:
            count = sum(1 for _ in f)
        
        if count < min_entries:
            logger.info(f"Not enough entries for fine-tuning. Have {count}, need {min_entries}")
            return None
        
        # Create a batch file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_file = os.path.join(self.data_dir, f"fine_tuning_batch_{timestamp}.jsonl")
        
        try:
            # Copy the data to the batch file
            with open(self.fine_tuning_dataset, "r") as src, open(batch_file, "w") as dst:
                dst.write(src.read())
            
            logger.info(f"Prepared fine-tuning batch with {count} entries: {batch_file}")
            return batch_file
        except Exception as e:
            logger.error(f"Error preparing fine-tuning batch: {str(e)}")
            return None
    
    def analyze_model_performance(self, query_type: Optional[str] = None, min_feedback_entries: int = 10) -> Dict[str, Dict[str, Any]]:
        """
        Analyze feedback data to determine model performance for different query types.
        
        This enables Minerva to learn which models perform best for different kinds of
        queries and adjust selection weights accordingly.
        
        Args:
            query_type: Optional filter for a specific query type
            min_feedback_entries: Minimum number of feedback entries needed for reliable analysis
            
        Returns:
            Dictionary mapping model names to performance metrics
        """
        # Initialize performance dictionary
        model_performance = {}
        
        # Filter feedback that has model information
        model_feedback = [f for f in self.feedback_data if 
                          "metadata" in f and 
                          "model_info" in f["metadata"] and
                          "selected_model" in f["metadata"].get("model_info", {})]
        
        # Return empty dict if we don't have enough data
        if len(model_feedback) < min_feedback_entries:
            logger.info(f"Not enough model feedback entries for analysis. Have {len(model_feedback)}, need {min_feedback_entries}")
            return {}
            
        # Filter by query type if specified
        if query_type:
            model_feedback = [f for f in model_feedback if 
                             f["metadata"].get("model_info", {}).get("query_type") == query_type]
        
        # Process feedback to calculate model performance
        for feedback in model_feedback:
            # Extract model information
            model_info = feedback["metadata"].get("model_info", {})
            selected_model = model_info.get("selected_model")
            feedback_score = feedback["feedback_score"]
            actual_query_type = model_info.get("query_type", "general")
            
            # Skip if no selected model
            if not selected_model:
                continue
                
            # Initialize model entry if needed
            if selected_model not in model_performance:
                model_performance[selected_model] = {
                    "total_score": 0,
                    "count": 0,
                    "avg_score": 0,
                    "query_types": {},
                    "is_api_model": model_info.get("is_api_model", False)
                }
            
            # Update overall stats
            model_performance[selected_model]["total_score"] += feedback_score
            model_performance[selected_model]["count"] += 1
            
            # Update query type stats
            if actual_query_type not in model_performance[selected_model]["query_types"]:
                model_performance[selected_model]["query_types"][actual_query_type] = {
                    "total_score": 0,
                    "count": 0,
                    "avg_score": 0
                }
                
            model_performance[selected_model]["query_types"][actual_query_type]["total_score"] += feedback_score
            model_performance[selected_model]["query_types"][actual_query_type]["count"] += 1
            
        # Calculate averages
        for model, stats in model_performance.items():
            if stats["count"] > 0:
                stats["avg_score"] = stats["total_score"] / stats["count"]
                
            # Calculate averages for each query type
            for qtype, qstats in stats["query_types"].items():
                if qstats["count"] > 0:
                    qstats["avg_score"] = qstats["total_score"] / qstats["count"]
        
        logger.info(f"Analyzed performance for {len(model_performance)} models across {len(model_feedback)} feedback entries")
        return model_performance

# Initialize the feedback system
feedback_system = FeedbackSystem()

# Exported functions for easy API integration

def record_user_feedback(
    conversation_id: str, 
    query: str, 
    response: str, 
    feedback_level: str, 
    comments: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Record feedback for an AI response"""
    return feedback_system.record_feedback(
        conversation_id=conversation_id,
        query=query,
        response=response,
        feedback_level=feedback_level,
        comments=comments,
        metadata=metadata
    )

def track_conversation(
    conversation_id: str, 
    user_query: str, 
    ai_response: str,
    context_window: int = 5
):
    """Track a conversation turn for context awareness"""
    feedback_system.track_conversation_context(
        conversation_id=conversation_id,
        user_query=user_query,
        ai_response=ai_response,
        context_window=context_window
    )

def enhance_query(
    conversation_id: str, 
    user_query: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """Enhance a query with both conversation context and memory"""
    return feedback_system.enhance_query_with_context(
        conversation_id=conversation_id,
        user_query=user_query
    )

def get_user_preferences(user_id: str = "default") -> Dict[str, Any]:
    """Get analyzed preferences for a user"""
    return feedback_system.analyze_user_preferences(user_id=user_id)

def check_fine_tuning_readiness(min_entries: int = 100) -> Optional[str]:
    """Check if we have enough data for fine-tuning"""
    return feedback_system.prepare_fine_tuning_batch(min_entries=min_entries)

def get_model_performance(query_type: Optional[str] = None, min_feedback_entries: int = 10) -> Dict[str, Dict[str, Any]]:
    """
    Analyze model performance based on user feedback for intelligent model selection.
    
    This function analyzes historical feedback data to determine which models
    perform best for different query types. This enables dynamic model selection
    that improves over time as more feedback is collected.
    
    Args:
        query_type: Optional filter to get performance for a specific query type
                   (technical, creative, reasoning, general)
        min_feedback_entries: Minimum number of feedback entries required for meaningful analysis
    
    Returns:
        Dictionary mapping model names to their performance metrics
    """
    return feedback_system.analyze_model_performance(query_type, min_feedback_entries)
