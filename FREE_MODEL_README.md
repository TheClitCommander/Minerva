# Minerva Think Tank - Free Model Configuration

This document explains how to use Minerva's Think Tank mode with free and open-source models only, avoiding API costs during development.

## Overview

The Think Tank mode has been optimized to work exclusively with free and open-source models, with the option to re-enable API-based models when needed. This implementation ensures that all models contribute effectively to response generation while avoiding costs associated with API calls.

## Available Free Models

The following free and open-source models are available for use with Think Tank mode:

- **Mistral 7B** - A powerful open-source model with good all-around capabilities
- **GPT4All** - A locally-runnable open-source assistant
- **LLaMA 2** - Meta's powerful open-source model
- **DistilGPT** - A lightweight distilled model
- **Falcon** - An open-source model with good reasoning capabilities
- **Bloom** - A multilingual open-source model

## Usage

### Toggling API Models

To easily toggle between free-only and mixed mode, use the provided utility script:

```bash
# Show current status
python toggle_api_models.py --status

# Disable API models (use free models only)
python toggle_api_models.py --disable

# Enable API models (when you're ready to use paid APIs)
python toggle_api_models.py --enable

# Test the configuration with a sample query
python toggle_api_models.py --disable --test "What is the capital of France?"
```

### Using Think Tank in Your Code

```python
from web.think_tank_processor import process_with_think_tank
from web.free_model_config import toggle_api_models

# To use only free models
toggle_api_models(False)

# Process a query with Think Tank
response = process_with_think_tank("Your query here")
print(response)

# Later, if you want to enable API models
toggle_api_models(True)
```

## Testing and Validation

A comprehensive test suite is provided to validate that all free models are contributing to Think Tank responses:

```bash
# Run the test suite
python test_think_tank_free_models.py
```

The test generates a detailed report showing model usage, response quality, and processing time metrics.

## Logging and Debugging

Detailed logging has been implemented to track model usage and performance:

- **Model Selection**: Logs which models are selected for each query
- **Processing Time**: Tracks how long each model takes to process a query
- **Model Types**: Distinguishes between free and API-based models
- **Response Quality**: Shows quality scores for each model's response
- **Ranking Results**: Displays how models were ranked for each query

By default, logs are saved to `think_tank_test.log` and `think_tank_free_model_test.log`.

## Implementation Details

The free model optimization is implemented across several files:

- **web/free_model_config.py**: Central configuration for free model settings
- **web/think_tank_processor.py**: Updated to prioritize free models
- **web/multi_model_processor.py**: Enhanced with additional free model processors
- **test_think_tank_free_models.py**: Comprehensive testing framework
- **toggle_api_models.py**: Utility script for toggling API models

## Performance Considerations

When running with only free models, you may notice slight differences in response quality compared to API models. The system has been calibrated to provide the best possible responses from the available free models, with LLaMA 2 and Mistral 7B typically producing the highest-quality outputs.

## Future Improvements

Planned improvements to the free model implementation include:

1. Adding more fine-tuned free models for specific domains
2. Implementing better local model hosting integration
3. Improving model capability profiles based on benchmark results
4. Adding cost tracking for when API models are enabled
