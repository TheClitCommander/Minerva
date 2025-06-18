#!/usr/bin/env python3
"""
Minerva AI - Test Runner

This script runs the test suite for the Minerva AI system.
"""

import os
import sys
import argparse
import pytest
import unittest
import importlib.util


def run_tests(test_type=None, verbose=False):
    """
    Run the test suite.
    
    Args:
        test_type (str, optional): Type of tests to run ('unit', 'integration', 'web', 'autogpt', or None for all)
        verbose (bool, optional): Whether to run tests in verbose mode
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    args = ["-v"] if verbose else []
    
    if test_type:
        if test_type == "unit":
            args.extend(["-m", "unit", "tests/unit"])
        elif test_type == "integration":
            args.extend(["-m", "integration", "tests/integration"])
        elif test_type == "web":
            args.extend(["-m", "web", "tests/web"])
        elif test_type == "autogpt":
            # Run AutoGPT integration tests directly
            return run_autogpt_tests(verbose)
        else:
            print(f"Unknown test type: {test_type}")
            return 1
    
    return pytest.main(args)


def run_autogpt_tests(verbose=False):
    """
    Run AutoGPT integration tests.
    
    Args:
        verbose (bool, optional): Whether to run tests in verbose mode
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Set up test loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Print test header
    print("\n======= RUNNING AUTOGPT INTEGRATION TESTS =======")
    
    # Load AutoGPT integration test
    try:
        spec = importlib.util.spec_from_file_location(
            "test_autogpt_integration", 
            os.path.join(os.getcwd(), "tests", "test_autogpt_integration.py")
        )
        autogpt_test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(autogpt_test_module)
        suite.addTest(loader.loadTestsFromModule(autogpt_test_module))
        
        print("Loaded AutoGPT integration test module")
    except Exception as e:
        print(f"Error loading AutoGPT integration tests: {str(e)}")
        return 1
    
    # Run the tests
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print completion message
    print("\nAutoGPT integration tests complete.")
    print(f"Ran {result.testsRun} tests with {len(result.errors)} errors and {len(result.failures)} failures.")
    
    # Return 0 for success, 1 for failure
    if result.wasSuccessful():
        return 0
    return 1


def main():
    """
    Parse command line arguments and run tests.
    """
    parser = argparse.ArgumentParser(description="Run Minerva AI tests")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "web", "autogpt", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Run tests in verbose mode"
    )
    
    args = parser.parse_args()
    
    test_type = None if args.type == "all" else args.type
    
    return run_tests(test_type, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
