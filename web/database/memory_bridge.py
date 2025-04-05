#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Memory Bridge Module

This module provides a bridge between the original JSON-based memory system
and the new SQLite database, ensuring backward compatibility during the transition.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

# Import the database module
from web.database.conversation_db import get_db, ConversationDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("memory_bridge")

class MemoryBridge:
    """
    Bridge class to maintain compatibility between JSON memory and SQLite database.
    This allows for a seamless transition without breaking existing functionality.
    """
    
    def __init__(self):
        """Initialize the bridge with database connection"""
        self.db = get_db()
        self.memory_data = {}
        self.in_memory_mode = False
        
    def init_from_json(self, json_path: str = None) -> bool:
        """
        Load existing JSON memory into the bridge.
        This ensures compatibility with code still expecting the JSON format.
        """
        if not json_path:
            # Find JSON memory in default location
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(current_dir, 'conversation_memory.json')
        
        if not os.path.exists(json_path):
            logger.info(f"No JSON memory file found at {json_path}, using empty memory")
            return False
            
        try:
            with open(json_path, 'r') as f:
                self.memory_data = json.load(f)
                
            logger.info(f"Loaded {len(self.memory_data)} conversations from JSON memory")
            
            # If we have in-memory data, enable in-memory mode for backward compatibility
            if self.memory_data:
                self.in_memory_mode = True
                
            return True
        except Exception as e:
            logger.error(f"Error loading JSON memory: {str(e)}")
            return False
    
    def get_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get a conversation by ID, checking both in-memory data and database.
        This maintains compatibility with both storage methods.
        """
        # First try to get from database (primary source)
        db_conversation = self.db.get_conversation(conversation_id)
        
        if db_conversation:
            # Convert database format to the old JSON memory format
            messages = []
            for msg in db_conversation['messages']:
                message = {
                    'role': msg['role'],
                    'content': msg['content']
                }
                messages.append(message)
            return messages
        
        # Fall back to in-memory data if available
        if self.in_memory_mode and conversation_id in self.memory_data:
            return self.memory_data[conversation_id]
            
        # Conversation not found in either location
        return []
    
    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """
        Add a message to a conversation, updating both database and in-memory data if needed.
        """
        # Always add to database (primary storage)
        self.db.add_message(conversation_id, role, content)
        
        # If we're in compatibility mode, also update in-memory data
        if self.in_memory_mode:
            if conversation_id not in self.memory_data:
                self.memory_data[conversation_id] = []
                
            self.memory_data[conversation_id].append({
                'role': role,
                'content': content
            })
    
    def save_to_json(self, json_path: str = None) -> bool:
        """
        Save the current memory data to JSON format for backward compatibility.
        This exports from the database to ensure data consistency.
        """
        if not json_path:
            # Use default location
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(current_dir, 'conversation_memory.json')
        
        try:
            # Get all conversation IDs from the database
            conversation_ids = self.db.get_conversation_ids()
            
            # Build the JSON memory structure
            json_memory = {}
            
            for conv_id in conversation_ids:
                # Get messages for this conversation
                db_conversation = self.db.get_conversation(conv_id)
                if not db_conversation:
                    continue
                    
                # Convert to the old JSON memory format
                messages = []
                for msg in db_conversation['messages']:
                    message = {
                        'role': msg['role'],
                        'content': msg['content']
                    }
                    messages.append(message)
                    
                json_memory[conv_id] = messages
            
            # Write to file
            with open(json_path, 'w') as f:
                json.dump(json_memory, f, indent=2)
                
            logger.info(f"Saved {len(json_memory)} conversations to JSON memory file")
            return True
        except Exception as e:
            logger.error(f"Error saving to JSON memory: {str(e)}")
            return False
    
    def get_all_conversations(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all conversations in the old JSON memory format.
        This is used for compatibility with code expecting the old format.
        """
        # Start with in-memory data if we have it
        result = self.memory_data.copy() if self.in_memory_mode else {}
        
        # Add or override with data from the database
        conversation_ids = self.db.get_conversation_ids()
        
        for conv_id in conversation_ids:
            db_conversation = self.db.get_conversation(conv_id)
            if not db_conversation:
                continue
                
            # Convert to the old JSON memory format
            messages = []
            for msg in db_conversation['messages']:
                message = {
                    'role': msg['role'],
                    'content': msg['content']
                }
                messages.append(message)
                
            result[conv_id] = messages
            
        return result
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update the title of a conversation in the database"""
        return self.db.update_conversation_title(conversation_id, title)
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of a conversation with message counts and timestamps"""
        return self.db.get_conversation_summary(conversation_id)
    
    def search_conversations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for conversations by content or title"""
        return self.db.search_conversations(query, limit)
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get a list of recent conversations with their summaries"""
        return self.db.get_conversations(limit)

# Create a singleton instance
_bridge_instance = None

def get_memory_bridge() -> MemoryBridge:
    """Get the singleton memory bridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = MemoryBridge()
        _bridge_instance.init_from_json()
    return _bridge_instance
