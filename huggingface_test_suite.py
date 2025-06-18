#!/usr/bin/env python3
"""
Comprehensive test suite for Minerva's enhanced Hugging Face processing.

This script runs all the test scripts we've developed to validate the 
enhanced Hugging Face processing functionality before integration into
the main Minerva system.
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("minerva.test_suite")

# List of test scripts
TEST_SCRIPTS = [
    "huggingface_test_enhanced.py",
    "huggingface_edge_cases_test.py",
    "huggingface_quality_benchmark.py"
]

def run_test_script(script_path, report_file=None):
    """Run a test script and capture output"""
    logger.info(f"Running test script: {script_path}")
    
    start_time = time.time()
    try:
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log success
        duration = time.time() - start_time
        logger.info(f"Test script {script_path} completed successfully in {duration:.2f}s")
        
        # Save output to report file if specified
        if report_file:
            with open(report_file, 'a') as f:
                f.write(f"\n\n{'=' * 80}\n")
                f.write(f"TEST SCRIPT: {script_path}\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(result.stdout)
                if result.stderr:
                    f.write("\nSTDERR:\n")
                    f.write(result.stderr)
        
        return True, result.stdout
        
    except subprocess.CalledProcessError as e:
        # Log failure
        duration = time.time() - start_time
        logger.error(f"Test script {script_path} failed after {duration:.2f}s")
        logger.error(f"Exit code: {e.returncode}")
        
        # Save error output to report file if specified
        if report_file:
            with open(report_file, 'a') as f:
                f.write(f"\n\n{'=' * 80}\n")
                f.write(f"TEST SCRIPT: {script_path} (FAILED)\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(e.stdout)
                if e.stderr:
                    f.write("\nSTDERR:\n")
                    f.write(e.stderr)
        
        return False, e.stdout + "\n" + e.stderr
    
    except Exception as e:
        # Log general exception
        duration = time.time() - start_time
        logger.error(f"Error running test script {script_path}: {str(e)}")
        
        # Save error to report file if specified
        if report_file:
            with open(report_file, 'a') as f:
                f.write(f"\n\n{'=' * 80}\n")
                f.write(f"TEST SCRIPT: {script_path} (ERROR)\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(str(e))
        
        return False, str(e)

def run_all_tests(report_dir=None):
    """Run all test scripts and generate a report"""
    logger.info("Starting comprehensive test suite for Hugging Face processing")
    
    # Create report directory if specified
    if report_dir:
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, f"test_report_{int(time.time())}.txt")
        logger.info(f"Test report will be saved to: {report_file}")
        
        # Initialize report file
        with open(report_file, 'w') as f:
            f.write("MINERVA HUGGING FACE PROCESSING - TEST SUITE REPORT\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    else:
        report_file = None
    
    # Track results
    results = []
    
    # Run each test script
    for script in TEST_SCRIPTS:
        script_path = os.path.join(os.path.dirname(__file__), script)
        if os.path.exists(script_path):
            success, output = run_test_script(script_path, report_file)
            results.append({
                "script": script,
                "success": success,
                "output": output[:500] + "..." if len(output) > 500 else output
            })
        else:
            logger.warning(f"Test script not found: {script_path}")
            results.append({
                "script": script,
                "success": False,
                "output": "Script not found"
            })
    
    # Generate summary
    success_count = sum(1 for result in results if result["success"])
    logger.info(f"Test suite completed: {success_count}/{len(results)} tests passed")
    
    # Add summary to report
    if report_file:
        with open(report_file, 'a') as f:
            f.write(f"\n\n{'=' * 80}\n")
            f.write("TEST SUITE SUMMARY\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(f"Tests completed: {len(results)}\n")
            f.write(f"Tests passed: {success_count}\n")
            f.write(f"Success rate: {success_count/len(results)*100:.2f}%\n\n")
            
            for result in results:
                status = "✅ PASSED" if result["success"] else "❌ FAILED"
                f.write(f"{status} - {result['script']}\n")
        
        logger.info(f"Test report saved to: {report_file}")
    
    return success_count == len(results), results
        
def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run test suite for Hugging Face processing")
    parser.add_argument("--report-dir", type=str, default="test_reports",
                        help="Directory to save test reports (default: test_reports)")
    parser.add_argument("--script", type=str, default=None,
                        help="Run a specific test script instead of all scripts")
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Run specific script or all scripts
    if args.script:
        script_path = os.path.join(os.path.dirname(__file__), args.script)
        if os.path.exists(script_path):
            report_file = os.path.join(args.report_dir, f"test_report_{int(time.time())}.txt") if args.report_dir else None
            success, _ = run_test_script(script_path, report_file)
            sys.exit(0 if success else 1)
        else:
            logger.error(f"Test script not found: {script_path}")
            sys.exit(1)
    else:
        success, _ = run_all_tests(args.report_dir)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
