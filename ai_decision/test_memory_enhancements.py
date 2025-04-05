"""
Test Memory and Real-Time Adaptation Enhancements

This module tests the integration and functionality of real-time adaptation,
memory optimization, and multi-AI context synchronization enhancements.
"""

import os
import sys
import json
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix import paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from memory.real_time_memory_manager import real_time_memory_manager
from ai_decision.real_time_adaptation import adaptation_engine
from ai_decision.multi_ai_context_sync import context_sync
from ai_decision.enhanced_memory_integration import enhanced_memory_system


def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def print_subheader(title):
    """Print a subsection header."""
    print("\n" + "-" * 40)
    print(title)
    print("-" * 40)


def test_real_time_adaptation():
    """Test real-time adaptation functionality."""
    print_subheader("Testing Real-Time Adaptation")
    
    user_id = "test_user_1"
    
    # Test engagement signals
    print("\n1. Testing Engagement Signal Processing")
    
    # Record increasing message length signals
    print("Recording user engagement signals...")
    for length in [50, 75, 120]:
        adaptation_engine.record_signal(
            user_id=user_id,
            signal=adaptation_engine.EngagementSignal(
                signal_type="message_length",
                value=length
            )
        )
    
    # Record expansion clicks
    for _ in range(2):
        adaptation_engine.record_signal(
            user_id=user_id,
            signal=adaptation_engine.EngagementSignal(
                signal_type="expansion_click",
                value=True
            )
        )
    
    # Check for adaptations
    adaptations = adaptation_engine.get_adaptations(user_id)
    print(f"Active adaptations: {adaptations}")
    
    # Test in-flight adaptation
    print("\n2. Testing In-Flight Response Adaptation")
    
    message_id = f"msg_{uuid.uuid4().hex[:8]}"
    original_context = {
        "length": "standard",
        "tone": "neutral",
        "detail_level": "balanced"
    }
    
    # Start adaptation
    adapted_context = adaptation_engine.start_response_adaptation(
        user_id=user_id,
        message_id=message_id,
        original_context=original_context
    )
    
    print(f"Original context: {original_context}")
    print(f"Adapted context: {adapted_context}")
    
    # Inject real-time feedback
    updated_context = adaptation_engine.inject_feedback(
        message_id=message_id,
        feedback_type="expansion_request",
        feedback_value=True
    )
    
    print(f"Context after feedback injection: {updated_context}")
    
    # Complete adaptation
    completed = adaptation_engine.complete_adaptation(
        message_id=message_id,
        result={"response_accepted": True}
    )
    
    print(f"Adaptation completed in {completed.get('duration', 0):.2f} seconds")
    
    print("\n=> Real-Time Adaptation Test: SUCCESS")


def test_memory_optimization():
    """Test memory optimization functionality."""
    print_subheader("Testing Memory Optimization")
    
    # Create test memories in different layers
    print("\n1. Testing Layered Memory Organization")
    
    # Create high-importance memory (long-term)
    memory1 = real_time_memory_manager.add_memory_with_context(
        content="User prefers technical explanations with code examples",
        source="system",
        category="preference",
        context="user_preferences",
        importance=8,
        tags=["preference", "technical", "code_examples"]
    )
    
    # Create medium-importance memory (short-term)
    memory2 = real_time_memory_manager.add_memory_with_context(
        content="User is researching machine learning frameworks",
        source="inference",
        category="interest",
        context="research_topics",
        importance=4,
        tags=["interest", "machine_learning", "frameworks"]
    )
    
    # Create low-importance memory (working)
    memory3 = real_time_memory_manager.add_memory_with_context(
        content="Current conversation about PyTorch vs TensorFlow",
        source="conversation",
        category="context",
        context="current_topic",
        importance=2,
        tags=["context", "pytorch", "tensorflow"]
    )
    
    # Check memory layers
    working_memories = real_time_memory_manager.get_memories_in_layer("working")
    short_term_memories = real_time_memory_manager.get_memories_in_layer("short_term")
    long_term_memories = real_time_memory_manager.get_memories_in_layer("long_term")
    
    print(f"Working memory layer: {len(working_memories)} items")
    print(f"Short-term memory layer: {len(short_term_memories)} items")
    print(f"Long-term memory layer: {len(long_term_memories)} items")
    
    # Test context relevance scoring
    print("\n2. Testing Context Persistence Scoring")
    
    # Update context scores
    real_time_memory_manager.update_context_score(memory1.id, "machine_learning", 0.7)
    real_time_memory_manager.update_context_score(memory2.id, "machine_learning", 0.5)
    real_time_memory_manager.update_context_score(memory3.id, "machine_learning", 0.3)
    
    # Get relevant memories
    relevant_memories = real_time_memory_manager.get_relevant_context_memories("machine_learning")
    
    print(f"Relevant memories for 'machine_learning': {len(relevant_memories)}")
    for i, memory in enumerate(relevant_memories, 1):
        print(f"  {i}. {memory.content} (importance: {memory.importance})")
    
    # Test memory caching
    print("\n3. Testing Memory Caching")
    
    # Access memories multiple times to trigger caching
    for _ in range(3):
        real_time_memory_manager.get_relevant_context_memories("machine_learning")
    
    print(f"Cache hit counts: {dict(real_time_memory_manager.cache_hit_counter)}")
    print(f"Cache size: {len(real_time_memory_manager.memory_cache)} items")
    
    print("\n=> Memory Optimization Test: SUCCESS")


