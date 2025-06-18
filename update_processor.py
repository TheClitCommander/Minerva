#!/usr/bin/env python3

# Get the content from the temporary file
with open('/tmp/improved_llama2.py', 'r') as f:
    improved_processor = f.read()

# Read the current file content
with open('/Users/bendickinson/Desktop/Minerva/web/multi_model_processor.py', 'r') as f:
    current_content = f.readlines()

# Find the start and end lines of the simulated_llama2_processor function
start_line = None
end_line = None
in_function = False
for i, line in enumerate(current_content):
    if 'async def simulated_llama2_processor' in line:
        start_line = i
        in_function = True
    elif in_function and line.strip() == '':
        end_line = i
        break
    elif in_function and 'async def' in line and 'simulated_llama2_processor' not in line:
        end_line = i
        break

# Replace the function with the improved version
if start_line is not None and end_line is not None:
    new_content = current_content[:start_line] + [improved_processor + '\n'] + current_content[end_line:]
    with open('/Users/bendickinson/Desktop/Minerva/web/multi_model_processor.py', 'w') as f:
        f.writelines(new_content)
    print("Successfully updated the simulated_llama2_processor function")
else:
    print("Could not find the function to replace")
