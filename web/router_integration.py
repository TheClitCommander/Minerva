"""
Router Integration Module

This module provides the bridge between Minerva's existing architecture 
and the new Advanced Model Router system.

It shows how to integrate the advanced routing capabilities into the 
current processing flow.
"""

import asyncio
import logging
import traceback
from typing import Dict, Any, List, Optional

# Import from existing Minerva architecture
from web.multi_ai_coordinator import MultiAICoordinator
from web.route_request import get_query_tags, estimate_query_complexity
from web.ensemble_validator import ensemble_validator

# Import the new router
from web.advanced_model_router import AdvancedModelRouter, router

# Set up logging
logger = logging.getLogger(__name__)

class MinervaAIOrchestrator:
    """
    Main orchestrator class that integrates the advanced model router
    with Minerva's existing processing pipeline.
    """
    
    def __init__(self, coordinator: Optional[MultiAICoordinator] = None):
        """Initialize the orchestrator
        
        Args:
            coordinator: Optional MultiAICoordinator instance
        """
        # Get a reference to the MultiAICoordinator
        try:
            # Use the provided coordinator if available, otherwise create a new one
            self.coordinator = coordinator
            
            # Import coordinator from app only as a fallback
            if not self.coordinator:
                try:
                    # Try to use the global coordinator from app module
                    from web.multi_ai_coordinator import MultiAICoordinator
                    self.coordinator = MultiAICoordinator.get_instance()
                    logger.info("Orchestrator using global coordinator instance from MultiAICoordinator.get_instance()")
                except Exception as e:
                    logger.error(f"Error getting global coordinator: {e}")
                    self.coordinator = MultiAICoordinator()
                    logger.warning("Created new MultiAICoordinator instance as fallback")
            
            # Log all registered models in the coordinator
            model_count = len(self.coordinator.model_processors) if hasattr(self.coordinator, 'model_processors') else 0
            
            if model_count > 0:
                logger.info(f"✅ Orchestrator using coordinator with {model_count} registered models: {list(self.coordinator.model_processors.keys())}")
            else:
                logger.warning("⚠️ Orchestrator using coordinator with NO registered models!")
        except Exception as e:
            logger.error(f"Error initializing coordinator in MinervaAIOrchestrator: {str(e)}")
            self.coordinator = MultiAICoordinator()
            logger.warning("Created new MultiAICoordinator instance due to error")
        
        # Initialize the router with our coordinator
        self.router = AdvancedModelRouter(self.coordinator)
        logger.info("✅ MinervaAIOrchestrator initialized successfully")
    
    async def process_with_think_tank(self, 
                                     user_id: str, 
                                     message: str, 
                                     conversation_id: str = None,
                                     use_advanced_routing: bool = True,
                                     test_mode: bool = False,
                                     context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.info(f"[🚨 THINK_TANK] Starting processing with test_mode={test_mode}, type={type(test_mode)}, user_id={user_id}")
        """
        Process a message using Minerva's Think Tank mode with advanced routing.
        
        Args:
            user_id: User identifier
            message: The user's message to process
            conversation_id: Optional conversation identifier
            use_advanced_routing: Whether to use advanced routing or fall back to the legacy system
            test_mode: Whether this is a test request
            context_data: Optional dictionary containing additional context like user preferences and patterns
            
        Returns:
            Response dictionary with model selections and final response
        """
        logger.info(f"🚀 Processing Think Tank message for user {user_id}: {message[:50]}... (conversation: {conversation_id})")

        # Log models available in coordinator at query time
        if hasattr(self.coordinator, 'model_processors'):
            model_count = len(self.coordinator.model_processors)
            model_names = list(self.coordinator.model_processors.keys())
            logger.info(f"[THINK_TANK] Processing with {model_count} available models: {model_names}")
        else:
            logger.warning("[THINK_TANK] No model processors available in coordinator!")

        # EMERGENCY FIX: Direct API call to bypass the complex model selection system
        # Only use when test_mode is True
        logger.critical(f"[💡 TEST_MODE] Using SIMULATED MODEL mode: test_mode={test_mode}, type={type(test_mode)}")
        if test_mode:
            logger.critical("[🚀 TEST MODE] Starting simulated processors (bypassing external API calls)")
            try:
                # Import necessary libraries
                import os
                import time
                import datetime
                import random
                import asyncio
                from web.multi_model_processor import (
                    simulated_gpt4_processor,
                    simulated_claude3_processor,
                    simulated_gemini_processor,
                    simulated_gpt35_processor,
                    simulated_mistral7b_processor,
                    simulated_gpt4all_processor
                )
                
                # Define the simulated model to use - based on query type
                # Extract query tags and complexity for better model selection
                tags = get_query_tags(message)
                complexity = estimate_query_complexity(message)
                
                logger.critical(f"[🧠 ANALYSIS] Query tags: {tags}, complexity: {complexity}")
                
                # Choose the appropriate simulated model based on query type
                # We prioritize different models for different query types
                if "code" in tags or "technical" in tags or complexity > 7:
                    primary_model = "gpt4"
                    processor = simulated_gpt4_processor
                    logger.critical(f"[🤖 MODEL SELECTION] Selected simulated GPT-4 for code/technical query")
                elif "creative" in tags:
                    primary_model = "claude3"
                    processor = simulated_claude3_processor
                    logger.critical(f"[🤖 MODEL SELECTION] Selected simulated Claude-3 for creative query")
                elif "reasoning" in tags or "multi_perspective" in tags:
                    # Alternate between simulated models to test blending
                    models = ["gpt4", "claude3", "gemini"]
                    processors = {
                        "gpt4": simulated_gpt4_processor,
                        "claude3": simulated_claude3_processor,
                        "gemini": simulated_gemini_processor
                    }
                    
                    # Get responses from multiple models asynchronously
                    async def get_multiple_responses():
                        tasks = []
                        for model in models:
                            tasks.append(processors[model](message, test_mode=True))
                        return await asyncio.gather(*tasks)
                    
                    # Get responses from multiple models
                    responses = await get_multiple_responses()
                    
                    # Create a blended response
                    logger.critical(f"[🔄 BLENDING] Blending responses from {len(models)} models")
                    
                    # Process and blend responses
                    blended_sections = []
                    for i, model in enumerate(models):
                        response = responses[i]
                        # Take different sections from different models
                        if isinstance(response, str):
                            # Split into paragraphs and take some paragraphs from each model
                            paragraphs = response.split('\n\n')
                            section_length = min(2, len(paragraphs))
                            contribution = section_length / len(paragraphs) if paragraphs else 0
                            
                            # Take 1-2 paragraphs from each model
                            start_idx = random.randint(0, max(0, len(paragraphs) - section_length))
                            section = '\n\n'.join(paragraphs[start_idx:start_idx + section_length])
                            
                            blended_sections.append({
                                "model": model,
                                "section": section,
                                "contribution": contribution
                            })
                    
                    # Combine the sections into a coherent response
                    blended_response = "\n\n".join([s["section"] for s in blended_sections])
                    
                    # Add introduction and conclusion if it's a longer response
                    if complexity > 5:
                        intro = "This question requires examining multiple perspectives and considerations.\n\n"
                        conclusion = "\n\nIn conclusion, this analysis represents a synthesis of multiple viewpoints on this complex topic."
                        blended_response = intro + blended_response + conclusion
                    
                    logger.critical(f"[✅ SUCCESS] Created blended response from multiple models! Length: {len(blended_response)} chars")
                    
                    # Return a properly formatted blended response
                    return {
                        "response": blended_response,
                        "model_info": {
                            "best_model": models[0],  # Primary model
                            "blended": True,
                            "models_used": models,
                            "complexity": complexity,
                            "task_type": "multi_perspective",
                            "response_source": "simulated_blend",
                            "tags": tags,
                            "blending_info": {
                                "strategy": "paragraph_selection",
                                "sections": blended_sections
                            }
                        },
                        "debug_info": {
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "message_length": len(message),
                            "test_mode": True,
                            "simulated": True,
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    }
                else:
                    # For simpler queries, use GPT-3.5
                    primary_model = "gpt-3.5-turbo"
                    processor = simulated_gpt35_processor
                    logger.critical(f"[🤖 MODEL SELECTION] Selected simulated GPT-3.5 for general query")
                
                # Generate response using selected simulated processor
                if "reasoning" not in tags and "multi_perspective" not in tags:
                    logger.critical(f"[🚀 SIMULATED] Generating response using simulated {primary_model}")
                    
                    # Call the processor function
                    response_text = await processor(message, test_mode=True)
                    
                    logger.critical(f"[✅ SUCCESS] Got simulated response from {primary_model}! Length: {len(response_text)} chars")
                    logger.critical(f"[✅ RESPONSE PREVIEW] First 100 chars: {response_text[:100]}...")
                    
                    # Return a properly formatted response
                    return {
                        "response": response_text,
                        "model_info": {
                            "best_model": primary_model,
                            "blended": False,
                            "models_used": [primary_model],
                            "complexity": complexity,
                            "task_type": tags[0] if tags else "general",
                            "response_source": "simulated_processor",
                            "tags": tags
                        },
                        "debug_info": {
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "message_length": len(message),
                            "test_mode": True,
                            "simulated": True,
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    }
                
            except Exception as setup_error:
                import traceback
                logger.critical(f"[❌ CRITICAL ERROR] Failed to set up simulated processors: {str(setup_error)}")
                logger.critical(f"[❌ ERROR TYPE] {type(setup_error).__name__}")
                logger.critical(f"[❌ TRACEBACK] {traceback.format_exc()}")
                
                # Return an error response that explains the setup failure
                return {
                    "response": f"I apologize, but I encountered an error when setting up the simulated processors: {str(setup_error)}. This is a technical issue with the test environment.",
                    "model_info": {
                        "best_model": "error_fallback",
                        "blended": False,
                        "models_used": [],
                        "complexity": 1,
                        "task_type": "error_handling",
                        "response_source": "error_handler",
                        "tags": ["error", "fallback"],
                        "error": str(setup_error)
                    }
                }
        
        if not test_mode:
            logger.info("[ℹ️ INFO] Test mode disabled, using standard model selection logic")
        
        if not use_advanced_routing:
            logger.info("⚠️ Advanced routing disabled, using legacy processing")
            # Fall back to legacy processing
            return await self._legacy_process(user_id, message, conversation_id)
        
        # Use advanced routing system
        try:
            # DEBUGGING: Log available models in coordinator
            available_models = list(self.coordinator.model_processors.keys()) if hasattr(self.coordinator, 'model_processors') else []
            logger.info(f"🔍 Available models in coordinator: {available_models}")
            
            # DEBUGGING: Check actual model processor functions
            if hasattr(self.coordinator, 'model_processors'):
                for model_name, processor in self.coordinator.model_processors.items():
                    logger.info(f"🔍 MODEL DEBUG: {model_name} processor is {processor.__name__ if hasattr(processor, '__name__') else 'unnamed'}")
            
            # DEBUG coordinator._model_capabilities
            if hasattr(self.coordinator, '_model_capabilities'):
                logger.info(f"🔍 MODEL CAPABILITIES: {list(self.coordinator._model_capabilities.keys())}")
            
            # 1. Get task classification and model selection from advanced router
            logger.info(f"🔎 Classifying task for message: {message[:50]}...")
            try:
                # Initialize enhanced task context 
                enhanced_message_context = {
                    'message': message,
                    'user_id': user_id,
                    'conversation_id': conversation_id
                }
                
                # Incorporate learned context if available
                if context_data and isinstance(context_data, dict):
                    # Extract user preferences and patterns from learning system
                    user_context = context_data.get('user_context', {})
                    if user_context:
                        logger.info(f"[🧠 LEARNING] Enhancing task classification with learned context")
                        
                        # Add user preferences to task context
                        if 'preferences' in user_context:
                            enhanced_message_context['user_preferences'] = user_context['preferences']
                            logger.info(f"[🧠 PREFERENCES] Applied {len(user_context['preferences'])} user preferences")
                        
                        # Add pattern matches to task context
                        if 'patterns' in user_context:
                            enhanced_message_context['user_patterns'] = user_context['patterns']
                            logger.info(f"[🧠 PATTERNS] Applied {len(user_context['patterns'])} detected patterns")
                        
                        # Add topic interests if available
                        if 'topics' in user_context:
                            enhanced_message_context['user_topics'] = user_context['topics']
                            logger.info(f"[🧠 TOPICS] Applied {len(user_context['topics'])} topic interests")
                
                # Call router with enhanced context
                task_info = self.router.classify_task(message, context=enhanced_message_context)
                logger.info(f"[🔍 DEBUG] Task classification successful: {task_info}")
            except Exception as e:
                logger.error(f"[❌ ERROR] Task classification failed: {str(e)}")
                logger.error(f"[❌ ERROR] Traceback: {traceback.format_exc()}")
                return await self._legacy_process(user_id, message, conversation_id)
            
            # DEBUGGING: Check if the router exists and has model functions
            if hasattr(self.router, 'available_models'):
                logger.info(f"[🔍 DEBUG] Models available to router: {self.router.available_models}")
            else:
                logger.error(f"[❌ ERROR] Router has no available_models attribute!")
                return await self._legacy_process(user_id, message, conversation_id)
            
            # FORCE models for debugging
            forced_models = []
            if 'gpt4' in self.router.available_models:
                forced_models = ['gpt4']
                logger.info(f"[🚀 FORCED] Manually selecting GPT-4 for debugging!")
            elif 'claude3' in self.router.available_models:
                forced_models = ['claude3']
                logger.info(f"[🚀 FORCED] Manually selecting Claude-3 for debugging!")
            
            # Try both the router's selection and our forced selection
            try:
                if forced_models:
                    selected_models = forced_models
                    logger.info(f"[🚀 FORCED] Using forced model selection: {selected_models}")
                else:
                    selected_models = self.router.select_models(task_info)
                    logger.info(f"[🔍 DEBUG] Router selected models: {selected_models}")
            except Exception as e:
                logger.error(f"[❌ ERROR] Model selection failed: {str(e)}")
                logger.error(f"[❌ ERROR] Traceback: {traceback.format_exc()}")
                return await self._legacy_process(user_id, message, conversation_id)
            
            logger.info(f"[✅ SUCCESS] Task classified as: {task_info['task_type']} with complexity {task_info['complexity']}")
            logger.info(f"[🤖 MODELS] Final selected models: {selected_models}")
            
            # 2. Process with selected models in parallel
            logger.info(f"[🔄 PROCESSING] Querying {len(selected_models)} models in parallel: {', '.join(selected_models)}")
            
            # DEBUGGING: Check each model processor function availability
            from web.advanced_model_router import MODEL_FUNCTIONS
            model_processor_status = {}
            
            # First check coordinator processors
            if hasattr(self.coordinator, 'model_processors'):
                for model in selected_models:
                    if model in self.coordinator.model_processors:
                        processor = self.coordinator.model_processors[model]
                        model_processor_status[model] = f"Found in coordinator: {processor.__name__ if hasattr(processor, '__name__') else 'unnamed'}"
                        logger.info(f"[✅ SUCCESS] Model {model} found in coordinator processors")
                    else:
                        model_processor_status[model] = "Not found in coordinator"
                        logger.warning(f"[⚠️ WARNING] Model {model} not in coordinator processors")
            else:
                logger.error(f"[❌ ERROR] Coordinator has no model_processors attribute!")
                model_processor_status['coordinator_status'] = "No model_processors attribute"
            
            # Then check MODEL_FUNCTIONS
            for model in selected_models:
                if model in MODEL_FUNCTIONS:
                    processor = MODEL_FUNCTIONS[model]
                    model_processor_status[f"{model}_func"] = f"Found in MODEL_FUNCTIONS: {processor.__name__ if hasattr(processor, '__name__') else 'unnamed'}"
                    logger.info(f"[✅ SUCCESS] Model {model} found in MODEL_FUNCTIONS")
                else:
                    model_processor_status[f"{model}_func"] = "Not found in MODEL_FUNCTIONS"
                    logger.warning(f"[⚠️ WARNING] Model {model} not found in MODEL_FUNCTIONS")
            
            logger.info(f"[🔍 DEBUG] Model processor status summary: {model_processor_status}")
                
            try:
                model_responses = await self.router.query_models(message, selected_models)
                logger.info(f"[✅ SUCCESS] model_responses returned: {type(model_responses).__name__}")
            except Exception as e:
                logger.error(f"[❌ ERROR] query_models failed: {str(e)}")
                # Import traceback locally to avoid scope issues
                try:
                    import traceback as tb
                    logger.error(f"[❌ ERROR] Traceback: {tb.format_exc()}")
                except Exception as tb_error:
                    logger.error(f"[❌ ERROR] Could not capture traceback: {str(tb_error)}")
                return await self._legacy_process(user_id, message, conversation_id)
            
            # DEBUGGING: Log the responses received
            if not model_responses:
                logger.error(f"[❌ ERROR] No responses received from any models! Empty model_responses dict.")
            else:
                logger.info(f"[🔍 DEBUG] Response keys: {list(model_responses.keys())}")
                
                for model, response in model_responses.items():
                    if isinstance(response, str) and response.startswith("Error"):
                        logger.error(f"[❌ ERROR] Error from {model}: {response}")
                    elif model == "local_fallback":
                        logger.warning(f"[⚠️ WARNING] Got local_fallback in responses! This indicates all model calls failed.")
                        logger.info(f"[🔍 DEBUG] local_fallback response: {str(response)[:100]}...")
                    else:
                        logger.info(f"[✅ SUCCESS] Got valid response from {model}")
                        logger.info(f"[🔍 DEBUG] Response type: {type(response).__name__}")
                        
                        # Check response format
                        if isinstance(response, dict):
                            logger.info(f"[🔍 DEBUG] Response keys: {list(response.keys())}")
                        elif isinstance(response, str):
                            logger.info(f"[🔍 DEBUG] String response preview: {response[:100]}...")
            
            logger.info(f"[📈 STATS] Received {len(model_responses)} model responses: {list(model_responses.keys())}")
            
            if not model_responses:
                # If no responses, fall back to legacy processing
                logger.warning("⚠️ No responses from advanced router, falling back to legacy processing")
                return await self._legacy_process(user_id, message, conversation_id)
            
            # 3. Analyze and rank the model responses
            best_model, best_response = self.router.rank_and_select_best(model_responses, task_info)
            
            # Get detailed rankings from the ensemble validator for metadata
            from web.ensemble_validator import ensemble_validator
            
            # Format task_info for ranking
            task_query = task_info.get('query', message)
            task_type = task_info.get('task_type', 'general')
            
            # Get detailed rankings including structure scores
            ranking_result = ensemble_validator.rank_responses(model_responses, task_query, query_type=task_type)
            detailed_rankings = ranking_result.get('rankings', [])
            structure_scores = ranking_result.get('structure_scores', {})
            
            # Calculate overall structure score for the best model
            best_model_structure_score = structure_scores.get(best_model, 0)
            # Normalize to 0-10 scale for the API response
            normalized_structure_score = round(best_model_structure_score * 10, 1)
            
            logger.info(f"[🔍 STRUCTURE SCORES] Best model {best_model} structure score: {normalized_structure_score}/10")
            
            # 4. Determine if blending is appropriate
            should_blend = self.router.should_blend_responses(model_responses, task_info)
            
            # 5. Generate final response
            if should_blend:
                final_response = self.router.blend_responses(model_responses, task_info)
                response_source = "blended"
            else:
                final_response = best_response
                response_source = best_model
            
            # 6. Format the complete response with metadata
            result = {
                "response": final_response,
                "model_info": {
                    "task_type": task_info["task_type"],
                    "complexity": task_info["complexity"],
                    "tags": task_info["tags"],
                    "models_used": list(model_responses.keys()),
                    "best_model": best_model,
                    "response_source": response_source,
                    "blended": should_blend,
                    "structure_score": normalized_structure_score,
                    "model_rankings": detailed_rankings,
                    "structure_scores": {model: round(score * 10, 1) for model, score in structure_scores.items()}
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in advanced processing: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            # Fall back to legacy processing on error
            return await self._legacy_process(user_id, message, conversation_id)
    
    async def _legacy_process(self, user_id: str, message: str, conversation_id: str = None) -> Dict[str, Any]:
        """
        Legacy processing method (fallback)
        
        Provides a basic response when the advanced router is unavailable.
        """
        logger.info("Using simplified fallback response")
        
        # Create a simple fallback response
        return {
            "response": f"I received your message: '{message}'. I'm currently running with limited capabilities. "
                      f"The advanced AI orchestration system is experiencing issues. I'll still try to assist you "
                      f"with your query to the best of my ability.",
            "model_info": {
                "task_type": "general",
                "complexity": 5,
                "tags": ["fallback"],
                "models_used": ["local_fallback"],
                "best_model": "local_fallback",
                "response_source": "local_fallback",
                "blended": False
            }
        }


# We'll initialize this at startup
orchestrator = None

# Main function for processing messages
async def process_with_orchestrator(user_id: str, 
                                   message: str, 
                                   conversation_id: str = None,
                                   use_advanced_routing: bool = True,
                                   test_mode: bool = False,
                                   context_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main entry point for processing messages using the AI Orchestrator.
    
    Args:
        user_id: User identifier
        message: User message to process
        conversation_id: Optional conversation identifier
        use_advanced_routing: Whether to use advanced routing
        test_mode: Whether to run in test mode with direct API calls
        context_data: Optional dictionary containing additional context (user preferences, patterns, etc.)
        
    Returns:
        Response from the AI orchestrator
    """
    # SYSTEMATIC DEBUGGING: Added more comprehensive debug logs per user request
    query_type = "general"  # Default type
    complexity = 5  # Default medium complexity
    
    logger.critical(f"🟢 [ORCHESTRATOR] Query: {message[:50]}... | Type: {query_type} | Complexity: {complexity} | test_mode={test_mode}")
    
    # CRITICAL: Verify OpenAI API key configuration
    import os
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        key_format = f"{api_key[:3]}...{api_key[-3:]} (length: {len(api_key)})"
        logger.critical(f"[✅ API KEY] OpenAI API key format: {key_format}")
    else:
        logger.critical("[❌ CRITICAL ERROR] OpenAI API key is NOT set in environment variables")
        logger.critical("[⚠️ API WARNING] All OpenAI model calls will fail without an API key")
    
    # Log what models are available in the orchestrator
    if orchestrator and hasattr(orchestrator, 'coordinator') and hasattr(orchestrator.coordinator, 'model_processors'):
        available_models = list(orchestrator.coordinator.model_processors.keys())
        logger.critical(f"🔍 [ORCHESTRATOR MODELS] Available models: {available_models}")
        
        if not available_models:
            logger.critical("[❌ CRITICAL ERROR] No models are registered in the orchestrator")
            logger.critical("[⚠️ ROOT CAUSE] This is why queries are using local_fallback responses")
    else:
        logger.critical("[❌ CRITICAL ERROR] Orchestrator or coordinator not properly initialized")
    try:
        # SYSTEMATIC DEBUGGING: Check orchestrator instance
        if not orchestrator:
            logger.critical("[❌ CRITICAL ERROR] Orchestrator is None - initialization failed")
            raise ValueError("Orchestrator is not initialized")
        
        if not hasattr(orchestrator, 'process_with_think_tank'):
            logger.critical("[❌ CRITICAL ERROR] Orchestrator missing 'process_with_think_tank' method")
            logger.critical(f"[❌ DEBUG] Orchestrator has attributes: {dir(orchestrator)}")
            raise ValueError("Orchestrator missing required methods")
        
        # SYSTEMATIC DEBUGGING: Check coordinator instance within orchestrator
        if not hasattr(orchestrator, 'coordinator'):
            logger.critical("[❌ CRITICAL ERROR] Orchestrator has no coordinator attribute")
            raise ValueError("Orchestrator coordinator not initialized")
            
        # SYSTEMATIC DEBUGGING: Show routing decision
        if use_advanced_routing:
            logger.critical(f"🛠 [ROUTING] Using advanced routing for query")
        else:
            logger.critical(f"🛠 [ROUTING] Using standard routing for query")
        
        # Log the call to process_with_think_tank
        logger.critical(f"🚀 [ORCHESTRATOR] Calling process_with_think_tank with test_mode={test_mode}")
        
        # SYSTEMATIC DEBUGGING: Start profiling execution time
        import time
        start_time = time.time()
        
        # Attempt to process with think tank
        # Initialize context data if needed
        if context_data is None:
            context_data = {}
        
        # Log the context data for debugging
        if context_data and 'user_context' in context_data:
            user_context_keys = list(context_data.get('user_context', {}).keys())
            logger.critical(f"[CONTEXT] Using enhanced context with keys: {user_context_keys}")
            
            # Log preferences if available
            if 'preferences' in context_data.get('user_context', {}):
                preferences = context_data['user_context']['preferences']
                logger.critical(f"[PREFERENCES] Using learned preferences: {preferences[:3]}{'...' if len(preferences) > 3 else ''}")
        
        result = await orchestrator.process_with_think_tank(
            user_id=user_id,
            message=message,
            conversation_id=conversation_id,
            use_advanced_routing=use_advanced_routing,
            test_mode=test_mode,
            context_data=context_data
        )
        
        # Record execution time
        execution_time = time.time() - start_time
        logger.critical(f"[⏱ TIMING] process_with_think_tank took {execution_time:.2f} seconds")
        
        # SYSTEMATIC DEBUGGING: Log detailed information about the response
        model_info = result.get('model_info', {})
        response_preview = result.get('response', '')[:100] + '...' if result.get('response') else 'No response text'
        
        # Check if this is a local fallback response
        is_fallback = model_info.get('best_model') == 'local_fallback' or model_info.get('response_source') == 'local_fallback'
        
        if is_fallback:
            logger.critical("[❌ FALLBACK DETECTED] Response is using local_fallback!")
            logger.critical(f"[⚠️ FALLBACK REASON] {model_info.get('fallback_reason', 'Unknown reason')}")
        else:
            logger.critical(f"[✅ SUCCESS] Response received from external model!")
        
        logger.critical(f"[📝 SOURCE] Response source: {model_info.get('response_source', 'unknown')}")
        logger.critical(f"[📝 MODELS] Models used: {model_info.get('models_used', [])}")
        logger.critical(f"[📝 BEST MODEL] Selected model: {model_info.get('best_model', 'none')}")
        logger.critical(f"[📝 PREVIEW] Response: {response_preview}")
        
        # SYSTEMATIC DEBUGGING: Add detailed analysis of response content
        if 'blended' in model_info:
            logger.critical(f"[📝 BLEND] Response was blended: {model_info.get('blended', False)}")
            
        # SYSTEMATIC DEBUGGING: Check for any warning signals in the response
        if "limited capabilities" in result.get('response', ''):
            logger.critical("[⚠️ WARNING] Response contains 'limited capabilities' text - indicates fallback")
        if "API key" in result.get('response', ''):
            logger.critical("[⚠️ WARNING] Response mentions API keys - likely an error")
        
        return result
    except Exception as e:
        import traceback
        logger.critical(f"❌ [ORCHESTRATOR ERROR] Error processing query: {str(e)}")
        logger.critical(f"❌ [ERROR TYPE] {type(e).__name__}")
        logger.critical(f"❌ [TRACEBACK] {traceback.format_exc()}")
        
        # SYSTEMATIC DEBUGGING: Check for specific error types
        if "API key" in str(e).lower() or "openai" in str(e).lower():
            logger.critical("[❌ API ERROR] This appears to be an OpenAI API key or authentication issue")
            logger.critical("[⚠️ ROOT CAUSE] API keys missing or invalid - causing fallback responses")
        elif "model" in str(e).lower() and ("not found" in str(e).lower() or "unavailable" in str(e).lower()):
            logger.critical("[❌ MODEL ERROR] This appears to be a model availability issue")
            logger.critical("[⚠️ ROOT CAUSE] Requested model not available or not found")
        elif "timeout" in str(e).lower() or "connection" in str(e).lower():
            logger.critical("[❌ NETWORK ERROR] This appears to be a network or timeout issue")
        
        # Create a fallback response
        logger.critical(f"⚠️ [FALLBACK] Using local fallback response due to orchestrator error")
        logger.critical(f"⚠️ [FALLBACK REASON] {str(e)}")
        return {
            "response": f"Sorry, I encountered an error processing your request. The system returned: {str(e)}",
            "model_info": {
                "error": str(e),
                "models_used": [],
                "best_model": "error_fallback",
                "task_type": "error_handling",
                "complexity": 1,
                "tags": ["error", "fallback"],
                "response_source": "error_handler",
                "blended": False
            }
        }


# Example usage in app.py:
"""
from web.router_integration import process_with_orchestrator

@app.route('/api/v1/think-tank', methods=['POST'])
async def think_tank_api():
    data = request.json
    user_id = data.get('user_id', 'anonymous')
    message = data.get('message', '')
    conversation_id = data.get('conversation_id')
    
    # Get advanced routing preference from headers or config
    use_advanced_routing = request.headers.get('X-Use-Advanced-Routing', 'true').lower() == 'true'
    
    # Process with the orchestrator
    result = await process_with_orchestrator(
        user_id=user_id,
        message=message,
        conversation_id=conversation_id,
        use_advanced_routing=use_advanced_routing
    )
    
    return jsonify(result)
"""
