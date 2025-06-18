#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Think Tank Analyzer

This script analyzes how Minerva's Think Tank mode is working, logging which models
are being used, how responses are being selected, and identifying any issues or 
missing model integrations.
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("think_tank_analysis.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("think_tank_analyzer")

# Make sure to use the minimal processor which doesn't have syntax errors
try:
    from web.multi_model_processor_minimal import (
        route_request,
        get_query_tags,
        calculate_query_complexity,
        classify_query_type,
        prioritize_models_for_query,
        MODEL_CAPABILITIES
    )
    logger.info("Successfully imported from minimal processor")
except ImportError as e:
    logger.error(f"Failed to import from minimal processor: {e}")
    sys.exit(1)

# Add the Minerva web directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "web"))

# Import required modules from Minerva
try:
    from web.multi_ai_coordinator import MultiAICoordinator
    from web.model_registry import ModelRegistry
    # route_request is already imported from the minimal processor
    from web.ensemble_validator import EnsembleValidator
    logger.info("Successfully imported core Minerva modules")
except ImportError as e:
    logger.error(f"Failed to import Minerva modules: {e}")
    traceback.print_exc()
    sys.exit(1)

class ThinkTankAnalyzer:
    """
    Analyzes the Think Tank mode of Minerva, checking which models are used
    and how responses are selected and combined.
    """
    
    def __init__(self):
        """Initialize the analyzer"""
        self.model_registry = ModelRegistry()
        self.coordinator = MultiAICoordinator()
        self.ensemble_validator = EnsembleValidator()
        self.model_usage_counts = {}
        self.model_cache = {}
        
    def analyze_registered_models(self) -> Dict[str, Any]:
        """
        Analyze which models are registered and available in the system
        """
        try:
            all_models = self.model_registry.get_all_models()
            logger.info(f"Found {len(all_models)} registered models")
            
            # Categorize models
            model_categories = {
                "commercial": [],
                "open_source": [],
                "local": [],
                "unknown": []
            }
            
            for model_name, model_info in all_models.items():
                if not model_info:
                    # Handle empty model info
                    model_categories["unknown"].append(model_name)
                    continue
                    
                # Categorize based on model name patterns
                if any(name in model_name.lower() for name in ["gpt4", "gpt-4", "claude", "gemini"]):
                    model_categories["commercial"].append(model_name)
                elif any(name in model_name.lower() for name in ["huggingface", "distilgpt", "distilgpt2", "gpt4all"]):
                    model_categories["local"].append(model_name)
                elif any(name in model_name.lower() for name in ["mistral", "llama", "mpt"]):
                    model_categories["open_source"].append(model_name)
                else:
                    model_categories["unknown"].append(model_name)
            
            # Log the findings
            for category, models in model_categories.items():
                logger.info(f"Category '{category}' has {len(models)} models: {models}")
                
            return {
                "total_models": len(all_models),
                "categories": model_categories,
                "all_models": all_models
            }
        except Exception as e:
            logger.error(f"Error analyzing registered models: {e}")
            traceback.print_exc()
            return {"error": str(e)}
    
    async def analyze_model_usage(self, sample_queries: List[str]) -> Dict[str, Any]:
        """
        Analyze which models are actually used for different types of queries
        
        Args:
            sample_queries: List of sample queries to test
            
        Returns:
            Dictionary with analysis results
        """
        results = {
            "query_results": {},
            "model_usage_summary": {},
            "missing_models": [],
            "errors": []
        }
        
        # Reset usage counts
        self.model_usage_counts = {}
        
        # Process each query
        for query in sample_queries:
            try:
                logger.info(f"Testing query: {query}")
                
                # Override the internal model processor with our monitoring version
                original_processors = self.coordinator.model_processors.copy()
                self.monitor_model_processors(original_processors)
                
                # Process the message with think_tank mode
                response = await self.coordinator.process_message(
                    user_id="analyzer",
                    message=query,
                    message_id=f"analyzer_{hash(query)}",
                    mode="think_tank"
                )
                
                # Restore original processors
                self.coordinator.model_processors = original_processors
                
                # Record the result
                results["query_results"][query] = {
                    "model_used": response.get("model_used", "unknown"),
                    "quality_score": response.get("quality_score", 0),
                    "processing_time": response.get("processing_time", 0),
                    "models_attempted": list(self.model_cache.get(query, {}).keys()),
                    "response_length": len(response.get("response", "")),
                    "models_responded": [model for model, resp in self.model_cache.get(query, {}).items() 
                                         if resp and (isinstance(resp, str) or (isinstance(resp, dict) and resp.get("response")))]
                }
                
                # Track overall model usage
                for model in results["query_results"][query]["models_attempted"]:
                    if model not in results["model_usage_summary"]:
                        results["model_usage_summary"][model] = {
                            "attempted": 0,
                            "responded": 0,
                            "selected": 0
                        }
                    results["model_usage_summary"][model]["attempted"] += 1
                
                for model in results["query_results"][query]["models_responded"]:
                    if model in results["model_usage_summary"]:
                        results["model_usage_summary"][model]["responded"] += 1
                
                selected_model = response.get("model_used", "unknown")
                if selected_model in results["model_usage_summary"]:
                    results["model_usage_summary"][model]["selected"] += 1
                
                logger.info(f"Query '{query}' used model: {response.get('model_used', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                traceback.print_exc()
                results["errors"].append({"query": query, "error": str(e)})
                
        # Identify missing models
        all_models = self.model_registry.get_all_models()
        for model_name in all_models:
            if model_name not in results["model_usage_summary"]:
                results["missing_models"].append(model_name)
                
        logger.info(f"Analysis complete. Models used: {list(results['model_usage_summary'].keys())}")
        logger.info(f"Missing models: {results['missing_models']}")
        
        return results
    
    def monitor_model_processors(self, original_processors):
        """
        Replace the model processors with monitoring versions
        """
        for model_name, processor_func in original_processors.items():
            # Create a custom monitoring wrapper for each processor
            async def monitored_processor(message, original_func=processor_func, model=model_name):
                logger.info(f"Calling model processor: {model}")
                self.model_usage_counts[model] = self.model_usage_counts.get(model, 0) + 1
                
                try:
                    # Call the original processor
                    result = await original_func(message)
                    
                    # Cache the result for analysis
                    if message not in self.model_cache:
                        self.model_cache[message] = {}
                    self.model_cache[message][model] = result
                    
                    # Log what happened
                    if isinstance(result, str) and result.strip():
                        logger.info(f"Model {model} returned string response of length {len(result)}")
                    elif isinstance(result, dict) and "response" in result:
                        logger.info(f"Model {model} returned dict response with quality {result.get('quality_score', 'unknown')}")
                    else:
                        logger.warning(f"Model {model} returned unexpected response format: {type(result)}")
                        
                    return result
                except Exception as e:
                    logger.error(f"Error in model processor {model}: {e}")
                    if message not in self.model_cache:
                        self.model_cache[message] = {}
                    self.model_cache[message][model] = {"error": str(e)}
                    return {"error": str(e), "model_used": model}
            
            # Replace the original processor with our monitored version
            self.coordinator.model_processors[model_name] = monitored_processor
    
    def analyze_model_routing(self, sample_queries: List[str]) -> Dict[str, Any]:
        """
        Analyze how the route_request function selects models for different query types
        """
        results = {}
        
        for query in sample_queries:
            try:
                # Call the routing function
                routing_decision = route_request(query)
                
                # Record the results
                results[query] = {
                    "recommended_models": routing_decision.get("recommended_models", []),
                    "query_type": routing_decision.get("query_type", "unknown"),
                    "complexity": routing_decision.get("complexity", 0),
                    "is_technical": routing_decision.get("is_technical", False),
                    "is_creative": routing_decision.get("is_creative", False)
                }
                
                logger.info(f"Query '{query}' routing: {results[query]}")
                
            except Exception as e:
                logger.error(f"Error in routing analysis for query '{query}': {e}")
                results[query] = {"error": str(e)}
                
        return results

async def main():
    """
    Run the Think Tank analysis
    """
    analyzer = ThinkTankAnalyzer()
    
    # Sample queries covering different types of requests
    sample_queries = [
        "What's the weather like today?",
        "Explain quantum computing to me",
        "Write a short poem about artificial intelligence",
        "What is the capital of France?",
        "Analyze the pros and cons of solar energy",
        "Can you help debug this Python code: for i in range(10): print(i]",
        "How does a neural network work?",
        "Suggest a recipe for chocolate chip cookies",
        "What are the key differences between Python and JavaScript?",
        "Tell me a joke about programming"
    ]
    
    logger.info("Starting Think Tank analysis")
    
    # 1. Analyze registered models
    model_analysis = analyzer.analyze_registered_models()
    logger.info(f"Model analysis: {json.dumps(model_analysis, indent=2)}")
    
    # 2. Analyze model routing
    routing_analysis = analyzer.analyze_model_routing(sample_queries)
    logger.info(f"Routing analysis: {json.dumps(routing_analysis, indent=2)}")
    
    # 3. Analyze model usage in think tank mode
    usage_analysis = await analyzer.analyze_model_usage(sample_queries[:3])  # Just use a few queries to save time
    
    # Write results to file
    with open("think_tank_analysis_results.json", "w") as f:
        json.dump({
            "model_analysis": model_analysis,
            "routing_analysis": routing_analysis,
            "usage_analysis": usage_analysis
        }, f, indent=2)
    
    logger.info("Analysis complete! Results written to think_tank_analysis_results.json")

if __name__ == "__main__":
    asyncio.run(main())
