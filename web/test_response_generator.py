#!/usr/bin/env python3
"""
Test Script for the Enhanced Response Generator

This script allows testing the enhanced response generator with various query types
and configurations without needing to go through the web API.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, Any, List

# Add the parent directory to the path so we can import the web module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Configure the test environment for response generator testing"""
    try:
        # Import required modules
        import web.response_generator
        
        # Check if response_generator has the required functions
        required_functions = [
            'tag_query', 'rank_responses', 'blend_responses', 
            'blend_technical_responses', 'blend_explanation_responses',
            'blend_comparison_responses', 'blend_general_responses'
        ]
        
        missing = []
        for func in required_functions:
            if not hasattr(web.response_generator, func):
                missing.append(func)
        
        if missing:
            logger.error(f"Missing required functions in response_generator: {', '.join(missing)}")
            return False
        
        logger.info("Response generator module loaded successfully")
        return True
    except ImportError as e:
        logger.error(f"Failed to import response_generator module: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to setup test environment: {str(e)}")
        return False

def mock_model_response(query: str, model_name: str) -> str:
    """
    Generate a mock response for a model to test the blending functionality
    
    Args:
        query: The test query
        model_name: Name of the model
        
    Returns:
        A simulated response string
    """
    # Simple structure for mock responses to test blending
    responses = {
        "technical": {
            "gpt4": "Here's a technical answer from GPT-4:\n\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```\n\nThis is an elegant recursive solution to calculate Fibonacci numbers.",
            "claude-3": "Claude-3 technical response:\n\n```python\ndef fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n```\n\nThis iterative approach is more efficient than recursion for large values.",
            "gemini-pro": "Gemini Pro suggests this approach:\n\n```python\ndef fibonacci(n, memo={}):\n    if n in memo:\n        return memo[n]\n    if n <= 1:\n        return n\n    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)\n    return memo[n]\n```\n\nThis uses memoization to optimize the recursive solution.",
            "gpt-3.5-turbo": "GPT-3.5 Turbo solution:\n\n```python\ndef fibonacci(n):\n    fib = [0, 1]\n    for i in range(2, n+1):\n        fib.append(fib[i-1] + fib[i-2])\n    return fib[n]\n```\n\nThis approach uses dynamic programming with an array.",
            "mistral7b": "Mistral-7B says:\n\n```python\nimport numpy as np\n\ndef fibonacci(n):\n    return int(((1+np.sqrt(5))**n - (1-np.sqrt(5))**n)/(2**n*np.sqrt(5)))\n```\n\nThis uses Binet's formula for direct calculation."
        },
        "explanation": {
            "gpt4": f"# GPT-4 Explanation\n\nBlockchain technology works by creating a distributed ledger across multiple computers. Each 'block' contains transaction data and a hash of the previous block, forming a chain.\n\n## Key Components\n\n1. **Decentralization**: No central authority controls the chain\n2. **Transparency**: All transactions are visible to participants\n3. **Immutability**: Once data is recorded, it cannot be altered\n\nThis creates a secure, transparent system for recording transactions.",
            "claude-3": f"# Claude-3 Explanation\n\nBlockchain is a distributed database technology that maintains a continuously growing list of records called blocks.\n\n## Core Elements\n\n1. **Distributed Ledger**: Copies exist across multiple locations\n2. **Consensus Mechanism**: Participants agree on valid transactions\n3. **Cryptographic Hashing**: Ensures data integrity and chronological order\n\n## Applications\n\nBlockchain extends beyond cryptocurrencies to supply chain management, voting systems, and more.",
            "gemini-pro": f"# Gemini Pro Explanation\n\nBlockchain technology functions as a secure digital record-keeping system using cryptography.\n\n## How It Works\n\n* Transactions are grouped into blocks\n* Each block contains transaction data, timestamp, and hash of previous block\n* Blocks are verified by network consensus\n* Once verified, blocks can't be modified\n\nThe technology enables secure peer-to-peer transactions without intermediaries.",
            "gpt-3.5-turbo": f"# GPT-3.5 Turbo Explanation\n\nBlockchain works as a digital chain of blocks containing transaction records.\n\nEach transaction is verified by multiple computers (nodes) before being added to the blockchain. Once added, it's nearly impossible to change.\n\nKey features include:\n- Decentralization\n- Security through cryptography\n- Transparency and traceability",
            "mistral7b": f"# Mistral-7B Explanation\n\nBlockchain is a chain of blocks with transaction data linked using cryptography.\n\nWhen a block is completed, it creates a unique hash. This hash goes into the next block, creating a chain.\n\nBlockchain is secure because:\n- It's distributed across many computers\n- Changing one block requires changing all subsequent blocks\n- Multiple parties must verify changes"
        },
        "comparison": {
            "gpt4": f"# Python vs JavaScript: GPT-4 Comparison\n\n## Syntax\nPython uses indentation for code blocks, while JavaScript uses curly braces.\n\n## Type System\nPython is dynamically typed with strong typing. JavaScript is dynamically typed with weak typing.\n\n## Use Cases\nPython excels in data science, ML, and backend. JavaScript dominates web development and has expanded to server-side with Node.js.",
            "claude-3": f"# Python vs JavaScript: Claude-3 Analysis\n\n## Language Paradigm\nPython: Multi-paradigm with emphasis on readability\nJavaScript: Prototype-based object-oriented with functional programming support\n\n## Execution\nPython: Interpreter-based\nJavaScript: Just-in-time compiled\n\n## Ecosystem\nPython: Rich scientific libraries\nJavaScript: Vast frontend frameworks",
            "gemini-pro": f"# Python vs JavaScript: Gemini Pro Perspective\n\n## Learning Curve\n- Python: Gentle learning curve, readable syntax\n- JavaScript: Moderate learning curve, more complex syntax\n\n## Performance\n- Python: Generally slower for CPU-intensive tasks\n- JavaScript: Faster for many operations due to V8 engine\n\n## Community\n- Both have massive communities and resources",
            "gpt-3.5-turbo": f"# Python vs JavaScript Compared by GPT-3.5 Turbo\n\n## Key Differences:\n\n1. **Syntax**: Python uses significant whitespace; JavaScript uses braces and semicolons\n2. **Environment**: Python runs on servers; JavaScript runs primarily in browsers plus Node.js\n3. **Libraries**: Python has extensive data science libraries; JavaScript has DOM manipulation and UI libraries",
            "mistral7b": f"# Python vs JavaScript: Mistral-7B Comparison\n\n## Basics:\n- Python: Clean syntax, general-purpose language\n- JavaScript: Web-focused language\n\n## Data Structures:\n- Python: Rich built-in types like lists, tuples, dictionaries\n- JavaScript: Arrays, objects as primary structures\n\n## Concurrency:\n- Python: GIL limitations\n- JavaScript: Event-driven, non-blocking I/O"
        },
        "general": {
            "gpt4": f"The capital of France is Paris. It's located in the north-central part of the country on the Seine River. Paris is one of the world's major global cities and serves as France's economic, political, and cultural center. With landmarks like the Eiffel Tower, Louvre Museum, and Notre-Dame Cathedral, Paris is also one of the world's most visited tourist destinations.",
            "claude-3": f"Paris is the capital city of France. Founded in the 3rd century BCE, Paris has grown to become one of Europe's major centers of finance, diplomacy, commerce, culture, and arts. The city is particularly known for its museums and architectural landmarks, with the Eiffel Tower being its most famous monument. Paris is located in the north-central part of France on the Seine River.",
            "gemini-pro": f"The capital of France is Paris. It's situated on the Seine River in the north-central part of the country. Paris is often called the 'City of Light' (La Ville Lumière) due to its role during the Age of Enlightenment and its early adoption of street lighting. The city is renowned for its art museums, fashion houses, gastronomy, and iconic structures like the Eiffel Tower and Arc de Triomphe.",
            "gpt-3.5-turbo": f"Paris is the capital of France. Located on the Seine River in the north-central part of the country, it's one of the world's most beautiful and culturally rich cities. Paris is famous for landmarks like the Eiffel Tower, Louvre Museum (home to the Mona Lisa), and Notre-Dame Cathedral. It's also known for its cuisine, fashion industry, and artistic heritage.",
            "mistral7b": f"The capital of France is Paris. It's one of the most populous cities in Europe and serves as France's major cultural, economic, and political center. Paris is known worldwide for its iconic landmarks such as the Eiffel Tower, Notre-Dame Cathedral, and the Louvre Museum. The city has been a global center for art, science, fashion, and gastronomy throughout its history."
        }
    }
    
    # Determine which response category to use based on the query
    if any(term in query.lower() for term in ["code", "program", "function", "algorithm"]):
        category = "technical"
    elif any(term in query.lower() for term in ["explain", "how does", "why is", "what is"]):
        category = "explanation"
    elif any(term in query.lower() for term in ["compare", "versus", "vs", "difference"]):
        category = "comparison"
    else:
        category = "general"
    
    # Return the appropriate mock response
    return responses[category].get(model_name, f"Default {model_name} response for {category} query")

