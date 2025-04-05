#!/usr/bin/env python3
"""
Response Generator for Minerva

This module provides enhanced response generation with multi-model blending capabilities.
It improves upon the simulated responses by implementing more sophisticated
response structures, context awareness, and blending strategies.
"""

import logging
import re
import json
import random
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import existing response handler if available

# Query tagging categories
TECHNICAL_TAGS = ["technical", "programming", "code", "development", "engineering"]
CREATIVE_TAGS = ["creative", "story", "poem", "imagine", "fiction"]
FACTUAL_TAGS = ["fact", "information", "data", "research", "statistics"]
COMPARISON_TAGS = ["compare", "versus", "vs", "difference", "similarity"]
EXPLANATION_TAGS = ["explain", "how", "why", "what is", "describe"]

def tag_query(query: str) -> List[str]:
    """
    Tag a user query with appropriate categories for model selection and blending.
    
    Args:
        query: The user's query text
        
    Returns:
        List of tags that categorize the query
    """
    query_lower = query.lower()
    tags = []
    
    # Check for technical content
    if any(term in query_lower for term in ["code", "program", "function", "algorithm", "api", "debug", "error"]):
        tags.append("technical")
    
    # Check for creative requests
    if any(term in query_lower for term in ["story", "poem", "creative", "imagine", "fiction", "write a"]):
        tags.append("creative")
    
    # Check for factual questions
    if any(term in query_lower for term in ["fact", "data", "research", "information", "when was", "who is"]):
        tags.append("factual")
    
    # Check for comparison questions
    if any(term in query_lower for term in ["compare", "versus", "vs", "difference between", "similarities"]):
        tags.append("comparison")
    
    # Check for explanations
    if any(term in query_lower for term in ["explain", "how does", "why is", "what is", "describe"]):
        tags.append("explanation")
    
    # Default tag if nothing else matches
    if not tags:
        tags.append("general")
    
    return tags
try:
    from web.response_handler import clean_ai_response, format_response
except ImportError:
    logger.warning("Could not import response_handler, using built-in fallbacks")
    
    def clean_ai_response(text):
        """Simple fallback for cleaning responses"""
        if not text:
            return "I couldn't generate a response. Please try again."
        return text.strip()
    
    def format_response(text, params=None):
        """Simple fallback for formatting responses"""
        return text

# Model capability profiles for response blending
MODEL_CAPABILITIES = {
    "gpt4": {
        "reasoning": 0.95,
        "creativity": 0.85,
        "technical": 0.92,
        "factual": 0.90,
        "detailed": 0.95,
        "conversational": 0.85
    },
    "gpt-3.5-turbo": {
        "reasoning": 0.75,
        "creativity": 0.80,
        "technical": 0.70,
        "factual": 0.80,
        "detailed": 0.75,
        "conversational": 0.90
    },
    "claude3": {
        "reasoning": 0.92,
        "creativity": 0.88,
        "technical": 0.85,
        "factual": 0.92,
        "detailed": 0.90,
        "conversational": 0.92
    },
    "gemini": {
        "reasoning": 0.90,
        "creativity": 0.85,
        "technical": 0.88,
        "factual": 0.85,
        "detailed": 0.85,
        "conversational": 0.80
    },
    "mistral7b": {
        "reasoning": 0.75,
        "creativity": 0.70,
        "technical": 0.65,
        "factual": 0.75,
        "detailed": 0.60,
        "conversational": 0.75
    },
    "gpt4all": {
        "reasoning": 0.65,
        "creativity": 0.60,
        "technical": 0.60,
        "factual": 0.65,
        "detailed": 0.55,
        "conversational": 0.70
    }
}

# Tags that indicate specific response blending strategies
TECHNICAL_TAGS = ["code", "programming", "technical", "algorithm", "science", "math"]
CREATIVE_TAGS = ["creative", "writing", "story", "design", "artistic", "novel"]
FACTUAL_TAGS = ["facts", "history", "data", "information", "research"]
COMPARISON_TAGS = ["comparison", "contrast", "versus", "vs", "difference", "compare"]
EXPLANATION_TAGS = ["explain", "explanation", "describe", "clarify", "elaborate"]

