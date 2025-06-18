"""
Adaptive Response Optimizer

This module implements self-improvement loops for optimizing responses based on
feedback analysis. It tracks common adjustment requests and progressively tunes
responses based on feedback signals.
"""

import os
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix import paths
import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from users.feedback_analysis import feedback_analyzer
from users.global_feedback_manager import global_feedback_manager

class AdaptiveResponseOptimizer:
    """
    Optimizes responses using AI self-improvement loops based on feedback patterns.
    Implements progressive response tuning and adaptive response scaling.
    """
    
    def __init__(self):
        """Initialize the adaptive response optimizer."""
        # Reference to the feedback analyzer
        self.feedback_analyzer = feedback_analyzer
        
        # Reference to global feedback manager
        self.feedback_manager = global_feedback_manager
        
        # Optimization parameters
        self.optimization_thresholds = {
            "confidence_required": 0.5,  # Minimum confidence for applying optimizations
            "feedback_count_required": 5,  # Minimum feedback items for reliable optimization
            "adaptation_rate": 0.1,  # How quickly to adapt (0.0-1.0)
            "max_adjustment": 0.3   # Maximum adjustment factor
        }
        
        logger.info("Adaptive Response Optimizer initialized")
    
    def get_optimized_parameters(self, user_id: str, message: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get optimized parameters for response generation based on feedback analysis
        and message characteristics.
        
        Args:
            user_id: Unique identifier for the user
            message: The user's message
            model_name: Optional name of the model generating the response
            
        Returns:
            Dict containing optimized parameters for response generation
        """
        # Get base parameters from feedback analysis
        user_analysis = self.feedback_analyzer.analyze_user_feedback(user_id)
        
        # Default parameters
        defaults = {
            "length_factor": 1.0,  # Normal length
            "detail_level": 1.0,   # Normal detail
            "formality_level": 0.5, # Neutral formality
            "structure_preference": "balanced"  # Balanced structure
        }
        
        # If not enough feedback or low confidence, return defaults
        confidence_score = user_analysis.get("confidence_score", 0.0)
        feedback_count = user_analysis.get("feedback_count", 0)
        
        if confidence_score < self.optimization_thresholds["confidence_required"] or \
           feedback_count < self.optimization_thresholds["feedback_count_required"]:
            return defaults
        
        # Get patterns from the analysis
        patterns = user_analysis.get("patterns", {})
        
        # Optimize parameters based on patterns
        optimized_params = defaults.copy()
        
        # Adjust length factor based on feedback
        length_patterns = patterns.get("length", {})
        if length_patterns.get("too_long", 0) > length_patterns.get("too_short", 0):
            # Users find responses too long, shorten them
            adjustment = min(
                self.optimization_thresholds["max_adjustment"],
                length_patterns.get("too_long", 0) * self.optimization_thresholds["adaptation_rate"]
            )
            optimized_params["length_factor"] = max(0.7, 1.0 - adjustment)
        elif length_patterns.get("too_short", 0) > length_patterns.get("too_long", 0):
            # Users find responses too short, lengthen them
            adjustment = min(
                self.optimization_thresholds["max_adjustment"],
                length_patterns.get("too_short", 0) * self.optimization_thresholds["adaptation_rate"]
            )
            optimized_params["length_factor"] = min(1.3, 1.0 + adjustment)
        
        # Message-specific adjustments based on complexity and length
        message_complexity = self._analyze_message_complexity(message)
        if message_complexity > 0.7:  # Complex message
            # For complex messages, we might need more detail
            optimized_params["detail_level"] = min(1.2, optimized_params["detail_level"] * 1.1)
        elif message_complexity < 0.3:  # Simple message
            # For simple messages, we might need less detail
            optimized_params["detail_level"] = max(0.8, optimized_params["detail_level"] * 0.9)
        
        # Add metadata
        optimized_params["optimization_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "user_id": user_id,
            "message_length": len(message),
            "message_complexity": message_complexity,
            "confidence_score": confidence_score,
            "feedback_count": feedback_count,
            "model_name": model_name
        }
        
        return optimized_params
    
    def optimize_response(self, response: str, optimization_params: Dict[str, Any]) -> str:
        """
        Optimize a response based on learned parameters and feedback patterns.
        
        Args:
            response: The original response to optimize
            optimization_params: Parameters for optimization
            
        Returns:
            Optimized response
        """
        try:
            # Extract optimization parameters
            length_factor = optimization_params.get("length_factor", 1.0)
            detail_level = optimization_params.get("detail_level", 1.0)
            formality_level = optimization_params.get("formality_level", 0.5)
            structure_preference = optimization_params.get("structure_preference", "balanced")
            
            # Apply optimizations
            optimized_response = response
            
            # Optimize length if needed
            if length_factor < 0.9 or length_factor > 1.1:
                optimized_response = self._optimize_length(optimized_response, length_factor)
            
            # Optimize detail level if needed
            if detail_level < 0.9 or detail_level > 1.1:
                optimized_response = self._optimize_detail(optimized_response, detail_level)
            
            # Apply formality adjustments if needed
            if formality_level < 0.4:
                optimized_response = self._optimize_formality(optimized_response, "casual")
            elif formality_level > 0.6:
                optimized_response = self._optimize_formality(optimized_response, "formal")
            
            # Apply structure optimizations if needed
            if structure_preference != "balanced":
                optimized_response = self._optimize_structure(optimized_response, structure_preference)
            
            return optimized_response
            
        except Exception as e:
            logger.error(f"Error optimizing response: {str(e)}")
            # Return original response if optimization fails
            return response
    
    def record_optimization_feedback(self, user_id: str, message_id: str, 
                                    is_positive: bool, optimization_params: Dict[str, Any]) -> None:
        """
        Record feedback specifically about optimization parameters to improve future optimizations.
        
        Args:
            user_id: Unique identifier for the user
            message_id: Identifier for the message
            is_positive: Whether the feedback is positive
            optimization_params: Parameters used for optimization
        """
        try:
            # Extract metadata from optimization params
            metadata = optimization_params.get("optimization_metadata", {})
            
            # Record feedback using global feedback manager
            self.feedback_manager.record_feedback(
                user_id=user_id,
                message_id=message_id,
                is_positive=is_positive,
                feedback_type="optimization",
                ai_instance_id=metadata.get("model_name", "optimizer")
            )
            
            logger.info(f"Recorded optimization feedback for user {user_id}, message {message_id}")
            
        except Exception as e:
            logger.error(f"Error recording optimization feedback: {str(e)}")
    
    def _analyze_message_complexity(self, message: str) -> float:
        """
        Analyze message complexity to inform optimization.
        
        Args:
            message: The user's message
            
        Returns:
            Float representing message complexity (0.0-1.0)
        """
        # Simple heuristics for message complexity
        
        # 1. Length-based complexity
        length_score = min(1.0, len(message) / 500)  # Normalize up to 500 chars
        
        # 2. Vocabulary complexity
        words = re.findall(r'\b\w+\b', message.lower())
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        vocab_score = min(1.0, avg_word_length / 8)  # Normalize up to avg length of 8
        
        # 3. Question complexity
        question_count = message.count('?')
        question_score = min(1.0, question_count / 3)  # Normalize up to 3 questions
        
        # Combine scores with different weights
        complexity_score = (0.4 * length_score) + (0.4 * vocab_score) + (0.2 * question_score)
        
        return complexity_score
    
    def _optimize_length(self, response: str, length_factor: float) -> str:
        """
        Optimize response length based on the length factor.
        
        Args:
            response: Original response
            length_factor: Factor to adjust length (< 1.0 = shorter, > 1.0 = longer)
            
        Returns:
            Length-optimized response
        """
        # Split into paragraphs
        paragraphs = response.split('\n\n')
        
        if length_factor < 1.0:
            # Shorten response
            if len(paragraphs) > 1:
                # Keep fewer paragraphs for shorter responses
                keep_count = max(1, int(len(paragraphs) * length_factor))
                shortened = paragraphs[:keep_count]
                
                # Add a note if significant content was removed
                if keep_count < len(paragraphs) - 1:
                    shortened.append("(Response shortened based on your feedback preferences)")
                
                return '\n\n'.join(shortened)
            else:
                # Single paragraph, use sentence trimming
                sentences = re.split(r'(?<=[.!?])\s+', response)
                keep_count = max(1, int(len(sentences) * length_factor))
                return ' '.join(sentences[:keep_count])
        
        elif length_factor > 1.0:
            # For longer responses, we don't actually generate new content
            # Instead, we ensure formatting that makes the response more detailed
            # This is just a simple placeholder - in practice you'd need more sophisticated logic
            return response
        
        return response
    
    def _optimize_detail(self, response: str, detail_level: float) -> str:
        """
        Optimize response detail level.
        
        Args:
            response: Original response
            detail_level: Factor to adjust detail (< 1.0 = less detail, > 1.0 = more detail)
            
        Returns:
            Detail-optimized response
        """
        # Simplified implementation
        if detail_level < 1.0:
            # Reduce detail by focusing on main points
            # This is a placeholder - would need more sophisticated implementation
            return response
        
        elif detail_level > 1.0:
            # For more detail, we encourage structured explanations
            # Again, this is a placeholder
            return response
            
        return response
    
    def _optimize_formality(self, response: str, formality: str) -> str:
        """
        Optimize response formality.
        
        Args:
            response: Original response
            formality: Target formality level ("formal", "casual", or "neutral")
            
        Returns:
            Formality-optimized response
        """
        # Placeholder implementation
        return response
    
    def _optimize_structure(self, response: str, structure_preference: str) -> str:
        """
        Optimize response structure.
        
        Args:
            response: Original response
            structure_preference: Preferred structure ("organized", "structured", "conversational")
            
        Returns:
            Structure-optimized response
        """
        # Placeholder implementation
        return response


# Create a singleton instance
response_optimizer = AdaptiveResponseOptimizer()


def test_adaptive_optimizer():
    """Test the AdaptiveResponseOptimizer functionality."""
    print("Testing Adaptive Response Optimizer...")
    
    # Test with a sample message
    sample_message = "Can you explain quantum computing in detail? I'm trying to understand the basic principles."
    sample_user = "test_optimizer_user"
    
    # Get optimized parameters
    params = response_optimizer.get_optimized_parameters(sample_user, sample_message)
    print(f"Optimized parameters: {json.dumps(params, indent=2)}")
    
    # Test with a sample response
    sample_response = """
    Quantum computing leverages principles of quantum mechanics to process information in ways that classical computers cannot. 
    
    At its core, quantum computing uses quantum bits or "qubits" instead of traditional binary bits. While classical bits can only be in a state of 0 or 1, qubits can exist in a superposition of both states simultaneously, enabling quantum computers to process a vastly greater number of possibilities at once.
    
    Key principles include:
    1. Superposition: Qubits can represent multiple states at the same time
    2. Entanglement: Qubits can be correlated in ways that have no classical analogue
    3. Quantum interference: Allows amplification of correct solutions and cancellation of incorrect ones
    
    Current quantum computers are still in early stages, with challenges in maintaining qubit coherence and scaling systems to practical sizes. However, they show promise for applications in cryptography, drug discovery, optimization problems, and simulating quantum systems.
    """
    
    # Optimize the response
    optimized = response_optimizer.optimize_response(sample_response, params)
    
    print("\nOriginal response length:", len(sample_response))
    print("Optimized response length:", len(optimized))
    print("\nTest completed.")


if __name__ == "__main__":
    test_adaptive_optimizer()
