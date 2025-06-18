#!/usr/bin/env python3
"""
Minerva Think Tank Validation Suite

This script systematically tests Minerva's Think Tank mode with a focus on:
1. Model selection logic
2. Response blending effectiveness
3. Claude-3 integration validation
4. Response quality evaluation

It runs standardized queries and analyzes the system's decision-making.
"""
import os
import sys
import json
import time
import asyncio
import logging
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('think_tank_validator')

# Test query categories based on capabilities from different models
TEST_QUERIES = {
    "factual": [
        "What are the primary factors affecting climate change?",
        "Explain the history and significance of the Magna Carta.",
        "What are the fundamental principles of quantum mechanics?"
    ],
    "technical": [
        "Explain how CRISPR gene editing technology works.",
        "How do neural networks implement backpropagation?",
        "Describe the process of nuclear fusion in stars."
    ],
    "analytical": [
        "Compare different approaches to renewable energy storage.",
        "Analyze the economic factors contributing to inflation in 2025.",
        "What are the implications of quantum computing for cryptography?"
    ],
    "creative": [
        "Write a short story about a world where AI and humans coexist.",
        "Create a poem about the relationship between technology and nature.",
        "Design a hypothetical sustainable city of the future."
    ],
    "code": [
        "Write a Python function to implement a binary search tree.",
        "Create a JavaScript function for deep comparison of objects.",
        "Implement a simple machine learning algorithm in Python."
    ]
}

MODEL_CAPABILITY_MAP = {
    "claude3": ["factual", "analytical", "technical"],
    "gpt4": ["creative", "code", "analytical"],
    "mistral": ["code", "technical"],
    "llama": ["creative", "factual"]
}

async def test_claude3_availability(api_key: Optional[str] = None) -> bool:
    """Test if Claude-3 API is available and properly configured"""
    try:
        # Import only if needed
        sys.path.append(str(Path(__file__).parent))
        from web.model_processors import process_with_claude3
        
        # If API key is provided, use it temporarily
        original_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        
        # Test with a simple query
        result = await process_with_claude3("What is 2+2?")
        
        # Restore original key if we set a temporary one
        if api_key and original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key
        elif api_key and not original_key:
            del os.environ["ANTHROPIC_API_KEY"]
        
        if result.get("is_error"):
            logger.warning(f"Claude-3 test failed: {result.get('error')}")
            return False
        
        logger.info("Claude-3 API is accessible and working correctly")
        return True
    
    except Exception as e:
        logger.error(f"Error testing Claude-3 availability: {str(e)}")
        return False

async def test_think_tank_endpoint(
    query: str, 
    minerva_url: str = "http://127.0.0.1:13083",
    debug_mode: bool = True
) -> Dict[str, Any]:
    """Test the Think Tank endpoint with a specific query"""
    headers = {
        "Content-Type": "application/json"
    }
    
    if debug_mode:
        headers["X-Debug-Mode"] = "true"
        headers["X-Test-Mode"] = "true"  # Request detailed model info
    
    data = {
        "message": query
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{minerva_url}/api/v1/advanced-think-tank",
            headers=headers,
            json=data,
            timeout=60  # Allow up to 60 seconds for complex queries
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            try:
                result = response.json()
                return {
                    "success": True,
                    "processing_time": processing_time,
                    "response": result
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON response",
                    "processing_time": processing_time,
                    "raw_response": response.text
                }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text,
                "processing_time": processing_time
            }
    
    except Exception as e:
        processing_time = time.time() - start_time
        return {
            "success": False,
            "error": str(e),
            "processing_time": processing_time
        }

def analyze_model_selection(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze model selection patterns from test results"""
    model_usage = {}
    category_model_match = {}
    blending_stats = {}
    
    for category, category_results in results.items():
        model_usage[category] = {}
        category_model_match[category] = {"matched": 0, "total": 0}
        
        for test_name, test_result in category_results.items():
            if not test_result.get("success"):
                continue
                
            response_data = test_result.get("response", {})
            
            # Track top model used
            model_used = response_data.get("model_used", "unknown")
            model_usage[category][model_used] = model_usage[category].get(model_used, 0) + 1
            
            # Check if model matches expected capability
            expected_models = []
            for model, capabilities in MODEL_CAPABILITY_MAP.items():
                if category in capabilities:
                    expected_models.append(model)
            
            category_model_match[category]["total"] += 1
            if any(expected in model_used.lower() for expected in expected_models):
                category_model_match[category]["matched"] += 1
            
            # Track blending information
            model_info = response_data.get("model_info", {})
            if model_info:
                model_count = len(model_info.get("contributing_models", []))
                blending_key = f"{model_count}_models"
                blending_stats[blending_key] = blending_stats.get(blending_key, 0) + 1
    
    # Calculate match percentages
    match_percentages = {}
    for category, stats in category_model_match.items():
        if stats["total"] > 0:
            match_percentages[category] = (stats["matched"] / stats["total"]) * 100
        else:
            match_percentages[category] = 0
    
    return {
        "model_usage": model_usage,
        "capability_match": match_percentages,
        "blending_stats": blending_stats
    }

async def run_validation_suite(
    minerva_url: str = "http://127.0.0.1:13083",
    anthropic_api_key: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """Run the complete validation suite"""
    # Start with Claude-3 availability test
    claude3_available = await test_claude3_availability(anthropic_api_key)
    
    # Run tests for each category and query
    results = {}
    
    for category, queries in TEST_QUERIES.items():
        logger.info(f"Testing category: {category}")
        results[category] = {}
        
        for i, query in enumerate(queries):
            test_name = f"{category}_{i+1}"
            logger.info(f"  Running test: {test_name}")
            
            test_result = await test_think_tank_endpoint(query, minerva_url)
            results[category][test_name] = test_result
            
            status = "✅ Success" if test_result.get("success") else "❌ Failed"
            logger.info(f"  {status} - Time: {test_result.get('processing_time', 0):.2f}s")
            
            # Add short delay between requests
            await asyncio.sleep(1)
    
    # Analyze results
    analysis = analyze_model_selection(results)
    
    # Compile final report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "claude3_available": claude3_available,
        "results": results,
        "analysis": analysis
    }
    
    # Save report if output file specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report saved to {output_file}")
    
    # Print summary
    print("\n===== MINERVA THINK TANK VALIDATION SUMMARY =====")
    print(f"Claude-3 API Available: {'✅ Yes' if claude3_available else '❌ No'}")
    
    print("\nModel Selection by Category:")
    for category, models in analysis["model_usage"].items():
        print(f"  {category.capitalize()}:")
        for model, count in sorted(models.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {model}: {count}")
    
    print("\nCapability Match Percentages:")
    for category, percentage in sorted(analysis["capability_match"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category.capitalize()}: {percentage:.1f}%")
    
    print("\nResponse Blending Statistics:")
    for blend, count in sorted(analysis["blending_stats"].items()):
        print(f"  {blend}: {count}")
    
    print("="*50)
    
    return report

def main():
    parser = argparse.ArgumentParser(description="Validate Minerva's Think Tank model selection and blending")
    parser.add_argument("--url", default="http://127.0.0.1:13083", help="Minerva API URL")
    parser.add_argument("--api-key", help="Anthropic API key (optional, will use environment if not provided)")
    parser.add_argument("--output", default="think_tank_validation_report.json", help="Output file for detailed report")
    
    args = parser.parse_args()
    
    # Run the validation suite
    asyncio.run(run_validation_suite(args.url, args.api_key, args.output))

if __name__ == "__main__":
    main()
