"""
Workflow Automation System

This module implements a structured workflow system inspired by MetaGPT's SOPs
(Standard Operating Procedures) to handle complex tasks autonomously.
"""

import logging
import time
import json
import uuid
from typing import Dict, List, Any, Optional, Callable

# Import existing components to build upon
from ai_decision.role_based_switcher import role_based_switcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowStep:
    """Represents a single step in a workflow process"""
    
    def __init__(self, step_id: str, name: str, role: str, description: str, 
                 input_dependencies: List[str] = None):
        """
        Initialize a workflow step
        
        Args:
            step_id: Unique identifier for this step
            name: Human-readable name for this step
            role: The role responsible for executing this step
            description: Detailed description of what this step should accomplish
            input_dependencies: List of step IDs that must complete before this step
        """
        self.step_id = step_id
        self.name = name
        self.role = role
        self.description = description
        self.input_dependencies = input_dependencies or []
        self.status = "pending"  # pending, in_progress, completed, failed
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "input_dependencies": self.input_dependencies,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error": self.error
        }


class WorkflowTemplate:
    """Template for creating specific workflow instances"""
    
    def __init__(self, template_id: str, name: str, description: str, steps: List[Dict[str, Any]]):
        """
        Initialize a workflow template
        
        Args:
            template_id: Unique identifier for this template
            name: Human-readable name for this template
            description: Detailed description of what this workflow accomplishes
            steps: List of step configurations (will be converted to WorkflowStep objects)
        """
        self.template_id = template_id
        self.name = name
        self.description = description
        self.steps = []
        
        # Convert step dictionaries to WorkflowStep objects
        for step_config in steps:
            step = WorkflowStep(
                step_id=step_config["step_id"],
                name=step_config["name"],
                role=step_config["role"],
                description=step_config["description"],
                input_dependencies=step_config.get("input_dependencies", [])
            )
            self.steps.append(step)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps]
        }


class WorkflowInstance:
    """An actual instance of a workflow being executed"""
    
    def __init__(self, instance_id: str, template: WorkflowTemplate, 
                 context: Dict[str, Any], user_id: str):
        """
        Initialize a workflow instance
        
        Args:
            instance_id: Unique identifier for this instance
            template: The WorkflowTemplate this instance is based on
            context: Contextual information for executing this workflow
            user_id: ID of the user this workflow is for
        """
        self.instance_id = instance_id
        self.template_id = template.template_id
        self.user_id = user_id
        self.context = context
        self.status = "initialized"  # initialized, running, completed, failed
        self.steps = []
        self.results = {}
        self.create_time = time.time()
        self.update_time = time.time()
        
        # Deep copy steps from template
        for template_step in template.steps:
            step = WorkflowStep(
                step_id=template_step.step_id,
                name=template_step.name,
                role=template_step.role,
                description=template_step.description,
                input_dependencies=template_step.input_dependencies
            )
            self.steps.append(step)
    
    def get_next_steps(self) -> List[WorkflowStep]:
        """Get all steps that are ready to be executed based on dependencies"""
        next_steps = []
        
        for step in self.steps:
            # Skip steps that aren't pending
            if step.status != "pending":
                continue
                
            # Check if all dependencies are completed
            dependencies_met = True
            for dep_id in step.input_dependencies:
                dependency_completed = False
                for other_step in self.steps:
                    if other_step.step_id == dep_id and other_step.status == "completed":
                        dependency_completed = True
                        break
                
                if not dependency_completed:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                next_steps.append(step)
        
        return next_steps
    
    def update_step_status(self, step_id: str, status: str, result: Any = None, error: str = None) -> bool:
        """
        Update the status of a step
        
        Args:
            step_id: ID of the step to update
            status: New status (in_progress, completed, failed)
            result: Result data if completed
            error: Error message if failed
            
        Returns:
            True if the step was found and updated
        """
        for step in self.steps:
            if step.step_id == step_id:
                step.status = status
                
                if status == "in_progress" and not step.start_time:
                    step.start_time = time.time()
                
                if status in ["completed", "failed"]:
                    step.end_time = time.time()
                    
                if result is not None:
                    step.result = result
                    self.results[step_id] = result
                
                if error is not None:
                    step.error = error
                
                self.update_time = time.time()
                return True
        
        return False
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def is_complete(self) -> bool:
        """Check if all steps are completed"""
        for step in self.steps:
            if step.status != "completed":
                return False
        return True
    
    def has_failed_steps(self) -> bool:
        """Check if any steps have failed"""
        for step in self.steps:
            if step.status == "failed":
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "instance_id": self.instance_id,
            "template_id": self.template_id,
            "user_id": self.user_id,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "context": self.context,
            "create_time": self.create_time,
            "update_time": self.update_time
        }


