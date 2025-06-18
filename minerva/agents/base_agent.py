"""
Base Agent Module

Provides the foundation for all specialized AI agents in Minerva's multi-agent system.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class BaseAgent:
    """
    Base class for all Minerva agents.
    
    Implements core functionality that all specialized agents will inherit,
    including messaging, state management, and interaction with other agents.
    """
    
    def __init__(self, name: str, role: str, capabilities: List[str] = None):
        """
        Initialize a base agent with name, role and capabilities.
        
        Args:
            name: Unique identifier for the agent
            role: The functional role this agent performs (e.g., "researcher", "programmer")
            capabilities: List of specific skills this agent possesses
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.capabilities = capabilities or []
        self.state = {
            "active": True,
            "busy": False,
            "current_task": None,
            "memory": {},
            "conversation_context": []
        }
        self.connected_agents = {}
        logger.info(f"Agent {name} ({role}) initialized with ID: {self.id}")
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task assigned to this agent.
        
        Args:
            task: Dictionary containing task details and requirements
            
        Returns:
            Dictionary containing the results of the task
        """
        self.state["busy"] = True
        self.state["current_task"] = task
        
        # This should be overridden by specialized agents
        result = {"status": "not_implemented", "message": "This method should be overridden by specialized agents"}
        
        self.state["busy"] = False
        self.state["current_task"] = None
        return result
    
    def send_message(self, recipient_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to another agent.
        
        Args:
            recipient_id: ID of the agent to receive the message
            message: Dictionary containing the message content
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if recipient_id not in self.connected_agents:
            logger.error(f"Agent {self.name} tried to send message to unknown agent ID: {recipient_id}")
            return False
        
        recipient = self.connected_agents[recipient_id]
        return recipient.receive_message(self.id, message)
    
    def receive_message(self, sender_id: str, message: Dict[str, Any]) -> bool:
        """
        Receive a message from another agent.
        
        Args:
            sender_id: ID of the agent that sent the message
            message: Dictionary containing the message content
            
        Returns:
            True if message was processed successfully, False otherwise
        """
        # Store in conversation context
        self.state["conversation_context"].append({
            "sender": sender_id,
            "message": message,
            "timestamp": self._get_timestamp()
        })
        
        logger.debug(f"Agent {self.name} received message from {sender_id}: {message.get('type', 'unknown')}")
        return True
    
    def connect_to_agent(self, agent: 'BaseAgent') -> bool:
        """
        Establish a connection with another agent.
        
        Args:
            agent: The agent to connect with
            
        Returns:
            True if connection was established successfully, False otherwise
        """
        if agent.id in self.connected_agents:
            logger.warning(f"Agent {self.name} already connected to {agent.name}")
            return False
        
        self.connected_agents[agent.id] = agent
        if self.id not in agent.connected_agents:
            agent.connected_agents[self.id] = self
        
        logger.debug(f"Agent {self.name} connected to {agent.name}")
        return True
    
    def update_state(self, state_updates: Dict[str, Any]) -> None:
        """
        Update the agent's internal state.
        
        Args:
            state_updates: Dictionary of state values to update
        """
        for key, value in state_updates.items():
            if key in self.state:
                self.state[key] = value
    
    def add_to_memory(self, key: str, value: Any) -> None:
        """
        Add an item to the agent's memory.
        
        Args:
            key: Key to store the memory under
            value: Value to store
        """
        self.state["memory"][key] = value
    
    def get_from_memory(self, key: str) -> Any:
        """
        Retrieve an item from the agent's memory.
        
        Args:
            key: Key to retrieve
            
        Returns:
            The stored memory value or None if not found
        """
        return self.state["memory"].get(key)
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in seconds."""
        import time
        return int(time.time())
    
    def __repr__(self) -> str:
        return f"<Agent: {self.name} ({self.role})>"
