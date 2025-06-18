#!/usr/bin/env python3
# Script to replace the validation block in app.py

def fix_validation_block():
    try:
        # Read the file
        with open('/Users/bendickinson/Desktop/Minerva/web/app.py', 'r') as f:
            lines = f.readlines()
        
        # Find the lines where the validation block starts and ends
        start_line = None
        for i, line in enumerate(lines):
            if "# Apply enhanced validation" in line:
                start_line = i
                break
        
        if start_line is None:
            print("Could not find validation block")
            return False
        
        # Replace the problematic section
        fixed_validation_block = [
            "                    # Apply enhanced validation\n",
            "                    if not bypass_validation:\n",
            "                        try:\n",
            "                            is_valid, validation_results = validate_response(\n",
            "                                response, \n",
            "                                message, \n",
            "                                model_name=\"huggingface_framework\", \n",
            "                                strict_mode=(query_complexity > 0.7)  # Stricter validation for complex queries\n",
            "                            )\n",
            "                            \n",
            "                            if not is_valid:\n",
            "                                validation_reason = validation_results.get('primary_reason', 'Unknown reason')\n",
            "                                logger.warning(f\"[HF PROCESS] Response failed validation: {validation_reason}\")\n",
            "                                logger.warning(f\"[HF PROCESS] Invalid response: {response[:100]}...\")\n",
            "                                \n"
        ]
        
        # Replace the lines
        lines[start_line:start_line + len(fixed_validation_block)] = fixed_validation_block
        
        # Write the fixed content back
        with open('/Users/bendickinson/Desktop/Minerva/web/app.py', 'w') as f:
            f.writelines(lines)
        
        print("Successfully replaced validation block in app.py")
        return True
    except Exception as e:
        print(f"Error fixing app.py: {str(e)}")
        return False

if __name__ == "__main__":
    fix_validation_block()
