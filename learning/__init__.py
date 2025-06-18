"""
Minerva Learning Module

This package contains components for Minerva's self-learning system, allowing
the assistant to learn from user interactions, detect patterns, and adapt
its behavior based on user preferences and feedback.

Components:
- PatternDetector: Identifies recurring topics and questions in user conversations
- PreferenceTracker: Learns and tracks user preferences both explicitly and implicitly
- FeedbackIntegration: Processes user feedback to refine learned information
"""

from learning.pattern_detector import PatternDetector
from learning.preference_tracker import PreferenceTracker

__all__ = ['PatternDetector', 'PreferenceTracker']
