#!/usr/bin/env python3
"""
Capability Validation Script
Tests the model capabilities system, ranking, and blending directly
"""

import os
import sys
import json
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(str(BASE_DIR))

# Import the ranking function
try:
    from processor.ensemble_validator import rank_responses, _get_model_capabilities
    print("✅ Successfully imported ensemble validator functions")
except Exception as e:
    print(f"❌ Error importing ensemble validator: {e}")
    sys.exit(1)

def validate_model_capabilities():
    """Validate the model capabilities system directly"""
    print("\n===== MODEL CAPABILITIES VALIDATION =====")
    
    try:
        # Get the model capabilities directly
        capabilities = _get_model_capabilities()
        
        print("Model Capability Profiles:")
        for model, scores in capabilities.items():
            print(f"  {model}:")
            for capability, score in scores.items():
                print(f"    {capability}: {score}")
        
        # Validate our key models have capability scores
        key_models = ['gpt-4o', 'claude-3-opus', 'gpt-4', 'claude-3', 'gemini-pro']
        for model in key_models:
            if model in capabilities:
                print(f"✅ Model {model} has capability scores")
            else:
                print(f"❌ Model {model} missing capability scores")
                
        return capabilities
    except Exception as e:
        import traceback
        print(f"❌ Error validating model capabilities: {e}")
        print(traceback.format_exc())
        return None

