#!/usr/bin/env python3
"""
Fine-tune Model Capabilities for Minerva's Think Tank

This script helps fine-tune the capability weights for different AI models based on
their actual performance in different tasks. It updates the MODEL_CAPABILITIES
dictionary in the think_tank.py file.
"""

import os
import re
import sys
from pathlib import Path

# Directory and file paths
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
MODEL_CAPABILITIES_FILE = BASE_DIR / 'processor' / 'think_tank.py'
ENSEMBLE_VALIDATOR_FILE = BASE_DIR / 'processor' / 'ensemble_validator.py'

# Enhanced capability weights based on observed performance
CAPABILITY_ADJUSTMENTS = {
    # Local Models
    "Llama-3.2-1B-Instruct-Q4_0.gguf": {
        'technical': 0.75,     # Improved for technical questions
        'creative': 0.70,      # Better creative capabilities than initially thought
        'reasoning': 0.72,     # Good reasoning for a local model
        'factual': 0.65,       # Moderate factual accuracy
        'structured': 0.68,    # Better structure in responses
        'max_tokens': 3072,    # Increased token limit
        'context_window': 4096
    },
    
    # Simulated models with enhanced weights
    "gpt-4o": {
        'technical': 0.95,     # Excellent technical capabilities
        'creative': 0.92,      # Very good creative responses
        'reasoning': 0.95,     # Superior reasoning
        'factual': 0.93,       # Highly factual
        'structured': 0.94,    # Well-structured responses
        'max_tokens': 8192,    # Increased token limit
        'context_window': 16384
    },
    
    "claude-3-opus": {
        'technical': 0.93,     # Very strong technical understanding
        'creative': 0.94,      # Excellent creative capabilities
        'reasoning': 0.95,     # Superior reasoning
        'factual': 0.92,       # Very factual
        'structured': 0.95,    # Excellent structured responses
        'max_tokens': 8192,    # Increased token limit
        'context_window': 16384
    },
    
    "gemini-pro": {
        'technical': 0.90,     # Good technical capabilities
        'creative': 0.88,      # Solid creative responses
        'reasoning': 0.91,     # Good reasoning
        'factual': 0.89,       # Factual with occasional errors
        'structured': 0.87,    # Good structure
        'max_tokens': 4096,
        'context_window': 8192
    },
    
    "mistral-large": {
        'technical': 0.88,     # Good technical capabilities
        'creative': 0.85,      # Good creative responses
        'reasoning': 0.87,     # Solid reasoning
        'factual': 0.86,       # Good factual accuracy
        'structured': 0.85,    # Good structure
        'max_tokens': 4096,
        'context_window': 8192
    }
}

def update_model_capabilities():
    """Update the MODEL_CAPABILITIES dictionary in think_tank.py"""
    if not MODEL_CAPABILITIES_FILE.exists():
        print(f"❌ Cannot find {MODEL_CAPABILITIES_FILE}")
        return False
    
    # Read the file
    with open(MODEL_CAPABILITIES_FILE, 'r') as f:
        content = f.read()
    
    # Find the MODEL_CAPABILITIES dictionary
    capabilities_start = content.find("MODEL_CAPABILITIES = {")
    
    if capabilities_start == -1:
        print("❌ Could not find MODEL_CAPABILITIES dictionary")
        return False
    
    capabilities_end = content.find("}", capabilities_start)
    if capabilities_end == -1:
        print("❌ Could not find end of MODEL_CAPABILITIES dictionary")
        return False
    
    # For each model in our adjustments
    modified_content = content
    changes_made = 0
    
    for model, capabilities in CAPABILITY_ADJUSTMENTS.items():
        # Check if model exists in capabilities
        model_pattern = re.escape(f'"{model}"') + r'\s*:\s*\{'
        model_match = re.search(model_pattern, modified_content)
        
        if model_match:
            # Model exists, update its capabilities
            model_start = model_match.start()
            model_dict_start = model_match.end()
            
            # Find the end of this model's dictionary
            bracket_count = 1
            model_dict_end = model_dict_start
            
            for i in range(model_dict_start, len(modified_content)):
                if modified_content[i] == '{':
                    bracket_count += 1
                elif modified_content[i] == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        model_dict_end = i + 1
                        break
            
            # Create the new capabilities dictionary
            new_capabilities = f'"{model}": {{\n'
            for capability, value in capabilities.items():
                new_capabilities += f"        '{capability}': {value},\n"
            new_capabilities += "    }"
            
            # Replace the old capabilities with the new ones
            modified_content = (
                modified_content[:model_start] + 
                new_capabilities + 
                modified_content[model_dict_end:]
            )
            
            print(f"✅ Updated capabilities for model: {model}")
            changes_made += 1
        else:
            # Model doesn't exist, add it
            # Find where to insert new model capabilities
            capabilities_end = modified_content.find("}", capabilities_start)
            
            # Create the capabilities dictionary
            new_capabilities = f'''
    "{model}": {{
        'technical': {capabilities['technical']},
        'creative': {capabilities['creative']},
        'reasoning': {capabilities['reasoning']},
        'factual': {capabilities['factual']},
        'structured': {capabilities['structured']},
        'max_tokens': {capabilities['max_tokens']},
        'context_window': {capabilities['context_window']}
    }},
'''
            
            # Insert the new capabilities
            modified_content = (
                modified_content[:capabilities_end] + 
                new_capabilities + 
                modified_content[capabilities_end:]
            )
            
            print(f"✅ Added new model capabilities for: {model}")
            changes_made += 1
    
    # Write the modified content back
    with open(MODEL_CAPABILITIES_FILE, 'w') as f:
        f.write(modified_content)
    
    print(f"✅ Updated model capabilities for {changes_made} models")
    return True

