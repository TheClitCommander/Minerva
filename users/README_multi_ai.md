# Multi-AI Coordination System

This document describes the Multi-AI Coordination System implemented in Minerva, which enables real-time feedback sharing and preference synchronization across all AI components.

## Overview

The Multi-AI Coordination System consists of two main components:

1. **Global Feedback Manager** - Centralized feedback collection and distribution
2. **Multi-AI Coordinator** - AI model selection and coordination

These components work together to ensure that user feedback, preferences, and response adjustments are shared across all AI models in real-time, creating a more consistent and personalized experience.

## Global Feedback Manager

The Global Feedback Manager serves as a central hub for collecting, storing, and distributing user feedback across all AI components. It ensures that preferences are synchronized in real-time.

### Key Features

- **Centralized Feedback Collection**: Records user feedback in a standardized format
- **Real-time Distribution**: Notifies all registered AI instances of feedback and preference changes
- **Preference Synchronization**: Ensures all AI models have access to the latest user preferences
- **AI Instance Registration**: Allows AI instances to register for updates
- **Decision Parameters**: Provides intelligent decision parameters for AI model selection

### Usage

```python
from users.global_feedback_manager import global_feedback_manager

# Record feedback with metadata
global_feedback_manager.record_feedback(
    user_id="user123",
    message_id="msg_456",
    is_positive=True,
    feedback_type="tone",
    ai_instance_id="claude-instance-1"
)

# Update user preferences
global_feedback_manager.update_user_preference(
    user_id="user123",
    preference_type="response_tone",
    value="formal"
)

# Get AI decision parameters
parameters = global_feedback_manager.get_ai_decision_parameters(
    user_id="user123",
    message="Tell me about quantum computing"
)
```

## Multi-AI Coordinator

The Multi-AI Coordinator manages multiple AI models, decides which models to use for each query, and selects the best response based on quality metrics and user preferences.

### Key Features

- **Model Registration**: Allows different AI model processors to register
- **Dynamic Model Selection**: Chooses appropriate models based on query complexity and user preferences
- **Quality Evaluation**: Evaluates responses for quality and relevance
- **Feedback Integration**: Records feedback and associates it with specific models
- **Adaptive Processing**: Adjusts processing parameters based on user preferences

### Usage

```python
from web.multi_ai_coordinator import multi_ai_coordinator

# Register model processors
multi_ai_coordinator.register_model_processor("claude", claude_processor_func)
multi_ai_coordinator.register_model_processor("openai", openai_processor_func)

# Process a message
result = await multi_ai_coordinator.process_message(
    user_id="user123",
    message="Explain the theory of relativity",
    message_id="msg_789"
)

# Record feedback
multi_ai_coordinator.record_feedback(
    user_id="user123",
    message_id=result["message_id"],
    is_positive=True,
    feedback_type="general",
    model_used=result["model_used"]
)
```

## Integration with User Preferences

The Multi-AI Coordination System seamlessly integrates with Minerva's existing user preference system:

- **Retrieval Depth**: Influences model selection and response processing time
- **Response Tone**: Applied consistently across all AI responses
- **Response Structure**: Formatting applied after selecting the best response
- **Response Length**: Controls truncation and detail level across all AIs

## API Endpoints

New and updated API endpoints support the Multi-AI Coordination System:

- **/api/user/feedback** - Records user feedback and distributes it to all AI instances
- **/api/user/preferences/update** - Updates multiple preferences and syncs across AIs

## Decision Flow

1. User sends a message
2. `multi_ai_coordinator` gets decision parameters from `global_feedback_manager`
3. Based on parameters, coordinator selects appropriate AI models
4. Selected models process the message
5. Coordinator evaluates responses and selects the best one
6. Response is formatted according to user preferences
7. User provides feedback, which is distributed to all AI instances
8. Preferences are automatically adjusted based on feedback patterns

## Implementation Details

The implementation follows these key principles:

1. **Loose Coupling**: Components interact through well-defined interfaces
2. **Real-time Updates**: Changes are propagated immediately
3. **Centralized State**: Single source of truth for preferences
4. **Extensibility**: Easy to add new AI models or preference types

## Testing

The system includes comprehensive test functions:

- `test_global_feedback_manager()` - Tests feedback recording and distribution
- `test_coordinator()` - Tests model selection and processing

To run the tests, execute:

```python
# For GlobalFeedbackManager
python -m users.global_feedback_manager

# For MultiAICoordinator
python -m web.multi_ai_coordinator
```
