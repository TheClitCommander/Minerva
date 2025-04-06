# project_api.py
"""API endpoints for project management and project context"""

import os
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging
from minerva.runtime import project_runtime as runtime
from minerva.ai import task_reasoner
from minerva.chat.chat_handler import detect_potential_project

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for project API
project_api = Blueprint('project_api', __name__)

# ----- Project Context API Routes -----

@project_api.route('/api/projects/detect', methods=['POST'])
def detect_project_reference():
    """Detect potential project references in a message"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Missing message data"}), 400
            
        # Detect potential project reference
        message = data['message']
        detected_project = detect_potential_project(message)
        
        return jsonify({
            "success": True, 
            "detected_project": detected_project,
            "has_reference": detected_project is not None
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_api.route('/api/projects/<project_id>/tasks/<int:task_index>/toggle', methods=['PUT'])
def toggle_task_status(project_id, task_index):
    """Toggle the completion status of a task"""
    try:
        # Load project context
        project_context = runtime.load_project_context(project_id)
        
        if not project_context or 'task_queue' not in project_context.memory:
            return jsonify({'success': False, 'error': 'No task queue found for this project'}), 404
        
        tasks = project_context.memory['task_queue']
        
        # Check if task exists
        if task_index < 0 or task_index >= len(tasks):
            return jsonify({'success': False, 'error': 'Task index out of range'}), 404
        
        # Get the task
        task = tasks[task_index]
        
        # Toggle completion status
        if isinstance(task, dict):
            # Object format
            task['completed'] = not (task.get('completed', False) or task.get('done', False))
            # For backward compatibility
            task['done'] = task['completed']
        else:
            # Convert string to object
            tasks[task_index] = {
                'text': task,
                'completed': True,
                'done': True
            }
        
        # Save updated context
        project_context.save_memory()
        
        return jsonify({
            'success': True,
            'tasks': tasks
        })
        
    except Exception as e:
        print(f"Error toggling task status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@project_api.route('/api/projects/<project_id>/tasks/<int:task_index>', methods=['PUT'])
def update_task(project_id, task_index):
    """Update a specific task's properties"""
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        # Load project context
        project_context = runtime.load_project_context(project_id)
        
        if not project_context or 'task_queue' not in project_context.memory:
            return jsonify({'success': False, 'error': 'No task queue found for this project'}), 404
        
        tasks = project_context.memory['task_queue']
        
        # Check if task exists
        if task_index < 0 or task_index >= len(tasks):
            return jsonify({'success': False, 'error': 'Task index out of range'}), 404
        
        # Get the task
        task = tasks[task_index]
        
        # Convert to object if it's a string
        if not isinstance(task, dict):
            task = {
                'text': task
            }
            tasks[task_index] = task
        
        # Update task properties
        if 'priority' in data:
            task['priority'] = data['priority']
            
        if 'deadline' in data:
            task['deadline'] = data['deadline']
            
        if 'dependencies' in data:
            task['dependencies'] = data['dependencies']
            
        if 'completed' in data:
            task['completed'] = data['completed']
            task['done'] = data['completed']  # For backward compatibility
            
        if 'text' in data:
            task['text'] = data['text']
        
        # Save updated context
        project_context.save_memory()
        
        return jsonify({
            'success': True,
            'tasks': tasks
        })
        
    except Exception as e:
        print(f"Error updating task: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@project_api.route('/api/projects/<project_id>/context', methods=['GET'])
def get_project_context(project_id):
    """Get a project's context (objectives, tasks, etc.)"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            return jsonify({"error": "Invalid project ID"}), 400
            
        # Load project context
        context = load_project_context(project_id)
        if not context:
            return jsonify({"error": "Project not found"}), 404
            
        return jsonify(context), 200
    except Exception as e:
        logger.error(f"Error getting project context: {str(e)}")
        return jsonify({"error": str(e)}), 500

@project_api.route('/api/projects/<project_id>/context/update', methods=['POST'])
def update_context_item(project_id):
    """Update a project's context by adding or updating items (tasks, logs, notes, etc.)"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            return jsonify({"error": "Invalid project ID"}), 400
            
        # Get request data
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        action_type = data.get('action_type')
        content = data.get('content')
        
        if not action_type:
            return jsonify({"error": "Missing required field: action_type"}), 400
        
        # Initialize with empty updated_context
        updated_context = None
        
        # Process the request based on action_type
        if action_type == "add_task":
            # Check for enhanced task properties
            priority = data.get('priority')
            dependencies = data.get('dependencies')
            deadline = data.get('deadline')
            
            if not content:
                return jsonify({"error": "Missing required field: content for task text"}), 400
                
            updated_context = update_project_context(
                project_id,
                action="add_task",
                task_text=content,
                task_priority=priority,
                task_dependencies=dependencies,
                task_deadline=deadline
            )
            
        elif action_type == "mark_task_done":
            # Find the task that best matches the content
            if not content:
                return jsonify({"error": "Missing required field: content for task text"}), 400
                
            updated_context = update_project_context(
                project_id,
                action="complete_task",
                task_text=content  # Runtime will find the best matching task
            )
            
        elif action_type == "add_log":
            if not content:
                return jsonify({"error": "Missing required field: content for log text"}), 400
                
            updated_context = update_project_context(
                project_id,
                action="add_log",
                log_text=content
            )
            
        elif action_type == "add_note":
            if not content:
                return jsonify({"error": "Missing required field: content for note text"}), 400
                
            updated_context = update_project_context(
                project_id,
                action="add_note",
                note_text=content
            )
            
        elif action_type == "update_task_priority":
            task_index = data.get('task_index')
            priority = data.get('priority')
            
            if task_index is None:
                return jsonify({"error": "Missing required field: task_index"}), 400
            if not priority:
                return jsonify({"error": "Missing required field: priority"}), 400
                
            updated_context = update_project_context(
                project_id,
                action="update_task_priority",
                task_index=int(task_index),
                task_priority=priority
            )
            
        elif action_type == "add_task_dependency":
            task_index = data.get('task_index')
            dependency = data.get('dependency')
            
            if task_index is None:
                return jsonify({"error": "Missing required field: task_index"}), 400
            if not dependency:
                return jsonify({"error": "Missing required field: dependency"}), 400
                
            updated_context = update_project_context(
                project_id,
                action="add_task_dependency",
                task_index=int(task_index),
                dependency=dependency
            )
            
        elif action_type == "set_task_deadline":
            task_index = data.get('task_index')
            deadline = data.get('deadline')
            
            if task_index is None:
                return jsonify({"error": "Missing required field: task_index"}), 400
            if not deadline:
                return jsonify({"error": "Missing required field: deadline"}), 400
                
            updated_context = update_project_context(
                project_id,
                action="set_task_deadline",
                task_index=int(task_index),
                deadline=deadline
            )
            
        else:
            return jsonify({"error": f"Unsupported action type: {action_type}"}), 400
            
        if updated_context:
            return jsonify({
                "success": True,
                "message": f"Updated project context with {action_type}",
                "updated_context": updated_context
            }), 200
        else:
            return jsonify({"error": "Failed to update project context"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_api.route('/api/projects/<project_id>/objectives', methods=['POST'])
def add_project_objective(project_id):
    """Add a new objective to a project"""
    try:
        data = request.json
        if not data or 'task' not in data:
            return jsonify({"error": "Missing task data"}), 400
            
        # Get optional task properties if provided
        task_text = data['task']
        priority = data.get('priority')
        dependencies = data.get('dependencies')
        deadline = data.get('deadline')
        
        # Use update_project_context to add the task with all properties
        updated_context = update_project_context(
            project_id,
            action="add_task",
            task_text=task_text,
            task_priority=priority,
            task_dependencies=dependencies,
            task_deadline=deadline
        )
        
        if updated_context and 'task_queue' in updated_context:
            return jsonify({"success": True, "tasks": updated_context['task_queue']}), 200
        else:
            return jsonify({"error": "Failed to add task"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_api.route('/api/projects/<project_id>/tasks/<int:index>', methods=['PUT'])
def update_project_task(project_id, index):
    """Update an existing task"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing task data"}), 400
            
        # Load current context
        context = load_project_context(project_id)
        
        # Validate index
        if 'task_queue' not in context or index >= len(context['task_queue']):
            return jsonify({"error": "Task not found"}), 404
            
        # Get the existing task
        task = context['task_queue'][index]
        
        # Convert string task to dict if needed
        if isinstance(task, str):
            task = {
                'text': task,
                'created_at': datetime.now().isoformat()
            }
        elif not isinstance(task, dict):
            return jsonify({"error": "Invalid task format"}), 500
            
        # Update task properties if provided
        if 'task' in data:
            task['text'] = data['task']
            
        if 'priority' in data:
            task['priority'] = data['priority']
            
        if 'dependencies' in data:
            task['dependencies'] = data['dependencies']
            
        if 'deadline' in data:
            task['deadline'] = data['deadline']
            
        # Update the task in the context
        context['task_queue'][index] = task
        
        # Save updated context
        save_project_context(project_id, context)
        
        return jsonify({"success": True, "tasks": context['task_queue']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_api.route('/api/projects/<project_id>/tasks/<int:index>/toggle', methods=['PUT'])
def toggle_task_status(project_id, index):
    """Toggle a task's completion status"""
    try:
        # Load current context
        context = load_project_context(project_id)
        
        # Validate index
        if 'task_queue' not in context or index >= len(context['task_queue']):
            return jsonify({"error": "Task not found"}), 404
            
        # Toggle task status
        task = context['task_queue'][index]
        if isinstance(task, dict):
            task['done'] = not task.get('done', False)
        else:
            # Convert string tasks to dict format with toggled status
            context['task_queue'][index] = {
                'text': task,
                'done': True  # Default to marking as done when toggling for the first time
            }
        
        # Save updated context
        save_project_context(project_id, context)
        
        return jsonify({"success": True, "tasks": context['task_queue']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_api.route('/api/projects/<project_id>/tasks/<int:index>', methods=['DELETE'])
def delete_project_task(project_id, index):
    """Delete a task"""
    try:
        # Load current context
        context = load_project_context(project_id)
        
        # Validate index
        if 'task_queue' not in context or index >= len(context['task_queue']):
            return jsonify({"error": "Task not found"}), 404
            
        # Remove task
        context['task_queue'].pop(index)
        
        # Save updated context
        save_project_context(project_id, context)
        
        return jsonify({"success": True, "tasks": context['task_queue']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_api.route('/api/projects/<project_id>/conversations', methods=['GET'])
def get_linked_conversations(project_id):
    """Get all conversations linked to a project"""
    try:
        conversations = get_project_conversations(project_id)
        return jsonify(conversations), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_api.route('/api/projects/<project_id>/conversations/<conversation_id>', methods=['POST'])
def link_conversation(project_id, conversation_id):
    """Link a conversation to a project"""
    try:
        data = request.json or {}
        conversation_title = data.get('title')
        
        success = runtime.link_conversation_to_project(
            project_id, 
            conversation_id,
            conversation_title
        )
        
        if success:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Failed to link conversation"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----- Task Suggestion API Routes -----

@project_api.route('/api/projects/<project_id>/suggest_next_tasks', methods=['GET'])
def suggest_next_tasks(project_id):
    """Get intelligent suggestions for the next tasks to work on"""
    try:
        # Get optional limit parameter (default to 3)
        limit = request.args.get('limit', 3, type=int)
        
        # Load project context
        project_context = runtime.load_project_context(project_id)
        
        if not project_context:
            return jsonify({"error": "Project not found"}), 404
            
        # Convert ProjectContextManager to dict for the task_reasoner
        context_data = project_context.memory if hasattr(project_context, 'memory') else {}
        
        # Get task suggestions
        suggestions = task_reasoner.suggest_next_tasks(context_data, limit=limit)
        
        # Generate human-readable suggestion text for the top suggestion
        suggestion_text = ""
        if suggestions and len(suggestions) > 0:
            suggestion_text = task_reasoner.generate_task_suggestion_text(suggestions[0])
        
        return jsonify({
            "success": True,
            "suggestions": suggestions,
            "suggestion_text": suggestion_text
        }), 200
    except Exception as e:
        logger.error(f"Error suggesting next tasks: {str(e)}")
        return jsonify({"error": str(e)}), 500

@project_api.route('/api/projects/<project_id>/tasks/<int:task_index>/mark_active', methods=['PUT'])
def mark_task_active(project_id, task_index):
    """Mark a task as the currently active task"""
    try:
        # Load project context
        project_context = runtime.load_project_context(project_id)
        
        if not project_context or 'task_queue' not in project_context.memory:
            return jsonify({"error": "Project context or task queue not found"}), 404
            
        tasks = project_context.memory['task_queue']
        
        # Validate task index
        if task_index < 0 or task_index >= len(tasks):
            return jsonify({"error": "Task index out of range"}), 404
            
        # Clear any previous active tasks
        for i, task in enumerate(tasks):
            if isinstance(task, dict):
                if 'active' in task:
                    task['active'] = False
        
        # Mark the specified task as active
        task = tasks[task_index]
        if isinstance(task, str):
            # Convert string task to object
            task = {
                'text': task,
                'active': True
            }
            tasks[task_index] = task
        else:
            # Update existing object
            task['active'] = True
        
        # Save the updated context
        project_context.save_memory()
        
        return jsonify({
            "success": True,
            "tasks": tasks,
            "active_task_index": task_index
        }), 200
    except Exception as e:
        logger.error(f"Error marking task as active: {str(e)}")
        return jsonify({"error": str(e)}), 500

@project_api.route('/api/projects/<project_id>/reprioritize', methods=['POST'])
def reprioritize_tasks(project_id):
    """Reprioritize tasks based on intelligent analysis"""
    try:
        # This is a placeholder for future implementation
        # Currently just returns a success message
        return jsonify({
            "success": True,
            "message": "Task reprioritization not yet implemented"
        }), 200
    except Exception as e:
        logger.error(f"Error reprioritizing tasks: {str(e)}")
        return jsonify({"error": str(e)}), 500
