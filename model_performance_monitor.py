#!/usr/bin/env python3
"""
Minerva AI Model Performance Monitoring System

This script provides real-time and historical analysis of:
1. Model selection decisions 
2. Response quality and confidence scores
3. Blending effectiveness
4. API reliability (especially for Claude-3)

Run this alongside Minerva to track performance metrics.
"""
import os
import re
import json
import time
import logging
import argparse
import subprocess
from datetime import datetime
from collections import defaultdict
import concurrent.futures
import requests
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/model_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('model_monitor')

# Default test queries representing different types of requests
DEFAULT_TEST_QUERIES = [
    {"type": "factual", "query": "What are the key factors affecting Maine's real estate market in 2025?"},
    {"type": "technical", "query": "Explain quantum computing in simple terms."},
    {"type": "creative", "query": "Write a short poem about artificial intelligence."},
    {"type": "analytical", "query": "Compare Tesla and Toyota for long-term investment."},
    {"type": "code", "query": "Write a Python function to find prime numbers."}
]

class ModelPerformanceMonitor:
    def __init__(self, minerva_url="http://127.0.0.1:13083", log_file="logs/minerva.log"):
        self.minerva_url = minerva_url
        self.log_file = log_file
        self.stats = {
            "model_selections": defaultdict(int),
            "model_confidence": defaultdict(list),
            "response_times": defaultdict(list),
            "api_errors": defaultdict(int),
            "blending_stats": defaultdict(int)
        }
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
    def tail_log(self, n_lines=100):
        """Get the last n lines from the log file"""
        try:
            result = subprocess.run(
                ["tail", "-n", str(n_lines), self.log_file], 
                capture_output=True, 
                text=True
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Error reading log file: {str(e)}")
            return ""
            
    def parse_log_for_model_selection(self):
        """Parse log file for model selection decisions"""
        log_content = self.tail_log(1000)  # Get last 1000 lines
        
        # Extract model selection patterns
        model_selections = re.findall(r"Selected model: (\w+) with confidence: ([\d\.]+)", log_content)
        routing_decisions = re.findall(r"Routing decision: Query type: (\w+), Selected: (\w+)", log_content)
        api_errors = re.findall(r"Error processing message with (\w+): (.+)", log_content)
        
        # Update stats
        for model, confidence in model_selections:
            self.stats["model_selections"][model] += 1
            self.stats["model_confidence"][model].append(float(confidence))
            
        for error_model, error_msg in api_errors:
            self.stats["api_errors"][error_model] += 1
            
        # Look for blending information
        blending_info = re.findall(r"Blended response: Used (\d+) models", log_content)
        for count in blending_info:
            self.stats["blending_stats"][int(count)] += 1
            
        return len(model_selections) > 0
            
    def test_api_endpoint(self, query, endpoint="/api/v1/advanced-think-tank", debug_mode=True):
        """Test the API endpoint with a specific query"""
        headers = {
            "Content-Type": "application/json"
        }
        
        if debug_mode:
            headers["X-Debug-Mode"] = "true"
            
        data = {
            "message": query
        }
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.minerva_url}{endpoint}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # Extract model information if available
                    model_used = result.get("model_used", "unknown")
                    self.stats["response_times"][model_used].append(processing_time)
                    
                    # Look for model_info field which would contain blending details
                    model_info = result.get("model_info", {})
                    if model_info:
                        # Count how many models contributed
                        contributing_models = model_info.get("contributing_models", [])
                        if contributing_models:
                            self.stats["blending_stats"][len(contributing_models)] += 1
                    
                    return {
                        "success": True,
                        "processing_time": processing_time,
                        "response": result
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "Invalid JSON response",
                        "processing_time": processing_time
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

    def run_batch_tests(self, test_queries=None, parallel=True):
        """Run a batch of test queries to evaluate performance"""
        if test_queries is None:
            test_queries = DEFAULT_TEST_QUERIES
            
        results = {}
        
        if parallel:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(test_queries))) as executor:
                future_to_query = {
                    executor.submit(self.test_api_endpoint, query["query"]): 
                    (query_type, query["query"]) 
                    for query_type, query in [(q["type"], q) for q in test_queries]
                }
                
                for future in concurrent.futures.as_completed(future_to_query):
                    query_type, query = future_to_query[future]
                    try:
                        result = future.result()
                        results[query_type] = result
                        logger.info(f"Query type: {query_type}, Success: {result['success']}, Time: {result['processing_time']:.2f}s")
                    except Exception as e:
                        logger.error(f"Error testing query {query}: {str(e)}")
        else:
            for query in test_queries:
                query_type = query["type"]
                result = self.test_api_endpoint(query["query"])
                results[query_type] = result
                logger.info(f"Query type: {query_type}, Success: {result['success']}, Time: {result['processing_time']:.2f}s")
                
        return results

    def generate_report(self):
        """Generate a report on model performance"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "model_selection_count": dict(self.stats["model_selections"]),
            "average_confidence": {
                model: sum(scores)/len(scores) if scores else 0 
                for model, scores in self.stats["model_confidence"].items()
            },
            "average_response_time": {
                model: sum(times)/len(times) if times else 0 
                for model, times in self.stats["response_times"].items()
            },
            "api_errors": dict(self.stats["api_errors"]),
            "blending_stats": dict(self.stats["blending_stats"])
        }
        
        # Save report to file
        report_path = f"logs/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Performance report saved to {report_path}")
        
        # Print summary
        print("\n===== MINERVA AI MODEL PERFORMANCE REPORT =====")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nModel Selection Distribution:")
        for model, count in sorted(report["model_selection_count"].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {model}: {count} selections")
            
        print("\nAverage Confidence Scores:")
        for model, score in sorted(report["average_confidence"].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {model}: {score:.2f}")
            
        print("\nAverage Response Times:")
        for model, time_val in sorted(report["average_response_time"].items(), key=lambda x: x[1]):
            print(f"  - {model}: {time_val:.2f}s")
            
        if report["api_errors"]:
            print("\nAPI Errors:")
            for model, count in sorted(report["api_errors"].items(), key=lambda x: x[1], reverse=True):
                print(f"  - {model}: {count} errors")
                
        if report["blending_stats"]:
            print("\nBlending Statistics:")
            for count, freq in sorted(report["blending_stats"].items()):
                print(f"  - Responses using {count} models: {freq}")
                
        print("\nDetailed report saved to:", report_path)
        print("="*50)
        
        return report
        
    def monitor_real_time(self, duration=300, interval=10):
        """Monitor Minerva in real-time for a specified duration"""
        logger.info(f"Starting real-time monitoring for {duration} seconds")
        
        end_time = time.time() + duration
        found_data = False
        
        while time.time() < end_time:
            if self.parse_log_for_model_selection():
                found_data = True
                
            time.sleep(interval)
            
        if not found_data:
            logger.warning("No model selection data found in logs during monitoring period")
            
        return self.generate_report()

def main():
    parser = argparse.ArgumentParser(description="Monitor Minerva AI model performance")
    parser.add_argument("--url", default="http://127.0.0.1:13083", help="Minerva API URL")
    parser.add_argument("--log-file", default="logs/minerva.log", help="Path to Minerva log file")
    parser.add_argument("--mode", choices=["realtime", "test", "both"], default="both", 
                        help="Monitoring mode: realtime log analysis, test queries, or both")
    parser.add_argument("--duration", type=int, default=300, help="Duration (seconds) for real-time monitoring")
    parser.add_argument("--test-file", help="JSON file with custom test queries")
    
    args = parser.parse_args()
    
    # Initialize the monitor
    monitor = ModelPerformanceMonitor(args.url, args.log_file)
    
    # Load custom test queries if specified
    test_queries = DEFAULT_TEST_QUERIES
    if args.test_file and os.path.exists(args.test_file):
        try:
            with open(args.test_file, 'r') as f:
                test_queries = json.load(f)
        except Exception as e:
            logger.error(f"Error loading test queries from {args.test_file}: {str(e)}")
    
    # Run in specified mode
    if args.mode in ["test", "both"]:
        logger.info("Running test queries...")
        monitor.run_batch_tests(test_queries)
        
    if args.mode in ["realtime", "both"]:
        logger.info(f"Starting real-time monitoring for {args.duration} seconds...")
        monitor.monitor_real_time(args.duration)
    
    # Generate final report
    monitor.generate_report()

if __name__ == "__main__":
    main()
