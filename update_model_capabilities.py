#!/usr/bin/env python3
"""
Update Model Capabilities for Minerva's Think Tank

This script updates the capability weights for AI models in both think_tank.py and
ensemble_validator.py to ensure consistency across the system.
"""

import os
import re
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Directory and file paths
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
THINK_TANK_FILE = BASE_DIR / 'processor' / 'think_tank.py'
ENSEMBLE_VALIDATOR_FILE = BASE_DIR / 'processor' / 'ensemble_validator.py'

# Enhanced capability weights based on observed performance
MODEL_CAPABILITIES = {
    # High-end models
    "gpt-4o": {
        'technical': 0.95,
        'creative': 0.92,
        'reasoning': 0.95,
        'factual': 0.93,
        'structured': 0.94,
        'max_tokens': 8192,
        'context_window': 16384
    },
    "claude-3-opus": {
        'technical': 0.93,
        'creative': 0.94,
        'reasoning': 0.95,
        'factual': 0.92,
        'structured': 0.95,
        'max_tokens': 8192,
        'context_window': 16384
    },
    "gpt-4": {
        'technical': 0.90,
        'creative': 0.85,
        'reasoning': 0.91,
        'factual': 0.88,
        'structured': 0.91,
        'max_tokens': 8192,
        'context_window': 8192
    },
    "gemini-pro": {
        'technical': 0.88,
        'creative': 0.90,
        'reasoning': 0.91,
        'factual': 0.89,
        'structured': 0.87,
        'max_tokens': 4096,
        'context_window': 8192
    },
    "mistral-large": {
        'technical': 0.87,
        'creative': 0.85,
        'reasoning': 0.89,
        'factual': 0.86,
        'structured': 0.88,
        'max_tokens': 4096,
        'context_window': 8192
    },
    
    # Mid-range models
    "gpt-4o-mini": {
        'technical': 0.82,
        'creative': 0.80,
        'reasoning': 0.84,
        'factual': 0.81,
        'structured': 0.83,
        'max_tokens': 4096,
        'context_window': 8192
    },
    "claude-3": {
        'technical': 0.85,
        'creative': 0.90,
        'reasoning': 0.85,
        'factual': 0.82,
        'structured': 0.85,
        'max_tokens': 4096,
        'context_window': 8192
    },
    "claude-3-haiku": {
        'technical': 0.80,
        'creative': 0.85,
        'reasoning': 0.82,
        'factual': 0.80,
        'structured': 0.81,
        'max_tokens': 2048,
        'context_window': 4096
    },
    
    # Local models
    "Llama-3.2-1B-Instruct-Q4_0.gguf": {
        'technical': 0.75,
        'creative': 0.70,
        'reasoning': 0.72,
        'factual': 0.65,
        'structured': 0.68,
        'max_tokens': 3072,
        'context_window': 4096
    }
}

# Capability boost function code
BOOST_FUNCTION = '''
def boost_model_capabilities_for_query(
    query: str, 
    model_capabilities: Dict[str, Dict[str, float]]
) -> Dict[str, Dict[str, float]]:
    """
    Boost model capabilities based on query content
    
    Args:
        query: User query text
        model_capabilities: Dict of model capabilities
        
    Returns:
        Dict of boosted model capabilities
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Create a copy of the capabilities to modify
    boosted_capabilities = {}
    for model, caps in model_capabilities.items():
        boosted_capabilities[model] = caps.copy()
    
    # Skip boost for empty queries
    if not query or not query.strip():
        return boosted_capabilities
        
    # Convert query to lowercase for pattern matching
    query_lower = query.lower()
    
    # Define patterns for different query types
    technical_patterns = [
        'code', 'programming', 'function', 'error', 'debug',
        'algorithm', 'api', 'database', 'html', 'css', 'javascript',
        'python', 'java', 'c++', 'sql', 'json', 'xml'
    ]
    
    creative_patterns = [
        'story', 'creative', 'poem', 'fiction', 'imagine',
        'art', 'design', 'write', 'generate', 'create'
    ]
    
    reasoning_patterns = [
        'explain', 'why', 'how does', 'reason', 'analyze',
        'compare', 'difference', 'implications', 'consequences'
    ]
    
    factual_patterns = [
        'fact', 'history', 'science', 'information', 'data',
        'research', 'statistics', 'report', 'study'
    ]
    
    # Technical query boosts
    if any(pattern in query_lower for pattern in technical_patterns):
        logger.info("Query detected as TECHNICAL")
        # Boost models that excel at technical content
        for model in ["gpt-4o", "gpt-4", "claude-3-opus"]:
            if model in boosted_capabilities:
                boosted_capabilities[model]["technical"] *= 1.15  # +15% boost
        
    # Creative query boosts
    if any(pattern in query_lower for pattern in creative_patterns):
        logger.info("Query detected as CREATIVE")
        # Boost models that excel at creative content
        for model in ["claude-3-opus", "gpt-4o", "gemini-pro"]:
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
    
    return boosted_capabilities
'''

