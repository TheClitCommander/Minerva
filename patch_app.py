#!/usr/bin/env python
'''
This script patches the app.py file to fix syntax errors in the process_message_thread function.
It searches for the function definition, extracts its location, and replaces it with a fixed version.
'''

import re
import os
import sys

def main():
    print("Starting app.py patching process...")
    
    # Paths
    app_path = os.path.join('web', 'app.py')
    fixed_func_path = 'app_fixed.py'
    backup_path = os.path.join('web', 'app.py.backup2')
    
    # Check paths
    if not os.path.exists(app_path):
        print(f"Error: {app_path} not found!")
        return 1
    
    if not os.path.exists(fixed_func_path):
        print(f"Error: {fixed_func_path} not found!")
        return 1
    
    # Read files
    print(f"Reading {app_path}...")
    with open(app_path, 'r') as f:
        app_content = f.read()
    
    print(f"Reading fixed function from {fixed_func_path}...")
    with open(fixed_func_path, 'r') as f:
        fixed_func_content = f.read()
    
    # Create backup
    print(f"Creating backup at {backup_path}...")
    with open(backup_path, 'w') as f:
        f.write(app_content)
    
    # Find function bounds
    print("Finding function boundaries...")
    pattern = r'(?:\s*)def process_message_thread\(\):.*?(?=\n\s*(?:@|def|class|if __name__|$))'
    match = re.search(pattern, app_content, re.DOTALL)
    
    if not match:
        print("Error: Could not find process_message_thread function!")
        return 1
    
    func_text = match.group(0)
    func_indent = re.match(r'^(\s*)', func_text).group(1)
    
    print(f"Found function with {len(func_text)} characters and {len(func_indent)} spaces of indentation")
    
    # Prepare fixed function with proper indentation
    fixed_lines = fixed_func_content.strip().split('\n')
    indented_fixed = '\n'.join([func_indent + line for line in fixed_lines])
    
    # Replace function
    print("Replacing function in app.py...")
    new_content = app_content.replace(func_text, indented_fixed)
    
    # Save patched file
    print("Saving patched app.py...")
    with open(app_path, 'w') as f:
        f.write(new_content)
    
    print("Patching complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
