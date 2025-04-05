"""
HuggingFace Integration Module for Minerva

This module provides integration with HuggingFace models and enables
their use within the Minerva framework.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Union

# Setup logging
logger = logging.getLogger(__name__)

class HuggingFaceIntegration:
    """
    Provides integration with HuggingFace models, allowing Minerva to use
    transformer models for various tasks.
    """
    
    def __init__(self, config=None):
        """
        Initialize the HuggingFace integration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.models = {}
        self.tokenizers = {}
        self.device = "cpu"  # Default to CPU
        
        # Use API key from environment
        self.api_key = os.environ.get("HUGGINGFACE_API_TOKEN")
        # Set the API key in environment for any HF library components if available
        if self.api_key:
            os.environ["HUGGINGFACE_API_KEY"] = self.api_key
            self.logger.info("HuggingFace API key found in environment variables")
        else:
            self.logger.warning("HuggingFace API key not found in environment variables")
        
        self.logger = logger
        
        # Try to use GPU if available
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch, 'mps') and torch.backends.mps.is_available():
                self.device = "mps"  # MacOS Metal Performance Shaders
        except (ImportError, AttributeError):
            pass
        
        self.logger.info(f"HuggingFace integration initialized with device: {self.device}")
    
    def load_model(self, model_name: str, model_type: str = "text-generation"):
        """
        Load a HuggingFace model.
        
        Args:
            model_name: Name of the model to load (e.g., 'distilgpt2')
            model_type: Type of model to load (e.g., 'text-generation', 'embeddings')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if model_type == "text-generation":
                from transformers import AutoModelForCausalLM, AutoTokenizer
                
                # Load tokenizer
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.tokenizers[model_name] = tokenizer
                
                # Load model
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map=self.device if self.device != "mps" else "auto",
                    torch_dtype="auto"
                )
                
                self.models[model_name] = model
                self.logger.info(f"Successfully loaded model: {model_name}")
                return True
                
            elif model_type == "embeddings":
                from transformers import AutoModel, AutoTokenizer
                
                # Load tokenizer
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.tokenizers[model_name] = tokenizer
                
                # Load model
                model = AutoModel.from_pretrained(model_name)
                if self.device != "mps":  # MPS handling is special
                    model = model.to(self.device)
                
                self.models[model_name] = model
                self.logger.info(f"Successfully loaded embedding model: {model_name}")
                return True
                
            else:
                self.logger.error(f"Unsupported model type: {model_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading model {model_name}: {e}")
            return False
    
    def generate_text(self, model_name: str, prompt: str, max_length: int = 100, **kwargs):
        """
        Generate text using a loaded model.
        
        Args:
            model_name: Name of the model to use
            prompt: Prompt to generate from
            max_length: Maximum length of generated text
            **kwargs: Additional arguments for generation
            
        Returns:
            Generated text or error message
        """
        if model_name not in self.models or model_name not in self.tokenizers:
            return {"error": f"Model {model_name} not loaded"}
        
        try:
            tokenizer = self.tokenizers[model_name]
            model = self.models[model_name]
            
            # Prepare inputs
            inputs = tokenizer(prompt, return_tensors="pt")
            if self.device != "mps":  # MPS handling is special
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate
            generation_params = {
                "max_length": max_length,
                "num_return_sequences": 1,
                "do_sample": True,
                "top_p": 0.95,
                "top_k": 50,
                "temperature": 0.7,
                **kwargs
            }
            
            # Handle special case for MPS
            if self.device == "mps":
                import torch
                with torch.no_grad():
                    outputs = model.generate(**inputs, **generation_params)
            else:
                outputs = model.generate(**inputs, **generation_params)
            
            # Decode
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return {"generated_text": generated_text}
            
        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            return {"error": f"Error generating text: {str(e)}"}
    
    def get_embeddings(self, model_name: str, texts: Union[str, List[str]]):
        """
        Get embeddings for text(s) using a loaded model.
        
        Args:
            model_name: Name of the model to use
            texts: Single text or list of texts to embed
            
        Returns:
            Embeddings or error message
        """
        if model_name not in self.models or model_name not in self.tokenizers:
            return {"error": f"Model {model_name} not loaded"}
        
        try:
            tokenizer = self.tokenizers[model_name]
            model = self.models[model_name]
            
            # Handle single text case
            if isinstance(texts, str):
                texts = [texts]
                
            # Prepare inputs
            encoded_inputs = tokenizer(
                texts, 
                padding=True, 
                truncation=True, 
                return_tensors="pt"
            )
            
            if self.device != "mps":  # MPS handling is special
                encoded_inputs = {k: v.to(self.device) for k, v in encoded_inputs.items()}
            
            # Get embeddings
            import torch
            with torch.no_grad():
                outputs = model(**encoded_inputs)
                
            # Mean pooling to get sentence embeddings
            attention_mask = encoded_inputs['attention_mask']
            token_embeddings = outputs.last_hidden_state
            
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            
            # Sum embeddings and normalize
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            embeddings = sum_embeddings / sum_mask
            
            # Convert to list/numpy for easier handling
            embeddings = embeddings.cpu().numpy().tolist()
            
            return {"embeddings": embeddings}
            
        except Exception as e:
            self.logger.error(f"Error getting embeddings: {e}")
            return {"error": f"Error getting embeddings: {str(e)}"}

# Framework factory function for integration with framework_manager
def get_huggingface_framework(config=None):
    """
    Factory function to create a HuggingFace integration instance.
    
    Args:
        config: Optional configuration
        
    Returns:
        HuggingFaceIntegration instance
    """
    return HuggingFaceIntegration(config)
