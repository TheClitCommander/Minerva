# Minerva AI Model Scoring and Selection System

## Overview

Minerva's AI model scoring and selection system has been enhanced to provide more intelligent decision-making when choosing which AI models to use for different types of queries. This document explains the key components and the algorithmic approach used to optimize the model selection process.

## Key Components

### 1. Query Complexity Analysis

The system now implements sophisticated query complexity analysis to determine the appropriate model(s) for each query:

- **Complexity Factors**:
  - Message length (longer messages typically indicate more complex queries)
  - Technical terminology detection (identifies specialized language)
  - Domain-specific indicators (recognizes subject matter indicators)

- **Dynamic Confidence Thresholds**:
  - Higher thresholds for simple queries (requiring more certainty)
  - Lower thresholds for complex queries (allowing more experimental approaches)
  - Adjustable based on user preferences and priorities

### 2. Historical Performance Integration

The AI Knowledge Repository plays a critical role in model selection by providing insights from past interactions:

- **Performance-Based Scoring**:
  - Tracks model performance on similar queries
  - Weights recent performance higher than older performance
  - Considers feedback type and relevance to the current query

- **Contextual Metadata**:
  - Stores query complexity with each insight
  - Tracks relevance tags for better context matching
  - Maintains user preference compatibility data

### 3. Advanced Quality Evaluation

Response quality evaluation has been enhanced to consider query complexity and model strengths:

- **Complexity-Adjusted Scoring**:
  - Expects longer, more detailed responses for complex queries
  - Considers structure and organization appropriate to query complexity
  - Evaluates depth of reasoning based on query requirements

- **Model Capability Matching**:
  - Identifies model-specific strengths (technical, creative, concise)
  - Provides scoring bonuses when models' strengths match query needs
  - Penalizes inappropriate model selection based on historical data

## Algorithm Details

### Model Selection Algorithm

1. **Query Analysis**:
   ```python
   def analyze_query(message):
       # Analyze message length
       complexity = min(10.0, len(message) / 100)
       
       # Check for technical terms
       if contains_technical_terms(message):
           complexity += 3.0
           
       # Domain-specific adjustments
       if contains_code_elements(message):
           complexity += 1.0
           
       return min(10.0, complexity)
   ```

2. **Confidence Threshold Calculation**:
   ```python
   def calculate_confidence_threshold(complexity):
       # Higher threshold for simpler queries
       # Lower threshold for complex queries
       return max(0.6, 0.8 - (complexity / 40))
   ```

3. **Model Selection Decision**:
   ```python
   def model_selection_decision(message, user_preferences):
       complexity = analyze_query(message)
       confidence_threshold = calculate_confidence_threshold(complexity)
       
       # Check repository for insights
       best_model, confidence = repository.get_best_model(message, complexity)
       
       if confidence >= confidence_threshold:
           return [best_model]
       else:
           # Smart fallback based on complexity
           return get_default_models(complexity)
   ```

### Quality Evaluation Algorithm

The quality evaluation takes into account query complexity when scoring responses:

```python
def evaluate_response_quality(response, message, complexity):
    # Base scoring factors
    length_score = score_length(response, expected_length=complexity * 100)
    structure_score = score_structure(response, min_expected=complexity / 2)
    
    # Complexity-based expectations
    if complexity > 7:  # Highly complex
        expect_technical_details = True
        expect_deep_reasoning = True
    elif complexity > 4:  # Moderately complex
        expect_technical_details = True
        expect_deep_reasoning = False
    else:  # Simple query
        expect_technical_details = False
        expect_deep_reasoning = False
        
    # Score based on expectations
    detail_score = score_detail_level(response, expect_technical_details)
    reasoning_score = score_reasoning(response, expect_deep_reasoning)
    
    return combine_scores(length_score, structure_score, detail_score, reasoning_score)
```

## Feedback Integration

User feedback is now integrated more deeply into the model selection process:

1. **Feedback Storage**:
   - Each feedback entry includes complexity information
   - Relevance tags categorize feedback for better retrieval
   - Context information tracks user preferences at time of feedback

2. **Performance Learning**:
   - Models gain affinity scores for different query types
   - Positive feedback reinforces model selection for similar queries
   - Negative feedback reduces the likelihood of using the same model

3. **Continuous Improvement**:
   - System automatically adjusts selection parameters based on feedback
   - Query complexity estimation improves over time
   - Model capability profiles become more accurate with usage

## Benefits

The enhanced model scoring and selection system provides several benefits:

1. **Improved Response Quality**:
   - Better matched models for each query type
   - More appropriate response complexity for each query
   - Better handling of technical vs. simple queries

2. **Resource Optimization**:
   - Uses more advanced models only when necessary
   - Prioritizes faster models for simple queries
   - Balances speed and quality based on query requirements

3. **Learning Capability**:
   - System improves over time through feedback
   - Adapts to changing model capabilities
   - Customizes selections based on user preferences

## Testing and Validation

The enhanced scoring system has been tested with various query types:

- **Simple queries** (e.g., "What's the capital of France?")
- **Medium complexity queries** (e.g., "Explain how photosynthesis works")
- **Complex technical queries** (e.g., "Describe neural network architecture details")

Test results show improved model selection accuracy and better quality scoring that matches expected response characteristics for each query type.

## Future Enhancements

Planned future enhancements include:

1. **Advanced semantic matching** for better insight retrieval
2. **User preference profiling** for personalized model selection
3. **Domain-specific optimization** for specialized knowledge areas
4. **Multi-model response composition** for complex queries

---

The enhanced model scoring and selection system represents a significant step forward in Minerva's ability to provide high-quality, appropriate responses across a wide range of query types and complexity levels.
