"""
Ensemble Validator Module

Handles ranking and validation of responses from multiple AI models.
Implements quality metrics, model capability-based scoring, and robust ranking logic.
"""

import re
import logging
from typing import Dict, List, Any, Union, Optional

logger = logging.getLogger(__name__)

def rank_responses(
    responses: Dict[str, str], 
    original_query: str,
    query_tags: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Rank responses from multiple models based on quality metrics
    
    Args:
        responses: Dict mapping model name to response text
        original_query: Original user query
        query_tags: Query classification tags
        
    Returns:
        List of ranked responses with scores and reasoning
    """
    if not responses:
        logger.warning("No responses to rank")
        return []
    
    if query_tags is None:
        query_tags = {}
    
    # Get model capabilities
    model_capabilities = _get_model_capabilities()
    
    # Evaluate each response across multiple metrics
    evaluations = {}
    for model, response in responses.items():
        # Skip empty responses
        if not response or not response.strip():
            logger.warning(f"Empty response from {model}, skipping")
            continue
            
        # Get base metrics
        metrics = _evaluate_response_quality(response, original_query)
        
        # Get capability scores based on query type
        capability_scores = _get_capability_scores(model, query_tags, model_capabilities)
        
        # Calculate total score (weighted average of quality metrics + capability boost)
        weights = {
            'relevance': 0.3,
            'coherence': 0.15,
            'correctness': 0.25, 
            'helpfulness': 0.2,
            'structure': 0.1
        }
        
        quality_score = sum(metrics[metric] * weights[metric] for metric in weights)
        
        # Apply capability boost (0-0.1 additional points)
        capability_boost = capability_scores.get('boost', 0)
        total_score = min(1.0, quality_score + capability_boost)
        
        # Get detailed reasoning
        reasoning = _generate_ranking_reason(metrics, capability_scores, total_score)
        
        # Store full evaluation data
        evaluations[model] = {
            'model': model,
            'score': total_score,
            'metrics': metrics,
            'capability_scores': capability_scores,
            'reason': reasoning,
            'response_length': len(response)
        }
    
    # Create ranked list of models
    ranked_responses = sorted(
        evaluations.values(), 
        key=lambda x: x['score'], 
        reverse=True
    )
    
    # Format the final ranking data (simplified for API response)
    formatted_rankings = []
    for rank_data in ranked_responses:
        formatted_rankings.append({
            'model': rank_data['model'],
            'score': round(rank_data['score'], 2),
            'reason': rank_data['reason']
        })
    
    logger.info(f"Ranked {len(responses)} models. Top model: {formatted_rankings[0]['model'] if formatted_rankings else 'None'}")
    return formatted_rankings

def validate_response(response: str, query: str, min_quality: float = 0.7) -> Dict[str, Any]:
    """
    Validate a response against quality standards
    
    Args:
        response: Response text to validate
        query: Original query
        min_quality: Minimum quality threshold (0-1)
        
    Returns:
        Dict with validation results
    """
    # Get quality metrics
    metrics = _evaluate_response_quality(response, query)
    
    # Calculate overall quality score
    weights = {
        'relevance': 0.35,
        'coherence': 0.2,
        'correctness': 0.2,
        'helpfulness': 0.15,
        'structure': 0.1
    }
    quality_score = sum(metrics[metric] * weights[metric] for metric in weights)
    
    # Check for rejection patterns
    rejection_check = _check_for_rejections(response)
    
    # Check for critical issues
    critical_issues = []
    if metrics['relevance'] < 0.6:
        critical_issues.append("Response is not relevant to the query")
    if rejection_check['is_rejection']:
        critical_issues.append(f"Response contains rejection pattern: {rejection_check['reason']}")
    if len(response.split()) < 10:
        critical_issues.append("Response is too short")
    
    # Determine if response is valid
    is_valid = quality_score >= min_quality and not critical_issues
    
    return {
        'is_valid': is_valid,
        'quality_score': quality_score,
        'metrics': metrics,
        'critical_issues': critical_issues,
        'rejection_info': rejection_check
    }

def _evaluate_response_quality(response: str, query: str) -> Dict[str, float]:
    """
    Evaluate response quality across multiple metrics
    
    Args:
        response: Response text to evaluate
        query: Original query
        
    Returns:
        Dict of quality metrics with scores (0-1)
    """
    # In production, this would use more sophisticated NLP analysis
    # For now, we'll use simple heuristics
    
    # Convert to lowercase for processing
    response_lower = response.lower()
    query_lower = query.lower()
    
    # Calculate relevance (keyword matching)
    relevance = _calculate_relevance(response_lower, query_lower)
    
    # Calculate coherence (structure, flow, consistency)
    coherence = _calculate_coherence(response)
    
    # Calculate correctness (factual accuracy, logic)
    correctness = _calculate_correctness(response_lower, query_lower)
    
    # Calculate helpfulness (practical, answers the question)
    helpfulness = _calculate_helpfulness(response_lower, query_lower)
    
    # Calculate structure quality (organization, formatting)
    structure = _calculate_structure_quality(response)
    
    return {
        'relevance': relevance,
        'coherence': coherence,
        'correctness': correctness,
        'helpfulness': helpfulness,
        'structure': structure
    }

def _calculate_relevance(response_lower: str, query_lower: str) -> float:
    """Calculate relevance score based on keyword matching"""
    # Extract keywords from query (excluding common words)
    common_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'as'}
    query_words = set(word for word in query_lower.split() if word not in common_words)
    
    # Count keyword matches
    if not query_words:
        return 0.8  # Default for very short queries
        
    matches = sum(1 for word in query_words if word in response_lower)
    relevance_score = min(1.0, matches / len(query_words) * 1.2)  # Scale up slightly
    
    # Check for question words and if they're addressed
    question_words = {'what', 'how', 'why', 'when', 'where', 'who', 'which'}
    query_question_words = [word for word in query_lower.split() if word in question_words]
    
    if query_question_words:
        # Check if response addresses the question type
        question_indicators = {
            'what': ['is', 'are', 'refers to', 'defined as', 'consists of'],
            'how': ['steps', 'process', 'method', 'approach', 'way to'],
            'why': ['because', 'reason', 'due to', 'result of', 'caused by'],
            'when': ['time', 'period', 'during', 'year', 'date', 'century'],
            'where': ['located', 'place', 'position', 'area', 'region'],
            'who': ['person', 'individual', 'group', 'team', 'organization'],
            'which': ['option', 'alternative', 'choice', 'selection', 'preference']
        }
        
        for question_word in query_question_words:
            indicators = question_indicators.get(question_word, [])
            indicator_matches = sum(1 for indicator in indicators if indicator in response_lower)
            if indicator_matches > 0:
                relevance_score += 0.1  # Bonus for addressing question type
                break
    
    return min(1.0, relevance_score)

def _calculate_coherence(response: str) -> float:
    """Calculate coherence score based on structure and flow"""
    # Check for well-formed paragraphs
    paragraphs = response.split('\n\n')
    paragraph_count = len(paragraphs)
    
    # Too many or too few paragraphs may indicate poor structure
    paragraph_score = 0.7
    if 2 <= paragraph_count <= 7:
        paragraph_score = 0.9
    elif paragraph_count > 15:
        paragraph_score = 0.6
    
    # Check for transition words that indicate logical flow
    transition_words = [
        'first', 'second', 'third', 'finally', 'next', 'then', 'additionally',
        'consequently', 'therefore', 'however', 'moreover', 'furthermore',
        'for example', 'specifically', 'in conclusion', 'in summary'
    ]
    
    response_lower = response.lower()
    transition_count = sum(1 for word in transition_words if word in response_lower)
    transition_score = min(1.0, transition_count / 5 * 0.7 + 0.3)  # Base 0.3, up to 1.0
    
    # Check for sentence variety
    sentences = re.split(r'[.!?]+', response)
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
    
    if not sentence_lengths:
        sentence_variety_score = 0.5
    else:
        avg_length = sum(sentence_lengths) / len(sentence_lengths)
        variety = sum(abs(length - avg_length) for length in sentence_lengths) / len(sentence_lengths)
        sentence_variety_score = min(1.0, variety / 5 * 0.7 + 0.3)  # Base 0.3, up to 1.0
    
    # Combine scores
    coherence_score = (paragraph_score * 0.4) + (transition_score * 0.3) + (sentence_variety_score * 0.3)
    
    return coherence_score

def _calculate_correctness(response_lower: str, query_lower: str) -> float:
    """Calculate correctness score based on indicators of accuracy and reasoning"""
    # In production, this would use fact verification against a knowledge base
    # For now, we'll use simple heuristics that look for confidence and reasoning patterns
    
    # Check for uncertainty markers (reduces score)
    uncertainty_markers = [
        'i think', 'probably', 'might be', 'could be', 'possibly',
        'i believe', 'i guess', 'perhaps', 'not sure', 'unclear'
    ]
    
    uncertainty_count = sum(1 for marker in uncertainty_markers if marker in response_lower)
    uncertainty_penalty = min(0.3, uncertainty_count * 0.05)
    
    # Check for reasoning indicators (increases score)
    reasoning_markers = [
        'because', 'therefore', 'since', 'as a result', 'consequently',
        'this means', 'this implies', 'this suggests', 'this indicates',
        'due to', 'reason is', 'explanation', 'evidence', 'research shows'
    ]
    
    reasoning_count = sum(1 for marker in reasoning_markers if marker in response_lower)
    reasoning_bonus = min(0.3, reasoning_count * 0.05)
    
    # Check for precision markers (increases score)
    precision_markers = [
        'specifically', 'precisely', 'exactly', 'in particular',
        'defined as', 'measured as', 'equal to', 'equivalent to',
        'data shows', 'studies indicate', 'research demonstrates'
    ]
    
    precision_count = sum(1 for marker in precision_markers if marker in response_lower)
    precision_bonus = min(0.2, precision_count * 0.04)
    
    # Base correctness score
    base_score = 0.7
    
    # Calculate final score
    correctness_score = min(1.0, max(0.3, base_score - uncertainty_penalty + reasoning_bonus + precision_bonus))
    
    return correctness_score

def _calculate_helpfulness(response_lower: str, query_lower: str) -> float:
    """Calculate helpfulness score based on practical utility"""
    # Check if response provides actionable information
    action_markers = [
        'you can', 'you should', 'you might', 'try', 'consider',
        'recommended', 'suggestion', 'option', 'alternative', 'solution',
        'steps', 'process', 'method', 'approach', 'technique',
        'tool', 'resource', 'example', 'demonstration', 'implementation'
    ]
    
    action_count = sum(1 for marker in action_markers if marker in response_lower)
    action_score = min(0.5, action_count * 0.05) + 0.5  # Base 0.5, up to 1.0
    
    # Check if response addresses different aspects/perspectives
    aspect_markers = [
        'aspect', 'perspective', 'viewpoint', 'approach', 'angle',
        'factor', 'consideration', 'element', 'component', 'dimension',
        'advantage', 'disadvantage', 'benefit', 'drawback', 'pro', 'con',
        'positive', 'negative', 'strength', 'weakness', 'opportunity', 'challenge'
    ]
    
    aspect_count = sum(1 for marker in aspect_markers if marker in response_lower)
    aspect_score = min(0.5, aspect_count * 0.05) + 0.5  # Base 0.5, up to 1.0
    
    # Check if query was a "how to" and if response provides steps
    if 'how to' in query_lower or 'how do i' in query_lower or 'steps to' in query_lower:
        # Look for numbered steps or bullet points
        has_steps = bool(re.search(r'(^|\n)[\*\-\d]+\.?\s', response_lower))
        has_steps_score = 0.9 if has_steps else 0.5
    else:
        has_steps_score = 0.8  # Not applicable
    
    # Combine scores
    helpfulness_score = (action_score * 0.4) + (aspect_score * 0.3) + (has_steps_score * 0.3)
    
    return helpfulness_score

def _calculate_structure_quality(response: str) -> float:
    """Calculate structural quality score based on formatting and organization"""
    # Check for formatting elements
    has_headings = bool(re.search(r'(^|\n)#+\s', response))
    has_bullet_points = bool(re.search(r'(^|\n)[\*\-]\s', response))
    has_numbered_list = bool(re.search(r'(^|\n)\d+\.?\s', response))
    has_code_blocks = bool(re.search(r'```', response))
    has_quotes = bool(re.search(r'(^|\n)>', response))
    
    # Count formatting elements
    formatting_count = sum([has_headings, has_bullet_points, has_numbered_list, has_code_blocks, has_quotes])
    formatting_score = min(1.0, formatting_count * 0.15 + 0.5)  # Base 0.5, up to 1.0
    
    # Check for appropriate length
    word_count = len(response.split())
    
    # Too short or too long responses may be suboptimal
    if word_count < 50:
        length_score = 0.5  # Too short
    elif 50 <= word_count <= 500:
        length_score = 0.9  # Optimal length
    elif 500 < word_count <= 1000:
        length_score = 0.8  # Longer but reasonable
    else:
        length_score = 0.6  # Too long
    
    # Check for section organization (headings/paragraphs ratio)
    paragraphs = response.split('\n\n')
    heading_count = len(re.findall(r'(^|\n)#+\s', response))
    
    if heading_count > 0 and len(paragraphs) > heading_count:
        organization_score = 0.9
    elif heading_count > 0:
        organization_score = 0.8
    elif len(paragraphs) >= 3:
        organization_score = 0.7
    else:
        organization_score = 0.6
    
    # Combine scores
    structure_score = (formatting_score * 0.4) + (length_score * 0.3) + (organization_score * 0.3)
    
    return structure_score

def _check_for_rejections(response: str) -> Dict[str, Any]:
    """Check if response contains refusal patterns"""
    response_lower = response.lower()
    
    # Common refusal/rejection patterns
    refusal_patterns = [
        r"(i'm|i am) (sorry|afraid)",
        r"cannot (provide|generate|create|give)",
        r"unable to (provide|generate|create|give)",
        r"don't have (access|information|ability)",
        r"(against|violates) (policy|policies|guidelines|terms)",
        r"not (able|permitted|allowed) to",
        r"it would be (inappropriate|unethical)",
        r"as an ai (assistant|model)",
    ]
    
    # Check each pattern
    for pattern in refusal_patterns:
        match = re.search(pattern, response_lower)
        if match:
            return {
                'is_rejection': True,
                'pattern': pattern,
                'matched_text': match.group(0),
                'reason': "Contains refusal pattern"
            }
    
    # Check if response is extremely short and contains sorry/cannot
    is_short = len(response.split()) < 40
    has_sorry = "sorry" in response_lower
    has_cannot = "cannot" in response_lower or "can't" in response_lower
    
    if is_short and (has_sorry or has_cannot):
        return {
            'is_rejection': True,
            'pattern': "short_refusal",
            'matched_text': response[:50] + "...",
            'reason': "Short response with refusal indicators"
        }
    
    return {
        'is_rejection': False,
        'pattern': None,
        'matched_text': None,
        'reason': None
    }


def boost_model_capabilities_for_query(
    query: str, 
    model_capabilities: Dict[str, Dict[str, float]]
) -> Dict[str, Dict[str, float]]:
    """
    Boost model capabilities based on query content
    
    Args:
        query: User query text
        model_capabilities: Dict of model capabilities
        
    Returns:
        Dict of boosted model capabilities
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Create a copy of the capabilities to modify
    boosted_capabilities = {}
    for model, caps in model_capabilities.items():
        boosted_capabilities[model] = caps.copy()
    
    # Skip boost for empty queries
    if not query or not query.strip():
        return boosted_capabilities
        
    # Convert query to lowercase for pattern matching
    query_lower = query.lower()
    
    # Define patterns for different query types
    technical_patterns = [
        'code', 'programming', 'function', 'error', 'debug',
        'algorithm', 'api', 'database', 'html', 'css', 'javascript',
        'python', 'java', 'c++', 'sql', 'json', 'xml'
    ]
    
    creative_patterns = [
        'story', 'creative', 'poem', 'fiction', 'imagine',
        'art', 'design', 'write', 'generate', 'create'
    ]
    
    reasoning_patterns = [
        'explain', 'why', 'how does', 'reason', 'analyze',
        'compare', 'difference', 'implications', 'consequences'
    ]
    
    factual_patterns = [
        'fact', 'history', 'science', 'information', 'data',
        'research', 'statistics', 'report', 'study'
    ]
    
    # Technical query boosts
    if any(pattern in query_lower for pattern in technical_patterns):
        logger.info("Query detected as TECHNICAL")
        # Boost models that excel at technical content
        for model in ["gpt-4o", "gpt-4", "claude-3-opus"]:
            if model in boosted_capabilities:
                boosted_capabilities[model]["technical"] *= 1.15  # +15% boost
        
    # Creative query boosts
    if any(pattern in query_lower for pattern in creative_patterns):
        logger.info("Query detected as CREATIVE")
        # Boost models that excel at creative content
        for model in ["claude-3-opus", "gpt-4o", "gemini-pro"]:
            if model in boosted_capabilities:
                boosted_capabilities[model]["creative"] *= 1.15  # +15% boost
    
    # Reasoning query boosts
    if any(pattern in query_lower for pattern in reasoning_patterns):
        logger.info("Query detected as REASONING")
        # Boost models that excel at reasoning
        for model in ["gpt-4o", "claude-3-opus", "gemini-pro"]:
            if model in boosted_capabilities:
                boosted_capabilities[model]["reasoning"] *= 1.10  # +10% boost
    
    # Factual query boosts
    if any(pattern in query_lower for pattern in factual_patterns):
        logger.info("Query detected as FACTUAL")
        # Boost models that excel at factual content
        for model in ["gpt-4o", "claude-3-opus", "gemini-pro"]:
            if model in boosted_capabilities:
                boosted_capabilities[model]["factual"] *= 1.10  # +10% boost
    
    # Apply length-based considerations
    query_length = len(query.split())
    if query_length > 100:  # For very complex, long queries
        logger.info("Query detected as COMPLEX (long)")
        # Boost models with larger context windows
        for model in ["gpt-4o", "claude-3-opus"]:
            if model in boosted_capabilities:
                for capability in ["technical", "reasoning"]:
                    boosted_capabilities[model][capability] *= 1.10  # +10% boost
    
    return boosted_capabilities


def _get_model_capabilities() -> Dict[str, Dict[str, float]]:
    """Get model capability profiles"""
    # These capability scores would ideally be calibrated based on 
    # empirical evaluation of model performance on different task types
    
    # In production, this might be loaded from a database or config file
    # that gets updated as model capabilities change
    
    return {
        'gpt-4o': {
            'technical': 0.95,
            'creative': 0.92,
            'reasoning': 0.95,
            'factual': 0.93,
            'structured': 0.94,
        },

        'claude-3-opus': {
            'technical': 0.93,
            'creative': 0.94,
            'reasoning': 0.95,
            'factual': 0.92,
            'structured': 0.95,
        },

        'gpt-4': {
            'technical': 0.9,
            'creative': 0.85,
            'reasoning': 0.91,
            'factual': 0.88,
            'structured': 0.91,
        },

        'gemini-pro': {
            'technical': 0.88,
            'creative': 0.9,
            'reasoning': 0.91,
            'factual': 0.89,
            'structured': 0.87,
        },

        'mistral-large': {
            'technical': 0.87,
            'creative': 0.85,
            'reasoning': 0.89,
            'factual': 0.86,
            'structured': 0.88,
        },

        'gpt-4o-mini': {
            'technical': 0.82,
            'creative': 0.8,
            'reasoning': 0.84,
            'factual': 0.81,
            'structured': 0.83,
        },

        'claude-3': {
            'technical': 0.85,
            'creative': 0.9,
            'reasoning': 0.85,
            'factual': 0.82,
            'structured': 0.85,
        },

        'claude-3-haiku': {
            'technical': 0.8,
            'creative': 0.85,
            'reasoning': 0.82,
            'factual': 0.8,
            'structured': 0.81,
        },

        'Llama-3.2-1B-Instruct-Q4_0.gguf': {
            'technical': 0.75,
            'creative': 0.7,
            'reasoning': 0.72,
            'factual': 0.65,
            'structured': 0.68,
        },
    }

def _get_capability_scores(model: str, query_tags: Dict[str, Any], 
                           model_capabilities: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """Calculate capability-based scores for a specific model and query type"""
    capability_scores = {}
    
    # Get model capability profile
    model_profile = model_capabilities.get(model, {})
    if not model_profile:
        return {'boost': 0, 'detail': 'Model capabilities unknown'}
    
    # Determine query type capability mapping
    capability_mapping = {}
    
    # Map from domain tags to capability areas
    domains = query_tags.get('domains', [])
    request_types = query_tags.get('request_types', [])
    
    # Domain to capability mapping
    if 'ai' in domains:
        capability_mapping['technical'] = 3.5
        capability_mapping['reasoning'] = 2.5
        capability_mapping['factual'] = 2.0
        capability_mapping['structured'] = 2.0
    elif 'data' in domains:
        capability_mapping['technical'] = 3.0
        capability_mapping['structured'] = 2.5
        capability_mapping['factual'] = 2.0
    elif 'code' in domains:
        capability_mapping['technical'] = 3.0
        capability_mapping['structured'] = 2.0
    elif 'math' in domains:
        capability_mapping['technical'] = 3.0
        capability_mapping['reasoning'] = 2.0
    elif 'science' in domains:
        capability_mapping['factual'] = 2.5
        capability_mapping['reasoning'] = 2.0
    elif 'business' in domains:
        capability_mapping['factual'] = 2.0
        capability_mapping['structured'] = 1.5
    elif 'creative' in domains:
        capability_mapping['creative'] = 3.0
    elif 'philosophical' in domains:
        capability_mapping['reasoning'] = 3.0
    
    # Request type to capability mapping
    if 'explanation' in request_types:
        capability_mapping['factual'] = capability_mapping.get('factual', 0) + 2.0
    elif 'comparison' in request_types:
        capability_mapping['reasoning'] = capability_mapping.get('reasoning', 0) + 2.0
        capability_mapping['structured'] = capability_mapping.get('structured', 0) + 1.5
    elif 'procedure' in request_types:
        capability_mapping['structured'] = capability_mapping.get('structured', 0) + 2.5
        capability_mapping['technical'] = capability_mapping.get('technical', 0) + 1.5
    elif 'evaluation' in request_types:
        capability_mapping['reasoning'] = capability_mapping.get('reasoning', 0) + 2.5
    elif 'generation' in request_types:
        capability_mapping['creative'] = capability_mapping.get('creative', 0) + 2.5
    elif 'optimization' in request_types:
        capability_mapping['technical'] = capability_mapping.get('technical', 0) + 3.0
        capability_mapping['reasoning'] = capability_mapping.get('reasoning', 0) + 2.0
    elif 'troubleshooting' in request_types:
        capability_mapping['technical'] = capability_mapping.get('technical', 0) + 3.5
        capability_mapping['reasoning'] = capability_mapping.get('reasoning', 0) + 2.5
        capability_mapping['structured'] = capability_mapping.get('structured', 0) + 1.5
    elif 'opinion' in request_types:
        capability_mapping['reasoning'] = capability_mapping.get('reasoning', 0) + 2.0
    
    # If we couldn't determine capability mapping, use a balanced approach
    if not capability_mapping:
        capability_mapping = {
            'technical': 1.0,
            'creative': 1.0,
            'reasoning': 1.0,
            'factual': 1.0,
            'structured': 1.0
        }
    
    # Calculate weighted capability score
    total_weight = sum(capability_mapping.values())
    if total_weight > 0:
        weighted_score = sum(model_profile.get(capability, 0.5) * weight 
                           for capability, weight in capability_mapping.items()) / total_weight
    else:
        weighted_score = 0.75  # Default mid-range score
    
    # Calculate boost (0-0.1 scale)
    capability_boost = (weighted_score - 0.75) * 0.2  # Convert from 0.5-1.0 to -0.05-0.05 range
    capability_boost = max(0, capability_boost)  # Only positive boosts
    
    # Format capability detail
    capability_detail = {
        capability: f"{model_profile.get(capability, 0):.2f}" 
        for capability in capability_mapping
    }
    
    return {
        'boost': round(capability_boost, 3),
        'weighted_score': round(weighted_score, 2),
        'detail': capability_detail
    }

def _generate_ranking_reason(metrics: Dict[str, float], 
                             capability_scores: Dict[str, Any], 
                             total_score: float) -> str:
    """Generate human-readable ranking reason based on metrics"""
    # Determine strongest and weakest metrics
    metrics_list = list(metrics.items())
    metrics_list.sort(key=lambda x: x[1], reverse=True)
    
    top_metrics = metrics_list[:2]
    bottom_metrics = metrics_list[-2:]
    
    # Format reason based on metrics and capability scores
    strengths = [f"{metric.capitalize()} ({score:.2f})" for metric, score in top_metrics]
    weaknesses = [f"{metric.capitalize()} ({score:.2f})" for metric, score in bottom_metrics if score < 0.75]
    
    reason_parts = []
    
    # Add strength components
    if strengths:
        reason_parts.append(f"Strong {' and '.join(strengths)}")
    
    # Add capability component if there's a boost
    boost = capability_scores.get('boost', 0)
    if boost > 0.02:
        reason_parts.append(f"Well-suited for this query type (+{boost:.2f})")
    
    # Add weakness components if any
    if weaknesses:
        if reason_parts:
            reason_parts.append("but")
        reason_parts.append(f"weaker {' and '.join(weaknesses)}")
    
    # Fallback if we couldn't generate specific reasons
    if not reason_parts:
        if total_score > 0.85:
            return "Excellent overall performance"
        elif total_score > 0.75:
            return "Good balanced response"
        elif total_score > 0.65:
            return "Acceptable but not exceptional"
        else:
            return "Multiple areas need improvement"
    
    # Join all reason components
    return " ".join(reason_parts)
