"""
Response Blender Module

Handles blending of responses from multiple AI models.
Implements specialized blending strategies for different query types.
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def blend_responses(
    responses: Dict[str, str], 
    rankings: List[Dict[str, Any]], 
    query_tags: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Blend responses from multiple models based on their rankings and query type
    
    Args:
        responses: Dict mapping model names to response text
        rankings: Ranked list of models with scores
        query_tags: Query classification tags
        
    Returns:
        Dict containing blended response and metadata
    """
    if not responses or not rankings:
        logger.warning("No responses or rankings to blend")
        # If we have at least one response but no rankings, use the first response
        if responses:
            model_name = next(iter(responses))
            return {
                'blended_response': responses[model_name],
                'blend_method': 'single_model',
                'contributing_models': [model_name],
                'sections': []
            }
        return {
            'blended_response': '',
            'blend_method': 'none',
            'contributing_models': [],
            'sections': []
        }
    
    # Get query type from tags
    if query_tags is None:
        query_tags = {}
    
    domains = query_tags.get('domains', [])
    request_types = query_tags.get('request_types', [])
    
    # Create ranked_responses dict for easier access
    ranked_responses = {}
    for rank_info in rankings:
        model = rank_info['model']
        if model in responses:
            ranked_responses[model] = {
                'text': responses[model],
                'score': rank_info['score'],
                'rank': len(ranked_responses)
            }
    
    # Choose blending strategy based on query type
    if 'ai' in domains:
        # Use a specialized AI/ML blending strategy
        result = blend_ai_responses(ranked_responses)
    elif 'comparison' in request_types:
        result = blend_comparison_responses(ranked_responses)
    elif 'code' in domains or 'technical' in request_types or 'data' in domains:
        result = blend_technical_responses(ranked_responses)
    elif 'troubleshooting' in request_types or 'optimization' in request_types:
        # Troubleshooting needs structured, solution-focused responses
        result = blend_technical_responses(ranked_responses)
    elif 'explanation' in request_types:
        result = blend_explanation_responses(ranked_responses)
    else:
        result = blend_general_responses(ranked_responses)
    
    # Log blending result
    logger.info(f"Blended {len(result['contributing_models'])} responses using {result['blend_method']} method")
    
    return result

