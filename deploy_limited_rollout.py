#!/usr/bin/env python3
"""
Minerva Limited Rollout Deployment

This script implements a controlled deployment of the enhanced Hugging Face
functions to a limited percentage of user traffic (initially 10%).
"""

import os
import sys
import json
import time
import random
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'logs', 
            f'deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ))
    ]
)

logger = logging.getLogger('deployment')

# Ensure project root is in path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import Minerva components (using try/except to handle potential import errors)
try:
    from web.app import process_huggingface_only
except ImportError as e:
    logger.error(f"Failed to import Minerva components: {e}")
    logger.error("Please run this script from the Minerva project root directory.")
    sys.exit(1)

class DeploymentController:
    """
    Controls the rollout of enhanced Hugging Face functions to a limited percentage of traffic.
    """
    
    def __init__(self, traffic_percentage: float = 10.0, config_file: Optional[str] = None):
        """
        Initialize the deployment controller.
        
        Args:
            traffic_percentage: Percentage of traffic to route through enhanced system (0-100).
            config_file: Optional path to deployment configuration file.
        """
        self.traffic_percentage = max(0.0, min(100.0, traffic_percentage))
        self.start_time = datetime.now()
        self.config_file = config_file or os.path.join(project_root, "config", "deployment_config.json")
        self.stats = {
            "start_time": self.start_time.isoformat(),
            "traffic_percentage": self.traffic_percentage,
            "total_requests": 0,
            "enhanced_requests": 0,
            "legacy_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "errors": []
        }
        
        # Load configuration if exists
        self.config = self._load_config()
        
        # Create necessary directories
        os.makedirs(os.path.join(project_root, "config"), exist_ok=True)
        os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)
        
        logger.info(f"Deployment controller initialized with {self.traffic_percentage}% traffic")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration from file."""
        default_config = {
            "traffic_percentage": self.traffic_percentage,
            "monitoring_interval_seconds": 60,
            "error_threshold_percent": 5.0,
            "response_time_threshold_ms": 2000,
            "monitoring_endpoints": [
                {"name": "Local Health Check", "url": "http://localhost:5000/health"},
                {"name": "Performance Metrics", "url": "http://localhost:5000/metrics"}
            ],
            "feature_flags": {
                "enhanced_parameter_optimization": True,
                "enhanced_response_cleaning": True,
                "enhanced_error_handling": True,
                "detailed_logging": True
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {self.config_file}")
                    return config
            else:
                # Create default config file
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                with open(self.config_file, "w") as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default configuration at {self.config_file}")
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return default_config
    
    def should_use_enhanced_system(self) -> bool:
        """Determine if a request should use the enhanced system based on traffic percentage."""
        return random.random() * 100 < self.traffic_percentage
    
    def record_request_stats(self, request_id: str, used_enhanced: bool, successful: bool, 
                            response_time: float, error: Optional[str] = None) -> None:
        """
        Record statistics for a single request.
        
        Args:
            request_id: Unique identifier for the request.
            used_enhanced: Whether the enhanced system was used.
            successful: Whether the request was successful.
            response_time: Time taken to process the request (in seconds).
            error: Optional error message if the request failed.
        """
        self.stats["total_requests"] += 1
        
        if used_enhanced:
            self.stats["enhanced_requests"] += 1
        else:
            self.stats["legacy_requests"] += 1
        
        if successful:
            self.stats["successful_requests"] += 1
            
            # Update average response time
            current_avg = self.stats["average_response_time"]
            total_successful = self.stats["successful_requests"]
            self.stats["average_response_time"] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
        else:
            self.stats["failed_requests"] += 1
            
            if error:
                self.stats["errors"].append({
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat(),
                    "used_enhanced": used_enhanced,
                    "error": error,
                    "response_time": response_time
                })
        
        # Log detailed stats
        logger.info(
            f"Request {request_id} - " 
            f"{'Enhanced' if used_enhanced else 'Legacy'} - "
            f"{'Success' if successful else 'Failed'} - "
            f"Time: {response_time:.4f}s"
        )
        
        # Save stats periodically
        if self.stats["total_requests"] % 10 == 0:
            self.save_stats()
    
    def save_stats(self) -> None:
        """Save current statistics to a JSON file."""
        stats_file = os.path.join(
            project_root, 
            "logs", 
            f"deployment_stats_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            with open(stats_file, "w") as f:
                json.dump(self.stats, f, indent=2)
            logger.debug(f"Saved stats to {stats_file}")
        except Exception as e:
            logger.error(f"Error saving stats: {str(e)}")
    
    def update_traffic_percentage(self, new_percentage: float) -> None:
        """
        Update the percentage of traffic going to the enhanced system.
        
        Args:
            new_percentage: New percentage (0-100) of traffic to route.
        """
        old_percentage = self.traffic_percentage
        self.traffic_percentage = max(0.0, min(100.0, new_percentage))
        
        logger.info(f"Updated traffic percentage from {old_percentage}% to {self.traffic_percentage}%")
        
        # Update config
        self.config["traffic_percentage"] = self.traffic_percentage
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating config: {str(e)}")
        
        # Update stats
        self.stats["traffic_percentage"] = self.traffic_percentage
        self.save_stats()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the deployment statistics."""
        current_time = datetime.now()
        running_time = current_time - self.start_time
        hours, remainder = divmod(running_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "start_time": self.start_time.isoformat(),
            "current_time": current_time.isoformat(),
            "running_time": f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}",
            "traffic_percentage": self.traffic_percentage,
            "total_requests": self.stats["total_requests"],
            "enhanced_requests": self.stats["enhanced_requests"],
            "legacy_requests": self.stats["legacy_requests"],
            "enhanced_percentage": (
                (self.stats["enhanced_requests"] / self.stats["total_requests"]) * 100
                if self.stats["total_requests"] > 0 else 0
            ),
            "success_rate": (
                (self.stats["successful_requests"] / self.stats["total_requests"]) * 100
                if self.stats["total_requests"] > 0 else 0
            ),
            "enhanced_success_rate": (
                (self.stats["successful_requests"] / self.stats["enhanced_requests"]) * 100
                if self.stats["enhanced_requests"] > 0 else 0
            ),
            "average_response_time": self.stats["average_response_time"],
            "error_count": self.stats["failed_requests"],
            "error_rate": (
                (self.stats["failed_requests"] / self.stats["total_requests"]) * 100
                if self.stats["total_requests"] > 0 else 0
            )
        }
    
    def print_summary(self) -> None:
        """Print a summary of the deployment statistics."""
        summary = self.get_summary()
        
        print("\n")
        print("="*80)
        print(f"DEPLOYMENT SUMMARY - {summary['current_time']}")
        print("="*80)
        print(f"Running Time: {summary['running_time']}")
        print(f"Traffic Percentage: {summary['traffic_percentage']:.1f}%")
        print(f"Total Requests: {summary['total_requests']}")
        print(f"  ├─ Enhanced: {summary['enhanced_requests']} ({summary['enhanced_percentage']:.1f}%)")
        print(f"  └─ Legacy: {summary['legacy_requests']}")
        print(f"Success Rate: {summary['success_rate']:.2f}%")
        print(f"Enhanced Success Rate: {summary['enhanced_success_rate']:.2f}%")
        print(f"Average Response Time: {summary['average_response_time'] * 1000:.2f}ms")
        print(f"Errors: {summary['error_count']} ({summary['error_rate']:.2f}%)")
        print("="*80)

