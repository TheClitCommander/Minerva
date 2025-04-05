#!/usr/bin/env python3
"""
Model Insights Manager for Minerva

This module provides visualization and analytics for the enhanced AI model selection system.
It tracks model performance metrics, query complexities, and feedback patterns to help
optimize the system.
"""

import os
import json
import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import statistics
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelInsightsManager:
    """
    Manages and analyzes insights about AI model performance and selection.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the insights manager.
        
        Args:
            data_dir: Directory to store insights data
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.insights_file = os.path.join(self.data_dir, "model_insights.json")
        self.selections_file = os.path.join(self.data_dir, "model_selections.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing data or create empty datasets
        self.insights = self._load_data(self.insights_file, {
            "total_queries": 0,
            "models": {},
            "complexity_distribution": {},
            "quality_scores": {},
            "feedback": {"positive": 0, "negative": 0}
        })
        
        self.selections = self._load_data(self.selections_file, {"selections": []})
        
        # Initialize database structure for evaluations
        self.evaluations_file = os.path.join(self.data_dir, "think_tank_evaluations.json")
        
        # Load evaluations or start with empty dict
        evaluations = self._load_data(self.evaluations_file, {})
        
        self.db = {
            "think_tank_evaluations": evaluations
        }
        
        # Register known models if they don't exist
        for model in ["openai", "claude", "huggingface"]:
            if model not in self.insights["models"]:
                self.insights["models"][model] = {
                    "count": 0,
                    "success_rate": 0,
                    "avg_quality": 0,
                    "feedback": {"positive": 0, "negative": 0},
                    "complexity_scores": {},
                    "tags": {}
                }
    
    def _load_data(self, filename: str, default_data: Dict) -> Dict:
        """Load data from a JSON file, or return default_data if file doesn't exist."""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
            return default_data
        except Exception as e:
            logger.error(f"Error loading data from {filename}: {e}")
            return default_data
    
    def _save_data(self, data: Dict, filename: str) -> bool:
        """Save data to a JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {e}")
            return False
    
    def save_to_disk(self) -> bool:
        """Save all database data to disk."""
        try:
            # Enhanced logging for debugging
            logger.info(f"[THINK TANK DEBUG] Starting save_to_disk() with data directory: {self.data_dir}")
            
            # Create the data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)
            
            # First, make sure the evaluation_storage directory exists
            eval_storage_dir = os.path.join(os.path.dirname(os.path.dirname(self.data_dir)), "evaluation_storage")
            os.makedirs(eval_storage_dir, exist_ok=True)
            logger.info(f"[THINK TANK DEBUG] Ensured evaluation_storage directory exists at: {eval_storage_dir}")
            
            # Save evaluations to a dedicated file
            evaluations_file = os.path.join(self.data_dir, "think_tank_evaluations.json")
            
            # Also save to the evaluation_storage directory
            timestamp = int(time.time())
            storage_file = os.path.join(eval_storage_dir, f"think_tank_eval_{timestamp}.json")
            
            # Log the current think tank evaluations state
            num_evaluations = len(self.db["think_tank_evaluations"])
            model_names = set([eval_data.get('best_model', '') for eval_id, eval_data in self.db["think_tank_evaluations"].items()])
            logger.info(f"[THINK TANK DEBUG] Saving {num_evaluations} evaluations for models: {model_names}")
            
            # Debug evaluation IDs
            eval_ids = list(self.db["think_tank_evaluations"].keys())
            logger.info(f"[THINK TANK DEBUG] Evaluation IDs: {eval_ids}")
            
            # Ensuring the evaluation_storage directory exists
            os.makedirs(eval_storage_dir, exist_ok=True)
            logger.info(f"[THINK TANK DEBUG] Evaluation storage directory confirmed: {os.path.exists(eval_storage_dir)}")
            
            # Save to both locations
            try:
                with open(evaluations_file, 'w') as f:
                    json.dump(self.db["think_tank_evaluations"], f, indent=2)
                logger.info(f"[THINK TANK DEBUG] Successfully saved to {evaluations_file}")
            except Exception as e:
                logger.error(f"[THINK TANK ERROR] Failed to save to {evaluations_file}: {str(e)}")
            
            try:
                with open(storage_file, 'w') as f:
                    json.dump(self.db["think_tank_evaluations"], f, indent=2)
                logger.info(f"[THINK TANK DEBUG] Successfully saved to {storage_file}")
            except Exception as e:
                logger.error(f"[THINK TANK ERROR] Failed to save to {storage_file}: {str(e)}")
            
            logger.info(f"[THINK TANK DEBUG] Saved evaluations to {evaluations_file} and {storage_file}")
                
            # Save main insights data
            self._save_data(self.insights, self.insights_file)
            
            # Save selection data
            self._save_data(self.selections, self.selections_file)
            
            return True
        except Exception as e:
            logger.error(f"Error saving database to disk: {e}")
            traceback.print_exc()
            return False
    
    def record_model_selection(self, 
                              user_id: str,
                              message_id: str,
                              query: str,
                              selected_model: str,
                              considered_models: List[str],
                              complexity: float,
                              quality_score: float,
                              query_tags: Optional[List[str]] = None,
                              decision_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Record a model selection event with enhanced context.
        
        Args:
            user_id: User ID
            message_id: Message ID
            query: The user query
            selected_model: The model that was selected
            considered_models: All models that were considered
            complexity: Query complexity score (1-10)
            quality_score: Response quality score (1-10)
            query_tags: Optional tags describing the query type
            decision_context: Additional context about the selection decision
            
        Returns:
            str: Selection ID
        """
        # Process query/complexity and map to standard tags if not provided
        if not query_tags:
            query_tags = []
            
            # Add default tags based on query analysis
            words = query.split()
            if len(words) < 5:
                query_tags.append("short_query")
            elif len(words) > 25:
                query_tags.append("long_query")
            
            # Detect potential code-related queries
            if any(term in query.lower() for term in ["code", "function", "script", "program", "debug", "error"]):
                query_tags.append("code")
            
            # Detect explanation queries
            if any(term in query.lower() for term in ["explain", "describe", "how", "what is", "why", "concept"]):
                query_tags.append("explanation")
                
            # Detect comparison queries
            if any(term in query.lower() for term in ["compare", "versus", "vs", "difference", "better", "pros and cons"]):
                query_tags.append("comparison")
                
            # Detect technical queries
            technical_indicators = [
                "algorithm", "architecture", "framework", "library", "system", "technical", 
                "implementation", "protocol", "methodology", "design pattern", "technology"
            ]
            if any(term in query.lower() for term in technical_indicators):
                query_tags.append("technical")
        
        # Round complexity to nearest 0.5
        complexity_rounded = round(complexity * 2) / 2
        
        # Determine selection method
        selection_method = "default"
        if decision_context:
            if decision_context.get("repository_guided", False):
                selection_method = "repository"
            elif decision_context.get("dashboard_guided", False):
                selection_method = "dashboard"
            elif decision_context.get("priority") == "comprehensive":
                selection_method = "comprehensive"
        
        # Create selection record
        selection_id = f"sel_{message_id}"
        selection = {
            "id": selection_id,
            "user_id": user_id,
            "message_id": message_id,
            "timestamp": datetime.now().isoformat(),
            "query": query[:100] + "..." if len(query) > 100 else query,  # Truncate long queries
            "selected_model": selected_model,
            "considered_models": considered_models,
            "complexity": complexity,
            "complexity_rounded": complexity_rounded,
            "quality_score": quality_score,
            "feedback": None,
            "tags": query_tags,
            "selection_method": selection_method
        }
        
        # Add additional decision context data if available
        if decision_context:
            selection["repository_guided"] = decision_context.get("repository_guided", False)
            selection["dashboard_guided"] = decision_context.get("dashboard_guided", False)
            selection["priority"] = decision_context.get("priority", "balanced")
            selection["confidence_threshold"] = decision_context.get("confidence_threshold", 0.7)
        
        # Update selections list
        self.selections["selections"].append(selection)
        
        # Keep only the most recent 1000 selections
        if len(self.selections["selections"]) > 1000:
            self.selections["selections"] = self.selections["selections"][-1000:]
        
        # Update insights
        self.insights["total_queries"] += 1
        
        # Update model-specific insights
        if selected_model in self.insights["models"]:
            model_data = self.insights["models"][selected_model]
            model_data["count"] += 1
            
            # Update success rate for all models
            for model in self.insights["models"]:
                model_count = self.insights["models"][model]["count"]
                self.insights["models"][model]["success_rate"] = (
                    (model_count / self.insights["total_queries"]) * 100 
                    if self.insights["total_queries"] > 0 else 0
                )
            
            # Update quality score
            current_avg = model_data["avg_quality"]
            current_count = model_data["count"]
            model_data["avg_quality"] = (
                (current_avg * (current_count - 1) + quality_score) / current_count
                if current_count > 1 else quality_score
            )
            
            # Update complexity distribution
            complexity_key = str(complexity_rounded)
            if complexity_key not in model_data["complexity_scores"]:
                model_data["complexity_scores"][complexity_key] = 0
            model_data["complexity_scores"][complexity_key] += 1
            
            # Update overall complexity distribution
            if complexity_key not in self.insights["complexity_distribution"]:
                self.insights["complexity_distribution"][complexity_key] = 0
            self.insights["complexity_distribution"][complexity_key] += 1
            
            # Update tags with weighted importance based on query complexity
            # More complex queries provide stronger signal about model capabilities
            tag_weight = min(2.0, max(1.0, complexity / 5.0))  # Weight between 1.0 and 2.0
            
            if query_tags:
                for tag in query_tags:
                    if tag not in model_data["tags"]:
                        model_data["tags"][tag] = 0
                    model_data["tags"][tag] += tag_weight
            
            # Track method of selection
            method_key = f"selection_method_{selection_method}"
            if method_key not in model_data:
                model_data[method_key] = 0
            model_data[method_key] += 1
        
        # Save data
        self._save_data(self.insights, self.insights_file)
        self._save_data(self.selections, self.selections_file)
        
        # Log the selection
        logger.info(f"Recorded model selection: {selected_model} for query with complexity {complexity_rounded}, tags: {query_tags}")
        
        return selection_id
    
    def record_feedback(self, message_id: str, is_positive: bool) -> bool:
        """
        Record feedback for a model selection.
        
        Args:
            message_id: Message ID
            is_positive: Whether the feedback was positive
            
        Returns:
            bool: Success
        """
        # Find the selection
        selection_id = f"sel_{message_id}"
        for selection in self.selections["selections"]:
            if selection["id"] == selection_id:
                selection["feedback"] = "positive" if is_positive else "negative"
                
                # Update feedback stats
                feedback_key = "positive" if is_positive else "negative"
                self.insights["feedback"][feedback_key] += 1
                
                # Update model feedback stats
                model = selection["selected_model"]
                if model in self.insights["models"]:
                    self.insights["models"][model]["feedback"][feedback_key] += 1
                
                # Save data
                self._save_data(self.insights, self.insights_file)
                self._save_data(self.selections, self.selections_file)
                return True
        
        return False
    
    def get_model_performance_by_complexity(self) -> Dict[str, List[float]]:
        """
        Get model selection rate by complexity level.
        
        Returns:
            Dict mapping model names to lists of percentages for each complexity level (1-10)
        """
        result = {}
        
        # Calculate the total selections at each complexity level
        complexity_totals = defaultdict(int)
        for selection in self.selections["selections"]:
            complexity = int(selection["complexity_rounded"])
            complexity_totals[complexity] += 1
        
        # Calculate percentage for each model at each complexity level
        for model in ["openai", "claude", "huggingface"]:
            result[model] = [0] * 10  # 10 complexity levels
            
            # Count model selections at each complexity level
            model_counts = defaultdict(int)
            for selection in self.selections["selections"]:
                if selection["selected_model"] == model:
                    complexity = int(selection["complexity_rounded"])
                    if 1 <= complexity <= 10:
                        model_counts[complexity] += 1
            
            # Calculate percentages
            for i in range(1, 11):
                total = complexity_totals.get(i, 0)
                model_count = model_counts.get(i, 0)
                percentage = (model_count / total * 100) if total > 0 else 0
                result[model][i-1] = round(percentage, 1)
        
        return result
    
    def get_quality_scores_by_model(self) -> List[float]:
        """
        Get average quality scores for each model.
        
        Returns:
            List of average quality scores, in order [openai, claude, huggingface]
        """
        models = ["openai", "claude", "huggingface"]
        result = []
        
        for model in models:
            if model in self.insights["models"]:
                result.append(round(self.insights["models"][model]["avg_quality"], 2))
            else:
                result.append(0)
        
        return result
    
    def get_best_model_for_query_type(self, query_tags: List[str]) -> Tuple[Optional[str], float]:
        """
        Find the best model for a specific query type based on historical performance.
        
        Args:
            query_tags: List of tags describing the query type
            
        Returns:
            Tuple of (best_model, confidence) or (None, 0) if no match found
        """
        if not query_tags:
            return None, 0.0
        
        # Calculate score for each model based on tag performance
        model_scores = {}
        for model_name, data in self.insights["models"].items():
            if data["count"] < 5:  # Skip models with insufficient data
                continue
                
            # Calculate match score based on how well this model performs on these tags
            score = 0.0
            matches = 0
            
            for tag in query_tags:
                tag_count = data["tags"].get(tag, 0)
                if tag_count > 0:
                    # Calculate tag score based on relative frequency
                    total_queries = data["count"]
                    tag_frequency = tag_count / total_queries
                    tag_score = tag_frequency * 10  # Scale to 0-10 range
                    score += tag_score
                    matches += 1
            
            # Calculate average score if any matches found
            if matches > 0:
                avg_score = score / matches
                # Adjust score based on overall quality
                quality_boost = data["avg_quality"] / 5.0  # Scale to 0-2 range
                final_score = avg_score * quality_boost
                
                # Boosted if all tags match
                if matches == len(query_tags) and len(query_tags) > 1:
                    final_score *= 1.5
                    
                model_scores[model_name] = final_score
        
        # Find best model
        if not model_scores:
            return None, 0.0
            
        best_model = max(model_scores.items(), key=lambda x: x[1])
        model_name, score = best_model
        
        # Calculate confidence (normalized to 0-1)
        confidence = min(1.0, score / 10.0)
        
        return model_name, confidence
    
    def update_model_selection(self, experiment_id: str, user_override: bool, 
                             new_winner: str, feedback_data: Dict[str, Any]) -> bool:
        """
        Update a model selection record based on A/B testing feedback.
        
        Args:
            experiment_id: ID of the experiment to update
            user_override: Whether the user overrode the algorithmic selection
            new_winner: The model selected by the user as the winner
            feedback_data: Additional feedback data from the user
            
        Returns:
            bool: True if the update was successful
        """
        # Record this feedback in the experiment feedback section
        if "experiments" not in self.insights:
            self.insights["experiments"] = {}
            
        # Store experiment feedback
        self.insights["experiments"][experiment_id] = {
            "user_override": user_override,
            "algorithm_winner": feedback_data.get("algorithm_winner"),
            "user_winner": new_winner,
            "feedback": feedback_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update model statistics to reflect this feedback
        if new_winner in self.insights["models"]:
            model_data = self.insights["models"][new_winner]
            
            # Increment user selection count
            if "user_selections" not in model_data:
                model_data["user_selections"] = 0
            model_data["user_selections"] += 1
            
            # If user provided specific quality feedback, update quality metrics
            if "quality_rating" in feedback_data:
                quality_rating = feedback_data["quality_rating"]
                if isinstance(quality_rating, (int, float)) and 0 <= quality_rating <= 10:
                    # Update running average of user-provided quality ratings
                    if "user_quality_ratings" not in model_data:
                        model_data["user_quality_ratings"] = []
                    model_data["user_quality_ratings"].append(quality_rating)
                    
                    # Calculate new average
                    model_data["user_avg_quality"] = sum(model_data["user_quality_ratings"]) / len(model_data["user_quality_ratings"])
            
            # Update tag performance if we have tags
            if "query_tags" in feedback_data and isinstance(feedback_data["query_tags"], list):
                for tag in feedback_data["query_tags"]:
                    if "tag_user_selections" not in model_data:
                        model_data["tag_user_selections"] = {}
                    model_data["tag_user_selections"][tag] = model_data["tag_user_selections"].get(tag, 0) + 1
        
        # Save the updated insights
        self._save_insights()
        return True
        
    def get_model_insights(self) -> List[Dict]:
        """
        Get formatted insights for each model for the dashboard.
        
        Returns:
            List of model insight dictionaries
        """
        models = []
        colors = {
            "openai": "bg-primary",
            "claude": "bg-danger",
            "huggingface": "bg-success"
        }
        
        for model_name, data in self.insights["models"].items():
            # Skip models with no usage
            if data["count"] == 0:
                continue
            
            # Calculate best complexity range
            complexity_range = self._get_best_complexity_range(data["complexity_scores"])
            
            # Get top tags
            best_tags = []
            if data["tags"]:
                top_tags = sorted(data["tags"].items(), key=lambda x: x[1], reverse=True)[:3]
                tag_colors = ["primary", "success", "info", "warning", "danger"]
                for i, (tag, count) in enumerate(top_tags):
                    color = tag_colors[i % len(tag_colors)]
                    best_tags.append({"name": tag, "color": color})
            
            # Calculate feedback stats
            positive = data["feedback"].get("positive", 0)
            negative = data["feedback"].get("negative", 0)
            feedback_percentage = (positive / (positive + negative) * 100) if (positive + negative) > 0 else 0
            
            models.append({
                "name": model_name.capitalize(),
                "success_rate": round(data["success_rate"], 1),
                "avg_quality": round(data["avg_quality"], 2),
                "feedback_positive": round(feedback_percentage, 1),
                "complexity_range": complexity_range,
                "best_tags": best_tags,
                "bg_color": colors.get(model_name, "bg-secondary")
            })
        
        return models
    
    def _get_best_complexity_range(self, complexity_scores: Dict[str, int]) -> Tuple[float, float]:
        """Determine the best complexity range for a model based on its performance."""
        if not complexity_scores:
            return (0, 10)
        
        # Convert string keys to floats and sort
        scores = [(float(k), v) for k, v in complexity_scores.items()]
        scores.sort()
        
        if len(scores) == 1:
            # Only one data point
            point = scores[0][0]
            return (max(point - 1, 0), min(point + 1, 10))
        
        # Find the range with the highest selection count
        total = sum(count for _, count in scores)
        
        # Start from the most frequent complexity level
        best = max(scores, key=lambda x: x[1])
        lower = best[0]
        upper = best[0]
        covered = best[1]
        
        # Expand the range to cover 80% of selections
        target = total * 0.8
        scores.sort(key=lambda x: abs(x[0] - best[0]))  # Sort by distance to best
        
        for compl, count in scores[1:]:
            if covered >= target:
                break
            if compl < lower:
                lower = compl
            if compl > upper:
                upper = compl
            covered += count
        
        return (lower, upper)
    
    def get_recent_selections(self, limit: int = 10) -> List[Dict]:
        """
        Get the most recent model selections.
        
        Args:
            limit: Maximum number of selections to return
            
        Returns:
            List of recent selection dictionaries
        """
        recent = sorted(
            self.selections["selections"], 
            key=lambda x: x["timestamp"], 
            reverse=True
        )[:limit]
        
        # Format the data for display
        result = []
        for selection in recent:
            time_str = datetime.fromisoformat(selection["timestamp"]).strftime("%H:%M:%S")
            
            result.append({
                "time": time_str,
                "query": selection["query"],
                "complexity": f"{selection['complexity']:.1f}",
                "model": selection["selected_model"].capitalize(),
                "quality": f"{selection['quality_score']:.2f}",
                "feedback": selection["feedback"]
            })
        
        return result
    
    def get_dashboard_data(self) -> Dict:
        """
        Get all data needed for the insights dashboard.
        
        Returns:
            Dictionary with all dashboard data
        """
        # Calculate basic stats
        total_queries = self.insights["total_queries"]
        
        # Calculate average quality score
        quality_scores = [s["quality_score"] for s in self.selections["selections"] if "quality_score" in s]
        avg_quality = round(statistics.mean(quality_scores), 2) if quality_scores else 0
        
        # Calculate positive feedback percentage
        positive = self.insights["feedback"].get("positive", 0)
        negative = self.insights["feedback"].get("negative", 0)
        positive_feedback = round((positive / (positive + negative) * 100), 1) if (positive + negative) > 0 else 0
        
        # Calculate average complexity
        complexities = [s["complexity"] for s in self.selections["selections"] if "complexity" in s]
        avg_complexity = round(statistics.mean(complexities), 2) if complexities else 0
        
        # Get model performance by complexity
        model_complexity_data = self.get_model_performance_by_complexity()
        
        # Format data for template
        return {
            "total_queries": total_queries,
            "query_change": "+5.2",  # Placeholder - would calculate from historical data
            "avg_quality": avg_quality,
            "quality_change": "+1.8",  # Placeholder
            "positive_feedback": positive_feedback,
            "feedback_change": "+3.1",  # Placeholder
            "avg_complexity": avg_complexity,
            "complexity_change": "-0.7",  # Placeholder
            "openai_by_complexity": model_complexity_data["openai"],
            "claude_by_complexity": model_complexity_data["claude"],
            "huggingface_by_complexity": model_complexity_data["huggingface"],
            "quality_by_model": self.get_quality_scores_by_model(),
            "models": self.get_model_insights(),
            "recent_selections": self.get_recent_selections(limit=15)
        }


    def record_evaluation(self, evaluation_data: Dict[str, Any]) -> None:
        """
        Record a model evaluation from the Think Tank process.
        
        Args:
            evaluation_data: Data from the model evaluation process including scores and selected model
        """
        try:
            # Enhanced debugging
            logger.info(f"[THINK TANK DEBUG] RECORDING EVALUATION with data: {json.dumps(evaluation_data, indent=2)[:500]}...")
            
            # Get timestamp or use current time
            timestamp = evaluation_data.get('timestamp', time.time())
            
            # Handle different timestamp formats
            if isinstance(timestamp, str):
                try:
                    # Try to extract a numeric timestamp from ISO format
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.split('.')[0])
                    timestamp_ms = int(dt.timestamp() * 1000)
                    eval_id = evaluation_data.get('evaluation_id', str(timestamp_ms))
                except Exception as e:
                    # Fallback to current time if parsing fails
                    logger.warning(f"Could not parse timestamp {timestamp}: {e}")
                    eval_id = evaluation_data.get('evaluation_id', str(int(time.time() * 1000)))
            else:
                # Numeric timestamp
                eval_id = evaluation_data.get('evaluation_id', str(int(timestamp * 1000)))
            
            # Log models that were compared
            models_compared = evaluation_data.get('models_compared', [])
            logger.info(f"[THINK TANK] Models compared in this evaluation: {models_compared}")
            best_model = evaluation_data.get('best_model', '')
            logger.info(f"[THINK TANK] Best model selected: {best_model}")
            
            # Create a record in the evaluations collection
            self.db['think_tank_evaluations'][eval_id] = {
                'timestamp': timestamp,
                'query': evaluation_data.get('query', ''),
                'query_tags': evaluation_data.get('query_tags', []),
                'best_model': best_model,
                'models_compared': models_compared,
                'scores': evaluation_data.get('all_scores', {}),
                'detailed_scores': evaluation_data.get('detailed_scores', {}),
                'quality_score': evaluation_data.get('quality_score', 0.0),
                'query_complexity': evaluation_data.get('query_complexity', 5),
            }
            
            # Limit the collection to the last 100 evaluations
            if len(self.db['think_tank_evaluations']) > 100:
                # Find and remove the oldest evaluation
                oldest_id = min(self.db['think_tank_evaluations'].keys(), 
                               key=lambda k: self.db['think_tank_evaluations'][k].get('timestamp', 0))
                del self.db['think_tank_evaluations'][oldest_id]
            
            # Log current size
            logger.info(f"[THINK TANK DEBUG] Current evaluation count: {len(self.db['think_tank_evaluations'])}")
                
            self.save_to_disk()  # Persist changes
            
            logger.info(f"[THINK TANK] Recorded evaluation {eval_id} for query: {evaluation_data.get('query', '')[:50]}...")
            
            return eval_id
        except Exception as e:
            logging.error(f"[THINK TANK] Error recording evaluation: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_think_tank_evaluations(self) -> Dict[str, Any]:
        """
        Get statistics and insights from the think tank evaluations.
        
        Returns:
            Dict containing various statistics about think tank performance.
        """
        if 'think_tank_evaluations' not in self.db or not self.db['think_tank_evaluations']:
            return {
                "total_evaluations": 0,
                "models_evaluated": [],
                "recent_evaluations": [],
                "model_performance": {},
                "tag_performance": {},
                "think_tank_stats": {
                    "evaluations": 0,
                    "avg_models_compared": 0,
                    "top_performing_models": []
                }
            }
        
        # Process evaluations
        model_scores = {}
        tag_performance = {}
        query_complexities = []
        recent_evals = []
        
        for eval_id, eval_data in self.db['think_tank_evaluations'].items():
            # Track model scores
            best_model = eval_data.get('best_model', '')
            if best_model:
                if best_model not in model_scores:
                    model_scores[best_model] = {
                        'count': 0,
                        'total_score': 0,
                        'scores': []
                    }
                
                quality_score = eval_data.get('quality_score', 0)
                model_scores[best_model]['count'] += 1
                model_scores[best_model]['total_score'] += quality_score
                model_scores[best_model]['scores'].append(quality_score)
            
            # Track query tag performance
            for tag in eval_data.get('query_tags', []):
                if tag not in tag_performance:
                    tag_performance[tag] = {
                        'count': 0,
                        'total_score': 0,
                        'best_model': None,
                        'best_score': 0
                    }
                
                tag_performance[tag]['count'] += 1
                tag_performance[tag]['total_score'] += eval_data.get('quality_score', 0)
                
                if eval_data.get('quality_score', 0) > tag_performance[tag]['best_score']:
                    tag_performance[tag]['best_score'] = eval_data.get('quality_score', 0)
                    tag_performance[tag]['best_model'] = best_model
            
            # Track query complexity
            if 'query_complexity' in eval_data:
                query_complexities.append(eval_data['query_complexity'])
            
            # Add to recent evaluations
            recent_evals.append({
                'id': eval_id,
                'timestamp': eval_data.get('timestamp'),
                'query': eval_data.get('query', '')[:100] + '...' if len(eval_data.get('query', '')) > 100 else eval_data.get('query', ''),
                'best_model': best_model,
                'quality_score': eval_data.get('quality_score', 0),
                'models_compared': eval_data.get('models_compared', [])
            })
        
        # Calculate averages for model performance
        model_performance = {}
        for model, data in model_scores.items():
            if data['count'] > 0:
                model_performance[model] = {
                    'count': data['count'],
                    'average_score': data['total_score'] / data['count'],
                    'latest_scores': data['scores'][-5:] if len(data['scores']) > 5 else data['scores']
                }
        
        # Sort recent evaluations by timestamp (newest first)
        recent_evals = sorted(recent_evals, key=lambda x: x.get('timestamp', 0), reverse=True)[:10]
        
        # Calculate tag performance averages
        for tag, data in tag_performance.items():
            if data['count'] > 0:
                data['average_score'] = data['total_score'] / data['count']
        
        # Find top performing models
        top_models = []
        if model_performance:
            top_models = sorted(
                [(model, data['average_score']) for model, data in model_performance.items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]  # Top 3 models
        
        # Calculate think tank stats
        num_evaluations = len(self.db['think_tank_evaluations'])
        avg_models_compared = sum(len(eval_data.get('models_compared', [])) 
                                  for eval_data in self.db['think_tank_evaluations'].values()) / num_evaluations \
                             if num_evaluations > 0 else 0
        
        return {
            "total_evaluations": num_evaluations,
            "models_evaluated": list(model_scores.keys()),
            "recent_evaluations": recent_evals,
            "model_performance": model_performance,
            "tag_performance": tag_performance,
            "query_complexity": sum(query_complexities) / len(query_complexities) if query_complexities else 0,
            "think_tank_stats": {
                "evaluations": num_evaluations,
                "avg_models_compared": round(avg_models_compared, 1),
                "top_performing_models": top_models
            }
        }


# Create a singleton instance
model_insights_manager = ModelInsightsManager()

# Add a get_instance method for compatibility
def get_instance():
    """
    Returns the singleton instance of the ModelInsightsManager.
    """
    return model_insights_manager

# Add get_instance as a class method for better compatibility
ModelInsightsManager.get_instance = staticmethod(get_instance)