def blend_comparison_responses(ranked_responses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Blend responses for comparison queries by selecting the most comprehensive comparison
    
    Args:
        ranked_responses: Dict of model -> response info mappings
        
    Returns:
        Dict containing blended response and metadata
    """
    if not ranked_responses:
        return {'blended_response': '', 'blend_method': 'none', 'contributing_models': [], 'sections': []}
    
    # For comparisons, we often want to use the highest quality full response
    # as comparisons are more coherent when kept intact
    models = sorted(ranked_responses.keys(), 
                   key=lambda m: ranked_responses[m]['score'], 
                   reverse=True)
    
    top_model = models[0]
    top_response = ranked_responses[top_model]['text']
    
    # Check if we can enhance with information from other models
    if len(models) > 1:
        # Try to identify comparison sections in top response
        sections = _identify_comparison_sections(top_response)
        
        if sections:
            # Look for additional comparison points in other responses
            for model in models[1:3]:  # Check second and third ranked models
                response_text = ranked_responses[model]['text']
                other_sections = _identify_comparison_sections(response_text)
                
                # Add any new sections not already covered
                for section in other_sections:
                    if all(section['title'] not in s['title'] for s in sections):
                        sections.append(section)
            
            # If we found additional sections, blend them in
            if len(sections) > len(_identify_comparison_sections(top_response)):
                # Build a new response with all sections
                blended_text = _build_comparison_response(sections)
                
                return {
                    'blended_response': blended_text,
                    'blend_method': 'enhanced_comparison',
                    'contributing_models': models[:3],
                    'sections': [{'title': s['title'], 'source_model': s.get('source_model', top_model)} 
                                for s in sections]
                }
    
    # If we couldn't enhance it or there's only one model, use the top response
    return {
        'blended_response': top_response,
        'blend_method': 'top_model',
        'contributing_models': [top_model],
        'sections': []
    }

def blend_technical_responses(ranked_responses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Blend responses for technical queries, prioritizing code quality and explanations
    
    Args:
        ranked_responses: Dict of model -> response info mappings
        
    Returns:
        Dict containing blended response and metadata
    """
    if not ranked_responses:
        return {'blended_response': '', 'blend_method': 'none', 'contributing_models': [], 'sections': []}
    
    models = sorted(ranked_responses.keys(), 
                    key=lambda m: ranked_responses[m]['score'], 
                    reverse=True)
    
    # Extract code blocks from each response
    code_blocks = {}
    explanations = {}
    
    for model in models:
        response_text = ranked_responses[model]['text']
        
        # Extract code blocks
        blocks = _extract_code_blocks(response_text)
        if blocks:
            code_blocks[model] = blocks
        
        # Extract explanations (text outside code blocks)
        expl = _extract_explanation_text(response_text)
        if expl:
            explanations[model] = expl
    
    # If no code blocks found, just use top response
    if not code_blocks:
        top_model = models[0]
        return {
            'blended_response': ranked_responses[top_model]['text'],
            'blend_method': 'top_model',
            'contributing_models': [top_model],
            'sections': []
        }
    
    # Choose best code blocks
    # (In a full implementation, we would evaluate code quality)
    best_code_model = next(iter(code_blocks))
    best_code = code_blocks[best_code_model]
    
    # Choose best explanation
    best_expl_model = next(iter(explanations)) if explanations else best_code_model
    best_explanation = explanations.get(best_expl_model, "")
    
    # Blend code and explanation
    blended_text = _build_technical_response(best_code, best_explanation)
    
    return {
        'blended_response': blended_text,
        'blend_method': 'code_explanation_blend',
        'contributing_models': list(set([best_code_model, best_expl_model])),
        'sections': [
            {'title': 'Code', 'source_model': best_code_model},
            {'title': 'Explanation', 'source_model': best_expl_model}
        ]
    }

def blend_explanation_responses(ranked_responses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Blend responses for explanation queries, combining the most comprehensive parts
    
    Args:
        ranked_responses: Dict of model -> response info mappings
        
    Returns:
        Dict containing blended response and metadata
    """
    if not ranked_responses:
        return {'blended_response': '', 'blend_method': 'none', 'contributing_models': [], 'sections': []}
    
    models = sorted(ranked_responses.keys(), 
                    key=lambda m: ranked_responses[m]['score'], 
                    reverse=True)
    
    # If only one model, just use it
    if len(models) == 1:
        model = models[0]
        return {
            'blended_response': ranked_responses[model]['text'],
            'blend_method': 'single_model',
            'contributing_models': [model],
            'sections': []
        }
    
    # Extract sections from each response
    sections_by_model = {}
    for model in models[:3]:  # Consider top 3 models
        response_text = ranked_responses[model]['text']
        sections = _extract_explanation_sections(response_text)
        if sections:
            sections_by_model[model] = sections
    
    # If couldn't extract sections, use top model
    if not sections_by_model:
        top_model = models[0]
        return {
            'blended_response': ranked_responses[top_model]['text'],
            'blend_method': 'top_model',
            'contributing_models': [top_model],
            'sections': []
        }
    
    # Build a comprehensive set of sections
    all_sections = []
    section_titles = set()
    
    # Start with top model's sections
    top_model = models[0]
    if top_model in sections_by_model:
        for section in sections_by_model[top_model]:
            all_sections.append({
                'title': section['title'],
                'content': section['content'],
                'source_model': top_model
            })
            section_titles.add(section['title'].lower())
    
    # Add unique sections from other models
    for model in models[1:3]:
        if model in sections_by_model:
            for section in sections_by_model[model]:
                # Check if this section is unique
                is_unique = True
                for existing_title in section_titles:
                    if (_similarity(section['title'].lower(), existing_title) > 0.6):
                        is_unique = False
                        break
                
                if is_unique:
                    all_sections.append({
                        'title': section['title'],
                        'content': section['content'],
                        'source_model': model
                    })
                    section_titles.add(section['title'].lower())
    
    # Build the blended response
    blended_text = _build_explanation_response(all_sections)
    contributing_models = list(set(section['source_model'] for section in all_sections))
    
    # Create section metadata
    section_meta = [
        {'title': s['title'], 'source_model': s['source_model']} 
        for s in all_sections
    ]
    
    return {
        'blended_response': blended_text,
        'blend_method': 'section_blend',
        'contributing_models': contributing_models,
        'sections': section_meta
    }

def blend_ai_responses(ranked_responses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Blend responses for AI/ML queries, combining technical accuracy with clear explanations
    
    Args:
        ranked_responses: Dict of model -> response info mappings
        
    Returns:
        Dict containing blended response and metadata
    """
    if not ranked_responses:
        return {'blended_response': '', 'blend_method': 'none', 'contributing_models': [], 'sections': []}
    
    # Sort models by score
    models = sorted(ranked_responses.keys(), 
                   key=lambda m: ranked_responses[m]['score'], 
                   reverse=True)
    
    if len(models) == 1:
        # If only one model, return its response
        model = models[0]
        return {
            'blended_response': ranked_responses[model]['text'],
            'blend_method': 'direct',
            'contributing_models': [model],
            'sections': [{'title': 'Complete Response', 'source_model': model}]
        }
    
    # We'll combine the best parts of the top responses
    # For AI/ML, we want to extract:
    # 1. Core concepts and definitions (from the most factually strong model)
    # 2. Technical details and implementation (from the most technically strong model)
    # 3. Real-world applications and examples (from models with good examples)
    
    # Get the top models (use up to top 3 models)
    top_models = models[:min(3, len(models))]
    
    # Extract sections from each model's response
    all_sections = []
    for model in top_models:
        text = ranked_responses[model]['text']
        sections = _extract_ai_ml_sections(text)
        for section in sections:
            section['source_model'] = model
            all_sections.append(section)
    
    # Sort sections by importance and relevance
    section_type_priority = {
        'introduction': 0,
        'definition': 1,
        'concept': 2,
        'technical': 3,
        'implementation': 4,
        'example': 5,
        'application': 6,
        'limitation': 7,
        'conclusion': 8,
        'other': 9
    }
    
    # Sort by section type and then by the model's ranking
    sorted_sections = sorted(all_sections, key=lambda s: (
        section_type_priority.get(s.get('type', 'other'), 999),
        ranked_responses[s['source_model']]['rank']
    ))
    
    # Deduplicate sections (remove highly similar sections)
    unique_sections = []
    for section in sorted_sections:
        # Check if this section is too similar to any section we've already included
        is_duplicate = False
        for included in unique_sections:
            if section['type'] == included['type'] and _similarity(section['content'], included['content']) > 0.7:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_sections.append(section)
    
    # Build blended response
    blended_response = _build_ai_ml_response(unique_sections)
    
    # Get list of contributing models
    contributing_models = list(set(section['source_model'] for section in unique_sections))
    
    # Prepare output sections for the API response
    output_sections = [{
        'title': section.get('title', f"{section['type'].capitalize()} Section"),
        'source_model': section['source_model']
    } for section in unique_sections]
    
    return {
        'blended_response': blended_response,
        'blend_method': 'ai_ml_specialized',
        'contributing_models': contributing_models,
        'sections': output_sections
    }

def blend_general_responses(ranked_responses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Blend general responses using the highest ranked response as a base
    
    Args:
        ranked_responses: Dict of model -> response info mappings
        
    Returns:
        Dict containing blended response and metadata
    """
    if not ranked_responses:
        return {'blended_response': '', 'blend_method': 'none', 'contributing_models': [], 'sections': []}
    
    # For general queries, often the top model's complete response is best
    models = sorted(ranked_responses.keys(), 
                   key=lambda m: ranked_responses[m]['score'], 
                   reverse=True)
    
    top_model = models[0]
    top_response = ranked_responses[top_model]['text']
    
    # For general queries, we'll just use the top model's response
    # In a more sophisticated implementation, we could try to enhance it
    # with unique points from other responses
    
    return {
        'blended_response': top_response,
        'blend_method': 'top_model',
        'contributing_models': [top_model],
        'sections': []
    }

# Helper functions

def _identify_comparison_sections(text: str) -> List[Dict[str, Any]]:
    """Identify comparison sections in a response"""
    sections = []
    
    # Look for comparison tables
    table_pattern = r'((?:\|[^\n]*\|\n)+)'
    tables = re.findall(table_pattern, text)
    
    for table in tables:
        sections.append({
            'title': 'Comparison Table',
            'content': table,
            'type': 'table'
        })
    
    # Look for sections with headings that contain comparison keywords
    heading_pattern = r'(#{1,3}\s*(.+?)(?:\n|$))(.*?)(?=#{1,3}|\Z)'
    matches = re.findall(heading_pattern, text, re.DOTALL)
    
    for match in matches:
        heading = match[1].strip()
        content = match[0] + match[2]
        
        # Check if it's a comparison section
        comparison_keywords = ['vs', 'versus', 'comparison', 'differ', 'similar', 
                              'advantage', 'disadvantage', 'pro', 'con', 'contrast']
        
        if any(keyword in heading.lower() for keyword in comparison_keywords):
            sections.append({
                'title': heading,
                'content': content,
                'type': 'section'
            })
    
    return sections

def _extract_code_blocks(text: str) -> List[str]:
    """Extract code blocks from text"""
    code_pattern = r'```(?:\w+)?\n(.*?)```'
    return re.findall(code_pattern, text, re.DOTALL)

def _extract_explanation_text(text: str) -> str:
    """Extract explanation text (non-code parts)"""
    # Replace code blocks with placeholders
    code_pattern = r'```(?:\w+)?\n.*?```'
    text_without_code = re.sub(code_pattern, '[CODE_BLOCK]', text, flags=re.DOTALL)
    
    # Remove leading/trailing whitespace
    return text_without_code.strip()

def _extract_explanation_sections(text: str) -> List[Dict[str, Any]]:
    """Extract sections from an explanation response"""
    sections = []
    
    # Look for headings
    heading_pattern = r'(#{1,3}\s*(.+?)(?:\n|$))(.*?)(?=#{1,3}|\Z)'
    matches = re.findall(heading_pattern, text, re.DOTALL)
    
    if matches:
        for match in matches:
            heading = match[1].strip()
            content = match[0] + match[2]
            
            sections.append({
                'title': heading,
                'content': content
            })
    else:
        # No headings, try to split by paragraphs
        paragraphs = text.split('\n\n')
        
        if len(paragraphs) >= 3:
            # Use first paragraph as introduction
            sections.append({
                'title': 'Introduction',
                'content': paragraphs[0]
            })
            
            # Group remaining paragraphs
            for i, para in enumerate(paragraphs[1:], 1):
                if para.strip():
                    # Try to infer a title from content
                    words = para.split()
                    title = ' '.join(words[:min(5, len(words))]) + '...'
                    
                    sections.append({
                        'title': f'Section {i}',
                        'content': para
                    })
    
    return sections

def _build_comparison_response(sections: List[Dict[str, Any]]) -> str:
    """Build a comparison response from sections"""
    # Arrange sections in a logical order
    arranged_sections = sorted(
        sections, 
        key=lambda s: 0 if s['title'].lower() in ('introduction', 'overview') else 1
    )
    
    # Join the sections
    blended_text = ""
    for section in arranged_sections:
        blended_text += section['content'] + '\n\n'
    
    return blended_text.strip()

def _build_technical_response(code_blocks: List[str], explanation: str) -> str:
    """Build a technical response from code blocks and explanation"""
    # Create a structured response
    parts = []
    
    # Extract introduction from explanation (first paragraph)
    intro_match = re.match(r'^(.*?)(\n\n|\Z)', explanation, re.DOTALL)
    if intro_match:
        parts.append(intro_match.group(1))
    
    # Add code blocks with proper formatting
    for i, block in enumerate(code_blocks):
        # If there are multiple blocks, add section headings
        if len(code_blocks) > 1:
            parts.append(f"\n## Code Implementation {i+1}\n")
        
        parts.append(f"```\n{block}\n```")
    
    # Add explanation (excluding intro if we used it)
    if intro_match and len(explanation) > len(intro_match.group(0)):
        remainder = explanation[len(intro_match.group(0)):]
        if remainder.strip():
            parts.append("\n## Explanation\n")
            parts.append(remainder)
    
    return "\n\n".join(parts)

def _build_explanation_response(sections: List[Dict[str, Any]]) -> str:
    """Build an explanation response from sections"""
    # Arrange sections in a logical order
    ordered_sections = []
    
    # Find intro/overview sections
    intro_sections = [s for s in sections 
                     if any(keyword in s['title'].lower() 
                           for keyword in ['introduction', 'overview', 'summary'])]
    
    # Other sections
    other_sections = [s for s in sections if s not in intro_sections]
    
    # Build the final arrangement
    ordered_sections = intro_sections + other_sections
    
    # Join the sections
    blended_text = ""
    for section in ordered_sections:
        blended_text += section['content'] + '\n\n'
    
    return blended_text.strip()

def _extract_ai_ml_sections(text: str) -> List[Dict[str, Any]]:
    """Extract AI/ML-specific sections from text response"""
    if not text or len(text) < 50:
        return [{'title': 'Complete Response', 'content': text, 'type': 'other'}]
    
    # First, try to extract based on markdown headers
    headers = re.findall(r'#+\s+(.*?)\n', text)
    
    # If we have headers, use them to split the content
    if len(headers) >= 2:
        sections = []
        header_pattern = r'#+\s+(.+?)\n(.+?)(?=\n#+\s+|$)'  
        matches = re.finditer(header_pattern, text, re.DOTALL)
        
        for match in matches:
            title = match.group(1).strip()
            content = match.group(2).strip()
            
            # Determine section type based on title
            section_type = 'other'
            if re.search(r'(introduction|overview|background|about)', title.lower()):
                section_type = 'introduction'
            elif re.search(r'(definition|what is|meaning)', title.lower()):
                section_type = 'definition'
            elif re.search(r'(concept|principle|theory|how it works)', title.lower()):
                section_type = 'concept'
            elif re.search(r'(technical|algorithm|architecture|component|structure)', title.lower()):
                section_type = 'technical'
            elif re.search(r'(implementation|code|pseudocode|process)', title.lower()):
                section_type = 'implementation'
            elif re.search(r'(example|case study|demonstration)', title.lower()):
                section_type = 'example'
            elif re.search(r'(application|use case|industry|use|usage)', title.lower()):
                section_type = 'application'
            elif re.search(r'(limitation|challenge|drawback|issue|problem)', title.lower()):
                section_type = 'limitation'
            elif re.search(r'(conclusion|summary|takeaway)', title.lower()):
                section_type = 'conclusion'
            
            sections.append({'title': title, 'content': content, 'type': section_type})
        
        if sections:
            return sections
    
    # Fallback: look for key AI/ML concepts and split based on content
    sections = []
    
    # Look for definitions or introductions
    intro_match = re.search(r'(?:^|\n\n)([^\n]+(?:\n[^\n]+){0,3}?(?:neural network|deep learning|machine learning|ai|artificial intelligence).{50,500}?)(?:\n\n|$)', text, re.IGNORECASE)
    if intro_match:
        sections.append({'title': 'Introduction', 'content': intro_match.group(1), 'type': 'introduction'})
    
    # Look for technical details
    tech_match = re.search(r'(?:\n\n)([^\n]+(?:\n[^\n]+){0,10}?(?:algorithm|architecture|layer|neuron|parameter|hyperparameter|training|gradient|backpropagation).{100,800}?)(?:\n\n|$)', text, re.IGNORECASE)
    if tech_match:
        sections.append({'title': 'Technical Details', 'content': tech_match.group(1), 'type': 'technical'})
    
    # Look for implementation examples
    impl_match = re.search(r'(?:\n\n)([^\n]+(?:\n[^\n]+){0,15}?(?:implement|code|example|tensorflow|pytorch|keras|framework).{100,1000}?)(?:\n\n|$)', text, re.IGNORECASE)
    if impl_match:
        sections.append({'title': 'Implementation', 'content': impl_match.group(1), 'type': 'implementation'})
    
    # Look for applications
    app_match = re.search(r'(?:\n\n)([^\n]+(?:\n[^\n]+){0,8}?(?:application|use case|real-world|industry|applied to|used for).{100,700}?)(?:\n\n|$)', text, re.IGNORECASE)
    if app_match:
        sections.append({'title': 'Applications', 'content': app_match.group(1), 'type': 'application'})
    
    # Look for limitations
    limit_match = re.search(r'(?:\n\n)([^\n]+(?:\n[^\n]+){0,6}?(?:limitation|challenge|drawback|issue|problem|difficulty).{50,500}?)(?:\n\n|$)', text, re.IGNORECASE)
    if limit_match:
        sections.append({'title': 'Limitations', 'content': limit_match.group(1), 'type': 'limitation'})
    
    # If we found sections, return them, otherwise return the whole text as one section
    if sections:
        return sections
    else:
        return [{'title': 'AI/ML Response', 'content': text, 'type': 'other'}]

def _build_ai_ml_response(sections: List[Dict[str, Any]]) -> str:
    """Build an AI/ML-specific response from extracted sections"""
    if not sections:
        return ""
    
    # If we only have one section, return its content
    if len(sections) == 1:
        return sections[0]['content']
    
    # Build response with proper headers and transitions
    response_parts = []
    
    # Add introduction if available
    intro_sections = [s for s in sections if s['type'] == 'introduction']
    if intro_sections:
        response_parts.append(f"# {intro_sections[0].get('title', 'Introduction')}\n\n{intro_sections[0]['content']}")
    
    # Add definition/concept sections
    definition_sections = [s for s in sections if s['type'] in ['definition', 'concept']]
    for section in definition_sections:
        response_parts.append(f"\n## {section.get('title', 'Key Concepts')}\n\n{section['content']}")
    
    # Add technical sections
    technical_sections = [s for s in sections if s['type'] in ['technical', 'implementation']]
    for section in technical_sections:
        response_parts.append(f"\n## {section.get('title', 'Technical Details')}\n\n{section['content']}")
    
    # Add example and application sections
    example_sections = [s for s in sections if s['type'] in ['example', 'application']]
    for section in example_sections:
        response_parts.append(f"\n## {section.get('title', 'Applications & Examples')}\n\n{section['content']}")
    
    # Add limitation sections
    limitation_sections = [s for s in sections if s['type'] == 'limitation']
    if limitation_sections:
        response_parts.append(f"\n## {limitation_sections[0].get('title', 'Limitations & Challenges')}\n\n{limitation_sections[0]['content']}")
    
    # Add conclusion if available
    conclusion_sections = [s for s in sections if s['type'] == 'conclusion']
    if conclusion_sections:
        response_parts.append(f"\n## {conclusion_sections[0].get('title', 'Conclusion')}\n\n{conclusion_sections[0]['content']}")
    
    # Add any remaining sections not handled above
    other_sections = [s for s in sections if s['type'] == 'other']
    for section in other_sections:
        response_parts.append(f"\n## {section.get('title', 'Additional Information')}\n\n{section['content']}")
    
    return '\n'.join(response_parts)

def _similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity (0-1)"""
    # This is a very basic similarity measure
    # In production, we'd use a more sophisticated approach
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)
