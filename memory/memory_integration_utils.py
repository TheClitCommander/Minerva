"""
Memory Integration Utilities for Minerva

This module provides utility functions for integrating the EnhancedMemoryManager
with Minerva's chat interface and other systems.

Features:
- Format memories for natural inclusion in responses
- Find and integrate relevant memories into AI responses
- Process natural language memory commands
- Memory command handlers for Minerva's API
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the EnhancedMemoryManager singleton
from memory.enhanced_memory_manager import EnhancedMemoryManager

# Get singleton instance
memory_manager = EnhancedMemoryManager()


def format_memory_for_response(memory: Dict[str, Any]) -> str:
    """
    Format a memory for inclusion in a response in a natural way.
    
    Args:
        memory: The memory item
        
    Returns:
        Formatted string for natural inclusion in a response
    """
    content = memory['content']
    category = memory['category']
    
    # Format based on category
    if category == 'preference':
        templates = [
            f"I remember you mentioned that {content}",
            f"You've told me before that {content}",
            f"Based on what you've shared with me, {content}"
        ]
    elif category == 'fact':
        templates = [
            f"I recall that {content}",
            f"From what I remember, {content}",
            f"According to what you've told me, {content}"
        ]
    elif category == 'instruction':
        templates = [
            f"You previously asked me to remember that {content}",
            f"You instructed me to note that {content}",
            f"I've been keeping in mind that {content}, as you requested"
        ]
    elif category == 'experience':
        templates = [
            f"You mentioned having experienced {content}",
            f"From your experiences, I recall that {content}",
            f"You previously shared that {content}"
        ]
    else:
        templates = [
            f"I remember that {content}",
            f"You've mentioned that {content}",
            f"From our previous conversations, {content}"
        ]
    
    # Choose a template based on memory ID as a simple way to get variety
    # but consistency for the same memory
    memory_id = memory['id']
    idx = sum(ord(c) for c in memory_id) % len(templates)
    return templates[idx]


def integrate_memories_into_response(user_query: str, context: str = None, 
                                  max_memories: int = 3) -> List[str]:
    """
    Find relevant memories for a user query and format them for inclusion in a response.
    
    Args:
        user_query: The user's query or message
        context: Optional conversation context
        max_memories: Maximum number of memories to include
        
    Returns:
        List of formatted memory strings ready for inclusion in a response
    """
    relevant_memories = memory_manager.get_memories(
        query=user_query, 
        context=context, 
        max_results=max_memories
    )
    
    if not relevant_memories:
        return []
        
    # Format each memory for inclusion
    formatted_memories = []
    for memory in relevant_memories:
        formatted = format_memory_for_response(memory)
        formatted_memories.append(formatted)
        
        # Update access count for this memory
        memory_id = memory['id']
        memory_manager.get_memory_by_id(memory_id)  # This automatically increments access_count
        
    return formatted_memories
    

def process_memory_command(command: str, content: str = None, memory_id: str = None,
                          category: str = None, tags: List[str] = None) -> Dict[str, Any]:
    """
    Process a memory management command from the user.
    
    Args:
        command: The command type ('add', 'update', 'delete', 'get', etc.)
        content: Content for add/update commands
        memory_id: ID for update/delete/get commands
        category: Optional category
        tags: Optional tags
        
    Returns:
        Dict with result and message
    """
    result = {"success": False, "message": "", "data": None}
    
    try:
        if command.lower() == 'add' or command.lower() == 'remember':
            if not content:
                result["message"] = "No content provided for memory"
                return result
                
            memory = memory_manager.add_memory(
                content=content,
                source="user_command",
                category=category or "instruction",
                tags=tags or []
            )
            
            result["success"] = True
            result["message"] = f"I'll remember that {content}"
            result["data"] = memory
            
        elif command.lower() == 'update':
            if not memory_id:
                result["message"] = "No memory ID provided for update"
                return result
                
            memory = memory_manager.update_memory(
                memory_id=memory_id,
                content=content,
                category=category,
                tags=tags
            )
            
            if memory:
                result["success"] = True
                result["message"] = f"Updated memory {memory_id}"
                result["data"] = memory
            else:
                result["message"] = f"Couldn't find memory {memory_id}"
                
        elif command.lower() == 'delete' or command.lower() == 'forget':
            if memory_id:
                # Delete specific memory
                success = memory_manager.delete_memory(memory_id)
                if success:
                    result["success"] = True
                    result["message"] = f"I've forgotten the memory with ID {memory_id}"
                else:
                    result["message"] = f"Couldn't find memory {memory_id}"
                    
            elif content:
                # Delete by content query
                deleted = memory_manager.delete_memories_by_query(query=content, category=category)
                result["success"] = True
                result["message"] = f"I've forgotten {deleted} memories related to '{content}'"
                result["data"] = {"deleted_count": deleted}
            else:
                result["message"] = "Need either memory ID or content to forget"
                
        elif command.lower() == 'get' or command.lower() == 'recall':
            if memory_id:
                # Get specific memory
                memory = memory_manager.get_memory_by_id(memory_id)
                if memory:
                    result["success"] = True
                    result["message"] = f"Memory {memory_id}: {memory['content']}"
                    result["data"] = memory
                else:
                    result["message"] = f"Couldn't find memory {memory_id}"
                    
            elif content or category or tags:
                # Search memories
                memories = memory_manager.get_memories(
                    query=content,
                    category=category,
                    tags=tags,
                    max_results=10
                )
                
                if memories:
                    memory_strings = [f"- {m['content']} (ID: {m['id'][:8]})..." for m in memories]
                    result["success"] = True
                    result["message"] = "Here are the memories I found:\n" + "\n".join(memory_strings)
                    result["data"] = memories
                else:
                    result["message"] = "I couldn't find any memories matching your criteria"
            else:
                result["message"] = "Need either memory ID or search criteria"
        else:
            result["message"] = f"Unknown memory command: {command}"
            
    except Exception as e:
        result["message"] = f"Error processing memory command: {str(e)}"
        logger.error(f"Error processing memory command: {str(e)}")
        
    return result


def get_relevant_memory_ids(user_query: str, context: str = None, 
                              max_results: int = 3) -> List[str]:
    """
    Find IDs of relevant memories for a user query without retrieving full content.
    Useful for tracking which memories were relevant to a response.
    
    Args:
        user_query: The user's query or message
        context: Optional conversation context
        max_results: Maximum number of memory IDs to return
        
    Returns:
        List of memory IDs that were relevant to the query
    """
    relevant_memories = memory_manager.get_memories(
        query=user_query, 
        context=context, 
        max_results=max_results
    )
    
    if not relevant_memories:
        return []
        
    # Extract just the IDs
    memory_ids = [memory['id'] for memory in relevant_memories]
    return memory_ids


def extract_memory_command(user_message: str) -> Optional[Dict[str, Any]]:
    """
    Extract a memory command from a natural language user message.
    
    Args:
        user_message: The user's message
        
    Returns:
        Dict with command details or None if no command detected
    """
    user_msg = user_message.lower().strip()
    
    # Simple keyword-based command detection
    # Would be replaced with more sophisticated NLU in production
    result = {"command": None, "content": None, "category": None, "tags": []}
    
    # Add/Remember command patterns
    if user_msg.startswith("remember ") or user_msg.startswith("please remember "):
        result["command"] = "add"
        content = user_msg.replace("please remember ", "").replace("remember ", "")
        
        # Check for category markers
        if " as a " in content:
            parts = content.split(" as a ")
            content = parts[0].strip()
            category = parts[1].strip()
            result["category"] = category
            
            # Convert category words to standard categories
            if category in ["preference", "like", "dislike"]:
                result["category"] = "preference"
            elif category in ["fact", "information"]:
                result["category"] = "fact"
            elif category in ["instruction", "command", "directive"]:
                result["category"] = "instruction"
            elif category in ["experience", "event"]:
                result["category"] = "experience"
                
        result["content"] = content
        
    # Forget/Delete command patterns
    elif user_msg.startswith("forget ") or user_msg.startswith("please forget "):
        result["command"] = "delete"
        content = user_msg.replace("please forget ", "").replace("forget ", "")
        
        # Check if it's an ID
        if content.startswith("memory ") and len(content) > 8:
            possible_id = content.replace("memory ", "").strip()
            if len(possible_id) >= 8:
                result["memory_id"] = possible_id
            else:
                result["content"] = content
        else:
            result["content"] = content
            
    # Recall/Get command patterns
    elif user_msg.startswith("recall ") or user_msg.startswith("what do you remember about "):
        result["command"] = "get"
        if user_msg.startswith("recall "):
            content = user_msg.replace("recall ", "")
        else:
            content = user_msg.replace("what do you remember about ", "")
            
        result["content"] = content
        
    # If no command was detected
    if result["command"] is None:
        return None
        
    return result


def handle_memory_api_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle an API request for memory management.
    
    Args:
        request_data: The API request data
        
    Returns:
        API response
    """
    command = request_data.get("command")
    content = request_data.get("content")
    memory_id = request_data.get("memory_id")
    category = request_data.get("category")
    tags = request_data.get("tags", [])
    
    if not command:
        return {
            "success": False,
            "message": "No command specified",
            "data": None
        }
        
    # Process the command
    result = process_memory_command(
        command=command,
        content=content,
        memory_id=memory_id,
        category=category,
        tags=tags
    )
    
    return result


