#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hierarchical Think Tank Workflow

This module implements a hierarchical AI collaboration workflow for Minerva's Think Tank mode.
It creates a specialized team approach where specific models are assigned leadership roles
based on query types, with collaborative input from other models, and final review by a "Boss AI".

The workflow consists of five steps:
1. Query Analysis - Determine the nature of the query
2. Lead Model Assignment - Assign a specialist model as the lead
3. Think Tank Collaboration - Get input from all models with weighted influence
4. Response Structuring - Optimize the response for readability and clarity
5. Boss AI Validation - Final review and refinement of the response

This approach ensures higher quality responses that leverage the strengths of each model
while maintaining a cohesive structure and preventing generic AI outputs.
"""

import logging
import re
import json
from typing import Dict, List, Any, Tuple, Optional, Union, Callable
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import required components
from web.ensemble_validator import ensemble_validator
from web.advanced_model_router import router as model_router

# Query type definitions with lead model assignments
QUERY_TYPE_LEADS = {
    "factual": ["gpt-4o", "gpt-4", "claude-3-opus"],  # Factual queries prioritize GPT-4o
    "creative": ["claude-3-opus", "claude-3-sonnet", "gpt-4o"],  # Creative queries prioritize Claude-3 Opus
    "technical": ["mistral", "mistral7b", "gpt-4o"],  # Technical queries prioritize Mistral
    "business": ["gpt-4o", "cohere", "claude-3-opus"],  # Business queries prioritize GPT-4o
    "general": ["gpt-4o", "claude-3-opus", "gpt-4"]  # General queries default to GPT-4o
}

# Boss AI models for final validation (models good at summarization and clarity)
BOSS_AI_MODELS = ["gpt-4o", "claude-3-opus", "gpt-4"]

# Patterns for query type detection (extending the existing patterns)
QUERY_TYPE_PATTERNS = {
    "factual": [
        r'\bwhat is\b', r'\bwho is\b', r'\bwhen did\b', r'\bwhere is\b',
        r'\bhow many\b', r'\bcapital of\b', r'\blargest\b', r'\bsmallest\b',
        r'\bpopulation of\b', r'\bin what year\b', r'\bwho was\b', r'\bfact\b',
        r'\bhistory of\b', r'\bdefinition of\b', r'\bmeaning of\b'
    ],
    "creative": [
        r'\bwrite a\b', r'\bcreate a\b', r'\bgenerate a\b', r'\bcompose a\b',
        r'\bstory\b', r'\bpoem\b', r'\bsong\b', r'\bnarrative\b', r'\bessay\b',
        r'\bcreative\b', r'\bfiction\b', r'\bimagine\b', r'\bdesign\b'
    ],
    "technical": [
        r'\bcode\b', r'\bprogram\b', r'\bfunction\b', r'\balgorithm\b',
        r'\bdebug\b', r'\bfix\b', r'\boptimize\b', r'\bimprove\b',
        r'\bimplementation\b', r'\barchitecture\b', r'\bframework\b',
        r'\btechnical\b', r'\bengineering\b', r'\bmath\b', r'\bcalculate\b'
    ],
    "business": [
        r'\bbusiness\b', r'\bstrategy\b', r'\bmarket\b', r'\bcompetition\b',
        r'\bindustry\b', r'\bproduct\b', r'\bservice\b', r'\bcustomer\b',
        r'\bvalue\b', r'\bsales\b', r'\bmarketing\b', r'\bfinance\b',
        r'\beconomic\b', r'\bforecast\b', r'\btrend\b', r'\banalysis\b'
    ]
}

# Generic AI filler phrases to remove or reduce in responses
GENERIC_AI_PHRASES = [
    r"As an AI(.*?)I",
    r"I'm an AI(.*?)and",
    r"As a language model(.*?)I",
    r"I don't have(.*?)access to",
    r"I don't have(.*?)ability to",
    r"I cannot(.*?)provide",
    r"I'm not able to",
    r"I cannot browse",
    r"Here's what I know about",
    r"Based on my knowledge",
    r"I hope this helps",
    r"I hope this information is useful",
    r"Let me know if you have any other questions",
    r"Thank you for your question",
    r"I'd be happy to help",
    r"In conclusion"
]


class HierarchicalWorkflow:
    """
    Implements the hierarchical workflow for Think Tank processing.
    """
    
    def __init__(self):
        """Initialize the hierarchical workflow handler."""
        self.validator = ensemble_validator
        self.router = model_router
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Step 1: Analyze the query to determine its type and required expertise.
        
        Args:
            query: The user query string
            
        Returns:
            Dictionary with query analysis information
        """
        # Start with basic task classification from the router
        task_info = self.router.classify_task(query)
        
        # Additional pattern-based detection for query types
        query_lower = query.lower()
        detected_types = []
        
        for query_type, patterns in QUERY_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    detected_types.append(query_type)
                    break
        
        # Assign the primary query type
        primary_type = "general"  # Default
        if detected_types:
            # Count occurrences of each type
            type_counts = {}
            for t in detected_types:
                type_counts[t] = type_counts.get(t, 0) + 1
            
            # Get the most frequent type
            primary_type = max(type_counts.items(), key=lambda x: x[1])[0]
        
        # Update task_info with our enhanced query type analysis
        task_info["query_type"] = primary_type
        task_info["detected_types"] = detected_types
        
        logger.info(f"Query analysis: Primary type = {primary_type}, Detected types = {detected_types}")
        return task_info
    
    def assign_lead_model(self, task_info: Dict[str, Any], available_models: List[str]) -> str:
        """
        Step 2: Assign a lead model based on query type and available models.
        
        Args:
            task_info: Query analysis information
            available_models: List of available model names
            
        Returns:
            Name of the assigned lead model
        """
        query_type = task_info.get("query_type", "general")
        
        # Get ordered list of potential lead models for this query type
        lead_candidates = QUERY_TYPE_LEADS.get(query_type, QUERY_TYPE_LEADS["general"])
        
        # Find the first available candidate
        for model in lead_candidates:
            if model in available_models:
                logger.info(f"Assigned lead model: {model} for query type: {query_type}")
                return model
        
        # If no preferred model is available, choose the first available model
        if available_models:
            default_model = available_models[0]
            logger.warning(f"No preferred lead model available. Using {default_model} as fallback.")
            return default_model
            
        logger.error("No models available to assign as lead!")
        return None
    
    def assign_boss_model(self, available_models: List[str]) -> str:
        """
        Assign a boss model for final validation from available models.
        
        Args:
            available_models: List of available model names
            
        Returns:
            Name of the assigned boss model
        """
        # Find the first available boss model
        for model in BOSS_AI_MODELS:
            if model in available_models:
                logger.info(f"Assigned boss model: {model}")
                return model
        
        # If no preferred boss model is available, choose the first available model
        if available_models:
            default_model = available_models[0]
            logger.warning(f"No preferred boss model available. Using {default_model} as fallback.")
            return default_model
            
        logger.error("No models available to assign as boss!")
        return None
    
    def weight_responses(self, responses: Dict[str, Any], lead_model: str) -> Dict[str, float]:
        """
        Step 3: Weight responses, giving more influence to the lead model.
        
        Args:
            responses: Dictionary of model responses
            lead_model: Name of the lead model
            
        Returns:
            Dictionary mapping model names to weight multipliers
        """
        # Default weight is 1.0
        weights = {model: 1.0 for model in responses}
        
        # Increase weight for lead model (50% boost)
        if lead_model in weights:
            weights[lead_model] = 1.5
            
        return weights
    
    def structure_response(self, response: str) -> str:
        """
        Step 4: Structure and optimize the response for readability.
        
        Args:
            response: Raw response text
            
        Returns:
            Structured and optimized response
        """
        # Remove generic AI phrases
        for phrase in GENERIC_AI_PHRASES:
            response = re.sub(phrase, "", response, flags=re.IGNORECASE)
        
        # Cleanup redundant spacing
        response = re.sub(r'\n\s*\n', '\n\n', response)
        response = re.sub(r' +', ' ', response)
        
        # Ensure there are proper paragraph breaks for readability
        if len(response) > 200 and response.count('\n\n') < 2:
            # Try to break into paragraphs at sentence boundaries if they don't exist
            sentences = re.split(r'(?<=[.!?])\s+', response)
            if len(sentences) > 5:
                paragraphs = []
                current_paragraph = []
                for i, sentence in enumerate(sentences):
                    current_paragraph.append(sentence)
                    # Create paragraph breaks every 2-3 sentences or at topic changes
                    if i % 3 == 2 or (len(current_paragraph) >= 2 and 
                                      (sentence.startswith("However") or 
                                       sentence.startswith("Furthermore") or
                                       sentence.startswith("In addition"))):
                        paragraphs.append(" ".join(current_paragraph))
                        current_paragraph = []
                
                # Add any remaining sentences
                if current_paragraph:
                    paragraphs.append(" ".join(current_paragraph))
                    
                response = "\n\n".join(paragraphs)
        
        return response.strip()
    
    async def boss_validation(self, response: str, query: str, boss_model: str) -> str:
        """
        Step 5: Perform final validation and refinement of the response.
        
        Args:
            response: Structured response from Step 4
            query: Original user query
            boss_model: Boss AI model to use
            
        Returns:
            Final validated and refined response
        """
        # Create a prompt for the boss model to refine the response
        boss_prompt = f"""
        Review and refine the following response to the user query: "{query}"
        
        ORIGINAL RESPONSE:
        {response}
        
        Please improve this response by:
        1. Ensuring it directly addresses the query
        2. Removing any remaining generic AI filler phrases or redundant text
        3. Improving structure and readability
        4. Adding any missing critical information
        5. Making the language more natural and concise
        
        Provide the refined response without mentioning that you've refined anything.
        """
        
        # Access the process function for this model
        try:
            boss_processor = None
            
            if hasattr(self.router, 'coordinator') and hasattr(self.router.coordinator, 'model_processors'):
                if boss_model in self.router.coordinator.model_processors:
                    boss_processor = self.router.coordinator.model_processors[boss_model]
            
            if boss_processor and callable(boss_processor):
                logger.info(f"Using boss model {boss_model} for response validation")
                boss_response = await boss_processor(boss_prompt)
                
                # Check if we got a valid response
                if boss_response and not isinstance(boss_response, str):
                    # Handle the case where the response is a dictionary with a 'response' key
                    if isinstance(boss_response, dict) and 'response' in boss_response:
                        return boss_response['response']
                    else:
                        logger.warning(f"Unexpected boss response format: {type(boss_response)}")
                        return response
                else:
                    return boss_response if boss_response else response
            else:
                logger.warning(f"Boss model {boss_model} processor not available")
                return response
        except Exception as e:
            logger.error(f"Error in boss validation: {str(e)}")
            # Return the original response if there's an error
            return response
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query using the full hierarchical workflow.
        
        Args:
            query: The user query string
            
        Returns:
            Dictionary with processed results
        """
        # Step 1: Query Analysis
        task_info = self.analyze_query(query)
        
        # Get available models from the router
        available_models = list(self.router.available_models)
        
        # Step 2: Lead Model Assignment
        lead_model = self.assign_lead_model(task_info, available_models)
        
        # Assign boss model for final validation
        boss_model = self.assign_boss_model(available_models)
        
        # Ensure lead model is included in the model selection
        # Start with router's model selection but prioritize our lead model
        selected_models = self.router.select_models(task_info)
        if lead_model and lead_model not in selected_models:
            selected_models.insert(0, lead_model)
            if len(selected_models) > 3:
                selected_models = selected_models[:3]
        
        # Process query with selected models (similar to router.process_query)
        responses = await self.router.query_models(query, selected_models)
        
        # Step 3: Think Tank Collaboration
        response_weights = self.weight_responses(responses, lead_model)
        
        # Add weights to task_info for ranking
        task_info['response_weights'] = response_weights
        task_info['lead_model'] = lead_model
        
        # Rank responses with our enhanced weighting
        ranked_responses = self.validator.rank_responses(responses, task_info)
        
        # Get best response
        if isinstance(ranked_responses, dict) and 'best_model' in ranked_responses:
            best_model = ranked_responses['best_model']
            best_response = responses.get(best_model, "")
            if isinstance(best_response, dict) and 'response' in best_response:
                best_response = best_response['response']
        else:
            # Fallback to lead model or first available response
            best_model = lead_model if lead_model in responses else next(iter(responses))
            best_response = responses.get(best_model, "")
            if isinstance(best_response, dict) and 'response' in best_response:
                best_response = best_response['response']
        
        # Step 4: Response Structuring
        structured_response = self.structure_response(best_response)
        
        # Step 5: Boss AI Validation
        final_response = await self.boss_validation(structured_response, query, boss_model)
        
        # Prepare the result
        result = {
            'response': {
                'model': best_model,
                'response': final_response,
                'confidence': 0.95  # High confidence due to hierarchical workflow
            },
            'model_info': {
                'best_model': best_model,
                'lead_model': lead_model,
                'boss_model': boss_model,
                'models_used': selected_models,
                'task_type': task_info.get('task_type', 'general'),
                'query_type': task_info.get('query_type', 'general'),
                'tags': task_info.get('tags', []),
                'complexity': task_info.get('complexity', 5),
                'workflow': 'hierarchical',
                'hierarchical': True,
                'blended': False
            }
        }
        
        # Add rankings if available
        if isinstance(ranked_responses, dict) and 'rankings' in ranked_responses:
            result['model_info']['rankings'] = ranked_responses['rankings']
        elif isinstance(ranked_responses, dict) and 'detailed_rankings' in ranked_responses:
            result['model_info']['rankings'] = ranked_responses['detailed_rankings']
        
        return result


# Create a singleton instance for easy importing
workflow = HierarchicalWorkflow()
