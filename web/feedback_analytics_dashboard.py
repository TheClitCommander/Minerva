"""
Feedback Analytics Dashboard

This module implements an analytics dashboard for monitoring response quality metrics.
It provides visualizations and insights based on feedback data to guide continuous AI tuning.
"""

import os
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict, Counter

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import required modules
from users.feedback_analysis import feedback_analyzer
from users.global_feedback_manager import global_feedback_manager

class FeedbackAnalyticsDashboard:
    """
    Provides analytics and visualizations based on feedback data to monitor
    response quality and guide AI tuning.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the feedback analytics dashboard.
        
        Args:
            cache_dir: Directory for caching analytics results
        """
        # Set cache directory
        if cache_dir is None:
            base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.cache_dir = base_dir / "web" / "analytics" / "cache"
        else:
            self.cache_dir = cache_dir
            
        # Ensure directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Reference to the feedback analyzer
        self.feedback_analyzer = feedback_analyzer
        
        # Cache settings
        self.cache_ttl_seconds = 3600  # Cache results for 1 hour
        
        logger.info("Feedback Analytics Dashboard initialized")
    
    def get_dashboard_data(self, time_range: str = "last_30_days") -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for the specified time range.
        
        Args:
            time_range: Time range for analysis (last_24_hours, last_7_days, last_30_days, all_time)
            
        Returns:
            Dict containing dashboard data
        """
        # Check cache first
        cache_key = f"dashboard_{time_range}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Convert time range to days for analysis
        days_lookup = {
            "last_24_hours": 1,
            "last_7_days": 7,
            "last_30_days": 30,
            "last_90_days": 90,
            "all_time": 9999  # Effectively all time
        }
        lookback_days = days_lookup.get(time_range, 30)
        
        # Get global feedback analysis (fallback to simulated data for the demo)
        try:
            global_analysis = self.feedback_analyzer.analyze_global_feedback(lookback_days)
        except AttributeError:
            # For demo purposes, generate simulated global data
            logger.info("Using simulated global feedback data for dashboard")
            global_analysis = self._generate_simulated_global_analysis(lookback_days)
        
        # Get model performance data
        model_performance = self._get_model_performance_data(lookback_days)
        
        # Get feedback trends
        feedback_trends = self._get_feedback_trends(lookback_days)
        
        # Get improvement metrics
        improvement_metrics = self._get_improvement_metrics(lookback_days)
        
        # Assemble dashboard data
        dashboard_data = {
            "generated_at": datetime.now().isoformat(),
            "time_range": time_range,
            "lookback_days": lookback_days,
            "summary": {
                "total_feedback_count": global_analysis.get("feedback_count", 0),
                "positive_ratio": self._extract_positive_ratio(global_analysis),
                "response_quality_score": self._calculate_quality_score(global_analysis, model_performance),
                "most_common_issues": self._extract_top_issues(global_analysis, 5)
            },
            "feedback_patterns": global_analysis.get("patterns", {}),
            "model_performance": model_performance,
            "feedback_trends": feedback_trends,
            "improvement_metrics": improvement_metrics,
            "recommendations": global_analysis.get("recommendations", {})
        }
        
        # Cache the results
        self._cache_data(cache_key, dashboard_data)
        
        return dashboard_data
    
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get insights specific to a particular user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dict containing user-specific insights
        """
        # Get user feedback analysis
        user_analysis = self.feedback_analyzer.analyze_user_feedback(user_id)
        
        # Get user's optimized parameters
        # Note: This would need to be updated to actually use a message
        dummy_message = "This is a placeholder message for parameter optimization"
        from users.adaptive_response_optimizer import response_optimizer
        optimized_params = response_optimizer.get_optimized_parameters(user_id, dummy_message)
        
        # Assemble user insights
        user_insights = {
            "generated_at": datetime.now().isoformat(),
            "user_id": user_id,
            "feedback_count": user_analysis.get("feedback_count", 0),
            "feedback_patterns": user_analysis.get("patterns", {}),
            "confidence_score": user_analysis.get("confidence_score", 0.0),
            "recommendations": user_analysis.get("recommendations", {}),
            "optimized_parameters": optimized_params
        }
        
        return user_insights
    
    def get_quality_trends(self, metric: str = "positive_ratio", time_range: str = "last_30_days") -> Dict[str, Any]:
        """
        Get trend data for a specific quality metric over time.
        
        Args:
            metric: Quality metric to analyze (positive_ratio, detail_score, etc.)
            time_range: Time range for analysis
            
        Returns:
            Dict containing trend data
        """
        # Convert time range to days
        days_lookup = {
            "last_7_days": 7,
            "last_30_days": 30,
            "last_90_days": 90
        }
        lookback_days = days_lookup.get(time_range, 30)
        
        # This would be implemented to extract trend data from the feedback database
        # Here we're returning a placeholder with simulated trend data
        
        # Simulated trend data
        if metric == "positive_ratio":
            # Simulate daily positive ratio data
            today = datetime.now().date()
            trend_data = []
            
            # Start with a base value and add some randomness
            base_value = 0.75
            for i in range(lookback_days):
                date = today - timedelta(days=i)
                # Gradually improve over time with some noise
                improvement_factor = i / (lookback_days * 2)  # Max 0.5 improvement
                noise = (hash(str(date)) % 20 - 10) / 100  # -0.1 to 0.1 noise
                value = min(0.95, base_value + improvement_factor + noise)
                
                trend_data.append({
                    "date": date.isoformat(),
                    "value": value
                })
            
            # Reverse to get chronological order
            trend_data.reverse()
            
            return {
                "metric": metric,
                "time_range": time_range,
                "data": trend_data,
                "trend_summary": {
                    "start_value": trend_data[0]["value"] if trend_data else 0,
                    "end_value": trend_data[-1]["value"] if trend_data else 0,
                    "change": (trend_data[-1]["value"] - trend_data[0]["value"]) if trend_data else 0
                }
            }
        
        # Default empty response for unsupported metrics
        return {
            "metric": metric,
            "time_range": time_range,
            "data": [],
            "error": "Unsupported metric"
        }
    
    def get_feedback_distribution(self, category: str = "all", time_range: str = "last_30_days") -> Dict[str, Any]:
        """
        Get distribution of feedback across different dimensions.
        
        Args:
            category: Feedback category to analyze (all, length, detail, tone, etc.)
            time_range: Time range for analysis
            
        Returns:
            Dict containing distribution data
        """
        # Convert time range to days
        days_lookup = {
            "last_7_days": 7,
            "last_30_days": 30,
            "last_90_days": 90
        }
        lookback_days = days_lookup.get(time_range, 30)
        
        # Get global analysis (fallback to simulated data for the demo)
        try:
            global_analysis = self.feedback_analyzer.analyze_global_feedback(lookback_days)
        except AttributeError:
            # For demo purposes, generate simulated global data
            logger.info("Using simulated global feedback data for dashboard")
            global_analysis = self._generate_simulated_global_analysis(lookback_days)
        patterns = global_analysis.get("patterns", {})
        
        # Extract distribution data
        distribution = {}
        
        if category == "all":
            # Get distributions for all categories
            for cat, issues in patterns.items():
                if cat != "overall" and isinstance(issues, dict):
                    distribution[cat] = issues
        elif category in patterns:
            # Get distribution for specific category
            distribution = {category: patterns.get(category, {})}
        
        return {
            "category": category,
            "time_range": time_range,
            "distribution": distribution,
            "total_count": global_analysis.get("feedback_count", 0)
        }
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get data from cache if available and not expired.
        
        Args:
            cache_key: Key for the cached data
            
        Returns:
            Cached data if available, None otherwise
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            # Check if cache is expired
            file_modified_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if (datetime.now() - file_modified_time).total_seconds() > self.cache_ttl_seconds:
                logger.info(f"Cache expired for {cache_key}")
                return None
            
            # Read cache
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded data from cache: {cache_key}")
            return data
        
        except Exception as e:
            logger.error(f"Error reading from cache: {str(e)}")
            return None
    
    def _cache_data(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """
        Cache data for future use.
        
        Args:
            cache_key: Key for the cached data
            data: Data to cache
            
        Returns:
            True if successful, False otherwise
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Cached data for {cache_key}")
            return True
        
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")
            return False
    
    def _get_model_performance_data(self, lookback_days: int) -> Dict[str, Any]:
        """
        Get performance data for different AI models.
        
        Args:
            lookback_days: Number of days to look back
            
        Returns:
            Dict containing model performance data
        """
        # This would normally get real data from the feedback analyzer
        # For demo purposes, we'll use simulated data
        
        # Simulated model performance data
        model_names = ["openai_gpt4", "anthropic_claude", "local_model"]
        
        # Generate simulated performance data
        all_models = self._generate_simulated_model_performance(None, lookback_days)
        
        # Get performance for each model
        model_data = {}
        for model in model_names:
            model_data[model] = self._generate_simulated_model_performance(model, lookback_days)
        
        return {
            "overall": all_models,
            "by_model": model_data
        }
        
    def _generate_simulated_model_performance(self, model_name: Optional[str], lookback_days: int) -> Dict[str, Any]:
        """
        Generate simulated model performance data for demonstration purposes.
        
        Args:
            model_name: Name of the model, or None for all models combined
            lookback_days: Number of days to look back
            
        Returns:
            Dict containing simulated model performance data
        """
        # Base data with some randomization based on model name hash
        if model_name:
            # Add some variation based on model name
            base_value = 0.75 + (hash(model_name) % 15) / 100  # 0.75-0.89
        else:
            # Overall average is slightly higher than individual models
            base_value = 0.82
        
        # Response time varies by model
        if model_name == "openai_gpt4":
            avg_response_time = 2.3
        elif model_name == "anthropic_claude":
            avg_response_time = 2.8
        elif model_name == "local_model":
            avg_response_time = 0.9
        else:
            avg_response_time = 2.0
        
        # Generate performance metrics
        performance_metrics = {
            "positive_ratio": min(0.95, base_value + 0.03),
            "relevance_score": min(0.95, base_value + 0.01),
            "completion_rate": min(0.98, base_value + 0.1),
            "avg_response_time": avg_response_time,
            "category_scores": {
                "informational": min(0.95, base_value + 0.05),
                "creative": min(0.95, base_value - 0.05),
                "analytical": min(0.95, base_value + 0.02),
                "conversational": min(0.95, base_value + 0.04)
            }
        }
        
        return {
            "model_name": model_name if model_name else "all_models",
            "sample_count": int(lookback_days * 5),
            "performance_metrics": performance_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_feedback_trends(self, lookback_days: int) -> Dict[str, Any]:
        """
        Analyze trends in feedback over time.
        
        Args:
            lookback_days: Number of days to look back
            
        Returns:
            Dict containing feedback trend data
        """
        # This would be implemented to analyze trends from the feedback database
        # Here we're returning a placeholder with simulated trend data
        
        # Simulated positive ratio trend (improving over time)
        today = datetime.now().date()
        positive_ratio_trend = []
        
        # Start with a base value and improve gradually
        base_value = 0.70
        for i in range(lookback_days):
            date = today - timedelta(days=lookback_days - i - 1)
            # Gradually improve over time with some noise
            improvement_factor = i / (lookback_days * 2)  # Max 0.5 improvement
            noise = (hash(str(date)) % 20 - 10) / 100  # -0.1 to 0.1 noise
            value = min(0.95, base_value + improvement_factor + noise)
            
            positive_ratio_trend.append({
                "date": date.isoformat(),
                "value": value
            })
        
        return {
            "positive_ratio": {
                "data": positive_ratio_trend,
                "trend": "improving" if positive_ratio_trend[-1]["value"] > positive_ratio_trend[0]["value"] else "declining"
            },
            # Other trends would be added here
        }
    
    def _get_improvement_metrics(self, lookback_days: int) -> Dict[str, Any]:
        """
        Calculate metrics that show improvement over time.
        
        Args:
            lookback_days: Number of days to look back
            
        Returns:
            Dict containing improvement metrics
        """
        # This would be implemented to calculate real improvement metrics
        # Here we're returning placeholder metrics
        
        return {
            "response_quality": {
                "current": 0.82,
                "previous": 0.76,
                "change": 0.06,
                "change_percent": 7.9
            },
            "feedback_volume": {
                "current": 250,
                "previous": 200,
                "change": 50,
                "change_percent": 25.0
            },
            "average_response_time": {
                "current": 1.8,  # seconds
                "previous": 2.2,
                "change": -0.4,
                "change_percent": -18.2
            }
        }
    
    def _extract_positive_ratio(self, analysis: Dict[str, Any]) -> float:
        """
        Extract positive feedback ratio from analysis.
        
        Args:
            analysis: Feedback analysis data
            
        Returns:
            Positive feedback ratio
        """
        patterns = analysis.get("patterns", {})
        overall = patterns.get("overall", {})
        return overall.get("positive_ratio", 0.0)
    
    def _calculate_quality_score(self, analysis: Dict[str, Any], model_performance: Dict[str, Any]) -> float:
        """
        Calculate an overall quality score based on multiple factors.
        
        Args:
            analysis: Feedback analysis data
            model_performance: Model performance data
            
        Returns:
            Quality score between 0 and 100
        """
        # Extract metrics
        positive_ratio = self._extract_positive_ratio(analysis)
        
        # Get metrics from model performance
        overall_performance = model_performance.get("overall", {})
        performance_metrics = overall_performance.get("performance_metrics", {})
        category_scores = performance_metrics.get("category_scores", {})
        
        # Calculate weighted score
        # 60% from positive ratio, 40% from category scores
        score = 60 * positive_ratio
        
        # Add category scores if available
        if category_scores:
            avg_category_score = sum(category_scores.values()) / len(category_scores) if category_scores else 0
            score += 40 * avg_category_score
        
        return score
    
    def _extract_top_issues(self, analysis: Dict[str, Any], count: int = 5) -> List[Dict[str, Any]]:
        """
        Extract top issues from the analysis.
        
        Args:
            analysis: Feedback analysis data
            count: Number of top issues to extract
            
        Returns:
            List of top issues with counts
        """
        patterns = analysis.get("patterns", {})
        issues = []
        
        # Extract issues from each category
        for category, data in patterns.items():
            if category != "overall" and isinstance(data, dict):
                for issue, issue_count in data.items():
                    # Only include actual issues (not positive patterns)
                    if "good" not in issue and "just_right" not in issue and issue_count > 0:
                        issues.append({
                            "category": category,
                            "issue": issue,
                            "count": issue_count
                        })
        
        # Sort by count (descending) and take top 'count'
        issues.sort(key=lambda x: x["count"], reverse=True)
        return issues[:count]
        
    def _generate_simulated_global_analysis(self, lookback_days: int) -> Dict[str, Any]:
        """
        Generate simulated global feedback analysis data for demonstration purposes.
        
        Args:
            lookback_days: Number of days to look back
            
        Returns:
            Dict containing simulated global analysis data
        """
        # Simulated feedback count based on lookback days
        feedback_count = min(500, lookback_days * 15)
        
        # Simulated patterns
        patterns = {
            "overall": {
                "positive_count": int(feedback_count * 0.78),
                "negative_count": int(feedback_count * 0.22),
                "positive_ratio": 0.78
            },
            "length": {
                "too_long": int(feedback_count * 0.14),
                "too_short": int(feedback_count * 0.05),
                "just_right": int(feedback_count * 0.81)
            },
            "relevance": {
                "irrelevant": int(feedback_count * 0.11),
                "partially_relevant": int(feedback_count * 0.17),
                "highly_relevant": int(feedback_count * 0.72)
            },
            "detail": {
                "too_detailed": int(feedback_count * 0.09),
                "too_vague": int(feedback_count * 0.13),
                "good_detail_level": int(feedback_count * 0.78)
            },
            "tone": {
                "too_formal": int(feedback_count * 0.07),
                "too_casual": int(feedback_count * 0.05),
                "good_tone": int(feedback_count * 0.88)
            },
            "formatting": {
                "poor_formatting": int(feedback_count * 0.12),
                "hard_to_read": int(feedback_count * 0.08),
                "good_formatting": int(feedback_count * 0.80)
            }
        }
        
        # Simulated recommendations
        recommendations = {
            "high_priority": [
                "Reduce response length for complex topics",
                "Improve formatting for code examples"
            ],
            "medium_priority": [
                "Add more specific examples in responses",
                "Improve relevance for technical questions"
            ],
            "low_priority": [
                "Adjust tone for educational contexts",
                "Include more bullet points for readability"
            ]
        }
        
        return {
            "feedback_count": feedback_count,
            "patterns": patterns,
            "confidence_score": 0.85,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }


# Create a singleton instance
feedback_dashboard = FeedbackAnalyticsDashboard()


def test_dashboard():
    """Test the FeedbackAnalyticsDashboard functionality."""
    print("Testing Feedback Analytics Dashboard...")
    
    # Get sample dashboard data
    dashboard_data = feedback_dashboard.get_dashboard_data("last_30_days")
    
    print("\nDashboard Summary:")
    summary = dashboard_data.get("summary", {})
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Get quality trends
    trends = feedback_dashboard.get_quality_trends()
    
    print("\nTrend Summary:")
    trend_summary = trends.get("trend_summary", {})
    for key, value in trend_summary.items():
        print(f"{key}: {value}")
    
    print("\nTest completed.")


if __name__ == "__main__":
    test_dashboard()
