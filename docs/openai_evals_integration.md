# OpenAI Evals Integration with Minerva

This document describes the integration of OpenAI Evals with Minerva's Think Tank mode, which enhances model evaluation, comparison, and selection capabilities.

## Overview

The OpenAI Evals integration provides Minerva with sophisticated tools for evaluating AI model responses, allowing for better model selection, performance tracking, and continuous improvement of the system.

### Key Components

1. **Model Evaluation Manager** - Central component for evaluating model responses using OpenAI Evals
2. **Model Registry Integration** - Enhancements to the model registry for tracking model performance
3. **Think Tank Integration** - Integration with the Multi-AI Coordinator for better model selection

## How It Works

### Model Evaluation Manager

The `ModelEvaluationManager` is a singleton class that manages the evaluation of model responses using OpenAI Evals. It provides methods for:

- Evaluating individual model responses (`evaluate_response`)
- Comparing responses from different models (`compare_responses`)
- Tracking model performance over time (`get_model_performance_history`)
- Ranking models based on their performance (`get_model_rankings`)

```python
from web.model_evaluation_manager import (
    get_evaluation_manager, evaluate_model_response, 
    get_model_rankings, get_model_performance_history
)

# Evaluate a model response
eval_result = evaluate_model_response("gpt4", "What is the capital of France?", "The capital of France is Paris.")

# Get model rankings
rankings = get_model_rankings()
```

### Model Registry Integration

The model registry has been enhanced to work with the evaluation manager, including:

- Methods for evaluating model responses (`evaluate_model_response`)
- Tracking model performance metrics (`update_model_performance`)
- Selecting models based on their evaluation scores (`get_best_models_for_query_type`)

```python
from web.model_registry import (
    evaluate_model_response, update_model_performance, get_best_models_for_query_type
)

# Evaluate a response using the model registry
result = evaluate_model_response("claude", "Explain quantum computing", "Quantum computing is...")

# Update model performance metrics
update_model_performance("claude", {"average_quality": 0.85, "success_rate": 0.95})

# Get best models for a specific query type
best_models = get_best_models_for_query_type("technical", limit=3)
```

### Think Tank Integration

The Multi-AI Coordinator has been updated to use OpenAI Evals when evaluating model responses in Think Tank mode:

- Automatically evaluates model responses using OpenAI Evals
- Adds evaluation metrics to response data
- Uses evaluation scores for model selection

## Evaluation Metrics

The OpenAI Evals integration provides various metrics for evaluating model responses:

- **Overall Score** - A composite score representing the overall quality of the response
- **Correctness** - How factually accurate the response is
- **Relevance** - How relevant the response is to the query
- **Coherence** - How well-structured and coherent the response is
- **Completeness** - Whether the response fully answers the query
- **Conciseness** - How concise and to-the-point the response is

## Using the Integration

### Direct Evaluation

To directly evaluate a model response:

```python
from web.model_evaluation_manager import evaluate_model_response

result = evaluate_model_response("gpt4", "What is the capital of France?", "The capital of France is Paris.")
print(f"Score: {result['overall_score']}")
print(f"Metrics: {result['metrics']}")
```

### Think Tank Mode

When using Think Tank mode, the evaluation is handled automatically:

```python
from web.multi_ai_coordinator import multi_ai_coordinator

result = await multi_ai_coordinator.process_message(
    user_id="user123",
    message="What is the capital of France?",
    mode="think_tank"
)

print(f"Best model: {result['model_used']}")
print(f"Quality score: {result['quality_score']}")
```

## Testing

Two test scripts are provided to demonstrate the integration:

1. `test_evals_integration.py` - Tests the basic evaluation functionality
2. `test_model_registry_evals.py` - Tests the model registry integration

Run these scripts to see the integration in action:

```bash
python test_evals_integration.py
python test_model_registry_evals.py
```

## Benefits

The OpenAI Evals integration provides several benefits to Minerva's Think Tank mode:

1. **Better Model Selection** - More accurate selection of models based on evaluation scores
2. **Performance Tracking** - Better tracking of model performance over time
3. **Continuous Learning** - Ability to adapt to changing model performance
4. **Quality Assurance** - Improved quality control for model responses
5. **Feedback Integration** - Better integration of user feedback with model evaluation

## Future Improvements

Potential future improvements to the OpenAI Evals integration include:

1. **Custom Evaluation Criteria** - Ability to define custom evaluation criteria
2. **User Preference Integration** - Integration with user preferences for model selection
3. **Adaptive Evaluation** - Adaptation of evaluation criteria based on query type
4. **Performance Optimization** - Optimization of evaluation performance for faster response times
5. **Extended Metrics** - Addition of more detailed evaluation metrics
