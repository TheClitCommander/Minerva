"""
Task Reasoner Module for Minerva

This module provides intelligent task analysis and suggestions based on:
- Task priority
- Deadlines
- Dependencies
- Current project context

It helps Minerva recommend the next best action for users.
"""

from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

# Constants for scoring
PRIORITY_SCORES = {
    "High": 5,
    "Medium": 3, 
    "Low": 1
}

DEADLINE_URGENCY = {
    "overdue": 6,     # Past deadline
    "today": 5,       # Due today
    "tomorrow": 4,    # Due tomorrow
    "this_week": 3,   # Due within 7 days
    "next_week": 2,   # Due within 14 days
    "future": 1       # Due beyond 14 days
}

# Maximum recursive depth for dependency checking
MAX_DEPENDENCY_DEPTH = 5

def get_task_text(task: Union[str, Dict]) -> str:
    """Extract the text content from a task (handles both string and object formats)"""
    if isinstance(task, str):
        return task
    elif isinstance(task, dict):
        return task.get("text", task.get("task", "Unknown task"))
    return "Unknown task"

def is_task_completed(task: Union[str, Dict]) -> bool:
    """Check if a task is completed (handles both string and object formats)"""
    if isinstance(task, dict):
        return task.get("completed", False) or task.get("done", False)
    return False

def calculate_deadline_score(task: Dict, now: datetime) -> Tuple[int, str]:
    """Calculate a score and reason based on task deadline proximity"""
    if "deadline" not in task:
        return 0, ""
    
    try:
        # Handle both ISO format and other string formats
        deadline_str = task["deadline"]
        if isinstance(deadline_str, str):
            # Try ISO format first
            try:
                deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            except ValueError:
                # Fall back to parsing common date formats
                try:
                    import dateutil.parser
                    deadline = dateutil.parser.parse(deadline_str)
                except (ImportError, ValueError):
                    # If all else fails, try a basic format
                    deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
        else:
            # Handle if deadline is already a datetime
            deadline = deadline_str if isinstance(deadline_str, datetime) else now
            
        # Calculate days until deadline
        days_left = (deadline - now).days
        
        # Determine urgency level and score
        if days_left < 0:
            return DEADLINE_URGENCY["overdue"], "Overdue by {} days!".format(abs(days_left))
        elif days_left == 0:
            return DEADLINE_URGENCY["today"], "Due today!"
        elif days_left == 1:
            return DEADLINE_URGENCY["tomorrow"], "Due tomorrow"
        elif days_left <= 7:
            return DEADLINE_URGENCY["this_week"], "Due in {} days".format(days_left)
        elif days_left <= 14:
            return DEADLINE_URGENCY["next_week"], "Due in {} days".format(days_left)
        else:
            return DEADLINE_URGENCY["future"], "Due in {} days".format(days_left)
    
    except Exception as e:
        logger.warning(f"Error parsing deadline: {e}")
        return 0, ""

def check_dependencies(task: Dict, all_tasks: List[Dict], depth: int = 0) -> Tuple[bool, List[str]]:
    """
    Check if a task's dependencies are completed
    Returns: (is_blocked, list_of_blocking_tasks)
    """
    if depth > MAX_DEPENDENCY_DEPTH:
        # Prevent infinite recursion for circular dependencies
        return True, ["Circular dependency detected"]
    
    # If no dependencies, task is not blocked
    if not task.get("dependencies"):
        return False, []
    
    blocking_tasks = []
    
    # Check each dependency
    for dep_name in task.get("dependencies", []):
        # Find the dependency task
        dep_task = None
        for t in all_tasks:
            task_text = get_task_text(t)
            if task_text == dep_name:
                dep_task = t
                break
        
        # If dependency not found or not completed, this task is blocked
        if dep_task is None:
            blocking_tasks.append(f"{dep_name} (not found)")
        elif not is_task_completed(dep_task):
            blocking_tasks.append(dep_name)
            # Recursively check if the dependency itself is blocked
            is_blocked, blocking_deps = check_dependencies(dep_task, all_tasks, depth + 1)
            if is_blocked and blocking_deps:
                # Only add unique dependencies
                for bd in blocking_deps:
                    if bd not in blocking_tasks:
                        blocking_tasks.append(f"{dep_name} → {bd}")
    
    return len(blocking_tasks) > 0, blocking_tasks

def get_task_dependency_chain(task_text: str, all_tasks: List[Dict], depth: int = 0) -> List[str]:
    """Get the full dependency chain for a task, for visualization purposes"""
    if depth > MAX_DEPENDENCY_DEPTH:
        return ["..."]  # Prevent infinite recursion
    
    # Find the task
    task = None
    for t in all_tasks:
        if get_task_text(t) == task_text:
            task = t
            break
            
    if not task or not isinstance(task, dict) or not task.get("dependencies"):
        return []
        
    chain = []
    for dep_name in task.get("dependencies", []):
        chain.append(dep_name)
        # Recursively get dependencies of dependencies
        dep_chain = get_task_dependency_chain(dep_name, all_tasks, depth + 1)
        for dc in dep_chain:
            chain.append(f"{dep_name} → {dc}")
            
    return chain

