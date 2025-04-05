#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test module for the Self-Learning Optimization Engine.
"""

import unittest
import sys
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Fix import paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the self-learning optimizer
from ai_decision.self_learning_optimizer import (
    TrendAnalyzer, 
    SelfAdjustmentSystem,
    SelfLearningEngine
)

class TestTrendAnalyzer(unittest.TestCase):
    """
    Test cases for the TrendAnalyzer class.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a fresh TrendAnalyzer instance for each test
        self.trend_analyzer = TrendAnalyzer()
        
        # Add some test metrics
        self.user_id = "test_user"
        metrics = [
            ("response_quality", 0.8, datetime.now() - timedelta(days=2)),
            ("response_quality", 0.7, datetime.now() - timedelta(days=1)),
            ("response_quality", 0.9, datetime.now()),
            ("helpful_feedback", 0.9, datetime.now() - timedelta(days=2)),
            ("helpful_feedback", 0.7, datetime.now() - timedelta(days=1)),
            ("helpful_feedback", 0.8, datetime.now()),
            ("engagement_rate", 0.5, datetime.now() - timedelta(days=2)),
            ("engagement_rate", 0.6, datetime.now() - timedelta(days=1)),
            ("engagement_rate", 0.7, datetime.now()),
        ]
        
        for metric, value, timestamp in metrics:
            self.trend_analyzer.record_metric_with_timestamp(
                self.user_id, metric, value, timestamp)
    
    def test_record_metric(self):
        """Test recording a metric."""
        self.trend_analyzer.record_metric(self.user_id, "test_metric", 0.5)
        metrics = self.trend_analyzer.get_metrics_for_time_window(self.user_id, 1)
        self.assertIn("test_metric", metrics)
        self.assertGreaterEqual(len(metrics["test_metric"]), 1)
    
    def test_get_metrics_for_time_window(self):
        """Test retrieving metrics for different time windows."""
        # Test 1-day window
        metrics_1d = self.trend_analyzer.get_metrics_for_time_window(self.user_id, 1)
        self.assertIn("response_quality", metrics_1d)
        self.assertEqual(len(metrics_1d["response_quality"]), 2)  # Today and yesterday
        
        # Test 7-day window
        metrics_7d = self.trend_analyzer.get_metrics_for_time_window(self.user_id, 7)
        self.assertIn("response_quality", metrics_7d)
        self.assertEqual(len(metrics_7d["response_quality"]), 3)  # All three entries
    
    def test_analyze_trends(self):
        """Test trend analysis for metrics."""
        trends = self.trend_analyzer.analyze_trends(self.user_id, 7)
        self.assertIn("response_quality", trends)
        self.assertIn("trend_direction", trends["response_quality"])
        self.assertIn("trend_strength", trends["response_quality"])
        
        # Response quality should have an increasing trend
        self.assertEqual(trends["response_quality"]["trend_direction"], "increasing")
    
    def test_detect_performance_shifts(self):
        """Test detecting significant performance shifts."""
        # Add more metrics with a clearer trend
        for i in range(10):
            value = 0.5 + (i * 0.05)  # Increasing trend
            timestamp = datetime.now() - timedelta(days=10-i)
            self.trend_analyzer.record_metric_with_timestamp(
                self.user_id, "test_shift_metric", value, timestamp)
        
        shifts = self.trend_analyzer.detect_performance_shifts(self.user_id)
        
        # We should detect at least one shift
        self.assertGreaterEqual(len(shifts), 1)
        
        # Check if our test metric is in the detected shifts
        shift_metrics = [shift["metric"] for shift in shifts]
        self.assertIn("test_shift_metric", shift_metrics)
    
    def test_generate_engagement_profile(self):
        """Test generating an engagement profile."""
        profile = self.trend_analyzer.generate_engagement_profile(self.user_id)
        
        # Check for required profile sections
        self.assertIn("metrics", profile)
        self.assertIn("trends", profile)
        self.assertIn("anomalies", profile)
        
        # Check for our test metrics
        self.assertIn("response_quality", profile["metrics"])
        self.assertIn("helpful_feedback", profile["metrics"])
        self.assertIn("engagement_rate", profile["metrics"])


