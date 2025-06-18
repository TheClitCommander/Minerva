# project_runtime.py

import os
import json
from minerva.core.project_context import ProjectContextManager

def load_project_context(project_name):
    context_manager = ProjectContextManager(project_name)
    return {
        "objectives": context_manager.memory["objectives"],
        "task_queue": context_manager.memory["task_queue"],
        "logs": context_manager.memory["logs"],
        "notes": context_manager.memory["notes"]
    }

def save_project_context(project_name, new_context):
    context_manager = ProjectContextManager(project_name)
    if "objectives" in new_context:
        context_manager.memory["objectives"] = new_context["objectives"]
    if "task_queue" in new_context:
        context_manager.memory["task_queue"] = new_context["task_queue"]
    if "logs" in new_context:
        context_manager.memory["logs"] = new_context["logs"]
    if "notes" in new_context:
        context_manager.memory["notes"] = new_context["notes"]
    context_manager._save_metadata()

# Additional helper functions to align with Minerva Master Ruleset

def link_conversation_to_project(project_name, conversation_id, conversation_title=None):
    """
    Links a conversation to a project, following Rule #3 and #12 of the Minerva Master Ruleset.
    
    Args:
        project_name: Name of the project to link to
        conversation_id: Unique ID of the conversation
        conversation_title: Optional title for the conversation
    
    Returns:
        Boolean indicating success
    """
    context_manager = ProjectContextManager(project_name)
    
    # Initialize conversations list if it doesn't exist
    if "conversations" not in context_manager.memory:
        context_manager.memory["conversations"] = []
    
    # Check if conversation is already linked
    for conv in context_manager.memory["conversations"]:
        if conv.get("id") == conversation_id:
            # Update title if provided
            if conversation_title:
                conv["title"] = conversation_title
            context_manager._save_metadata()
            return True
    
    # Add new conversation link
    context_manager.memory["conversations"].append({
        "id": conversation_id,
        "title": conversation_title or f"Conversation {len(context_manager.memory['conversations']) + 1}",
        "linked_at": import_time_module().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # Log the linking action
    context_manager.log(f"Linked conversation: {conversation_title or conversation_id}")
    context_manager._save_metadata()
    return True

def import_time_module():
    """Helper function to import time module only when needed"""
    import time
    return time

def get_project_conversations(project_name):
    """
    Get all conversations linked to a project.
    
    Args:
        project_name: Name of the project
    
    Returns:
        List of conversation objects
    """
    context_manager = ProjectContextManager(project_name)
    return context_manager.memory.get("conversations", [])

def update_project_context(project_name, action, **kwargs):
    """
    Update a project's context with actions like adding tasks, logs, or notes
    following Rule #1 (Progressive Enhancement) of the Minerva Master Ruleset.
    
    Args:
        project_name: Name of the project to update
        action: Type of action to perform (add_task, complete_task, add_log, add_note, etc.)
        **kwargs: Various arguments depending on the action
            - task_text: Text of task to add/complete
            - task_priority: Priority of the task (High, Medium, Low)
            - task_dependencies: List of task texts that this task depends on
            - task_deadline: Deadline for the task (ISO format date string)
            - log_text: Text of log entry to add
            - note_text: Text of note to add
            - task_index: Index of task to modify (for priority/dependency/deadline updates)
            
    Returns:
        Updated context dictionary
    """
    context_manager = ProjectContextManager(project_name)
    
    if action == "add_task":
        # Add a new task with optional priority, dependencies, deadline
        task_text = kwargs.get("task_text")
        priority = kwargs.get("task_priority")
        dependencies = kwargs.get("task_dependencies")
        deadline = kwargs.get("task_deadline")
        
        if task_text:
            context_manager.add_task(
                task_text, 
                priority=priority,
                dependencies=dependencies,
                deadline=deadline
            )
    
    elif action == "complete_task":
        # Complete a task by text or index
        task_text = kwargs.get("task_text")
        task_index = kwargs.get("task_index")
        
        if task_index is not None:
            context_manager.complete_task(task_index)
        elif task_text:
            # Find the task by text and complete it
            tasks = context_manager.get_tasks()
            for i, task in enumerate(tasks):
                task_content = task["text"] if isinstance(task, dict) else task
                if task_text.lower() in task_content.lower():
                    context_manager.complete_task(i)
                    break
    
    elif action == "update_task_priority":
        # Update a task's priority
        task_index = kwargs.get("task_index")
        priority = kwargs.get("task_priority")
        
        if task_index is not None and priority:
            context_manager.update_task_priority(task_index, priority)
    
    elif action == "add_task_dependency":
        # Add a dependency to a task
        task_index = kwargs.get("task_index")
        dependency = kwargs.get("dependency")
        
        if task_index is not None and dependency:
            context_manager.add_task_dependency(task_index, dependency)
    
    elif action == "set_task_deadline":
        # Set a deadline for a task
        task_index = kwargs.get("task_index")
        deadline = kwargs.get("deadline")
        
        if task_index is not None and deadline:
            context_manager.set_task_deadline(task_index, deadline)
    
    elif action == "add_log":
        # Add a log entry
        log_text = kwargs.get("log_text")
        if log_text:
            context_manager.log(log_text)
    
    elif action == "add_note":
        # Add a note
        note_text = kwargs.get("note_text")
        if note_text:
            context_manager.add_note(note_text)
    
    # Return updated context
    return {
        "objectives": context_manager.memory["objectives"],
        "task_queue": context_manager.memory["task_queue"],
        "logs": context_manager.memory["logs"],
        "notes": context_manager.memory["notes"]
    }
