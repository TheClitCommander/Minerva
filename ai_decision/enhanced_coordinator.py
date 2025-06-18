"""
Enhanced Multi-AI Coordinator

This module enhances the existing Multi-AI Coordinator with context-aware decision trees
and intelligent model switching capabilities.
"""

import os
import sys
import logging
import asyncio
import time
from typing import Dict, Any, Optional, List

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the decision-making components
from ai_decision.context_decision_tree import decision_tree
from ai_decision.ai_model_switcher import model_switcher

# Import the existing coordinator for integration
from web.multi_ai_coordinator import multi_ai_coordinator

class EnhancedCoordinator:
    """
    Enhances Minerva's decision-making with context-aware analysis and adaptive model selection.
    """
    
    def __init__(self):
        """Initialize the enhanced coordinator."""
        self.decision_tree = decision_tree
        self.model_switcher = model_switcher
        self.base_coordinator = multi_ai_coordinator
        
        # Track interaction history for contextual improvements
        self.interaction_history = {}
        
        logger.info("Enhanced AI Coordinator initialized")
    
    def record_interaction(self, user_id: str, message: str, response: str, model_used: str, quality_score: float):
        """
        Record an interaction to build context history.
        
        Args:
            user_id: The ID of the user
            message: The user's message
            response: The AI's response
            model_used: The AI model that generated the response
            quality_score: The quality score for the response
        """
        if user_id not in self.interaction_history:
            self.interaction_history[user_id] = []
            
        # Add the interaction to the history
        self.interaction_history[user_id].append({
            "timestamp": time.time(),
            "message": message,
            "response": response[:100] + "..." if len(response) > 100 else response,  # Store truncated response
            "model_used": model_used,
            "quality_score": quality_score
        })
        
        # Keep only the last 10 interactions
        if len(self.interaction_history[user_id]) > 10:
            self.interaction_history[user_id] = self.interaction_history[user_id][-10:]
            
        logger.info(f"Recorded interaction for user {user_id}, quality score: {quality_score:.2f}")
    
    def get_context_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get the interaction history for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The user's interaction history
        """
        return self.interaction_history.get(user_id, [])
    
    def enhance_decision_parameters(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Enhance decision parameters with context analysis.
        
        Args:
            user_id: The ID of the user
            message: The user's message
            
        Returns:
            Enhanced decision parameters
        """
        # Get basic context analysis
        context_analysis = self.decision_tree.analyze_context(message)
        
        # Get user interaction history
        history = self.get_context_history(user_id)
        
        # Enhance parameters based on history
        if history:
            # Calculate average quality score from recent interactions
            avg_quality = sum(item["quality_score"] for item in history) / len(history)
            
            # Track model performance
            model_performance = {}
            for item in history:
                model = item["model_used"]
                if model not in model_performance:
                    model_performance[model] = {"count": 0, "total_score": 0}
                model_performance[model]["count"] += 1
                model_performance[model]["total_score"] += item["quality_score"]
            
            # Find best performing model based on history
            best_model = None
            best_score = -1
            for model, data in model_performance.items():
                if data["count"] >= 2:  # Require at least 2 interactions with this model
                    avg_score = data["total_score"] / data["count"]
                    if avg_score > best_score:
                        best_score = avg_score
                        best_model = model
            
            # Add these insights to the parameters
            if best_model:
                context_analysis["preferred_model"] = best_model
                context_analysis["historical_quality"] = avg_quality
        
        return context_analysis
    
    async def process_message(self, user_id: str, message: str, message_id: Optional[str] = None, 
                         override_response: Optional[str] = None, override_model: Optional[str] = None,
                         context_hints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message with enhanced decision-making.
        
        Args:
            user_id: The ID of the user
            message: The user's message
            message_id: Optional message ID
            override_response: Optional pre-generated response (from enhanced AI features)
            override_model: Optional model name to use (from enhanced AI features)
            context_hints: Optional additional context hints to guide processing
            
        Returns:
            The processing result
        """
        start_time = time.time()
        logger.info(f"Enhanced processing for message from user {user_id}")
        
        # Step 1: Enhance decision parameters with context analysis
        enhanced_params = self.enhance_decision_parameters(user_id, message)
        logger.info(f"Enhanced parameters: {enhanced_params}")
        
        # If we have context hints from enhanced AI features, merge them
        if context_hints:
            enhanced_params.update(context_hints)
            logger.info(f"Enhanced with additional context hints: {context_hints.keys()}")
        
        # Step 2: Determine the optimal model based on context (unless overridden)
        selected_model = override_model or self.model_switcher.select_model(enhanced_params)
        logger.info(f"Selected model: {selected_model}{' (overridden)' if override_model else ''}")
        
        # Step 3: Process with the base coordinator, with our enhanced model selection
        models_to_use = [selected_model]
        
        # Map our context analysis to formatting parameters
        formatting_params = {
            "tone": enhanced_params.get("tone", "neutral"),
            "structure": enhanced_params.get("structure", "paragraph"),
            "length": enhanced_params.get("length", "medium")
        }
        
        # Create a comprehensive override for the base coordinator
        self.base_coordinator._override_model_selection = {
            "models_to_use": models_to_use,
            "timeout": 30.0 if enhanced_params.get("detail_level") == "technical" else 15.0,
            "formatting_params": formatting_params,
            "override_response": override_response,  # Pass through any pre-generated response
            "enhanced_processing": True  # Flag that this is processed by enhanced features
        }
        
        # Process with the base coordinator using our enhanced decision
        result = await self.base_coordinator.process_message(user_id, message, message_id)
        
        # Clear the override after use
        self.base_coordinator._override_model_selection = None
        
        # Record this interaction, using the actual response and model used
        self.record_interaction(
            user_id=user_id,
            message=message,
            response=result.get("response", ""),
            model_used=result.get("model_used", override_model or "unknown"),
            quality_score=result.get("quality_score", 0.0)
        )
        
        # Add enhanced processing metadata
        result["enhanced_processing"] = {
            "context_analysis": enhanced_params,
            "suggested_model": selected_model,
            "override_applied": override_response is not None,
            "processing_time": time.time() - start_time,
            "context_hints_applied": bool(context_hints)
        }
        
        return result


# Create a singleton instance
enhanced_coordinator = EnhancedCoordinator()


async def test_enhanced_coordinator():
    """Test the enhanced coordinator."""
    print("Testing Enhanced Multi-AI Coordinator...")
    
    # Test with different context messages
    test_messages = [
        {"user_id": "test_user_1", "message": "Can you explain quantum computing?"},
        {"user_id": "test_user_1", "message": "Be more concise in your explanation."},
        {"user_id": "test_user_2", "message": "Explain in detail how neural networks work."},
        {"user_id": "test_user_2", "message": "Use technical terms in your response."}
    ]
    
    for test in test_messages:
        user_id = test["user_id"]
        message = test["message"]
        
        print(f"\nProcessing message: '{message}'")
        
        # Analyze context first to show the decision process
        context = enhanced_coordinator.enhance_decision_parameters(user_id, message)
        print(f"Context Analysis: {context}")
        
        selected_model = model_switcher.select_model(context)
        print(f"Selected Model: {selected_model}")
        
        # Only uncomment this when integrated with a real coordinator
        # result = await enhanced_coordinator.process_message(user_id, message)
        # print(f"Response Quality Score: {result.get('quality_score', 0.0):.2f}")
    
    print("\nTest completed.")


if __name__ == "__main__":
    asyncio.run(test_enhanced_coordinator())
