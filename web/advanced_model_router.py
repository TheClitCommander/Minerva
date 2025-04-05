import asyncio
import re
import logging
import traceback
import asyncio
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Set, Optional, Union

from web.multi_ai_coordinator import MultiAICoordinator
from web.model_processors import (
    process_with_gpt4o, 
    process_with_claude3, 
    process_with_mistral, 
    process_with_cohere,
    process_with_llama2
)
from web.ensemble_validator import ensemble_validator
from web.route_request import get_query_tags, estimate_query_complexity

# Set up logging
logger = logging.getLogger(__name__)

# Task types and complexity thresholds
TASK_TYPES = {
    "fact_simple": {
        "keywords": ["define", "what is", "who is", "where is", "when did"],
        "complexity_threshold": 3
    },
    "explanation": {
        "keywords": ["how to", "explain", "why", "describe", "elaborate"],
        "complexity_threshold": 5
    },
    "technical": {
        "keywords": ["code", "program", "debug", "fix", "algorithm", "function", "class", "math", "calculate"],
        "complexity_threshold": 7
    },
    "creative": {
        "keywords": ["story", "poem", "creative", "write", "design", "generate", "create"],
        "complexity_threshold": 6
    },
    "comparison": {
        "keywords": ["compare", "versus", "vs", "which is better", "difference between", "similarities"],
        "complexity_threshold": 6
    },
    "reasoning": {
        "keywords": ["analyze", "evaluate", "critique", "assess", "review", "examine"],
        "complexity_threshold": 8
    },
    "research": {
        "keywords": ["research", "investigate", "explore", "study", "comprehensive"],
        "complexity_threshold": 9
    },
    "general": {
        "keywords": [],
        "complexity_threshold": 5
    }
}

# Model capabilities profile (1-10 scale)
MODEL_CAPABILITIES = {
    "gpt-4o": {
        "technical": 9,
        "creative": 8,
        "reasoning": 9,
        "factual": 8,
        "explanation": 9,
        "speed": 7,
        "cost": 4
    },
    "gpt-4o-mini": {
        "technical": 7,
        "creative": 6,
        "reasoning": 7,
        "factual": 7,
        "explanation": 7,
        "speed": 9,
        "cost": 8
    },
    "claude-3-opus": {
        "technical": 8,
        "creative": 9,
        "reasoning": 9,
        "factual": 8,
        "explanation": 9,
        "speed": 6,
        "cost": 3
    },
    "claude-3-haiku": {
        "technical": 6,
        "creative": 7,
        "reasoning": 7,
        "factual": 7,
        "explanation": 8,
        "speed": 9,
        "cost": 9
    },
    "mistral": {
        "technical": 8,
        "creative": 7,
        "reasoning": 8,
        "factual": 7,
        "explanation": 8,
        "speed": 8,
        "cost": 7
    },
    "cohere": {
        "technical": 7,
        "creative": 6,
        "reasoning": 7,
        "factual": 8,
        "explanation": 7,
        "speed": 8,
        "cost": 8
    },
    "llama": {
        "technical": 7,
        "creative": 6,
        "reasoning": 7,
        "factual": 6,
        "explanation": 7,
        "speed": 7,
        "cost": 10
    }
}

# Dynamic model priority mapping
MODEL_PRIORITY = {
    "fact_simple": ["gpt4", "cohere", "claude3"],
    "explanation": ["gpt4", "claude3", "mistral7b"],
    "technical": ["gpt4", "mistral7b", "claude3"],
    "creative": ["claude3", "gpt4", "mistral7b"],
    "comparison": ["gpt4", "claude3", "mistral7b"],
    "reasoning": ["gpt4", "claude3", "mistral7b"],
    "research": ["claude3", "gpt4", "mistral7b"],
    "general": ["gpt4", "claude3", "mistral7b"]
}

# Function mapping for model processing
MODEL_FUNCTIONS = {
    # Updated mapping to match the actual registered model names
    "gpt4": process_with_gpt4o,  # Maps to process_with_gpt4o
    "gpt-4": process_with_gpt4o,  # Maps to process_with_gpt4o
    "gpt-4o": process_with_gpt4o,  # Original mapping
    "gpt-4o-mini": process_with_gpt4o,
    "claude-3": process_with_claude3,  # Maps to process_with_claude3
    "claude3": process_with_claude3,  # Alternative name mapping
    "claude-3-opus": process_with_claude3,
    "claude-3-haiku": process_with_claude3,
    "mistral": process_with_mistral,
    "mistral7b": process_with_mistral,  # Maps to process_with_mistral
    "cohere": process_with_cohere,
    "llama": process_with_llama2,
    "llama2": process_with_llama2  # Maps to process_with_llama2
}


