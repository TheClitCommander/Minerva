#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Direct model testing without going through the API
This bypasses all web servers and directly loads and tests the model
"""

import sys
import os
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def test_model_directly(message, model_name="distilgpt2"):
    """Test a model directly without going through the API"""
    print(f"Loading model: {model_name}")
    
    try:
        # Load tokenizer and model
        start_time = time.time()
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Move model to appropriate device
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
            
        model = model.to(device)
        load_time = time.time() - start_time
        print(f"Model loaded in {load_time:.2f}s on {device}")
        
        # Format prompt
        formatted_prompt = f"User: {message.strip()}\nAssistant: "
        print(f"Formatted prompt: {formatted_prompt}")
        
        # Generate
        gen_start = time.time()
        input_ids = tokenizer(formatted_prompt, return_tensors="pt").to(device)
        
        with torch.no_grad():
            generation_output = model.generate(
                **input_ids,
                max_new_tokens=300,
                do_sample=True,
                temperature=0.8,
                top_k=50
            )
        
        # Get raw output
        raw_output = tokenizer.decode(generation_output[0], skip_special_tokens=True)
        gen_time = time.time() - gen_start
        
        # Extract response with minimal processing
        response = raw_output.replace(formatted_prompt, "").strip()
        
        print(f"Generation completed in {gen_time:.2f}s")
        print("\nRaw output:")
        print("=" * 50)
        print(raw_output)
        print("=" * 50)
        
        print("\nExtracted response:")
        print("=" * 50)
        print(response)
        print("=" * 50)
        
        return response
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function to run tests"""
    if len(sys.argv) > 1:
        message = sys.argv[1]
    else:
        message = "What is the purpose of neural networks?"
    
    test_model_directly(message)

if __name__ == "__main__":
    main()