# Memory and user preference handling
def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Retrieve user preferences for personalized responses.
    
    Args:
        user_id: The user's identifier
        
    Returns:
        Dictionary with user preferences
    """
    # This would typically query a database in a real implementation
    # For now, we'll use a simple mock implementation
    default_prefs = {
        "preferred_tone": "conversational",
        "detail_level": "medium",
        "technical_depth": "medium",
        "frequent_topics": [],
        "preferred_models": []
    }
    
    logger.info(f"Retrieved preferences for user {user_id}")
    return default_prefs

def get_relevant_memories(query: str, user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve relevant memories for contextual response generation.
    
    Args:
        query: The user's current query
        user_id: The user's identifier
        
    Returns:
        List of relevant memories
    """
    # This would typically query a memory database in a real implementation
    # For now, we'll return an empty list
    logger.info(f"Retrieved relevant memories for query from user {user_id}")
    return []

# Model selection and quality evaluation
def select_models_for_query(query: str, user_prefs: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    """
    Select appropriate models based on query type and user preferences.
    
    Args:
        query: The user's query
        user_prefs: User preferences
        context: Additional context information
        
    Returns:
        List of model identifiers to use
    """
    # Extract query tags if available
    tags = context.get("tags", [])
    
    # Define models to use based on query characteristics
    models = []
    
    # Check for technical content
    if any(tag in TECHNICAL_TAGS for tag in tags):
        models.extend(["gpt4", "claude3"])
    
    # Check for creative content
    elif any(tag in CREATIVE_TAGS for tag in tags):
        models.extend(["claude3", "gemini"])
    
    # Check for factual content
    elif any(tag in FACTUAL_TAGS for tag in tags):
        models.extend(["gpt4", "claude3"])
    
    # Check for comparison requests
    elif any(tag in COMPARISON_TAGS for tag in tags):
        models.extend(["gpt4", "claude3", "gemini"])
    
    # Check for explanation requests
    elif any(tag in EXPLANATION_TAGS for tag in tags):
        models.extend(["gpt4", "claude3"])
    
    # Default model selection
    if not models:
        models = ["gpt-3.5-turbo", "gpt4"]
    
    # Add user preferred models if specified
    preferred_models = user_prefs.get("preferred_models", [])
    if preferred_models:
        # Ensure preferred models are prioritized
        for model in preferred_models:
            if model not in models:
                models.insert(0, model)
    
    # Limit to 3 models maximum for efficiency
    return models[:3]

def evaluate_response_quality(response: str, query: str) -> Dict[str, float]:
    """
    Evaluate the quality of a model response across multiple dimensions.
    
    Args:
        response: The model's response text
        query: The original user query
        
    Returns:
        Dictionary with scores for different quality dimensions
    """
    # Calculate clarity score (1-5)
    clarity = 4.0  # Default score
    # Penalize for overly complex language or poor structure
    if len(response) > 5000:  # Very long responses
        clarity -= 0.5
    # Check for good paragraph structure
    if re.search(r'\n\n', response):
        clarity += 0.5
    # Check for bullet points and lists
    if re.search(r'\n[\*\-+] ', response):
        clarity += 0.5
    
    # Calculate relevance score (1-5)
    relevance = 4.0  # Default score
    # Simple relevance check: if query terms appear in response
    for term in query.lower().split():
        if len(term) > 3 and term.lower() in response.lower():
            relevance += 0.1
    # Penalize for AI self-references
    if re.search(r'(as an ai|as a language model)', response.lower()):
        relevance -= 1.0
    
    # Calculate coherence score (1-5)
    coherence = 4.0  # Default score
    # Penalty for disjointed content
    if len(re.findall(r'\n\n\n+', response)) > 3:  # Too many paragraph breaks
        coherence -= 0.5
    # Check for good transitions between paragraphs
    if re.search(r'(however|therefore|in addition|furthermore|moreover)', response.lower()):
        coherence += 0.5
    
    # Adjust scores to 1-5 range
    clarity = max(1.0, min(5.0, clarity))
    relevance = max(1.0, min(5.0, relevance))
    coherence = max(1.0, min(5.0, coherence))
    
    # Calculate overall score (1-5)
    overall = (clarity + relevance + coherence) / 3
    
    # Add a small random factor to avoid ties
    overall += random.uniform(-0.1, 0.1)
    
    return {
        "clarity": clarity,
        "relevance": relevance,
        "coherence": coherence,
        "overall": overall
    }

def rank_responses(model_responses: Dict[str, str], query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Rank multiple model responses based on quality and capability.
    
    Args:
        model_responses: Dict mapping model names to their response texts
        query: The original user query
        context: Additional context information
        
    Returns:
        List of ranked response objects with quality scores
    """
    # Extract query tags if available
    tags = context.get("tags", [])
    
    # Evaluate each response
    scored_responses = []
    for model_name, response_text in model_responses.items():
        # Evaluate base quality
        quality_scores = evaluate_response_quality(response_text, query)
        
        # Get model capabilities
        model_key = model_name.lower().replace("-", "").replace(".", "")  # Normalize model name
        capabilities = MODEL_CAPABILITIES.get(model_key, {})
        
        # Calculate capability boost based on query type
        capability_boost = 1.0  # Default multiplier
        boost_reason = "No specific capability boost applied"
        
        # Apply capability boost based on query type
        if any(tag in TECHNICAL_TAGS for tag in tags) and "technical" in capabilities:
            capability_boost = 1.0 + (capabilities["technical"] * 0.3)
            boost_reason = f"Technical query boosted by {capabilities['technical']:.2f} factor"
        elif any(tag in CREATIVE_TAGS for tag in tags) and "creativity" in capabilities:
            capability_boost = 1.0 + (capabilities["creativity"] * 0.3)
            boost_reason = f"Creative query boosted by {capabilities['creativity']:.2f} factor"
        elif any(tag in FACTUAL_TAGS for tag in tags) and "factual" in capabilities:
            capability_boost = 1.0 + (capabilities["factual"] * 0.3)
            boost_reason = f"Factual query boosted by {capabilities['factual']:.2f} factor"
        elif any(tag in COMPARISON_TAGS for tag in tags) and "reasoning" in capabilities:
            capability_boost = 1.0 + (capabilities["reasoning"] * 0.3)
            boost_reason = f"Comparison query boosted by {capabilities['reasoning']:.2f} factor"
        elif any(tag in EXPLANATION_TAGS for tag in tags) and "detailed" in capabilities:
            capability_boost = 1.0 + (capabilities["detailed"] * 0.3)
            boost_reason = f"Explanation query boosted by {capabilities['detailed']:.2f} factor"
        
        # Calculate final score
        final_score = quality_scores["overall"] * capability_boost
        
        scored_responses.append({
            "model_name": model_name,
            "response_text": response_text,
            "quality_scores": quality_scores,
            "capability_boost": capability_boost,
            "boost_reason": boost_reason,
            "final_score": final_score
        })
    
    # Sort by final score in descending order
    scored_responses.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Add rank positions
    for i, resp in enumerate(scored_responses):
        resp["rank"] = i + 1
    
    return scored_responses

def extract_key_points(response: str) -> List[str]:
    """
    Extract key points from a response text.
    
    Args:
        response: The text to extract points from
        
    Returns:
        List of key point statements
    """
    points = []
    
    # Extract bullet points and lists
    bullet_pattern = re.compile(r'\n[\*\-+] ([^\n]+)')
    bullets = bullet_pattern.findall(response)
    points.extend(bullets)
    
    # Extract numbered points
    numbered_pattern = re.compile(r'\n\d+\.\s+([^\n]+)')
    numbered = numbered_pattern.findall(response)
    points.extend(numbered)
    
    # Extract sentences with strong indicators
    indicator_pattern = re.compile(r'(?:key|important|main|critical|essential)\s+(?:point|aspect|factor|element|consideration)s?\s+(?:is|are|include)\s+([^\.]+')
    indicators = indicator_pattern.findall(response.lower())
    points.extend(indicators)
    
    # If not enough points found, extract sentences with strong structures
    if len(points) < 3:
        # Look for sentences that begin with "The" or "A" and end with a period
        sentence_pattern = re.compile(r'(?:\. |^)([A-Z][^\.]+(\.|\!|\?))')
        sentences = sentence_pattern.findall(response)
        for sentence in sentences[:5]:  # Limit to first 5 sentences
            if sentence[0] not in points:
                points.append(sentence[0])
    
    return points[:10]  # Limit to 10 key points maximum

def blend_technical_responses(ranked_responses: List[Dict[str, Any]]) -> str:
    """
    Blend technical responses with focus on code quality and explanation.
    
    Args:
        ranked_responses: List of ranked model responses
        
    Returns:
        Blended response text
    """
    blended = ""
    
    # Extract code blocks from all responses
    code_blocks = []
    for resp in ranked_responses:
        # Find code blocks in the response
        code_pattern = re.compile(r'```(?:\w+)?\n(.+?)\n```', re.DOTALL)
        blocks = code_pattern.findall(resp["response_text"])
        for block in blocks:
            if block not in code_blocks and len(block.strip()) > 10:  # Avoid duplicates and empty blocks
                code_blocks.append(block)
    
    # Get explanation from highest ranked response
    top_response = ranked_responses[0]["response_text"]
    
    # Remove code blocks from explanation to avoid duplication
    explanation = re.sub(r'```(?:\w+)?\n.+?\n```', '', top_response, flags=re.DOTALL)
    
    # Build the blended response
    blended += explanation.strip() + "\n\n"
    
    # Add compiled code examples
    if code_blocks:
        blended += "Here's the implementation:\n\n"
        for i, block in enumerate(code_blocks[:2]):  # Limit to 2 code blocks
            lang = "python"  # Default language
            if "def " in block or "class " in block or "import " in block:
                lang = "python"
            elif "{" in block and "}" in block and "function" in block:
                lang = "javascript"
            elif "public static void" in block or "class " in block and "{" in block:
                lang = "java"
            
            blended += f"```{lang}\n{block}\n```\n\n"
    
    # Add insights from other models
    if len(ranked_responses) > 1:
        insights = []
        for resp in ranked_responses[1:]:
            points = extract_key_points(resp["response_text"])
            insights.extend(points)
        
        # Add unique insights
        if insights:
            blended += "Additional insights:\n\n"
            for insight in insights[:3]:  # Limit to 3 insights
                blended += f"- {insight}\n"
    
    return blended.strip()

def blend_explanation_responses(ranked_responses: List[Dict[str, Any]]) -> str:
    """
    Blend explanation responses with focus on comprehensiveness and clarity.
    
    Args:
        ranked_responses: List of ranked model responses
        
    Returns:
        Blended response text
    """
    # Start with the highest ranked explanation
    blended = ranked_responses[0]["response_text"]
    
    # Look for structured sections in other responses that could enhance the explanation
    if len(ranked_responses) > 1:
        section_headers = []
        sections_to_add = []
        
        # Extract section headers from top response
        headers_pattern = re.compile(r'\n\s*#{1,3}\s+([^\n]+)\n')
        existing_headers = headers_pattern.findall(blended)
        section_headers.extend([h.lower() for h in existing_headers])
        
        # Look for strong section headers in other responses
        for resp in ranked_responses[1:]:
            resp_text = resp["response_text"]
            
            # Find section headers in this response
            resp_headers = headers_pattern.findall(resp_text)
            
            for header in resp_headers:
                # If this section doesn't exist in the blended response, extract it
                if header.lower() not in section_headers:
                    # Try to extract the section content
                    header_pattern = re.escape(header)
                    section_pattern = re.compile(f"\n\s*#{1,3}\s+{header_pattern}\n([^#]+)")
                    matches = section_pattern.findall(resp_text)
                    
                    if matches:
                        sections_to_add.append(f"\n\n## {header}\n{matches[0].strip()}")
                        section_headers.append(header.lower())
        
        # Add unique sections to the blended response
        if sections_to_add:
            blended += "\n\n" + "\n\n".join(sections_to_add)
    
    return blended.strip()

def blend_general_responses(ranked_responses: List[Dict[str, Any]]) -> str:
    """
    Default response blending for general queries.
    
    Args:
        ranked_responses: List of ranked model responses
        
    Returns:
        Blended response text
    """
    # For general responses, use the best response as the base
    blended = ranked_responses[0]["response_text"]
    
    # Only add insights if we have multiple responses
    if len(ranked_responses) > 1:
        insights = []
        for resp in ranked_responses[1:]:  # Skip the top response as we're already using it
            points = extract_key_points(resp["response_text"])
            for point in points:
                if point not in blended and point not in insights:
                    insights.append(point)
        
        # Add unique insights
        if insights:
            blended += "\n\nAdditional insights:\n\n"
            for insight in insights[:3]:  # Limit to 3 additional insights
                blended += f"- {insight}\n"
    
    return blended.strip()

def blend_responses(ranked_responses: List[Dict[str, Any]], query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Blend multiple responses into a cohesive final response.
    
    Args:
        ranked_responses: List of ranked model responses
        query: The original user query
        context: Additional context information
        
    Returns:
        Dictionary with blended response and metadata
    """
    if not ranked_responses:
        return {
            "response_text": "I couldn't generate a response to your query.",
            "model_name": "blended",
            "blended": False,
            "sources": []
        }
    
    # If only one response, return it directly
    if len(ranked_responses) == 1:
        return {
            "response_text": ranked_responses[0]["response_text"],
            "model_name": ranked_responses[0]["model_name"],
            "blended": False,
            "sources": [ranked_responses[0]["model_name"]]
        }
    
    # Extract query tags if available
    tags = context.get("tags", [])
    
    # Choose appropriate blending strategy based on query type
    if any(tag in TECHNICAL_TAGS for tag in tags):
        blended_text = blend_technical_responses(ranked_responses)
        blend_strategy = "technical"
    elif any(tag in COMPARISON_TAGS for tag in tags):
        blended_text = blend_comparison_responses(ranked_responses)
        blend_strategy = "comparison"
    elif any(tag in EXPLANATION_TAGS for tag in tags):
        blended_text = blend_explanation_responses(ranked_responses)
        blend_strategy = "explanation"
    else:
        blended_text = blend_general_responses(ranked_responses)
        blend_strategy = "general"
    
    # Create source attribution
    sources = [resp["model_name"] for resp in ranked_responses]
    contributions = []
    
    for resp in ranked_responses:
        model_name = resp["model_name"]
        score = resp["final_score"]
        rank = resp["rank"]
        boost_reason = resp["boost_reason"]
        
        contributions.append({
            "model": model_name,
            "rank": rank,
            "score": score,
            "reason": boost_reason
        })
    
    return {
        "response_text": blended_text,
        "model_name": "blended",
        "blended": True,
        "blend_strategy": blend_strategy,
        "sources": sources,
        "contributions": contributions
    }

def generate_enhanced_response(query: str, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate an enhanced response using multi-model blending and personalization.
    
    Args:
        query: The user's query
        user_id: The user's identifier
        context: Optional additional context
        
    Returns:
        Dictionary with response text and metadata
    """
    if context is None:
        context = {}
    
    # Augment context with user preferences and memories
    user_prefs = get_user_preferences(user_id)
    memories = get_relevant_memories(query, user_id)
    
    if memories:
        context["memories"] = memories
    
    # Tag the query to help with model selection and response formatting
    context["tags"] = tag_query(query)
    
    # Select appropriate models for this query
    selected_models = select_models_for_query(query, user_prefs, context)
    
    # Process the query with selected models
    model_responses = {}
    error_responses = {}
    
    from web.router_integration import query_models
    
    # Log model selection for debugging
    logging.info(f"Selected models for query '{query[:50]}...': {selected_models}")
    
    for model_name in selected_models:
        try:
            # Query the model (implementation depends on your system)
            response = query_models([model_name], query, context.get("history", []))
            
            if response and model_name in response:
                cleaned_response = clean_ai_response(response[model_name])
                model_responses[model_name] = cleaned_response
            else:
                logging.warning(f"Model {model_name} returned no response")
                error_responses[model_name] = "No response returned"
        except Exception as e:
            logging.error(f"Error querying model {model_name}: {str(e)}")
            error_responses[model_name] = str(e)
    
    # If no successful responses, return an error
    if not model_responses:
        return {
            "response_text": "I'm sorry, I couldn't process your query at this time. Please try again later.",
            "model_name": "error",
            "errors": error_responses,
            "blended": False
        }
    
    # Rank the responses
    ranked_responses = rank_responses(model_responses, query, context)
    
    # Blend the responses
    final_response = blend_responses(ranked_responses, query, context)
    
    # Add metadata for debugging and analysis
    final_response["query"] = query
    final_response["user_id"] = user_id
    final_response["context"] = {
        "tags": context.get("tags", []),
        "has_memories": bool(memories)
    }
    
    # Log response generation metadata
    logging.info(f"Generated response for user {user_id} using {len(model_responses)} models")
    if final_response.get("blended", False):
        logging.info(f"Blended response using strategy: {final_response.get('blend_strategy', 'unknown')}")
    
    return final_response
def blend_comparison_responses(ranked_responses: List[Dict[str, Any]]) -> str:
    """
    Blend comparison responses with focus on balanced perspectives.
    
    Args:
        ranked_responses: List of ranked model responses
        
    Returns:
        Blended response text
    """
    # Use the top response as the base
    blended = ranked_responses[0]["response_text"]
    
    # Add insights from other responses if there are any
    if len(ranked_responses) > 1:
        additional_points = []
        
        for resp in ranked_responses[1:]:
            points = extract_key_points(resp["response_text"])
            additional_points.extend(points)
        
        # Only include non-duplicate insights
        unique_points = []
        for point in additional_points:
            if point not in blended and point not in unique_points:
                unique_points.append(point)
        
        if unique_points:
            blended += "\n\nAdditional perspectives from other models:\n\n"
            for point in unique_points[:5]:  # Limit to 5 additional points
                blended += f"- {point}\n"
    
    return blended.strip()
