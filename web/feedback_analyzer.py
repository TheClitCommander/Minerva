#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feedback Analyzer System

Analyzes collected user feedback to improve Think Tank response generation.
This module bridges feedback data with the Think Tank processor,
creating a self-learning loop.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Import our components
from web.feedback_handler import FeedbackHandler
try:
    from web.think_tank_processor import get_model_weights, update_model_weights
except ImportError:
    # Mock functions for testing
    def get_model_weights():
        return {"gpt4": 1.0, "claude3": 1.0, "gemini": 1.0, "mistral7b": 0.8, "llama2": 0.7}
        
    def update_model_weights(new_weights):
        print(f"Would update model weights to: {new_weights}")
        return True

# Configure logging
logger = logging.getLogger(__name__)

class FeedbackAnalyzer:
    """Analyzes feedback data to improve Think Tank model selection."""
    
    def __init__(self, feedback_handler: Optional[FeedbackHandler] = None):
        """Initialize the feedback analyzer.
        
        Args:
            feedback_handler: Optional FeedbackHandler instance. If None, creates a new one.
        """
        self.feedback_handler = feedback_handler or FeedbackHandler()
        self.learning_rate = 0.05  # How quickly to adjust weights (0.01-0.1 is reasonable)
        self.recency_window = 30   # Consider feedback from last 30 days as most relevant
    
    def analyze_and_update_models(self, query_type_boost: bool = True) -> Dict[str, Any]:
        """Analyze feedback and update model weights accordingly.
        
        Args:
            query_type_boost: Whether to adjust weights by query type
            
        Returns:
            Dict with updated weights and analysis statistics
        """
        # Get current model weights
        current_weights = get_model_weights()
        
        # Get feedback statistics by model
        model_stats = self.feedback_handler.get_model_performance()
        
        # Calculate weight adjustments based on feedback
        weight_adjustments = self._calculate_weight_adjustments(model_stats, current_weights)
        
        # Apply adjustments to current weights
        new_weights = {}
        for model, current_weight in current_weights.items():
            adjustment = weight_adjustments.get(model, 0)
            new_weights[model] = max(0.1, min(2.0, current_weight + adjustment))
        
        # Normalize weights if needed
        if sum(new_weights.values()) > 0:
            weight_scale = len(new_weights) / sum(new_weights.values())
            if weight_scale < 0.5 or weight_scale > 2.0:
                # Scale weights to have an average of 1.0
                new_weights = {model: weight * weight_scale for model, weight in new_weights.items()}
        
        # Apply query type specific adjustments if requested
        query_type_adjustments = {}
        if query_type_boost:
            query_analysis = self.analyze_query_patterns()
            query_effectiveness = query_analysis.get('query_effectiveness', {})
            
            if query_effectiveness:
                # For each query type, identify the best model and try to boost it
                for query_type, data in query_effectiveness.items():
                    # Only consider query types with sufficient data
                    if data['sample_size'] >= 5 and data['helpful_percentage'] >= 70:
                        best_model = data['best_model']
                        if best_model in new_weights:
                            # Store this adjustment
                            query_type_adjustments[query_type] = best_model
                            
                logger.info(f"Identified model specializations for query types: {query_type_adjustments}")
                
                try:
                    # Try to update the router for query-specific routing
                    self._update_query_type_routing(query_type_adjustments)
                except Exception as e:
                    logger.warning(f"Could not update query type routing: {e}")
        
        # Update model weights in the Think Tank processor
        success = update_model_weights(new_weights)
        
        # Log the update
        if success:
            logger.info(f"Updated model weights based on feedback: {new_weights}")
        else:
            logger.error("Failed to update model weights")
        
        return {
            "previous_weights": current_weights,
            "updated_weights": new_weights,
            "adjustments": weight_adjustments,
            "query_type_adjustments": query_type_adjustments,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "statistics": model_stats
        }
    
    def _calculate_weight_adjustments(
        self, 
        model_stats: Dict[str, Dict[str, Any]], 
        current_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate how much to adjust each model's weight based on feedback.
        
        Args:
            model_stats: Statistics for each model's performance
            current_weights: Current model weights
            
        Returns:
            Dictionary mapping model names to weight adjustments
        """
        adjustments = {}
        
        # Get recent feedback for recency bias
        recent_cutoff = datetime.now() - timedelta(days=self.recency_window)
        recent_feedback = self.feedback_handler.get_feedback_by_date_range(
            start_date=recent_cutoff.isoformat()
        )
        
        # Calculate recency-weighted helpfulness scores
        recent_model_scores = defaultdict(lambda: {"helpful": 0, "not_helpful": 0})
        for feedback in recent_feedback:
            model = feedback.get("model")
            if not model:
                continue
                
            if feedback.get("feedback") == "helpful":
                recent_model_scores[model]["helpful"] += 1
            else:
                recent_model_scores[model]["not_helpful"] += 1
        
        # Create adjustments for each model
        for model, stats in model_stats.items():
            if model not in current_weights:
                continue
                
            if stats["total_feedback"] < 3:
                # Not enough data to make adjustments
                adjustments[model] = 0
                continue
            
            # Base adjustment on helpful percentage
            helpful_pct = stats["helpful_percentage"] / 100.0
            base_adjustment = (helpful_pct - 0.5) * 2 * self.learning_rate
            
            # Add recency bias
            recent = recent_model_scores.get(model, {"helpful": 0, "not_helpful": 0})
            recent_total = recent["helpful"] + recent["not_helpful"]
            
            if recent_total > 0:
                recent_helpful_pct = recent["helpful"] / recent_total
                recency_adjustment = (recent_helpful_pct - 0.5) * self.learning_rate
                
                # Weight the recent adjustment more heavily
                adjustment = (base_adjustment * 0.7) + (recency_adjustment * 0.3)
            else:
                adjustment = base_adjustment
            
            adjustments[model] = adjustment
        
        return adjustments
    
    def analyze_query_patterns(self) -> Dict[str, Any]:
        """Analyze query patterns to identify strengths/weaknesses by query type.
        
        Returns:
            Dictionary with query pattern analysis
        """
        # Get all feedback data
        all_feedback = self.feedback_handler.feedback_data
        
        # Extract query patterns
        query_patterns = defaultdict(lambda: {"helpful": 0, "not_helpful": 0, "models": defaultdict(int)})
        
        for feedback in all_feedback:
            query = feedback.get("query", "").lower()
            if not query:
                continue
                
            # Identify query types (simplified approach)
            query_type = self._identify_query_type(query)
            
            # Record result
            is_helpful = feedback.get("feedback") == "helpful"
            model = feedback.get("model", "unknown")
            
            if is_helpful:
                query_patterns[query_type]["helpful"] += 1
            else:
                query_patterns[query_type]["not_helpful"] += 1
                
            query_patterns[query_type]["models"][model] += 1
        
        # Calculate effectiveness by query type
        query_effectiveness = {}
        for query_type, stats in query_patterns.items():
            total = stats["helpful"] + stats["not_helpful"]
            if total < 3:
                continue  # Not enough data
                
            helpful_pct = (stats["helpful"] / total) * 100
            
            # Find best model for this query type
            best_model = max(stats["models"].items(), key=lambda x: x[1])[0]
            
            query_effectiveness[query_type] = {
                "helpful_percentage": helpful_pct,
                "sample_size": total,
                "best_model": best_model
            }
        
        return {
            "query_effectiveness": query_effectiveness,
            "timestamp": datetime.now().isoformat()
        }
    
    def _identify_query_type(self, query: str) -> str:
        """Identify the type of query based on text patterns.
        
        Args:
            query: The user query text
            
        Returns:
            String identifying the query type
        """
        query = query.lower()
        
        # Enhanced pattern matching (could be further improved with ML/NLP)
        if any(code in query for code in ["code", "function", "program", "implement", "script", "class", "method"]):
            return "technical_coding"
        elif any(math in query for math in ["calculate", "equation", "formula", "solve", "math", "computation"]):
            return "technical_math"
        elif "how" in query and "to" in query:
            return "how_to"
        elif "what is" in query or "what are" in query or "define" in query or "meaning of" in query:
            return "definition"
        elif "why" in query:
            return "explanation"
        elif "?" in query and any(w in query for w in ["when", "where", "who", "which"]):
            return "factual"
        elif "compare" in query or "difference" in query or "versus" in query or " vs " in query:
            return "comparison"
        elif any(creative in query for creative in ["design", "create", "imagine", "story", "write", "essay"]):
            return "creative"
        elif any(w in query for w in ["list", "steps", "process", "procedure", "guide"]):
            return "list_steps" 
        elif any(reason in query for reason in ["analyze", "evaluate", "consider", "argument", "implications"]):
            return "reasoning"
        else:
            return "general"
    
    def _update_query_type_routing(self, query_type_adjustments: Dict[str, str]) -> None:
        """Update the router to prioritize specific models for query types.
        
        Args:
            query_type_adjustments: Mapping of query type to best model
            
        Raises:
            Exception: If there's an issue updating the router
        """
        try:
            # Set a path for the specialized model mapping
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, 'data', 'query_type_model_mappings.json')
            
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Load existing mappings if available
            existing_mappings = {}
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        existing_mappings = json.load(f)
                except (json.JSONDecodeError, IOError):
                    logger.warning(f"Could not load existing query type mappings from {config_path}")
            
            # Merge the new mappings with existing ones
            updated_mappings = {**existing_mappings, **query_type_adjustments}
            
            # Save the updated mappings
            with open(config_path, 'w') as f:
                json.dump(updated_mappings, f, indent=2)
                
            logger.info(f"Updated query type model mappings at {config_path}")
            
            # Try to inform the router about the updates - this depends on how the router is implemented
            # For now, we just save the file and assume that the router will check it periodically
            # In a more integrated system, we could directly update the router's configuration
            
        except Exception as e:
            logger.error(f"Failed to update query type routing: {str(e)}")
            raise
            
    def _get_model_adjustment_recommendations(self, model_stats: List[Dict[str, Any]], 
                                               query_type_stats: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Generate model adjustment recommendations based on feedback data.
        
        This method analyzes model performance across different query types and
        provides specific recommendations for routing improvements.
        
        Args:
            model_stats: List of dictionaries with model stats
            query_type_stats: Statistics by query type
            
        Returns:
            Dict with model adjustment recommendations
        """
        recommendations = {}
        
        # Define query type categories and their corresponding capability names
        query_type_mapping = {
            'technical': ['technical', 'coding', 'programming', 'development'],
            'creative': ['creative', 'writing', 'ideation', 'brainstorming'],
            'reasoning': ['reasoning', 'logic', 'problem_solving', 'analytical'],
            'factual': ['factual', 'knowledge', 'information', 'data'],
            'general': ['general', 'conversational', 'chat']
        }
        
        # 1. Identify top and bottom performing models overall
        model_performances = []
        model_query_type_scores = {}  # Store scores by model and query type
        
        for model_data in model_stats:
            model = model_data.get('model')
            stats = model_data.get('stats', {})
            
            helpful = stats.get('helpful', 0)
            not_helpful = stats.get('not_helpful', 0)
            total = helpful + not_helpful
            
            if total < 5:  # Ignore models with very little feedback
                continue
                
            helpful_pct = (helpful / total * 100) if total > 0 else 0
            
            # Calculate the trend (if available)
            recent_stats = stats.get('recent', {})
            recent_helpful = recent_stats.get('helpful', 0)
            recent_not_helpful = recent_stats.get('not_helpful', 0)
            recent_total = recent_helpful + recent_not_helpful
            
            recent_helpful_pct = (recent_helpful / recent_total * 100) if recent_total > 3 else helpful_pct
            trend = recent_helpful_pct - helpful_pct if recent_total > 3 else 0
            
            model_performances.append({
                'model': model,
                'helpful_percentage': helpful_pct,
                'feedback_count': total,
                'trend': trend,
                'recent_helpful_percentage': recent_helpful_pct if recent_total > 3 else None
            })
            
            # Process query type breakdown
            query_breakdown = stats.get('query_types', {})
            model_query_type_scores[model] = {}
            
            for query_type, type_data in query_breakdown.items():
                helpful = type_data.get('helpful', 0)
                not_helpful = type_data.get('not_helpful', 0)
                total = helpful + not_helpful
                
                if total < 3:  # Need minimum data points
                    continue
                    
                score = (helpful / total * 100) if total > 0 else 0
                
                # Store the score for this model and query type
                model_query_type_scores[model][query_type] = {
                    'score': score,
                    'total': total
                }
        
        # Sort by helpful percentage
        model_performances.sort(key=lambda x: x['helpful_percentage'], reverse=True)
        
        # Get top and bottom performers
        top_performers = model_performances[:2] if len(model_performances) >= 2 else model_performances
        bottom_performers = model_performances[-2:] if len(model_performances) >= 4 else []
        
        # Extract improving and declining models
        improving_models = [m for m in model_performances if m.get('trend', 0) > 5]  # 5% improvement
        declining_models = [m for m in model_performances if m.get('trend', 0) < -5]  # 5% decline
        
        # Create general recommendation text
        general_recommendation = ""
        if top_performers:
            general_recommendation = f"Prioritize {', '.join([m['model'] for m in top_performers])} for general queries"
            
            if improving_models:
                improving_names = ', '.join([m['model'] for m in improving_models])
                general_recommendation += f". {improving_names} {'is' if len(improving_models) == 1 else 'are'} showing improved performance recently"
        else:
            general_recommendation = "Insufficient data for general recommendations"
        
        # Add general recommendations based on top/bottom performers
        recommendations['general'] = {
            'top_models': [m['model'] for m in top_performers],
            'bottom_models': [m['model'] for m in bottom_performers],
            'improving_models': [m['model'] for m in improving_models],
            'declining_models': [m['model'] for m in declining_models],
            'recommendation': general_recommendation
        }
        
        # 2. Analyze performance by query type
        query_type_recommendations = {}
        
        # Group similar query types using the mapping
        grouped_query_types = {}
        for query_type, type_stats in query_type_stats.items():
            # Skip query types with little data
            if type_stats.get('helpful', 0) + type_stats.get('not_helpful', 0) < 5:
                continue
                
            # Find which category this query type belongs to
            category_found = False
            for category, related_types in query_type_mapping.items():
                if any(related in query_type.lower() for related in related_types):
                    if category not in grouped_query_types:
                        grouped_query_types[category] = []
                        
                    grouped_query_types[category].append(query_type)
                    category_found = True
                    break
            
            if not category_found:
                # Put in a misc category if no match found
                if 'misc' not in grouped_query_types:
                    grouped_query_types['misc'] = []
                    
                grouped_query_types['misc'].append(query_type)
        
        # Process each category of query types
        for category, query_types in grouped_query_types.items():
            # Find the best model for this category of query types
            model_category_scores = {}
            
            for model in model_query_type_scores:
                # Calculate combined score for this model across all query types in this category
                category_data = {
                    'total_score': 0,
                    'total_samples': 0,
                    'query_types_covered': 0
                }
                
                for query_type in query_types:
                    if query_type in model_query_type_scores[model]:
                        type_data = model_query_type_scores[model][query_type]
                        category_data['total_score'] += type_data['score'] * type_data['total']
                        category_data['total_samples'] += type_data['total']
                        category_data['query_types_covered'] += 1
                
                if category_data['total_samples'] > 0:
                    # Calculate average score weighted by sample size
                    avg_score = category_data['total_score'] / category_data['total_samples']
                    
                    # Adjust for coverage - how many query types this model has data for
                    coverage_factor = category_data['query_types_covered'] / len(query_types)
                    
                    # Final weighted score
                    weighted_score = avg_score * coverage_factor
                    
                    model_category_scores[model] = {
                        'score': avg_score,
                        'weighted_score': weighted_score,
                        'coverage': coverage_factor,
                        'samples': category_data['total_samples']
                    }
            
            # Find the best model for this category
            if model_category_scores:
                best_model = max(model_category_scores.items(), key=lambda x: x[1]['weighted_score'])
                model_name = best_model[0]
                score_data = best_model[1]
                
                # Calculate confidence based on score and coverage
                confidence = score_data['weighted_score'] * min(1, score_data['samples'] / 15)  # Cap at 15 samples
                
                # Create query type specific recommendations
                query_list = ', '.join([qt.replace('_', ' ') for qt in query_types])
                query_type_recommendations[category] = {
                    'best_model': model_name,
                    'confidence': min(100, confidence),  # Cap at 100%
                    'coverage': score_data['coverage'] * 100,  # Convert to percentage
                    'recommendation': f"Route {category} queries ({query_list}) to {model_name}",
                    'query_types': query_types
                }
        
        recommendations['by_query_type'] = query_type_recommendations
        
        # 3. Generate specific action items
        actions = []
        
        # General model preference action
        if top_performers:
            top_model = top_performers[0]
            actions.append({
                'action': 'increase_weight',
                'model': top_model['model'],
                'amount': '+15%',
                'reason': f"Top performing model with {top_model['helpful_percentage']:.1f}% helpful rating across {top_model['feedback_count']} feedback instances"
            })
        
        # Improving model action
        if improving_models:
            improve_model = improving_models[0]
            actions.append({
                'action': 'increase_weight',
                'model': improve_model['model'],
                'amount': '+10%',
                'reason': f"Showing recent improvement trend of +{improve_model['trend']:.1f}% in helpful ratings"
            })
        
        # Bottom performer action
        if bottom_performers:
            bottom_model = bottom_performers[0]
            actions.append({
                'action': 'decrease_weight',
                'model': bottom_model['model'],
                'amount': '-10%',
                'reason': f"Underperforming with {bottom_model['helpful_percentage']:.1f}% helpful rating across {bottom_model['feedback_count']} instances"
            })
        
        # Declining model action
        if declining_models:
            decline_model = declining_models[0]
            actions.append({
                'action': 'decrease_weight',
                'model': decline_model['model'],
                'amount': '-15%',
                'reason': f"Showing declining performance trend of {decline_model['trend']:.1f}% in helpful ratings"
            })
        
        # Query type specific actions - prioritize high confidence categories
        for query_type, rec in query_type_recommendations.items():
            if rec.get('confidence', 0) >= 75:  # High confidence threshold
                actions.append({
                    'action': 'specialize',
                    'model': rec['best_model'],
                    'query_type': query_type,
                    'reason': f"Performs best for {query_type} queries with {rec['confidence']:.1f}% confidence based on user feedback"
                })
        
        # Add comprehensive action for route optimizations if we have enough data
        if len(query_type_recommendations) >= 3:
            routing_action = {
                'action': 'optimize_routing',
                'model': 'system',
                'reason': 'Update routing configuration based on query type specialization data:',
                'details': []
            }
            
            for query_type, rec in query_type_recommendations.items():
                if rec.get('confidence', 0) >= 60:  # Include medium confidence and above
                    routing_action['details'].append(
                        f"{query_type}: {rec['best_model']} ({rec['confidence']:.1f}% confidence)"
                    )
            
            if routing_action['details']:
                actions.append(routing_action)
        
        recommendations['actions'] = actions
        
        return recommendations
    
    def generate_feedback_report(self) -> Dict[str, Any]:
        """Generate a comprehensive feedback analysis report.
        
        Returns:
            Dictionary with feedback analysis report
        """
        # Get overall statistics
        overall_stats = self.feedback_handler.get_feedback_stats()
        
        # Get model performance
        model_stats = self.feedback_handler.get_model_performance()
        
        # Get query pattern analysis
        query_analysis = self.analyze_query_patterns()
        
        # Create recommendations based on the analysis
        recommendations = []
        
        # Low helpful percentage overall
        if overall_stats["helpful_percentage"] < 60 and overall_stats["total_feedback"] > 10:
            recommendations.append({
                "type": "overall_quality",
                "severity": "high",
                "message": "Overall helpful rating is below 60%. Consider reviewing model configurations."
            })
        
        # Model-specific recommendations
        for model, stats in model_stats.items():
            if stats["total_feedback"] < 5:
                continue
                
            if stats["helpful_percentage"] < 50:
                recommendations.append({
                    "type": "model_performance",
                    "model": model,
                    "severity": "high",
                    "message": f"Model {model} has a low helpful rating ({stats['helpful_percentage']:.1f}%). Consider reducing its weight."
                })
        
        # Query type recommendations
        for query_type, stats in query_analysis.get("query_effectiveness", {}).items():
            if stats["helpful_percentage"] < 50 and stats["sample_size"] >= 5:
                recommendations.append({
                    "type": "query_type",
                    "query_type": query_type,
                    "severity": "medium",
                    "message": f"Poor performance on {query_type} queries. Consider routing these to {stats['best_model']}."
                })
        
        return {
            "overall_statistics": overall_stats,
            "model_performance": model_stats,
            "query_analysis": query_analysis,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    
    def export_report_to_json(self, output_file: Optional[str] = None) -> str:
        """Export the feedback analysis report to a JSON file.
        
        Args:
            output_file: Path to output file. If None, creates a file in the feedback directory.
            
        Returns:
            Path to the created JSON file
        """
        report = self.generate_feedback_report()
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Get directory of the feedback handler's storage path
            base_dir = os.path.dirname(self.feedback_handler.storage_path)
            output_file = os.path.join(base_dir, f"feedback_report_{timestamp}.json")
            
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        return output_file


# Example usage
if __name__ == "__main__":
    # Initialize the analyzer
    analyzer = FeedbackAnalyzer()
    
    # Update model weights based on feedback
    update_result = analyzer.analyze_and_update_models()
    print(f"Updated model weights: {update_result['updated_weights']}")
    
    # Generate and export a report
    report_path = analyzer.export_report_to_json()
    print(f"Feedback analysis report exported to: {report_path}")