class WorkflowAutomationSystem:
    """
    Workflow automation system for orchestrating complex multi-step tasks.
    Inspired by MetaGPT's SOP (Standard Operating Procedure) system.
    """
    
    def __init__(self):
        """Initialize the workflow automation system"""
        self.templates = {}
        self.instances = {}
        self.step_handlers = {}
        self.role_switcher = role_based_switcher
        
        # Initialize with built-in workflow templates
        self._initialize_default_templates()
        
        logger.info("Workflow Automation System initialized")
    
    def _initialize_default_templates(self):
        """Initialize the system with default workflow templates"""
        # Software Development Workflow
        software_dev_steps = [
            {
                "step_id": "requirements",
                "name": "Requirements Analysis",
                "role": "researcher",
                "description": "Analyze the requirements and gather necessary information",
                "input_dependencies": []
            },
            {
                "step_id": "planning",
                "name": "Solution Planning",
                "role": "planner",
                "description": "Create a plan for implementing the solution",
                "input_dependencies": ["requirements"]
            },
            {
                "step_id": "design",
                "name": "System Design",
                "role": "designer",
                "description": "Design the components and architecture of the solution",
                "input_dependencies": ["planning"]
            },
            {
                "step_id": "implementation",
                "name": "Implementation",
                "role": "programmer",
                "description": "Implement the solution according to design",
                "input_dependencies": ["design"]
            },
            {
                "step_id": "testing",
                "name": "Testing",
                "role": "programmer",
                "description": "Test the implementation to ensure it meets requirements",
                "input_dependencies": ["implementation"]
            },
            {
                "step_id": "documentation",
                "name": "Documentation",
                "role": "explainer",
                "description": "Document the solution and its usage",
                "input_dependencies": ["implementation"]
            }
        ]
        
        software_dev_template = WorkflowTemplate(
            template_id="software_development",
            name="Software Development Workflow",
            description="A complete workflow for developing software solutions",
            steps=software_dev_steps
        )
        
        # Research and Analysis Workflow
        research_steps = [
            {
                "step_id": "topic_analysis",
                "name": "Topic Analysis",
                "role": "researcher",
                "description": "Analyze the research topic and define key questions",
                "input_dependencies": []
            },
            {
                "step_id": "information_gathering",
                "name": "Information Gathering",
                "role": "researcher",
                "description": "Gather relevant information from various sources",
                "input_dependencies": ["topic_analysis"]
            },
            {
                "step_id": "data_analysis",
                "name": "Data Analysis",
                "role": "researcher",
                "description": "Analyze the gathered information to identify patterns and insights",
                "input_dependencies": ["information_gathering"]
            },
            {
                "step_id": "conclusion_generation",
                "name": "Conclusion Generation",
                "role": "researcher",
                "description": "Generate conclusions based on the analysis",
                "input_dependencies": ["data_analysis"]
            },
            {
                "step_id": "report_creation",
                "name": "Report Creation",
                "role": "explainer",
                "description": "Create a comprehensive report with findings and recommendations",
                "input_dependencies": ["conclusion_generation"]
            }
        ]
        
        research_template = WorkflowTemplate(
            template_id="research_analysis",
            name="Research and Analysis Workflow",
            description="A structured workflow for researching topics and generating insights",
            steps=research_steps
        )
        
        # Register the templates
        self.register_template(software_dev_template)
        self.register_template(research_template)
    
    def register_template(self, template: WorkflowTemplate) -> None:
        """
        Register a workflow template
        
        Args:
            template: The WorkflowTemplate to register
        """
        self.templates[template.template_id] = template
        logger.info(f"Registered workflow template: {template.name}")
    
    def register_step_handler(self, step_name: str, handler: Callable) -> None:
        """
        Register a handler function for a specific type of workflow step
        
        Args:
            step_name: Name of the step type to handle
            handler: Function that will process steps of this type
        """
        self.step_handlers[step_name] = handler
        logger.info(f"Registered step handler for: {step_name}")
    
    def create_workflow_instance(self, template_id: str, context: Dict[str, Any], 
                                user_id: str) -> Optional[str]:
        """
        Create a new workflow instance from a template
        
        Args:
            template_id: ID of the template to use
            context: Contextual information for this workflow
            user_id: ID of the user this workflow is for
            
        Returns:
            ID of the created instance or None if template not found
        """
        if template_id not in self.templates:
            logger.error(f"Template not found: {template_id}")
            return None
        
        instance_id = str(uuid.uuid4())
        instance = WorkflowInstance(
            instance_id=instance_id,
            template=self.templates[template_id],
            context=context,
            user_id=user_id
        )
        
        self.instances[instance_id] = instance
        logger.info(f"Created workflow instance {instance_id} for template {template_id}")
        
        return instance_id
    
    def get_workflow_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a workflow instance
        
        Args:
            instance_id: ID of the workflow instance
            
        Returns:
            Status dictionary or None if instance not found
        """
        if instance_id not in self.instances:
            logger.error(f"Workflow instance not found: {instance_id}")
            return None
        
        instance = self.instances[instance_id]
        
        # Calculate progress as percentage of completed steps
        total_steps = len(instance.steps)
        completed_steps = sum(1 for step in instance.steps if step.status == "completed")
        progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        # Get all step statuses
        step_statuses = []
        for step in instance.steps:
            step_status = {
                "step_id": step.step_id,
                "name": step.name,
                "status": step.status,
                "role": step.role
            }
            
            if step.start_time:
                step_status["start_time"] = step.start_time
            
            if step.end_time:
                step_status["end_time"] = step.end_time
                step_status["duration"] = step.end_time - step.start_time
            
            if step.error:
                step_status["error"] = step.error
                
            step_statuses.append(step_status)
        
        return {
            "instance_id": instance_id,
            "template_id": instance.template_id,
            "status": instance.status,
            "progress": progress,
            "steps": step_statuses,
            "create_time": instance.create_time,
            "update_time": instance.update_time
        }
    
    def execute_step(self, instance_id: str, step_id: str, 
                     input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific step in a workflow
        
        Args:
            instance_id: ID of the workflow instance
            step_id: ID of the step to execute
            input_data: Input data for the step
            
        Returns:
            Result dictionary with execution status
        """
        if instance_id not in self.instances:
            return {"success": False, "error": f"Workflow instance not found: {instance_id}"}
        
        instance = self.instances[instance_id]
        step = instance.get_step(step_id)
        
        if not step:
            return {"success": False, "error": f"Step not found: {step_id}"}
        
        if step.status != "pending":
            return {"success": False, "error": f"Step is not pending, current status: {step.status}"}
        
        # Check if dependencies are met
        for dep_id in step.input_dependencies:
            dep_step = instance.get_step(dep_id)
            if not dep_step or dep_step.status != "completed":
                return {
                    "success": False, 
                    "error": f"Dependency not met: {dep_id}, status: {dep_step.status if dep_step else 'not found'}"
                }
        
        # Mark step as in progress
        instance.update_step_status(step_id, "in_progress")
        
        # Get role and model information
        role_config = self.role_switcher.get_role_configuration(step.role)
        if not role_config:
            instance.update_step_status(
                step_id, 
                "failed", 
                error=f"Role configuration not found: {step.role}"
            )
            return {"success": False, "error": f"Role configuration not found: {step.role}"}
        
        # Execute the step using the appropriate handler
        # In a real implementation, this would use the registered step handlers
        try:
            # Placeholder for actual execution logic
            # This would integrate with the AI coordinator for processing
            
            result = {
                "role": step.role,
                "model": role_config["model_preference"],
                "input": input_data,
                "output": f"Simulated output for step {step.name}",
                "execution_time": time.time()
            }
            
            # Mark step as completed with result
            instance.update_step_status(step_id, "completed", result=result)
            
            # Check if workflow is complete
            if instance.is_complete():
                instance.status = "completed"
            
            return {
                "success": True,
                "step_id": step_id,
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            error_message = f"Error executing step {step_id}: {str(e)}"
            logger.error(error_message)
            instance.update_step_status(step_id, "failed", error=error_message)
            return {"success": False, "error": error_message}
    
    def execute_workflow(self, instance_id: str, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an entire workflow from start to finish
        
        Args:
            instance_id: ID of the workflow instance
            initial_input: Initial input data for the workflow
            
        Returns:
            Dictionary with workflow execution result
        """
        if instance_id not in self.instances:
            return {"success": False, "error": f"Workflow instance not found: {instance_id}"}
        
        instance = self.instances[instance_id]
        instance.status = "running"
        
        current_input = initial_input
        results = {}
        
        # Execute steps in topological order (respecting dependencies)
        while True:
            next_steps = instance.get_next_steps()
            
            if not next_steps:
                # No more steps to execute
                break
            
            for step in next_steps:
                step_result = self.execute_step(instance_id, step.step_id, current_input)
                
                if step_result["success"]:
                    # Add this step's result to the results collection
                    results[step.step_id] = step_result["result"]
                    
                    # Update the input for the next steps
                    current_input = {
                        **current_input,
                        "previous_step_result": step_result["result"],
                        "previous_step_id": step.step_id,
                        "workflow_results": results
                    }
                else:
                    # If any step fails, mark the workflow as failed
                    instance.status = "failed"
                    return {
                        "success": False,
                        "error": step_result["error"],
                        "failed_step": step.step_id,
                        "partial_results": results
                    }
        
        # Check if all steps completed successfully
        if instance.is_complete():
            instance.status = "completed"
            return {
                "success": True,
                "status": "completed",
                "results": results
            }
        elif instance.has_failed_steps():
            instance.status = "failed"
            return {
                "success": False,
                "status": "failed",
                "error": "One or more steps failed",
                "partial_results": results
            }
        else:
            instance.status = "incomplete"
            return {
                "success": False,
                "status": "incomplete",
                "error": "Workflow execution incomplete",
                "partial_results": results
            }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get a list of all available workflow templates"""
        return [
            {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description
            }
            for template in self.templates.values()
        ]


# Create a singleton instance
workflow_automation = WorkflowAutomationSystem()

if __name__ == "__main__":
    # Example usage
    print("Testing Workflow Automation System")
    
    # Get available templates
    templates = workflow_automation.get_available_templates()
    print(f"\nAvailable Templates: {json.dumps(templates, indent=2)}")
    
    # Create a workflow instance
    user_id = "workflow_test_user"
    context = {"task": "Create a Python web application"}
    
    instance_id = workflow_automation.create_workflow_instance(
        template_id="software_development",
        context=context,
        user_id=user_id
    )
    
    if instance_id:
        print(f"\nCreated workflow instance: {instance_id}")
        
        # Get initial status
        status = workflow_automation.get_workflow_status(instance_id)
        print(f"\nInitial Status: {json.dumps(status, indent=2)}")
        
        # Execute the workflow
        result = workflow_automation.execute_workflow(
            instance_id=instance_id,
            initial_input={"requirements": "Build a web application that displays user data"}
        )
        
        print(f"\nWorkflow Execution Result: {json.dumps(result, indent=2)}")
        
        # Get final status
        final_status = workflow_automation.get_workflow_status(instance_id)
        print(f"\nFinal Status: {json.dumps(final_status, indent=2)}")
    else:
        print("Failed to create workflow instance")
