#!/usr/bin/env python3

import re

def fix_docstrings():
    """Fix all docstrings in the multi_model_processor.py file."""
    
    filename = "/Users/bendickinson/Desktop/Minerva/web/multi_model_processor.py"
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the module docstring with single quotes
    content = content.replace('"""', "'''", 3)  # Replace first 3 instances
    
    # Fix the f-string docstrings
    # This pattern finds all return f""" blocks and ensures they have closing quotes
    content = re.sub(r'return f"""(.*?)<\|assistant\|>', r'return f"""\1<|assistant|>"""', content, flags=re.DOTALL)
    
    # Write the fixed content
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed docstrings in {filename}")

if __name__ == "__main__":
    fix_docstrings()
