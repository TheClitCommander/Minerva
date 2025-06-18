# Minerva Enhanced Model Selection System

## Overview

The Enhanced Model Selection System in Minerva provides intelligent, adaptive selection of AI models based on query complexity, historical performance, and user preferences. This system ensures that each user query is handled by the most appropriate AI model, optimizing both response quality and resource utilization.

## Key Components

### 1. Multi-AI Coordinator

The `MultiAICoordinator` class orchestrates the model selection process:

- Analyzes incoming queries for complexity
- Determines the appropriate model(s) to use
- Sets timeout thresholds based on expected processing time
- Manages the parallel execution of selected models
- Evaluates response quality and selects the best result
- Records insights and user feedback to improve future selections

### 2. AI Knowledge Repository

The `AIKnowledgeRepository` provides historical performance data:

- Stores insights about model performance on different query types
- Retrieves relevant insights based on query similarity
- Calculates confidence scores for model recommendations
- Adjusts scores based on recency, relevance, and complexity matching
- Integrates user feedback to improve future recommendations

### 3. Scoring Utilities

The `scoring.py` module contains utility functions for:

- Query complexity estimation
- Confidence threshold calculation
- Model capability matching
- User preference integration
- Recency adjustments
- Default model selection

## How It Works

### Query Processing Flow

1. **Query Analysis**
   - The system analyzes the incoming query to determine its complexity
   - Technical terms and code-related content increase complexity scores
   - Query length contributes to complexity assessment

2. **Model Selection**
   - The AI Knowledge Repository is consulted for model recommendations
   - If confidence exceeds the dynamic threshold, the recommended model is used
   - Otherwise, default models are selected based on complexity
   - User preferences influence the final selection

3. **Response Processing**
   - Selected models generate responses in parallel
   - Response quality is evaluated with complexity-aware scoring
   - The best response is selected and returned to the user

4. **Feedback Integration**
   - User feedback is recorded with query complexity information
   - The feedback updates model confidence scores in the repository
   - Future model selections are improved based on accumulated feedback

## Configuration Options

### Model Capabilities

The system maintains capability profiles for each model:

- `technical_expertise`: Ability to handle technical and specialized topics
- `creative`: Strength in creative and open-ended responses
- `concise`: Ability to provide brief, direct answers
- `depth`: Level of detail and thoroughness (0.0-1.0)
- `speed`: Response generation speed (0.0-1.0)
- `domains`: List of specialized domains where the model excels

### User Preferences

User preferences that influence model selection include:

- `priority`: Speed vs. quality tradeoff (speed, balanced, quality)
- `tone`: Communication style (formal, casual, neutral)
- `length`: Preferred response length (short, medium, long)

## Implementation Details

### Complexity Estimation

Complexity is estimated on a scale of 1.0-10.0 based on:

```python
def estimate_query_complexity(query):
    # Base complexity from length
    complexity = min(5.0, len(query) / 100)
    
    # Add complexity for technical terms
    if contains_technical_terms(query):
        complexity += 3.0
        
    # Add complexity for code elements
    if contains_code_elements(query):
        complexity += 1.0
        
    return min(10.0, complexity)
```

### Dynamic Confidence Thresholds

Confidence thresholds are dynamically calculated:

```python
def calculate_confidence_threshold(complexity):
    # Higher threshold for simpler queries
    # Lower threshold for complex queries
    return max(0.6, 0.8 - (complexity / 40))
```

### Quality Evaluation

Response quality is evaluated considering query complexity:

```python
def evaluate_response_quality(response, message, query_complexity):
    # Base scoring
    score = 0.0
    
    # Length expectations scale with complexity
    expected_length = 100 * query_complexity
    
    # Structure expectations increase with complexity
    expected_structure = determine_structure_expectations(query_complexity)
    
    # Detail expectations based on complexity
    expected_detail = determine_detail_expectations(query_complexity)
    
    # Score various aspects and combine
    return combined_score
```

## Testing

The system includes comprehensive test suites:

- `test_scoring_utilities.py`: Tests individual scoring functions
- `test_enhanced_scoring.py`: Tests the quality evaluation system
- `test_enhanced_model_selection.py`: End-to-end integration tests

## Usage Example

```python
from web.multi_ai_coordinator import MultiAICoordinator

# Create the coordinator
coordinator = MultiAICoordinator()

# Process a message
result = await coordinator.process_message(
    user_id="user123",
    message="Explain quantum computing in simple terms",
    message_id="msg_12345"
)

# Extract the response
response = result["response"]
model_used = result["model_used"]
processing_time = result["processing_time"]

# Record feedback
coordinator.record_feedback(
    user_id="user123",
    message_id="msg_12345",
    is_positive=True,
    feedback_type="general",
    model_used=model_used
)
```

## Performance Considerations

The enhanced model selection system is designed for optimal performance:

- Repository lookups are optimized with caching
- Complexity estimation uses efficient heuristics
- Default model selection provides fast fallback when needed
- Timeout parameters adjust based on expected processing time

By default, the system is tuned to favor balanced performance, with a slight preference for quality over speed. These defaults can be adjusted through user preferences or system configuration.

## Extending the System

To add support for a new AI model:

1. Add the model's capability profile in `scoring.py`
2. Implement a processor for the model in `multi_model_processor.py`
3. Register the model with the coordinator

## Future Improvements

Planned enhancements include:

1. Advanced semantic matching for better insight retrieval
2. Automatic adjustment of model capability profiles based on performance
3. Multi-model response composition for highly complex queries
4. Domain-specific optimization for specialized knowledge areas

The modular architecture makes it easy to extend and enhance the system as new requirements emerge.
