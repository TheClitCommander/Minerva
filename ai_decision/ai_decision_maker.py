"""
AI Decision Maker

This module serves as the main integration point for Minerva's AI Decision-Making Enhancements,
combining context-aware decision trees, dynamic AI model switching, and enhanced multi-AI coordination.
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all decision-making components
from ai_decision.context_decision_tree import decision_tree
from ai_decision.ai_model_switcher import model_switcher
from ai_decision.enhanced_coordinator import enhanced_coordinator
from users.feedback_driven_refinements import feedback_driven_refinements

# Import new enhanced AI capabilities
try:
    from ai_decision.role_based_switcher import RoleBasedSwitcher
    from ai_decision.workflow_automation import WorkflowAutomation
    from ai_decision.knowledge_manager import KnowledgeManager
    from ai_decision.enhanced_ai_integration import EnhancedAIIntegration
    ENHANCED_FEATURES_AVAILABLE = True
    logger.info("Enhanced AI features successfully imported")
except ImportError as e:
    logger.warning(f"Some enhanced AI features are not available: {e}")
    ENHANCED_FEATURES_AVAILABLE = False


class AIDecisionMaker:
    """
    Main integration point for Minerva's decision-making capabilities,
    combining context analysis, model selection, and response optimization.
    """
    
    def __init__(self):
        """Initialize the AI Decision Maker."""
        self.context_analyzer = decision_tree
        self.model_switcher = model_switcher
        self.coordinator = enhanced_coordinator
        self.refinements = feedback_driven_refinements
        
        # Initialize enhanced capabilities if available
        self.enhanced_features_available = ENHANCED_FEATURES_AVAILABLE
        if self.enhanced_features_available:
            try:
                # Initialize the role-based switcher for specialized agent roles
                self.role_based_switcher = RoleBasedSwitcher()
                
                # Initialize workflow automation for complex multi-step tasks
                self.workflow_automation = WorkflowAutomation()
                
                # Initialize knowledge management for RAG capabilities
                self.knowledge_manager = KnowledgeManager()
                
                # Initialize the integration layer that manages feature toggling
                self.enhanced_integration = EnhancedAIIntegration(
                    role_based_switcher=self.role_based_switcher,
                    workflow_automation=self.workflow_automation,
                    knowledge_manager=self.knowledge_manager
                )
                logger.info("Enhanced AI features initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize enhanced features: {e}")
                self.enhanced_features_available = False
        
        logger.info("AI Decision Maker initialized")
    
    async def process_user_request(self, user_id: str, message: str, message_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user request with the full AI decision-making pipeline.
        
        Args:
            user_id: The ID of the user
            message: The user's message
            message_id: Optional message ID
            
        Returns:
            The processing result with the final response
        """
        logger.info(f"Processing request from user {user_id}")
        
        # Step 1: Analyze user context and message patterns
        context_analysis = self.context_analyzer.analyze_context(message)
        logger.info(f"Context analysis: {context_analysis}")
        
        # Step 2: Enhance decision parameters based on context history
        enhanced_params = self.coordinator.enhance_decision_parameters(user_id, message)
        logger.info(f"Enhanced parameters: {enhanced_params}")
        
        # Step 3: Apply enhanced AI capabilities if available
        enhanced_result = None
        if self.enhanced_features_available:
            try:
                # Check if this is part of an ongoing workflow
                workflow_context = self.enhanced_integration.get_workflow_context(user_id)
                
                # Enhanced processing path with new capabilities
                enhanced_result = await self.enhanced_integration.process_request(
                    user_id=user_id,
                    message=message,
                    message_id=message_id,
                    context_analysis=context_analysis,
                    enhanced_params=enhanced_params,
                    workflow_context=workflow_context
                )
                
                logger.info(f"Enhanced AI processing completed: {enhanced_result.get('processing_type', 'standard')}")
                
                # If the request was fully handled by enhanced features, merge results and return
                if enhanced_result.get('request_handled', False):
                    logger.info("Request fully handled by enhanced AI features")
                    # Still pass through the coordinator for consistent logging/tracking
                    coordination_result = await self.coordinator.process_message(
                        user_id, message, message_id, 
                        override_response=enhanced_result.get('response'),
                        override_model=enhanced_result.get('model_used')
                    )
                else:
                    # Fall back to standard processing with enhancements applied to parameters
                    coordination_result = await self.coordinator.process_message(
                        user_id, message, message_id,
                        context_hints=enhanced_result.get('context_hints', {})
                    )
            except Exception as e:
                logger.error(f"Error in enhanced AI processing: {e}")
                # Fall back to standard processing path
                coordination_result = await self.coordinator.process_message(user_id, message, message_id)
        else:
            # Standard processing path (no enhanced features)
            coordination_result = await self.coordinator.process_message(user_id, message, message_id)
        
        # Step 4: Apply feedback-driven refinements to optimize the response
        optimized_result = self.refinements.process_response(
            user_id=user_id,
            message=message,
            response=coordination_result.get("response", ""),
            message_id=coordination_result.get("message_id"),
            model_name=coordination_result.get("model_used"),
            user_preferences={"response_length": enhanced_params.get("length", "medium")}
        )
        
        # Step 5: Combine all results into a final response
        final_result = {
            "message_id": coordination_result.get("message_id"),
            "original_response": coordination_result.get("response", ""),
            "optimized_response": optimized_result.get("optimized_response", ""),
            "display_data": optimized_result.get("display_data", {}),
            "feedback_ui": optimized_result.get("feedback_ui", {}),
            "model_used": coordination_result.get("model_used", "unknown"),
            "quality_score": coordination_result.get("quality_score", 0.0),
            "context_analysis": context_analysis,
            "processing_metadata": {
                "coordinator_time": coordination_result.get("processing_time", 0.0),
                "optimization_time": optimized_result.get("processing_metadata", {}).get("processed_at", ""),
                "total_time": 0.0,  # Will be calculated by the calling function
                "context_based_model": self.model_switcher.select_model(context_analysis)
            }
        }
        
        # Add enhanced results if available
        if enhanced_result:
            final_result["enhanced_features"] = {
                "active": True,
                "processing_type": enhanced_result.get("processing_type", "standard"),
                "roles_used": enhanced_result.get("roles_used", []),
                "workflow_active": enhanced_result.get("workflow_active", False),
                "workflow_step": enhanced_result.get("workflow_step", None),
                "knowledge_used": enhanced_result.get("knowledge_used", False),
                "knowledge_sources": enhanced_result.get("knowledge_sources", [])
            }
        else:
            final_result["enhanced_features"] = {"active": False}
        
        logger.info(f"Completed request processing for user {user_id}")
        return final_result
    
    def record_user_feedback(self, user_id: str, message_id: str, is_positive: bool, 
                             feedback_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record user feedback for a response.
        
        Args:
            user_id: The ID of the user
            message_id: The ID of the message
            is_positive: Whether the feedback is positive
            feedback_details: Optional additional feedback details
            
        Returns:
            True if the feedback was successfully recorded
        """
        logger.info(f"Recording feedback from user {user_id} for message {message_id}")
        
        # Record feedback through the feedback-driven refinements system
        feedback_recorded = self.refinements.record_response_feedback(
            user_id=user_id,
            message_id=message_id,
            is_positive=is_positive,
            feedback_details=feedback_details
        )
        
        return feedback_recorded
    
    def get_decision_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get insights about the decision-making process for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Insights about the decision-making process
        """
        # Get interaction history from the coordinator
        history = self.coordinator.get_context_history(user_id)
        
        # Get user insights from the refinements system
        refinement_insights = self.refinements.get_user_insights(user_id)
        
        # Combine into a single insights object
        insights = {
            "interaction_history": history,
            "refinement_insights": refinement_insights,
            "decision_patterns": {
                "preferred_model": None,
                "typical_context": {},
                "feedback_trend": None
            }
        }
        
        # Analyze interaction history for patterns
        if history:
            # Count model usage
            model_counts = {}
            for item in history:
                model = item.get("model_used", "unknown")
                if model not in model_counts:
                    model_counts[model] = 0
                model_counts[model] += 1
            
            # Find most used model
            if model_counts:
                preferred_model = max(model_counts.items(), key=lambda x: x[1])[0]
                insights["decision_patterns"]["preferred_model"] = preferred_model
            
            # Calculate feedback trend
            if len(history) >= 2:
                quality_scores = [item.get("quality_score", 0.0) for item in history]
                first_half = quality_scores[:len(quality_scores)//2]
                second_half = quality_scores[len(quality_scores)//2:]
                
                first_avg = sum(first_half) / len(first_half) if first_half else 0
                second_avg = sum(second_half) / len(second_half) if second_half else 0
                
                if second_avg > first_avg:
                    insights["decision_patterns"]["feedback_trend"] = "improving"
                elif second_avg < first_avg:
                    insights["decision_patterns"]["feedback_trend"] = "declining"
                else:
                    insights["decision_patterns"]["feedback_trend"] = "stable"
        
        return insights


# Create a singleton instance
ai_decision_maker = AIDecisionMaker()


async def test_ai_decision_maker():
    """Test the AI Decision Maker."""
    print("Testing AI Decision Maker...")
    
    # Test with different user messages
    test_messages = [
        {"user_id": "decision_test_user", "message": "Explain how machine learning works."},
        {"user_id": "decision_test_user", "message": "Can you summarize that more briefly?"},
        {"user_id": "decision_test_user", "message": "Now give more technical details about neural networks."}
    ]
    
    for test in test_messages:
        user_id = test["user_id"]
        message = test["message"]
        
        print(f"\nProcessing message: '{message}'")
        
        # Get context analysis first
        context = ai_decision_maker.context_analyzer.analyze_context(message)
        suggested_model = ai_decision_maker.model_switcher.select_model(context)
        
        print(f"Context Analysis: {json.dumps(context, indent=2)}")
        print(f"Suggested Model: {suggested_model}")
        
        # We can't fully test processing without real AI models
        # result = await ai_decision_maker.process_user_request(user_id, message)
        # print(f"Response Quality: {result.get('quality_score', 0.0):.2f}")
    
    # Test insights
    insights = ai_decision_maker.get_decision_insights("decision_test_user")
    print("\nDecision Insights Available:", "Yes" if insights else "No")
    
    print("\nTest completed.")


if __name__ == "__main__":
    asyncio.run(test_ai_decision_maker())