def run_single_test(query: str, user_id: str = "test_user", 
                   context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run a single test with the enhanced response generator
    
    Args:
        query: The test query to process
        user_id: Test user identifier
        context: Optional context data
        
    Returns:
        The response data from the generator
    """
    from web.response_generator import tag_query, rank_responses, blend_responses
    
    # Create default context if none provided
    if context is None:
        context = {
            'history': [],
            'test_mode': True
        }
    
    # Add query tags to context
    context['tags'] = tag_query(query)
    
    logger.info(f"Processing test query: '{query}'")
    logger.info(f"Query tags: {context['tags']}")
    
    # Generate mock responses from different models
    model_names = ["gpt4", "claude-3", "gemini-pro", "gpt-3.5-turbo", "mistral7b"]
    model_responses = {}
    
    for model_name in model_names:
        model_responses[model_name] = mock_model_response(query, model_name)
    
    # Rank the responses
    ranked_responses = rank_responses(model_responses, query, context)
    
    # Blend the responses
    final_response = blend_responses(ranked_responses, query, context)
    
    # Add query and user info to the response
    final_response["query"] = query
    final_response["user_id"] = user_id
    final_response["context"] = {
        "tags": context.get("tags", []),
        "test_mode": True
    }
    
    return final_response

def display_response(response: Dict[str, Any], verbose: bool = False):
    """
    Display the response in a readable format
    
    Args:
        response: The response data from the generator
        verbose: Whether to show full details
    """
    print("\n" + "="*80)
    print(f"RESPONSE TEXT:\n{'-'*80}\n{response['response_text']}\n{'-'*80}")
    
    print(f"\nPRIMARY MODEL: {response.get('model_name', 'unknown')}")
    print(f"BLENDED: {response.get('blended', False)}")
    
    if response.get('blended', False):
        print(f"BLEND STRATEGY: {response.get('blend_strategy', 'unknown')}")
        print(f"SOURCE MODELS: {', '.join(response.get('sources', []))}")
    
    if verbose:
        if 'contributions' in response:
            print("\nMODEL CONTRIBUTIONS:")
            for contrib in response.get('contributions', []):
                print(f"  - {contrib['model']}: Rank {contrib['rank']} (Score: {contrib['score']:.2f})")
                if 'reason' in contrib:
                    print(f"    Reason: {contrib['reason']}")
        
        # Pretty print the full response for detailed inspection
        print("\nFULL RESPONSE DATA:")
        print(json.dumps(response, indent=2, default=str))
    
    print("="*80 + "\n")

def run_test_suite():
    """Run a comprehensive test suite with various query types"""
    test_queries = [
        # Technical queries
        "Write a Python function to calculate the Fibonacci sequence",
        "How do I fix a NullPointerException in Java?",
        "Explain the difference between REST and GraphQL",
        
        # Factual queries
        "What is the capital of France?",
        "Who discovered penicillin?",
        "Explain quantum computing",
        
        # Comparison queries
        "Compare Python and JavaScript programming languages",
        "What's the difference between machine learning and deep learning?",
        "AWS vs Azure: which cloud provider is better?",
        
        # Creative queries
        "Write a short poem about technology",
        "Create a story about artificial intelligence",
        
        # Explanation queries
        "How does blockchain technology work?",
        "Why is the sky blue?",
        "What is the theory of relativity?"
    ]
    
    results = {}
    
    for i, query in enumerate(test_queries):
        print(f"\nRunning test {i+1}/{len(test_queries)}: '{query}'")
        response = run_single_test(query)
        results[query] = {
            "blended": response.get("blended", False),
            "blend_strategy": response.get("blend_strategy"),
            "sources": response.get("sources", []),
            "tags": response.get("context", {}).get("tags", [])
        }
        display_response(response)
    
    # Show summary of test results
    print("\nTEST SUMMARY:")
    print(f"Total tests run: {len(test_queries)}")
    
    blended_count = sum(1 for r in results.values() if r["blended"])
    print(f"Responses blended: {blended_count}/{len(test_queries)}")
    
    strategies = {}
    for r in results.values():
        if r["blended"]:
            strategy = r.get("blend_strategy", "unknown")
            strategies[strategy] = strategies.get(strategy, 0) + 1
    
    print("Blend strategies used:")
    for strategy, count in strategies.items():
        print(f"  - {strategy}: {count}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Test the enhanced response generator")
    parser.add_argument("--query", type=str, help="Run a single test with this query")
    parser.add_argument("--type", choices=["technical", "explanation", "comparison", "general"], 
                       help="Test a specific query type with predefined examples")
    parser.add_argument("--user", type=str, default="test_user", help="User ID for testing")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--suite", action="store_true", help="Run the full test suite")
    
    args = parser.parse_args()
    
    # Set up test environment
    if not setup_test_environment():
        logger.error("Failed to set up test environment")
        return
    
    # Sample queries by type for quick testing
    sample_queries = {
        "technical": "Write a Python function to calculate the Fibonacci sequence",
        "explanation": "How does blockchain technology work?",
        "comparison": "Compare Python and JavaScript programming languages",
        "general": "What is the capital of France?"
    }
    
    if args.suite:
        # Run the full test suite
        run_test_suite()
    elif args.query:
        # Run a single test with user-provided query
        response = run_single_test(args.query, args.user)
        display_response(response, args.verbose)
    elif args.type:
        # Run test with sample query of specified type
        query = sample_queries[args.type]
        print(f"\nTesting {args.type} query: '{query}'")
        response = run_single_test(query, args.user)
        display_response(response, args.verbose)
    else:
        # Run a quick demo if no arguments
        print("\n=== MINERVA ENHANCED RESPONSE GENERATOR DEMO ===")
        print("Running quick tests for different query types...\n")
        
        for query_type, query in sample_queries.items():
            print(f"\n----- Testing {query_type.upper()} query -----")
            print(f"Query: '{query}'")
            response = run_single_test(query, args.user)
            display_response(response, False)  # Brief display format
            
        print("\nDemo complete! For more options, run with --help")

if __name__ == "__main__":
    main()