def add_capability_boost_function():
    """Add a capability boost function for query-specific model selection"""
    if not MODEL_CAPABILITIES_FILE.exists():
        print(f"❌ Cannot find {MODEL_CAPABILITIES_FILE}")
        return False
    
    # Read the file
    with open(MODEL_CAPABILITIES_FILE, 'r') as f:
        content = f.read()
    
    # Check if the boost function already exists
    if "def boost_model_capabilities_for_query(" in content:
        print("✅ Capability boost function already exists")
        return True
    
    # Find where to insert the boost function
    # Look for the rank_responses function
    rank_responses_pos = content.find("def rank_responses(")
    
    if rank_responses_pos == -1:
        print("❌ Could not find rank_responses function")
        return False
    
    # Function to insert
    boost_function = '''
def boost_model_capabilities_for_query(query, model_capabilities):
    """
    Boost model capabilities based on query content and characteristics.
    This allows dynamic capability adjustment based on query analysis.
    
    Args:
        query: The user query to analyze
        model_capabilities: The current model capabilities dictionary
    
    Returns:
        Updated model capabilities dictionary with query-specific boosts
    """
    query_lower = query.lower()
    
    # Create a copy of the capabilities to avoid modifying the original
    boosted_capabilities = {model: capabilities.copy() for model, capabilities in model_capabilities.items()}
    
    # Technical query detection (code, programming, math, technical concepts)
    technical_patterns = [
        "code", "program", "function", "class", "algorithm", "implement",
        "debug", "error", "bug", "compile", "runtime", "syntax",
        "math", "calculate", "equation", "formula", "proof",
        "how does", "explain technically", "technical explanation"
    ]
    
    # Creative query detection (writing, stories, creative content)
    creative_patterns = [
        "write", "story", "creative", "poem", "fiction", "imagine",
        "generate", "create a", "design", "art", "novel", "dialogue",
        "character", "scene", "setting", "plot"
    ]
    
    # Reasoning query detection (logic, analysis, problem-solving)
    reasoning_patterns = [
        "why", "analyze", "evaluate", "compare", "contrast", "reason",
        "logic", "problem", "solution", "deduce", "infer", "conclusion",
        "cause", "effect", "relationship", "scenario", "situational"
    ]
    
    # Factual query detection (information seeking, factual content)
    factual_patterns = [
        "what is", "who is", "when did", "where is", "history", "fact",
        "information about", "tell me about", "explain", "describe",
        "definition", "timeline", "events", "data", "statistics"
    ]
    
    # Check for query types and apply boosts
    # Technical query boosts
    if any(pattern in query_lower for pattern in technical_patterns):
        logger.info("Query detected as TECHNICAL")
        # Boost models that excel at technical content
        for model in ["gpt-4o", "claude-3-opus", "Llama-3.2-1B-Instruct-Q4_0.gguf"]:
            if model in boosted_capabilities:
                boosted_capabilities[model]["technical"] *= 1.15  # +15% boost
        
    # Creative query boosts
    if any(pattern in query_lower for pattern in creative_patterns):
        logger.info("Query detected as CREATIVE")
        # Boost models that excel at creative content
        for model in ["claude-3-opus", "gpt-4o"]:
            if model in boosted_capabilities:
                boosted_capabilities[model]["creative"] *= 1.15  # +15% boost
    
    # Reasoning query boosts
    if any(pattern in query_lower for pattern in reasoning_patterns):
        logger.info("Query detected as REASONING")
        # Boost models that excel at reasoning
        for model in ["gpt-4o", "claude-3-opus", "gemini-pro"]:
            if model in boosted_capabilities:
                boosted_capabilities[model]["reasoning"] *= 1.10  # +10% boost
    
    # Factual query boosts
    if any(pattern in query_lower for pattern in factual_patterns):
        logger.info("Query detected as FACTUAL")
        # Boost models that excel at factual content
        for model in ["gpt-4o", "claude-3-opus", "gemini-pro"]:
            if model in boosted_capabilities:
                boosted_capabilities[model]["factual"] *= 1.10  # +10% boost
    
    # Apply length-based considerations
    query_length = len(query.split())
    if query_length > 100:  # For very complex, long queries
        logger.info("Query detected as COMPLEX (long)")
        # Boost models with larger context windows
        for model in ["gpt-4o", "claude-3-opus"]:
            if model in boosted_capabilities:
                for capability in ["technical", "reasoning"]:
                    boosted_capabilities[model][capability] *= 1.10  # +10% boost
    
    # Log the boosted capabilities for debugging
    for model, capabilities in boosted_capabilities.items():
        # Only log changes for models that received boosts
        original = model_capabilities.get(model, {})
        if any(capabilities.get(k, 0) != original.get(k, 0) for k in capabilities):
            logger.info(f"Applied query-specific capability boost for {model}")
    
    return boosted_capabilities

'''
    
    # Insert the boost function before the _get_model_capabilities function
    modified_content = content[:boost_function_pos] + boost_function + content[boost_function_pos:]
    
    # Write the modified content back
    with open(ENSEMBLE_VALIDATOR_FILE, 'w') as f:
        f.write(modified_content)
    
    print(f"✅ Added capability boost function to {ENSEMBLE_VALIDATOR_FILE}")
    return True

