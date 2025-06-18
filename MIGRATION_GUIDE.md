# Think Tank Migration Guide

## Overview

This guide outlines how to migrate from the legacy Think Tank implementation to the new consolidated one. The consolidated implementation integrates all the optimized components while maintaining backward compatibility during the transition period.

## Migration Steps

### 1. Use the New Consolidated Module

```python
# Old approach - DO NOT USE
from web.think_tank_processor import process_with_think_tank

# New approach - USE THIS
from web.think_tank_consolidated import process_with_think_tank
```

### 2. Updated Function Signatures

The consolidated implementation has simplified function signatures with better default handling:

```python
# Old signature
result = process_with_think_tank(
    message, 
    available_models=None, 
    conversation_id=None
)

# New signature
result = process_with_think_tank(
    message,
    conversation_id=None,  
    test_mode=False  # New parameter for testing
)
```

### 3. Enhanced Response Format

The response structure has been enhanced with more detailed model information:

```python
# Response structure
{
    "response": "The blended response text",
    "model_info": {
        "models_used": ["gpt-4", "claude-3", "mistral"],
        "rankings": [
            {
                "model": "gpt-4",
                "score": 0.92,
                "reasoning": "Strong technical accuracy and comprehensive coverage"
            },
            # Other model rankings...
        ],
        "blending": {
            "method": "technical",  # The specialized blending strategy used
            "contributing_models": ["gpt-4", "claude-3"],
            "sections": [
                {"model": "gpt-4", "section": "explanation"},
                {"model": "claude-3", "section": "code_example"}
            ]
        }
    },
    "processing_stats": {
        "time_taken": 2.45,
        "models_used": 3,
        "complexity_score": 0.78,
        "query_type": "technical"
    }
}
```

### 4. New Testing Features

The consolidated implementation supports a dedicated test mode:

```python
# Enable test mode to get detailed debug information
result = process_with_think_tank(message, test_mode=True)

# In API requests, use the X-Test-Mode header
headers = {"X-Test-Mode": "true"}
```

### 5. New API Endpoints

New endpoints have been added to provide more transparency:

```
# New endpoint for query analysis
POST /api/analyze-query
{
  "message": "Your query here"
}

# Enhanced health check with model status
GET /api/health
```

## Backwards Compatibility

For backward compatibility during the transition period:
- A symlink from the old file location to the new implementation has been created
- The deprecated file is kept as `think_tank_processor.py.backup` for reference
- All function signatures maintain compatibility with existing code

## Timeline

- **Immediate**: Start using the consolidated implementation in new code
- **Short-term**: Update all existing references to use the new module
- **Medium-term**: Remove the compatibility symlink after all references are updated
- **Long-term**: Complete removal of the deprecated implementation

## Verification

To verify your code is using the consolidated implementation, check for:
1. Detailed model rankings with reasoning in the response
2. Specialized blending strategies being applied based on query type
3. Enhanced quality evaluation metrics in test mode output