def update_think_tank_capabilities():
    """Update MODEL_CAPABILITIES in think_tank.py"""
    if not THINK_TANK_FILE.exists():
        logger.error(f"❌ Cannot find {THINK_TANK_FILE}")
        return False
    
    # Read the file
    with open(THINK_TANK_FILE, 'r') as f:
        content = f.read()
    
    # Find the MODEL_CAPABILITIES dictionary
    model_cap_pattern = r'MODEL_CAPABILITIES\s*=\s*{'
    match = re.search(model_cap_pattern, content)
    
    if not match:
        logger.error("❌ Could not find MODEL_CAPABILITIES dictionary in think_tank.py")
        return False
    
    # Find the start and end of the dictionary
    dict_start = match.start()
    # Find the end of the dictionary by finding the matching closing brace
    depth = 0
    dict_end = dict_start
    for i in range(dict_start, len(content)):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                dict_end = i + 1
                break
    
    if dict_end == dict_start:
        logger.error("❌ Could not find end of MODEL_CAPABILITIES dictionary")
        return False
    
    # Build the new capabilities dictionary string
    new_capabilities = "MODEL_CAPABILITIES = {\n"
    for model, caps in MODEL_CAPABILITIES.items():
        new_capabilities += f"    '{model}': {{\n"
        for cap, value in caps.items():
            new_capabilities += f"        '{cap}': {value},\n"
        new_capabilities += "    },\n"
    new_capabilities += "}"
    
    # Replace the old dictionary with the new one
    modified_content = content[:dict_start] + new_capabilities + content[dict_end:]
    
    # Write the modified content back
    with open(THINK_TANK_FILE, 'w') as f:
        f.write(modified_content)
    
    logger.info(f"✅ Updated MODEL_CAPABILITIES in {THINK_TANK_FILE}")
    return True

def update_ensemble_validator_capabilities():
    """Update _get_model_capabilities function in ensemble_validator.py"""
    if not ENSEMBLE_VALIDATOR_FILE.exists():
        logger.error(f"❌ Cannot find {ENSEMBLE_VALIDATOR_FILE}")
        return False
    
    # Read the file
    with open(ENSEMBLE_VALIDATOR_FILE, 'r') as f:
        content = f.read()
    
    # Check if boost function already exists
    if "boost_model_capabilities_for_query" in content:
        logger.info("✅ boost_model_capabilities_for_query function already exists")
    else:
        # Find a good place to insert the boost function
        # Insert before _get_model_capabilities
        get_cap_pattern = r'def _get_model_capabilities\(\)'
        match = re.search(get_cap_pattern, content)
        
        if not match:
            logger.error("❌ Could not find _get_model_capabilities function")
            return False
        
        # Insert the boost function
        insert_pos = match.start()
        content = content[:insert_pos] + BOOST_FUNCTION + "\n\n" + content[insert_pos:]
        logger.info("✅ Added boost_model_capabilities_for_query function")
    
    # Find the _get_model_capabilities function and its return statement
    get_cap_pattern = r'def _get_model_capabilities\(\).*?return\s*{'
    match = re.search(get_cap_pattern, content, re.DOTALL)
    
    if not match:
        logger.error("❌ Could not find return statement in _get_model_capabilities")
        return False
    
    # Find the end of the return dictionary
    return_start = match.end() - 1  # -1 to keep the opening brace
    depth = 1  # We're already inside the opening brace
    return_end = return_start + 1
    for i in range(return_start + 1, len(content)):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                return_end = i + 1
                break
    
    if return_end <= return_start:
        logger.error("❌ Could not find end of capabilities dictionary")
        return False
    
    # Build the new capabilities dictionary string
    new_capabilities = "{"
    for model, caps in MODEL_CAPABILITIES.items():
        # Only include the basic capabilities, not max_tokens and context_window
        basic_caps = {k: v for k, v in caps.items() if k not in ['max_tokens', 'context_window']}
        new_capabilities += f"\n        '{model}': {{\n"
        for cap, value in basic_caps.items():
            new_capabilities += f"            '{cap}': {value},\n"
        new_capabilities += "        },\n"
    new_capabilities += "    }"
    
    # Replace the old dictionary with the new one
    modified_content = content[:return_start] + new_capabilities + content[return_end:]
    
    # Write the modified content back
    with open(ENSEMBLE_VALIDATOR_FILE, 'w') as f:
        f.write(modified_content)
    
    logger.info(f"✅ Updated model capabilities in _get_model_capabilities")
    return True

def main():
    """Main function to update model capabilities"""
    print("=== Updating Model Capabilities for Minerva's Think Tank ===\n")
    
    # Update capabilities in think_tank.py
    think_tank_updated = update_think_tank_capabilities()
    
    # Update capabilities in ensemble_validator.py
    ensemble_validator_updated = update_ensemble_validator_capabilities()
    
    if think_tank_updated and ensemble_validator_updated:
        print("\n===== Update Complete =====")
        print("Your Think Tank now has:")
        print("1. Enhanced model capability profiles based on observed performance")
        print("2. Dynamic capability adjustment based on query analysis")
        print("3. Query-specific model selection for optimal responses")
        print("\nTest your improved Think Tank with:")
        print("   python run_think_tank_test.py")
    else:
        print("\n❌ Update incomplete - please check the errors above")

if __name__ == "__main__":
    main()