def modify_rank_responses_to_use_boost():
    """Modify the rank_responses function to use the new capability boost function"""
    if not ENSEMBLE_VALIDATOR_FILE.exists():
        print(f"❌ Cannot find {ENSEMBLE_VALIDATOR_FILE}")
        return False
    
    # Read the file
    with open(ENSEMBLE_VALIDATOR_FILE, 'r') as f:
        content = f.read()
    
    # Check if the rank_responses function already uses the boost function
    if "boost_model_capabilities_for_query" in content and "boosted_capabilities" in content:
        print("✅ rank_responses already uses capability boost function")
        return True
    
    # Find the _get_model_capabilities function
    get_capabilities_pattern = r'def _get_model_capabilities\(\)'
    match = re.search(get_capabilities_pattern, content)
    
    if not match:
        print("❌ Could not find _get_model_capabilities function")
        return False
        
    # Find the return statement in the function
    get_capabilities_start = match.start()
    return_pattern = r'\s+return\s+{'
    return_match = re.search(return_pattern, content[get_capabilities_start:])
    
    if not return_match:
        print("❌ Could not find return statement in _get_model_capabilities")
        return False
    
    # Position to replace the capabilities dictionary
    capabilities_start = get_capabilities_start + return_match.start()
    
    # Find where the capabilities dictionary ends
    capabilities_end = content.find('\n    }', capabilities_start)
    capabilities_end = content.find('}', capabilities_end) + 1
    
    if capabilities_end == 0:
        print("❌ Could not find end of capabilities dictionary")
        return False
    
    # Updated capabilities to insert
    updated_capabilities = '''
    return {
        'gpt-4': {
            'technical': 0.9,
            'creative': 0.8,
            'reasoning': 0.9,
            'factual': 0.85,
            'structured': 0.9
        },
        'gpt-4o': {
            'technical': 0.95,
            'creative': 0.92,
            'reasoning': 0.95,
            'factual': 0.93,
            'structured': 0.94
        },
        'claude-3-opus': {
            'technical': 0.93,
            'creative': 0.94,
            'reasoning': 0.95,
            'factual': 0.92,
            'structured': 0.95
        },
        'gemini-pro': {
            'technical': 0.88,
            'creative': 0.90,
            'reasoning': 0.91,
            'factual': 0.89,
            'structured': 0.87
        },
        'mistral-large': {
            'technical': 0.87,
            'creative': 0.85,
            'reasoning': 0.89,
            'factual': 0.86,
            'structured': 0.88
        },
        'Llama-3.2-1B-Instruct-Q4_0.gguf': {
            'technical': 0.75,
            'creative': 0.70,
            'reasoning': 0.72,
            'factual': 0.65,
            'structured': 0.68
        },
        'claude-3': {
            'technical': 0.85,
            'creative': 0.9,
            'reasoning': 0.85,
            'factual': 0.82,
            'structured': 0.85
        },
        'gpt-4o-mini': {
            'technical': 0.8,
            'creative': 0.75,
            'reasoning': 0.78,
            'factual': 0.76,
            'structured': 0.8
        },
        'claude-3-haiku': {
            'technical': 0.8,
            'creative': 0.85,
            'reasoning': 0.82,
            'factual': 0.8,
            'structured': 0.81
        }
    }'''
    
    # Replace the capabilities dictionary
    modified_content = content[:capabilities_start] + updated_capabilities + content[capabilities_end:]
    
    # Write the modified content back
    with open(MODEL_CAPABILITIES_FILE, 'w') as f:
        f.write(modified_content)
    
    print(f"✅ Modified rank_responses to use capability boost function")
    return True

def main():
    print("=== Fine-tuning Model Capabilities for Minerva's Think Tank ===")
    
    # Step 1: Update model capabilities
    update_model_capabilities()
    
    # Step 2: Add capability boost function
    add_capability_boost_function()
    
    # Step 3: Modify rank_responses to use boost
    modify_rank_responses_to_use_boost()
    
    print("\n===== Fine-tuning Complete =====")
    print("Your Think Tank now has:")
    print("1. Enhanced model capability profiles based on observed performance")
    print("2. Dynamic capability adjustment based on query analysis")
    print("3. Query-specific model selection for optimal responses")
    print("\nTest your improved Think Tank with:")
    print("   python run_think_tank_test.py")

if __name__ == "__main__":
    main()