def simulate_deployment(args):
    """
    Simulate a limited deployment of the enhanced Hugging Face functions.
    
    This is a demonstration of how the system would deploy the enhanced functions
    to a limited percentage of traffic.
    """
    # Initialize deployment controller
    controller = DeploymentController(traffic_percentage=args.percentage)
    
    print("="*80)
    print("MINERVA LIMITED DEPLOYMENT SIMULATION")
    print("="*80)
    print(f"Simulating {args.percentage}% traffic to enhanced Hugging Face functions")
    print(f"Running for {args.duration} minutes")
    print("="*80)
    
    # Define some test requests
    test_queries = [
        "What is the capital of France?",
        "Explain quantum computing in simple terms.",
        "Write a Python function to calculate the Fibonacci sequence.",
        "What are the main causes of climate change?",
        "Compare and contrast different leadership styles.",
        "How does the immune system work?",
        "Analyze the themes in Shakespeare's Macbeth.",
        "What are the key principles of machine learning?",
        "Discuss the ethical implications of artificial intelligence."
    ]
    
    # Calculate the end time
    end_time = datetime.now() + timedelta(minutes=args.duration)
    
    # Run the simulation
    request_id = 1
    while datetime.now() < end_time:
        try:
            # Select a random query
            query = random.choice(test_queries)
            
            # Determine if this request should use the enhanced system
            use_enhanced = controller.should_use_enhanced_system()
            
            # Simulate processing the request
            start_time = time.time()
            
            # In a real deployment, this would call different implementations
            # based on use_enhanced. Here we just simulate it.
            if use_enhanced:
                # Simulate enhanced system (faster on average but with occasional failures)
                success = random.random() < 0.98  # 98% success rate
                processing_time = random.uniform(0.1, 0.3)  # 100-300ms
                error = "Simulated error in enhanced system" if not success else None
            else:
                # Simulate legacy system (slower but more reliable)
                success = random.random() < 0.99  # 99% success rate
                processing_time = random.uniform(0.2, 0.5)  # 200-500ms
                error = "Simulated error in legacy system" if not success else None
            
            # Add artificial delay to simulate processing
            time.sleep(processing_time)
            
            end_time_req = time.time()
            elapsed_time = end_time_req - start_time
            
            # Record the request stats
            controller.record_request_stats(
                request_id=f"REQ-{request_id}",
                used_enhanced=use_enhanced,
                successful=success,
                response_time=elapsed_time,
                error=error
            )
            
            request_id += 1
            
            # Print summary periodically
            if request_id % 20 == 0:
                controller.print_summary()
            
            # Random delay between requests
            time.sleep(random.uniform(0.1, 0.5))
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
            break
        except Exception as e:
            logger.error(f"Error in simulation: {str(e)}")
            time.sleep(1)  # Add a delay in case of errors
    
    # Print final summary
    controller.print_summary()
    
    # Save final stats
    controller.save_stats()
    
    print("\nSimulation complete! Check the logs directory for detailed statistics.")

def main():
    """Run the limited deployment script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run a limited deployment of enhanced Hugging Face functions")
    parser.add_argument("--percentage", type=float, default=10.0, help="Percentage of traffic to route to enhanced system")
    parser.add_argument("--duration", type=int, default=5, help="Duration of simulation in minutes")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Run the deployment simulation
    simulate_deployment(args)

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)
    
    main()
