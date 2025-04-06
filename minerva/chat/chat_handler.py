#!/usr/bin/env python3
"""
Project-Aware Chat Handler for Minerva

This module handles the injection of project context into conversations,
making Minerva responses aware of project objectives, tasks, logs, and notes.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

# Import project context functionality
from minerva.runtime.project_runtime import load_project_context, get_project_conversations
from minerva.core.project_context import ProjectContextManager

# Import intent parser
from minerva.chat.project_intent_parser import parse_project_intent, generate_action_suggestion, INTENT_SUGGEST_TASKS

# Import the task reasoner for suggestions
from minerva.ai.task_reasoner import suggest_next_tasks

def get_active_project_for_user(user_id: str = None, session_data: Dict = None) -> Optional[str]:
    """
    Determine the active project for a user based on session data or recent activity.
    
    Args:
        user_id: The user's unique identifier
        session_data: Optional session data that might contain project info
        
    Returns:
        str: Project name or None if no active project
    """
    # Priority 1: Check session data for explicitly selected project
    if session_data and "active_project" in session_data:
        logger.info(f"Found active project in session: {session_data['active_project']}")
        return session_data["active_project"]
    
    # Priority 2: Check if user has a default project set
    # TODO: Implement user preferences storage and retrieval
    
    # Priority 3: Return the user_id as the default project if all else fails
    # This assumes users might have personal projects named after their ID
    if user_id:
        logger.info(f"Using user_id as default project: {user_id}")
        return user_id
    
    # No active project found
    return None

def format_context(project_name: str, context_data: Dict) -> str:
    """
    Format project context data into a readable, helpful format for AI prompts.
    
    Args:
        project_name: The name of the project
        context_data: Dict containing project context (objectives, task_queue, logs, notes)
        
    Returns:
        str: Formatted context text for inclusion in prompts
    """
    if not context_data:
        return ""
    
    # Format objectives as a bullet point list
    objectives = context_data.get("objectives", [])
    objectives_text = ""
    if objectives:
        objectives_text = "Project Objectives:\n" + "\n".join([f"- {obj}" for obj in objectives])
    
    # Format tasks as a checkbox list with completion status
    tasks = context_data.get("task_queue", [])
    tasks_text = ""
    if tasks:
        tasks_text = "Current Tasks:\n"
        for task in tasks:
            if isinstance(task, dict):
                # Handle task objects with completion status
                done = task.get("done", False) or task.get("completed", False)
                task_text = task.get("text", task.get("task", "Unknown task"))
                checkbox = "✅" if done else "☐"
                tasks_text += f"{checkbox} {task_text}\n"
            else:
                # Handle simple string tasks
                tasks_text += f"☐ {task}\n"
    
    # Format most recent logs (limited to last 3)
    logs = context_data.get("logs", [])
    logs_text = ""
    if logs:
        # Limit to last 3 logs for brevity
        recent_logs = logs[-3:]
        logs_text = "Recent Logs:\n" + "\n".join([f"- {log}" for log in recent_logs])
    
    # Format notes
    notes = context_data.get("notes", [])
    notes_text = ""
    if notes:
        notes_text = "Notes:\n" + "\n".join([f"- {note}" for note in notes])
    
    # Assemble the complete context section
    context_sections = []
    context_sections.append(f"You are currently working on the project: **{project_name}**\n")
    
    if objectives_text:
        context_sections.append(objectives_text)
    
    if tasks_text:
        context_sections.append(tasks_text)
    
    if logs_text:
        context_sections.append(logs_text)
    
    if notes_text:
        context_sections.append(notes_text)
    
    context_sections.append("\n---\n\nNow continue the conversation as Minerva with this context in mind.")
    
    # Join all sections with double newlines for readability
    return "\n\n".join(context_sections)

def build_chat_prompt(user_message: str, project_name: str = None) -> Dict:
    """
    Build a project-aware chat prompt by injecting project context.
    
    Args:
        user_message: The user's message
        project_name: Optional project name (if None, no context is injected)
        
    Returns:
        Dict: Messages ready for the AI model, with context injected
    """
    messages = []
    
    # If we have a project name, inject the context
    if project_name:
        try:
            # Load project context
            context_data = load_project_context(project_name)
            
            # Format the context into a system message
            context_text = format_context(project_name, context_data)
            
            if context_text:
                # Add as system message
                messages.append({
                    "role": "system", 
                    "content": context_text
                })
                logger.info(f"Injected project context for '{project_name}' into prompt")
            else:
                # Fallback system message if context couldn't be formatted
                messages.append({
                    "role": "system",
                    "content": f"You are Minerva, an AI assistant working on the project: {project_name}."
                })
        except Exception as e:
            logger.error(f"Error injecting project context: {str(e)}")
            # Fallback system message in case of error
            messages.append({
                "role": "system",
                "content": "You are Minerva, an AI assistant."
            })
    else:
        # Default system message when no project is active
        messages.append({
            "role": "system",
            "content": "You are Minerva, an AI assistant."
        })
    
    # Add the user message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    return messages

def inject_project_context_into_prompt(prompt: Dict, project_name: str = None) -> Dict:
    """
    Inject project context into an existing prompt structure.
    
    Args:
        prompt: The existing prompt structure
        project_name: Optional project name
        
    Returns:
        Dict: Updated prompt with project context injected
    """
    if not project_name:
        return prompt
    
    try:
        # Load project context
        context_data = load_project_context(project_name)
        
        # Format the context
        context_text = format_context(project_name, context_data)
        
        if not context_text:
            return prompt
        
        # Create a copy of the prompt to avoid modifying the original
        updated_prompt = prompt.copy()
        
        # Check if the prompt has a messages key (for chat models)
        if "messages" in updated_prompt:
            # Check if there's already a system message
            has_system = any(msg.get("role") == "system" for msg in updated_prompt["messages"])
            
            if has_system:
                # Update the existing system message
                for i, msg in enumerate(updated_prompt["messages"]):
                    if msg.get("role") == "system":
                        # Prepend our context to the existing system message
                        updated_prompt["messages"][i]["content"] = context_text + "\n\n" + msg["content"]
                        break
            else:
                # Add a new system message at the beginning
                updated_prompt["messages"].insert(0, {
                    "role": "system",
                    "content": context_text
                })
        else:
            # For non-chat models, add context to the prompt string
            if isinstance(updated_prompt, str):
                updated_prompt = context_text + "\n\n" + updated_prompt
            elif "prompt" in updated_prompt:
                updated_prompt["prompt"] = context_text + "\n\n" + updated_prompt["prompt"]
        
        return updated_prompt
    
    except Exception as e:
        logger.error(f"Error injecting context into prompt: {str(e)}")
        return prompt  # Return original prompt if there's an error

def process_message_with_project_context(message: str, user_id: str = None, 
                                        session_data: Dict = None, **kwargs) -> Dict:
    """
    Process a user message with project context awareness.
    This function should be called before passing the message to the AI models.
    
    Args:
        message: The user's message
        user_id: The user's ID for tracking
        session_data: Optional session data containing project info
        
    Returns:
        Dict: Enhanced message data with project context
    """
    # Step 1: Detect the active project
    project_name = get_active_project_for_user(user_id, session_data)
    
    # Step 2: Build project-aware messages
    messages = build_chat_prompt(message, project_name)
    
    # Step 3: Return enhanced data
    return {
        "original_message": message,
        "enhanced_messages": messages,
        "project_name": project_name,
        "has_project_context": project_name is not None,
        **kwargs
    }

def extract_possible_project_from_message(message: str) -> Optional[str]:
    """
    Try to extract a project name from a message for auto-linking.
    
    Args:
        message: The user's message
        
    Returns:
        str: Extracted project name or None
    """
    # This is a simple implementation that can be enhanced with more NLP later
    # Current approach: Look for phrases like "for project X" or "in project X"
    
    import re
    
    # Pattern to match common project reference phrases
    patterns = [
        r"for\s+(?:the\s+)?project\s+['\"]?([a-zA-Z0-9_-]+)['\"]?",
        r"in\s+(?:the\s+)?project\s+['\"]?([a-zA-Z0-9_-]+)['\"]?",
        r"on\s+(?:the\s+)?project\s+['\"]?([a-zA-Z0-9_-]+)['\"]?",
        r"project\s+['\"]?([a-zA-Z0-9_-]+)['\"]?\s+context",
    ]
    
    for pattern in patterns:
        matches = re.search(pattern, message, re.IGNORECASE)
        if matches:
            return matches.group(1)
    
    return None

def detect_potential_project(message: str) -> Optional[str]:
    """
    Detect a potential project reference in a message but don't link automatically.
    This respects the user's preference for manual project creation.
    
    Args:
        message: The user's message
        
    Returns:
        str: Detected project name or None if none found
    """
    # Try to extract project name from the message
    project_name = extract_possible_project_from_message(message)
    
    if not project_name:
        return None
    
    try:
        # Check if the project exists
        ProjectContextManager(project_name)
        logger.info(f"Detected potential project reference: {project_name}")
        return project_name
    except Exception as e:
        logger.debug(f"Project detection found name, but project doesn't exist: {str(e)}")
    
    return None

def detect_project_intent(message: str, project_name: str = None) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    Detect project-related intent in a user message and generate appropriate suggestions.
    
    Args:
        message: The user's message
        project_name: Optional active project name
        
    Returns:
        Tuple containing:
            - Parsed intent dict with 'action' and 'content' keys
            - Optional suggestion dict for user confirmation
    """
    # Parse the message for project-related intent
    intent = parse_project_intent(message)
    
    # If no actionable intent was found or no project is active, return early
    if not intent["action"] or not project_name:
        return intent, None
    
    # Generate a user-friendly suggestion based on the intent
    suggestion = generate_action_suggestion(intent, project_name)
    
    logger.info(f"Detected project intent: {intent['action']} - '{intent['content']}'")
    
    return intent, suggestion

