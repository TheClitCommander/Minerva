#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model Evaluator for Minerva's Think Tank AI System

This module provides functions for evaluating the quality of AI model responses
and comparing multiple responses to select the best one.
"""

import logging
import re
import time
import json
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelEvaluator:
    """
    Evaluates and compares responses from different AI models.
    """
    
    def __init__(self):
        """Initialize the evaluator with default evaluation criteria."""
        self.evaluation_history = {}
        
    def evaluate_response_quality(self, 
                                 response: str, 
                                 query: str, 
                                 model_name: str = None,
                                 query_complexity: int = 5,
                                 model_capabilities: Dict[str, Any] = None) -> float:
        """
        Evaluate the quality of a response based on multiple criteria.
        
        Args:
            response: The AI model's response text
            query: The original user query
            model_name: Optional name of the model for logging
            query_complexity: Estimated complexity of the query (1-10)
            model_capabilities: Dictionary of model capabilities
            
        Returns:
            float: Quality score between 0.0 and 1.0
        """
        if not response or not query:
            logger.warning(f"Empty response or query received for evaluation")
            return 0.0
            
        # Start timing the evaluation
        start_time = time.time()
        
        # Initialize scores for different aspects
        coherence_score = self._evaluate_coherence(response)
        relevance_score = self._evaluate_relevance(response, query)
        completeness_score = self._evaluate_completeness(response, query)
        accuracy_score = self._evaluate_accuracy(response)
        formatting_score = self._evaluate_formatting(response)
        
        # Log individual scores for debugging
        if model_name:
            logger.info(f"Model {model_name} scores - Coherence: {coherence_score:.2f}, "
                      f"Relevance: {relevance_score:.2f}, Completeness: {completeness_score:.2f}, "
                      f"Accuracy: {accuracy_score:.2f}, Formatting: {formatting_score:.2f}")
        
        # Weight the scores based on query complexity
        # More complex queries prioritize accuracy and completeness
        if query_complexity >= 7:
            weights = {
                'coherence': 0.2,
                'relevance': 0.25,
                'completeness': 0.3,
                'accuracy': 0.2,
                'formatting': 0.05
            }
        else:
            weights = {
                'coherence': 0.25,
                'relevance': 0.3,
                'completeness': 0.2,
                'accuracy': 0.15,
                'formatting': 0.1
            }
            
        # Calculate weighted score
        total_score = (
            weights['coherence'] * coherence_score +
            weights['relevance'] * relevance_score +
            weights['completeness'] * completeness_score +
            weights['accuracy'] * accuracy_score +
            weights['formatting'] * formatting_score
        )
        
        # Apply more sophisticated model-specific adjustments based on capabilities
        if model_capabilities:
            capability_boost = 0.0
            query_lower = query.lower()
            
            # Technical/coding queries
            if any(term in query_lower for term in ['code', 'programming', 'function', 'algorithm', 'technical', 'syntax', 'error']):
                if model_capabilities.get('technical_expertise', 0) > 0.7:
                    capability_boost += 0.05 * model_capabilities.get('technical_expertise', 0)
            
            # Creative/writing queries
            if any(term in query_lower for term in ['write', 'story', 'creative', 'poem', 'essay', 'describe']):
                if model_capabilities.get('creative_writing', 0) > 0.7:
                    capability_boost += 0.05 * model_capabilities.get('creative_writing', 0)
            
            # Reasoning/analysis queries
            if any(term in query_lower for term in ['explain', 'analyze', 'compare', 'why', 'reason', 'cause']):
                if model_capabilities.get('reasoning', 0) > 0.7:
                    capability_boost += 0.05 * model_capabilities.get('reasoning', 0)
            
            # Math/logic queries
            if any(term in query_lower for term in ['math', 'calculate', 'solve', 'equation', 'formula', 'logic']):
                if model_capabilities.get('mathematical_reasoning', 0) > 0.7:
                    capability_boost += 0.05 * model_capabilities.get('mathematical_reasoning', 0)
                    
            # Apply the boost with a cap to prevent excessive adjustment
            total_score += min(capability_boost, 0.15)
        
        # Cap score at 1.0
        total_score = min(total_score, 1.0)
        
        # Record evaluation time
        evaluation_time = time.time() - start_time
        logger.debug(f"Evaluation completed in {evaluation_time:.2f}s with score {total_score:.2f}")
        
        # Record this evaluation for later analysis
        if model_name:
            self.evaluation_history[f"{model_name}_{time.time()}"] = {
                'query': query,
                'response_brief': response[:100] + "..." if len(response) > 100 else response,
                'score': total_score,
                'evaluation_time': evaluation_time,
                'individual_scores': {
                    'coherence': coherence_score,
                    'relevance': relevance_score,
                    'completeness': completeness_score,
                    'accuracy': accuracy_score,
                    'formatting': formatting_score
                }
            }
            
        return total_score
        
    def _evaluate_coherence(self, response: str) -> float:
        """Evaluate how coherent and well-structured the response is."""
        # Check for general coherence indicators
        score = 0.7  # Start with a baseline score
        
        # Check for nonsensical or repetitive text patterns
        if re.search(r'(?i)(\b\w+\b)(\s+\1\b){3,}', response):  # Excessive repetition
            score -= 0.2
            
        # Check for proper paragraph structure and transitions
        paragraphs = response.split('\n\n')
        if len(paragraphs) >= 2:
            score += 0.1  # Good structure with multiple paragraphs
        
        # Check for extreme brevity which may indicate a poor response
        if len(response) < 50:
            score -= 0.2
            
        # Check for proper sentence structure
        sentences = re.split(r'[.!?]+', response)
        valid_sentences = [s for s in sentences if len(s.strip()) > 10]
        if valid_sentences and len(valid_sentences) / len(sentences) > 0.8:
            score += 0.1
            
        return max(0.0, min(score, 1.0))  # Ensure score is between 0 and 1
    
    def _evaluate_relevance(self, response: str, query: str) -> float:
        """Evaluate how relevant the response is to the original query."""
        # Basic relevance check based on keyword matching
        score = 0.5  # Start with a moderate baseline
        
        # Extract main keywords from the query
        query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
        if not query_words:
            return score  # If no significant words, return baseline
            
        # Check if key query terms appear in the response
        response_lower = response.lower()
        matched_words = sum(1 for word in query_words if word in response_lower)
        term_match_score = matched_words / len(query_words) if query_words else 0
        
        # Adjust score based on term matching
        score += 0.4 * term_match_score
        
        # Check for direct acknowledgment of the query
        if any(query_term.lower() in response_lower[:150] for query_term in query.split()[:3]):
            score += 0.1
            
        return max(0.0, min(score, 1.0))  # Ensure score is between 0 and 1
    
    def _evaluate_completeness(self, response: str, query: str) -> float:
        """Evaluate how completely the response addresses all aspects of the query."""
        score = 0.6  # Start with a somewhat favorable baseline
        
        # Check for question words in the query
        question_words = ['what', 'why', 'how', 'when', 'where', 'who', 'which']
        query_questions = [word for word in question_words if word in query.lower().split()]
        
        # If question words are present, check if they're addressed
        if query_questions:
            # For each question word, check if there's content that seems to address it
            for q_word in query_questions:
                # Simple heuristic: look for sentences that might be responding to the question
                if q_word == 'how' and re.search(r'(?i)(steps|process|method|way to|approach)', response):
                    score += 0.1
                elif q_word == 'why' and re.search(r'(?i)(because|reason|due to|as a result)', response):
                    score += 0.1
                elif q_word == 'what' and re.search(r'(?i)(is|are|refers to|means|defined as)', response):
                    score += 0.1
                    
        # Check if the response has a substantial length relative to query complexity
        relative_length_score = min(len(response) / (len(query) * 3), 1.0) * 0.2
        score += relative_length_score
        
        # Penalize very short responses
        if len(response) < 100 and len(query) > 50:
            score -= 0.2
            
        return max(0.0, min(score, 1.0))  # Ensure score is between 0 and 1
    
    def _evaluate_accuracy(self, response: str) -> float:
        """
        Evaluate the factual accuracy and logical consistency of the response.
        
        Note: This is a simplified approximation as true factual verification
        would require external knowledge sources.
        """
        score = 0.7  # Start with a somewhat favorable baseline
        
        # Check for hedging or uncertainty indicators which might suggest inaccuracy
        uncertainty_patterns = [
            r'(?i)\bmight be\b', r'(?i)\bcould be\b', r'(?i)\bperhaps\b',
            r'(?i)\bpossibly\b', r'(?i)\bi think\b', r'(?i)\bprobably\b'
        ]
        
        uncertainty_count = sum(1 for pattern in uncertainty_patterns if re.search(pattern, response))
        
        # Minor penalization for excessive uncertainty
        if uncertainty_count > 3:
            score -= 0.1
        
        # Check for logical consistency indicators
        consistency_indicators = [
            r'(?i)first.*second.*third', r'(?i)on one hand.*on the other hand',
            r'(?i)however', r'(?i)therefore', r'(?i)consequently', r'(?i)in conclusion'
        ]
        
        consistency_count = sum(1 for indicator in consistency_indicators if re.search(indicator, response))
        
        # Reward logical structure
        score += min(consistency_count * 0.05, 0.15)
        
        return max(0.0, min(score, 1.0))  # Ensure score is between 0 and 1
    
    def _evaluate_formatting(self, response: str) -> float:
        """Evaluate how well-formatted the response is."""
        score = 0.5  # Start with a moderate baseline
        
        # Check for proper use of paragraphs
        paragraphs = response.split('\n\n')
        if len(paragraphs) > 1:
            score += 0.1
            
        # Check for proper use of markdown (if any)
        if re.search(r'(?i)(#+\s|\*\*|\*|\`|---|>|\[.*\]\(.*\))', response):
            score += 0.1
            
        # Check for proper use of lists
        if re.search(r'(?m)^\s*(-|\d+\.)\s', response):
            score += 0.1
            
        # Check for code blocks if applicable
        if re.search(r'```[\s\S]*?```', response):
            score += 0.1
            
        # Penalize ALL CAPS text (unless in code blocks)
        non_code_content = re.sub(r'```[\s\S]*?```', '', response)
        if re.search(r'[A-Z]{5,}', non_code_content):
            score -= 0.1
            
        return max(0.0, min(score, 1.0))  # Ensure score is between 0 and 1
        
    def compare_responses(self, 
                         responses: Dict[str, Any], 
                         query: str,
                         query_tags: List[str] = None,
                         query_complexity: int = 5,
                         model_capabilities: Dict[str, Dict[str, float]] = None,
                         detailed_scores: bool = True,
                         evaluation_criteria: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Compare multiple model responses and select the best one with enhanced evaluation criteria.
        Enhanced to support the Think Tank approach with more detailed scoring.
        
        Args:
            responses: Dictionary mapping model names to their responses (can be strings or objects)
            query: The original user query
            query_tags: List of tags describing the query type
            query_complexity: Estimated complexity of the query (1-10)
            model_capabilities: Dictionary mapping model names to their capabilities with scores
            detailed_scores: Whether to include detailed scoring breakdowns
            evaluation_criteria: Custom weights for evaluation criteria
            
        Returns:
            Dict with best_model, best_response, scores, and detailed evaluation metadata
        """
        if not responses:
            logger.warning("No responses provided for comparison")
            return {
                "best_model": None,
                "best_response": "I'm sorry, but I don't have a response for your query at this time.",
                "quality_score": 0.0,
                "all_scores": {},
                "detailed_scores": {}
            }
            
        start_time = time.time()
        logger.info(f"[THINK TANK] Comparing responses from {len(responses)} models")
        
        # Set default evaluation criteria if none provided
        if not evaluation_criteria:
            evaluation_criteria = {
                'relevance': 0.3,    # How relevant is the response to the query
                'coherence': 0.2,    # How well-structured and logical is the response
                'accuracy': 0.25,    # How factually accurate is the response
                'completeness': 0.15, # How thorough is the response
                'formatting': 0.1     # How well-formatted is the response
            }
        
        # Evaluate each response with detailed criteria
        scores = {}
        detailed_score_results = {}
        
        for model_name, response_data in responses.items():
            # Extract the actual response text (handles both string and object responses)
            if isinstance(response_data, str):
                response_text = response_data
            elif isinstance(response_data, dict) and 'content' in response_data:
                response_text = response_data['content']
            else:
                logger.warning(f"[THINK TANK] Invalid response format for {model_name}")
                continue
                
            # Get this model's capabilities if available
            model_caps = model_capabilities.get(model_name, {}) if model_capabilities else {}
            
            # Calculate detailed scores for each criterion
            detailed_model_scores = {}
            
            # Relevance score - how well the response addresses the query
            relevance_score = self._calculate_relevance_score(response_text, query, query_tags)
            detailed_model_scores['relevance'] = relevance_score
            
            # Coherence score - how well-structured and logical the response is
            coherence_score = self._calculate_coherence_score(response_text)
            detailed_model_scores['coherence'] = coherence_score
            
            # Accuracy score - factual correctness (hard to validate, use model capabilities as proxy)
            accuracy_score = self._calculate_accuracy_score(response_text, model_caps)
            detailed_model_scores['accuracy'] = accuracy_score
            
            # Completeness score - how thorough the response is
            completeness_score = self._calculate_completeness_score(response_text, query_complexity)
            detailed_model_scores['completeness'] = completeness_score
            
            # Formatting score - how well-formatted the response is
            formatting_score = self._calculate_formatting_score(response_text)
            detailed_model_scores['formatting'] = formatting_score
            
            # Calculate weighted score based on evaluation criteria
            weighted_score = sum(score * evaluation_criteria.get(criterion, 0.2) 
                                for criterion, score in detailed_model_scores.items())
            
            # Adjust score based on model capabilities and query tags match
            capability_boost = self._calculate_capability_match(model_caps, query_tags)
            adjusted_score = weighted_score * (1 + capability_boost * 0.2)  # Boost up to 20%
            
            # Store scores
            scores[model_name] = min(adjusted_score, 1.0)  # Cap at 1.0
            detailed_score_results[model_name] = detailed_model_scores
            
            logger.info(f"[THINK TANK] Model {model_name} score: {scores[model_name]:.2f}")
            
        # Find the best model and response
        best_model = max(scores.items(), key=lambda x: x[1])[0] if scores else None
        
        # Get the best response text
        if best_model:
            if isinstance(responses[best_model], str):
                best_response = responses[best_model]
            elif isinstance(responses[best_model], dict) and 'content' in responses[best_model]:
                best_response = responses[best_model]['content']
            else:
                best_response = "Unable to retrieve best response text"
            best_score = scores[best_model]
        else:
            best_response = ""
            best_score = 0.0
        
        processing_time = time.time() - start_time
        logger.info(f"[THINK TANK] Selected best response from {best_model} with score {best_score:.2f} "
                   f"in {processing_time:.2f}s")
        
        # Log all scores for analysis
        for model, score in scores.items():
            logger.info(f"[THINK TANK]  - {model}: {score:.2f}")
            if detailed_scores and model in detailed_score_results:
                for criterion, criterion_score in detailed_score_results[model].items():
                    logger.info(f"[THINK TANK]    * {criterion}: {criterion_score:.2f}")
        
        # Prepare response previews for logging (first 100 chars)
        response_previews = {}
        for model_name, response_data in responses.items():
            if isinstance(response_data, str):
                preview = response_data[:100] + "..." if len(response_data) > 100 else response_data
            elif isinstance(response_data, dict) and 'content' in response_data:
                preview = response_data['content'][:100] + "..." if len(response_data['content']) > 100 else response_data['content']
            else:
                preview = "[Invalid response format]"
            response_previews[model_name] = preview
            
        # Record this evaluation for future analysis
        evaluation_record = {
            "timestamp": time.time(),
            "query": query,
            "query_tags": query_tags,
            "query_complexity": query_complexity,
            "best_model": best_model,
            "all_scores": scores,
            "detailed_scores": detailed_score_results,
            "processing_time": processing_time,
            "models_compared": list(responses.keys()),
            "response_previews": response_previews,
            "quality_score": best_score
        }
        
        # Store in evaluation history (limited to last 100 evaluations)
        eval_id = str(int(time.time() * 1000))  # Timestamp as ID
        self.evaluation_history[eval_id] = evaluation_record
        if len(self.evaluation_history) > 100:
            oldest_key = min(self.evaluation_history.keys())
            del self.evaluation_history[oldest_key]
            
        # Send to insights manager for permanent storage
        try:
            from web.model_insights_manager import model_insights_manager
            logger.info(f"[THINK TANK] Sending evaluation to insights manager for permanent storage")
            # Add the evaluation ID explicitly
            evaluation_record['evaluation_id'] = eval_id
            # Print the evaluation data for debugging
            logger.info(f"[THINK TANK DEBUG] Evaluation data: {json.dumps({k: v for k, v in evaluation_record.items() if k != 'response_previews'}, indent=2)}")
            # Record the evaluation
            result_id = model_insights_manager.record_evaluation(evaluation_record)
            logger.info(f"[THINK TANK] Evaluation recorded with ID: {result_id}")
        except Exception as e:
            logger.error(f"[THINK TANK] Failed to send evaluation to insights manager: {str(e)}")
            import traceback
            logger.error(f"[THINK TANK] Error details: {traceback.format_exc()}")
            
        # Return comprehensive results
        result = {
            "best_model": best_model,
            "best_response": best_response,
            "quality_score": best_score,
            "all_scores": scores,
            "query_complexity": query_complexity,
            "query_tags": query_tags,
            "processing_time": processing_time,
            "timestamp": time.time(),
            "evaluation_id": eval_id,
            "models_compared": list(responses.keys()),
            "response_previews": response_previews
        }
        
        # Include detailed scores if requested
        if detailed_scores:
            result["detailed_scores"] = detailed_score_results
            
        return result
        


    def _calculate_relevance_score(self, response: str, query: str, query_tags: List[str] = None) -> float:
        """
        Calculate how relevant the response is to the query.
        
        Args:
            response: The response text to evaluate
            query: The original query
            query_tags: List of tags describing the query
            
        Returns:
            Float score between 0 and 1
        """
        score = 0.5  # Start with a neutral score
        
        # Check if response contains key terms from the query
        query_terms = set(re.findall(r'\w+', query.lower()))
        query_terms = {term for term in query_terms if len(term) > 3}  # Only significant terms
        
        if not query_terms:
            return 0.7  # Can't evaluate properly, return a reasonable default
            
        response_lower = response.lower()
        matched_terms = sum(1 for term in query_terms if term in response_lower)
        term_match_ratio = matched_terms / len(query_terms) if query_terms else 0
        
        # More matched terms = higher relevance
        score += term_match_ratio * 0.3
        
        # Check for query tag matches in the response
        if query_tags:
            tag_matches = sum(1 for tag in query_tags if tag.lower() in response_lower)
            tag_match_ratio = tag_matches / len(query_tags)
            score += tag_match_ratio * 0.2
        
        # Check if the response directly references the query
        if any(phrase in response_lower for phrase in [
            "you asked", "your question", "your query", "regarding your", 
            "to answer your", "in response to your"
        ]):
            score += 0.1
        
        # Check for specific domain terms based on query tags
        domain_terms = []
        if query_tags:
            if "programming" in query_tags or "code" in query_tags:
                domain_terms = ["function", "class", "variable", "method", "parameter", "return", "import"]
            elif "math" in query_tags:
                domain_terms = ["equation", "formula", "calculation", "solve", "proof", "theorem"]
            elif "science" in query_tags:
                domain_terms = ["experiment", "theory", "hypothesis", "observation", "evidence"]
                
            if domain_terms:
                domain_match = sum(1 for term in domain_terms if term in response_lower)
                domain_ratio = min(domain_match / len(domain_terms), 1.0)
                score += domain_ratio * 0.1
        
        return max(0.0, min(score, 1.0))  # Ensure score is between 0 and 1
    
    def _calculate_coherence_score(self, response: str) -> float:
        """
        Calculate how well-structured and logical the response is.
        
        Args:
            response: The response text to evaluate
            
        Returns:
            Float score between 0 and 1
        """
        score = 0.5  # Start with a neutral score
        
        # Check for clear structure with sections
        has_sections = bool(re.search(r'#+\s+.+|\n\s*(-|\d+\.)', response))
        if has_sections:
            score += 0.2
        
        # Check for proper paragraph breaks
        paragraphs = [p for p in response.split('\n\n') if p.strip()]
        if len(paragraphs) >= 2:
            score += 0.1
        
        # Check for logical connectors
        logical_connectors = ["therefore", "consequently", "thus", "hence", "as a result", 
                              "first", "second", "third", "finally", "in conclusion", 
                              "additionally", "furthermore", "moreover", "however", "nevertheless"]
        
        connector_count = sum(1 for connector in logical_connectors 
                             if re.search(r'\b' + connector + r'\b', response.lower()))
        
        # More connectors = better coherence (up to a point)
        connector_score = min(connector_count / 3, 1.0) * 0.2
        score += connector_score
        
        # Penalize excessively short or long sentences
        sentences = re.split(r'[.!?]\s+', response)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Ideal sentence length: 10-25 words
        if 10 <= avg_sentence_length <= 25:
            score += 0.1
        elif avg_sentence_length > 35 or avg_sentence_length < 5:
            score -= 0.1
        
        return max(0.0, min(score, 1.0))  # Ensure score is between 0 and 1
    
    def _calculate_accuracy_score(self, response: str, model_capabilities: Dict[str, float]) -> float:
        """
        Estimate the factual accuracy of the response (difficult to validate automatically).
        Uses model capabilities as a proxy for accuracy in different domains.
        
        Args:
            response: The response text to evaluate
            model_capabilities: Dictionary of model capabilities
            
        Returns:
            Float score between 0 and 1
        """
        score = 0.6  # Start with a moderate score
        
        # Use model capabilities as proxy for accuracy in different domains
        if model_capabilities:
            # Technical accuracy
            if 'technical_expertise' in model_capabilities:
                score += model_capabilities['technical_expertise'] * 0.2
                
            # Factual accuracy
            if 'factual' in model_capabilities:
                score += model_capabilities['factual'] * 0.2
                
            # Analytical accuracy
            if 'analytical' in model_capabilities:
                score += model_capabilities['analytical'] * 0.1
        
        # Check for hedging language that indicates uncertainty (slight penalty)
        hedging_phrases = ["I think", "probably", "might be", "could be", "I believe", 
                          "possibly", "perhaps", "may be", "it seems", "appears to"]
        
        hedging_count = sum(1 for phrase in hedging_phrases 
                           if re.search(r'\b' + phrase + r'\b', response.lower()))
        
        # Too much hedging suggests uncertainty
        if hedging_count > 3:
            score -= 0.1
        
        # Check for references to authoritative sources (positive indicator)
        reference_phrases = ["according to", "research shows", "studies indicate", 
                            "evidence suggests", "data from", "experts say"]
        
        ref_count = sum(1 for phrase in reference_phrases 
                       if re.search(r'\b' + phrase + r'\b', response.lower()))
        
        if ref_count > 0:
            score += min(ref_count * 0.05, 0.15)
        
        return max(0.0, min(score, 1.0))  # Ensure score is between 0 and 1
    
    def _calculate_completeness_score(self, response: str, query_complexity: int) -> float:
        """
        Calculate how thorough and complete the response is given the query complexity.
        
        Args:
            response: The response text to evaluate
            query_complexity: Estimated complexity of the query (1-10)
            
        Returns:
            Float score between 0 and 1
        """
        score = 0.5  # Start with a neutral score
        
        # Analyze response length relative to query complexity
        word_count = len(response.split())
        
        # For complex queries, longer responses are generally better (up to a point)
        # For simple queries, concise responses are better
        if query_complexity >= 7:  # Complex query
            # For complex queries, expect 150-400 words
            if word_count < 100:
                score -= 0.2  # Too short for a complex topic
            elif 150 <= word_count <= 400:
                score += 0.2  # Good length for a complex topic
            elif word_count > 600:
                score -= 0.1  # Excessively verbose
        elif query_complexity <= 3:  # Simple query
            # For simple queries, expect 50-150 words
            if 50 <= word_count <= 150:
                score += 0.2  # Good length for a simple topic
            elif word_count > 250:
                score -= 0.2  # Too verbose for a simple query
        else:  # Moderate complexity
            # For moderately complex queries, expect 100-250 words
            if 100 <= word_count <= 250:
                score += 0.2  # Good length for a moderately complex topic
        
        # Check for comprehensive coverage (multiple angles/aspects)
        # Look for section headings, numbered points, or bullet points
        sections = re.findall(r'#+\s+.+|\n\s*(-|\d+\.)', response)
        section_count = len(sections)
        
        if query_complexity >= 5 and section_count >= 3:
            score += 0.15  # Good structure for complex topics
        elif query_complexity < 5 and section_count >= 1:
            score += 0.1   # Some structure for simpler topics
        
        # Check for examples, which enhance completeness
        examples = re.findall(r'\bexample\b|\bfor instance\b|\bsuch as\b|\be\.g\.\b|```', response.lower())
        if examples:
            example_score = min(len(examples) * 0.05, 0.15)
            score += example_score
        
        return max(0.0, min(score, 1.0))  # Ensure score is between 0 and 1
    
    def _calculate_formatting_score(self, response: str) -> float:
        """
        Calculate how well-formatted the response is with proper markdown and structure.
        
        Args:
            response: The response text to evaluate
            
        Returns:
            Float score between 0 and 1
        """
        score = 0.5  # Start with a neutral score
        
        # Check for headings
        if re.search(r'#+\s+.+', response):
            score += 0.1
        
        # Check for code blocks or inline code
        if re.search(r'```\w*\n[\s\S]*?```|`[^`]+`', response):
            score += 0.1
        
        # Check for lists (ordered or unordered)
        if re.search(r'\n\s*(-|\d+\.)\s+', response):
            score += 0.1
        
        # Check for proper formatting of links
        if re.search(r'\[.+?\]\(.+?\)', response):
            score += 0.05
        
        # Check for proper use of emphasis (bold, italic)
        if re.search(r'\*\*.*?\*\*|\*.*?\*|__.*?__|_.*?_', response):
            score += 0.05
        
        # Check for consistent paragraph spacing
        paragraphs = response.split('\n\n')
        if len(paragraphs) > 1 and all(p.strip() for p in paragraphs):
            score += 0.1
        
        # Penalize for shouting (ALL CAPS) outside of headings/code
        if re.search(r'\b[A-Z]{5,}\b', re.sub(r'```[\s\S]*?```|#+\s+.+', '', response)):
            score -= 0.15
        
        return max(0.0, min(score, 1.0))  # Ensure score is between 0 and 1
        
    def _calculate_capability_match(self, model_capabilities: Dict[str, float], query_tags: List[str]) -> float:
        """
        Calculate how well the model's capabilities match the query requirements.
        
        Args:
            model_capabilities: Dictionary of model capabilities and their strengths
            query_tags: List of tags describing the query
            
        Returns:
            Float score between 0 and 1 representing the match quality
        """
        if not model_capabilities or not query_tags:
            return 0.0
            
        # Map query tags to related capabilities
        capability_map = {
            'code': ['code_generation', 'technical_expertise'],
            'programming': ['code_generation', 'technical_expertise'],
            'creative': ['creative', 'conversational'],
            'technical': ['technical_expertise', 'analytical'],
            'explain': ['educational', 'coherent', 'structured'],
            'science': ['analytical', 'factual', 'technical_expertise'],
            'math': ['analytical', 'technical_expertise'],
            'summarize': ['concise', 'analytical'],
            'story': ['creative', 'coherent'],
            'brainstorm': ['creative', 'comprehensive'],
            'plan': ['planning', 'structured', 'analytical'],
            'analyze': ['analytical', 'factual', 'comprehensive']            
        }
        
        # Calculate capability match score
        total_match = 0.0
        matched_tags = 0
        
        for tag in query_tags:
            tag = tag.lower()
            if tag in capability_map:
                related_capabilities = capability_map[tag]
                capability_scores = [model_capabilities.get(cap, 0.0) for cap in related_capabilities]
                
                # Take the best capability score for this tag
                if capability_scores:
                    tag_score = max(capability_scores)
                    total_match += tag_score
                    matched_tags += 1
        
        # Calculate average match score
        if matched_tags > 0:
            return total_match / matched_tags
        else:
            return 0.0
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """
        Retrieve statistics and insights from the model evaluations.
        
        Returns:
            Dict containing various statistics about model performance in the think tank.
        """
        if not self.evaluation_history:
            return {
                "total_evaluations": 0,
                "models_evaluated": [],
                "average_score": 0,
                "evaluation_count_by_model": {},
                "top_performing_models": [],
                "recent_evaluations": [],
                "think_tank_stats": {
                    "evaluations": 0,
                    "improvement": 0,
                    "successful_selections": 0
                }
            }
            
        # Count evaluations by model
        model_counts = {}
        model_scores = {}
        tag_performance = {}
        think_tank_evaluations = []
        
        for eval_id, eval_data in self.evaluation_history.items():
            model_name = eval_id.split('_')[0]  # Extract model name from the evaluation ID
            
            # Count evaluations per model
            if model_name not in model_counts:
                model_counts[model_name] = 0
                model_scores[model_name] = []
                
            model_counts[model_name] += 1
            model_scores[model_name].append(eval_data['score'])
            
            # Track query tag performance if available
            if 'query_tags' in eval_data:
                for tag in eval_data['query_tags']:
                    if tag not in tag_performance:
                        tag_performance[tag] = {
                            'total_score': 0,
                            'count': 0,
                            'best_model': None,
                            'best_score': 0
                        }
                    
                    tag_performance[tag]['total_score'] += eval_data['score']
                    tag_performance[tag]['count'] += 1
                    
                    if eval_data['score'] > tag_performance[tag]['best_score']:
                        tag_performance[tag]['best_score'] = eval_data['score']
                        tag_performance[tag]['best_model'] = model_name
            
            # Track think tank evaluations
            if 'comparison_id' in eval_data:
                think_tank_evaluations.append({
                    'id': eval_data['comparison_id'],
                    'model': model_name,
                    'score': eval_data['score'],
                    'selected': eval_data.get('selected', False),
                    'query': eval_data.get('query', '')
                })
        
        # Calculate average scores per model
        average_by_model = {}
        for model, scores in model_scores.items():
            if scores:
                average_by_model[model] = sum(scores) / len(scores)
            else:
                average_by_model[model] = 0
                
        # Calculate tag performance averages
        for tag, data in tag_performance.items():
            if data['count'] > 0:
                data['average_score'] = data['total_score'] / data['count']
                
        # Find top performing models
        top_models = sorted(
            average_by_model.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]  # Top 3 models
        
        # Get recent evaluations for display
        recent_evals = sorted(
            [
                {
                    "id": eval_id,
                    "model": eval_id.split('_')[0],
                    "query": eval_data['query'],
                    "score": eval_data['score'],
                    "response_preview": eval_data.get('response_brief', '')
                }
                for eval_id, eval_data in self.evaluation_history.items()
            ],
            key=lambda x: x["id"],  # Sort by evaluation ID (which contains timestamp)
            reverse=True
        )[:10]  # Most recent 10 evaluations
        
        # Calculate overall stats
        all_scores = [eval_data['score'] for eval_data in self.evaluation_history.values()]
        average_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        # Process think tank stats
        think_tank_stats = {
            "evaluations": 0,
            "improvement": 0,
            "successful_selections": 0,
            "comparisons": []
        }
        
        # Group by comparison ID
        comparison_groups = {}
        for eval_data in think_tank_evaluations:
            comp_id = eval_data.get('id')
            if not comp_id:
                continue
                
            if comp_id not in comparison_groups:
                comparison_groups[comp_id] = []
                
            comparison_groups[comp_id].append(eval_data)
        
        # Calculate improvement for each group
        for comp_id, evaluations in comparison_groups.items():
            if len(evaluations) <= 1:
                continue
                
            think_tank_stats["evaluations"] += 1
            
            # Find selected model
            selected = next((e for e in evaluations if e.get('selected')), None)
            if not selected:
                continue
                
            # Calculate average of all scores
            avg_score = sum(e.get('score', 0) for e in evaluations) / len(evaluations)
            
            # Was the selected model better than average?
            if selected.get('score', 0) > avg_score:
                think_tank_stats["successful_selections"] += 1
                
                # Calculate percentage improvement
                improvement = ((selected.get('score', 0) / avg_score) - 1) * 100
                think_tank_stats["improvement"] += improvement
                
                # Add to comparisons list
                think_tank_stats["comparisons"].append({
                    "id": comp_id,
                    "selected_model": selected.get('model'),
                    "improvement": round(improvement, 1),
                    "query": selected.get('query', '')[:100],
                    "candidate_models": [e.get('model') for e in evaluations]
                })
        
        # Calculate average improvement
        if think_tank_stats["successful_selections"] > 0:
            think_tank_stats["improvement"] = round(
                think_tank_stats["improvement"] / think_tank_stats["successful_selections"], 1
            )
        
        return {
            "total_evaluations": len(self.evaluation_history),
            "models_evaluated": list(model_counts.keys()),
            "average_score": average_score,
            "average_score_by_model": average_by_model,
            "evaluation_count_by_model": model_counts,
            "top_performing_models": top_models,
            "recent_evaluations": recent_evals,
            "query_tag_performance": tag_performance,
            "think_tank_stats": think_tank_stats
        }

# Create a singleton instance
evaluator = ModelEvaluator()

def evaluate_response_quality(response, query, **kwargs):
    """Convenience function to access the singleton evaluator."""
    return evaluator.evaluate_response_quality(response, query, **kwargs)
    
def compare_responses(responses, query, **kwargs):
    """Convenience function to access the singleton evaluator."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Think Tank comparing {len(responses)} responses for query: {query[:100]}...")
    logger.info(f"Models being compared: {list(responses.keys())}")
    result = evaluator.compare_responses(responses, query, **kwargs)
    logger.info(f"Think Tank comparison result: {result}")
    return result
