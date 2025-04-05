"""
Text correction module for Minerva.

This module provides utilities for correcting common spelling and grammatical errors
in text responses from AI models, improving the overall quality of outputs.
"""
import re
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Common misspellings and their corrections
COMMON_MISSPELLINGS = {
    # General misspellings
    "teh": "the",
    "definately": "definitely",
    "recieve": "receive",
    "seperate": "separate",
    "occured": "occurred",
    "occuring": "occurring",
    "accomodate": "accommodate",
    "untill": "until",
    "accross": "across",
    "relevent": "relevant",
    "alot": "a lot",
    "wierd": "weird",
    "beleive": "believe",
    "concious": "conscious",
    "greatful": "grateful",
    "wich": "which",
    "doesnt": "doesn't",
    "dont": "don't",
    "wont": "won't",
    "cant": "can't",
    "isnt": "isn't",
    "wasnt": "wasn't",
    "didnt": "didn't",
    "havent": "haven't",
    "wouldnt": "wouldn't",
    "shouldnt": "shouldn't",
    "couldnt": "couldn't",
    "im": "I'm",
    "ive": "I've",
    "id": "I'd",
    "youre": "you're",
    "theyre": "they're",
    "thats": "that's",
    "hes": "he's",
    "shes": "she's",
    "its a": "it's a",
    "weve": "we've",
    "werent": "weren't",
    "arent": "aren't",
    
    # Technical terms
    "ai assistent": "AI assistant",
    "artifical": "artificial",
    "inteligence": "intelligence",
    "algorythm": "algorithm",
    "pyhton": "Python",
    "javascipt": "JavaScript",
    "programing": "programming",
    "responce": "response",
    "validaton": "validation",
}

# Common grammatical patterns to fix
GRAMMAR_PATTERNS = [
    # Double words
    (r'\b(\w+)\s+\1\b', r'\1'),
    # Space before punctuation
    (r'\s+([.,;:!?])', r'\1'),
    # Missing spaces after punctuation
    (r'([.,;:!?])([a-zA-Z])', r'\1 \2'),
    # "a" vs "an" for words starting with vowels
    (r'\ba ([aeiou]\w+)\b', r'an \1'),
    # Incorrect "your/you're"
    (r'\byour ([a-z]+ing)\b', r"you're \1"),
    # Capitalize first word in sentence
    (r'(?<=[\.\?!]\s)([a-z])', lambda m: m.group(1).upper()),
    # Capitalize "I"
    (r'\bi\b', 'I'),
]

def correct_text(text: str) -> Tuple[str, Dict]:
    """
    Apply spelling and grammar corrections to text.
    
    Args:
        text: The input text to correct
        
    Returns:
        Tuple of (corrected_text, correction_stats)
    """
    if not text:
        return text, {"spelling_corrections": 0, "grammar_corrections": 0}
    
    original_text = text
    correction_stats = {
        "spelling_corrections": 0,
        "grammar_corrections": 0
    }
    
    # Fix spelling errors
    for misspelled, correct in COMMON_MISSPELLINGS.items():
        pattern = r'\b' + misspelled + r'\b'
        replacement = correct
        
        # Count occurrences before replacement
        count = len(re.findall(pattern, text, re.IGNORECASE))
        correction_stats["spelling_corrections"] += count
        
        # Replace misspellings
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Fix grammar patterns
    for pattern, replacement in GRAMMAR_PATTERNS:
        # Count occurrences before replacement
        count = len(re.findall(pattern, text))
        correction_stats["grammar_corrections"] += count
        
        # Apply grammar correction
        text = re.sub(pattern, replacement, text)
    
    # Log corrections if any were made
    total_corrections = correction_stats["spelling_corrections"] + correction_stats["grammar_corrections"]
    if total_corrections > 0:
        logger.info(f"Applied {total_corrections} text corrections ({correction_stats['spelling_corrections']} spelling, {correction_stats['grammar_corrections']} grammar)")
        
        # Log detailed changes if significant
        if total_corrections > 2:
            # Show a preview of changes (truncated if needed)
            max_length = 100
            orig_preview = original_text[:max_length] + ("..." if len(original_text) > max_length else "")
            corr_preview = text[:max_length] + ("..." if len(text) > max_length else "")
            logger.debug(f"Original: {orig_preview}")
            logger.debug(f"Corrected: {corr_preview}")
    
    return text, correction_stats

def should_attempt_correction(text: str) -> bool:
    """
    Determine if text correction should be attempted based on text characteristics.
    
    Args:
        text: The text to evaluate
        
    Returns:
        Boolean indicating whether correction should be attempted
    """
    # Skip correction for very short texts
    if len(text) < 10:
        return False
    
    # Skip correction for code blocks and technical content
    code_indicators = ['```', 'def ', 'class ', 'import ', 'function', '<html', '<div', 'SELECT ', 'WHERE ']
    if any(indicator in text for indicator in code_indicators):
        return False
    
    return True
