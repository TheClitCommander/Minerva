#!/usr/bin/env python3

import re
import os

def fix_python_file(file_path):
    """Fix unterminated triple quotes in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace problematic parts
    fixed_content = re.sub(r'<\|assistant\|\>\n"""', r'<|assistant|>', content)
    
    # Write the fixed content to a new file
    new_file_path = file_path + '.fixed'
    with open(new_file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    # Replace the original file
    os.replace(new_file_path, file_path)
    
    print(f"Fixed file: {file_path}")

if __name__ == "__main__":
    fix_python_file("/Users/bendickinson/Desktop/Minerva/web/multi_model_processor.py")
