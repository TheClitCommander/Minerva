"""
Self-Learning Optimization Engine

This module implements autonomous learning capabilities for Minerva,
enabling it to analyze performance trends and automatically refine its behavior
without manual intervention.
"""

import os
import sys
import json
import time
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix import paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import system components
from memory.real_time_memory_manager import real_time_memory_manager
from ai_decision.real_time_adaptation import adaptation_engine
from ai_decision.multi_ai_context_sync import context_sync
from web.multi_ai_coordinator import multi_ai_coordinator
from users.global_feedback_manager import global_feedback_manager

class TrendAnalyzer:
    """
    Analyzes response quality and user engagement trends over time to detect
    patterns and shifts in performance.
    """
    
    def __init__(self):
        """Initialize the trend analyzer."""
        # Time windows for analysis (in days)
        self.time_windows = [1, 7, 30]
        
        # Metrics to track
        self.tracked_metrics = [
            "response_quality",
            "user_satisfaction",
            "engagement_rate",
            "expansion_clicks",
            "helpful_feedback",
            "interaction_depth"
        ]
        
        # Storage for metric trends
        self.metric_history = defaultdict(lambda: defaultdict(list))
        
        # Anomaly detection thresholds
        self.anomaly_thresholds = {
            "z_score": 2.0,  # Standard deviations from mean
            "min_samples": 5,  # Minimum samples needed for trend analysis
            "significant_change": 0.15  # 15% change is considered significant
        }
        
        logger.info("Trend Analyzer initialized")
    
    def record_metric(self, user_id: str, metric_name: str, value: float, 
                     timestamp: Optional[datetime] = None):
        """
        Record a new data point for a metric.
        
        Args:
            user_id: User ID
            metric_name: Name of the metric
            value: Metric value
            timestamp: Optional timestamp (defaults to now)
        """
        if metric_name not in self.tracked_metrics:
            logger.warning(f"Unrecognized metric: {metric_name}")
            return
            
        timestamp = timestamp or datetime.now()
        
        # Store metric with timestamp
        self.metric_history[user_id][metric_name].append({
            "value": value,
            "timestamp": timestamp
        })
        
        # Keep history trimmed (keep at most 90 days)
        cutoff = datetime.now() - timedelta(days=90)
        self.metric_history[user_id][metric_name] = [
            m for m in self.metric_history[user_id][metric_name] 
            if m["timestamp"] > cutoff
        ]
    
    def analyze_metric_trend(self, user_id: str, metric_name: str, 
                            window_days: int = 7) -> Dict[str, Any]:
        """
        Analyze trend for a specific metric over a time window.
        
        Args:
            user_id: User ID
            metric_name: Name of the metric
            window_days: Analysis window in days
            
        Returns:
            Dictionary with trend analysis results
        """
        if metric_name not in self.tracked_metrics:
            logger.warning(f"Unrecognized metric: {metric_name}")
            return {"error": "Unrecognized metric"}
            
        # Get metric history for this user and metric
        history = self.metric_history[user_id][metric_name]
        
        # Filter to specified time window
        cutoff = datetime.now() - timedelta(days=window_days)
        window_history = [m for m in history if m["timestamp"] > cutoff]
        
        # Check if we have enough data
        if len(window_history) < self.anomaly_thresholds["min_samples"]:
            return {
                "metric": metric_name,
                "window_days": window_days,
                "status": "insufficient_data",
                "sample_count": len(window_history)
            }
        
        # Extract values
        values = [m["value"] for m in window_history]
        
        # Calculate statistics
        mean_value = np.mean(values)
        median_value = np.median(values)
        std_dev = np.std(values)
        min_value = min(values)
        max_value = max(values)
        
        # Calculate trend (simple linear regression)
        timestamps = [(m["timestamp"] - cutoff).total_seconds() / 86400 for m in window_history]
        
        if len(timestamps) >= 2:
            slope, intercept = np.polyfit(timestamps, values, 1)
            trend_direction = "increasing" if slope > 0 else "decreasing"
            trend_strength = abs(slope) / mean_value if mean_value != 0 else 0
        else:
            slope = 0
            trend_direction = "stable"
            trend_strength = 0
        
        # Check for anomalies
        anomalies = []
        for i, value in enumerate(values):
            if std_dev > 0:
                z_score = abs(value - mean_value) / std_dev
                if z_score > self.anomaly_thresholds["z_score"]:
                    anomalies.append({
                        "index": i,
                        "value": value,
                        "z_score": z_score,
                        "timestamp": window_history[i]["timestamp"].isoformat()
                    })
        
        # Determine if trend is significant
        significant = abs(slope * window_days / mean_value) > self.anomaly_thresholds["significant_change"] if mean_value != 0 else False
        
        return {
            "metric": metric_name,
            "window_days": window_days,
            "sample_count": len(window_history),
            "mean": mean_value,
            "median": median_value,
            "std_dev": std_dev,
            "min": min_value,
            "max": max_value,
            "trend_direction": trend_direction,
            "trend_strength": trend_strength,
            "significant_trend": significant,
            "slope": slope,
            "anomalies": anomalies,
            "status": "analyzed"
        }
    
    def detect_performance_shifts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Detect significant shifts in performance metrics across all tracked metrics.
        
        Args:
            user_id: User ID
            
        Returns:
            List of detected shifts with analysis details
        """
        detected_shifts = []
        
        # Check each metric across different time windows
        for metric in self.tracked_metrics:
            for window in self.time_windows:
                analysis = self.analyze_metric_trend(user_id, metric, window)
                
                # Only include significant trends
                if analysis.get("status") == "analyzed" and analysis.get("significant_trend", False):
                    detected_shifts.append(analysis)
        
        return detected_shifts
    
    def get_user_engagement_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive engagement profile for a user based on all metrics.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with engagement profile data
        """
        profile = {
            "user_id": user_id,
            "metrics": {},
            "trends": {},
            "overall_engagement": "unknown"
        }
        
        # Not enough data for any metrics
        if user_id not in self.metric_history:
            return profile
        
        # Process each metric
        total_metrics = 0
        metrics_with_data = 0
        
        for metric in self.tracked_metrics:
            if metric in self.metric_history[user_id]:
                # Get recent values
                recent = self.metric_history[user_id][metric][-10:]
                
                if recent:
                    total_metrics += 1
                    metrics_with_data += 1
                    
                    # Calculate average for recent values
                    avg_value = sum(m["value"] for m in recent) / len(recent)
                    
                    # Get 7-day trend
                    trend = self.analyze_metric_trend(user_id, metric, 7)
                    
                    profile["metrics"][metric] = avg_value
                    profile["trends"][metric] = {
                        "direction": trend.get("trend_direction", "stable"),
                        "strength": trend.get("trend_strength", 0),
                        "significant": trend.get("significant_trend", False)
                    }
        
        # Calculate overall engagement level if we have enough data
        if metrics_with_data >= 3:
            engagement_indicators = []
            
            if "engagement_rate" in profile["metrics"]:
                engagement_indicators.append(profile["metrics"]["engagement_rate"] > 0.5)
                
            if "helpful_feedback" in profile["metrics"]:
                engagement_indicators.append(profile["metrics"]["helpful_feedback"] > 0.7)
                
            if "interaction_depth" in profile["metrics"]:
                engagement_indicators.append(profile["metrics"]["interaction_depth"] > 3)
            
            # Determine overall engagement based on indicators
            if engagement_indicators:
                positive_indicators = sum(1 for i in engagement_indicators if i)
                engagement_ratio = positive_indicators / len(engagement_indicators)
                
                if engagement_ratio > 0.8:
                    profile["overall_engagement"] = "high"
                elif engagement_ratio > 0.5:
                    profile["overall_engagement"] = "medium"
                else:
                    profile["overall_engagement"] = "low"
        
        return profile

