"""
HuggingFace Integration for Minerva

This module provides integration with the HuggingFace Transformers library,
allowing Minerva to leverage various transformer models for different tasks.
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger
from pydantic import BaseModel

# Import base integration
from integrations.base_integration import BaseIntegration

class HuggingFaceIntegration(BaseIntegration):
    """Integration with HuggingFace Transformers."""
    
    def __init__(self, framework_path: str = None):
        """Initialize HuggingFace integration."""
        # Use default framework path if not provided
        if framework_path is None:
            # Default to a directory in the project for HuggingFace
            framework_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                         "frameworks/huggingface")
            
        super().__init__(
            framework_name="HuggingFace",
            framework_path=framework_path
        )
        
        self.capabilities = ["code_generation", "text_generation", "summarization", "translation", "image_generation"]
        
        # Check if Transformers is installed
        self.api_available = False
        self.cli_available = False
        
        # Check for API availability
        try:
            import transformers
            self.api_available = True
            logger.info("HuggingFace Transformers API is available")
            
            # Check if specific modules are available
            self.check_modules()
            
        except ImportError:
            logger.warning("HuggingFace Transformers API is not available. Install with: pip install transformers")
        
        # Check for HuggingFace API token
        self.hf_api_token = os.environ.get("HF_API_TOKEN") or os.environ.get("HUGGINGFACE_API_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
        if not self.hf_api_token and self.api_available:
            logger.warning("HuggingFace API token not found. Some features may be limited.")
    
    def check_modules(self):
        """Check if specific modules/features are available."""
        self.text_generation_available = False
        self.image_generation_available = False
        self.summarization_available = False
        self.translation_available = False
        self.code_generation_available = False
        
        try:
            import transformers
            
            # Check for pipeline availability
            if hasattr(transformers, "pipeline"):
                # Text generation
                try:
                    from transformers import pipeline
                    # Just check if pipeline can be imported, don't actually load models yet
                    self.text_generation_available = True
                    self.code_generation_available = True
                    self.summarization_available = True
                    self.translation_available = True
                except ImportError:
                    logger.warning("Transformers pipeline not fully available")
            
            # Check for diffusers (image generation)
            try:
                import diffusers
                self.image_generation_available = True
            except ImportError:
                logger.warning("Diffusers not available. Install with: pip install diffusers")
            
        except Exception as e:
            logger.error(f"Error checking modules: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if HuggingFace Transformers is available for use."""
        return self.api_available or self.cli_available
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the HuggingFace Transformers integration."""
        status = {
            "name": self.name,
            "api_available": self.api_available,
            "cli_available": self.cli_available,
            "hf_api_token": bool(self.hf_api_token),
            "text_generation_available": self.text_generation_available,
            "code_generation_available": self.code_generation_available,
            "summarization_available": self.summarization_available,
            "translation_available": self.translation_available,
            "image_generation_available": self.image_generation_available,
            "status": "operational" if self.is_available() else "unavailable"
        }
        
        # Attempt to make a simple call if API is available
        if self.api_available and self.text_generation_available:
            try:
                from transformers import pipeline
                
                # Use a small model for testing
                generator = pipeline('text-generation', model='gpt2', max_length=10)
                result = generator("Hello, I'm Minerva")[0]['generated_text']
                
                status["test_result"] = result
                status["test_success"] = True
            except Exception as e:
                status["test_success"] = False
                status["error"] = str(e)
        
        return status
    
    def generate_code(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate code using HuggingFace models.
        
        Args:
            prompt: The prompt for code generation
            context: Optional context for the code generation
            
        Returns:
            Dictionary with code generation results
        """
        if not self.api_available or not self.code_generation_available:
            return {
                "status": "error",
                "code": "",
                "note": "HuggingFace code generation is not available. Install transformers with pip."
            }
        
        try:
            from transformers import pipeline
            
            # Determine language or default to Python
            language = "python"
            if context and "language:" in context.lower():
                for line in context.split("\n"):
                    if line.lower().startswith("language:"):
                        language = line.split(":", 1)[1].strip()
            
            # Format the prompt with appropriate context
            if context:
                full_prompt = f"{context}\n\nWrite {language} code for: {prompt}\n```{language}\n"
            else:
                full_prompt = f"Write {language} code for: {prompt}\n```{language}\n"
            
            # Use code generation model
            model_name = "Salesforce/codegen-2B-mono"  # Decent open-source code model
            
            generator = pipeline('text-generation', model=model_name, max_length=500)
            result = generator(full_prompt)[0]['generated_text']
            
            # Extract code from the generated text
            if "```" in result:
                # Find the code block
                code_block = result.split("```", 2)[1]
                if language in code_block:
                    code = code_block.split(language, 1)[1].strip()
                else:
                    code = code_block.strip()
            else:
                # If no code block markers, just extract everything after the prompt
                code = result[len(full_prompt):].strip()
            
            return {
                "status": "success",
                "code": code,
                "language": language,
                "note": f"Code generated using HuggingFace model: {model_name}"
            }
            
        except Exception as e:
            logger.error(f"Error generating code with HuggingFace: {str(e)}")
            return {
                "status": "error",
                "code": "",
                "error": str(e),
                "note": "Failed to generate code with HuggingFace"
            }
    
    def execute_task(self, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a task using HuggingFace models.
        
        Args:
            task: The task to execute
            context: Optional context for the task
            
        Returns:
            Dictionary with task execution results
        """
        # For HuggingFace, task execution is primarily about choosing the right model and pipeline
        # We'll analyze the task and select appropriate models

        if not self.api_available or not self.text_generation_available:
            return {
                "status": "error",
                "result": "",
                "note": "HuggingFace text generation is not available. Install transformers with pip."
            }
        
        try:
            from transformers import pipeline
            
            # Determine task type
            task_lower = task.lower()
            
            # Summarization task
            if any(keyword in task_lower for keyword in ["summarize", "summary", "summarization"]):
                if not self.summarization_available:
                    return {
                        "status": "error",
                        "result": "",
                        "note": "Summarization not available"
                    }
                
                # Extract text to summarize from context
                text_to_summarize = context if context else task
                
                # Use summarization pipeline
                summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
                result = summarizer(text_to_summarize, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
                
                return {
                    "status": "success",
                    "result": result,
                    "note": "Text summarized using HuggingFace model"
                }
            
            # Translation task
            elif any(keyword in task_lower for keyword in ["translate", "translation"]):
                if not self.translation_available:
                    return {
                        "status": "error",
                        "result": "",
                        "note": "Translation not available"
                    }
                
                # Extract text to translate from context
                text_to_translate = context if context else task
                
                # Use translation pipeline (defaults to English to French)
                translator = pipeline("translation_en_to_fr", model="t5-small")
                result = translator(text_to_translate, max_length=100)[0]['translation_text']
                
                return {
                    "status": "success",
                    "result": result,
                    "note": "Text translated using HuggingFace model"
                }
            
            # Generate image from text
            elif any(keyword in task_lower for keyword in ["generate image", "create image", "image from text"]):
                if not self.image_generation_available:
                    return {
                        "status": "error",
                        "result": "",
                        "note": "Image generation not available. Install with: pip install diffusers"
                    }
                
                # Extract prompt for image generation
                image_prompt = context if context else task
                
                # Import diffusers
                from diffusers import StableDiffusionPipeline
                import torch
                
                # Initialize pipeline
                model_id = "runwayml/stable-diffusion-v1-5"
                pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
                
                if torch.cuda.is_available():
                    pipe = pipe.to("cuda")
                
                # Generate image
                # Note: In a real implementation, you'd save the image and return a path
                # Here we just indicate success
                pipe(image_prompt).images[0]
                
                return {
                    "status": "success",
                    "result": "Image generated successfully",
                    "note": "Image generated using Stable Diffusion"
                }
            
            # Default to general text generation
            else:
                # Format the prompt
                if context:
                    full_prompt = f"{context}\n\n{task}"
                else:
                    full_prompt = task
                
                # Use text generation model
                generator = pipeline('text-generation', model='gpt2-medium', max_length=250)
                result = generator(full_prompt)[0]['generated_text']
                
                return {
                    "status": "success",
                    "result": result,
                    "note": "Text generated using HuggingFace model"
                }
            
        except Exception as e:
            logger.error(f"Error executing task with HuggingFace: {str(e)}")
            return {
                "status": "error",
                "result": "",
                "error": str(e),
                "note": "Failed to execute task with HuggingFace"
            }
    
    def get_model_list(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a list of available HuggingFace models for a specific task.
        
        Args:
            task_type: Type of task to get models for (e.g., 'text-generation', 'summarization')
            
        Returns:
            Dictionary with model list
        """
        if not self.api_available:
            return {
                "status": "error",
                "models": [],
                "note": "HuggingFace API is not available"
            }
        
        try:
            from huggingface_hub import HfApi
            
            # Initialize API
            api = HfApi(token=self.hf_api_token if self.hf_api_token else None)
            
            # Filter models by task
            if task_type:
                models = api.list_models(filter=task_type, limit=20)
            else:
                models = api.list_models(limit=20)
            
            # Format the results
            formatted_models = []
            for model in models:
                formatted_models.append({
                    "id": model.id,
                    "downloads": model.downloads,
                    "tags": model.tags,
                    "pipeline_tag": model.pipeline_tag
                })
            
            return {
                "status": "success",
                "models": formatted_models,
                "note": f"Retrieved models for task type: {task_type if task_type else 'all'}"
            }
            
        except Exception as e:
            logger.error(f"Error retrieving models from HuggingFace: {str(e)}")
            return {
                "status": "error",
                "models": [],
                "error": str(e),
                "note": "Failed to retrieve models from HuggingFace"
            }

    def load_files(self):
        """Load configuration files."""
        # Any special configuration loading for HuggingFace
        pass
        
    def load_huggingface_model(self, model_name: str):
        """
        Loads the correct Hugging Face model dynamically based on model architecture.
        
        Args:
            model_name: Name of the model to load from HuggingFace
            
        Returns:
            Tuple of (model, tokenizer) or (None, None) if loading fails
        """
        try:
            logger.info(f"Attempting to load model: {model_name}")
            
            # Import the necessary HuggingFace components
            from transformers import AutoModelForCausalLM, AutoTokenizer, T5ForConditionalGeneration
            import torch
            
            # First try loading the tokenizer
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
                logger.info(f"Successfully loaded tokenizer for {model_name}")
            except Exception as e:
                logger.error(f"Failed to load tokenizer for {model_name}: {e}")
                return None, None
            
            # Determine the model architecture to load the correct model type
            try:
                # First try as a causal language model (most common for chat/generation)
                model = AutoModelForCausalLM.from_pretrained(model_name)
                logger.info(f"Successfully loaded model as AutoModelForCausalLM: {model_name}")
            except Exception as causal_error:
                logger.warning(f"Failed to load as causal LM: {causal_error}")
                try:
                    # Try as a T5 model (used by some models like flan-t5)
                    model = T5ForConditionalGeneration.from_pretrained(model_name)
                    logger.info(f"Successfully loaded model as T5ForConditionalGeneration: {model_name}")
                except Exception as t5_error:
                    logger.error(f"Failed to load as T5 model: {t5_error}")
                    # Add more model types here if needed
                    logger.error(f"Exhausted all model type options for {model_name}")
                    return None, None
            
            # Move to appropriate device
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            
            logger.info(f"Successfully loaded model {model_name} on {device}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Error in load_huggingface_model: {e}")
            return None, None
    
    def generate_text(self, prompt: str, max_length: int = 150, model_name: str = None) -> str:
        """
        Generate text response using HuggingFace Transformers.
        
        Args:
            prompt: The input prompt to generate text from
            max_length: Maximum length of the generated text
            model_name: Specific model to use, defaults to a simple text generation model
            
        Returns:
            Generated text response
        """
        logger.info(f"Generating text with HuggingFace for prompt: {prompt[:50]}...")
        
        if not self.api_available or not self.text_generation_available:
            logger.warning("HuggingFace text generation is not available")
            return "I'm sorry, text generation capabilities are not currently available."
        
        try:
            from transformers import pipeline
            
            # Use provided model or default to a slightly better model
            model = model_name or "distilgpt2"
            
            # Check if it's an advanced model to adjust parameters
            is_advanced_model = "zephyr" in model.lower() or "mistral" in model.lower()
            
            # Initialize the pipeline (will download model if not cached)
            generator = pipeline('text-generation', model=model)
            
            # Generate response with proper parameters
            if is_advanced_model:
                # Advanced models benefit from higher temperature and better parameters
                result = generator(
                    prompt, 
                    max_length=max_length, 
                    num_return_sequences=1,
                    do_sample=True,
                    temperature=0.3,
                    top_k=40,
                    top_p=0.9,
                    repetition_penalty=1.2
                )
            else:
                # Check if this is a conversational query (likely short)
                is_conversational = len(prompt.split()) < 10
                
                if is_conversational:
                    # Use better settings for conversational queries
                    result = generator(
                        prompt, 
                        max_length=100,  # Shorter responses for conversational queries
                        num_return_sequences=1,
                        do_sample=True,
                        temperature=0.7,  # Higher temperature for more variety
                        top_k=50,
                        top_p=0.9,
                        repetition_penalty=1.8  # Stronger repetition penalty
                    )
                else:
                    # More conservative settings for smaller models (non-conversational)
                    result = generator(
                        prompt, 
                        max_length=max_length, 
                        num_return_sequences=1,
                        do_sample=True,
                        temperature=0.2,
                        top_k=30,
                        top_p=0.85,
                        repetition_penalty=1.5  # Add higher repetition penalty to prevent loops
                    )
            
            # Extract the generated text
            generated_text = result[0]['generated_text']
            
            # Clean up the response if needed (removing the prompt)
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
                
            logger.info(f"Successfully generated text with HuggingFace: {generated_text[:50]}...")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating text with HuggingFace: {str(e)}")
            return f"Sorry, I encountered an error while generating a response: {str(e)}"
