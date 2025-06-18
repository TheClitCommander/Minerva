#!/usr/bin/env python3
"""
Minerva Real Query Monitoring

This script monitors and analyzes real user queries processed by the enhanced
Hugging Face functions during the 50% rollout phase to validate system stability
and response quality.
"""

import os
import sys
import json
import time
import logging
import argparse
import threading
import statistics
import pandas as pd
import matplotlib.pyplot as plt
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
            f'query_monitor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ))
    ]
)

logger = logging.getLogger('query_monitor')

# Ensure project root is in path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import Minerva components (using try/except to handle potential import errors)
try:
    from web.app import process_huggingface_only
    from web.response_handler import clean_ai_response
except ImportError as e:
    logger.error(f"Failed to import Minerva components: {e}")
    logger.error("Please run this script from the Minerva project root directory.")
    sys.exit(1)

class QueryMonitor:
    """
    Monitors and analyzes real user queries processed through Minerva.
    """
    
    def __init__(self, log_file: Optional[str] = None, report_dir: Optional[str] = None):
        """
        Initialize the query monitor.
        
        Args:
            log_file: Path to the log file to monitor. If None, uses the most recent log.
            report_dir: Directory to save reports. If None, uses the default reports directory.
        """
        self.log_file = log_file
        self.report_dir = report_dir or os.path.join(project_root, "reports")
        self.start_time = datetime.now()
        self.query_data = []
        self.error_data = []
        self.performance_data = []
        self.stop_monitoring = False
        
        # Create necessary directories
        os.makedirs(self.report_dir, exist_ok=True)
        
        # If no log file specified, use the most recent log
        if not self.log_file:
            log_dir = os.path.join(project_root, "logs")
            log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
            if log_files:
                log_files.sort(key=lambda f: os.path.getmtime(os.path.join(log_dir, f)), reverse=True)
                self.log_file = os.path.join(log_dir, log_files[0])
                logger.info(f"Using most recent log file: {self.log_file}")
            else:
                self.log_file = os.path.join(log_dir, "minerva.log")
                logger.warning(f"No existing log files found. Will monitor {self.log_file} when it appears.")
        
        logger.info(f"Query monitor initialized. Monitoring log file: {self.log_file}")
    
    def extract_query_data(self, log_line: str) -> Optional[Dict[str, Any]]:
        """
        Extract query data from a log line.
        
        Args:
            log_line: The log line to parse.
            
        Returns:
            Extracted query data or None if the line doesn't contain query data.
        """
        try:
            # Example log line format:
            # 2025-03-03 14:23:45 - minerva.huggingface - INFO - CALL process_huggingface_only - Started with query: "What is quantum computing?"
            if "minerva.huggingface" in log_line and "CALL process_huggingface_only" in log_line:
                # Extract timestamp
                timestamp_str = log_line.split(" - ")[0]
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                
                # Extract query
                if "Started with query:" in log_line:
                    query = log_line.split("Started with query:")[1].strip().strip('"')
                else:
                    # Extract whatever is available after the function name
                    parts = log_line.split("CALL process_huggingface_only - ")[1]
                    query = parts.split(":")[1].strip() if ":" in parts else parts.strip()
                
                # Determine if this is a start or completion log
                is_start = "Started" in log_line
                is_complete = "Completed" in log_line
                
                # Extract processing time if available
                processing_time = None
                if "Completed in" in log_line:
                    time_part = log_line.split("Completed in")[1].strip()
                    processing_time = float(time_part.split("s")[0])
                
                return {
                    "timestamp": timestamp,
                    "query": query,
                    "is_start": is_start,
                    "is_complete": is_complete,
                    "processing_time": processing_time
                }
            
            # Check for error logs
            if "ERROR" in log_line and "process_huggingface_only" in log_line:
                timestamp_str = log_line.split(" - ")[0]
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                
                error_msg = log_line.split("ERROR - ")[1]
                
                return {
                    "timestamp": timestamp,
                    "is_error": True,
                    "error_message": error_msg
                }
            
            return None
        except Exception as e:
            logger.error(f"Error parsing log line: {str(e)}")
            return None
    
    def monitor_log_file(self, interval_seconds: int = 1) -> None:
        """
        Monitor the log file for new queries.
        
        Args:
            interval_seconds: Interval in seconds to check for new log lines.
        """
        logger.info(f"Starting to monitor log file: {self.log_file}")
        
        # If the file doesn't exist yet, wait for it
        while not os.path.exists(self.log_file):
            if self.stop_monitoring:
                return
            logger.warning(f"Log file {self.log_file} does not exist yet. Waiting...")
            time.sleep(5)
        
        # Get the current file size
        file_size = os.path.getsize(self.log_file)
        
        while not self.stop_monitoring:
            try:
                # Check if the file has grown
                current_size = os.path.getsize(self.log_file)
                
                if current_size > file_size:
                    # File has grown, read the new lines
                    with open(self.log_file, "r") as f:
                        f.seek(file_size)
                        new_lines = f.readlines()
                    
                    # Process new lines
                    for line in new_lines:
                        query_data = self.extract_query_data(line)
                        if query_data:
                            if query_data.get("is_error", False):
                                self.error_data.append(query_data)
                                logger.info(f"Detected error: {query_data['error_message'][:50]}...")
                            else:
                                self.query_data.append(query_data)
                                if query_data.get("is_complete", False) and query_data.get("processing_time"):
                                    self.performance_data.append({
                                        "timestamp": query_data["timestamp"],
                                        "processing_time": query_data["processing_time"]
                                    })
                                    logger.info(f"Detected completed query: {query_data['query'][:30]}... in {query_data['processing_time']:.4f}s")
                    
                    # Update file size
                    file_size = current_size
                
                # Sleep before checking again
                time.sleep(interval_seconds)
            
            except Exception as e:
                logger.error(f"Error while monitoring log file: {str(e)}")
                time.sleep(5)  # Wait a bit longer in case of errors
    
    def start_monitoring(self, interval_seconds: int = 1) -> None:
        """
        Start monitoring the log file in a separate thread.
        
        Args:
            interval_seconds: Interval in seconds to check for new log lines.
        """
        self.monitor_thread = threading.Thread(
            target=self.monitor_log_file,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Monitoring thread started")
    
    def stop(self) -> None:
        """Stop monitoring the log file."""
        self.stop_monitoring = True
        if hasattr(self, "monitor_thread"):
            self.monitor_thread.join(timeout=5)
        logger.info("Monitoring stopped")
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics based on the collected query data."""
        if not self.performance_data:
            return {"error": "No performance data collected yet"}
        
        processing_times = [data["processing_time"] for data in self.performance_data]
        
        stats = {
            "total_queries": len(self.query_data),
            "completed_queries": len(self.performance_data),
            "error_count": len(self.error_data),
            "processing_time": {
                "min": min(processing_times) if processing_times else 0,
                "max": max(processing_times) if processing_times else 0,
                "mean": statistics.mean(processing_times) if processing_times else 0,
                "median": statistics.median(processing_times) if processing_times else 0,
                "stdev": statistics.stdev(processing_times) if len(processing_times) > 1 else 0
            }
        }
        
        # Calculate error rate
        if stats["total_queries"] > 0:
            stats["error_rate"] = (stats["error_count"] / stats["total_queries"]) * 100
        else:
            stats["error_rate"] = 0
        
        return stats
    
    def generate_performance_chart(self, save_path: Optional[str] = None) -> str:
        """
        Generate a performance chart based on the collected data.
        
        Args:
            save_path: Path to save the chart. If None, a default path is used.
            
        Returns:
            Path to the saved chart.
        """
        if not self.performance_data:
            logger.warning("No performance data to generate chart")
            return ""
        
        try:
            # Convert to DataFrame for easier plotting
            df = pd.DataFrame(self.performance_data)
            
            # Set the timestamp as index
            df.set_index("timestamp", inplace=True)
            
            # Resample to smooth the data (e.g., average by minute)
            resampled = df.resample("1min").mean()
            
            # Create the plot
            plt.figure(figsize=(12, 6))
            
            # Plot the raw data points
            plt.scatter(
                df.index, 
                df["processing_time"],
                alpha=0.5,
                label="Individual Queries"
            )
            
            # Plot the trend line
            plt.plot(
                resampled.index,
                resampled["processing_time"],
                "r-",
                linewidth=2,
                label="1-Minute Average"
            )
            
            # Add labels and title
            plt.xlabel("Time")
            plt.ylabel("Processing Time (seconds)")
            plt.title("Query Processing Performance Over Time")
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Add a horizontal line for the average
            avg_time = statistics.mean(df["processing_time"])
            plt.axhline(y=avg_time, color="g", linestyle="--", alpha=0.7, label=f"Overall Average: {avg_time:.4f}s")
            
            # Annotate with statistics
            stats = self.calculate_statistics()
            plt.figtext(
                0.02, 0.02,
                f"Total Queries: {stats['total_queries']}\n"
                f"Average Time: {stats['processing_time']['mean']:.4f}s\n"
                f"Error Rate: {stats['error_rate']:.2f}%",
                bbox={"facecolor": "white", "alpha": 0.7, "pad": 5}
            )
            
            # Save the plot
            if save_path is None:
                os.makedirs(os.path.join(self.report_dir, "charts"), exist_ok=True)
                save_path = os.path.join(
                    self.report_dir, 
                    "charts", 
                    f"performance_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
            
            plt.tight_layout()
            plt.savefig(save_path)
            plt.close()
            
            logger.info(f"Performance chart saved to {save_path}")
            return save_path
        
        except Exception as e:
            logger.error(f"Error generating performance chart: {str(e)}")
            return ""
    
    def generate_report(self, include_chart: bool = True) -> Dict[str, Any]:
        """
        Generate a comprehensive report based on the collected data.
        
        Args:
            include_chart: Whether to include a performance chart in the report.
            
        Returns:
            The generated report.
        """
        stats = self.calculate_statistics()
        
        # Prepare the report
        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_duration": str(datetime.now() - self.start_time),
            "log_file": self.log_file,
            "statistics": stats,
            "recent_errors": self.error_data[-10:] if self.error_data else []
        }
        
        # Generate and include chart if requested
        if include_chart:
            chart_path = self.generate_performance_chart()
            if chart_path:
                report["performance_chart"] = chart_path
        
        # Save the report
        report_path = os.path.join(
            self.report_dir,
            f"query_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {report_path}")
        return report
    
    def print_summary(self) -> None:
        """Print a summary of the collected data."""
        stats = self.calculate_statistics()
        
        print("\n")
        print("="*80)
        print(f"QUERY MONITORING SUMMARY - {datetime.now().isoformat()}")
        print("="*80)
        print(f"Monitoring Duration: {datetime.now() - self.start_time}")
        print(f"Log File: {self.log_file}")
        print(f"Total Queries Detected: {stats['total_queries']}")
        print(f"Completed Queries: {stats['completed_queries']}")
        print(f"Errors: {stats['error_count']} ({stats['error_rate']:.2f}%)")
        
        if stats.get("processing_time"):
            pt = stats["processing_time"]
            print("\nProcessing Time (seconds):")
            print(f"  Min: {pt['min']:.4f}")
            print(f"  Max: {pt['max']:.4f}")
            print(f"  Mean: {pt['mean']:.4f}")
            print(f"  Median: {pt['median']:.4f}")
            print(f"  StdDev: {pt['stdev']:.4f}")
        
        if self.error_data:
            print("\nMost Recent Errors:")
            for i, error in enumerate(self.error_data[-3:]):
                print(f"  {i+1}. {error['timestamp']} - {error['error_message'][:50]}...")
        
        print("="*80)

def main():
    """Run the query monitoring script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Monitor real user queries processed by Minerva")
    parser.add_argument("--log-file", type=str, help="Path to the log file to monitor")
    parser.add_argument("--report-dir", type=str, help="Directory to save reports")
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in minutes")
    parser.add_argument("--interval", type=int, default=1, help="Monitoring interval in seconds")
    parser.add_argument("--chart", action="store_true", help="Generate performance chart")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    print("="*80)
    print("MINERVA REAL QUERY MONITORING")
    print("="*80)
    print(f"Monitoring real user queries for {args.duration} minutes")
    print("="*80)
    
    # Initialize the query monitor
    monitor = QueryMonitor(log_file=args.log_file, report_dir=args.report_dir)
    
    try:
        # Start monitoring
        monitor.start_monitoring(interval_seconds=args.interval)
        
        # Calculate the end time
        end_time = datetime.now() + timedelta(minutes=args.duration)
        
        # Run until the specified duration
        while datetime.now() < end_time:
            # Sleep for a while
            time.sleep(30)
            
            # Print a summary
            monitor.print_summary()
        
        # Generate a final report
        monitor.generate_report(include_chart=args.chart)
        
        # Print a final summary
        monitor.print_summary()
        
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    finally:
        # Stop monitoring
        monitor.stop()
        
        # Generate a final report
        monitor.generate_report(include_chart=args.chart)
        
        print("\nMonitoring complete! Check the reports directory for detailed statistics.")

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "reports"), exist_ok=True)
    
    main()
