#!/usr/bin/env python3
# Script to fix the self-reference block in app.py

def fix_self_reference_block():
    try:
        # Read the file
        with open('/Users/bendickinson/Desktop/Minerva/web/app.py', 'r') as f:
            lines = f.readlines()
        
        # Find the problematic section
        for i, line in enumerate(lines):
            if "validation_reason = validation_results.get" in line:
                # The fix needs to insert a conditional statement
                # Check the next few lines to find where we need to add the if statement
                for j in range(i+1, i+10):
                    if j < len(lines) and "if len(cleaned_response) > 50:" in lines[j]:
                        # We found the indented if without its parent conditional
                        # Insert the missing conditional statement
                        fixed_lines = lines[:j]
                        fixed_lines.append("                                # Try to fix common validation issues\n")
                        fixed_lines.append("                                if validation_reason == \"self_reference\" and query_complexity < 0.5:\n")
                        fixed_lines.append("                                    # For simple queries with self-references, we can try to fix it\n")
                        fixed_lines.append("                                    logger.warning(\"[HF PROCESS] Attempting to fix self-reference in response\")\n")
                        fixed_lines.append("                                    cleaned_response = re.sub(r'(As an AI|I am an AI|As an artificial intelligence|I\\'m an AI assistant).*?[.!]\\s*', '', response)\n")
                        fixed_lines.extend(lines[j:])
                        
                        # Write the fixed content back
                        with open('/Users/bendickinson/Desktop/Minerva/web/app.py', 'w') as f:
                            f.writelines(fixed_lines)
                        
                        print("Successfully fixed self-reference block in app.py")
                        return True
        
        print("Could not find section to fix")
        return False
    except Exception as e:
        print(f"Error fixing app.py: {str(e)}")
        return False

if __name__ == "__main__":
    fix_self_reference_block()
