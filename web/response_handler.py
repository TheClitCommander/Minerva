#!/usr/bin/env python3
"""
Response Handler for Minerva

This module cleans, processes, and improves AI responses to ensure
they are coherent, useful, and properly formatted.
"""

import re
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_ai_response(ai_response: str) -> str:
    """
    Ensures the AI response is coherent and useful.
    
    Args:
        ai_response: The raw AI response
        
    Returns:
        A cleaned and improved response
    """
    # Return early if the response is empty or None
    if not ai_response:
        return "I apologize, but I couldn't generate a response. Could you please rephrase your question?"
    
    # Clean up common issues
    cleaned_response = ai_response.strip()
    
    # Remove any AI self-reference patterns
    self_ref_patterns = [
        r"As an AI language model,?",
        r"As an AI assistant,?",
        r"As an artificial intelligence,?",
        r"I'm an AI language model,?",
        r"I'm an AI assistant,?",
        r"I'm an artificial intelligence,?",
        r"As a language model,?",
        r"As an? ?AI,?",
        r"I do not have personal opinions",
        r"I do not have the ability to",
        r"I don't have access to",
        r"I don't have the ability to",
        r"I cannot provide",
        r"I cannot browse"
    ]
    
    for pattern in self_ref_patterns:
        cleaned_response = re.sub(pattern, "", cleaned_response, flags=re.IGNORECASE)
    
    # Filter out nonsensical or unhelpful responses
    unhelpful_patterns = [
        r"^I'm not sure if I'm going to be able to do that",
        r"^I'm sorry, (but )?I (can't|cannot|don't|do not) (have|know|understand|provide)",
        r"^As an AI( language model)?, I (don't|do not|cannot|can't) ",
        r"^I apologize, but "
    ]
    
    for pattern in unhelpful_patterns:
        if re.match(pattern, cleaned_response, re.IGNORECASE):
            logger.info(f"Detected unhelpful response matching pattern: {pattern}")
            return "I'll do my best to help you with that. Here's what I know: " + cleaned_response.split(".", 1)[-1].strip()
    
    # Check if the response is too short
    if len(cleaned_response.split()) < 5:
        logger.info(f"Response too short: {cleaned_response}")
        return "I'm sorry, but I couldn't generate a complete response. Could you please rephrase your question?"
    
    # Remove common artifacts and formatting issues
    cleaned_response = re.sub(r'\n{3,}', '\n\n', cleaned_response)  # Replace excessive newlines
    cleaned_response = re.sub(r'\s{2,}', ' ', cleaned_response)  # Replace multiple spaces
    cleaned_response = re.sub(r'(\w)\s+([.,!?:;])', r'\1\2', cleaned_response)  # Fix spacing before punctuation
    
    # Clean up any special tokens or markers that might remain
    cleaned_response = re.sub(r'<.*?>', '', cleaned_response)  # Remove HTML-like tags
    cleaned_response = re.sub(r'\[\w+\]', '', cleaned_response)  # Remove markdown-style tags
    
    # Fix common formatting inconsistencies
    cleaned_response = re.sub(r'(\d)\s+(\.)\s+(\d)', r'\1\2\3', cleaned_response)  # Fix decimal spacing
    
    # Final normalization: ensure single spaces between sentences
    cleaned_response = re.sub(r'([.!?])\s{2,}', r'\1 ', cleaned_response)
    
    # Handle repetitive text
    lines = cleaned_response.split("\n")
    unique_lines = []
    for line in lines:
        if line not in unique_lines or not line.strip():
            unique_lines.append(line)
    
    if len(unique_lines) < len(lines) * 0.8:  # If more than 20% of lines were repetitive
        logger.info("Detected repetitive content in response")
        cleaned_response = "\n".join(unique_lines)
    
    # Log significant cleaning
    if len(cleaned_response) < len(ai_response) * 0.8:  # More than 20% reduction
        logger.info(f"Response significantly cleaned from {len(ai_response)} to {len(cleaned_response)} chars")
    
    return cleaned_response.strip()

def format_response(ai_response: str, formatting_params: Optional[Dict[str, Any]] = None) -> str:
    """
    Format the AI response according to user preferences.
    
    Args:
        ai_response: The AI response to format
        formatting_params: Dictionary with formatting parameters (tone, structure, length)
        
    Returns:
        Formatted response
    """
    if not formatting_params:
        return ai_response
    
    response = ai_response
    
    # Apply tone adjustment if specified
    tone = formatting_params.get('tone')
    if tone == 'formal':
        # Replace casual language with more formal alternatives
        casual_words = {
            r'\bkinda\b': 'somewhat',
            r'\bgonna\b': 'going to',
            r'\bwanna\b': 'want to',
            r'\byeah\b': 'yes',
            r'\bnah\b': 'no',
            r'\bcool\b': 'excellent',
            r'\bawesome\b': 'impressive',
            r'\btotally\b': 'completely',
            r'\bstuff\b': 'items',
            r'\bthings\b': 'matters',
        }
        
        for casual, formal in casual_words.items():
            response = re.sub(casual, formal, response, flags=re.IGNORECASE)
            
    elif tone == 'casual':
        # No need to modify if already casual
        pass
    
    # Apply structure formatting if specified
    structure = formatting_params.get('structure')
    if structure == 'bullet_points' and '\n- ' not in response:
        # Convert paragraphs to bullet points
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            response = '\n'.join([f"- {p}" for p in paragraphs])
        else:
            # Split single paragraph into sentences and bullet them
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', response) if s.strip()]
            if len(sentences) > 1:
                response = '\n'.join([f"- {s}" for s in sentences])
    
    elif structure == 'numbered_list' and not re.search(r'\n\d+\.', response):
        # Convert paragraphs to numbered list
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            response = '\n'.join([f"{i+1}. {p}" for i, p in enumerate(paragraphs)])
        else:
            # Split single paragraph into sentences and number them
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', response) if s.strip()]
            if len(sentences) > 1:
                response = '\n'.join([f"{i+1}. {s}" for i, s in enumerate(sentences)])
    
    elif structure == 'summary':
        # Create a summary version if it's long
        if len(response.split()) > 100:
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', response) if s.strip()]
            # Take first sentence and possibly last if it's a conclusion
            if len(sentences) > 2:
                summary = sentences[0]
                if any(w in sentences[-1].lower() for w in ['conclusion', 'summary', 'overall', 'therefore']):
                    summary += ' ' + sentences[-1]
                response = summary
    
    # Apply length adjustment if specified
    length = formatting_params.get('length')
    if length == 'concise' and len(response.split()) > 50:
        # Make it more concise by removing qualifiers and keeping essential info
        response = re.sub(r'\b(I think|basically|essentially|actually|really|in my opinion|as I see it)\b', '', response)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', response) if s.strip()]
        if len(sentences) > 3:
            # Keep first 2-3 sentences depending on original length
            keep_count = min(3, max(2, len(sentences) // 3))
            response = ' '.join(sentences[:keep_count])
    
    elif length == 'comprehensive' and len(response.split()) < 100:
        # Already handled by the AI model with longer generation
        pass
    
    return response.strip()
