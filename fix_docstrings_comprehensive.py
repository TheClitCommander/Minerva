#!/usr/bin/env python3

import re

def fix_docstrings():
    """Fix all docstrings in the multi_model_processor.py file."""
    
    file_path = "/Users/bendickinson/Desktop/Minerva/web/multi_model_processor.py"
    
    # Create a backup first
    import shutil
    backup_path = file_path + ".bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Fix the issue with triple single quotes
    lines = content.split('\n')
    fixed_lines = []
    in_triple_single = False
    
    for line in lines:
        # Check for triple single quotes
        if "'''" in line:
            if not in_triple_single:
                in_triple_single = True
            else:
                in_triple_single = False
        
        fixed_lines.append(line)
    
    # If we ended with an open triple single quote, close it
    if in_triple_single:
        # Find the last line with triple single quotes and add closing quotes
        for i in range(len(fixed_lines) - 1, -1, -1):
            if "'''" in fixed_lines[i]:
                # If this is an opening quote, add closing quote to the end of the docstring
                # Look ahead to find where the docstring logically ends
                for j in range(i + 1, len(fixed_lines)):
                    if fixed_lines[j].strip() and not fixed_lines[j].strip().startswith('#'):
                        # Insert closing quotes before this line
                        fixed_lines.insert(j, "'''")
                        break
                break
    
    # 2. Fix f-string triple quotes in return statements
    content = '\n'.join(fixed_lines)
    
    # Fix return f""" patterns ensuring they have closing quotes
    pattern = r'return f"""(.*?)<\|assistant\|>'
    replacement = r'return f"""\1<|assistant|>"""'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Fix the specific issue with line 2198
    if 'Assistant: I\'ll respond briefly and naturally to your greeting."""' in content:
        content = content.replace(
            'Assistant: I\'ll respond briefly and naturally to your greeting."""',
            'Assistant: I\'ll respond briefly and naturally to your greeting."""'
        )
    
    # 3. Fix any line 84 issues (if it's still showing as a problem)
    lines = content.split('\n')
    
    # Scan all triple-quoted strings to ensure they're closed
    in_triple_double = False
    in_triple_single = False
    triple_double_start = 0
    triple_single_start = 0
    
    for i, line in enumerate(lines):
        if '"""' in line:
            count = line.count('"""')
            if count % 2 != 0:  # Odd number of triple quotes
                if not in_triple_double:
                    in_triple_double = True
                    triple_double_start = i
                else:
                    in_triple_double = False
        
        if "'''" in line:
            count = line.count("'''")
            if count % 2 != 0:  # Odd number of triple quotes
                if not in_triple_single:
                    in_triple_single = True
                    triple_single_start = i
                else:
                    in_triple_single = False
    
    # Add closing quotes if needed
    if in_triple_double:
        print(f"Adding closing triple double quotes for string starting at line {triple_double_start + 1}")
        # Find where to add the closing quotes
        for j in range(triple_double_start + 1, len(lines)):
            if lines[j].strip() and not lines[j].lstrip().startswith('#'):
                lines.insert(j, '"""')
                break
    
    if in_triple_single:
        print(f"Adding closing triple single quotes for string starting at line {triple_single_start + 1}")
        # Find where to add the closing quotes
        for j in range(triple_single_start + 1, len(lines)):
            if lines[j].strip() and not lines[j].lstrip().startswith('#'):
                lines.insert(j, "'''")
                break
    
    # Join lines back together
    content = '\n'.join(lines)
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed docstrings in {file_path}")

if __name__ == "__main__":
    fix_docstrings()
