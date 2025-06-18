# Minerva Advanced AI Orchestration System

## Overview

The Advanced AI Orchestration System is a sophisticated enhancement to Minerva that enables intelligent model selection, parallel processing, and response blending. This system transforms Minerva from a single-model processor into a true AI orchestrator that can dynamically select the most appropriate models for different tasks, run multiple models in parallel, and blend their insights to create superior responses.

## Key Components

### 1. Advanced Model Router (`advanced_model_router.py`)

The core router implements sophisticated logic for:

- **Task Classification**: Identifies query type, complexity, and intent
- **Dynamic Model Selection**: Chooses optimal AI models based on capability, speed, and cost
- **Parallel Execution**: Runs queries against multiple AI models simultaneously
- **Response Ranking**: Evaluates model responses using coherence, correctness, and completeness
- **Multi-Model Response Blending**: Merges insights from multiple models into a cohesive response

### 2. Integration Layer (`router_integration.py`)

Bridges the new routing system with Minerva's existing architecture:

- **Seamless Integration**: Connects to existing processors and coordinators
- **Graceful Degradation**: Falls back to legacy processing if needed
- **API Compatibility**: Maintains existing API contracts

### 3. API Endpoint

Added a dedicated API endpoint for accessing the advanced routing capabilities:

```
POST /api/v1/advanced-think-tank
```

## Task Classification System

The router classifies queries into categories:

| Task Type    | Example                                         | Preferred Models              |
|--------------|------------------------------------------------|------------------------------|
| fact_simple  | "What is the capital of France?"               | GPT-4o-mini, Cohere          |
| explanation  | "Explain how photosynthesis works."            | GPT-4o, Claude-3-Opus        |
| technical    | "Write a Python function for Fibonacci."       | GPT-4o, Mistral              |
| creative     | "Write a poem about AI."                       | Claude-3-Opus, GPT-4o        |
| comparison   | "Compare machine learning vs. deep learning."  | GPT-4o, Claude-3-Opus, Mistral|
| reasoning    | "Analyze ethical implications of AI in healthcare." | GPT-4o, Claude-3-Opus    |
| research     | "Comprehensive overview of quantum computing." | Claude-3-Opus, GPT-4o        |
| general      | Fallback for unclassified queries              | GPT-4o, Claude-3-Haiku       |

## Model Capabilities System

Each model has capability ratings (1-10) across different dimensions:

```python
MODEL_CAPABILITIES = {
    "gpt-4o": {
        "technical": 9,
        "creative": 8,
        "reasoning": 9,
        "factual": 8,
        "explanation": 9,
        "speed": 7,
        "cost": 4
    },
    "claude-3-opus": {
        "technical": 8,
        "creative": 9,
        "reasoning": 9,
        "factual": 8,
        "explanation": 9,
        "speed": 6,
        "cost": 3
    },
    # Additional models...
}
```

## Response Blending Logic

The system determines when to blend responses based on:

1. Task type (always blend for comparisons)
2. Query complexity (blend for complex queries)
3. Response quality (blend when multiple models provide high-quality insights)

Blending strategies are specialized for different task types:
- Technical responses prioritize code blocks and technical details
- Creative responses preserve stylistic elements
- Explanation responses ensure comprehensive coverage
- Comparison responses include perspectives from multiple models

## Using the Advanced Router

### API Request Format

```json
{
  "user_id": "string",  
  "message": "string",  
  "conversation_id": "string"  
}
```

### API Response Format

```json
{
  "response": "string",
  "model_info": {
    "task_type": "string",
    "complexity": 7,
    "tags": ["tag1", "tag2"],
    "models_used": ["model1", "model2"],
    "best_model": "model1",
    "response_source": "blended",
    "blended": true
  }
}
```

### Test Mode

Add the `X-Test-Mode: true` header to get additional debugging information:

```json
{
  "response": "...",
  "model_info": { ... },
  "debug_info": {
    "timestamp": "2025-03-08T18:05:59-05:00",
    "user_id": "test_user",
    "conversation_id": "test_123",
    "message_length": 120
  }
}
```

## Testing

Two test scripts are provided:

1. **`test_advanced_router.py`**: Tests the core routing logic
2. **`test_advanced_api.py`**: Tests the API integration

Run the API test:
```bash
python3 test_advanced_api.py
```

Or test a specific query:
```bash
python3 test_advanced_api.py "Write a function to calculate prime numbers in Python"
```

## Implementation Details

The system is designed to be modular and extensible:

- New task types can be added by updating the `TASK_TYPES` dictionary
- New models can be integrated by updating the `MODEL_CAPABILITIES` and `MODEL_FUNCTIONS` mappings
- Different blending strategies can be implemented for specialized tasks

## Future Enhancements

Planned improvements include:

1. **Learning from Feedback**: Adjusting model selection based on user feedback
2. **Cost Optimization**: Dynamically selecting models based on budget constraints
3. **Adaptive Complexity Detection**: Improved query complexity estimation
4. **Custom Blending Strategies**: Additional specialized blending for different domains
5. **Cross-Model Follow-ups**: Allowing models to ask questions of each other

---

*This implementation creates a self-improving system where user queries are intelligently routed to the most appropriate AI models based on content analysis, resulting in higher quality responses tailored to the specific requirements of each query.*