# Create singleton instance
trend_analyzer = TrendAnalyzer()


class SelfAdjustmentSystem:
    """
    Implements autonomous adjustment logic to refine Minerva's performance
    based on detected performance trends without manual intervention.
    """
    
    def __init__(self):
        """Initialize the self-adjustment system."""
        # Reference to trend analyzer
        self.trend_analyzer = trend_analyzer
        
        # Reference to system components
        self.memory_manager = real_time_memory_manager
        self.adaptation_engine = adaptation_engine
        self.context_sync = context_sync
        
        # Adjustment parameters
        self.adjustment_thresholds = {
            "min_confidence": 0.6,  # Minimum confidence to make automatic adjustment
            "max_adjustment": 0.3,  # Maximum single adjustment size
            "learning_rate": 0.1,  # Base learning rate for adjustments
            "cool_down_hours": 24  # Hours between automatic adjustments
        }
        
        # Mappings between metrics and adaptation parameters
        self.metric_to_parameter_map = {
            "response_quality": ["detail_level", "tone"],
            "user_satisfaction": ["detail_level", "tone", "structure"],
            "engagement_rate": ["length", "detail_level"],
            "expansion_clicks": ["length"],
            "helpful_feedback": ["detail_level", "structure"],
            "interaction_depth": ["length", "detail_level"]
        }
        
        # Parameter adjustment directions
        self.parameter_adjustments = {
            "length": {
                "increasing": {"expansion_clicks": 1, "engagement_rate": 1},
                "decreasing": {"expansion_clicks": -1, "engagement_rate": -1}
            },
            "detail_level": {
                "increasing": {"response_quality": 1, "helpful_feedback": 1},
                "decreasing": {"response_quality": -1, "helpful_feedback": -1}
            },
            "tone": {
                "neutral": {"user_satisfaction": 0},
                "formal": {"user_satisfaction": 1},
                "casual": {"user_satisfaction": -1}
            },
            "structure": {
                "paragraph": {"helpful_feedback": 0},
                "bullets": {"helpful_feedback": 1},
                "numbered": {"helpful_feedback": 0.5}
            }
        }
        
        # Track recent adjustments
        self.recent_adjustments = defaultdict(dict)
        
        logger.info("Self-Adjustment System initialized")
    
    def can_adjust_for_user(self, user_id: str) -> bool:
        """
        Check if we can make adjustments for a user based on cool-down period.
        
        Args:
            user_id: User ID
            
        Returns:
            True if adjustments are allowed, False otherwise
        """
        if user_id not in self.recent_adjustments:
            return True
            
        now = datetime.now()
        for param, adjustment in self.recent_adjustments[user_id].items():
            hours_since = (now - adjustment["timestamp"]).total_seconds() / 3600
            if hours_since < self.adjustment_thresholds["cool_down_hours"]:
                return False
                
        return True
    
    def calculate_adjustment_confidence(self, trend_data: Dict[str, Any]) -> float:
        """
        Calculate confidence level for making an adjustment based on trend data.
        
        Args:
            trend_data: Trend analysis data for a metric
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Start with base confidence
        confidence = 0.5
        
        # Adjust based on trend strength
        confidence += min(0.3, trend_data.get("trend_strength", 0))
        
        # Adjust based on sample count (more samples = higher confidence)
        samples = trend_data.get("sample_count", 0)
        if samples > 20:
            confidence += 0.2
        elif samples > 10:
            confidence += 0.1
        
        # Reduce confidence if there are anomalies
        anomaly_count = len(trend_data.get("anomalies", []))
        if anomaly_count > 0:
            confidence -= min(0.3, 0.05 * anomaly_count)
        
        # Ensure confidence is within valid range
        return max(0.0, min(1.0, confidence))
    
    def determine_parameter_adjustment(self, metric: str, trend_direction: str, 
                                     current_value: Optional[Any] = None) -> Dict[str, Any]:
        """
        Determine how to adjust parameters based on metric trends.
        
        Args:
            metric: Metric name
            trend_direction: Direction of trend (increasing, decreasing, stable)
            current_value: Current value of the parameter (if applicable)
            
        Returns:
            Dictionary with parameter adjustment details
        """
        adjustment = {
            "parameters": [],
            "directions": {}
        }
        
        # Get parameters affected by this metric
        if metric not in self.metric_to_parameter_map:
            return adjustment
            
        affected_parameters = self.metric_to_parameter_map[metric]
        
        for param in affected_parameters:
            # Skip if we don't have mapping for this parameter
            if param not in self.parameter_adjustments:
                continue
                
            param_map = self.parameter_adjustments[param]
            
            # Handle different parameter types differently
            if isinstance(next(iter(param_map.values())), dict):
                # Complex parameter with direction mapping
                if trend_direction in param_map:
                    direction_map = param_map[trend_direction]
                    if metric in direction_map:
                        adjustment["parameters"].append(param)
                        adjustment["directions"][param] = direction_map[metric]
            elif isinstance(current_value, (str, bool)):
                # Categorical parameter - need to choose a new value
                best_option = None
                best_score = float('-inf')
                
                for option, option_scores in param_map.items():
                    if metric in option_scores:
                        score = option_scores[metric]
                        if trend_direction == "increasing" and score > best_score:
                            best_score = score
                            best_option = option
                        elif trend_direction == "decreasing" and score < best_score:
                            best_score = score
                            best_option = option
                
                if best_option is not None:
                    adjustment["parameters"].append(param)
                    adjustment["directions"][param] = best_option
        
        return adjustment
    
    def apply_automatic_adjustments(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze trends and automatically apply adjustments if confidence is high enough.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with adjustment results
        """
        result = {
            "user_id": user_id,
            "adjustments_made": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if we can adjust for this user
        if not self.can_adjust_for_user(user_id):
            result["status"] = "cool_down"
            return result
        
        # Get performance shifts
        shifts = self.trend_analyzer.detect_performance_shifts(user_id)
        
        if not shifts:
            result["status"] = "no_shifts_detected"
            return result
            
        # Track made adjustments
        adjustments_made = []
        
        # Process each shift
        for shift in shifts:
            metric = shift.get("metric")
            trend_direction = shift.get("trend_direction")
            
            # Calculate confidence for this adjustment
            confidence = self.calculate_adjustment_confidence(shift)
            
            # Only proceed if confidence is high enough
            if confidence < self.adjustment_thresholds["min_confidence"]:
                continue
            
            # Get current adaptations
            current_adaptations = self.adaptation_engine.get_adaptations(user_id)
            
            # Determine parameter adjustments
            adjustment = self.determine_parameter_adjustment(
                metric=metric,
                trend_direction=trend_direction,
                current_value=current_adaptations.get(metric)
            )
            
            # Apply each parameter adjustment
            for param in adjustment["parameters"]:
                direction = adjustment["directions"][param]
                
                # Apply numerical adjustment
                if isinstance(direction, (int, float)):
                    # Get current value or default
                    current = current_adaptations.get(param, 0.5)
                    
                    # Calculate adjustment size
                    adjustment_size = self.adjustment_thresholds["learning_rate"] * abs(direction)
                    adjustment_size = min(adjustment_size, self.adjustment_thresholds["max_adjustment"])
                    
                    # Apply adjustment in the right direction
                    if direction > 0:
                        new_value = min(1.0, current + adjustment_size)
                    else:
                        new_value = max(0.0, current - adjustment_size)
                    
                    # Update adaptation
                    self.adaptation_engine.set_adaptation_value(user_id, param, new_value)
                    
                    # Record adjustment
                    self.recent_adjustments[user_id][param] = {
                        "from": current,
                        "to": new_value,
                        "timestamp": datetime.now(),
                        "metric": metric,
                        "confidence": confidence
                    }
                    
                    adjustments_made.append({
                        "parameter": param,
                        "from": current,
                        "to": new_value,
                        "based_on": metric,
                        "confidence": confidence
                    })
                    
                    logger.info(f"Adjusted {param} for user {user_id} from {current} to {new_value} "
                               f"based on {metric} trend ({confidence:.2f} confidence)")
                    
                # Apply categorical adjustment
                elif isinstance(direction, str):
                    # Update adaptation with new category
                    self.adaptation_engine.set_adaptation_value(user_id, param, direction)
                    
                    # Record adjustment
                    self.recent_adjustments[user_id][param] = {
                        "from": current_adaptations.get(param, "unknown"),
                        "to": direction,
                        "timestamp": datetime.now(),
                        "metric": metric,
                        "confidence": confidence
                    }
                    
                    adjustments_made.append({
                        "parameter": param,
                        "from": current_adaptations.get(param, "unknown"),
                        "to": direction,
                        "based_on": metric,
                        "confidence": confidence
                    })
                    
                    logger.info(f"Set {param} for user {user_id} to {direction} "
                               f"based on {metric} trend ({confidence:.2f} confidence)")
        
        # Update result
        result["adjustments_made"] = adjustments_made
        result["status"] = "success" if adjustments_made else "no_adjustments_needed"
        
        # Record significant adjustments to memory
        if adjustments_made:
            self._record_adjustments_to_memory(user_id, adjustments_made)
        
        return result
    
    def _record_adjustments_to_memory(self, user_id: str, adjustments: List[Dict[str, Any]]):
        """
        Record significant adjustments to the memory system.
        
        Args:
            user_id: User ID
            adjustments: List of adjustments made
        """
        if not adjustments:
            return
            
        # Prepare content for memory
        content = f"Automatic adaptation adjustments made for user based on performance trends: "
        content += ", ".join([f"{a['parameter']} adjusted to {a['to']} based on {a['based_on']} trends" 
                            for a in adjustments])
        
        # Add to memory system
        self.memory_manager.add_memory_with_context(
            content=content,
            source="self_adjustment",
            category="adaptation",
            context=f"user:{user_id}",
            importance=5,  # Medium-high importance
            tags=["adaptation", "self_learning", "automatic_adjustment"]
        )
    
    def suggest_manual_adjustments(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Suggest manual adjustments that haven't met confidence threshold for automatic application.
        
        Args:
            user_id: User ID
            
        Returns:
            List of suggested adjustments with confidence levels
        """
        suggested_adjustments = []
        
        # Get all shifts regardless of confidence
        all_shifts = self.trend_analyzer.detect_performance_shifts(user_id)
        
        # Get current adaptations
        current_adaptations = self.adaptation_engine.get_adaptations(user_id)
        
        # Process each shift
        for shift in all_shifts:
            metric = shift.get("metric")
            trend_direction = shift.get("trend_direction")
            
            # Calculate confidence
            confidence = self.calculate_adjustment_confidence(shift)
            
            # Only include if it's not high enough for automatic but still noteworthy
            if confidence >= 0.3 and confidence < self.adjustment_thresholds["min_confidence"]:
                # Determine parameter adjustments
                adjustment = self.determine_parameter_adjustment(
                    metric=metric,
                    trend_direction=trend_direction,
                    current_value=current_adaptations.get(metric)
                )
                
                # Add each parameter adjustment as a suggestion
                for param in adjustment["parameters"]:
                    direction = adjustment["directions"][param]
                    
                    suggested_adjustments.append({
                        "parameter": param,
                        "current_value": current_adaptations.get(param, "unknown"),
                        "suggested_value": direction if isinstance(direction, str) else "increase" if direction > 0 else "decrease",
                        "based_on": metric,
                        "trend": trend_direction,
                        "confidence": confidence,
                        "window_days": shift.get("window_days", 7)
                    })
        
        return suggested_adjustments

# Create singleton instance
self_adjustment_system = SelfAdjustmentSystem()


class SelfLearningEngine:
    """
    Main integration class that combines trend analysis and self-adjustment
    to create a complete self-learning optimization engine for Minerva.
    """
    
    def __init__(self):
        """Initialize the self-learning engine."""
        self.trend_analyzer = trend_analyzer
        self.adjustment_system = self_adjustment_system
        self.global_feedback = global_feedback_manager
        
        # Configuration for automatic processing
        self.auto_processing_config = {
            "enabled": True,
            "process_interval_hours": 12,
            "min_data_points": 5,
            "last_processed": {},  # By user_id
            "processing_enabled_by_user": {}  # By user_id
        }
        
        logger.info("Self-Learning Engine initialized")
    
    def enable_auto_processing(self, user_id: str, enabled: bool = True) -> bool:
        """
        Enable or disable automatic processing for a specific user.
        
        Args:
            user_id: User ID
            enabled: Whether to enable or disable auto processing
            
        Returns:
            Current status after update
        """
        self.auto_processing_config["processing_enabled_by_user"][user_id] = enabled
        return enabled
    
    def is_auto_processing_enabled(self, user_id: str) -> bool:
        """
        Check if automatic processing is enabled for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if enabled, False otherwise
        """
        # Check global setting first
        if not self.auto_processing_config["enabled"]:
            return False
            
        # Check user-specific override
        return self.auto_processing_config["processing_enabled_by_user"].get(user_id, True)
    
    def should_process_user(self, user_id: str) -> bool:
        """
        Determine if we should process a user's data based on last processing time.
        
        Args:
            user_id: User ID
            
        Returns:
            True if we should process, False otherwise
        """
        # Check if auto processing is enabled
        if not self.is_auto_processing_enabled(user_id):
            return False
            
        # Get last processed time
        last_processed = self.auto_processing_config["last_processed"].get(user_id)
        
        # If never processed, we should process
        if last_processed is None:
            return True
            
        # Check if enough time has passed
        hours_since = (datetime.now() - last_processed).total_seconds() / 3600
        return hours_since >= self.auto_processing_config["process_interval_hours"]
    
    def record_feedback(self, user_id: str, response_id: str, feedback_type: str, 
                       feedback_value: Any, source: str = "user") -> Dict[str, Any]:
        """
        Record user feedback and trigger metric updates.
        
        Args:
            user_id: User ID
            response_id: Response identifier
            feedback_type: Type of feedback (helpful, relevant, etc)
            feedback_value: Value of the feedback
            source: Source of the feedback
            
        Returns:
            Result of the operation
        """
        # Record feedback in the global feedback system
        feedback_result = self.global_feedback.record_feedback(
            user_id=user_id,
            response_id=response_id,
            feedback_type=feedback_type,
            feedback_value=feedback_value,
            source=source
        )
        
        # Map feedback to performance metrics
        self._map_feedback_to_metrics(user_id, feedback_type, feedback_value)
        
        # Check if we should run automatic processing
        if self.should_process_user(user_id):
            self.process_user_data(user_id)
        
        return feedback_result
    
    def _map_feedback_to_metrics(self, user_id: str, feedback_type: str, feedback_value: Any) -> None:
        """
        Map feedback to performance metrics for trend analysis.
        
        Args:
            user_id: User ID
            feedback_type: Type of feedback
            feedback_value: Value of the feedback
        """
        # Map based on feedback type
        if feedback_type == "helpful":
            # Convert boolean or numeric helpful feedback to our metrics
            if isinstance(feedback_value, bool):
                value = 1.0 if feedback_value else 0.0
            elif isinstance(feedback_value, (int, float)):
                value = max(0.0, min(1.0, float(feedback_value)))
            else:
                return
                
            # Record as response quality and helpful feedback metrics
            self.trend_analyzer.record_metric(user_id, "response_quality", value)
            self.trend_analyzer.record_metric(user_id, "helpful_feedback", value)
            
        elif feedback_type == "satisfaction":
            # Satisfaction score (assume 0-10 or 0-1 scale)
            if isinstance(feedback_value, (int, float)):
                # Normalize to 0-1 range
                if feedback_value > 1.0:
                    value = feedback_value / 10.0
                else:
                    value = feedback_value
                    
                value = max(0.0, min(1.0, value))
                self.trend_analyzer.record_metric(user_id, "user_satisfaction", value)
                
        elif feedback_type == "expanded":
            # User expanded a truncated response
            if isinstance(feedback_value, bool) and feedback_value:
                self.trend_analyzer.record_metric(user_id, "expansion_clicks", 1.0)
            
        elif feedback_type == "engagement":
            # Engagement measurement (e.g., time spent reading)
            if isinstance(feedback_value, (int, float)):
                # Normalize engagement value
                value = min(1.0, feedback_value / 60.0)  # Assume 60 seconds is max normal engagement
                self.trend_analyzer.record_metric(user_id, "engagement_rate", value)
    
    def process_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Process all user data to apply adjustments and update knowledge.
        
        Args:
            user_id: User ID
            
        Returns:
            Results of the processing
        """
        result = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "adjustments": None,
            "suggestions": None,
            "trends": None
        }
        
        # Get all metrics for this user
        metrics = self.trend_analyzer.get_all_user_metrics(user_id)
        
        # Check if we have enough data
        if len(metrics) < self.auto_processing_config["min_data_points"]:
            result["status"] = "insufficient_data"
            return result
        
        # Apply automatic adjustments
        adjustments = self.adjustment_system.apply_automatic_adjustments(user_id)
        result["adjustments"] = adjustments
        
        # Get manual adjustment suggestions
        suggestions = self.adjustment_system.suggest_manual_adjustments(user_id)
        result["suggestions"] = suggestions
        
        # Get engagement profile for user
        trends = self.trend_analyzer.generate_engagement_profile(user_id)
        result["trends"] = trends
        
        # Update last processed time
        self.auto_processing_config["last_processed"][user_id] = datetime.now()
        
        result["status"] = "success"
        return result
    
    def get_learning_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get learning insights for a specific user including trend data and adjustment history.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with learning insights
        """
        insights = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "trends": {},
            "adjustments": [],
            "suggestions": []
        }
        
        # Get metrics data
        for window_days in [1, 7, 30]:
            metrics = self.trend_analyzer.get_metrics_for_time_window(user_id, window_days)
            insights["metrics"][f"{window_days}_day"] = metrics
        
        # Get trend data
        for window_days in [1, 7, 30]:
            trends = self.trend_analyzer.analyze_trends(user_id, window_days)
            insights["trends"][f"{window_days}_day"] = trends
        
        # Get adjustment history - convert defaultdict to regular dict for serialization
        adjustments_dict = dict(self.adjustment_system.recent_adjustments.get(user_id, {}))
        for param, adjustment in adjustments_dict.items():
            # Convert datetime to string for json serialization
            if "timestamp" in adjustment and isinstance(adjustment["timestamp"], datetime):
                adjustment["timestamp"] = adjustment["timestamp"].isoformat()
            insights["adjustments"].append({
                "parameter": param,
                **adjustment
            })
        
        # Get suggestions
        insights["suggestions"] = self.adjustment_system.suggest_manual_adjustments(user_id)
        
        return insights
    
    def apply_manual_adjustment(self, user_id: str, parameter: str, value: Any) -> Dict[str, Any]:
        """
        Apply a manual adjustment to a user's parameters.
        
        Args:
            user_id: User ID
            parameter: Parameter to adjust
            value: New value
            
        Returns:
            Result of the operation
        """
        result = {
            "user_id": user_id,
            "parameter": parameter,
            "applied_value": value,
            "timestamp": datetime.now().isoformat(),
            "status": "unknown"
        }
        
        try:
            # Get current value for comparison
            current_value = self.adaptation_engine.get_adaptation_value(user_id, parameter)
            result["previous_value"] = current_value
            
            # Apply the adjustment
            self.adaptation_engine.set_adaptation_value(user_id, parameter, value)
            
            # Record the adjustment in our history
            self.adjustment_system.recent_adjustments[user_id][parameter] = {
                "from": current_value,
                "to": value,
                "timestamp": datetime.now(),
                "metric": "manual_adjustment",
                "confidence": 1.0  # Manual adjustments have maximum confidence
            }
            
            # Record in memory system
            self.adjustment_system._record_adjustments_to_memory(
                user_id, [
                    {
                        "parameter": parameter,
                        "from": current_value,
                        "to": value,
                        "based_on": "manual_adjustment"
                    }
                ]
            )
            
            result["status"] = "success"
            
        except Exception as e:
            logger.exception(f"Error applying manual adjustment: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            
        return result
    
    def reset_user_adaptations(self, user_id: str) -> Dict[str, Any]:
        """
        Reset all adaptations for a user to default values.
        
        Args:
            user_id: User ID
            
        Returns:
            Result of the operation
        """
        result = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "status": "unknown"
        }
        
        try:
            # Reset adaptations in the adaptation engine
            self.adaptation_engine.reset_adaptations(user_id)
            
            # Clear adjustment history for this user
            if user_id in self.adjustment_system.recent_adjustments:
                self.adjustment_system.recent_adjustments.pop(user_id)
            
            # Record reset in memory
            self.adjustment_system.memory_manager.add_memory_with_context(
                content=f"Reset all adaptations to default values",
                source="manual_reset",
                category="adaptation",
                context=f"user:{user_id}",
                importance=7,  # High importance
                tags=["adaptation", "reset", "manual_action"]
            )
            
            result["status"] = "success"
            
        except Exception as e:
            logger.exception(f"Error resetting user adaptations: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            
        return result

# Create singleton instance
self_learning_engine = SelfLearningEngine()