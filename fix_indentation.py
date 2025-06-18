#!/usr/bin/env python3
# Script to fix indentation in app.py

filename = '/Users/bendickinson/Desktop/Minerva/web/app.py'
target_start = 4086
target_end = 4090

with open(filename, 'r') as f:
    lines = f.readlines()

# Modify the lines
if len(lines) >= target_end:
    # Get the content
    content = ''.join(lines[target_start-1:target_end])
    
    # Create corrected content
    if 'try:' not in content:
        corrected_content = lines[target_start-1]  # Keep the first line
        corrected_content += '                        try:\n'  # Add try block with proper indentation
        corrected_content += ''.join(lines[target_start:target_end])  # Add remaining lines
        
        # Replace in the lines array
        lines[target_start-1:target_end] = corrected_content.split('\n')
        if lines[-1] != '\n':
            lines[-1] += '\n'
    
    # Write back to the file
    with open(filename, 'w') as f:
        f.writelines(lines)
        print("File updated successfully.")
else:
    print("Line numbers out of range.")
