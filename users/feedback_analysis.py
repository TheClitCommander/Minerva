"""
Feedback Analysis Module

This module analyzes patterns in user feedback to dynamically improve response quality.
It identifies common issues, tracks feedback reliability, and provides insights for 
AI self-improvement loops.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import Counter, defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeedbackAnalysis:
    """
    Analyzes user feedback patterns to improve response quality over time.
    Implements confidence-based scoring and identifies common adjustment needs.
    """
    
    def __init__(self, feedback_dir: Optional[Path] = None):
        """
        Initialize the feedback analysis module.
        
        Args:
            feedback_dir: Directory where feedback data is stored
        """
        # Set feedback directory
        if feedback_dir is None:
            base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.feedback_dir = base_dir / "users" / "preferences" / "feedback"
        else:
            self.feedback_dir = feedback_dir
            
        # Ensure directory exists
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        
        # Feedback pattern cache
        self.pattern_cache = {}
        self.pattern_cache_timestamp = {}
        
        # Confidence scoring parameters
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.5,
            "low": 0.3
        }
        
        # Known feedback categories and common issues
        self.feedback_categories = {
            "length": ["too_long", "too_short", "just_right"],
            "detail": ["too_detailed", "not_detailed_enough", "good_detail_level"],
            "relevance": ["off_topic", "partially_relevant", "highly_relevant"],
            "tone": ["too_formal", "too_casual", "good_tone"],
            "structure": ["poor_organization", "good_organization", "needs_better_formatting"]
        }
        
        logger.info("Feedback Analysis module initialized")
    
    def analyze_user_feedback(self, user_id: str, lookback_days: int = 30) -> Dict[str, Any]:
        """
        Analyze feedback patterns for a specific user over a given time period.
        
        Args:
            user_id: Unique identifier for the user
            lookback_days: Number of days to look back for analysis
            
        Returns:
            Dict containing feedback patterns and confidence scores
        """
        # Check cache first (refresh if older than 1 hour)
        cache_key = f"{user_id}_{lookback_days}"
        if cache_key in self.pattern_cache:
            cache_time = self.pattern_cache_timestamp.get(cache_key)
            if cache_time and (datetime.now() - cache_time).total_seconds() < 3600:
                return self.pattern_cache[cache_key]
        
        # Load feedback data
        feedback_data = self._load_user_feedback(user_id)
        if not feedback_data:
            logger.warning(f"No feedback data found for user {user_id}")
            return {
                "patterns": {},
                "confidence_score": 0.0,
                "recommendations": {},
                "feedback_count": 0
            }
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        recent_feedback = [
            f for f in feedback_data
            if datetime.fromisoformat(f.get("timestamp", "2020-01-01")) > cutoff_date
        ]
        
        # Analyze patterns
        patterns = self._extract_feedback_patterns(recent_feedback)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(recent_feedback)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(patterns, confidence_score)
        
        # Prepare result
        result = {
            "patterns": patterns,
            "confidence_score": confidence_score,
            "recommendations": recommendations,
            "feedback_count": len(recent_feedback),
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Cache the result
        self.pattern_cache[cache_key] = result
        self.pattern_cache_timestamp[cache_key] = datetime.now()
        
        return result
    
    def _load_user_feedback(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Load feedback data for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List of feedback items
        """
        feedback_file = self.feedback_dir / f"{user_id}_feedback.json"
        
        if not feedback_file.exists():
            return []
        
        try:
            with open(feedback_file, 'r') as f:
                data = json.load(f)
                return data.get("feedback", [])
        except Exception as e:
            logger.error(f"Error loading feedback for user {user_id}: {str(e)}")
            return []
    
    def _extract_feedback_patterns(self, feedback_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract patterns from a list of feedback items.
        
        Args:
            feedback_list: List of feedback items to analyze
            
        Returns:
            Dict containing identified patterns
        """
        patterns = {}
        
        # Extract feedback types and whether they were positive
        feedback_types = [(f.get("feedback_type", "general"), f.get("is_positive", False)) for f in feedback_list]
        
        # Count by category
        by_category = defaultdict(lambda: defaultdict(int))
        for ftype, is_positive in feedback_types:
            if is_positive:
                by_category[ftype]["positive"] += 1
            else:
                by_category[ftype]["negative"] += 1
        
        # Analyze specific categories
        for category, issues in self.feedback_categories.items():
            category_counts = defaultdict(int)
            
            # Count occurrences of specific issues
            for feedback in feedback_list:
                if feedback.get("feedback_type") == category:
                    # Check comments or metadata for specific issues
                    comments = feedback.get("comments", "")
                    metadata = feedback.get("metadata", {})
                    
                    for issue in issues:
                        if issue in comments.lower() or metadata.get("issue") == issue:
                            category_counts[issue] += 1
            
            if category_counts:
                patterns[category] = dict(category_counts)
        
        # Overall sentiment
        overall = {
            "positive_ratio": sum(1 for _, is_pos in feedback_types if is_pos) / len(feedback_types) if feedback_types else 0,
            "by_category": {k: dict(v) for k, v in by_category.items()}
        }
        
        patterns["overall"] = overall
        
        return patterns
    
    def _calculate_confidence_score(self, feedback_list: List[Dict[str, Any]]) -> float:
        """
        Calculate a confidence score for the feedback analysis based on quantity,
        consistency, and recency of feedback.
        
        Args:
            feedback_list: List of feedback items to analyze
            
        Returns:
            Float between 0.0 and 1.0 representing confidence
        """
        if not feedback_list:
            return 0.0
        
        # Quantity factor: More feedback = higher confidence
        quantity_score = min(1.0, len(feedback_list) / 20)  # Max out at 20 items
        
        # Consistency factor: Consistent feedback = higher confidence
        feedback_types = [f.get("feedback_type", "general") for f in feedback_list]
        type_counts = Counter(feedback_types)
        most_common_count = type_counts.most_common(1)[0][1] if type_counts else 0
        consistency_score = most_common_count / len(feedback_list) if feedback_list else 0
        
        # Recency factor: Recent feedback = higher confidence
        current_time = datetime.now()
        timestamps = [datetime.fromisoformat(f.get("timestamp", "2020-01-01")) for f in feedback_list]
        time_diffs = [(current_time - ts).total_seconds() / (86400 * 30) for ts in timestamps]  # In months
        avg_age = sum(time_diffs) / len(time_diffs) if time_diffs else 0
        recency_score = max(0.0, 1.0 - min(1.0, avg_age))  # Newer = higher score
        
        # Weighted combination
        final_score = (0.4 * quantity_score) + (0.3 * consistency_score) + (0.3 * recency_score)
        
        return final_score
    
    def _generate_recommendations(self, patterns: Dict[str, Any], confidence_score: float) -> Dict[str, Any]:
        """
        Generate recommendations based on feedback patterns and confidence score.
        
        Args:
            patterns: Dict containing feedback patterns
            confidence_score: Confidence score for the analysis
            
        Returns:
            Dict containing recommendations for response improvement
        """
        if confidence_score < 0.3:
            return {
                "confidence_level": "low",
                "suggestions": ["Collect more feedback for reliable recommendations"]
            }
        
        recommendations = {
            "confidence_level": "high" if confidence_score >= 0.7 else "medium",
            "suggestions": []
        }
        
        # Extract overall patterns
        overall = patterns.get("overall", {})
        positive_ratio = overall.get("positive_ratio", 0.5)
        
        # If overall positive ratio is high, fewer changes needed
        if positive_ratio >= 0.8 and confidence_score >= 0.5:
            recommendations["suggestions"].append("Responses are generally well-received; minor optimizations may help")
        
        # Check length patterns
        length_patterns = patterns.get("length", {})
        if length_patterns.get("too_long", 0) > length_patterns.get("too_short", 0):
            recommendations["suggestions"].append("Reduce response length; responses may be too verbose")
        elif length_patterns.get("too_short", 0) > length_patterns.get("too_long", 0):
            recommendations["suggestions"].append("Increase response detail; responses may be too brief")
        
        # Check other patterns and add recommendations accordingly
        # ... (other pattern checks would go here)
        
        return recommendations


# Create a singleton instance
feedback_analyzer = FeedbackAnalysis()


# Basic test function
def test_feedback_analysis():
    """Test the FeedbackAnalysis functionality."""
    print("Testing Feedback Analysis module...")
    analyzer = FeedbackAnalysis()
    
    # Test user ID
    test_user = "test_user"
    
    # Create test directory if needed
    feedback_dir = analyzer.feedback_dir
    feedback_file = feedback_dir / f"{test_user}_feedback.json"
    
    print(f"Analysis complete. Test file location: {feedback_file}")


if __name__ == "__main__":
    test_feedback_analysis()
