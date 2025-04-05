"""
Enhanced Memory Integration

This module integrates real-time adaptation, memory optimization, and multi-AI
context synchronization components with Minerva's existing systems.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix import paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from memory.real_time_memory_manager import real_time_memory_manager
from ai_decision.real_time_adaptation import adaptation_engine
from ai_decision.multi_ai_context_sync import context_sync
from ai_decision.context_decision_tree import decision_tree
from ai_decision.ai_model_switcher import model_switcher
from ai_decision.ai_decision_maker import ai_decision_maker
from web.multi_ai_coordinator import multi_ai_coordinator
from users.global_feedback_manager import global_feedback_manager
from users.response_formatter import response_formatter

class EnhancedMemorySystem:
    """
    Integrates real-time adaptation, memory optimization, and multi-AI context synchronization
    with Minerva's existing systems for a comprehensive enhancement to memory and decision-making.
    """
    
    def __init__(self):
        """Initialize the enhanced memory system."""
        # Reference components
        self.memory_manager = real_time_memory_manager
        self.adaptation_engine = adaptation_engine
        self.context_sync = context_sync
        self.decision_tree = decision_tree
        self.model_switcher = model_switcher
        self.ai_decision_maker = ai_decision_maker
        self.multi_ai_coordinator = multi_ai_coordinator
        self.global_feedback_manager = global_feedback_manager
        self.response_formatter = response_formatter
        
        # Track active user contexts
        self.active_contexts = {}
        
        logger.info("Enhanced Memory System initialized")
    
    def process_message(self, user_id: str, message: str, message_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message with enhanced memory and real-time adaptation.
        
        Args:
            user_id: User ID
            message: User message
            message_id: Optional message ID
            
        Returns:
            Processing result
        """
        if not message_id:
            message_id = f"msg_{int(time.time())}_{hash(message) % 10000}"
        
        logger.info(f"Processing message {message_id} from user {user_id}")
        
        # Step 1: Context Analysis
        context_analysis = self.decision_tree.analyze_context(message)
        logger.info(f"Context analysis for message {message_id}: {context_analysis}")
        
        # Step 2: Create/Update Shared Context
        if user_id not in self.active_contexts:
            # Create new context for user
            context = self.context_sync.create_shared_context(
                user_id=user_id,
                initial_data=context_analysis,
                priority=2
            )
            self.active_contexts[user_id] = context.context_id
        else:
            # Update existing context
            context_id = self.active_contexts[user_id]
            context = self.context_sync.update_shared_context(
                user_id=user_id,
                context_id=context_id,
                updates=context_analysis
            )
            
            if not context:
                # Context was lost, create new one
                context = self.context_sync.create_shared_context(
                    user_id=user_id,
                    initial_data=context_analysis,
                    priority=2
                )
                self.active_contexts[user_id] = context.context_id
        
        # Step 3: Apply Real-Time Adaptations
        adapted_context = self.adaptation_engine.start_response_adaptation(
            user_id=user_id,
            message_id=message_id,
            original_context=context_analysis
        )
        
        # Step 4: Select AI Model with Context-Awareness
        selected_model = self.model_switcher.select_model(adapted_context)
        logger.info(f"Selected model for message {message_id}: {selected_model}")
        
        # Step 5: Apply Model Selection Override
        override = self.context_sync.apply_model_override(
            user_id=user_id,
            message=message,
            message_id=message_id,
            context_id=self.active_contexts[user_id]
        )
        
        # Step 6: Process with Multi-AI Coordinator
        coordinator_result = None
        try:
            # Calls would be async in real implementation
            # For demonstration, we simulate the result
            coordinator_result = {
                "response": f"This is a simulated response for message: {message}",
                "model_used": selected_model,
                "quality_score": 0.9,
                "message_id": message_id,
                "processing_time": 0.5
            }
        finally:
            # Always clear the override after use
            self.context_sync.clear_model_override()
        
        if not coordinator_result:
            logger.error(f"Failed to process message {message_id}")
            return {
                "success": False,
                "error": "Failed to process message"
            }
        
        # Step 7: Complete Real-Time Adaptation
        self.adaptation_engine.complete_adaptation(
            message_id=message_id,
            result={
                "response_generated": True,
                "model_used": coordinator_result["model_used"]
            }
        )
        
        # Step 8: Optimize Memory
        self._optimize_memory(user_id, message, coordinator_result)
        
        # Step 9: Synchronize Context Across Models
        all_models = ["claude", "claude-light", "claude-opus", "claude-sonnet"]
        self.context_sync.sync_context_to_models(
            user_id=user_id,
            context_id=self.active_contexts[user_id],
            target_models=all_models
        )
        
        return {
            "success": True,
            "message_id": message_id,
            "response": coordinator_result["response"],
            "model_used": coordinator_result["model_used"],
            "context": adapted_context,
            "processing_time": coordinator_result["processing_time"]
        }
    
    def _optimize_memory(self, user_id: str, message: str, result: Dict[str, Any]):
        """
        Optimize memory by extracting important information and updating context scores.
        
        Args:
            user_id: User ID
            message: User message
            result: Processing result
        """
        # Extract topic from message (simplified)
        topic = message.lower().split()
        topic = " ".join(topic[:min(5, len(topic))])
        
        # Update context scores for relevant memories
        memories = self.memory_manager.get_relevant_context_memories(f"user:{user_id}")
        
        for memory in memories:
            self.memory_manager.update_context_score(
                memory_id=memory.id,
                context=topic,
                score_increment=0.1
            )
        
        # Clean up expired memories
        self.memory_manager.cleanup_expired_memories()
    
    def process_feedback(self, user_id: str, message_id: str, 
                         feedback_type: str, feedback_value: Any) -> Dict[str, Any]:
        """
        Process feedback for a message with enhanced memory integration.
        
        Args:
            user_id: User ID
            message_id: Message ID
            feedback_type: Feedback type
            feedback_value: Feedback value
            
        Returns:
            Processing result
        """
        logger.info(f"Processing {feedback_type} feedback for message {message_id} from user {user_id}")
        
        # Step 1: Inject Real-Time Feedback
        updated_context = self.adaptation_engine.inject_feedback(
            message_id=message_id,
            feedback_type=feedback_type,
            feedback_value=feedback_value
        )
        
        # Step 2: Update Global Feedback
        self.global_feedback_manager.record_feedback(
            user_id=user_id,
            message_id=message_id,
            feedback_type=feedback_type,
            feedback_value=feedback_value
        )
        
        # Step 3: Update Context with Feedback Data
        if user_id in self.active_contexts:
            context_id = self.active_contexts[user_id]
            self.context_sync.update_shared_context(
                user_id=user_id,
                context_id=context_id,
                updates={"recent_feedback": {feedback_type: feedback_value}}
            )
        
        # Step 4: Record Feedback Signal
        self.adaptation_engine.record_signal(
            user_id=user_id,
            signal=adaptation_engine.EngagementSignal(
                signal_type=feedback_type,
                value=feedback_value,
                metadata={"message_id": message_id}
            )
        )
        
        return {
            "success": True,
            "message_id": message_id,
            "feedback_processed": True,
            "adaptations_applied": bool(updated_context)
        }
    
    def create_conversation_memory(self, user_id: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new conversation with memory tracking.
        
        Args:
            user_id: User ID
            conversation_id: Optional conversation ID
            
        Returns:
            Conversation data
        """
        # Create conversation in core memory manager
        conversation = self.memory_manager.memory_manager.create_conversation(user_id)
        
        # Create shared context for this conversation
        context = self.context_sync.create_shared_context(
            user_id=user_id,
            initial_data={"conversation_id": conversation.conversation_id},
            priority=3
        )
        
        # Associate context with user
        self.active_contexts[user_id] = context.context_id
        
        return {
            "success": True,
            "user_id": user_id,
            "conversation_id": conversation.conversation_id,
            "context_id": context.context_id
        }


# Create a singleton instance
enhanced_memory_system = EnhancedMemorySystem()


def test_enhanced_memory_system():
    """Test the EnhancedMemorySystem functionality."""
    print("\nTesting Enhanced Memory System...\n")
    
    user_id = "test_user_3"
    
    # Step 1: Create conversation
    print("Creating conversation with memory tracking...")
    conversation = enhanced_memory_system.create_conversation_memory(user_id)
    print(f"Conversation created: {conversation}")
    
    # Step 2: Process messages
    print("\nProcessing messages with real-time adaptation...")
    
    messages = [
        "What is machine learning?",
        "Can you explain neural networks in more detail?",
        "Show me some examples of deep learning applications"
    ]
    
    for i, message in enumerate(messages):
        print(f"\nMessage {i+1}: '{message}'")
        result = enhanced_memory_system.process_message(
            user_id=user_id,
            message=message
        )
        
        print(f"Response from: {result['model_used']}")
        print(f"Context: {result['context']}")
        print(f"Processing time: {result['processing_time']:.2f}s")
    
    # Step 3: Process feedback
    print("\nProcessing user feedback...")
    feedback_result = enhanced_memory_system.process_feedback(
        user_id=user_id,
        message_id=result["message_id"],
        feedback_type="helpful",
        feedback_value=True
    )
    
    print(f"Feedback processed: {feedback_result}")
    
    # Step 4: Check memory optimizations
    print("\nChecking optimized memory...")
    
    # Process another message to see adaptations
    print("\nProcessing follow-up message with adaptations...")
    result = enhanced_memory_system.process_message(
        user_id=user_id,
        message="Can you give me more practical examples?"
    )
    
    print(f"Response from: {result['model_used']}")
    print(f"Adapted context: {result['context']}")
    
    print("\nEnhanced Memory System tests completed!")


if __name__ == "__main__":
    test_enhanced_memory_system()
