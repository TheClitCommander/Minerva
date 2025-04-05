# AI Knowledge Repository

The AI Knowledge Repository is a centralized system designed to store and manage shared insights between multiple AI models in the Minerva system. It enables knowledge transfer and trend-based learning across multiple AI instances.

## Overview

The repository serves as a collective memory for AI models, allowing them to:
- Share successful responses and techniques
- Learn from each other's performance
- Identify which models perform best for specific query types
- Improve response quality through collaborative learning

## Core Features

1. **Cross-Model Knowledge Sharing**
   - Stores insights from multiple AI models in a centralized repository
   - Enables access to combined knowledge across all registered models

2. **Historical Performance Tracking**
   - Records effectiveness and user satisfaction metrics
   - Maintains model-specific performance data
   - Helps identify strengths and weaknesses of different models

3. **Adaptive Model Selection**
   - Recommends the best model for specific query types
   - Leverages historical performance data to make intelligent routing decisions
   - Improves response quality by matching queries with specialized models

4. **Efficient Knowledge Retrieval**
   - Implements caching for frequently accessed insights
   - Uses term-based relevance ranking for query matching
   - Provides fast access to the most relevant insights

## Integration Points

The AI Knowledge Repository can be integrated with other Minerva components:

### Multi-AI Coordinator
- **Implemented**: The Multi-AI Coordinator now leverages the repository to select the optimal model for processing user queries
- Insights from past queries guide model selection when confidence is high enough
- Automated feedback capture enhances the repository with each user interaction
- Performance metrics are tracked and used for future routing decisions

### Self-Learning Optimizer
- Contribute performance metrics to the repository
- Use insights to improve self-adjustment algorithms
- Leverage cross-model learning for faster optimization

### Global Feedback Manager
- Connect user feedback directly to stored insights
- Use feedback data to update model performance metrics
- Develop a feedback loop for continuous improvement

## Implementation Status

| Component | Status | Description |
|-----------|--------|-------------|
| Core Repository | ✅ Complete | Main knowledge storage and retrieval functionality |
| Multi-AI Integration | ✅ Complete | Repository-guided model selection in coordinator |
| Self-Learning Integration | 📝 Planned | Sync with self-learning optimizer |
| Feedback Manager Integration | 📝 Planned | Enhanced feedback loop with global manager |
| Real-Time Adaptation | 📝 Planned | Dynamic adjustments based on repository insights |

## Usage Examples

### Registering Models

```python
from ai_decision.ai_knowledge_repository import ai_knowledge_repository

# Register models with the repository
ai_knowledge_repository.register_model("claude")
ai_knowledge_repository.register_model("gpt4")
```

### Storing Insights

```python
# Store a new insight from a model
insight_id = ai_knowledge_repository.store_insight(
    model_name="claude",
    query="How does machine learning work?",
    response="Machine learning is a subset of AI that focuses on algorithms...",
    feedback={"rating": 4.5, "helpful": True},
    context={"user_expertise": "beginner", "session_id": "12345"}
)
```

### Retrieving Insights

```python
# Retrieve relevant insights for a query
insights = ai_knowledge_repository.retrieve_insights(
    query="What is machine learning?",
    limit=5
)

# Process the insights
for insight in insights:
    print(f"Model: {insight['model']}, Relevance: {insight.get('relevance', 0)}")
    print(f"Response: {insight['response']}")
```

### Finding the Best Model

```python
# Get the best model for a specific query
best_model, confidence = ai_knowledge_repository.get_best_model_for_query(
    query="Explain the difference between supervised and unsupervised learning"
)

print(f"Best model: {best_model}, Confidence: {confidence}")
```

### Integration with Multi-AI Coordinator

```python
# Model selection with AI Knowledge Repository in the Multi-AI Coordinator
def _model_selection_decision(self, user_id: str, message: str) -> Dict[str, Any]:
    # Get decision parameters from the global feedback manager
    parameters = self.feedback_manager.get_ai_decision_parameters(user_id, message)
    
    # Check AI Knowledge Repository for best model recommendation
    best_model, confidence = ai_knowledge_repository.get_best_model_for_query(message)
    
    # Use repository recommendation if confidence is high enough
    if best_model and confidence > 0.7:
        models_to_use.append(best_model)
        repository_guided = True
    else:
        # Default model selection logic
        models_to_use.append(default_model)
    
    # Rest of the decision logic...
```

### Recording Feedback with the Repository

```python
# Record feedback and update the repository
def record_feedback(self, user_id, message_id, is_positive, feedback_type, model_used, query, response):
    # Forward to the global feedback manager
    success = self.feedback_manager.record_feedback(
        user_id, message_id, is_positive, feedback_type, model_used
    )
    
    # Update the AI Knowledge Repository
    if success and model_used and query and response:
        # Convert boolean feedback to a rating
        rating = 4.5 if is_positive else 1.5
        
        # Store updated insight
        insight_id = ai_knowledge_repository.store_insight(
            model_name=model_used,
            query=query,
            response=response,
            feedback={"rating": rating, "feedback_type": feedback_type},
            context={"user_id": user_id, "message_id": message_id}
        )
    
    return success
```

## Next Steps

1. **Enhanced Relevance Ranking**: Implement more sophisticated relevance metrics for insight retrieval
2. **Topic Clustering**: Group insights by topic to improve knowledge organization
3. **Adaptive Learning Rate**: Adjust model weights dynamically based on recent performance
4. **Cross-Model Validation**: Verify insights across multiple models for higher confidence
5. **Automated Knowledge Pruning**: Remove outdated or low-quality insights periodically

## Implementation Status

The AI Knowledge Repository has been successfully implemented and tested with basic functionality. Next steps include integrating it with the Multi-AI Coordinator and Self-Learning Optimizer.