def analyze_task(task: Dict, all_tasks: List[Dict], now: datetime) -> Dict:
    """
    Analyze a single task and return its score and reasons.
    Higher score = higher priority to work on now.
    """
    if not task:
        return None
        
    # Initialize score and reasons
    score = 0
    reasons = []
    
    # Check if task is already completed
    if is_task_completed(task):
        return {
            "task": task,
            "score": -100,  # Lowest priority
            "reasons": ["Already completed"],
            "is_blocked": False,
            "blocking_tasks": [],
            "suggested": False
        }
    
    # 1. Priority score
    priority = task.get("priority", "Medium")
    priority_score = PRIORITY_SCORES.get(priority, PRIORITY_SCORES["Medium"])
    score += priority_score
    reasons.append(f"{priority} priority")
    
    # 2. Deadline score
    deadline_score, deadline_reason = calculate_deadline_score(task, now)
    if deadline_reason:
        score += deadline_score
        reasons.append(deadline_reason)
    
    # 3. Dependency check (penalty if blocked)
    is_blocked, blocking_tasks = check_dependencies(task, all_tasks)
    if is_blocked:
        dependency_penalty = -5  # Significant penalty for blocked tasks
        score += dependency_penalty
        if len(blocking_tasks) == 1:
            reasons.append(f"Blocked by: {blocking_tasks[0]}")
        else:
            reasons.append(f"Blocked by {len(blocking_tasks)} tasks")
    else:
        # Bonus for being ready to start
        score += 2
        reasons.append("Ready to start")
    
    return {
        "task": task,
        "score": score,
        "reasons": reasons,
        "is_blocked": is_blocked,
        "blocking_tasks": blocking_tasks,
        "suggested": False  # Will be set to True for the top suggestion
    }

def suggest_next_tasks(project_context: Dict, limit: int = 3) -> List[Dict]:
    """
    Analyze tasks and return suggested next actions in order of priority.
    Returns a list of task suggestions with scores and reasons.
    
    Args:
        project_context: The project context containing tasks
        limit: Maximum number of suggestions to return
        
    Returns:
        List of task suggestions with scores and reasoning
    """
    if not project_context or not isinstance(project_context, dict):
        logger.error("Invalid project context provided")
        return []
    
    # Get tasks from context (handle both memory format and direct format)
    tasks = []
    if "memory" in project_context and "task_queue" in project_context["memory"]:
        tasks = project_context["memory"]["task_queue"]
    elif "task_queue" in project_context:
        tasks = project_context["task_queue"]
    
    if not tasks:
        logger.info("No tasks found in project context")
        return []
    
    now = datetime.now()
    analyzed_tasks = []
    
    # Analyze each task
    for task in tasks:
        # Skip if not a dict or string
        if not isinstance(task, (dict, str)):
            continue
            
        # Convert string tasks to dict format for consistency
        if isinstance(task, str):
            task = {"text": task}
            
        analysis = analyze_task(task, tasks, now)
        if analysis:
            analyzed_tasks.append(analysis)
    
    # Sort by score (highest first)
    sorted_tasks = sorted(analyzed_tasks, key=lambda x: x["score"], reverse=True)
    
    # Mark the top suggestion
    if sorted_tasks:
        sorted_tasks[0]["suggested"] = True
    
    # Return the top N suggestions
    return sorted_tasks[:limit]

def get_critical_path(project_context: Dict) -> List[Dict]:
    """
    Identify the critical path of tasks based on dependencies and deadlines.
    The critical path is the sequence of dependent tasks with the least slack.
    
    Returns:
        List of tasks forming the critical path
    """
    # Implementation for critical path algorithm would go here
    # This is a placeholder for future enhancement
    pass

def reprioritize_tasks(project_context: Dict) -> Dict:
    """
    Suggest an optimized order for tasks based on priority, deadlines, and dependencies.
    
    Returns:
        Updated project context with reordered tasks
    """
    # Implementation for task reprioritization would go here
    # This is a placeholder for future enhancement
    pass

def generate_task_suggestion_text(suggestion: Dict) -> str:
    """
    Generate a natural language suggestion for the next task.
    
    Args:
        suggestion: The top task suggestion
        
    Returns:
        Human-readable suggestion with reasoning
    """
    if not suggestion:
        return "There are no tasks to suggest at this time."
        
    task = suggestion["task"]
    task_text = get_task_text(task)
    reasons = suggestion["reasons"]
    
    # Build the suggestion text
    suggestion_text = f"I suggest working on: \"{task_text}\""
    
    if reasons:
        reasoning = ", ".join(reasons)
        suggestion_text += f" because: {reasoning}"
        
    # Add blocking information if relevant
    if suggestion["is_blocked"] and suggestion["blocking_tasks"]:
        blocking = ", ".join(suggestion["blocking_tasks"][:3])
        if len(suggestion["blocking_tasks"]) > 3:
            blocking += f" and {len(suggestion['blocking_tasks']) - 3} more"
        suggestion_text += f". Note: This task is blocked by: {blocking}"
        
    return suggestion_text