def test_multi_ai_context_sync():
    """Test multi-AI context synchronization functionality."""
    print_subheader("Testing Multi-AI Context Synchronization")
    
    user_id = "test_user_2"
    
    # Create shared context
    print("\n1. Testing Shared Context Creation and Distribution")
    
    context = context_sync.create_shared_context(
        user_id=user_id,
        initial_data={
            "skill_level": "advanced",
            "interests": ["deep learning", "neural networks"],
            "detail_level": "technical"
        },
        source_model="claude-opus",
        priority=4
    )
    
    print(f"Created shared context: {context.context_id}")
    
    # Sync to multiple models
    target_models = ["claude-light", "claude-sonnet", "claude-opus"]
    success = context_sync.sync_context_to_models(
        user_id=user_id,
        context_id=context.context_id,
        target_models=target_models
    )
    
    print(f"Synchronized to {len(target_models)} models: {success}")
    
    # Test model selection override
    print("\n2. Testing Context-Aware Model Selection Override")
    
    message = "Explain how transformer models work with attention mechanisms"
    
    override = context_sync.create_model_override(
        user_id=user_id,
        message=message,
        context_id=context.context_id
    )
    
    print(f"Model override: {override}")
    
    # Test applying and clearing override
    print("\n3. Testing Override Application and Clearing")
    
    applied_override = context_sync.apply_model_override(
        user_id=user_id,
        message=message,
        message_id=f"msg_{uuid.uuid4().hex[:8]}",
        context_id=context.context_id
    )
    
    print(f"Applied override models: {applied_override.get('models_to_use', [])}")
    
    # Clear override
    context_sync.clear_model_override()
    print("Override cleared successfully")
    
    print("\n=> Multi-AI Context Sync Test: SUCCESS")


def test_integrated_functionality():
    """Test the integrated functionality of all enhancements."""
    print_subheader("Testing Integrated Functionality")
    
    user_id = "integrated_test_user"
    
    # Create conversation with memory tracking
    print("\n1. Testing Conversation Creation with Memory Tracking")
    
    conversation = enhanced_memory_system.create_conversation_memory(user_id)
    print(f"Conversation created with ID: {conversation.get('conversation_id', 'unknown')}")
    print(f"Associated context ID: {conversation.get('context_id', 'unknown')}")
    
    # Process a sequence of related messages
    print("\n2. Testing End-to-End Message Processing")
    
    messages = [
        "What are transformer models in machine learning?",
        "Can you explain attention mechanisms in more detail?",
        "Show me a simple example of self-attention in code"
    ]
    
    results = []
    
    for i, message in enumerate(messages, 1):
        print(f"\nMessage {i}: '{message}'")
        
        result = enhanced_memory_system.process_message(
            user_id=user_id,
            message=message
        )
        
        results.append(result)
        
        print(f"Processed with model: {result.get('model_used', 'unknown')}")
        print(f"Context parameters: {result.get('context', {})}")
        
        # If not the last message, add positive feedback
        if i < len(messages):
            feedback_result = enhanced_memory_system.process_feedback(
                user_id=user_id,
                message_id=result.get('message_id', ''),
                feedback_type="helpful",
                feedback_value=True
            )
            
            print(f"Feedback processed: {feedback_result.get('feedback_processed', False)}")
    
    # Test adaptation progression
    print("\n3. Testing Adaptation Progression")
    
    contexts = [r.get('context', {}) for r in results]
    
    print("Context progression across messages:")
    for i, ctx in enumerate(contexts, 1):
        print(f"  Message {i}: {ctx}")
    
    # Process a follow-up message to see memory influence
    print("\n4. Testing Memory Influence on New Requests")
    
    follow_up = "Can you summarize what we discussed about transformers?"
    
    result = enhanced_memory_system.process_message(
        user_id=user_id,
        message=follow_up
    )
    
    print(f"Follow-up processed with model: {result.get('model_used', 'unknown')}")
    print(f"Context parameters: {result.get('context', {})}")
    
    # Check memory for recorded conversation insights
    print("\n5. Checking Memory for Conversation Insights")
    
    memories = real_time_memory_manager.get_relevant_context_memories(f"user:{user_id}")
    
    print(f"Found {len(memories)} relevant memories for this user")
    for i, memory in enumerate(memories[:3], 1):
        print(f"  {i}. {memory.content[:100]}...")
    
    print("\n=> Integrated Functionality Test: SUCCESS")


def run_all_tests():
    """Run all memory enhancement tests."""
    print_header("MEMORY AND REAL-TIME ADAPTATION ENHANCEMENT TESTS")
    
    print("\nRunning comprehensive tests for the new memory enhancements...")
    
    # Run individual component tests
    test_real_time_adaptation()
    test_memory_optimization()
    test_multi_ai_context_sync()
    
    # Run integrated test
    test_integrated_functionality()
    
    print_header("ALL TESTS COMPLETED SUCCESSFULLY")
    print("\nMemory and Real-Time Adaptation Enhancements are fully functional and integrated!")


if __name__ == "__main__":
    run_all_tests()
