"""
Role-Based AI Model Switcher

This module enhances the existing AI model selection system with specialized roles
inspired by MetaGPT's multi-agent architecture.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union

# Import existing components to build upon
from ai_decision.ai_model_switcher import AIModelSwitcher, model_switcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoleBasedSwitcher:
    """
    Extends the AI model selection with role-based specialization.
    This allows for specialized models to handle different aspects of a task.
    """

    def __init__(self):
        """Initialize the role-based switcher"""
        # Build on top of the existing model switcher
        self.base_switcher = model_switcher
        
        # Define specialized roles and their model preferences
        self.roles = {
            "researcher": {
                "description": "Specialized in information gathering and analysis",
                "model_preference": "Claude-3-Opus",
                "capabilities": ["information_retrieval", "summarization", "analysis"],
                "prompt_prefix": "As a research specialist, analyze the following topic in depth: "
            },
            "programmer": {
                "description": "Specialized in code generation and debugging",
                "model_preference": "Claude-3-Sonnet",
                "capabilities": ["code_generation", "debugging", "code_explanation"],
                "prompt_prefix": "As a programming expert, address the following code task: "
            },
            "designer": {
                "description": "Specialized in visual and UI design concepts",
                "model_preference": "Claude-3-Sonnet",
                "capabilities": ["design_suggestion", "layout_planning", "ui_components"],
                "prompt_prefix": "As a design specialist, consider the following design challenge: "
            },
            "planner": {
                "description": "Specialized in task breakdown and project planning",
                "model_preference": "Claude-3-Opus",
                "capabilities": ["task_breakdown", "timeline_planning", "resource_allocation"],
                "prompt_prefix": "As a planning expert, develop a structured approach for: "
            },
            "explainer": {
                "description": "Specialized in clear explanations of complex topics",
                "model_preference": "Claude-3-Light",
                "capabilities": ["simplification", "analogies", "step_by_step_explanation"],
                "prompt_prefix": "Explain the following concept clearly and simply: "
            }
        }
        
        # Create a mapping of capabilities to roles for lookup
        self.capability_to_role = {}
        for role_name, role_info in self.roles.items():
            for capability in role_info["capabilities"]:
                if capability not in self.capability_to_role:
                    self.capability_to_role[capability] = []
                self.capability_to_role[capability].append(role_name)
        
        logger.info(f"Role-Based Switcher initialized with {len(self.roles)} specialized roles")
    
    def select_role(self, context_analysis: Dict[str, Any]) -> str:
        """
        Determine the best agent role based on the context analysis.
        
        Args:
            context_analysis: A dictionary containing context information
            
        Returns:
            The name of the selected role
        """
        # Extract task type from context or use default
        task_type = context_analysis.get("task_type", "general")
        
        # Match task type to appropriate role
        if "code" in task_type or "programming" in task_type:
            return "programmer"
        elif "research" in task_type or "information" in task_type:
            return "researcher"
        elif "design" in task_type or "interface" in task_type:
            return "designer"
        elif "plan" in task_type or "organize" in task_type:
            return "planner"
        elif "explain" in task_type or "teaching" in task_type:
            return "explainer"
        
        # Default to the role best matching the detail level
        detail_level = context_analysis.get("detail_level", "balanced")
        if detail_level == "technical":
            return "programmer"
        elif detail_level == "comprehensive":
            return "researcher"
        else:
            return "explainer"
    
    def get_role_configuration(self, role_name: str) -> Dict[str, Any]:
        """
        Get the configuration for a specific role.
        
        Args:
            role_name: The name of the role
            
        Returns:
            Configuration dictionary for the role
        """
        if role_name in self.roles:
            return self.roles[role_name]
        return None
    
    def select_model_for_role(self, role_name: str, context_analysis: Dict[str, Any]) -> str:
        """
        Select the best model for a specific role given the context.
        
        Args:
            role_name: The name of the role
            context_analysis: Dictionary containing context information
            
        Returns:
            The name of the selected model
        """
        # Get the role's preferred model
        role_config = self.get_role_configuration(role_name)
        if not role_config:
            # Fall back to the base switcher if role not found
            return self.base_switcher.select_model(context_analysis)
        
        # Use role's preferred model but consider context overrides
        if context_analysis.get("emergency_response", False):
            # In emergency/quick response mode, use faster models
            return "Claude-3-Light"
        
        # Otherwise use the role's preferred model
        return role_config["model_preference"]
    
    def get_prompt_enhancement(self, role_name: str, prompt: str) -> str:
        """
        Enhance a prompt with role-specific instructions.
        
        Args:
            role_name: The name of the role
            prompt: The original prompt
            
        Returns:
            Enhanced prompt with role-specific instructions
        """
        role_config = self.get_role_configuration(role_name)
        if not role_config:
            return prompt
        
        # Add the role-specific prefix to the prompt
        return f"{role_config['prompt_prefix']}\n\n{prompt}"
    
    def coordinate_multi_role_task(self, context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        For complex tasks, break them down into sub-tasks for different roles.
        
        Args:
            context_analysis: A dictionary containing context information
            
        Returns:
            Task breakdown with assigned roles
        """
        # Determine if task is complex enough to need multiple roles
        task_complexity = context_analysis.get("length", "standard")
        if task_complexity != "long" and context_analysis.get("detail_level", "balanced") != "technical":
            # For simpler tasks, just use a single role
            primary_role = self.select_role(context_analysis)
            return {
                "multi_role": False,
                "primary_role": primary_role,
                "subtasks": None
            }
        
        # For complex tasks, create a task breakdown
        subtasks = []
        
        # Add research subtask if needed
        if "research" in context_analysis.get("task_type", ""):
            subtasks.append({
                "role": "researcher",
                "description": "Research and gather necessary information",
                "order": 1
            })
        
        # Add planning subtask for complex tasks
        subtasks.append({
            "role": "planner",
            "description": "Develop a structured approach to the overall task",
            "order": len(subtasks) + 1
        })
        
        # Add implementation subtask if coding is involved
        if "code" in context_analysis.get("task_type", ""):
            subtasks.append({
                "role": "programmer",
                "description": "Implement the required code solution",
                "order": len(subtasks) + 1
            })
        
        # Add design subtask if UI/UX is involved
        if "design" in context_analysis.get("task_type", ""):
            subtasks.append({
                "role": "designer",
                "description": "Create design specifications and visual elements",
                "order": len(subtasks) + 1
            })
        
        # Always add an explanation subtask
        subtasks.append({
            "role": "explainer",
            "description": "Provide a clear explanation of the solution",
            "order": len(subtasks) + 1
        })
        
        # Determine the primary role based on task type
        primary_role = self.select_role(context_analysis)
        
        return {
            "multi_role": True,
            "primary_role": primary_role,
            "subtasks": subtasks
        }


# Create a singleton instance
role_based_switcher = RoleBasedSwitcher()

if __name__ == "__main__":
    # Example usage
    test_contexts = [
        {"task_type": "code", "detail_level": "technical", "length": "long"},
        {"task_type": "explain", "detail_level": "balanced", "length": "short"},
        {"task_type": "research", "detail_level": "comprehensive", "length": "long"}
    ]
    
    for ctx in test_contexts:
        role = role_based_switcher.select_role(ctx)
        model = role_based_switcher.select_model_for_role(role, ctx)
        multi_role_plan = role_based_switcher.coordinate_multi_role_task(ctx)
        
        print(f"\nContext: {json.dumps(ctx, indent=2)}")
        print(f"Selected Role: {role}")
        print(f"Selected Model: {model}")
        
        if multi_role_plan["multi_role"]:
            print("Task requires multiple roles:")
            for subtask in sorted(multi_role_plan["subtasks"], key=lambda x: x["order"]):
                print(f"  - {subtask['order']}. {subtask['role']}: {subtask['description']}")
        else:
            print("Task can be handled by a single role")
