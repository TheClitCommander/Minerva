#!/usr/bin/env python3
"""
Create stub files for missing dependencies to enable testing.
"""

import os
import sys

def create_dir_if_not_exists(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def create_file_if_not_exists(path, content=""):
    """Create file if it doesn't exist."""
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(content)
        print(f"Created file: {path}")

def main():
    """Create necessary stub files and directories."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create required directories
    dirs = [
        "memory",
        "ai_decision",
        "users",
        "web"
    ]
    
    for d in dirs:
        create_dir_if_not_exists(os.path.join(base_dir, d))
    
    # Create stub files for missing modules
    
    # Memory Manager
    create_file_if_not_exists(
        os.path.join(base_dir, "memory", "memory_manager.py"),
        """
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import uuid

class MemoryItem:
    def __init__(self, content, source, category, importance=1, tags=None):
        self.id = str(uuid.uuid4())
        self.content = content
        self.source = source
        self.category = category
        self.importance = importance
        self.tags = tags or []
        self.created_at = datetime.now()
        self.expires_at = None
        self.metadata = {}

class ConversationMemory:
    def __init__(self, user_id):
        self.conversation_id = str(uuid.uuid4())
        self.user_id = user_id
        self.created_at = datetime.now()
        self.messages = []
        self.metadata = {}

class MemoryManager:
    def __init__(self):
        self.memories = {}
        self.conversations = {}
    
    def add_memory(self, content, source, category, importance=1, tags=None, 
                  expires_at=None, metadata=None):
        memory = MemoryItem(content, source, category, importance, tags)
        memory.expires_at = expires_at
        memory.metadata = metadata or {}
        self.memories[memory.id] = memory
        return memory
    
    def create_conversation(self, user_id):
        conversation = ConversationMemory(user_id)
        self.conversations[conversation.conversation_id] = conversation
        return conversation

# Create singleton instance
memory_manager = MemoryManager()
"""
    )
    
    # Web Multi-AI Coordinator
    create_file_if_not_exists(
        os.path.join(base_dir, "web", "multi_ai_coordinator.py"),
        """
class MultiAICoordinator:
    def __init__(self):
        self._override_model_selection = None

# Create singleton instance
multi_ai_coordinator = MultiAICoordinator()
"""
    )
    
    # Users Global Feedback Manager
    create_file_if_not_exists(
        os.path.join(base_dir, "users", "global_feedback_manager.py"),
        """
class GlobalFeedbackManager:
    def __init__(self):
        self.feedback = {}
    
    def record_feedback(self, user_id, message_id, feedback_type, feedback_value):
        if user_id not in self.feedback:
            self.feedback[user_id] = {}
        
        self.feedback[user_id][message_id] = {
            "type": feedback_type,
            "value": feedback_value,
            "timestamp": None
        }
        
        return True

# Create singleton instance
global_feedback_manager = GlobalFeedbackManager()
"""
    )
    
    # Users Response Formatter
    create_file_if_not_exists(
        os.path.join(base_dir, "users", "response_formatter.py"),
        """
class ResponseFormatter:
    def __init__(self):
        self.formats = {}

# Create singleton instance
response_formatter = ResponseFormatter()
"""
    )
    
    # AI Decision Maker and Decision Tree
    create_file_if_not_exists(
        os.path.join(base_dir, "ai_decision", "context_decision_tree.py"),
        """
class ContextDecisionTree:
    def __init__(self):
        pass
    
    def analyze_context(self, message):
        return {
            "detail_level": "balanced",
            "tone": "neutral",
            "length": "standard"
        }

# Create singleton instance
decision_tree = ContextDecisionTree()
"""
    )
    
    create_file_if_not_exists(
        os.path.join(base_dir, "ai_decision", "ai_decision_maker.py"),
        """
class AIDecisionMaker:
    def __init__(self):
        pass

# Create singleton instance
ai_decision_maker = AIDecisionMaker()
"""
    )
    
    create_file_if_not_exists(
        os.path.join(base_dir, "ai_decision", "ai_model_switcher.py"),
        """
class AIModelSwitcher:
    def __init__(self):
        pass
    
    def select_model(self, context):
        return "claude-light"

# Create singleton instance
model_switcher = AIModelSwitcher()
"""
    )
    
    # Users Adaptive Response Optimizer
    create_file_if_not_exists(
        os.path.join(base_dir, "users", "adaptive_response_optimizer.py"),
        """
class AdaptiveResponseOptimizer:
    def __init__(self):
        # Optimization parameters
        self.optimization_thresholds = {
            "confidence_required": 0.5,
            "feedback_count_required": 5,
            "adaptation_rate": 0.1,
            "max_adjustment": 0.3
        }

# Create singleton instance
adaptive_response_optimizer = AdaptiveResponseOptimizer()
"""
    )
    
    # Users Feedback Analysis
    create_file_if_not_exists(
        os.path.join(base_dir, "users", "feedback_analysis.py"),
        """
class FeedbackAnalysis:
    def __init__(self):
        pass

# Create singleton instance
feedback_analysis = FeedbackAnalysis()
"""
    )
    
    print("\nStub files created successfully. You can now run the tests.")

if __name__ == "__main__":
    main()
