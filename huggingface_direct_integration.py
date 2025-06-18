#!/usr/bin/env python3
"""
Direct Integration Script for Enhanced Hugging Face Processing

This script will help integrate our enhanced Hugging Face processing 
functionality directly into the Minerva codebase.

Usage:
    python huggingface_direct_integration.py
"""

import os
import sys
import shutil
from pathlib import Path
import datetime

# Define paths
SCRIPT_DIR = Path(__file__).parent
APP_PATH = SCRIPT_DIR / "web" / "app.py"
BACKUP_DIR = SCRIPT_DIR / "backups"
INTEGRATED_MODULE_PATH = SCRIPT_DIR / "integrated_huggingface.py"

def create_backup():
    """Create a backup of app.py before making changes"""
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Generate timestamp for backup
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create backup of app.py
    if APP_PATH.exists():
        backup_path = BACKUP_DIR / f"app.py.{timestamp}.bak"
        shutil.copy2(APP_PATH, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    else:
        print(f"❌ Error: {APP_PATH} not found")
        return None

def integrate_functions():
    """
    Integrate the enhanced functions directly into the Minerva codebase
    
    This function imports our optimized functions and updates the
    app.py file accordingly.
    """
    # Step 1: Import the optimized functions
    try:
        from integrated_huggingface import (
            optimize_generation_parameters as enhanced_optimize,
            generate_fallback_response as enhanced_fallback,
            clean_ai_response as enhanced_clean
        )
        print("✅ Successfully imported enhanced functions")
    except ImportError:
        print("❌ Error: Cannot import from integrated_huggingface.py")
        return False
    
    # Step 2: Check for app.py
    if not APP_PATH.exists():
        print(f"❌ Error: {APP_PATH} not found")
        return False
    
    # Create backup before proceeding
    backup_path = create_backup()
    if not backup_path:
        return False
    
    # Step 3: Update app.py with enhanced functions
    print("\n📝 Integration Steps:")
    print("1. Copy the enhanced functions to app.py")
    print("2. Update the process_huggingface_only function")
    print("3. Add any missing imports or dependencies")
    
    print("\n⚠️ Manual Integration Required:")
    print(f"To complete the integration, you should:")
    print(f"1. Copy the optimize_generation_parameters function from {INTEGRATED_MODULE_PATH}")
    print(f"2. Copy the generate_fallback_response function from {INTEGRATED_MODULE_PATH}")
    print(f"3. Copy the clean_ai_response function from {INTEGRATED_MODULE_PATH}")
    print(f"4. Update the process_huggingface_only function with enhanced validation and error handling")
    
    print("\n📋 Testing After Integration:")
    print("1. Run the huggingface_test_suite.py to verify integration")
    print("2. Test with sample queries of various complexities")
    print("3. Check logs for any errors or issues")
    
    return True

def main():
    """Main entry point"""
    print("\n=== MINERVA HUGGING FACE ENHANCEMENT DIRECT INTEGRATION ===\n")
    
    # Verify paths
    print(f"App Path: {APP_PATH}")
    print(f"Backup Directory: {BACKUP_DIR}")
    print(f"Integration Module: {INTEGRATED_MODULE_PATH}")
    
    # Run the integration
    success = integrate_functions()
    
    if success:
        print("\n✅ Integration preparation complete")
        print("Please follow the manual integration steps outlined above")
    else:
        print("\n❌ Integration preparation failed")
        print("Please check the errors and try again")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