def test_response_ranking():
    """Test the response ranking system with different query types"""
    print("\n===== RESPONSE RANKING VALIDATION =====")
    
    # Sample responses for testing
    test_responses = {
        "gpt-4o": "Transformers and RNNs (Recurrent Neural Networks) are two fundamental neural network architectures used in natural language processing, with key differences in how they process sequential data.\n\nRNNs process data sequentially, maintaining a hidden state that captures information from previous inputs. This makes them naturally suited for sequential data like text. However, they struggle with long-range dependencies due to the vanishing/exploding gradient problem, and their sequential nature limits parallelization.\n\nTransformers, introduced in the 'Attention is All You Need' paper, use a self-attention mechanism instead of recurrence. This allows them to directly model relationships between all words in a sequence, regardless of their distance. Key advantages include:\n\n1. Parallel processing: Can process entire sequences simultaneously\n2. Better handling of long-range dependencies\n3. More effective capture of contextual relationships\n\nArchitecturally, transformers consist of encoder and decoder blocks with multi-head attention mechanisms, while RNNs use recurrent connections with gates (in variants like LSTM and GRU) to control information flow.\n\nTransformers have largely supplanted RNNs in state-of-the-art NLP models (like BERT, GPT, T5) due to their superior performance, though RNNs remain useful for specific applications, especially with limited computational resources or when sequential processing is explicitly required.",
        
        "claude-3-opus": "# Transformers vs. RNNs in Natural Language Processing\n\nTransformers and Recurrent Neural Networks (RNNs) represent two different architectural approaches to sequence modeling in NLP, with distinct characteristics and capabilities.\n\n## RNNs: Sequential Processing\n\nRNNs process text sequentially (word by word) and maintain a hidden state that acts as a form of memory:\n\n- **Sequential nature**: Process tokens one at a time, with each step depending on previous computations\n- **Memory mechanism**: Use hidden states to remember information from earlier in the sequence\n- **Variants**: Include LSTM (Long Short-Term Memory) and GRU (Gated Recurrent Unit) that address the vanishing gradient problem\n- **Directional flow**: Information flows forward (or bidirectionally in BiRNNs)\n\n### Limitations of RNNs:\n- Cannot be easily parallelized due to their sequential nature\n- Struggle with very long-range dependencies despite LSTM/GRU improvements\n- Training is relatively slow because of sequential processing\n\n## Transformers: Parallel Attention-Based Processing\n\nTransformers, introduced in the \"Attention is All You Need\" paper (2017), take a fundamentally different approach:\n\n- **Parallel processing**: Process the entire sequence at once rather than sequentially\n- **Self-attention mechanism**: Directly model relationships between all words in a sequence regardless of their position\n- **Positional encoding**: Since they process all tokens simultaneously, they require explicit position information\n- **Multi-head attention**: Capture different types of relationships between words\n\n### Advantages of Transformers:\n- Highly parallelizable, enabling more efficient training on GPUs\n- Better at capturing long-range dependencies\n- Scale more effectively to larger datasets and model sizes\n- Support for transfer learning via pretraining (BERT, GPT, etc.)\n\n## Performance Comparison\n\nTransformers have largely replaced RNNs in state-of-the-art NLP systems because:\n\n1. They achieve superior performance on most NLP benchmarks\n2. They can be trained on much larger datasets due to parallelization\n3. They scale better with model size and computational resources\n4. They handle context windows of thousands of tokens effectively\n\nHowever, RNNs may still be preferable in specific scenarios requiring strict sequential processing or when computational resources are limited.",
        
        "gpt-4": "# Transformers vs. RNNs in Natural Language Processing\n\nBoth transformers and Recurrent Neural Networks (RNNs) are architectures used in natural language processing, but they differ significantly in their approach to handling sequential data.\n\n## RNNs: Sequential Processing\n\nRNNs process text as a sequence, one token at a time, maintaining a hidden state that carries information from previous steps:\n\n- **Sequential nature**: Process words one after another, with each state dependent on the previous one\n- **Memory mechanism**: Use internal memory (hidden state) to remember information from earlier in the sequence\n- **Variants**: Include LSTM (Long Short-Term Memory) and GRU (Gated Recurrent Unit) designed to address issues with long-term dependencies\n\n**Limitations**:\n- Struggle with long sequences due to vanishing/exploding gradients\n- Cannot be easily parallelized due to their sequential nature\n- Have difficulty capturing dependencies between distant words\n\n## Transformers: Parallel Attention-Based Processing\n\nTransformers, introduced in the \"Attention is All You Need\" paper (2017), take a fundamentally different approach:\n\n- **Parallel processing**: Process the entire sequence at once rather than step by step\n- **Self-attention mechanism**: Allow the model to focus on different parts of the input sequence regardless of position\n- **No recurrence**: Don't rely on sequential processing, using positional encodings instead\n\n**Advantages**:\n- Highly parallelizable, making training much faster\n- Better at capturing long-range dependencies\n- More effective for transfer learning and large-scale pre-training\n\n## Key Differences\n\n1. **Processing approach**: Sequential (RNNs) vs. parallel (Transformers)\n2. **Computational efficiency**: Transformers can be trained much faster with GPUs/TPUs\n3. **Context handling**: Transformers can directly model relationships between any words in a sequence\n4. **Scalability**: Transformers scale better to larger datasets and model sizes\n5. **State-of-the-art performance**: Transformer-based models (BERT, GPT, T5) have largely replaced RNN-based approaches\n\nWhile transformers have become dominant in most NLP tasks, RNNs still have applications in certain scenarios, particularly when sequential processing is inherently required or when working with limited computational resources."
    }
    
    # Test different query types
    query_types = [
        {
            "query": "Explain the differences between transformers and RNNs in natural language processing.",
            "tags": {"domains": ["technical", "ai", "nlp"], "request_types": ["explanation", "comparison"]},
            "description": "Technical/AI Query"
        },
        {
            "query": "Write a poem about the changing seasons.",
            "tags": {"domains": ["creative", "writing"], "request_types": ["creative", "poem"]},
            "description": "Creative Writing Query"
        },
        {
            "query": "What ethical principles should guide AI development?",
            "tags": {"domains": ["ethics", "philosophy"], "request_types": ["reasoning", "analysis"]},
            "description": "Ethical Reasoning Query"
        }
    ]
    
    # Test ranking system with our technical query
    technical_query = query_types[0]
    print(f"\nTesting ranking for: {technical_query['description']}")
    print(f"Query: {technical_query['query']}")
    
    try:
        # Call the ranking function
        rankings = rank_responses(
            responses=test_responses,
            original_query=technical_query['query'],
            query_tags=technical_query['tags']
        )
        
        # Display rankings
        print("\nModel Rankings:")
        for i, ranking in enumerate(rankings):
            print(f"  {i+1}. {ranking['model']} - Score: {ranking.get('score', 'N/A')}")
            reason = ranking.get('reason', 'No reasoning provided')
            print(f"     Reason: {reason[:150]}..." if len(reason) > 150 else f"     Reason: {reason}")
            
        # Validate ranking has all the expected fields
        expected_fields = ['model', 'score', 'reason']
        for field in expected_fields:
            if field in rankings[0]:
                print(f"✅ Rankings include '{field}' field")
            else:
                print(f"❌ Rankings missing '{field}' field")
                
        # Check if capability scores are being applied
        if any('capability' in ranking.get('reason', '').lower() for ranking in rankings):
            print("✅ Rankings show evidence of capability-based scoring")
        else:
            print("❌ No evidence of capability-based scoring in rankings")
        
        return rankings
    except Exception as e:
        import traceback
        print(f"❌ Error testing response ranking: {e}")
        print(traceback.format_exc())
        return None

def main():
    # Force real API mode
    os.environ["MINERVA_TEST_MODE"] = "false"
    
    print("\n🔍 MINERVA MODEL CAPABILITIES AND RANKING VALIDATION 🔍")
    
    # Load .env file for API keys if needed
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    # Remove quotes if present
                    value = value.strip("'\"")
                    os.environ[key] = value
    
    # Validate model capabilities
    capabilities = validate_model_capabilities()
    
    # Test response ranking
    if capabilities:
        rankings = test_response_ranking()
    
    # Summarize validation results
    print("\n===== VALIDATION SUMMARY =====")
    if capabilities:
        print("✅ Model capability profiles validated successfully")
    else:
        print("❌ Model capability profiles validation failed")
    
    if 'rankings' in locals() and rankings:
        print("✅ Response ranking system validated successfully")
    else:
        print("❌ Response ranking system validation failed")

if __name__ == "__main__":
    main()
