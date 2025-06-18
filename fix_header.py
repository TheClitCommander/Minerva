#!/usr/bin/env python3

def fix_header():
    """Fix the header of the multi_model_processor.py file"""
    
    # Define the path
    file_path = "/Users/bendickinson/Desktop/Minerva/web/multi_model_processor.py"
    
    # Create the corrected header
    corrected_header = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Multi-model processor for handling different AI model integrations.
This module coordinates different model types, validates responses,
and provides routing functionality for optimal model selection.
'''

import logging
import random
import re
from typing import Dict, List, Tuple, Any, Optional
import logging

"""
    
    # Read the current file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the header
    content = content.replace(content[:300], corrected_header)
    
    # Write the corrected content to a new file
    with open(file_path + '.fixed', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Replace the original file
    import os
    os.replace(file_path + '.fixed', file_path)
    
    print(f"Fixed header in {file_path}")

if __name__ == "__main__":
    fix_header()