def get_task_suggestions(project_name: str) -> Dict:
    """
    Get task suggestions for a project using the task reasoner.
    
    Args:
        project_name: The name of the project
        
    Returns:
        Dict containing task suggestions and explanation
    """
    try:
        # Load the project context
        project_manager = ProjectContextManager(project_name)
        project_context = project_manager.load_context()
        
        if not project_context or not project_context.get("task_queue"):
            return {
                "success": False,
                "message": "No tasks found in the project.",
                "suggestions": []
            }
        
        # Get suggestions using our task reasoner
        suggestions = suggest_next_tasks(project_context)
        
        # Format the suggestions for the chat
        formatted_suggestions = []
        for suggestion in suggestions:
            task_text = suggestion.get("task", "Unknown task")
            reasoning = suggestion.get("reasoning", "")
            formatted_suggestions.append({
                "task": task_text,
                "reasoning": reasoning,
                "score": suggestion.get("score", 0),
                "index": suggestion.get("index", -1)
            })
        
        return {
            "success": True,
            "message": "Here are your suggested tasks:",
            "suggestions": formatted_suggestions
        }
    except Exception as e:
        logger.error(f"Error getting task suggestions: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting task suggestions: {str(e)}",
            "suggestions": []
        }

def process_message_with_intent_detection(message: str, user_id: str = None, 
                                         session_data: Dict = None, **kwargs) -> Dict:
    """
    Process a user message with both project context and intent detection.
    
    Args:
        message: The user's message
        user_id: The user's ID for tracking
        session_data: Optional session data containing project info
        
    Returns:
        Dict: Enhanced message data with project context and detected intents
    """
    # Step 1: Process with project context
    enhanced_data = process_message_with_project_context(message, user_id, session_data, **kwargs)
    
    # Step 2: Detect project-related intents if a project is active
    project_name = enhanced_data.get("project_name")
    intent, suggestion = detect_project_intent(message, project_name)
    
    # Step 3: Handle task suggestion intent specially
    if intent.get("action") == INTENT_SUGGEST_TASKS and project_name:
        task_suggestions = get_task_suggestions(project_name)
        enhanced_data["task_suggestions"] = task_suggestions
    
    # Step 4: Add intent data to the enhanced message
    enhanced_data["detected_intent"] = intent
    enhanced_data["intent_suggestion"] = suggestion
    
    return enhanced_data

