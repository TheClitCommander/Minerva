#!/usr/bin/env python3

def find_unclosed_string(filename):
    """Find unclosed string literals in a Python file."""
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i in range(len(lines)):
        try:
            # Try to compile each line
            compile(lines[i], '<string>', 'single')
        except SyntaxError as e:
            if 'unterminated' in str(e) and 'string' in str(e):
                print(f"Line {i+1} might have an unterminated string: {lines[i].strip()}")
    
    # Also check for triple-quoted strings that span multiple lines
    in_triple_single = False
    in_triple_double = False
    triple_start_line = 0
    
    for i, line in enumerate(lines):
        # Count occurrences of triple quotes
        triple_single_count = line.count("'''")
        triple_double_count = line.count('"""')
        
        # Toggle state based on occurrences
        if triple_single_count % 2 == 1:  # Odd number means opening/closing
            if not in_triple_single:
                in_triple_single = True
                triple_start_line = i + 1
            else:
                in_triple_single = False
        
        if triple_double_count % 2 == 1:  # Odd number means opening/closing
            if not in_triple_double:
                in_triple_double = True
                triple_start_line = i + 1
            else:
                in_triple_double = False
    
    # Check if we ended with an open triple-quoted string
    if in_triple_single:
        print(f"Unclosed triple single-quoted string starting at line {triple_start_line}")
    if in_triple_double:
        print(f"Unclosed triple double-quoted string starting at line {triple_start_line}")

if __name__ == "__main__":
    filename = "/Users/bendickinson/Desktop/Minerva/web/multi_model_processor.py"
    find_unclosed_string(filename)
