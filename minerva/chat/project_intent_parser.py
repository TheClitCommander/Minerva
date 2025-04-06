#!/usr/bin/env python3
"""
Project Intent Parser

Detects project-related intents in user messages, such as:
- Adding tasks
- Marking tasks as complete
- Adding logs
- Creating notes

This module uses heuristic-based natural language processing
to identify potential actionable items in user messages.
"""

import re
import logging
from typing import Dict, Optional, Any, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Intent types
INTENT_ADD_TASK = "add_task"
INTENT_MARK_TASK_DONE = "mark_task_done"
INTENT_ADD_LOG = "add_log"
INTENT_ADD_NOTE = "add_note"
INTENT_SUGGEST_TASKS = "suggest_tasks"

# Pattern collections for different intent types
TASK_PATTERNS = [
    r"(?:we|i)(?:'d| would)? (?:should|need to|have to) (.*)",
    r"(?:we|i)(?:'d| would)? (?:must|ought to) (.*)",
    r"let(?:'s| us) (.*)",
    r"add(?:ing)? (?:a )?task(?::| to)? (.*)",
    r"(?:we|i) need to (.*)",
    r"(?:we|i) should (.*)",
    r"(?:we|i) have to (.*)",
    r"(?:we|i) must (.*)",
    r"don'?t forget to (.*)",
    r"remind me to (.*)",
    r"consider(?:ing)? (.*)",
    r"implement(?:ing)? (.*)",
    r"build(?:ing)? (.*)",
    r"create (?:a|the) (.*)",
    r"develop(?:ing)? (?:a|the) (.*)",
    r"add (?:a|the) (.*)"
]

TASK_COMPLETION_PATTERNS = [
    r"(?:we|i) (?:just )?(?:finished|completed) (.*)",
    r"(?:we|i) (?:have|'ve) (?:finished|completed) (.*)",
    r"(?:we|i) (?:are|'re) done (?:with)? (.*)",
    r"(?:we|i) (?:have|'ve) done (.*)",
    r"(?:we|i) (?:did|made|got) (.*) done",
    r"mark(?:ing)? (?:the )?task(?::| as)? (.*) (?:as )?(?:done|complete)",
    r"(?:we|i) marked (.*) as (?:done|complete)",
    r"(?:the )?task (.*) is (?:now )?(?:done|complete)",
    r"(?:we|i)'ve ticked off (.*)"
]

LOG_PATTERNS = [
    r"(?:we|i) (?:just|recently) (.*)",
    r"update(?:d)?(?: the)? log(?::| with)? (.*)",
    r"log(?:ged)? (?:that|the|this)? (.*)",
    r"(?:we|i) (?:had|have|just had) (?:a|the) (.*meeting.*)",
    r"(?:we|i) (?:had|have|just had) (?:a|the) (.*call.*)",
    r"(?:we|i) met with (.*)",
    r"(?:we|i) spoke (?:with|to) (.*)",
    r"(?:we|i) (?:were|are) (.*)"
]

NOTE_PATTERNS = [
    r"note(?:d)? (?:that|down|this)(?::)? (.*)",
    r"remember(?:ing)? (?:that|to|about)(?::)? (.*)",
    r"keep in mind (?:that|to|about)(?::)? (.*)",
    r"(?:just|important|quick) note(?::)? (.*)",
    r"write(?:ing)? (?:down|this)(?::)? (.*)",
    r"(?:we|i) (?:should|need to|must) remember (?:that|to|about) (.*)",
    r"don'?t forget (?:that|about) (.*)"
]

# Pattern for task suggestions
TASK_SUGGESTION_PATTERNS = [
    r"what (?:should|can) (?:we|i) (?:do|work on) next",
    r"what'?s (?:my|our) next task",
    r"which task (?:should|could) (?:we|i) (?:do|work on|focus on) next",
    r"what (?:should|can) (?:we|i) (?:focus|concentrate) on",
    r"suggest (?:a|some) task(?:s)?(?: to work on)?",
    r"what'?s the (?:highest|most) priority task",
    r"what (?:task )?(?:needs|should) (?:to be|be) (?:done|completed) (?:first|next)",
    r"(?:give|provide) me (?:a|some) task suggestion(?:s)?",
    r"what'?s (?:left|remaining) (?:to do|on the list)",
    r"help me prioritize (?:my|the) tasks"
]

# Stop words that suggest the sentence is not an actionable item
STOP_PHRASES = [
    "can you help",
    "could you",
    "would you",
    "do you know",
    "is it possible",
    "how can I",
    "how do I",
    "how do we",
    "how to",
    "what is",
    "tell me about",
    "explain",
    "I'm wondering",
    "I wonder",
    "do we have"
]

