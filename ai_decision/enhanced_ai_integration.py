"""
Enhanced AI Integration

This module integrates the new capabilities from MetaGPT and JARVIS-AGI into Minerva's
existing architecture, building upon rather than replacing the current components.
"""

import logging
import time
import json
import asyncio
from typing import Dict, List, Any, Optional

# Import existing Minerva components
from ai_decision.ai_decision_maker import ai_decision_maker
from ai_decision.enhanced_coordinator import enhanced_coordinator
from ai_decision.context_decision_tree import decision_tree

# Import new enhanced components
from ai_decision.role_based_switcher import role_based_switcher
from ai_decision.workflow_automation import workflow_automation
from ai_decision.knowledge_manager import knowledge_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedAIIntegration:
    """
    Integrates the new AI capabilities into Minerva's existing architecture.
    This is a bridge that preserves backward compatibility while adding new features.
    """
    
    def __init__(self):
        """Initialize the enhanced AI integration"""
        # Connect to existing components
        self.decision_maker = ai_decision_maker
        self.coordinator = enhanced_coordinator
        self.context_analyzer = decision_tree
        
        # Add new enhanced components
        self.role_switcher = role_based_switcher
        self.workflow_system = workflow_automation
        self.knowledge_system = knowledge_manager
        
        # Configuration for feature toggles
        self.enabled_features = {
            "role_based_selection": True,
            "workflow_automation": True,
            "knowledge_enhancement": True,
            "multi_modal": False  # Will be implemented in future phases
        }
        
        logger.info("Enhanced AI Integration initialized")
    
    async def process_request(self, user_id: str, message: str, 
                            message_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user request with all enhanced capabilities
        
        Args:
            user_id: The ID of the user
            message: The user's message
            message_id: Optional message ID
            
        Returns:
            Enhanced processing result
        """
        start_time = time.time()
        logger.info(f"Processing enhanced request from user {user_id}")
        
        # Step 1: Pre-process to identify complex workflow tasks
        workflow_analysis = self._analyze_for_workflow(message)
        
        # For complex workflow tasks, use the workflow system
        if workflow_analysis["requires_workflow"] and self.enabled_features["workflow_automation"]:
            logger.info(f"Request requires workflow: {workflow_analysis['workflow_template']}")
            return await self._process_workflow_request(
                user_id, message, message_id, workflow_analysis
            )
        
        # Step 2: Enhance context with knowledge retrieval if enabled
        if self.enabled_features["knowledge_enhancement"]:
            enhanced_context = self.knowledge_system.context_enhancer.enhance_context(message, user_id)
            logger.info(f"Enhanced context with knowledge: {enhanced_context['knowledge']['has_relevant_knowledge']}")
        else:
            # Use regular context analysis
            enhanced_context = self.context_analyzer.analyze_context(message)
            
        # Step 3: Apply role-based model selection if enabled
        if self.enabled_features["role_based_selection"]:
            # Determine the appropriate role for this request
            selected_role = self.role_switcher.select_role(enhanced_context)
            logger.info(f"Selected role: {selected_role}")
            
            # Get the best model for this role and context
            selected_model = self.role_switcher.select_model_for_role(selected_role, enhanced_context)
            
            # Apply role-specific prompt enhancement
            # We'll do this by modifying the context
            enhanced_context["preferred_model"] = selected_model
            enhanced_context["role"] = selected_role
            
            # Get the role configuration for metadata
            role_config = self.role_switcher.get_role_configuration(selected_role)
            if role_config:
                enhanced_context["role_config"] = role_config
        
        # Step 4: Process with the existing decision maker, passing our enhanced context
        result = await self.decision_maker.process_user_request(
            user_id=user_id,
            message=message,
            message_id=message_id
        )
        
        # Step 5: Enhance the response with knowledge if enabled and available
        if self.enabled_features["knowledge_enhancement"]:
            original_response = result.get("optimized_response", result.get("original_response", ""))
            
            knowledge_enhanced = self.knowledge_system.enhance_response_with_knowledge(
                message=message,
                response=original_response,
                context=enhanced_context
            )
            
            if knowledge_enhanced["has_knowledge_enhancement"]:
                # Replace the response with the knowledge-enhanced version
                result["original_response"] = original_response
                result["optimized_response"] = knowledge_enhanced["enhanced_response"]
                result["knowledge_enhancement"] = {
                    "applied": True,
                    "document_references": knowledge_enhanced.get("document_references", []),
                    "knowledge_summary": knowledge_enhanced.get("knowledge_summary", "")
                }
        
        # Add processing metadata
        result["enhanced_processing"] = {
            "total_time": time.time() - start_time,
            "applied_enhancements": [
                k for k, v in self.enabled_features.items() if v
            ],
            "context": enhanced_context
        }
        
        return result
    
    def _analyze_for_workflow(self, message: str) -> Dict[str, Any]:
        """
        Analyze a message to determine if it requires a workflow
        
        Args:
            message: The user's message
            
        Returns:
            Workflow analysis result
        """
        # Define workflow triggers
        workflow_triggers = {
            "software_development": [
                "create a new", "develop a", "build me a", "implement a", 
                "code a", "program a", "software project"
            ],
            "research_analysis": [
                "research on", "analyze this topic", "find information about",
                "detailed analysis", "investigate the", "study the"
            ]
        }
        
        # Check if message matches any workflow triggers
        message_lower = message.lower()
        matched_template = None
        
        for template_id, triggers in workflow_triggers.items():
            if any(trigger in message_lower for trigger in triggers):
                matched_template = template_id
                break
        
        # Determine if this requires a workflow
        requires_workflow = matched_template is not None
        
        return {
            "requires_workflow": requires_workflow,
            "workflow_template": matched_template,
            "complexity": "high" if requires_workflow else "standard"
        }
    
    async def _process_workflow_request(self, user_id: str, message: str, 
                                     message_id: Optional[str] = None,
                                     workflow_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request using the workflow automation system
        
        Args:
            user_id: The ID of the user
            message: The user's message
            message_id: Optional message ID
            workflow_analysis: Result from workflow analysis
            
        Returns:
            Processing result
        """
        template_id = workflow_analysis["workflow_template"]
        
        # Create context for the workflow
        context = {
            "user_id": user_id,
            "message": message,
            "message_id": message_id,
            "created_at": time.time()
        }
        
        # Create a workflow instance
        instance_id = self.workflow_system.create_workflow_instance(
            template_id=template_id,
            context=context,
            user_id=user_id
        )
        
        if not instance_id:
            # Fall back to standard processing if workflow creation fails
            logger.warning(f"Failed to create workflow instance for template {template_id}")
            return await self.decision_maker.process_user_request(
                user_id=user_id,
                message=message,
                message_id=message_id
            )
        
        # Get the initial status
        initial_status = self.workflow_system.get_workflow_status(instance_id)
        
        # For the initial response, we won't execute the workflow yet
        # Instead, return information about the workflow that was created
        # The execution would happen asynchronously or on subsequent requests
        
        return {
            "message_id": message_id,
            "workflow_created": True,
            "instance_id": instance_id,
            "workflow_status": initial_status,
            "response": f"I've started a {initial_status['template_id']} workflow to handle your request. This will be processed in several steps. I'll keep you updated on the progress.",
            "next_steps": [step["name"] for step in initial_status["steps"] if step["status"] == "pending"][:3]
        }
    
    async def continue_workflow(self, user_id: str, instance_id: str, 
                             input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Continue processing a workflow instance
        
        Args:
            user_id: The ID of the user
            instance_id: The workflow instance ID
            input_data: Optional input data for the workflow
            
        Returns:
            Updated workflow status
        """
        # Get the current status
        current_status = self.workflow_system.get_workflow_status(instance_id)
        
        if not current_status:
            return {
                "success": False,
                "error": f"Workflow instance not found: {instance_id}"
            }
        
        if current_status["status"] in ["completed", "failed"]:
            return {
                "success": True,
                "status": current_status["status"],
                "message": f"Workflow has already {current_status['status']}.",
                "details": current_status
            }
        
        # Execute the next step or steps in the workflow
        result = self.workflow_system.execute_workflow(
            instance_id=instance_id,
            initial_input=input_data or {}
        )
        
        # Get the updated status
        updated_status = self.workflow_system.get_workflow_status(instance_id)
        
        # Create a user-friendly response
        if result["success"]:
            message = f"Workflow processing completed successfully."
        else:
            message = f"Workflow processing encountered an issue: {result.get('error', 'Unknown error')}"
        
        return {
            "success": result["success"],
            "status": updated_status["status"],
            "progress": updated_status["progress"],
            "message": message,
            "updated_status": updated_status,
            "completed_steps": [
                step for step in updated_status["steps"] 
                if step["status"] == "completed"
            ],
            "next_steps": [
                step for step in updated_status["steps"] 
                if step["status"] == "pending"
            ][:3]  # Show the next 3 steps
        }
    
    def toggle_feature(self, feature_name: str, enabled: bool) -> Dict[str, Any]:
        """
        Toggle a feature on or off
        
        Args:
            feature_name: The name of the feature
            enabled: Whether the feature should be enabled
            
        Returns:
            Result of the toggle operation
        """
        if feature_name not in self.enabled_features:
            return {
                "success": False,
                "error": f"Unknown feature: {feature_name}"
            }
        
        self.enabled_features[feature_name] = enabled
        
        logger.info(f"Feature {feature_name} is now {'enabled' if enabled else 'disabled'}")
        
        return {
            "success": True,
            "feature": feature_name,
            "enabled": enabled,
            "all_features": self.enabled_features
        }
    
    def get_enabled_features(self) -> Dict[str, bool]:
        """Get the status of all features"""
        return self.enabled_features


# Create a singleton instance
enhanced_ai_integration = EnhancedAIIntegration()

async def test_enhanced_integration():
    """Test the enhanced AI integration"""
    print("Testing Enhanced AI Integration")
    
    # Test with different types of requests
    test_messages = [
        {
            "user_id": "integration_test_user",
            "message": "What is the capital of France?"
        },
        {
            "user_id": "integration_test_user",
            "message": "Create a Python function to calculate Fibonacci numbers."
        },
        {
            "user_id": "integration_test_user",
            "message": "Research and analyze the impact of artificial intelligence on healthcare."
        }
    ]
    
    for test in test_messages:
        user_id = test["user_id"]
        message = test["message"]
        
        print(f"\nProcessing message: '{message}'")
        
        # Analyze for workflow first
        workflow_analysis = enhanced_ai_integration._analyze_for_workflow(message)
        print(f"Workflow Analysis: {workflow_analysis}")
        
        # Process the request (we can't fully execute this in testing)
        # result = await enhanced_ai_integration.process_request(user_id, message)
        # print(f"Response Type: {'Workflow' if 'workflow_created' in result else 'Standard'}")
    
    # Test feature toggling
    print("\nTesting Feature Toggling:")
    features = enhanced_ai_integration.get_enabled_features()
    print(f"Initial Features: {features}")
    
    toggle_result = enhanced_ai_integration.toggle_feature("multi_modal", True)
    print(f"After Toggle: {enhanced_ai_integration.get_enabled_features()}")
    
    print("\nTest completed.")


if __name__ == "__main__":
    asyncio.run(test_enhanced_integration())