def test_memory_integration():
    """
    Test the memory integration utilities.
    """
    print("Testing memory integration utilities...")
    
    # Add sample memories first
    memory_manager.add_memory(
        content="you prefer dark chocolate over milk chocolate",
        source="conversation",
        category="preference",
        tags=["food", "preference"],
        importance=7
    )
    
    memory_manager.add_memory(
        content="you live in San Francisco",
        source="conversation",
        category="fact",
        tags=["location", "personal"]
    )
    
    memory_manager.add_memory(
        content="never use technical jargon without explanation",
        source="instruction",
        category="instruction",
        tags=["communication", "instruction"],
        importance=9
    )
    
    # Test extracting commands from natural language
    test_messages = [
        "Remember that I like pizza with extra cheese",
        "Please remember I have a meeting tomorrow at 3pm as a fact",
        "Forget what I said about pizza",
        "What do you remember about my food preferences?",
        "This is not a memory command"
    ]
    
    print("\nTesting natural language command extraction:")
    for msg in test_messages:
        command = extract_memory_command(msg)
        if command:
            print(f"'{msg}' → {command}")
        else:
            print(f"'{msg}' → No command detected")
    
    # Test command processing
    print("\nTesting memory command processing:")
    
    # Add memory
    result = process_memory_command(
        command="add",
        content="I have a dog named Max",
        category="fact",
        tags=["pet", "personal"]
    )
    print(f"Add memory result: {result['message']}")
    
    # Test getting relevant memories
    print("\nTesting memory integration into responses:")
    query = "What kind of chocolate do I like?"
    memories = integrate_memories_into_response(query)
    
    print(f"For query: '{query}'")
    if memories:
        print("Relevant memories:")
        for memory in memories:
            print(f" - {memory}")
    else:
        print("No relevant memories found")
        
    # Test integration with another query
    query = "Where do I live?"
    memories = integrate_memories_into_response(query)
    
    print(f"\nFor query: '{query}'")
    if memories:
        print("Relevant memories:")
        for memory in memories:
            print(f" - {memory}")
    else:
        print("No relevant memories found")
    
    print("\nMemory integration tests completed!")


if __name__ == "__main__":
    test_memory_integration()
