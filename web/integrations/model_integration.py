"""
Model Integration Layer

Central coordination point for all AI model integrations in Minerva.
This module provides a unified interface for accessing different AI models.
"""

import logging
import time
import os
import uuid
from typing import Dict, Any, List, Optional, Tuple

# Configure logger first before using it
logger = logging.getLogger(__name__)

# Import integration modules
from .config import (
    OPENAI_API_KEY, ANTHROPIC_API_KEY, MISTRAL_API_KEY, 
    GOOGLE_API_KEY, COHERE_API_KEY, AVAILABLE_EXTERNAL_MODELS
)

# Import usage tracking and cost optimization functionality
from .usage_tracking import track_model_usage
try:
    from .cost_optimizer import get_cost_optimized_model, is_budget_exceeded, get_budget_status
    from .usage_alerts import check_budget_and_alert, start_budget_monitoring
    COST_OPTIMIZATION_ENABLED = True
except ImportError:
    # Handle the case where cost optimization modules are not available
    logger.warning("Cost optimization modules not found. Cost-aware features will be disabled.")
    COST_OPTIMIZATION_ENABLED = False

class ModelIntegrationHub:
    """
    Central hub for model integrations, providing a unified interface
    for accessing all available models across different providers.
    
    Features:
    - Unified API for accessing all AI models
    - Cost optimization to automatically switch to cheaper models when appropriate
    - Budget monitoring to prevent cost overruns
    - Usage tracking for all model API calls
    """
    
    def __init__(self):
        """Initialize the model integration hub with available models."""
        self.available_models = self._initialize_available_models()
        self.cost_optimization_enabled = COST_OPTIMIZATION_ENABLED
        self.emergency_cost_mode = False
        
        # Start budget monitoring if cost optimization is enabled
        if self.cost_optimization_enabled:
            try:
                # Check if we're already in emergency mode
                budget_status = get_budget_status()
                self.emergency_cost_mode = budget_status.get('emergency_mode', False)
                
                if self.emergency_cost_mode:
                    logger.warning("Starting in EMERGENCY COST-CUTTING MODE due to budget exceeded")
                
                # Start budget monitoring in background
                start_budget_monitoring()
            except Exception as e:
                logger.error(f"Error initializing budget monitoring: {str(e)}")
    
    def _initialize_available_models(self) -> Dict[str, bool]:
        """
        Initialize available model integrations based on API keys.
        
        Returns:
            Dict mapping model names to availability status (True/False)
        """
        available = {}
        
        # OpenAI models
        if OPENAI_API_KEY:
            available.update({
                'gpt-4': True,
                'gpt-4o': True,
                'gpt-4o-mini': True,
                'gpt4': True,  # Alias for gpt-4
            })
            logger.info("✅ OpenAI API models initialized")
        else:
            logger.warning("⚠️ OpenAI API models unavailable - missing API key")
        
        # Anthropic models
        if ANTHROPIC_API_KEY:
            available.update({
                'claude-3': True,
                'claude3': True,  # Alias
                'claude-3-opus': True,
                'claude-3-haiku': True,
            })
            logger.info("✅ Anthropic API models initialized")
        else:
            logger.warning("⚠️ Anthropic API models unavailable - missing API key")
        
        # Mistral models
        if MISTRAL_API_KEY:
            available.update({
                'mistral': True,
                'mistral7b': True,
                'llama': True,    # Handled by Mistral
                'llama2': True,   # Handled by Mistral
            })
            logger.info("✅ Mistral API models initialized")
        else:
            logger.warning("⚠️ Mistral API models unavailable - missing API key")
        
        # Google models
        if GOOGLE_API_KEY:
            available.update({
                'gemini': True,
            })
            logger.info("✅ Google API models initialized")
        else:
            logger.warning("⚠️ Google API models unavailable - missing API key")
        
        # Cohere models
        if COHERE_API_KEY:
            available.update({
                'cohere': True,
            })
            logger.info("✅ Cohere API models initialized")
        else:
            logger.warning("⚠️ Cohere API models unavailable - missing API key")
        
        # GPT4All requires checking if the local model files are available
        try:
            # Try to import GPT4All to check availability
            from web.model_processors import check_gpt4all_availability
            is_available = check_gpt4all_availability()
            available.update({
                'gpt4all': is_available,
            })
            if is_available:
                logger.info("✅ GPT4All local model initialized")
            else:
                logger.warning("⚠️ GPT4All local model unavailable - model files not found")
        except ImportError:
            logger.warning("⚠️ GPT4All integration not available")
            available.update({
                'gpt4all': False,
            })
        
        return available
    
    def is_model_available(self, model_name: str) -> bool:
        """
        Check if a specific model is available for use.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model is available, False otherwise
        """
        return self.available_models.get(model_name, False)
    
    def list_available_models(self) -> List[str]:
        """
        Get a list of all currently available models.
        
        Returns:
            List of available model names
        """
        # Get basic list of available models
        models = [model for model, available in self.available_models.items() 
                 if available]
        
        # If in emergency cost-cutting mode, filter out expensive models
        if self.cost_optimization_enabled and self.emergency_cost_mode:
            from .cost_optimizer import MODEL_COMPLEXITY_TIERS
            
            # Only allow low-tier models in emergency mode
            allowed_models = []
            for provider_models in MODEL_COMPLEXITY_TIERS['low'].values():
                allowed_models.extend(provider_models)
            
            # Filter to only low-tier models
            models = [model for model in models if any(am in model.lower() for am in allowed_models)]
            
            # Ensure we have at least one model available
            if not models:
                logger.warning("Emergency mode would block all models; allowing all to prevent system failure")
                models = [model for model, available in self.available_models.items() 
                          if available]
        
        return models
    
    def get_response(
        self, 
        model_name: str, 
        message: str, 
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        query_type: str = 'general',
        force_requested_model: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Get a response from the specified model.
        
        Args:
            model_name: Name of the model to use
            message: User message to process
            system_prompt: System prompt to guide the model
            temperature: Controls randomness in generation
            max_tokens: Maximum response length
            
        Returns:
            The model's response text
            
        Raises:
            ValueError: If the model is not available
            Exception: For any errors during model processing
        """
        # Check if we need to apply cost optimization
        original_model = model_name
        cost_optimized = False
        
        if self.cost_optimization_enabled and not force_requested_model:
            try:
                # Check if we're in emergency mode
                if not self.emergency_cost_mode:
                    budget_status = get_budget_status()
                    self.emergency_cost_mode = budget_status.get('emergency_mode', False)
                
                # Get all available models
                available_models = self.list_available_models()
                
                # If in emergency mode, force cost optimization
                if self.emergency_cost_mode:
                    optimized_model = get_cost_optimized_model(
                        requested_model=model_name,
                        message=message,
                        system_prompt=system_prompt,
                        available_models=available_models,
                        force_requested=False
                    )
                    
                    if optimized_model != model_name:
                        logger.warning(f"EMERGENCY COST MODE: Switched from {model_name} to {optimized_model}")
                        model_name = optimized_model
                        cost_optimized = True
                else:
                    # Normal cost optimization based on query complexity
                    optimized_model = get_cost_optimized_model(
                        requested_model=model_name,
                        message=message,
                        system_prompt=system_prompt,
                        available_models=available_models,
                        force_requested=False
                    )
                    
                    if optimized_model != model_name:
                        logger.info(f"Cost optimization: Switched from {model_name} to {optimized_model}")
                        model_name = optimized_model
                        cost_optimized = True
            except Exception as e:
                logger.error(f"Error in cost optimization, using original model: {str(e)}")
        
        # Check if the selected model is available
        if not self.is_model_available(model_name):
            error_msg = f"Model {model_name} is not available"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Generate a unique request ID for tracking
        request_id = str(uuid.uuid4())
        
        # Route to the appropriate model integration
        start_time = time.time()
        logger.info(f"Generating response with model: {model_name}")
        
        try:
            # OpenAI models
            if model_name.startswith('gpt') and model_name != 'gpt4all':
                from .openai_integration import generate_response, generate_response_with_usage
                response, usage_info = generate_response_with_usage(
                    message, system_prompt, model_name, temperature, max_tokens
                )
                
            # Anthropic models
            elif 'claude' in model_name:
                from .anthropic_integration import generate_response_with_usage
                response, usage_info = generate_response_with_usage(
                    message, system_prompt, model_name, temperature, max_tokens
                )
                
            # Mistral models
            elif model_name in ['mistral', 'mistral7b', 'llama', 'llama2']:
                from .mistral_integration import generate_response
                response, usage_info = generate_response_with_usage(
                    message, system_prompt, model_name, temperature, max_tokens
                )
                
            # Google models
            elif model_name == 'gemini':
                from .google_integration import generate_response
                response, usage_info = generate_response_with_usage(
                    message, system_prompt, model_name, temperature, max_tokens
                )
                
            # Cohere models
            elif model_name == 'cohere':
                from .cohere_integration import generate_response
                response, usage_info = generate_response_with_usage(
                    message, system_prompt, model_name, temperature, max_tokens
                )
                
            # GPT4All (local model)
            elif model_name == 'gpt4all':
                try:
                    from web.model_processors import process_with_gpt4all_with_usage
                    # Ensure we're passing the system prompt to GPT4All like all other models
                    response, usage_info = process_with_gpt4all_with_usage(message, system_prompt=system_prompt)
                    if not response or len(response.strip()) < 10:
                        logger.warning("GPT4All returned inadequate response, treating as unavailable")
                        self.available_models['gpt4all'] = False
                        raise ValueError("Inadequate response from GPT4All model")
                except Exception as e:
                    logger.error(f"Error with GPT4All model: {str(e)}")
                    self.available_models['gpt4all'] = False
                    raise
                
            else:
                error_msg = f"Unknown model: {model_name}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Generated response with {model_name} in {latency_ms}ms")
            
            # Track the API usage
            self._track_usage(
                model_name=model_name,
                request_id=request_id,
                latency_ms=latency_ms,
                query_type=query_type,
                usage_info=usage_info,
                success=True,
                original_model=original_model if cost_optimized else None
            )
            
            # After successful API call, check budgets and trigger alerts if needed
            if self.cost_optimization_enabled:
                try:
                    check_budget_and_alert()
                except Exception as e:
                    logger.error(f"Error checking budget after API call: {str(e)}")
            
            return response, usage_info
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Error generating response with {model_name}: {str(e)} (after {latency_ms}ms)"
            logger.error(error_msg)
            
            # Track failed API call
            self._track_usage(
                model_name=model_name,
                request_id=request_id,
                latency_ms=latency_ms,
                query_type=query_type,
                usage_info={'input_tokens': 0, 'output_tokens': 0},
                success=False,
                error_message=str(e),
                original_model=original_model if cost_optimized else None
            )
            
            raise Exception(error_msg)

    def _track_usage(self, 
                    model_name: str, 
                    request_id: str,
                    latency_ms: int,
                    query_type: str,
                    usage_info: Dict[str, Any],
                    success: bool,
                    error_message: str = '',
                    original_model: Optional[str] = None):
        """
        Track model usage metrics using the usage tracking system
        
        Args:
            model_name: Name of the model used
            request_id: Unique request ID
            latency_ms: Request latency in milliseconds
            query_type: Type of query (general, code, factual, etc.)
            usage_info: Dictionary containing token usage information
            success: Whether the request was successful
            error_message: Error message if request failed
        """
        try:
            input_tokens = usage_info.get('input_tokens', 0)
            output_tokens = usage_info.get('output_tokens', 0)
            
            # Additional tracking info for cost optimization
            additional_info = {}
            if original_model and original_model != model_name:
                additional_info['original_model'] = original_model
                additional_info['cost_optimized'] = True
            
            # Track the usage
            track_model_usage(
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                query_type=query_type,
                request_id=request_id,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
                **additional_info
            )
            
            if success:
                logger.debug(
                    f"Usage tracked for {model_name}: {input_tokens}in/{output_tokens}out tokens, "
                    f"{latency_ms}ms, type={query_type}"
                )
        except Exception as e:
            # Log but don't raise - we don't want tracking errors to affect the main flow
            logger.error(f"Error tracking usage: {str(e)}")

# Create a singleton instance
model_hub = ModelIntegrationHub()
