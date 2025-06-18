#!/usr/bin/env python3

import os

def fix_file():
    """Fix the multi_model_processor.py file by ensuring docstrings are properly closed"""
    
    # Define the path
    file_path = "/Users/bendickinson/Desktop/Minerva/web/multi_model_processor.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Make fixes to problematic triple quotes
    for i in range(len(lines)):
        # Fix pattern 1: <|assistant|> followed by """ on the same line
        if "<|assistant|>" in lines[i] and '"""' in lines[i]:
            lines[i] = lines[i].replace('"""', '')
            
        # Fix pattern 2: <|assistant|> followed by """ on the next line
        if "<|assistant|>" in lines[i] and i+1 < len(lines) and '"""' in lines[i+1]:
            lines[i+1] = lines[i+1].replace('"""', '')
    
    # Write back
    with open(file_path + '.fixed', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # Backup the original file
    os.rename(file_path, file_path + '.bak')
    
    # Replace with fixed version
    os.rename(file_path + '.fixed', file_path)
    
    print(f"Fixed and replaced {file_path}")

if __name__ == "__main__":
    fix_file()
