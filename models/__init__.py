#!/usr/bin/env python3
"""
Minerva Model Clients

This package contains AI model client implementations for different providers.
Each client handles the specific API integration for its respective service.
"""

from .base_client import BaseModelClient

# Import specific clients when available
try:
    from .openai_client import OpenAIClient
except ImportError:
    OpenAIClient = None

try:
    from .anthropic_client import AnthropicClient
except ImportError:
    AnthropicClient = None

try:
    from .mistral_client import MistralClient
except ImportError:
    MistralClient = None

try:
    from .huggingface_client import HuggingFaceClient
except ImportError:
    HuggingFaceClient = None

__all__ = [
    'BaseModelClient',
    'OpenAIClient',
    'AnthropicClient', 
    'MistralClient',
    'HuggingFaceClient'
] 