class TestSelfAdjustmentSystem(unittest.TestCase):
    """
    Test cases for the SelfAdjustmentSystem class.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks for dependencies
        self.mock_trend_analyzer = MagicMock()
        self.mock_memory_manager = MagicMock()
        self.mock_adaptation_engine = MagicMock()
        self.mock_context_sync = MagicMock()
        
        # Create patches for the dependencies
        self.patches = [
            patch("ai_decision.self_learning_optimizer.trend_analyzer", self.mock_trend_analyzer),
            patch("ai_decision.self_learning_optimizer.real_time_memory_manager", self.mock_memory_manager),
            patch("ai_decision.self_learning_optimizer.adaptation_engine", self.mock_adaptation_engine),
            patch("ai_decision.self_learning_optimizer.context_sync", self.mock_context_sync)
        ]
        
        # Start all patches
        for p in self.patches:
            p.start()
        
        # Create the SelfAdjustmentSystem instance
        self.adjustment_system = SelfAdjustmentSystem()
        self.user_id = "test_user"
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop all patches
        for p in self.patches:
            p.stop()
    
    def test_can_adjust_for_user(self):
        """Test checking if adjustments are allowed for a user."""
        # New user should be adjustable
        self.assertTrue(self.adjustment_system.can_adjust_for_user(self.user_id))
        
        # Add a recent adjustment and test again
        self.adjustment_system.recent_adjustments[self.user_id]["test_param"] = {
            "timestamp": datetime.now()
        }
        self.assertFalse(self.adjustment_system.can_adjust_for_user(self.user_id))
        
        # Add an old adjustment and test again
        self.adjustment_system.recent_adjustments[self.user_id]["test_param"] = {
            "timestamp": datetime.now() - timedelta(hours=25)
        }
        self.assertTrue(self.adjustment_system.can_adjust_for_user(self.user_id))
    
    def test_calculate_adjustment_confidence(self):
        """Test calculating confidence for an adjustment."""
        # Low confidence scenario
        low_confidence_data = {
            "trend_strength": 0.1,
            "sample_count": 3,
            "anomalies": [1, 2, 3]
        }
        low_confidence = self.adjustment_system.calculate_adjustment_confidence(low_confidence_data)
        self.assertLess(low_confidence, 0.5)
        
        # High confidence scenario
        high_confidence_data = {
            "trend_strength": 0.3,
            "sample_count": 25,
            "anomalies": []
        }
        high_confidence = self.adjustment_system.calculate_adjustment_confidence(high_confidence_data)
        self.assertGreater(high_confidence, 0.7)
    
    def test_determine_parameter_adjustment(self):
        """Test determining parameter adjustments based on metrics."""
        # Test an increasing helpful_feedback trend
        adjustment = self.adjustment_system.determine_parameter_adjustment(
            "helpful_feedback", "increasing")
        
        self.assertIn("parameters", adjustment)
        self.assertIn("directions", adjustment)
        
        # Should affect detail_level and structure
        self.assertIn("detail_level", adjustment["parameters"])
        self.assertIn("structure", adjustment["parameters"])
    
    def test_apply_automatic_adjustments(self):
        """Test applying automatic adjustments."""
        # Configure mocks
        self.mock_trend_analyzer.detect_performance_shifts.return_value = [
            {
                "metric": "helpful_feedback",
                "trend_direction": "increasing",
                "trend_strength": 0.8,
                "sample_count": 30,
                "anomalies": []
            }
        ]
        
        self.mock_adaptation_engine.get_adaptations.return_value = {
            "detail_level": 0.5,
            "structure": "paragraph"
        }
        
        # Apply adjustments
        result = self.adjustment_system.apply_automatic_adjustments(self.user_id)
        
        # Check results
        self.assertEqual(result["status"], "success")
        self.assertGreater(len(result["adjustments_made"]), 0)
        
        # Verify memory recording
        self.mock_memory_manager.add_memory_with_context.assert_called_once()


class TestSelfLearningEngine(unittest.TestCase):
    """
    Test cases for the SelfLearningEngine class.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks for dependencies
        self.mock_trend_analyzer = MagicMock()
        self.mock_adjustment_system = MagicMock()
        self.mock_global_feedback = MagicMock()
        self.mock_adaptation_engine = MagicMock()
        
        # Create patches for the dependencies
        self.patches = [
            patch("ai_decision.self_learning_optimizer.trend_analyzer", self.mock_trend_analyzer),
            patch("ai_decision.self_learning_optimizer.self_adjustment_system", self.mock_adjustment_system),
            patch("ai_decision.self_learning_optimizer.global_feedback_manager", self.mock_global_feedback),
            patch("ai_decision.self_learning_optimizer.adaptation_engine", self.mock_adaptation_engine)
        ]
        
        # Start all patches
        for p in self.patches:
            p.start()
        
        # Create the SelfLearningEngine instance
        self.learning_engine = SelfLearningEngine()
        self.user_id = "test_user"
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop all patches
        for p in self.patches:
            p.stop()
    
    def test_record_feedback(self):
        """Test recording feedback and updating metrics."""
        # Configure mocks
        self.mock_global_feedback.record_feedback.return_value = {"status": "success"}
        
        # Record helpful feedback
        result = self.learning_engine.record_feedback(
            user_id=self.user_id,
            response_id="resp123",
            feedback_type="helpful",
            feedback_value=True
        )
        
        # Verify global feedback was called
        self.mock_global_feedback.record_feedback.assert_called_once()
        
        # Verify metrics were recorded
        self.mock_trend_analyzer.record_metric.assert_called()
    
    def test_map_feedback_to_metrics(self):
        """Test mapping feedback to performance metrics."""
        # Test helpful feedback
        self.learning_engine._map_feedback_to_metrics(self.user_id, "helpful", True)
        # Should record both response quality and helpful feedback
        self.assertEqual(self.mock_trend_analyzer.record_metric.call_count, 2)
        
        # Reset mock
        self.mock_trend_analyzer.record_metric.reset_mock()
        
        # Test satisfaction feedback
        self.learning_engine._map_feedback_to_metrics(self.user_id, "satisfaction", 8.5)
        # Should record user satisfaction
        self.mock_trend_analyzer.record_metric.assert_called_once()
    
    def test_process_user_data(self):
        """Test processing all user data."""
        # Configure mocks
        self.mock_trend_analyzer.get_all_user_metrics.return_value = {
            "helpful_feedback": [
                {"value": 0.8, "timestamp": datetime.now()},
                {"value": 0.7, "timestamp": datetime.now() - timedelta(days=1)}
            ]
        }
        
        self.mock_adjustment_system.apply_automatic_adjustments.return_value = {
            "status": "success",
            "adjustments_made": [{"parameter": "detail_level", "from": 0.5, "to": 0.6}]
        }
        
        self.mock_adjustment_system.suggest_manual_adjustments.return_value = [
            {"parameter": "tone", "current_value": "neutral", "suggested_value": "formal"}
        ]
        
        self.mock_trend_analyzer.generate_engagement_profile.return_value = {
            "metrics": {"helpful_feedback": 0.75},
            "trends": {"helpful_feedback": {"trend_direction": "stable"}}
        }
        
        # Process user data
        result = self.learning_engine.process_user_data(self.user_id)
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["adjustments"]["status"], "success")
    
    def test_get_learning_insights(self):
        """Test getting learning insights."""
        # Configure mocks
        self.mock_trend_analyzer.get_metrics_for_time_window.return_value = {
            "helpful_feedback": [{"value": 0.8, "timestamp": datetime.now()}]
        }
        
        self.mock_trend_analyzer.analyze_trends.return_value = {
            "helpful_feedback": {"trend_direction": "stable", "trend_strength": 0.1}
        }
        
        self.mock_adjustment_system.suggest_manual_adjustments.return_value = []
        self.mock_adjustment_system.recent_adjustments = {}
        
        # Get insights
        insights = self.learning_engine.get_learning_insights(self.user_id)
        
        # Check insights
        self.assertIn("metrics", insights)
        self.assertIn("trends", insights)
        self.assertIn("1_day", insights["metrics"])
        self.assertIn("7_day", insights["trends"])
    
    def test_apply_manual_adjustment(self):
        """Test applying a manual adjustment."""
        # Configure mocks
        self.mock_adaptation_engine.get_adaptation_value.return_value = 0.5
        
        # Apply adjustment
        result = self.learning_engine.apply_manual_adjustment(
            self.user_id, "detail_level", 0.8)
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["previous_value"], 0.5)
        self.assertEqual(result["applied_value"], 0.8)
        
        # Verify adaptation was set
        self.mock_adaptation_engine.set_adaptation_value.assert_called_once_with(
            self.user_id, "detail_level", 0.8)
        
        # Verify memory recording
        self.mock_adjustment_system._record_adjustments_to_memory.assert_called_once()
    
    def test_reset_user_adaptations(self):
        """Test resetting all adaptations for a user."""
        # Configure mocks
        self.mock_adjustment_system.recent_adjustments = {self.user_id: {"detail_level": {}}}
        
        # Reset adaptations
        result = self.learning_engine.reset_user_adaptations(self.user_id)
        
        # Check result
        self.assertEqual(result["status"], "success")
        
        # Verify adaptations were reset
        self.mock_adaptation_engine.reset_adaptations.assert_called_once_with(self.user_id)
        
        # Verify adjustment history was cleared
        self.assertNotIn(self.user_id, self.mock_adjustment_system.recent_adjustments)
        
        # Verify memory recording
        self.mock_adjustment_system.memory_manager.add_memory_with_context.assert_called_once()


if __name__ == "__main__":
    unittest.main()
