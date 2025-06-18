# Minerva Think Tank System Documentation

## Overview
The Think Tank is Minerva's advanced multi-model blending system that combines responses from various AI models based on their strengths. This is a critical component that must remain functional throughout development.

## Core Components

### 1. Model Selection & Blending
- **Location**: `think-tank-bridge.js`, `minimal_server.py`
- **How it Works**:
  - Multiple AI models are queried simultaneously
  - Responses are scored based on relevance and quality
  - The system blends or selects from these responses
  - Model weights are adjusted based on historical performance

### 2. Response Processing Pipeline
- **Location**: `minerva-chat.js`, `think-tank-metrics.js`
- **How it Works**:
  - Raw model responses are processed and formatted
  - Markdown and code formatting is preserved
  - Citations and sources are verified and attached
  - Response metrics are calculated and displayed

### 3. Metrics and Analytics
- **Location**: `model-metrics.js`, `model-visualization.js`
- **How it Works**:
  - Each model's performance is tracked over time
  - Metrics include accuracy, latency, relevance, and creativity
  - Visualizations show relative model performance
  - Analytics inform future model selection

## Critical Functions

### API Integration Functions
- `queryThinkTank()`: Sends requests to the Think Tank API
- `processModelResponses()`: Handles the responses from various models
- `calculateModelWeights()`: Determines optimal model weighting
- `selectBestResponse()`: Chooses the most appropriate response

### Response Handling Functions
- `handleThinkTankResponse()`: Processes responses from the Think Tank
- `addBotMessageWithModelInfo()`: Displays responses with model metadata
- `updateModelMetrics()`: Updates performance metrics after responses
- `processModelInfo()`: Extracts and processes model information

### Visualization Functions
- `updateModelPerformanceVisualizations()`: Updates charts and graphs
- `renderModelComparisonChart()`: Shows comparative model performance
- `displayModelContributionBreakdown()`: Shows which models contributed to a response
- `logModelEvaluation()`: Records performance data for future analysis

## Integration Points

### Chat System Integration
- Chat interface displays model information with responses
- Think Tank metrics are accessible from the chat interface
- Response quality feedback is sent back to the Think Tank

### Memory System Integration
- Previous model performances influence future selection
- Conversation context informs model selection
- Project-specific model preferences are stored in memory

### Orbital UI Integration
- Model metrics are visualized in the orbital UI
- Individual model agents can be represented as sub-orbs
- Think Tank performance affects central orb visualization

## Implementation Details

### Model Blending Approach
```javascript
// Example model blending logic
function blendModelResponses(responses, weights) {
  // Calculate weighted scores
  const scoredResponses = responses.map((response, i) => ({
    text: response.text,
    score: response.quality * weights[i]
  }));
  
  // Select best response or blend multiple
  return selectOptimalResponse(scoredResponses);
}
```

### Performance Tracking
- Models are evaluated on multiple dimensions
- Historical performance influences future weighting
- User feedback affects model reputation

## Known Limitations
- API rate limits for some models
- Response latency varies between models
- Edge cases where model consensus is low

## Testing Methodology
- Compare responses across different query types
- Measure response quality and relevance
- Test model fallback mechanisms
- Verify metrics accuracy

---

## DO NOT MODIFY WITHOUT TESTING
Any changes to the Think Tank system should be thoroughly tested to ensure:
1. Model blending continues to work properly
2. Response quality remains high
3. Performance metrics are accurately tracked
4. The UI correctly displays model information
