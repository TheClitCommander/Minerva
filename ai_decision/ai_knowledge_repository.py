"""
AI Knowledge Repository

This module stores and manages shared insights between AI models.
It enables knowledge transfer and trend-based learning across multiple AI instances.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix import paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AIKnowledgeRepository:
    """
    Centralized repository for storing and managing knowledge and insights 
    shared between multiple AI models. Enables cross-AI learning and 
    synchronization of insights.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the AI Knowledge Repository.
        
        Args:
            storage_path: Optional path to store knowledge data
        """
        # Default storage path
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "ai_knowledge.json"
        )
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # Knowledge store structure
        self.knowledge_store = self._load_repository()
        
        # Cache for recently accessed insights
        self.insights_cache = {}
        
        # Keep track of registered AI models
        self.registered_models = set()
        
        # Statistics for knowledge usage
        self.usage_stats = defaultdict(int)
        
        logger.info(f"AI Knowledge Repository initialized with storage at {self.storage_path}")
    
    def _load_repository(self) -> Dict[str, Any]:
        """
        Load knowledge from file.
        
        Returns:
            Dictionary containing knowledge data
        """
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading knowledge repository: {str(e)}")
                return self._initialize_empty_repository()
        return self._initialize_empty_repository()
    
    def _initialize_empty_repository(self) -> Dict[str, Any]:
        """
        Initialize empty knowledge repository structure.
        
        Returns:
            Empty knowledge structure
        """
        return {
            "insights": {},
            "model_performance": {},
            "query_patterns": {},
            "response_effectiveness": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
    
    def _save_repository(self) -> bool:
        """
        Save knowledge to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update metadata
            self.knowledge_store["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save to file
            with open(self.storage_path, "w") as f:
                json.dump(self.knowledge_store, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving knowledge repository: {str(e)}")
            return False
    
    def register_model(self, model_name: str) -> bool:
        """
        Register an AI model with the knowledge repository.
        
        Args:
            model_name: Name of the AI model
            
        Returns:
            True if registration was successful
        """
        self.registered_models.add(model_name)
        
        # Initialize model performance tracking if needed
        if model_name not in self.knowledge_store["model_performance"]:
            self.knowledge_store["model_performance"][model_name] = {
                "response_quality": [],
                "user_satisfaction": [],
                "response_time": [],
                "effectiveness_by_topic": {},
                "last_updated": datetime.now().isoformat()
            }
            self._save_repository()
        
        logger.info(f"Model {model_name} registered with Knowledge Repository")
        return True
    
    def store_insight(self, model_name: str, query: str, response: str, 
                     feedback: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """
        Store response insights from AI models.
        
        Args:
            model_name: Name of the AI model
            query: User query
            response: AI response
            feedback: Feedback data
            context: Optional context information
            
        Returns:
            Insight ID
        """
        # Generate insight ID
        insight_id = str(uuid.uuid4())
        
        # Register model if not already registered
        if model_name not in self.registered_models:
            self.register_model(model_name)
        
        # Create insight entry
        insight = {
            "id": insight_id,
            "model": model_name,
            "query": query,
            "response": response,
            "feedback": feedback,
            "context": context or {},
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "effectiveness_score": feedback.get("rating", 0)
        }
        
        # Store in the insights collection
        if "insights" not in self.knowledge_store:
            self.knowledge_store["insights"] = {}
        
        self.knowledge_store["insights"][insight_id] = insight
        
        # Update query patterns
        query_terms = query.lower().split()
        for term in query_terms:
            if len(term) > 3:  # Skip very short terms
                if term not in self.knowledge_store["query_patterns"]:
                    self.knowledge_store["query_patterns"][term] = []
                
                if insight_id not in self.knowledge_store["query_patterns"][term]:
                    self.knowledge_store["query_patterns"][term].append(insight_id)
        
        # Update model performance
        if "rating" in feedback:
            self.knowledge_store["model_performance"][model_name]["response_quality"].append({
                "value": feedback["rating"],
                "timestamp": datetime.now().isoformat(),
                "insight_id": insight_id
            })
            
            # Trim to keep only recent performance data (last 100 entries)
            self.knowledge_store["model_performance"][model_name]["response_quality"] = \
                self.knowledge_store["model_performance"][model_name]["response_quality"][-100:]
        
        # Save repository
        self._save_repository()
        
        logger.info(f"Stored new insight {insight_id} from model {model_name}")
        return insight_id
    
    def retrieve_insights(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant insights for a given query.
        
        Args:
            query: Query to find insights for
            limit: Maximum number of insights to return
            
        Returns:
            List of relevant insights
        """
        self.usage_stats["retrieve_insights"] += 1
        
        # Check cache first
        cache_key = f"{query}:{limit}"
        if cache_key in self.insights_cache:
            return self.insights_cache[cache_key]
        
        # Find potentially relevant insights
        relevant_insight_ids = set()
        query_terms = query.lower().split()
        
        # Collect potentially relevant insights based on query terms
        for term in query_terms:
            if len(term) > 3 and term in self.knowledge_store["query_patterns"]:
                relevant_insight_ids.update(self.knowledge_store["query_patterns"][term])
        
        # Get the actual insights
        insights = []
        for insight_id in relevant_insight_ids:
            if insight_id in self.knowledge_store["insights"]:
                insight = self.knowledge_store["insights"][insight_id]
                # Calculate relevance score (simple implementation)
                term_matches = sum(1 for term in query_terms if term in insight["query"].lower())
                relevance = term_matches / len(query_terms) if query_terms else 0
                insight["relevance"] = relevance
                insights.append(insight)
        
        # Sort by relevance and limit results
        insights.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        result = insights[:limit]
        
        # Update usage count for retrieved insights
        for insight in result:
            if insight["id"] in self.knowledge_store["insights"]:
                self.knowledge_store["insights"][insight["id"]]["usage_count"] += 1
        
        # Save if any usage counts were updated
        if result:
            self._save_repository()
        
        # Cache the result
        self.insights_cache[cache_key] = result
        
        logger.info(f"Retrieved {len(result)} insights for query: {query}")
        return result
    
    def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """
        Get performance data for a specific AI model.
        
        Args:
            model_name: Name of the AI model
            
        Returns:
            Performance data for the model
        """
        if model_name not in self.knowledge_store["model_performance"]:
            return {}
        
        return self.knowledge_store["model_performance"][model_name]
    
    def get_best_model_for_query(self, query: str, user_preferences: Optional[Dict[str, Any]] = None) -> Tuple[str, float]:
        """
        Determine the best model to handle a specific query based on past performance,
        query complexity, and user preferences.
        
        Args:
            query: The query to evaluate
            user_preferences: Optional dictionary of user preferences
            
        Returns:
            Tuple of (model_name, confidence_score)
        """
        if not self.registered_models:
            return (None, 0.0)
        
        # Get relevant insights for this query
        insights = self.retrieve_insights(query, limit=10)
        
        # Calculate query complexity (simple heuristic based on length and structure)
        words = query.split()
        query_complexity = min(10, max(1, len(words) / 10))
        
        # Check for technical or specialized terms that suggest complexity
        technical_terms = ["algorithm", "neural", "quantum", "framework", "architecture", 
                          "protocol", "implementation", "function", "methodology", "technique"]
        complexity_boost = sum(2 for word in words if any(term in word.lower() for term in technical_terms)) / 10
        query_complexity += min(5, complexity_boost)
        
        # Count successful responses by model
        model_scores = defaultdict(list)
        model_recency = {}  # Track recency of insights
        model_complexity_match = defaultdict(list)  # Track complexity matching
        
        # Track which models have handled similar queries
        current_time = datetime.now()
        
        for insight in insights:
            model = insight.get("model")
            rating = insight.get("effectiveness_score", 0)
            relevance = insight.get("relevance", 0)
            context = insight.get("context", {})
            insight_time_str = insight.get("created_at")
            
            if not model or rating <= 0:
                continue
                
            # Calculate recency factor - more recent insights get higher weight
            recency_factor = 1.0
            if insight_time_str:
                try:
                    insight_time = datetime.fromisoformat(insight_time_str)
                    age_days = (current_time - insight_time).days
                    # Reduce weight for older insights, but still consider them
                    recency_factor = max(0.5, 1.0 - (age_days / 30))  # Gradually reduce over 30 days
                    
                    # Track most recent use of this model
                    if model not in model_recency or insight_time > model_recency[model]:
                        model_recency[model] = insight_time
                except (ValueError, TypeError):
                    pass
            
            # Consider complexity matching - models that performed well on similar complexity
            insight_complexity = context.get("query_complexity", 5)  # Default to medium complexity
            complexity_match = 1.0 - (abs(query_complexity - insight_complexity) / 10)
            model_complexity_match[model].append(complexity_match)
            
            # Weight the rating by relevance, recency and complexity match
            weighted_score = rating * relevance * recency_factor * complexity_match
            model_scores[model].append(weighted_score)
        
        # Calculate average score for each model with adjustments
        model_avg_scores = {}
        for model, scores in model_scores.items():
            if not scores:
                continue
                
            # Base score from historical performance
            base_score = sum(scores) / len(scores)
            
            # Adjust based on complexity matching
            complexity_adjustment = 1.0
            if model in model_complexity_match and model_complexity_match[model]:
                complexity_adjustment = sum(model_complexity_match[model]) / len(model_complexity_match[model])
            
            # Calculate final score
            model_avg_scores[model] = base_score * complexity_adjustment
            
            # Apply user preference adjustments if available
            if user_preferences:
                preferred_tone = user_preferences.get("response_tone")
                preferred_length = user_preferences.get("response_length")
                
                # If we know this model matches user preferences, boost its score
                if preferred_tone or preferred_length:
                    tone_match = self._model_matches_tone(model, preferred_tone) if preferred_tone else 1.0
                    length_match = self._model_matches_length(model, preferred_length) if preferred_length else 1.0
                    preference_boost = (tone_match + length_match) / 2
                    model_avg_scores[model] *= preference_boost
        
        # Find best model
        best_model = None
        best_score = 0
        
        for model, score in model_avg_scores.items():
            if score > best_score:
                best_score = score
                best_model = model
        
        # If no best model found from insights, default to first registered
        if not best_model and self.registered_models:
            best_model = next(iter(self.registered_models))
            best_score = 0.5  # Default confidence
        
        logger.info(f"Selected model {best_model} with confidence {min(1.0, best_score):.2f} for query complexity {query_complexity:.1f}")
        return (best_model, min(1.0, best_score))
        
    def _model_matches_tone(self, model: str, preferred_tone: str) -> float:
        """
        Calculate how well a model matches the preferred tone based on historical performance.
        Returns a score between 0.8 and 1.2 (0.8 = poor match, 1.2 = excellent match)
        """
        # Default to neutral match (no penalty or boost)
        match_score = 1.0
        
        # This would ideally use historical data about tone performance
        # For now, use some reasonable assumptions based on model capabilities
        if model == "openai" and preferred_tone in ["neutral", "formal"]:
            match_score = 1.2
        elif model == "claude" and preferred_tone in ["casual", "friendly"]:
            match_score = 1.15
        elif model == "huggingface" and preferred_tone == "neutral":
            match_score = 1.1
            
        return match_score
        
    def _model_matches_length(self, model: str, preferred_length: str) -> float:
        """
        Calculate how well a model matches the preferred response length.
        Returns a score between 0.8 and 1.2 (0.8 = poor match, 1.2 = excellent match)
        """
        # Default to neutral match (no penalty or boost)
        match_score = 1.0
        
        # This would ideally use historical data about length performance
        # For now, use some reasonable assumptions based on model capabilities
        if model == "openai" and preferred_length in ["medium", "long"]:
            match_score = 1.2
        elif model == "claude" and preferred_length == "long":
            match_score = 1.15
        elif model == "huggingface" and preferred_length == "short":
            match_score = 1.1
            
        return match_score
    
    def clear_cache(self) -> None:
        """Clear the insights cache."""
        self.insights_cache = {}
        logger.info("Cleared insights cache")


# Create a singleton instance
ai_knowledge_repository = AIKnowledgeRepository()

# Test function
def test_knowledge_repository():
    """Test the AI Knowledge Repository functionality."""
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_knowledge.json")
    repo = AIKnowledgeRepository(storage_path=test_file)
    
    # Register models
    repo.register_model("claude")
    repo.register_model("gpt4")
    
    # Store some insights
    repo.store_insight(
        "claude", 
        "What is artificial intelligence?", 
        "Artificial intelligence (AI) refers to systems that can perform tasks typically requiring human intelligence.",
        {"rating": 4.5}
    )
    
    repo.store_insight(
        "gpt4", 
        "Explain the concept of artificial intelligence", 
        "Artificial intelligence is the simulation of human intelligence in machines...",
        {"rating": 4.8}
    )
    
    repo.store_insight(
        "claude", 
        "How does machine learning work?", 
        "Machine learning is a subset of AI that focuses on algorithms that improve through experience.",
        {"rating": 4.2}
    )
    
    # Retrieve insights
    ai_insights = repo.retrieve_insights("What is AI?")
    print(f"Found {len(ai_insights)} insights about AI")
    
    for insight in ai_insights:
        print(f"Model: {insight['model']}, Relevance: {insight.get('relevance', 0):.2f}")
        print(f"Query: {insight['query']}")
        print(f"Response: {insight['response'][:50]}...")
    
    # Get best model
    best_model, confidence = repo.get_best_model_for_query("What is artificial intelligence?")
    print(f"\nBest model for AI question: {best_model} (confidence: {confidence:.2f})")
    
    # Clean up test file
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    test_knowledge_repository()
