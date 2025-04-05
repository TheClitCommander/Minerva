"""
Minerva Project Management System

This module provides functionality for organizing conversations into projects.
It enables users to create projects, add conversations to projects, and retrieve
conversations by project.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class ProjectManager:
    """
    Project management system for organizing conversations in Minerva.
    This class provides methods to create, update, and manage projects.
    """
    
    def __init__(self, projects_directory: str = "./data/projects"):
        """
        Initialize the project management system.
        
        Args:
            projects_directory: Path where project data will be stored
        """
        # Ensure directory exists
        self.projects_directory = projects_directory
        os.makedirs(projects_directory, exist_ok=True)
        
        # Path to the projects index file
        self.projects_index_path = os.path.join(projects_directory, "projects_index.json")
        
        # Initialize the projects index
        self.projects = self._load_projects_index()
        
        logger.info(f"ProjectManager initialized with {len(self.projects)} projects")
    
    def _load_projects_index(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the projects index from disk.
        
        Returns:
            Dictionary of projects
        """
        if os.path.exists(self.projects_index_path):
            try:
                with open(self.projects_index_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse projects index, creating new one")
                return {}
        return {}
    
    def _save_projects_index(self):
        """Save the projects index to disk."""
        with open(self.projects_index_path, 'w') as f:
            json.dump(self.projects, f, indent=2)
    
    def create_project(self, 
                      name: str, 
                      description: str = "", 
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new project.
        
        Args:
            name: Name of the project
            description: Description of the project
            metadata: Additional metadata for the project
            
        Returns:
            project_id: Unique ID for the created project
        """
        # Generate a unique ID for this project
        project_id = str(uuid.uuid4())
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
            
        # Create project entry
        self.projects[project_id] = {
            "project_id": project_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "conversations": [],
            "metadata": metadata
        }
        
        # Save the updated index
        self._save_projects_index()
        
        logger.info(f"Created project {name} with ID {project_id}")
        return project_id
    
    def update_project(self, 
                      project_id: str, 
                      name: Optional[str] = None, 
                      description: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing project.
        
        Args:
            project_id: ID of the project to update
            name: New name for the project (optional)
            description: New description for the project (optional)
            metadata: New metadata for the project (optional)
            
        Returns:
            success: True if the project was updated successfully
        """
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return False
        
        project = self.projects[project_id]
        
        # Update fields if provided
        if name is not None:
            project["name"] = name
        
        if description is not None:
            project["description"] = description
            
        if metadata is not None:
            project["metadata"].update(metadata)
        
        # Update the updated_at timestamp
        project["updated_at"] = datetime.now().isoformat()
        
        # Save the updated index
        self._save_projects_index()
        
        logger.info(f"Updated project {project_id}")
        return True
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            success: True if the project was deleted successfully
        """
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return False
        
        # Remove the project from the index
        del self.projects[project_id]
        
        # Save the updated index
        self._save_projects_index()
        
        logger.info(f"Deleted project {project_id}")
        return True
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a project by ID.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            Project data if found, None otherwise
        """
        return self.projects.get(project_id)
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """
        Get all projects.
        
        Returns:
            List of all projects
        """
        return list(self.projects.values())
    
    def add_conversation_to_project(self, 
                                   project_id: str, 
                                   conversation_id: str,
                                   title: Optional[str] = None) -> bool:
        """
        Add a conversation to a project.
        
        Args:
            project_id: ID of the project
            conversation_id: ID of the conversation to add
            title: Optional title for the conversation in this project
            
        Returns:
            success: True if the conversation was added successfully
        """
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return False
        
        project = self.projects[project_id]
        
        # Check if conversation is already in the project
        for conv in project["conversations"]:
            if conv["conversation_id"] == conversation_id:
                logger.info(f"Conversation {conversation_id} already in project {project_id}")
                
                # Update title if provided
                if title is not None:
                    conv["title"] = title
                    
                # Update the project's updated_at timestamp
                project["updated_at"] = datetime.now().isoformat()
                self._save_projects_index()
                return True
        
        # Add the conversation to the project
        project["conversations"].append({
            "conversation_id": conversation_id,
            "title": title or f"Conversation {len(project['conversations']) + 1}",
            "added_at": datetime.now().isoformat()
        })
        
        # Update the project's updated_at timestamp
        project["updated_at"] = datetime.now().isoformat()
        
        # Save the updated index
        self._save_projects_index()
        
        logger.info(f"Added conversation {conversation_id} to project {project_id}")
        return True
    
    def remove_conversation_from_project(self, 
                                        project_id: str, 
                                        conversation_id: str) -> bool:
        """
        Remove a conversation from a project.
        
        Args:
            project_id: ID of the project
            conversation_id: ID of the conversation to remove
            
        Returns:
            success: True if the conversation was removed successfully
        """
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return False
        
        project = self.projects[project_id]
        
        # Find and remove the conversation
        for i, conv in enumerate(project["conversations"]):
            if conv["conversation_id"] == conversation_id:
                project["conversations"].pop(i)
                
                # Update the project's updated_at timestamp
                project["updated_at"] = datetime.now().isoformat()
                
                # Save the updated index
                self._save_projects_index()
                
                logger.info(f"Removed conversation {conversation_id} from project {project_id}")
                return True
        
        logger.error(f"Conversation {conversation_id} not found in project {project_id}")
        return False
    
    def get_project_conversations(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations in a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of conversations in the project
        """
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return []
        
        return self.projects[project_id]["conversations"]

# Initialize a singleton instance for global use
project_manager = ProjectManager()

# Utility functions for easy access to the project manager
def create_project(name: str, description: str = "", metadata: Optional[Dict] = None) -> str:
    """
    Create a new project.
    
    Args:
        name: Name of the project
        description: Description of the project
        metadata: Additional metadata
        
    Returns:
        project_id: ID of the created project
    """
    return project_manager.create_project(name, description, metadata)

def update_project(project_id: str, name: Optional[str] = None, 
                  description: Optional[str] = None, metadata: Optional[Dict] = None) -> bool:
    """
    Update an existing project.
    
    Args:
        project_id: ID of the project to update
        name: New name for the project
        description: New description for the project
        metadata: New metadata for the project
        
    Returns:
        success: True if the project was updated successfully
    """
    return project_manager.update_project(project_id, name, description, metadata)

def delete_project(project_id: str) -> bool:
    """
    Delete a project.
    
    Args:
        project_id: ID of the project to delete
        
    Returns:
        success: True if the project was deleted successfully
    """
    return project_manager.delete_project(project_id)

def get_project(project_id: str) -> Optional[Dict]:
    """
    Get a project by ID.
    
    Args:
        project_id: ID of the project
        
    Returns:
        Project data if found, None otherwise
    """
    return project_manager.get_project(project_id)

def get_all_projects() -> List[Dict]:
    """
    Get all projects.
    
    Returns:
        List of all projects
    """
    return project_manager.get_all_projects()

def add_conversation_to_project(project_id: str, conversation_id: str, title: Optional[str] = None) -> bool:
    """
    Add a conversation to a project.
    
    Args:
        project_id: ID of the project
        conversation_id: ID of the conversation
        title: Optional title for the conversation
        
    Returns:
        success: True if the conversation was added successfully
    """
    return project_manager.add_conversation_to_project(project_id, conversation_id, title)

def remove_conversation_from_project(project_id: str, conversation_id: str) -> bool:
    """
    Remove a conversation from a project.
    
    Args:
        project_id: ID of the project
        conversation_id: ID of the conversation
        
    Returns:
        success: True if the conversation was removed successfully
    """
    return project_manager.remove_conversation_from_project(project_id, conversation_id)

def get_project_conversations(project_id: str) -> List[Dict]:
    """
    Get all conversations in a project.
    
    Args:
        project_id: ID of the project
        
    Returns:
        List of conversations in the project
    """
    return project_manager.get_project_conversations(project_id)