class AdvancedModelRouter:
    """
    Advanced Model Router for intelligent AI orchestration in Minerva.
    Handles task classification, model selection, parallel execution,
    response ranking, and multi-model blending.
    """
    
    def __init__(self, coordinator: Optional[MultiAICoordinator] = None):
        """
        Initialize the Advanced Model Router.
        
        Args:
            coordinator: Optional MultiAICoordinator instance
        """
        self.coordinator = coordinator or MultiAICoordinator()
        self.available_models = self._get_available_models()
        
        # Update MODEL_FUNCTIONS dictionary with real processors from the coordinator
        self._update_model_functions()
        
        logger.info(f"Advanced Model Router initialized with available models: {self.available_models}")
    
    def _get_available_models(self) -> Set[str]:
        """
        Get the set of available models from the coordinator.
        
        Returns:
            Set of available model names
        """
        # Get available models from coordinator and also include all models in MODEL_FUNCTIONS
        available_models = set()
        
        # Add models from coordinator if they're available
        if hasattr(self.coordinator, 'model_processors') and self.coordinator.model_processors:
            coordinator_models = set(self.coordinator.model_processors.keys())
            available_models.update(coordinator_models)
            logger.info(f"Available models from coordinator: {coordinator_models}")
        else:
            logger.warning("No model processors found in coordinator!")
        
        # Add models from MODEL_FUNCTIONS too, to ensure mappings work
        available_models.update(MODEL_FUNCTIONS.keys())
        
        logger.info(f"Final available models set: {available_models}")
        return available_models
        
    def _update_model_functions(self):
        """
        Update the MODEL_FUNCTIONS dictionary with real processors from the coordinator.
        This ensures that we always have the latest registered models available.
        """
        global MODEL_FUNCTIONS
        
        # Only update if we have access to the coordinator's model processors
        if hasattr(self.coordinator, 'model_processors') and self.coordinator.model_processors:
            # Get the real processor functions from the coordinator
            for model_name, processor_func in self.coordinator.model_processors.items():
                # Update the MODEL_FUNCTIONS dictionary with the real processor
                MODEL_FUNCTIONS[model_name] = processor_func
                logger.info(f"Added {model_name} to MODEL_FUNCTIONS from coordinator")
                
            # Log the updated MODEL_FUNCTIONS keys
            logger.info(f"Updated MODEL_FUNCTIONS with models: {list(MODEL_FUNCTIONS.keys())}")
        else:
            logger.warning("Could not update MODEL_FUNCTIONS: No model processors in coordinator")
    
    def classify_task(self, query_input, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Classify the task type based on query content and complexity.
        Handles both string inputs and existing task_info dictionaries.
        
        Args:
            query_input: The user query string or existing task_info dictionary
            context: Additional context data such as user preferences or patterns
            
        Returns:
            Dictionary with task classification information
        """
        # Import json at function level to avoid circular imports
        import json
        
        # Handle different input types
        if isinstance(query_input, dict):
            logger.info("classify_task received a dictionary, extracting query")
            # Extract the query from task_info dictionary
            query = query_input.get('query', '')
            if not query:
                logger.warning("⚠️ No query found in task_info dictionary, using empty string")
                query = ''
            # Return the dictionary with any missing required fields added
            result = query_input.copy()
            if 'task_type' not in result:
                # Perform classification only if task_type is missing
                task_type = self._classify_query_type(query)
                result['task_type'] = task_type
            if 'complexity' not in result:
                result['complexity'] = estimate_query_complexity(query)
            if 'tags' not in result:
                result['tags'] = get_query_tags(query)
            if 'query' not in result:
                result['query'] = query
            return result
        elif isinstance(query_input, str):
            # 🔧 If query_input is a string, attempt to parse it as JSON
            try:
                parsed_input = json.loads(query_input)
                if isinstance(parsed_input, dict):
                    logger.info("Successfully parsed string input as JSON dictionary")
                    # Recursively call classify_task with the parsed dictionary
                    return self.classify_task(parsed_input, context)
                else:
                    logger.warning(f"⚠️ String parsed as JSON but result is not a dictionary: {type(parsed_input)}")
            except json.JSONDecodeError:
                # Not a JSON string, treat as a regular query
                logger.info(f"classify_task processing query string: '{query_input[:50]}...'" if len(query_input) > 50 else f"classify_task processing query string: '{query_input}'")
                return self._classify_query_type_full(query_input, context)
        else:
            # 🔧 Handle unexpected types
            logger.warning(f"⚠️ classify_task received an unexpected type: {type(query_input)}")
            try:
                query = str(query_input)
                logger.info(f"Converted unexpected type to string: '{query[:50]}...'" if len(query) > 50 else f"Converted unexpected type to string: '{query}'")
                return self._classify_query_type_full(query)
            except Exception as e:
                logger.error(f"⚠️ Error converting query_input to string: {e}")
                # Fallback to an empty dictionary
                return {
                    "task_type": "general",
                    "complexity": 5,
                    "tags": [],
                    "query": ""
                }
    
    def _classify_query_type(self, query: str) -> str:
        """
        Determine just the task type based on query content.
        
        Args:
            query: The user query string
            
        Returns:
            Task type string
        """
        query_lower = query.lower()
        complexity = estimate_query_complexity(query)
        
        # Score each task type based on keyword matches
        task_scores = defaultdict(int)
        
        for task_type, info in TASK_TYPES.items():
            # Score based on keyword presence
            for keyword in info["keywords"]:
                if keyword in query_lower:
                    task_scores[task_type] += 2
            
            # Add points if complexity matches expected range
            if complexity >= info["complexity_threshold"]:
                task_scores[task_type] += 1
        
        # If no clear match, default to general
        if not task_scores or max(task_scores.values()) < 2:
            task_type = "general"
        else:
            # Get the task type with highest score
            task_type = max(task_scores.items(), key=lambda x: x[1])[0]
        
        # For high complexity queries, consider research or reasoning types
        if complexity >= 8 and task_type == "general":
            task_type = "research"
            
        return task_type
        
    def _classify_query_type_full(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Full classification of query, returning all task metadata.
        
        Args:
            query: The user query string
            context: Additional context data such as user preferences or patterns
            
        Returns:
            Dictionary with complete task classification information
        """
        task_type = self._classify_query_type(query)
        complexity = estimate_query_complexity(query)
        tags = get_query_tags(query)
        
        # Score each task type
        task_scores = defaultdict(int)
        query_lower = query.lower()
        
        for task_type_key, info in TASK_TYPES.items():
            # Score based on keyword presence
            for keyword in info["keywords"]:
                if keyword in query_lower:
                    task_scores[task_type_key] += 2
            
            # Add points if complexity matches expected range
            if complexity >= info["complexity_threshold"]:
                task_scores[task_type_key] += 1
        
        result = {
            "task_type": task_type,
            "complexity": complexity,
            "tags": tags,
            "scores": dict(task_scores),
            "query": query  # Always include the original query
        }
        
        # Apply context enhancements if available
        if context:
            result = self._enhance_with_context(result, context)
            
        return result
    
    def _enhance_with_context(self, task_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance the task classification with context from the learning system.
        
        Args:
            task_info: Original task classification information
            context: Context data from the learning system
            
        Returns:
            Enhanced task classification with context-aware adjustments
        """
        logger.info(f"Enhancing task classification with context data: {context.keys() if context else None}")
        
        if not context or not isinstance(context, dict):
            return task_info
        
        # Create a copy to avoid modifying the original
        enhanced = task_info.copy()
        
        # Check if we have user_context in the context data - this is our learning system data
        user_context = context.get('user_context', {})
        if not user_context:
            # If we don't have user_context directly, maybe the context itself is the user_context
            if any(key in context for key in ['preferences', 'patterns', 'topics']):
                user_context = context
        
        # If we still don't have valid user context data, return unmodified task info
        if not user_context:
            return task_info
            
        # Add the user context to the classification for downstream processors
        enhanced['user_context'] = user_context
        
        # Get user preferences and patterns that might influence model selection
        preferences = user_context.get('preferences', [])
        topics = user_context.get('topics', [])
        patterns = user_context.get('patterns', [])
        relevant_memories = user_context.get('relevant_memories', [])
        
        logger.info(f"Found {len(preferences)} preferences, {len(topics)} topics, {len(patterns)} patterns, and {len(relevant_memories)} relevant memories")
        
        # Apply preferences to task classification
        if preferences:
            # Extract model preferences if any exist
            model_prefs = {}
            response_style_prefs = []
            content_depth_prefs = []
            
            for pref in preferences:
                if not isinstance(pref, dict):
                    continue
                    
                # Handle model preferences
                if pref.get('category') == 'model' and pref.get('sentiment') == 'positive':
                    model_name = pref.get('value', '').lower()
                    if model_name in self.available_models:
                        model_prefs[model_name] = pref.get('confidence', 0.8)
                
                # Handle response style preferences (technical, conversational, etc.)
                elif pref.get('category') == 'style':
                    response_style_prefs.append({
                        'style': pref.get('value', ''),
                        'sentiment': pref.get('sentiment', 'positive'),
                        'confidence': pref.get('confidence', 0.7)
                    })
                
                # Handle content depth preferences (detailed, concise, etc.)
                elif pref.get('category') == 'depth':
                    content_depth_prefs.append({
                        'depth': pref.get('value', ''),
                        'sentiment': pref.get('sentiment', 'positive'),
                        'confidence': pref.get('confidence', 0.7)
                    })
            
            # Apply model preferences
            if model_prefs:
                enhanced['model_preferences'] = model_prefs
                logger.info(f"Applied user model preferences: {model_prefs}")
            
            # Apply response style preferences
            if response_style_prefs:
                enhanced['response_style_preferences'] = response_style_prefs
                logger.info(f"Applied response style preferences: {response_style_prefs}")
                
                # Adjust task type based on response style
                for style_pref in response_style_prefs:
                    if style_pref['sentiment'] == 'positive' and style_pref['confidence'] > 0.7:
                        if style_pref['style'].lower() in ['technical', 'detailed', 'academic']:
                            # Boost technical models for users who prefer technical responses
                            if enhanced.get('task_type') == 'general':
                                enhanced['task_type'] = 'technical'
                                logger.info(f"Changed task type to 'technical' based on user preference for {style_pref['style']}")
                        elif style_pref['style'].lower() in ['creative', 'imaginative', 'storytelling']:
                            # Boost creative models for users who prefer creative responses
                            if enhanced.get('task_type') == 'general':
                                enhanced['task_type'] = 'creative'
                                logger.info(f"Changed task type to 'creative' based on user preference for {style_pref['style']}")
            
            # Apply content depth preferences
            if content_depth_prefs:
                enhanced['content_depth_preferences'] = content_depth_prefs
                logger.info(f"Applied content depth preferences: {content_depth_prefs}")
                
                # Adjust complexity based on depth preference
                for depth_pref in content_depth_prefs:
                    if depth_pref['sentiment'] == 'positive' and depth_pref['confidence'] > 0.7:
                        if depth_pref['depth'].lower() in ['detailed', 'comprehensive', 'thorough', 'in-depth']:
                            # Increase complexity for users who prefer detailed responses
                            enhanced['complexity'] = min(10, enhanced.get('complexity', 5) + 2)
                            enhanced['complexity_boosted'] = True
                            logger.info(f"Boosted complexity to {enhanced['complexity']} based on preference for {depth_pref['depth']} content")
                        elif depth_pref['depth'].lower() in ['concise', 'brief', 'short']:
                            # Decrease complexity for users who prefer concise responses
                            enhanced['complexity'] = max(1, enhanced.get('complexity', 5) - 1)
                            enhanced['complexity_reduced'] = True
                            logger.info(f"Reduced complexity to {enhanced['complexity']} based on preference for {depth_pref['depth']} content")
        
        # Apply topic interests to enhance task type and complexity
        if topics:
            # Look for topic matches in the query
            topic_matches = []
            query = enhanced.get('query', '').lower()
            
            for topic_info in topics:
                if not isinstance(topic_info, dict):
                    continue
                    
                topic = topic_info.get('topic', '').lower()
                # Check if topic keyword is present in the query
                if topic and (topic in query or any(term in query for term in topic.split())):
                    topic_matches.append({
                        'topic': topic,
                        'score': topic_info.get('interest_score', 0.5),
                        'category': topic_info.get('category', 'general')
                    })
            
            # If we have topic matches, use them to adjust task classification
            if topic_matches:
                enhanced['topic_matches'] = topic_matches
                logger.info(f"Found {len(topic_matches)} topic matches in query")
                
                # Increase complexity for topics the user is highly interested in
                if any(t.get('score', 0) > 0.8 for t in topic_matches):
                    enhanced['complexity'] = min(10, enhanced.get('complexity', 5) + 1)
                    enhanced['complexity_boosted'] = True
                    logger.info(f"Boosted complexity to {enhanced['complexity']} based on user interests")
                
                # Adjust task type based on matched topics
                for topic_match in topic_matches:
                    if topic_match.get('score', 0) > 0.7:
                        category = topic_match.get('category', '').lower()
                        if category in ['programming', 'code', 'development', 'software']:
                            if 'code' not in enhanced.get('tags', []):
                                enhanced.setdefault('tags', []).append('code')
                            if enhanced.get('task_type') == 'general':
                                enhanced['task_type'] = 'technical'
                                logger.info(f"Changed task type to 'technical' based on user interest in {topic_match['topic']}")
                        elif category in ['math', 'science', 'physics', 'chemistry', 'biology']:
                            if category not in enhanced.get('tags', []):
                                enhanced.setdefault('tags', []).append(category)
                            if enhanced.get('task_type') == 'general':
                                enhanced['task_type'] = 'technical'
                                logger.info(f"Changed task type to 'technical' based on user interest in {topic_match['topic']}")
                        elif category in ['writing', 'creative', 'literature', 'storytelling', 'poetry']:
                            if 'creative_writing' not in enhanced.get('tags', []):
                                enhanced.setdefault('tags', []).append('creative_writing')
                            if enhanced.get('task_type') == 'general':
                                enhanced['task_type'] = 'creative'
                                logger.info(f"Changed task type to 'creative' based on user interest in {topic_match['topic']}")
        
        # Apply learned patterns to enhance model selection
        if patterns:
            # Track recognized patterns
            pattern_matches = []
            query = enhanced.get('query', '').lower()
            
            for pattern in patterns:
                if not isinstance(pattern, dict):
                    continue
                    
                pattern_text = pattern.get('pattern', '').lower()
                # Check if pattern is present in the query
                if pattern_text and pattern_text in query:
                    pattern_matches.append({
                        'pattern': pattern_text,
                        'confidence': pattern.get('confidence', 0.8),
                        'examples': pattern.get('examples', []),
                        'category': pattern.get('category', 'general')
                    })
            
            # If patterns match, add them to the task info
            if pattern_matches:
                enhanced['pattern_matches'] = pattern_matches
                logger.info(f"Found {len(pattern_matches)} pattern matches in query")
                
                # Apply pattern-based adjustments
                for pattern in pattern_matches:
                    # If pattern indicates a specific behavior preference
                    if pattern.get('category') == 'behavior' and pattern.get('confidence', 0) > 0.7:
                        behavior = pattern.get('pattern', '')
                        if behavior in ['step-by-step', 'explanatory', 'tutorial-like']:
                            enhanced.setdefault('behavior_preferences', []).append({'type': behavior, 'confidence': pattern.get('confidence', 0.8)})
                            logger.info(f"Added behavior preference: {behavior}")
                
                # Check if we have examples to see how previous similar queries were handled
                example_models = set()
                for pattern in pattern_matches:
                    for example in pattern.get('examples', []):
                        if isinstance(example, dict) and 'model' in example:
                            example_models.add(example['model'])
                            # If this example has a high satisfaction score, boost its priority
                            if example.get('satisfaction_score', 0) > 0.8:
                                enhanced.setdefault('high_satisfaction_models', set()).add(example['model'])
                
                # Add these to help model selection
                if example_models:
                    enhanced['previous_models'] = list(example_models)
                    logger.info(f"Added previous successful models: {enhanced['previous_models']}")
                    
                    # If we have high satisfaction models, convert from set to list
                    if 'high_satisfaction_models' in enhanced:
                        enhanced['high_satisfaction_models'] = list(enhanced['high_satisfaction_models'])
                        logger.info(f"Added high satisfaction models: {enhanced['high_satisfaction_models']}")
        
        # Apply relevant memories if available
        if relevant_memories:
            enhanced['relevant_memories'] = relevant_memories
            logger.info(f"Added {len(relevant_memories)} relevant memories to context")
            
            # Look for content types in memories to enhance task classification
            code_count = sum(1 for mem in relevant_memories if isinstance(mem, str) and (
                'code' in mem.lower() or 'function' in mem.lower() or 'programming' in mem.lower()
            ))
            math_count = sum(1 for mem in relevant_memories if isinstance(mem, str) and (
                'math' in mem.lower() or 'equation' in mem.lower() or 'formula' in mem.lower()
            ))
            creative_count = sum(1 for mem in relevant_memories if isinstance(mem, str) and (
                'creative' in mem.lower() or 'writing' in mem.lower() or 'story' in mem.lower()
            ))
            
            # Adjust tags based on memory content
            if code_count > 0 and 'code' not in enhanced.get('tags', []):
                enhanced.setdefault('tags', []).append('code')
                logger.info("Added 'code' tag based on relevant memories")
            if math_count > 0 and 'math' not in enhanced.get('tags', []):
                enhanced.setdefault('tags', []).append('math')
                logger.info("Added 'math' tag based on relevant memories")
            if creative_count > 0 and 'creative_writing' not in enhanced.get('tags', []):
                enhanced.setdefault('tags', []).append('creative_writing')
                logger.info("Added 'creative_writing' tag based on relevant memories")
        
        return enhanced
    
    def select_models(self, task_info: Dict[str, Any], max_models: int = 3) -> List[str]:
        """
        Dynamically select the best models for a given task based on its classification.
        Enhanced to utilize context data from the learning system and integrate with failure handler.
        
        Args:
            task_info: Task classification information including context data
            max_models: Maximum number of models to select
            
        Returns:
            List of selected model names prioritized based on context and availability
        """
        task_type = task_info["task_type"]
        complexity = task_info["complexity"]
        tags = task_info["tags"]
        
        logger.info(f"[🔍 DEBUG] Task info: type={task_type}, complexity={complexity}, tags={tags}")
        
        # Extract context-specific data from task_info
        user_preferences = task_info.get('model_preferences', {})
        previous_models = task_info.get('previous_models', [])
        high_satisfaction_models = task_info.get('high_satisfaction_models', [])
        response_style_prefs = task_info.get('response_style_preferences', [])
        behavior_prefs = task_info.get('behavior_preferences', [])
        
        # Log any context-specific data we found
        if user_preferences or previous_models or high_satisfaction_models:
            logger.info(f"[🧠 CONTEXT] Found learning data: {len(user_preferences)} preferences, "
                      f"{len(previous_models)} previous models, {len(high_satisfaction_models)} high satisfaction models")
        
        # NEW: Import and use the model failure handler to detect API issues
        try:
            from web.model_failure_handler import get_failure_handler
            failure_handler = get_failure_handler()
            openai_failing = failure_handler.is_api_failing("openai")
            anthropic_failing = failure_handler.is_api_failing("anthropic")
            mistral_failing = failure_handler.is_api_failing("mistral")
            logger.info(f"[🚫 API STATUS] OpenAI failing: {openai_failing}, Anthropic failing: {anthropic_failing}, Mistral failing: {mistral_failing}")
        except Exception as e:
            logger.warning(f"[⚠️ WARNING] Error loading failure handler: {e}")
            # Default to assuming all APIs are working unless we know otherwise
            openai_failing = False
            anthropic_failing = False
            mistral_failing = False
            
        # Log available models
        logger.info(f"[🚀 MODEL SELECTION] Available models: {self.available_models}")
        
        # CONTEXT-AWARE MODEL SELECTION: Intelligently prioritize models based on user context and API status
        # First, identify local vs API models
        local_models = []
        api_models = []
        
        for model in self.available_models:
            model_lower = model.lower()
            if any(local_id in model_lower for local_id in ["huggingface", "llama", "mistral-7b", "phi", "gpt4all", "falcon"]):
                local_models.append(model)
            else:
                api_models.append(model)
        
        logger.info(f"[📊 MODEL GROUPS] Local models: {local_models}, API models: {api_models}")

        # 1. Build base model priorities based on task type and tags
        base_priorities = self._get_base_model_priorities(task_type, tags, complexity)
        logger.info(f"[🔰 BASE PRIORITY] Models for {task_type}: {base_priorities}")
        
        # 2. Apply user preferences and learning context to model priorities
        context_adjusted_priorities = self._apply_context_preferences(
            base_priorities, 
            user_preferences, 
            previous_models, 
            high_satisfaction_models,
            response_style_prefs,
            behavior_prefs
        )
        logger.info(f"[🧠 CONTEXT ADJUSTED] Model priorities: {context_adjusted_priorities}")
        
        # 3. Apply API reliability adjustments
        if openai_failing or anthropic_failing or mistral_failing:
            # Some APIs are failing, adjust priorities accordingly
            logger.info("[🔄 RELIABILITY ADJUSTMENT] API issues detected, adjusting model priorities")
            
            # Define model groups by provider
            openai_models = [m for m in self.available_models if any(id in m.lower() for id in ["gpt", "gpt-4", "gpt-3", "gpt4"])]
            anthropic_models = [m for m in self.available_models if "claude" in m.lower()]
            mistral_models = [m for m in self.available_models if "mistral" in m.lower() and "7b" not in m.lower()]
            
            # Build adjusted priorities list
            reliability_adjusted = []
            
            # Add local models first as they're most reliable
            local_priority = [m for m in context_adjusted_priorities if m in local_models]
            reliability_adjusted.extend(local_priority)
            
            # Then add API models based on their status
            if not anthropic_failing:
                anthropic_priority = [m for m in context_adjusted_priorities if m in anthropic_models and m not in reliability_adjusted]
                reliability_adjusted.extend(anthropic_priority)
                
            if not mistral_failing:
                mistral_priority = [m for m in context_adjusted_priorities if m in mistral_models and m not in reliability_adjusted]
                reliability_adjusted.extend(mistral_priority)
                
            if not openai_failing:
                openai_priority = [m for m in context_adjusted_priorities if m in openai_models and m not in reliability_adjusted]
                reliability_adjusted.extend(openai_priority)
            
            # Add any remaining models not yet included
            remaining = [m for m in context_adjusted_priorities if m not in reliability_adjusted]
            reliability_adjusted.extend(remaining)
            
            # Set our final priority list to the reliability-adjusted version
            final_priorities = reliability_adjusted
        else:
            # All APIs working, use the context-adjusted priorities
            final_priorities = context_adjusted_priorities
        
        # 4. Ensure we have actual models available
        final_priorities = [m for m in final_priorities if m in self.available_models]
        
        # 5. If we somehow have no models selected, fall back to all available models
        if not final_priorities:
            logger.warning("[⚠️ WARNING] No models selected through priority system, falling back to all available models")
            final_priorities = self.available_models
        
        # 6. Return the top models based on our intelligent selection
        selected_models = final_priorities[:max_models]
        logger.info(f"[🎯 FINAL SELECTION] Selected models: {selected_models}")
        return selected_models
        
    def _get_base_model_priorities(self, task_type: str, tags: List[str], complexity: float) -> List[str]:
        """
        Get base model priorities based on task type, tags, and complexity.
        
        Args:
            task_type: The classified task type (coding, creative, etc.)
            tags: Content tags associated with the query
            complexity: Complexity score of the query (0-1)
            
        Returns:
            List of model names in priority order for this task type
        """
        # Configure task-specific model priorities
        priorities = []
        
        # HIGH COMPLEXITY TECHNICAL TASKS: Programming, math, science, etc.
        if task_type in ["coding", "programming", "technical", "math", "science"] and complexity > 0.65:
            logger.info(f"[🔷 TASK PRIORITY] Complex {task_type} task detected, prioritizing capable technical models")
            # Prioritize models known for technical capabilities
            priorities = [
                # Most capable technical models first
                m for m in self.available_models if any(name in m.lower() for name in 
                  ["gpt-4", "gpt4o", "claude-3-opus", "claude-3-sonnet", "mistral-large"])
            ]
            # Add medium capability models
            priorities.extend([m for m in self.available_models if any(name in m.lower() for name in 
              ["gpt-3.5", "claude-3-haiku", "mistral-medium"]) and m not in priorities])
            # Add remaining models
            priorities.extend([m for m in self.available_models if m not in priorities])
            
        # CREATIVE WRITING: Focus on models with strong language and creative capabilities
        elif task_type in ["creative", "writing", "story", "content"] or "creative" in tags:
            logger.info(f"[🎨 TASK PRIORITY] Creative task detected, prioritizing language-focused models")
            # Prioritize creative/language-focused models
            priorities = [
                # Strong creative models first
                m for m in self.available_models if any(name in m.lower() for name in 
                  ["claude-3", "gpt-4", "gpt4o", "mistral-large"])
            ]
            # Add medium capability models
            priorities.extend([m for m in self.available_models if any(name in m.lower() for name in 
              ["gpt-3.5", "mistral-medium"]) and m not in priorities])
            # Add remaining models
            priorities.extend([m for m in self.available_models if m not in priorities])
            
        # SIMPLE GENERAL TASKS: Favor efficient models for simple tasks
        elif complexity < 0.4:
            logger.info(f"[💬 TASK PRIORITY] Simple {task_type} task detected, prioritizing efficient models")
            # Prioritize faster and more efficient models for simple tasks
            priorities = [
                # Efficient models first
                m for m in self.available_models if any(name in m.lower() for name in 
                  ["gpt-3.5", "claude-3-haiku", "mistral-medium", "huggingface"])
            ]
            # Add more capable models as backup
            priorities.extend([m for m in self.available_models if m not in priorities])
            
        # DEFAULT CASE: Balanced approach for other task types
        else:
            logger.info(f"[⚖️ TASK PRIORITY] Balanced approach for {task_type} task")
            # Create a balanced priority list based on general capabilities
            priorities = [
                # Top-tier models first
                m for m in self.available_models if any(name in m.lower() for name in 
                  ["gpt-4", "gpt4o", "claude-3-opus", "claude-3-sonnet", "mistral-large"])
            ]
            # Medium-tier models next
            priorities.extend([m for m in self.available_models if any(name in m.lower() for name in 
              ["gpt-3.5", "claude-3-haiku", "mistral-medium"]) and m not in priorities])
            # Add remaining models
            priorities.extend([m for m in self.available_models if m not in priorities])
        
        return priorities
        
    def _apply_context_preferences(
            self, 
            base_priorities: List[str],
            user_preferences: Dict[str, float],
            previous_models: List[str],
            high_satisfaction_models: List[str],
            response_style_prefs: List[str],
            behavior_prefs: List[str]
        ) -> List[str]:
        """
        Apply user context and preferences to model selection priorities.
        
        Args:
            base_priorities: Base model priorities determined by task type
            user_preferences: Dictionary of models with user preference scores
            previous_models: List of previously successful models for this user
            high_satisfaction_models: Models with high satisfaction scores
            response_style_prefs: User preferences for response style
            behavior_prefs: User preferences for model behavior
            
        Returns:
            List of model names reprioritized based on user context
        """
        if not base_priorities:
            return []
            
        # Create a working copy of our priorities list
        adjusted_priorities = base_priorities.copy()
        
        # 1. Apply preference scores to create a scoring system
        model_scores = {model: 0 for model in adjusted_priorities}
        
        # 2. Add points for models that appear in user preferences with high scores
        for model, score in user_preferences.items():
            # Look for this model in our available models (case-insensitive)
            matching_models = [m for m in adjusted_priorities if model.lower() in m.lower()]
            # Add a score boost proportional to user preference score
            for matching_model in matching_models:
                model_scores[matching_model] += float(score) * 10  # Scale factor
        
        # 3. Add points for models that have previously given satisfactory responses
        for model in high_satisfaction_models:
            matching_models = [m for m in adjusted_priorities if model.lower() in m.lower()]
            for matching_model in matching_models:
                model_scores[matching_model] += 5  # Fixed boost for satisfaction
        
        # 4. Consider response style preferences
        if response_style_prefs:
            # If user prefers detailed responses, prioritize larger models
            if any(pref in ['detailed', 'comprehensive', 'thorough'] for pref in response_style_prefs):
                for model in adjusted_priorities:
                    if any(large_model in model.lower() for large_model in ['gpt-4', 'claude-3-opus', 'claude-3-sonnet', 'mistral-large']):
                        model_scores[model] += 3
            # If user prefers concise responses, consider more efficient models
            if any(pref in ['concise', 'brief', 'short'] for pref in response_style_prefs):
                for model in adjusted_priorities:
                    if any(concise_model in model.lower() for concise_model in ['gpt-3.5', 'claude-3-haiku', 'mistral-medium']):
                        model_scores[model] += 3
        
        # 5. Consider behavior preferences
        if behavior_prefs:
            # If user prefers creative responses
            if any(pref in ['creative', 'innovative', 'original'] for pref in behavior_prefs):
                for model in adjusted_priorities:
                    if any(creative_model in model.lower() for creative_model in ['claude-3', 'gpt-4']):
                        model_scores[model] += 2
            # If user prefers factually accurate responses
            if any(pref in ['factual', 'accurate', 'precise'] for pref in behavior_prefs):
                for model in adjusted_priorities:
                    if any(factual_model in model.lower() for factual_model in ['gpt-4', 'claude-3-opus']):
                        model_scores[model] += 2
        
        # 6. Sort models by score and create final priority list
        sorted_models = sorted(adjusted_priorities, key=lambda m: model_scores[m], reverse=True)
        
        # Log the scores we calculated
        if user_preferences or high_satisfaction_models or response_style_prefs:
            logger.info(f"[💯 CONTEXT SCORES] Calculated model scores: {model_scores}")
            
        return sorted_models
        
    def _adjust_model_priority(self, base_priority: List[Optional[str]], 
                             user_preferences: Dict[str, float], 
                             previous_models: List[str]) -> List[Optional[str]]:
        """
        Adjust model priority based on user preferences and pattern history.
        
        Args:
            base_priority: Base model priority list
            user_preferences: User model preferences with confidence scores
            previous_models: Models that worked well for similar queries previously
            
        Returns:
            Adjusted model priority list
        """
        # Remove None values from base priority
        base_priority = [m for m in base_priority if m is not None]
        
        # If no user preferences or previous models, return base priority
        if not user_preferences and not previous_models:
            return base_priority
        
        # Create a set of models to prioritize
        priority_models = set()
        
        # Add user preferred models
        for model, confidence in user_preferences.items():
            if confidence > 0.7 and model in self.available_models:  # Only high confidence preferences
                priority_models.add(model)
        
        # Add previously successful models
        for model in previous_models:
            if model in self.available_models:
                priority_models.add(model)
        
        # Convert to list and keep only real models that are available
        priority_models = [m for m in priority_models if m and m in self.available_models]
        
        # If we have priority models, move them to the front of the list
        if priority_models:
            # Remove priority models from base list to avoid duplicates
            remaining_models = [m for m in base_priority if m not in priority_models]
            # Combine priority models with remaining models
            return priority_models + remaining_models
        
        # If no adjustments needed, return the original list
        return base_priority[:max_models]
        
        # If we don't need restructuring or haven't found any models through restructuring,
        # fall back to the intelligent content-based routing system from our existing implementation
        
        # Define adaptive model groups based on current API status
        model_priority_groups = [
            # Start with local models
            ["huggingface-mixtral", "llama", "llama-2", "llama2", "mistral-7b", "phi-2"],
            # Add Hugging Face models
            ["huggingface", "hf", "transformers"],
            # Then consider API models that aren't failing
            [] if anthropic_failing else ["claude-3", "claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
            [] if mistral_failing else ["mistral", "mistral-large", "mistral-medium"],
            # Only try OpenAI if it's not failing (though we're prioritizing other models anyway)
            [] if openai_failing else ["gpt-4", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        ]
        
        # Go through each priority group and check for matches
        for priority_group in model_priority_groups:
            for model in priority_group:
                if model in self.available_models:
                    logger.info(f"[🚀 ADAPTIVE MODEL SELECTION] Using model: {model}")
                    return [model]
        
        # If we couldn't find any of the expected models, use our content-based routing
        # from the original implementation, but with adjusted priorities
        logger.info(f"[🔍 CONTENT ROUTING] Using content-based model selection with adjusted priorities")
        
        # Get base model priority list for this task type
        base_models = MODEL_PRIORITY.get(task_type, MODEL_PRIORITY["general"])
        logger.info(f"[🔍 DEBUG] Base models for {task_type}: {base_models}")
        
        # Apply our content-based prioritization but with knowledge of failing APIs
        candidate_models = []
        
        # Add local models first always
        for model in local_models:
            if model not in candidate_models:
                candidate_models.append(model)
        
        # Then add API models that aren't known to be failing
        for model in base_models:
            if model in self.available_models and model not in candidate_models:
                # Skip OpenAI models if they're failing
                if openai_failing and any(openai_id in model.lower() for 
                    openai_id in ["gpt-4", "gpt-3.5", "gpt4", "gpt4o"]):
                    continue
                # Skip Anthropic models if they're failing
                if anthropic_failing and "claude" in model.lower():
                    continue
                # Skip Mistral models if they're failing
                if mistral_failing and "mistral" in model.lower() and "7b" not in model.lower():
                    continue
                    
                candidate_models.append(model)
        
        # If we somehow ended up with no candidates, use whatever is available
        if not candidate_models and self.available_models:
            candidate_models = list(self.available_models)[:max_models]
            logger.warning(f"[⚠️ FALLBACK] No candidate models found, using any available: {candidate_models}")
        
        # Apply our task-specific refinements from the original implementation
        # For simple queries, use fewer models
        if complexity < 4:
            max_models = min(2, max_models)
        
        # For complex queries, use more models if available
        elif complexity >= 8:
            max_models = max_models
        
        # Optimize for specific query types using our tags
        if "code" in tags:
            # For code, prefer specialized models that are good at code
            for code_model in ["huggingface-mixtral", "mistral-7b", "phi-2"]:
                if code_model in self.available_models and code_model not in candidate_models[:max_models]:
                    candidate_models.insert(0, code_model)
                    break
        
        if "creative" in tags and not anthropic_failing:
            # For creative, prefer Claude if it's not failing
            for claude_model in ["claude-3-opus", "claude-3-sonnet"]:
                if claude_model in self.available_models and claude_model not in candidate_models[:max_models]:
                    candidate_models.insert(0, claude_model)
                    break
        
        # Return the top N models with our intelligent selection
        logger.info(f"[🎯 FINAL SELECTION] Final selected models: {candidate_models[:max_models]}")
        return candidate_models[:max_models]
    
    async def query_models(self, query: str, models: List[str]) -> Dict[str, Any]:
        """
        Run multiple models in parallel and collect their responses.
        
        Args:
            query: The user query string
            models: List of model names to query
            
        Returns:
            Dictionary of model responses
        """
        # ENHANCED DEBUGGING: User requested detailed debug logs
        # Extract query type and complexity for better analysis
        query_type = "general"  # Default type
        complexity = 5  # Default medium complexity
        
        logger.critical(f"🟢 [QUERY MODELS] Query received: {query[:50]}... | Type: {query_type} | Complexity: {complexity}")
        
        # Log all available models in coordinator and model functions
        coordinator_models = list(self.coordinator.model_processors.keys()) if hasattr(self.coordinator, 'model_processors') else []
        model_function_models = list(MODEL_FUNCTIONS.keys())
        available_models_set = set(coordinator_models + model_function_models)
        
        # SYSTEMATIC DEBUGGING: Check if models are actually available
        logger.critical(f"🔍 [AVAILABLE MODELS] {list(available_models_set)}")
        
        if not available_models_set:
            logger.critical("⚠️ [CRITICAL] No models available in either coordinator or MODEL_FUNCTIONS!")
            logger.critical("⚠️ [FALLBACK REASON] Defaulting to local_fallback because no models are registered.")
            return self.process_with_local_fallback(query)
        
        logger.critical(f"🔍 [REQUESTED MODELS] Models to query: {models}")
        
        # Calculate which models are actually available from the requested list
        available_requested_models = [m for m in models if m in available_models_set]
        unavailable_requested_models = [m for m in models if m not in available_models_set]
        
        if unavailable_requested_models:
            logger.critical(f"⚠️ [UNAVAILABLE MODELS] These requested models are not available: {unavailable_requested_models}")
        
        if not available_requested_models:
            logger.critical("⚠️ [CRITICAL] None of the requested models are available!")
            logger.critical("⚠️ [FALLBACK REASON] Defaulting to local_fallback because no requested models are available.")
            return self.process_with_local_fallback(query)
        
        # Select the best model from available models
        best_model = None
        if available_requested_models:
            # Use the first available model as a basic selection strategy
            best_model = available_requested_models[0]
            logger.critical(f"⭐ [SELECTED MODEL] {best_model} (first available from requested models)")
        # 🔍 DETAILED DEBUGGING for model selection and execution
        logger.info(f"[🔍 DEBUG] Starting query_models with message: '{query[:50]}...' and models: {models}")
        
        # Log MODEL_FUNCTIONS to see what's available
        logger.info(f"[🔍 DEBUG] MODEL_FUNCTIONS has {len(MODEL_FUNCTIONS)} models: {list(MODEL_FUNCTIONS.keys())}")
        
        # Log coordinator model processors
        if hasattr(self.coordinator, 'model_processors'):
            logger.info(f"[🔍 DEBUG] Coordinator has {len(self.coordinator.model_processors)} models: {list(self.coordinator.model_processors.keys())}")
            # Log function types
            for model_name, func in self.coordinator.model_processors.items():
                logger.info(f"[🔍 DEBUG] Model {model_name} processor type: {type(func).__name__}, callable: {callable(func)}")
        else:
            logger.warning(f"[⚠️ WARNING] Coordinator has no model_processors attribute!")
        
        tasks = []
        results = {}
        model_status = {}  # Track status for each model
        
        # EMERGENCY FIX: Enhanced debugging for model processors
        logger.critical(f"[🔥 DEBUG CRITICAL] MODEL_FUNCTIONS keys: {list(MODEL_FUNCTIONS.keys())}")
        if hasattr(self.coordinator, 'model_processors'):
            logger.critical(f"[🔥 DEBUG CRITICAL] coordinator.model_processors keys: {list(self.coordinator.model_processors.keys())}")
        
        # CRITICAL DEBUG: Check OpenAI API key configuration
        import os
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            key_format = f"{api_key[:3]}...{api_key[-3:]} (length: {len(api_key)})"
            logger.critical(f"[✅ API KEY] OpenAI API key format: {key_format}")
        else:
            logger.critical("[❌ CRITICAL] OpenAI API key is NOT set in environment")
            logger.critical("[❌ API ERROR] This will cause all OpenAI model calls to fail!")
        
        # Create async tasks for each model
        for model in models:
            model_status[model] = "not_started"
            logger.critical(f"[💡 PROCESSING MODEL] Attempting to process with model: {model}")
            
            # EMERGENCY FIX: Force direct GPT-4 processing
            # This is the most critical path for debugging
            if model in ["gpt4", "gpt-4", "gpt-4o", "gpt-4-turbo"]:
                try:
                    # Import for direct API access
                    import openai
                    import os
                    
                    # Log OpenAI API key status (safely)
                    api_key = os.environ.get("OPENAI_API_KEY")
                    if api_key:
                        key_format = f"{api_key[:3]}...{api_key[-3:]} (length: {len(api_key)})"
                        logger.info(f"[📝 DEBUG] Using OpenAI API key format: {key_format}")
                    else:
                        logger.critical("[❌ CRITICAL] OpenAI API key not found in environment!")
                    
                    # Define direct GPT-4 processing function
                    async def emergency_direct_gpt4(query_text):
                        logger.critical("[🔥 EMERGENCY] Using direct GPT-4 API call")
                        try:
                            from openai import OpenAI
                            client = OpenAI(api_key=api_key)
                            
                            response = client.chat.completions.create(
                                model="gpt-4o",  # Using gpt-4o instead of gpt-4 as it's more widely available
                                messages=[
                                    {"role": "system", "content": "You are a helpful, accurate assistant that provides detailed answers to questions."},
                                    {"role": "user", "content": query_text}
                                ],
                                temperature=0.7,
                                max_tokens=1000
                            )
                            
                            # Extract and return the response text
                            response_text = response.choices[0].message.content
                            logger.critical(f"[✅ EMERGENCY SUCCESS] Direct GPT-4 response received!")
                            return response_text
                        except Exception as api_error:
                            logger.critical(f"[❌ EMERGENCY ERROR] Direct GPT-4 API call failed: {str(api_error)}")
                            import traceback
                            logger.critical(f"[❌ TRACEBACK] {traceback.format_exc()}")
                            raise api_error
                    
                    # Use emergency direct function
                    logger.critical("[💡 STRATEGY] Using emergency direct GPT-4 API call")
                    model_status[model] = "emergency_direct_gpt4"
                    tasks.append(asyncio.create_task(emergency_direct_gpt4(query)))
                    continue
                    
                except Exception as setup_error:
                    logger.critical(f"[❌ CRITICAL ERROR] Failed to set up emergency GPT-4 call: {str(setup_error)}")
                    # Continue to standard processing paths
            
            # Standard processing paths
            # First check if we can get the processor directly from the coordinator
            if (hasattr(self.coordinator, 'model_processors') and 
                model in self.coordinator.model_processors):
                # Use the real processor registered with the coordinator
                process_func = self.coordinator.model_processors[model]
                logger.critical(f"[✅ SUCCESS] Using processor function from coordinator for {model}: {process_func.__name__ if hasattr(process_func, '__name__') else 'unnamed'}")
                model_status[model] = "using_coordinator"
                tasks.append(asyncio.create_task(process_func(query)))
            elif model in MODEL_FUNCTIONS:
                # Fallback to MODEL_FUNCTIONS if necessary
                process_func = MODEL_FUNCTIONS[model]
                logger.critical(f"[✅ SUCCESS] Using processor function from MODEL_FUNCTIONS for {model}: {process_func.__name__ if hasattr(process_func, '__name__') else 'unnamed'}")
                model_status[model] = "using_model_functions"
                tasks.append(asyncio.create_task(process_func(query)))
            else:
                logger.critical(f"[⚠️ WARNING] No processor function found for model: {model}")
                model_status[model] = "processor_not_found"
                # Try to use process_with_gpt4o as a last resort if available
                if "gpt4" in MODEL_FUNCTIONS:
                    logger.critical(f"[ℹ️ INFO] Falling back to gpt4 for {model}")
                    process_func = MODEL_FUNCTIONS["gpt4"]
                    model_status[model] = "fallback_to_gpt4"
                    tasks.append(asyncio.create_task(process_func(query)))
                elif "claude-3" in MODEL_FUNCTIONS:
                    logger.critical(f"[ℹ️ INFO] Falling back to claude-3 for {model}")
                    process_func = MODEL_FUNCTIONS["claude-3"]
                    model_status[model] = "fallback_to_claude3"
                    tasks.append(asyncio.create_task(process_func(query)))
                else:
                    logger.critical(f"[❌ ERROR] No available fallback processor for {model}!")
                    model_status[model] = "no_fallback_available"
        
        # 🔍 LOG model selection summary
        logger.critical(f"[🔍 DEBUG] Model status summary: {model_status}")
        logger.critical(f"[🔍 DEBUG] Created {len(tasks)} tasks for {len(models)} requested models")
        
        # Enhanced logging of which models are actually being processed
        if tasks:
            logger.critical(f"⭐ [SELECTED MODELS] Using {len(tasks)} models for processing: {list(model_status.keys())}")
            logger.critical(f"🚀 [PROCESSING] Starting {len(tasks)} model tasks")
        else:
            logger.critical(f"⚠️ [MODEL SELECTION FAILED] No models selected from: {models}")
            logger.critical("⚠️ [FALLBACK REASON] Defaulting to local_fallback because no models could be executed.")
            return self.process_with_local_fallback(query)
        
        # Run all tasks in parallel if we have any
        if tasks:
            logger.critical(f"🚀 [PROCESSING] Executing {len(tasks)} model tasks in parallel for models: {list(model_status.keys())}")
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Initialize quota error detection
            openai_quota_error = False
            
            # Collect results, handling any exceptions
            for model, response in zip(models, responses):
                if isinstance(response, Exception):
                    logger.error(f"[❌ ERROR] Model {model} failed: {str(response)}")
                    logger.error(f"[❌ ERROR] Exception type: {type(response).__name__}")
                    logger.error(f"[❌ ERROR] Exception traceback: {traceback.format_exc()}")
                    results[model] = f"Error: {str(response)}"
                    model_status[model] += ", execution_failed"
                else:
                    logger.critical(f"[✅ SUCCESS] Model {model} responded successfully")
                    if isinstance(response, str):
                        logger.critical(f"[🔍 DEBUG] Response from {model} (first 100 chars): {response[:100]}...")
                    else:
                        logger.critical(f"[🔍 DEBUG] Response from {model} type: {type(response).__name__}")
                    results[model] = response
                    model_status[model] += ", execution_succeeded"
        else:
            logger.error(f"[❌ ERROR] No tasks created - could not find processors for any requested models: {models}!")
        
        # EMERGENCY FIX: More aggressive error logging before fallback
        if not results:
            logger.critical("[❌ CRITICAL ERROR] No results collected from any models! Debugging info:")
            logger.critical(f"[❌ DEBUG] Requested models: {models}")
            logger.critical(f"[❌ DEBUG] Tasks created: {len(tasks)}")
            logger.critical(f"[❌ DEBUG] Model status: {model_status}")
        elif all(isinstance(r, str) and r.startswith("Error") for r in results.values()):
            logger.critical("[❌ CRITICAL ERROR] All models returned errors! Errors:")
            for model_name, error_response in results.items():
                logger.critical(f"[❌ MODEL ERROR] {model_name}: {error_response}")
            
        # Try alternative models if OpenAI error is detected (quota OR api key issues)
        if (openai_quota_error or openai_missing_key_error) and all(isinstance(r, str) and r.startswith("Error") for r in results.values()):
            logger.critical("[🛠️ ADAPTIVE ROUTING] OpenAI quota exceeded, trying alternative models")
            
            # Try Claude or Mistral as alternatives if they weren't in the original model list
            alternative_models = []
            # Check if we have Claude models available
            if "claude-3-opus" in self.available_models and "claude-3-opus" not in models:
                alternative_models.append("claude-3-opus")
            elif "claude-3-sonnet" in self.available_models and "claude-3-sonnet" not in models:
                alternative_models.append("claude-3-sonnet")
            # Or try Mistral as fallback
            elif "mistral" in self.available_models and "mistral" not in models:
                alternative_models.append("mistral")
            
            if alternative_models:
                logger.critical(f"[🔄 ALTERNATE MODELS] Trying alternative models: {alternative_models}")
                
                # Create tasks for alternative models
                alt_tasks = []
                alt_model_status = {}
                
                for alt_model in alternative_models:
                    if alt_model in MODEL_FUNCTIONS:
                        process_func = MODEL_FUNCTIONS[alt_model]
                        alt_model_status[alt_model] = "started_as_alternative"
                        alt_tasks.append(asyncio.create_task(process_func(query)))
                
                if alt_tasks:
                    logger.critical(f"[🚀 PROCESSING] Executing {len(alt_tasks)} alternative model tasks")
                    alt_responses = await asyncio.gather(*alt_tasks, return_exceptions=True)
                    
                    # Process alternative responses
                    for alt_model, alt_response in zip(alternative_models, alt_responses):
                        if isinstance(alt_response, Exception):
                            logger.error(f"[❌ ERROR] Alternative model {alt_model} failed: {str(alt_response)}")
                            alt_model_status[alt_model] = "alternative_failed"
                        else:
                            logger.critical(f"[✅ SUCCESS] Alternative model {alt_model} responded successfully")
                            results[alt_model] = alt_response
                            model_status[alt_model] = "alternative_succeeded"
                            # If we got a successful alternative response, return early
                            if not isinstance(alt_response, str) or not alt_response.startswith("Error"):
                                logger.critical(f"[✅ SUCCESS] Using alternative model {alt_model} due to OpenAI quota error")
                                return {
                                    "responses": results,
                                    "status": model_status,
                                    "selected": alt_model
                                }
        
        # Add a fallback local model response if no valid responses were collected
        if not results or all(isinstance(r, str) and r.startswith("Error") for r in results.values()):
            logger.critical("[⚠️ CRITICAL WARNING] No models responded successfully. Using local fallback.")
            logger.critical(f"[❌ ERROR] Model status summary at failure point: {model_status}")
            logger.critical("⚠️ [FALLBACK REASON] Defaulting to local_fallback because all models failed or returned errors.")
            
            # EMERGENCY FIX: Skip direct API call if we already know there's a quota error or API key issue
            if not (openai_quota_error or openai_missing_key_error):
                try:
                    import os
                    from openai import OpenAI
                    api_key = os.environ.get("OPENAI_API_KEY")
                    
                    if api_key:
                        logger.critical("[💡 LAST RESORT] Attempting final direct GPT-4 API call before fallback")
                        client = OpenAI(api_key=api_key)
                        response = client.chat.completions.create(
                            model="gpt-4o",  # Using gpt-4o instead of gpt-4 as it's more widely available
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant."},
                                {"role": "user", "content": query}
                            ],
                            temperature=0.7
                        )
                        response_text = response.choices[0].message.content
                        
                        if response_text:
                            logger.critical("[✅ SUCCESS] Last resort direct API call succeeded!")
                            results["gpt4_last_resort"] = response_text
                            model_status["gpt4_last_resort"] = "direct_api_last_resort_success"
                            # Skip the fallback by returning early
                            return {
                                "responses": results,
                                "status": model_status,
                                "selected": "gpt4_last_resort"
                            }
                except Exception as last_error:
                    logger.critical(f"[❌ ERROR] Last resort API call failed: {str(last_error)}")
            
            # Log detailed info about what went wrong
            if not results:
                logger.error("[❌ ERROR] No results collected at all - model tasks failed to start or complete")
            else:
                error_messages = {model: resp for model, resp in results.items() if isinstance(resp, str) and resp.startswith("Error")}
                logger.error(f"[❌ ERROR] All responses contained errors: {error_messages}")
            
            # Create a more informative fallback response about what happened
            logger.critical("[❌ CRITICAL WARNING] CREATING LOCAL FALLBACK RESPONSE - AFTER TRYING ALL ALTERNATIVES")
            logger.critical(f"[❌ DEBUG] MODEL_FUNCTIONS has {len(MODEL_FUNCTIONS)} models: {list(MODEL_FUNCTIONS.keys())}")
            logger.critical(f"[❌ DEBUG] coordinator has {len(coordinator_models)} models: {coordinator_models}")
            logger.critical(f"[❌ DEBUG] Original requested models: {models}")
            logger.critical(f"[❌ DEBUG] Available models: {list(available_models_set)}")
            
            # Create a more specific fallback message based on what we found
            fallback_reason = "All models failed or returned errors"
            fallback_message = ""
            
            if openai_missing_key_error:
                fallback_reason = "OpenAI API key missing or invalid, and alternative models also failed"
                fallback_message = (f"I received your message: '{query}'. I attempted to process it using several AI models, "
                                   f"but your OpenAI API key appears to be missing or invalid. Please add a valid OpenAI API key "
                                   f"in your environment variables or .env file to use external AI models.")
            elif openai_quota_error:
                fallback_reason = "OpenAI API quota exceeded, and alternative models also failed"
                fallback_message = (f"I received your message: '{query}'. I attempted to process it using several AI models, "
                                   f"but encountered an OpenAI quota limit error, and alternative models were unavailable or failed. "
                                   f"Please check your OpenAI API quota in your account settings, or try again later.")
            else:
                fallback_message = (f"I received your message: '{query}'. I'm currently running with limited capabilities. "
                                   f"To use the full capabilities of the advanced AI orchestration system, please ensure your API keys "
                                   f"are configured correctly in the settings. For now, I'll assist you to the best of my ability.")
            
            results["local_fallback"] = {
                "response": fallback_message,
                "model": "local_fallback",
                "confidence": 0.8,
                "latency": 0.1,
                "tokens": len(query.split()),
                "error": None,
                "fallback_reason": fallback_reason,
                "model_status": model_status
            }
            logger.critical("[❌ CRITICAL] Added local_fallback response as no valid model responses were received")
        
        return results
    
    def rank_and_select_best(self, responses: Dict[str, Any], task_info: Dict[str, Any]) -> Tuple[str, Any]:
        """
        Rank responses and select the best one based on quality metrics.
        
        Args:
            responses: Dictionary of model responses
            task_info: Task classification information
            
        Returns:
            Tuple of (best_model_name, best_response)
        """
        # Add detailed logging
        logger.info(f"🔍 DEBUG: Starting rank_and_select_best with {len(responses)} responses")
        logger.info(f"🔍 DEBUG: Available models: {list(responses.keys())}")
        logger.info(f"🔍 DEBUG: Response types: {[(k, type(v).__name__) for k, v in responses.items()]}")
        
        # Filter out error responses
        valid_responses = {k: v for k, v in responses.items() if not isinstance(v, str) or not v.startswith("Error")}
        
        logger.info(f"🔍 DEBUG: After filtering, {len(valid_responses)} valid responses remain")
        logger.info(f"🔍 DEBUG: Valid models: {list(valid_responses.keys())}")
        
        if not valid_responses:
            logger.error("⚠️ No responses available for ranking.")
            return "unknown", "No valid responses received"
        
        try:
            # Use ensemble validator to rank responses
            from web.ensemble_validator import ensemble_validator
            logger.info(f"🔍 DEBUG: Calling ensemble_validator.rank_responses")
            
            # Format the task_info appropriately for rank_responses
            task_query = ''
            query_type = 'general'
            
            # Handle different task_info formats
            if isinstance(task_info, dict):
                task_query = task_info.get('query', '')
                query_type = task_info.get('task_type', 'general')
                
                # Also check for query_type directly
                if 'query_type' in task_info:
                    explicit_query_type = task_info.get('query_type', '').lower()
                    if explicit_query_type in ['factual', 'fact', 'knowledge']:
                        query_type = 'factual'
                        logger.info(f"🚨 Setting query_type to 'factual' from explicit query_type: {explicit_query_type}")
                        
            elif isinstance(task_info, str):
                task_query = task_info
                
            logger.info(f"🔍 DEBUG: Query type for ranking: {query_type}")
            
            # Identify factual queries with a more robust detection method
            is_factual_query = False
            if query_type in ["factual", "fact_simple"]:
                is_factual_query = True
                logger.info(f"🔎 Detected factual query type from task_info: {query_type}")
            else:
                # Additional patterns to detect factual queries
                factual_patterns = [
                    r'\bwhat is\b', r'\bwho is\b', r'\bwhen did\b', r'\bwhere is\b',
                    r'\bhow many\b', r'\bcapital of\b', r'\blargest\b', r'\bsmallest\b',
                    r'\bpopulation of\b', r'\bin what year\b', r'\bwho was\b'
                ]
                if any(re.search(pattern, task_query.lower()) for pattern in factual_patterns):
                    is_factual_query = True
                    logger.info(f"🔍 Detected factual query from pattern matching: '{task_query[:50]}...'")
                    
            # 🚨 CRITICAL: Force GPT-4o/GPT-4o-mini for factual queries if available
            if is_factual_query:
                logger.info(f"🚨 FACTUAL QUERY DETECTED: '{task_query[:50]}...'")
                # Try GPT-4o first, then GPT-4o-mini, then GPT-4
                if "gpt-4o" in valid_responses:
                    logger.info(f"🚨 FORCING GPT-4o for factual query")
                    return "gpt-4o", valid_responses["gpt-4o"]
                elif "gpt-4o-mini" in valid_responses:
                    logger.info(f"🚨 FORCING GPT-4o-mini for factual query")
                    return "gpt-4o-mini", valid_responses["gpt-4o-mini"]
                elif "gpt-4" in valid_responses:
                    logger.info(f"🚨 FORCING GPT-4 for factual query")
                    return "gpt-4", valid_responses["gpt-4"]
                
            # Get the ranking result for non-factual queries
            ranked = ensemble_validator.rank_responses(valid_responses, task_query, query_type=query_type)
            logger.info(f"🔍 DEBUG: Received ranking result type: {type(ranked).__name__}")
            logger.info(f"🔍 DEBUG: Ranking result: {ranked}")
            
            if not ranked:
                logger.error("⚠️ Ranking failed: No models were selected.")
                # Fallback to first available model
                model_key = list(valid_responses.keys())[0]
                logger.info(f"🔍 DEBUG: Falling back to first valid model: {model_key}")
                return model_key, valid_responses[model_key]
            
            # Handle different return types from rank_responses
            if isinstance(ranked, list):
                if ranked:
                    logger.info(f"🔍 DEBUG: Using list format ranking, best model: {ranked[0][0]}")
                    best_model, best_response = ranked[0]
                else:
                    logger.error("⚠️ Ranked list is empty, falling back to first valid response")
                    model_key = list(valid_responses.keys())[0]
                    return model_key, valid_responses[model_key]
            elif isinstance(ranked, dict):
                # Handle both legacy 'rankings' key and new 'detailed_rankings' key
                if 'rankings' in ranked and ranked['rankings']:
                    logger.info(f"🔍 DEBUG: Using dict format with rankings key")
                    best_model = ranked['rankings'][0]['model']
                    best_response = valid_responses.get(best_model, "Response not found")
                    logger.info(f"🔍 DEBUG: Best model from dict rankings: {best_model}")
                elif 'detailed_rankings' in ranked and ranked['detailed_rankings']:
                    # Convert detailed_rankings to rankings format for compatibility
                    ranked['rankings'] = ranked['detailed_rankings']
                    logger.info(f"🔍 DEBUG: Using dict format with detailed_rankings key")
                    best_model = ranked['rankings'][0]['model']
                    best_response = valid_responses.get(best_model, "Response not found")
                    logger.info(f"🔍 DEBUG: Best model from dict rankings: {best_model}")
                else:
                    logger.error("⚠️ Ranked dict has no rankings, falling back to first valid response")
                    model_key = list(valid_responses.keys())[0]
                    return model_key, valid_responses[model_key]            
            else:
                logger.error(f"⚠️ Unexpected ranking type: {type(ranked).__name__}, falling back to first valid response")
                model_key = list(valid_responses.keys())[0]
                return model_key, valid_responses[model_key]
            
            logger.info(f"🔍 DEBUG: Selected best model: {best_model}")
            return best_model, best_response
            
        except Exception as e:
            logger.error(f"❌ Error during ranking: {e}")
            logger.exception("Detailed ranking error:")
            
            # Fallback to first available model
            if valid_responses:
                model_key = list(valid_responses.keys())[0]
                return model_key, valid_responses[model_key]
            return "unknown", "Error during ranking process"
    
    def should_blend_responses(self, responses: Dict[str, Any], task_info: Dict[str, Any]) -> bool:
        """
        Determine if responses should be blended based on task type and complexity.
        
        Args:
            responses: Dictionary of model responses
            task_info: Task classification information
            
        Returns:
            Boolean indicating whether to blend responses
        """
        # Only blend if we have multiple valid responses
        valid_responses = {k: v for k, v in responses.items() if not isinstance(v, str) or not v.startswith("Error")}
        
        if len(valid_responses) < 2:
            return False
        
        task_type = task_info["task_type"]
        complexity = task_info["complexity"]
        
        # Always blend for comparison tasks
        if task_type == "comparison":
            return True
        
        # Blend for complex research or reasoning tasks
        if task_type in ["research", "reasoning"] and complexity >= 7:
            return True
        
        # Blend for technical tasks if complexity is high
        if task_type == "technical" and complexity >= 8:
            return True
        
        # For other task types, blend if complexity is very high
        return complexity >= 9
    
    def blend_responses(self, responses: Dict[str, Any], task_info: Dict[str, Any]) -> str:
        """
        Blend responses from multiple models if necessary.
        
        Args:
            responses: Dictionary of model responses
            task_info: Task classification information
            
        Returns:
            Blended response string
        """
        # Filter out error responses
        valid_responses = {k: v for k, v in responses.items() if not isinstance(v, str) or not v.startswith("Error")}
        
        if len(valid_responses) <= 1:
            return list(valid_responses.values())[0] if valid_responses else "No valid responses received"
        
        # Use the ensemble validator's blend_responses method with task info context
        return ensemble_validator.blend_responses(valid_responses, task_info)
    
    async def process_query(self, query: str, override_models: List[str] = None, task_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query using the intelligent model routing system.
        
        Args:
            query: The user query string
            override_models: Optional list of models to use, bypassing the selection logic
            task_info: Optional pre-classified task information including query_type
            
        Returns:
            Dictionary with processing results
        """
        # 1. Classify the task (or use provided task_info)
        if task_info is None:
            task_info = self.classify_task(query)
        else:
            # If task_info is provided but doesn't have all required fields, merge with classification
            base_task_info = self.classify_task(query)
            
            # Preserve the explicitly provided query_type if it exists
            query_type = task_info.get('query_type')
            
            # Update task_info with base classification while preserving query_type
            task_info = {**base_task_info, **task_info}
            
            # If a query_type was provided, update task_type to match
            if query_type and query_type in ["factual", "knowledge", "fact"]:
                task_info['task_type'] = "fact_simple"
                logger.info(f"Setting task type to fact_simple based on provided query_type: {query_type}")
            
        logger.info(f"Task classified as: {task_info['task_type']} with complexity {task_info['complexity']}")
        
        # 2. Select models (or use override)
        selected_models = override_models or self.select_models(task_info)
        logger.info(f"Selected models: {selected_models}")
        
        # 3. Query models in parallel
        responses = await self.query_models(query, selected_models)
        
        if not responses:
            return {
                "error": "No valid responses received",
                "task_info": task_info,
                "models_used": []
            }
        
        # 4. Rank responses and get the best one
        # First get detailed rankings from the ensemble validator
        from web.ensemble_validator import ensemble_validator
        
        # Format task_info for ranking
        task_query = task_info.get('query', query)
        task_type = task_info.get('task_type', 'general')
        
        # Get detailed rankings for response metadata
        ranking_result = ensemble_validator.rank_responses(responses, task_query, query_type=task_type)
        detailed_rankings = ranking_result.get('rankings', [])
        
        # Get best model and response
        best_model, best_response = self.rank_and_select_best(responses, task_info)
        
        # 5. Decide whether to blend responses
        should_blend = self.should_blend_responses(responses, task_info)
        
        # 6. Generate final response (blended or best single model)
        if should_blend:
            final_response = self.blend_responses(responses, task_info)
            response_source = "blended"
        else:
            final_response = best_response
            response_source = best_model
        
        # 7. Return comprehensive result with detailed model info
        return {
            "task_info": task_info,
            "models_used": list(responses.keys()),
            "best_model": best_model,
            "response_source": response_source,
            "blended": should_blend,
            "final_response": final_response,
            "rankings": detailed_rankings,  # Include detailed model rankings with scores and reasoning
            "ranking_metadata": {
                "capability_scores": ranking_result.get('capability_scores', {}),
                "confidence_scores": ranking_result.get('confidence_scores', {}),
                "voting_scores": ranking_result.get('voting_scores', {}),
                "consensus_scores": ranking_result.get('consensus_scores', {})
            }
        }


# Create a singleton instance for use throughout the application
router = AdvancedModelRouter()

# Main entry point function
async def route_and_process_query(query: str, override_models: List[str] = None, query_type: str = None) -> Dict[str, Any]:
    """
    Main entry point for processing queries with the advanced model router.
    
    Args:
        query: The user query string
        override_models: Optional list of specific models to use
        query_type: Optional query type for better model selection (factual, technical, etc.)
        
    Returns:
        Result dictionary from the router
    """
    # Create task_info dictionary if query_type is provided
    task_info = {"query_type": query_type} if query_type else None
    
    # Pass task_info to the router's process_query method
    logger.info(f"Routing query with type: {query_type}")
    return await router.process_query(query, override_models, task_info=task_info)
