"""
Think Tank Core Module

Processes requests with multiple AI models based on routing information.
Handles model orchestration, request processing, and response management.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Available model configurations 
MODEL_CAPABILITIES = {
    'gpt-4o': {
        'technical': 0.95,
        'creative': 0.92,
        'reasoning': 0.95,
        'factual': 0.93,
        'structured': 0.94,
        'max_tokens': 8192,
        'context_window': 16384,
    },
    'claude-3-opus': {
        'technical': 0.93,
        'creative': 0.94,
        'reasoning': 0.95,
        'factual': 0.92,
        'structured': 0.95,
        'max_tokens': 8192,
        'context_window': 16384,
    },
    'gpt-4': {
        'technical': 0.9,
        'creative': 0.85,
        'reasoning': 0.91,
        'factual': 0.88,
        'structured': 0.91,
        'max_tokens': 8192,
        'context_window': 8192,
    },
    'gemini-pro': {
        'technical': 0.88,
        'creative': 0.9,
        'reasoning': 0.91,
        'factual': 0.89,
        'structured': 0.87,
        'max_tokens': 4096,
        'context_window': 8192,
    },
    'mistral-large': {
        'technical': 0.87,
        'creative': 0.85,
        'reasoning': 0.89,
        'factual': 0.86,
        'structured': 0.88,
        'max_tokens': 4096,
        'context_window': 8192,
    },
    'gpt-4o-mini': {
        'technical': 0.82,
        'creative': 0.8,
        'reasoning': 0.84,
        'factual': 0.81,
        'structured': 0.83,
        'max_tokens': 4096,
        'context_window': 8192,
    },
    'claude-3': {
        'technical': 0.85,
        'creative': 0.9,
        'reasoning': 0.85,
        'factual': 0.82,
        'structured': 0.85,
        'max_tokens': 4096,
        'context_window': 8192,
    },
    'claude-3-haiku': {
        'technical': 0.8,
        'creative': 0.85,
        'reasoning': 0.82,
        'factual': 0.8,
        'structured': 0.81,
        'max_tokens': 2048,
        'context_window': 4096,
    },
    'Llama-3.2-1B-Instruct-Q4_0.gguf': {
        'technical': 0.75,
        'creative': 0.7,
        'reasoning': 0.72,
        'factual': 0.65,
        'structured': 0.68,
        'max_tokens': 3072,
        'context_window': 4096,
    },
}

def process_with_think_tank(
    message: str, 
    model_priority: List[str] = None, 
    complexity: float = 0.0,
    query_tags: Dict[str, Any] = None,
    conversation_id: str = None
) -> Dict[str, Any]:
    """
    Process a message with multiple AI models according to routing priority
    
    Args:
        message: User message to process
        model_priority: List of models in priority order
        complexity: Assessed complexity score of the message (0-100)
        query_tags: Dict containing query classification tags
    
    Returns:
        Dict containing:
        - responses: Dict of model_name -> response mapping
        - processing_stats: Performance statistics
    """
    if query_tags is None:
        query_tags = {}
    
    # Set default model priority if none provided
    if model_priority is None or len(model_priority) == 0:
        model_priority = ['gpt-4o', 'claude-3-opus', 'gpt-4', 'gemini-pro']
    
    # Log processing details
    logger.info(f"Processing with Think Tank, priority: {model_priority}, complexity: {complexity}")
    logger.info(f"Query tags: {query_tags}")
    if conversation_id:
        logger.info(f"Using conversation ID: {conversation_id}")
    
    # Initialize processing stats
    start_time = time.time()
    processing_stats = {
        'started_at': datetime.now().isoformat(),
        'model_stats': {},
        'total_models': len(model_priority),
        'complexity_score': complexity,
    }
    
    # Integrate with the smart model selector for cost optimization
    try:
        # Import the smart model selector to optimize model selection based on cost
        from web.integrations.smart_model_selector import select_cost_efficient_model, estimate_cost_savings
        
        # Try to optimize the model selection based on query complexity and budget
        query_type = query_tags.get('primary_domain', 'general_knowledge')
        system_prompt = _get_system_prompt(query_tags)
        
        # Apply cost optimization for the primary model
        original_primary = model_priority[0] if model_priority else "gpt-4"
        primary_model, selection_metadata = select_cost_efficient_model(
            requested_model=original_primary,
            message=message,
            system_prompt=system_prompt,
            force_requested=False
        )
        
        # Log the model selection decision
        if original_primary != primary_model:
            savings = estimate_cost_savings(original_primary, primary_model)
            logger.info(f"Cost optimization: Changed primary model from {original_primary} to {primary_model} (est. savings: {savings:.1f}%)")
            logger.info(f"Selection reason: {selection_metadata.get('selection_method', 'unknown')}")
            
            # Record the optimization in stats
            processing_stats['cost_optimization'] = {
                'original_model': original_primary,
                'selected_model': primary_model,
                'estimated_savings': savings,
                'selection_method': selection_metadata.get('selection_method', 'unknown'),
                'query_type': query_type,
                'budget_risk': selection_metadata.get('budget_risk', 'unknown')
            }
            
            # Update the model priority list with the optimized primary model
            if primary_model not in model_priority:
                model_priority = [primary_model] + [m for m in model_priority if m != primary_model]
            else:
                # Move the optimized model to the front if it's already in the list
                model_priority.remove(primary_model)
                model_priority.insert(0, primary_model)
    except ImportError as e:
        logger.warning(f"Smart model selector not available, using default model priority: {e}")
    except Exception as e:
        logger.error(f"Error during cost optimization, using default model priority: {e}")
    
    # Determine how many models to use based on complexity and domain specificity
    domains = query_tags.get('domains', [])
    request_types = query_tags.get('request_types', [])
    
    # Adjust model usage strategy based on query complexity and type
    # Simple queries use fewer models, complex queries use more
    is_simple_query = complexity < 0.5 and not any(t in request_types for t in ['comparison', 'technical', 'reasoning'])
    use_more_models = complexity > 1.5 or 'ai' in domains or 'comparison' in request_types or 'technical' in request_types
    
    # For simple queries, just use one cost-efficient model
    # For complex queries, use multiple models but prioritize cost-efficiency
    if is_simple_query:
        model_count = 1  # Use only one model for simple queries to save costs
        logger.info(f"Using 1 model for simple query (complexity: {complexity})")
    else:
        model_count = min(3 if use_more_models else 2, len(model_priority))
        logger.info(f"Using {model_count} models due to complexity {complexity} and domain specificity")
    
    # Limit to the top models based on priority and domain suitability
    priority_models = model_priority[:model_count]
    logger.info(f"Using {model_count} models due to complexity {complexity} and domain specificity")
    
    # Container for all model responses
    responses = {}
    errors = {}
    
    # Get appropriate prompt for this message type
    system_prompt = _get_system_prompt(query_tags)
    
    # Process with each model according to priority
    available_models = _get_available_models()
    
    for model_name in priority_models:
        # Skip if we don't have this model available
        if model_name not in available_models:
            logger.warning(f"Model {model_name} not available, skipping")
            continue
            
        # Track model processing stats
        model_start_time = time.time()
        
        try:
            # Get model's response
            # For AI/ML queries, provide specialized system prompt
            specialized_prompt = system_prompt
            if 'ai' in domains:
                specialized_prompt += "\n\nThis query relates to artificial intelligence or machine learning. Provide detailed technical information, explain concepts clearly, and include practical implementation details where appropriate."
            
            # Get model's response with the potentially specialized prompt
            response = _get_model_response(model_name, message, specialized_prompt)
            responses[model_name] = response
            
            processing_stats['model_stats'][model_name] = {
                'processing_time': time.time() - model_start_time,
                'success': True,
                'response_length': len(response),
                'specialized_prompt': 'ai' in domains,
            }
            
            # Using real AI model integrations via the centralized model hub
            # Each model provides an authentic response based on its capabilities
            
        except Exception as e:
            logger.error(f"Error processing with model {model_name}: {str(e)}")
            errors[model_name] = str(e)
            processing_stats['model_stats'][model_name] = {
                'processing_time': time.time() - model_start_time,
                'success': False,
                'error': str(e),
            }
    
    # Update overall processing stats
    processing_stats['total_time'] = time.time() - start_time
    processing_stats['successful_models'] = len(responses)
    processing_stats['failed_models'] = len(errors)
    processing_stats['model_count'] = model_count
    processing_stats['used_more_models'] = use_more_models
    
    logger.info(f"Think Tank processing complete. Success: {len(responses)}, Failed: {len(errors)}")
    
    # Extract primary domain and request type for better response blending
    primary_domain = query_tags.get('primary_domain', None)
    primary_request = query_tags.get('primary_request', None)
    
    # Format enriched query metadata
    query_metadata = {
        'domains': domains,
        'request_types': request_types,
        'primary_domain': primary_domain,
        'primary_request': primary_request,
        'has_ai_content': 'ai' in domains,
        'is_technical': any(tech in domains for tech in ['code', 'math', 'science', 'ai', 'data']),
        'is_comparison': 'comparison' in request_types,
        'is_troubleshooting': 'troubleshooting' in request_types,
        'complexity_score': complexity
    }
    
    return {
        'responses': responses,
        'processing_stats': processing_stats,
        'errors': errors,
        'query_tags': query_tags,
        'query_metadata': query_metadata,
        'model_count': model_count
    }

def _get_available_models() -> List[str]:
    """
    Get list of available AI models that can be used
    
    Checks the model integration hub to see which models are available
    based on configured API keys and services
    
    Returns:
        List of available model names
    """
    try:
        # Get available models from the model integration hub
        from web.integrations.model_integration import model_hub
        available_models = model_hub.list_available_models()
        
        if not available_models:
            logger.warning("No models available from integration hub. Please check API keys and connections.")
        else:
            logger.info(f"Available models from integration hub: {available_models}")
            
        return available_models
    except ImportError as e:
        # This is now a critical error as we exclusively rely on the model hub
        error_msg = f"Model integration hub not available: {str(e)}"
        logger.error(error_msg)
        raise ImportError(error_msg)

def _get_system_prompt(query_tags: Dict[str, Any]) -> str:
    """
    Generate appropriate system prompt based on query tags
    
    Args:
        query_tags: Dict containing query classification
        
    Returns:
        System prompt string appropriate for the query type
    """
    domains = query_tags.get('domains', [])
    request_types = query_tags.get('request_types', [])
    primary_domain = query_tags.get('primary_domain')
    primary_request = query_tags.get('primary_request')
    memory_context = query_tags.get('memory_context', {})
    
    # Base prompt components
    base_prompt = "You are Minerva, an intelligent assistant with expertise across many domains. "
    response_guidance = "Provide a clear, accurate and helpful response. "
    
    # Domain-specific prompt additions
    domain_prompts = {
        'code': "Focus on providing clean, efficient code with proper documentation and explanation. Pay attention to edge cases and potential issues.",
        'math': "Show your work step-by-step and explain the reasoning behind each step. Use proper mathematical notation where appropriate.",
        'science': "Base your response on scientific evidence and cite relevant research or principles. Distinguish between established facts and theories.",
        'business': "Consider practical business implications, costs, benefits, and risks in your response.",
        'creative': "Be creative and original while staying true to the user's request. Consider different perspectives and approaches.",
        'philosophical': "Explore multiple viewpoints and perspectives. Avoid presenting any single philosophical position as definitive truth."
    }
    
    # Request-type specific prompt additions
    request_prompts = {
        'explanation': "Explain concepts clearly, defining technical terms and using analogies where helpful.",
        'comparison': "Compare options fairly, highlighting both similarities and differences. Present advantages and disadvantages of each option.",
        'procedure': "Provide clear, step-by-step instructions in a logical order. Anticipate common errors or challenges.",
        'evaluation': "Evaluate based on multiple relevant criteria. Support your assessment with reasoning and evidence.",
        'generation': "Generate content that fully addresses the request while maintaining quality and coherence.",
        'opinion': "Offer balanced insights while noting that this represents one perspective among many possible views."
    }
    
    # Build the complete prompt
    prompt_parts = [base_prompt]
    
    # Add domain-specific guidance
    if primary_domain and primary_domain in domain_prompts:
        prompt_parts.append(domain_prompts[primary_domain])
    else:
        # Add any relevant domain prompts (up to 2)
        domain_additions = [domain_prompts[d] for d in domains if d in domain_prompts][:2]
        prompt_parts.extend(domain_additions)
    
    # Add request-type guidance
    if primary_request and primary_request in request_prompts:
        prompt_parts.append(request_prompts[primary_request])
    
    # Add standard response guidance
    prompt_parts.append(response_guidance)
    
    # Add memory context if available
    if memory_context:
        memory_prompt = "\n\nRelevant information from previous conversations:\n"
        
        # Add preference memories if available
        preferences = memory_context.get('preferences', [])
        if preferences:
            memory_prompt += "\nUser preferences: " + "; ".join(preferences) + ".\n"
        
        # Add fact memories if available
        facts = memory_context.get('facts', [])
        if facts:
            memory_prompt += "\nRelevant facts: " + "; ".join(facts) + ".\n"
        
        # Add experience memories if available
        experiences = memory_context.get('experiences', [])
        if experiences:
            memory_prompt += "\nUser experiences: " + "; ".join(experiences) + ".\n"
        
        # Add instruction memories if available
        instructions = memory_context.get('instructions', [])
        if instructions:
            memory_prompt += "\nUser instructions: " + "; ".join(instructions) + ".\n"
        
        # Add general memories if other categories not available
        general = memory_context.get('general', [])
        if general:
            memory_prompt += "\nAdditional context: " + "; ".join(general) + ".\n"
        
        # Add conversation memory guidelines
        memory_prompt += "\nUse this information to provide a more personalized and contextually relevant response. "
        memory_prompt += "Incorporate relevant memories naturally, without explicitly stating 'As you mentioned before' or similar phrases unless it adds value."
        
        # Add memory prompt to the full prompt
        prompt_parts.append(memory_prompt)
    
    # Join all parts
    full_prompt = " ".join(prompt_parts)
    
    return full_prompt

def _get_model_response(model_name: str, message: str, system_prompt: str) -> str:
    """
    Get response from a specific AI model using the central model integration hub
    
    Args:
        model_name: Name of model to use
        message: User message to process
        system_prompt: System prompt to guide response
        
    Returns:
        Model's response text
        
    Raises:
        ValueError: If the model is not available
        Exception: For any errors during model processing
    """
    # Use the centralized model integration hub to get responses from real AI models
    try:
        # Import the model integration hub
        from web.integrations.model_integration import model_hub
        
        # Check if the requested model is available
        if not model_hub.is_model_available(model_name):
            # If requested model isn't available, get all available models
            available_models = model_hub.list_available_models()
            logger.warning(f"Model {model_name} not available. Available models: {available_models}")
            
            # If there are any available models, use the first one as a fallback
            if available_models:
                fallback_model = available_models[0]
                logger.info(f"Using fallback model {fallback_model} instead of {model_name}")
                model_name = fallback_model
            else:
                # No models available - this is a critical error
                error_msg = f"No AI models are available. Please check API keys and connections."
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Use the hub to get a response from the selected model
        logger.info(f"Using real model integration for {model_name}")
        response_tuple = model_hub.get_response(model_name, message, system_prompt)
        # Unpack the tuple - model_hub.get_response returns (response, usage_info)
        response = response_tuple[0] if isinstance(response_tuple, tuple) else response_tuple
        
        # Verify the response is valid
        if not response or not isinstance(response, str) or len(response.strip()) < 10:
            error_msg = f"Model {model_name} returned an invalid or empty response"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        return response
        
    except ImportError as e:
        # If the model hub is not available, this is a critical error
        error_msg = f"Model integration hub not available: {str(e)}"
        logger.error(error_msg)
        raise ImportError(error_msg)
        
    except Exception as e:
        # Log any other errors that occur during model processing
        error_msg = f"Error getting response from model {model_name}: {str(e)}"
        logger.error(error_msg)
        raise

# MODEL INTEGRATION
# All template generators have been removed.
# The system now exclusively uses real AI models through the centralized model integration hub.

