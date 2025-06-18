# minerva/core/project_context.py

import json
import os
from datetime import datetime

class ProjectContextManager:
    def __init__(self, project_name, base_path="projects"):
        self.project_name = project_name
        self.base_path = base_path
        self.project_path = os.path.join(base_path, project_name)
        self.meta_file = os.path.join(self.project_path, "metadata.json")
        self.memory = {
            "objectives": [],
            "task_queue": [],
            "logs": [],
            "notes": []
        }
        self._load_metadata()

    def _load_metadata(self):
        if os.path.exists(self.meta_file):
            with open(self.meta_file, 'r') as f:
                self.memory = json.load(f)
        else:
            os.makedirs(self.project_path, exist_ok=True)
            self._save_metadata()

    def _save_metadata(self):
        with open(self.meta_file, 'w') as f:
            json.dump(self.memory, f, indent=2)

    def log(self, entry):
        self.memory["logs"].append(entry)
        self._save_metadata()

    def add_task(self, task, priority=None, dependencies=None, deadline=None):
        # Support backward compatibility - if task is a string, convert to dict
        if isinstance(task, str):
            task_obj = {
                "text": task,
                "created_at": datetime.now().isoformat()
            }
        elif isinstance(task, dict) and "text" in task:
            # If it's already a dict with text, use as is
            task_obj = task.copy()
            if "created_at" not in task_obj:
                task_obj["created_at"] = datetime.now().isoformat()
        else:
            # Invalid task format
            raise ValueError("Task must be a string or dict with 'text' key")
            
        # Add optional task properties if provided
        if priority is not None:
            task_obj["priority"] = priority
        
        if dependencies is not None:
            task_obj["dependencies"] = dependencies
            
        if deadline is not None:
            task_obj["deadline"] = deadline
            
        self.memory["task_queue"].append(task_obj)
        self._save_metadata()
        
        return len(self.memory["task_queue"]) - 1  # Return the index of the new task

    def complete_task(self, task_index):
        if 0 <= task_index < len(self.memory["task_queue"]):
            task = self.memory["task_queue"].pop(task_index)
            
            # Handle both string and dict task formats for logging
            if isinstance(task, dict) and "text" in task:
                task_text = task["text"]
            else:
                task_text = str(task)
                
            self.log(f"✅ Completed: {task_text}")
            
            # Check for dependent tasks and update
            self._update_dependencies_after_completion(task_text)
            
            self._save_metadata()
            return task
        return None

    def set_objectives(self, objectives):
        self.memory["objectives"] = objectives
        self._save_metadata()

    def add_note(self, note):
        self.memory["notes"].append(note)
        self._save_metadata()

    def _update_dependencies_after_completion(self, completed_task_text):
        """Update dependencies when a task is completed"""
        for i, task in enumerate(self.memory["task_queue"]):
            if isinstance(task, dict) and "dependencies" in task:
                # If the completed task was a dependency, remove it
                if completed_task_text in task["dependencies"]:
                    task["dependencies"].remove(completed_task_text)
    
    def update_task_priority(self, task_index, priority):
        """Update the priority of a task"""
        if 0 <= task_index < len(self.memory["task_queue"]):
            task = self.memory["task_queue"][task_index]
            
            # Convert string task to dict if needed
            if isinstance(task, str):
                self.memory["task_queue"][task_index] = {
                    "text": task,
                    "created_at": datetime.now().isoformat(),
                    "priority": priority
                }
            else:
                task["priority"] = priority
                
            self._save_metadata()
            return True
        return False
        
    def add_task_dependency(self, task_index, dependency):
        """Add a dependency to a task"""
        if 0 <= task_index < len(self.memory["task_queue"]):
            task = self.memory["task_queue"][task_index]
            
            # Convert string task to dict if needed
            if isinstance(task, str):
                self.memory["task_queue"][task_index] = {
                    "text": task,
                    "created_at": datetime.now().isoformat(),
                    "dependencies": [dependency]
                }
            else:
                if "dependencies" not in task:
                    task["dependencies"] = []
                
                if dependency not in task["dependencies"]:
                    task["dependencies"].append(dependency)
                
            self._save_metadata()
            return True
        return False
        
    def set_task_deadline(self, task_index, deadline):
        """Set a deadline for a task"""
        if 0 <= task_index < len(self.memory["task_queue"]):
            task = self.memory["task_queue"][task_index]
            
            # Convert string task to dict if needed
            if isinstance(task, str):
                self.memory["task_queue"][task_index] = {
                    "text": task,
                    "created_at": datetime.now().isoformat(),
                    "deadline": deadline
                }
            else:
                task["deadline"] = deadline
                
            self._save_metadata()
            return True
        return False
        
    def get_task(self, task_index):
        """Get a task by index"""
        if 0 <= task_index < len(self.memory["task_queue"]):
            return self.memory["task_queue"][task_index]
        return None
        
    def get_tasks(self):
        """Get all tasks"""
        return self.memory["task_queue"]
        
    def get_context(self):
        return self.memory
