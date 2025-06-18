#!/usr/bin/env python3
# Script to fix indentation issues in app.py

import re

def fix_app_py():
    try:
        # Read the file
        with open('/Users/bendickinson/Desktop/Minerva/web/app.py', 'r') as f:
            content = f.read()
        
        # Find and fix the validation section
        pattern = re.compile(r'(\s+# Apply enhanced validation\s+if not bypass_validation:\s+)(\s+is_valid,)', re.MULTILINE)
        fixed_content = pattern.sub(r'\1    try:\n\2', content)
        
        # Write the fixed content back
        with open('/Users/bendickinson/Desktop/Minerva/web/app.py', 'w') as f:
            f.write(fixed_content)
        
        print("Successfully fixed app.py")
        return True
    except Exception as e:
        print(f"Error fixing app.py: {str(e)}")
        return False

if __name__ == "__main__":
    fix_app_py()
