#!/usr/bin/env python3
"""
AI Coordinator Singleton

This file creates and exports a single instance of the MultiAICoordinator.
It breaks the circular dependency chain by providing a dedicated place for
the coordinator instance that can be imported without circular references.
"""

from web.multi_ai_coordinator import MultiAICoordinator

# Create the singleton instance that will be shared across imports
coordinator = MultiAICoordinator()
Coordinator = coordinator  # Capital C for backward compatibility
print("✅ AI Coordinator singleton initialized and ready for import") 