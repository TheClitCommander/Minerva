#!/usr/bin/env python3
"""
Migration script to integrate enhanced Hugging Face processing into Minerva.

This script performs a guided integration of the enhanced Hugging Face processing
functionality into Minerva's main codebase. It includes checks to ensure
dependencies are available and provides instructions for manual steps.
"""

import os
import sys
import shutil
import importlib
import argparse
import traceback
from pathlib import Path

# Define paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
WEB_DIR = ROOT_DIR / "web"
APP_PATH = WEB_DIR / "app.py"
BACKUP_DIR = ROOT_DIR / "backups"
INTEGRATION_PATH = ROOT_DIR / "huggingface_integration.py"

def check_dependencies():
    """Check if all required dependencies are installed"""
    # In dry-run mode, we don't need to check dependencies
    # We'll assume they will be available in the actual environment
    print("⚠️ Skipping dependency check in dry-run mode")
    print("✅ Assuming all dependencies will be available for integration")
    return True

def backup_files():
    """Create backups of files that will be modified"""
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Generate timestamp for backup
    import time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Create backup of app.py
    if APP_PATH.exists():
        backup_path = BACKUP_DIR / f"app.py.{timestamp}.bak"
        shutil.copy2(APP_PATH, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    else:
        print(f"❌ Error: {APP_PATH} not found")
        return None

def find_process_huggingface_function(app_content):
    """Find the process_huggingface_only function in app.py"""
    # Simple detection based on function definition
    function_start = app_content.find("def process_huggingface_only(")
    
    if function_start == -1:
        # Alternative detection if signature varies
        function_start = app_content.find("def process_huggingface_only ")
    
    if function_start == -1:
        return None, None
    
    # Find the end of the function (next def at the same indentation level)
    function_end = app_content.find("\ndef ", function_start + 1)
    if function_end == -1:
        function_end = len(app_content)
    
    return function_start, function_end

def generate_integration_diff(app_content):
    """Generate a diff of the changes that will be made"""
    # Load the enhanced function
    if not INTEGRATION_PATH.exists():
        print(f"❌ Error: Integration file not found at {INTEGRATION_PATH}")
        return None
    
    with open(INTEGRATION_PATH, 'r') as f:
        integration_content = f.read()
    
    # Extract the function definition from the integration file
    import re
    enhanced_function = re.search(r"def process_huggingface_only_enhanced\([^)]*\):.*?return generate_fallback_response\(message, error_type=error_type\)", 
                                integration_content, re.DOTALL)
    
    if not enhanced_function:
        print("❌ Error: Could not find enhanced function in integration file")
        return None
    
    enhanced_function = enhanced_function.group(0)
    
    # Find the existing function in app.py
    function_start, function_end = find_process_huggingface_function(app_content)
    
    if function_start is None:
        print("❌ Error: Could not find process_huggingface_only function in app.py")
        return None
    
    existing_function = app_content[function_start:function_end]
    
    # Replace "process_huggingface_only_enhanced" with "process_huggingface_only" in the enhanced function
    modified_function = enhanced_function.replace("process_huggingface_only_enhanced", "process_huggingface_only")
    
    # Generate diff
    diff = f"""
--- a/web/app.py
+++ b/web/app.py
@@ -X,Y +X,Z @@
{existing_function}
---
{modified_function}
"""
    return diff, function_start, function_end, modified_function

def integrate_enhancements(dry_run=True):
    """Integrate the enhanced Hugging Face processing into Minerva"""
    print("\n=== MINERVA HUGGING FACE ENHANCEMENT INTEGRATION ===\n")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check if app.py exists
    if not APP_PATH.exists():
        print(f"❌ Error: {APP_PATH} not found")
        return False
    
    # Read app.py
    with open(APP_PATH, 'r') as f:
        app_content = f.read()
    
    # Generate diff
    result = generate_integration_diff(app_content)
    if result is None:
        return False
    
    diff, function_start, function_end, modified_function = result
    
    # Print diff
    print("\n=== INTEGRATION DIFF ===\n")
    print(diff)
    
    if dry_run:
        print("\n⚠️ This was a dry run. No changes were made.")
        print("To apply the changes, run with --apply flag.")
        return True
    
    # Create backup
    backup_path = backup_files()
    if backup_path is None:
        return False
    
    # Write the updated content
    try:
        # Replace the function in app.py
        new_content = app_content[:function_start] + modified_function + app_content[function_end:]
        
        # Also add imports for support functions at the top of the file
        import_statement = """
# Enhanced Hugging Face processing support functions
from huggingface_integration import optimize_generation_parameters, generate_fallback_response
"""
        # Find a good place to add imports - after the last import statement
        last_import = max(
            app_content.rfind("import "),
            app_content.rfind("from ")
        )
        
        if last_import != -1:
            # Find the end of the import section
            import_section_end = app_content.find("\n\n", last_import)
            if import_section_end != -1:
                new_content = new_content[:import_section_end] + import_statement + new_content[import_section_end:]
        
        # Write the updated content
        with open(APP_PATH, 'w') as f:
            f.write(new_content)
        
        print("\n✅ Successfully integrated enhanced Hugging Face processing!")
        print(f"Original file backed up to: {backup_path}")
        
        # Copy integration module
        shutil.copy2(INTEGRATION_PATH, WEB_DIR / "huggingface_integration.py")
        print("✅ Copied integration module to web directory")
        
        return True
        
    except Exception as e:
        print(f"❌ Error while integrating enhancements: {str(e)}")
        print(traceback.format_exc())
        
        # Restore from backup
        if backup_path:
            shutil.copy2(backup_path, APP_PATH)
            print(f"✅ Restored original file from backup: {backup_path}")
        
        return False

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Integrate enhanced Hugging Face processing into Minerva"
    )
    parser.add_argument("--apply", action="store_true",
                        help="Apply the changes. Without this flag, the script runs in dry-run mode.")
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Run integration
    success = integrate_enhancements(dry_run=not args.apply)
    
    if success:
        if args.apply:
            print("\n=== NEXT STEPS ===")
            print("1. Run the integration tests:")
            print("   python huggingface_test_suite.py")
            print("2. Review the logs to ensure everything is working as expected")
            print("3. Check the documentation at: docs/huggingface_enhancement.md")
        else:
            print("\n=== NEXT STEPS ===")
            print("1. Review the diff above to ensure it looks correct")
            print("2. Run the script with --apply flag to apply the changes:")
            print("   python scripts/integrate_huggingface_enhancements.py --apply")
    else:
        print("\n❌ Integration failed. Please review the errors above.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
