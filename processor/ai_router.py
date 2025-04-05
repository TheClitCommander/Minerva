"""
AI Router Module

Handles intelligent model selection based on content analysis.
Implements content-based routing and query tagging for optimal model selection.
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def route_request(message: str) -> Dict[str, Any]:
    """
    Analyzes message content and determines optimal model routing
    
    Args:
        message: User message text
        
    Returns:
        Dict containing routing information:
        - model_priority: List of models in priority order
        - complexity_score: Numerical assessment of query complexity (0-100)
        - confidence: Router confidence in its selection
    """
    # Message preprocessing
    message_lower = message.lower().strip()
    word_count = len(message_lower.split())
    
    # Complexity scoring
    complexity_factors = {
        'length': min(1.0, word_count / 100) * 30,  # Up to 30 points for length (caps at 100 words)
        'technical_terms': _count_technical_terms(message) * 5,  # 5 points per technical term
        'question_complexity': _assess_question_complexity(message) * 20,  # Up to 20 points
        'domain_specificity': _assess_domain_specificity(message) * 25,  # Up to 25 points
    }
    
    complexity_score = min(100, sum(complexity_factors.values()))
    
    # Determine confidence threshold based on complexity
    # Higher complexity = higher threshold for confident routing
    confidence_threshold = 0.5 + (complexity_score / 400)  # 0.5 to 0.75 range
    
    # Model priority based on content analysis
    model_priority = _determine_model_priority(message, complexity_score)
    
    # Calculate confidence in routing decision
    confidence = _calculate_routing_confidence(message, complexity_score)
    
    # Prepare routing metadata
    routing_info = {
        'model_priority': model_priority,
        'complexity_score': complexity_score,
        'confidence': confidence,
        'confidence_threshold': confidence_threshold,
        'complexity_factors': complexity_factors
    }
    
    logger.debug(f"Routing decision: {routing_info}")
    return routing_info

def get_query_tags(message: str) -> Dict[str, Any]:
    """
    Identifies query types and domains based on message content
    
    Args:
        message: User message text
        
    Returns:
        Dict of identified tags and metadata
    """
    message_lower = message.lower().strip()
    
    # Content domain detection
    domains = {
        'code': bool(re.search(r'(code|function|programming|algorithm|bug|class|variable|api|framework|library|module|package|repository|git)', message_lower)),
        'math': bool(re.search(r'(math|equation|calculate|formula|computation|algebra|calculus|geometric|statistical|probability|distribution)', message_lower)),
        'science': bool(re.search(r'(science|scientific|physics|chemistry|biology|experiment|hypothesis|theory|research|empirical)', message_lower)),
        'business': bool(re.search(r'(business|market|company|profit|loss|investment|strategy|customer|revenue|financial|commercial)', message_lower)),
        'creative': bool(re.search(r'(creative|write|story|poem|song|design|imagine|create|art|novel|fiction|craft)', message_lower)),
        'philosophical': bool(re.search(r'(philosophy|ethics|meaning|purpose|consciousness|moral|value|belief|existential|metaphysical)', message_lower)),
        'ai': bool(re.search(r'(machine learning|neural network|ai|artificial intelligence|deep learning|nlp|natural language processing|model|training|dataset|feature|classification|regression|clustering|transformer|embedding|tokenization|fine-tuning|hyperparameter|backpropagation|gradient descent)', message_lower)),
        'data': bool(re.search(r'(data|database|sql|query|analytics|visualization|dashboard|metrics|statistics|graph|plot|chart|pandas|excel|csv|json|api data|rest api|data science)', message_lower)),
    }
    
    # Request type detection
    request_types = {
        'explanation': bool(re.search(r'(explain|what is|how does|tell me about|describe|clarify|elaborate on|help me understand)', message_lower)),
        'comparison': bool(re.search(r'(compare|difference|versus|vs|better|worse|contrast|similar|differentiating|pros and cons)', message_lower)),
        'procedure': bool(re.search(r'(how to|steps|procedure|process|method|approach|implementation|guide|tutorial|walkthrough|instructions)', message_lower)),
        'evaluation': bool(re.search(r'(evaluate|assess|analyze|review|critique|feedback|pros|cons|strength|weakness|performance)', message_lower)),
        'generation': bool(re.search(r'(generate|create|make|design|develop|build|implement|produce|construct|synthesize|form)', message_lower)),
        'opinion': bool(re.search(r'(opinion|think|believe|view|perspective|stance|thought|position|attitude|judgment|feeling)', message_lower)),
        'optimization': bool(re.search(r'(optimize|improve|enhance|boost|upgrade|refine|streamline|efficiency|performance|faster|better)', message_lower)),
        'troubleshooting': bool(re.search(r'(troubleshoot|debug|fix|solve|issue|problem|error|bug|not working|failed|crashes|exception)', message_lower)),
    }
    
    # Attempt to identify primary domain and request type
    primary_domain = max(domains.items(), key=lambda x: x[1] * 1)[0] if any(domains.values()) else None
    primary_request = max(request_types.items(), key=lambda x: x[1] * 1)[0] if any(request_types.values()) else None
    
    # Prepare query tags
    tags = {
        'domains': [domain for domain, present in domains.items() if present],
        'request_types': [req_type for req_type, present in request_types.items() if present],
        'primary_domain': primary_domain,
        'primary_request': primary_request,
    }
    
    logger.debug(f"Query tags: {tags}")
    return tags

# Internal helper functions
def _count_technical_terms(message: str) -> int:
    """Count technical terms in message"""
    technical_terms = [
        'algorithm', 'function', 'class', 'method', 'API', 'database', 'server',
        'client', 'backend', 'frontend', 'framework', 'library', 'component',
        'integration', 'deployment', 'optimization', 'performance', 'scalability',
        'architecture', 'infrastructure', 'protocol', 'interface', 'dependency',
        'recursion', 'iteration', 'inheritance', 'polymorphism', 'encapsulation',
        'abstraction', 'serialization', 'deserialization', 'synchronous', 'asynchronous'
    ]
    
    count = 0
    message_lower = message.lower()
    for term in technical_terms:
        if term.lower() in message_lower:
            count += 1
    return count

def _assess_question_complexity(message: str) -> float:
    """Rate question complexity on 0-1 scale"""
    # Base complexity
    complexity = 0.0
    
    # Multi-part questions
    if re.search(r'(\?[^?]*\?)', message) or message.count('?') > 1:
        complexity += 0.3
    
    # Questions requiring detailed explanation
    if re.search(r'(explain|elaborate|detail|describe|clarify)', message.lower()):
        complexity += 0.25
    
    # Questions about relationships or comparisons
    if re.search(r'(relate|relationship|compare|difference|similarity)', message.lower()):
        complexity += 0.2
    
    # Questions about reasons or causes
    if re.search(r'(why|cause|reason|rationale|factor)', message.lower()):
        complexity += 0.25
        
    return min(1.0, complexity)

def _assess_domain_specificity(message: str) -> float:
    """Rate domain specificity on 0-1 scale"""
    specificity = 0.0
    
    # Check for specialized terminology
    specialized_domains = {
        'programming': r'(function|algorithm|class|method|API|object|variable|inheritance)',
        'medicine': r'(diagnosis|treatment|disease|syndrome|patient|symptoms|prognosis)',
        'finance': r'(investment|stock|portfolio|asset|liability|equity|dividend|yield)',
        'law': r'(statute|regulation|precedent|contract|liability|tort|plaintiff|defendant)',
        'physics': r'(quantum|relativity|gravity|particle|acceleration|velocity|momentum)'
    }
    
    for domain, pattern in specialized_domains.items():
        if re.search(pattern, message.lower()):
            specificity += 0.2
            break
            
    # Check for specialized measures or units
    if re.search(r'([0-9]+\s*(kg|m|s|A|K|mol|cd|Hz|N|Pa|J|W|C|V|F|Ω|S|Wb|T|H|lm|lx))', message):
        specificity += 0.15
        
    # Check for equations or formulas
    if re.search(r'[a-zA-Z]\s*[=]\s*[a-zA-Z0-9\+\-\*\/\(\)]', message):
        specificity += 0.25
        
    # Check for specific named entities (simplified)
    capitalized_words = re.findall(r'\b[A-Z][a-zA-Z]*\b', message)
    if len(capitalized_words) >= 2:
        specificity += min(0.2, len(capitalized_words) * 0.05)
        
    return min(1.0, specificity)

def _determine_model_priority(message: str, complexity_score: float) -> List[str]:
    """
    Determine model priority order based on content analysis
    
    Args:
        message: User message
        complexity_score: Message complexity score (0-100)
        
    Returns:
        List of models in priority order
    """
    # Default/fallback priority for general messages
    default_priority = ['gpt-4', 'claude-3', 'gpt-4o', 'claude-3-opus']
    
    # Get query characteristics
    message_lower = message.lower()
    
    # Code-focused routing
    if re.search(r'(code|function|program|algorithm|bug|debug|class|method|api)', message_lower):
        if complexity_score > 70:
            return ['gpt-4', 'claude-3-opus', 'gpt-4o', 'claude-3']
        else:
            return ['gpt-4', 'gpt-4o', 'claude-3', 'claude-3-opus']
    
    # Math/Science routing
    elif re.search(r'(math|equation|calculate|formula|physics|chemistry|biology|scientific)', message_lower):
        if complexity_score > 65:
            return ['claude-3-opus', 'gpt-4', 'gpt-4o', 'claude-3']
        else:
            return ['gpt-4', 'claude-3-opus', 'gpt-4o', 'claude-3']
    
    # Creative content
    elif re.search(r'(write|creative|story|narrative|poem|song|imagine|design)', message_lower):
        return ['claude-3-opus', 'claude-3', 'gpt-4', 'gpt-4o']
    
    # Business/Strategic
    elif re.search(r'(business|market|strategy|customer|financial|investment|company)', message_lower):
        return ['gpt-4', 'claude-3-opus', 'claude-3', 'gpt-4o']
    
    # High complexity prioritizes more capable models
    if complexity_score > 75:
        return ['claude-3-opus', 'gpt-4', 'gpt-4o', 'claude-3']
    elif complexity_score > 50:
        return ['gpt-4', 'claude-3-opus', 'gpt-4o', 'claude-3']
    
    # Default fallback
    return default_priority

def _calculate_routing_confidence(message: str, complexity_score: float) -> float:
    """
    Calculate confidence in the routing decision
    
    Args:
        message: User message
        complexity_score: Complexity score (0-100)
        
    Returns:
        Confidence score (0-1)
    """
    # Base confidence inversely related to complexity
    # Very complex queries = less confident in specific routing
    base_confidence = 1.0 - (complexity_score / 200)  # 0.5 to 1.0 range
    
    # Adjust based on query clarity
    clarity_adjustment = 0
    
    # Clear domain indicators increase confidence
    message_lower = message.lower()
    domain_indicators = [
        'code', 'program', 'algorithm', 'function',
        'math', 'calculate', 'equation', 'solve',
        'write', 'create', 'design', 'generate',
        'explain', 'summarize', 'describe', 'detail'
    ]
    
    for indicator in domain_indicators:
        if indicator in message_lower:
            clarity_adjustment += 0.05
            break
    
    # Question mark presence slightly increases confidence
    if '?' in message:
        clarity_adjustment += 0.05
    
    # Very short queries decrease confidence
    if len(message.split()) < 5:
        clarity_adjustment -= 0.1
    
    # Calculate final confidence
    confidence = min(0.95, max(0.5, base_confidence + clarity_adjustment))
    
    return confidence