# Simple test for the module
if __name__ == "__main__":
    # Test project context injection
    test_message = "Minerva, help me write a Stripe webhook for user signups"
    test_project = "OptionLingo"
    
    # Process message with context
    enhanced_data = process_message_with_project_context(
        message=test_message,
        user_id="test_user",
        session_data={"active_project": test_project}
    )
    
    print("\n===== Enhanced Message with Project Context =====\n")
    for msg in enhanced_data["enhanced_messages"]:
        print(f"Role: {msg['role']}")
        print(f"Content:\n{msg['content']}\n")
    
    print(f"Project Name: {enhanced_data['project_name']}")
    print(f"Has Context: {enhanced_data['has_project_context']}")
    
    # Test project intent detection
    print("\n===== Testing Project Intent Detection =====\n")
    
    intent_test_messages = [
        "We should implement user authentication for the app",
        "I need to remember to call the client on Monday",
        "Don't forget to update the database schema",
        "We just finished the login page design",
        "Let's add a dark mode option to the app",
        "What should I work on next?",
        "What's the highest priority task?",
        "Suggest some tasks for me to work on"
    ]
    
    for test_msg in intent_test_messages:
        print(f"\nMessage: '{test_msg}'")
        intent_data = process_message_with_intent_detection(
            message=test_msg,
            user_id="test_user",
            session_data={"active_project": test_project}
        )
        
        intent = intent_data.get("detected_intent", {})
        suggestion = intent_data.get("intent_suggestion", {})
        
        if intent.get("action"):
            print(f"Detected intent: {intent['action']}")
            print(f"Content: '{intent['content']}'")
            
            if suggestion:
                print(f"Suggestion: '{suggestion['suggestion']}'")
                
            # Show task suggestions if available
            if intent.get("action") == INTENT_SUGGEST_TASKS and "task_suggestions" in intent_data:
                task_suggs = intent_data["task_suggestions"]
                print(f"\nTask Suggestions: {task_suggs['message']}")
                for i, sugg in enumerate(task_suggs.get("suggestions", [])):
                    print(f"{i+1}. {sugg['task']} - {sugg['reasoning']}")
        else:
            print("No intent detected.")
