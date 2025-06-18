#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Syntax Error Finder Script

This script attempts to locate Python syntax errors by loading and 
parsing a Python file line by line using the ast module.
"""

import ast
import sys
import os

def find_syntax_error(file_path):
    """Parse a Python file and identify syntax errors"""
    try:
        # Try to parse the entire file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            print(f"✅ No syntax errors found in the complete file: {file_path}")
            return
        except SyntaxError as e:
            print(f"❌ Syntax error in {file_path} at line {e.lineno}, column {e.offset}")
            print(f"   Error message: {e}")
            
            # Now try to pinpoint the error by parsing line by line
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Try to parse incrementally to find where the error starts
            for i in range(1, len(lines) + 1):
                try:
                    partial_content = ''.join(lines[:i])
                    ast.parse(partial_content)
                except SyntaxError as e2:
                    print(f"❌ Error starts at line {i}:")
                    # Print the problematic line and a few lines before/after for context
                    start = max(0, i - 3)
                    end = min(len(lines), i + 3)
                    
                    for j in range(start, end):
                        prefix = ">>> " if j == i - 1 else "    "
                        print(f"{prefix}Line {j+1}: {lines[j].rstrip()}")
                    
                    break
            
    except Exception as e:
        print(f"Error while analyzing file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_syntax_error.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        sys.exit(1)
    
    find_syntax_error(file_path)
