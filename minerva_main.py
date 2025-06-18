#!/usr/bin/env python3
"""
Minerva - Main Entry Point

This module serves as the main entry point for the Minerva AI Assistant,
providing initialization for all components and coordinating their interaction.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
from typing import Dict, Any, Optional, List

# Ensure the project's directory is in the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(PROJECT_ROOT, "minerva_logs"), exist_ok=True)

# Load environment variables
load_dotenv()

# Import Minerva components
from integrations.framework_manager import FrameworkManager
from memory.memory_manager import MemoryManager

class MinervaAI:
    """Main Minerva AI Assistant class."""
    
    def __init__(self):
        """Initialize Minerva AI Assistant."""
        logger.info("Initializing Minerva AI Assistant")
        
        # Set up logging
        self._setup_logging()
        
        # Initialize components
        self.framework_manager = FrameworkManager()
        self.memory_manager = MemoryManager()
        
        logger.info("Minerva AI Assistant initialized")
    
    def _setup_logging(self):
        """Set up logging for Minerva."""
        # Remove existing loguru handlers
        logger.remove()
        
        # Add console handler
        log_level = "INFO"
        logger.add(sys.stderr, level=log_level)
        
        # Add file handler
        logger.add(
            os.path.join(PROJECT_ROOT, "minerva_logs", "minerva.log"),
            rotation="10 MB",
            retention="7 days",
            level="DEBUG"
        )
        
        # Intercept standard library logging
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                # Get corresponding Loguru level if it exists
                try:
                    level = logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno
                
                # Find caller from where the logged message originated
                frame, depth = logging.currentframe(), 2
                while frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1
                
                logger.opt(depth=depth, exception=record.exc_info).log(
                    level, record.getMessage()
                )
        
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    def _check_frameworks(self):
        """Check for pre-registered frameworks."""
        frameworks = self.framework_manager.get_all_frameworks()
        framework_count = len(frameworks)
        
        if framework_count == 0:
            logger.warning("No frameworks registered. Use the CLI to register frameworks.")
        else:
            logger.info(f"Found {framework_count} registered frameworks")
    
    def discover_frameworks(self, search_path):
        """Discover frameworks in the specified directory."""
        logger.info(f"Discovering frameworks in {search_path}")
        
        discovered = self.framework_manager.discover_frameworks(search_path)
        
        for framework in discovered:
            name = framework['name']
            path = framework['path']
            
            # Check if already registered
            info = self.framework_manager.get_framework_info(name)
            
            if not info:
                logger.info(f"Registering newly discovered framework: {name}")
                self.framework_manager.register_framework(name, path)
        
        return discovered
    
    def generate_code(self, prompt, framework=None, context=None):
        """Generate code using a framework."""
        logger.info(f"Generating code for prompt: {prompt[:50]}...")
        
        try:
            if framework:
                return self.framework_manager.execute_with_framework(
                    framework, "generate_code", prompt, context
                )
            else:
                return self.framework_manager.execute_with_capability(
                    "code_generation", "generate_code", prompt, context
                )
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise
    
    def execute_task(self, task, framework=None, context=None):
        """Execute a task using a framework."""
        logger.info(f"Executing task: {task[:50]}...")
        
        try:
            if framework:
                return self.framework_manager.execute_with_framework(
                    framework, "execute_task", task, context
                )
            else:
                return self.framework_manager.execute_with_capability(
                    "task_execution", "execute_task", task, context
                )
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            raise
    
    def get_memory_manager(self) -> MemoryManager:
        """Get the memory manager instance."""
        return self.memory_manager
    
    def add_memory(self, content: str, category: str, importance: int = 5, 
                  tags: Optional[List[str]] = None, source: str = "system") -> Dict[str, Any]:
        """
        Add a memory item to Minerva's memory.
        
        Args:
            content: The content of the memory
            category: Category of the memory (e.g., 'preference', 'fact', 'instruction')
            importance: Importance score (1-10)
            tags: List of tags for search/retrieval
            source: Source of the memory
            
        Returns:
            Dictionary with memory information
        """
        memory_item = self.memory_manager.add_memory(
            content=content,
            source=source,
            category=category,
            importance=importance,
            tags=tags or []
        )
        
        return {
            "id": memory_item.id,
            "status": "success",
            "content": memory_item.content
        }
    
    def search_memories(self, query: Optional[str] = None, category: Optional[str] = None,
                      tags: Optional[List[str]] = None, max_results: int = 5) -> Dict[str, Any]:
        """
        Search for memories based on criteria.
        
        Args:
            query: Text to search for in content
            category: Category to filter by
            tags: Tags to filter by
            max_results: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        memories = self.memory_manager.search_memories(
            query=query,
            category=category,
            tags=tags,
            max_results=max_results
        )
        
        results = []
        for memory in memories:
            results.append({
                "id": memory.id,
                "content": memory.content,
                "category": memory.category,
                "importance": memory.importance,
                "tags": memory.tags,
                "created_at": memory.created_at.isoformat()
            })
            
        return {
            "status": "success",
            "count": len(results),
            "memories": results
        }
    
    def start_conversation(self, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Start a new conversation.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with conversation information
        """
        conversation = self.memory_manager.create_conversation(user_id)
        
        return {
            "status": "success",
            "conversation_id": conversation.id,
            "user_id": user_id
        }
    
    def add_message(self, conversation_id: str, role: str, content: str) -> Dict[str, Any]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            role: Role of the sender (e.g., 'user', 'assistant')
            content: Content of the message
            
        Returns:
            Dictionary with status information
        """
        success = self.memory_manager.add_message_to_conversation(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        
        if not success:
            return {
                "status": "error",
                "message": f"Conversation {conversation_id} not found"
            }
            
        return {
            "status": "success",
            "conversation_id": conversation_id
        }
    
    def shutdown(self):
        """Perform any necessary cleanup."""
        logger.info("Shutting down Minerva AI Assistant")
        # Perform any necessary cleanup here
        
    def generate_response(self, conversation_id: str) -> str:
        """
        Generate a response to the conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Generated response text
        """
        logger.info(f"Generating response for conversation: {conversation_id}")
        
        # Get the conversation history
        conversation = self.memory_manager.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            return "I'm sorry, I couldn't find that conversation."
            
        # Get the messages to provide context
        messages = conversation.messages
        if not messages:
            logger.warning(f"No messages in conversation {conversation_id}")
            return "Hello! How can I assist you today?"
        
        # Get the most recent user message
        user_messages = [m for m in messages if m.role == "user"]
        if not user_messages:
            logger.warning(f"No user messages in conversation {conversation_id}")
            return "I'm not sure what you're asking. Could you please provide more information?"
        
        last_user_message = user_messages[-1].content
        
        try:
            # Try to use LangChain or HuggingFace for response generation
            response = None
            
            # First, try LangChain for response generation
            try:
                response = self.framework_manager.execute_with_framework(
                    "LangChain", "generate_text", last_user_message
                )
            except Exception as e:
                logger.warning(f"Error generating response with LangChain: {str(e)}")
                
            # If LangChain fails, try HuggingFace
            if not response:
                try:
                    response = self.framework_manager.execute_with_framework(
                        "HuggingFace", "generate_text", last_user_message
                    )
                except Exception as e:
                    logger.warning(f"Error generating response with HuggingFace: {str(e)}")
            
            # If all integrations fail, use our fallback response generator
            if not response:
                logger.warning("No framework available for response generation, using fallback")
                response = self._generate_fallback_response(last_user_message)
                
            # Save assistant's response to the conversation
            self.memory_manager.add_message_to_conversation(
                conversation_id=conversation_id,
                role="assistant",
                content=response
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return f"I'm sorry, I encountered an error while processing your request: {str(e)}"
    
    def _generate_fallback_response(self, message: str) -> str:
        """
        Generate a simple fallback response without relying on external AI frameworks.
        This ensures we always get a response even if external integrations fail.
        
        Args:
            message: The user's message
            
        Returns:
            A simple response
        """
        # Convert message to lowercase for easier matching
        message_lower = message.lower()
        
        # Simple rule-based responses
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
            return "Hello! How can I help you today?"
            
        elif any(question in message_lower for question in ["how are you", "how's it going"]):
            return "I'm functioning well, thank you for asking. How can I assist you?"
            
        elif any(question in message_lower for question in ["what can you do", "help", "capabilities"]):
            return "I can assist with various tasks including answering questions, generating text, and processing information. However, my advanced AI capabilities are currently limited as the frameworks aren't fully configured."
        
        elif any(term in message_lower for term in ["thanks", "thank you", "appreciate"]):
            return "You're welcome! Feel free to ask if you need anything else."
            
        elif "?" in message:
            return f"That's an interesting question about '{message}'. I'm currently unable to provide a detailed response as my AI frameworks aren't fully configured. When properly set up, I'd be able to give you a comprehensive answer."
        
        # Default response
        return f"I've received your message about '{message}'. While I understand the topic, I'm currently running in fallback mode with limited capabilities. Once the AI frameworks are properly configured, I'll be able to provide more sophisticated responses."

    def get_ai_response(self, conversation_id):
        """
        Generate an AI response for a conversation.
        
        Args:
            conversation_id (str): The ID of the conversation
        
        Returns:
            dict: Contains the AI response and metadata
        """
        print(f"[MINERVA] Generating AI response for conversation: {conversation_id}")
        
        try:
            # Get the conversation history
            conversation = self.memory_manager.get_conversation(conversation_id)
            if not conversation:
                return {"status": "error", "message": f"Conversation {conversation_id} not found"}
        
            # Try to use AI frameworks for response
            try:
                # This would normally use LangChain, Hugging Face, etc.
                # For now, we're providing a fallback for testing
                last_message = None
                for message in conversation.messages:
                    if message.role == "human":
                        last_message = message.content
            
                if last_message:
                    # Try to use a model to generate a response
                    # This is a placeholder for your AI integration
                    response_text = f"Minerva AI response to: '{last_message}'"
                else:
                    response_text = "I don't have any messages to respond to yet."
                
            except Exception as e:
                print(f"[MINERVA] Error using AI frameworks: {str(e)}")
                # Fallback to simple response generation
                response_text = "I'm having trouble connecting to my AI frameworks, but I received your message."
        
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "response": response_text
            }
        
        except Exception as e:
            print(f"[MINERVA] Error generating response: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to generate response: {str(e)}"
            }

def main():
    """Main entry point for Minerva AI when run directly."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Minerva AI Assistant")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--discover", "-d", help="Discover frameworks in the specified directory")
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Print welcome message
    print("\n" + "=" * 50)
    print(" Minerva AI Assistant")
    print("=" * 50 + "\n")
    
    try:
        # Initialize Minerva
        minerva = MinervaAI()
        
        # Discover frameworks if requested
        if args.discover:
            minerva.discover_frameworks(args.discover)
        
        # If launched directly, notify about CLI usage
        print("\nUse the Minerva CLI for full functionality.")
        print("Run 'python minerva_cli.py --help' for more information.\n")
        
        # Clean shutdown
        minerva.shutdown()
        
    except Exception as e:
        logger.error(f"Error running Minerva: {str(e)}")
        sys.exit(1)

def setup_logging(verbose=False):
    """Set up logging for Minerva."""
    # Remove existing loguru handlers
    logger.remove()
    
    # Add console handler
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stderr, level=log_level)
    
    # Add file handler
    logger.add(
        os.path.join(PROJECT_ROOT, "minerva_logs", "minerva.log"),
        rotation="10 MB",
        retention="7 days",
        level="DEBUG"
    )
    
    # Intercept standard library logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Find caller from where the logged message originated
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

if __name__ == "__main__":
    main()