def parse_project_intent(message: str) -> Dict[str, Any]:
    """
    Parse a message to detect project-related intents.
    
    Args:
        message: The user message to parse
        
    Returns:
        Dict containing detected intent type and content, e.g.
        {"action": "add_task", "content": "implement user authentication"}
        or {"action": None, "content": None} if no intent is detected
    """
    # Default response (no intent detected)
    result = {
        "action": None,
        "content": None
    }
    
    # Normalize the message for better matching
    normalized_message = message.lower().strip()
    
    # Check for stop phrases that indicate this isn't an actionable message
    for phrase in STOP_PHRASES:
        if phrase in normalized_message:
            logger.debug(f"Found stop phrase '{phrase}' in message, skipping intent detection")
            return result
    
    # First check for task completion intent (higher priority)
    task_completion_match = check_patterns(normalized_message, TASK_COMPLETION_PATTERNS)
    if task_completion_match:
        return {
            "action": INTENT_MARK_TASK_DONE,
            "content": task_completion_match
        }
    
    # Check for task creation intent
    task_match = check_patterns(normalized_message, TASK_PATTERNS)
    if task_match:
        return {
            "action": INTENT_ADD_TASK,
            "content": task_match
        }
    
    # Check for log entry intent
    log_match = check_patterns(normalized_message, LOG_PATTERNS)
    if log_match:
        return {
            "action": INTENT_ADD_LOG,
            "content": log_match
        }
    
    # Check for note creation intent
    note_match = check_patterns(normalized_message, NOTE_PATTERNS)
    if note_match:
        return {
            "action": INTENT_ADD_NOTE,
            "content": note_match
        }
    
    # Check for task suggestion request
    for pattern in TASK_SUGGESTION_PATTERNS:
        if re.search(pattern, normalized_message, re.IGNORECASE):
            return {
                "action": INTENT_SUGGEST_TASKS,
                "content": "task suggestions"
            }
    
    return result

def check_patterns(message: str, pattern_list: List[str]) -> Optional[str]:
    """
    Check if a message matches any pattern in a list.
    
    Args:
        message: The message to check
        pattern_list: List of regex patterns to match against
        
    Returns:
        Extracted content if a match is found, None otherwise
    """
    for pattern in pattern_list:
        matches = re.search(pattern, message, re.IGNORECASE)
        if matches:
            content = matches.group(1).strip()
            
            # Skip if content is too short (likely a false positive)
            if len(content) < 3:
                continue
                
            logger.debug(f"Pattern match: '{pattern}' -> '{content}'")
            return content
    
    return None

def extract_task_context(message: str, tasks: List[Dict[str, Any]]) -> Optional[Tuple[int, str]]:
    """
    Try to identify which existing task the user is referring to.
    
    Args:
        message: The user message
        tasks: List of existing tasks
        
    Returns:
        Tuple of (task_index, task_text) if a match is found, None otherwise
    """
    normalized_message = message.lower()
    
    # Loop through each task and check if it's mentioned in the message
    for i, task in enumerate(tasks):
        task_text = task.get('text', task) if isinstance(task, dict) else task
        task_text = str(task_text).lower()
        
        # Check for exact match
        if task_text in normalized_message:
            return (i, task_text)
        
        # Try to find a partial match (at least 60% of words match)
        task_words = set(re.findall(r'\b\w+\b', task_text))
        message_words = set(re.findall(r'\b\w+\b', normalized_message))
        
        if task_words and len(task_words.intersection(message_words)) / len(task_words) >= 0.6:
            return (i, task_text)
    
    return None

def generate_action_suggestion(intent: Dict[str, Any], project_name: str = None) -> Dict[str, Any]:
    """
    Generate a user-friendly suggestion based on the detected intent.
    
    Args:
        intent: The detected intent dictionary
        project_name: Optional name of the current project
        
    Returns:
        Dict with suggestion text and action details
    """
    if not intent or not intent.get("action") or not intent.get("content"):
        return None
    
    action = intent["action"]
    content = intent["content"]
    
    project_context = f" to the '{project_name}' project" if project_name else ""
    
    if action == INTENT_ADD_TASK:
        return {
            "suggestion": f"Would you like me to add '{content}' as a task{project_context}?",
            "action_type": "add_task",
            "content": content,
            "project_name": project_name
        }
    elif action == INTENT_MARK_TASK_DONE:
        return {
            "suggestion": f"Would you like me to mark the task '{content}' as complete{project_context}?",
            "action_type": "mark_task_done",
            "content": content,
            "project_name": project_name
        }
    elif action == INTENT_ADD_LOG:
        return {
            "suggestion": f"Would you like me to add '{content}' to the activity log{project_context}?",
            "action_type": "add_log",
            "content": content,
            "project_name": project_name
        }
    elif action == INTENT_ADD_NOTE:
        return {
            "suggestion": f"Would you like me to add a note about '{content}'{project_context}?",
            "action_type": "add_note",
            "content": content,
            "project_name": project_name
        }
    elif action == INTENT_SUGGEST_TASKS:
        return {
            "suggestion": f"I can suggest tasks for you to work on{project_context} based on priorities and deadlines.",
            "action_type": "suggest_tasks",
            "content": content,
            "project_name": project_name
        }
    
    return None

# Quick test function 
def test_intent_parser(messages: List[str]) -> None:
    """Test the intent parser with a list of sample messages"""
    for message in messages:
        intent = parse_project_intent(message)
        if intent["action"]:
            suggestion = generate_action_suggestion(intent, "Test Project")
            print(f"Message: '{message}'")
            print(f"Detected intent: {intent['action']}")
            print(f"Content: '{intent['content']}'")
            print(f"Suggestion: '{suggestion['suggestion']}'")
            print("-" * 50)
        else:
            print(f"No intent detected in: '{message}'")

if __name__ == "__main__":
    # Run some tests
    test_messages = [
        "We should implement user authentication for the app",
        "I need to remember to call the client on Monday",
        "Don't forget to update the database schema",
        "We just finished the login page design",
        "Note that the API keys need to be rotated monthly",
        "We had a meeting with the design team yesterday",
        "What do you think about adding push notifications?",
        "Can you help me with the CSS?",
        "Mark the task design homepage as complete",
        "Let's create a backup system"
    ]
    
    test_intent_parser(test_messages)
