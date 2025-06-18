"""
Response Formatter

This module handles dynamic formatting of responses based on user preferences.
It processes raw AI responses according to user-defined style preferences,
structuring them into different formats (paragraph, bullet points, etc.)
and applying tone adjustments.
"""

import re
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class ResponseFormatter:
    """
    Formats AI responses according to user preferences.
    """
    
    def __init__(self):
        """Initialize the response formatter."""
        pass
    
    def format_response(self, raw_response: str, formatting_params: Dict[str, Any]) -> tuple[str, bool]:
        """
        Format a raw AI response according to formatting parameters.
        
        Args:
            raw_response: The raw AI response text
            formatting_params: Dictionary of formatting parameters from UserPreferenceManager
            
        Returns:
            tuple of (formatted_response, has_more): The formatted response and whether there's more content
        """
        try:
            # Extract parameters
            structure_type = formatting_params.get('structure_type', 'paragraph')
            tone_markers = formatting_params.get('tone_markers', [])
            max_paragraphs = formatting_params.get('max_paragraphs', 3)
            use_headings = formatting_params.get('use_headings', False)
            truncation_enabled = formatting_params.get('truncation_enabled', True)
            truncation_length = formatting_params.get('truncation_length', 1000)
            
            # Extract response length parameters
            response_length = formatting_params.get('response_length', 'medium')
            expand_details = formatting_params.get('expand_details', True)
            
            # Apply truncation if enabled and needed
            if truncation_enabled and len(raw_response) > truncation_length:
                if expand_details and response_length != 'long':
                    # Add expand details link for short and medium responses
                    truncated_response, has_more = self._smart_truncate_with_expansion(raw_response, truncation_length)
                else:
                    # Regular truncation for long responses or when expansion not needed
                    truncated_response = self._smart_truncate(raw_response, truncation_length)
                    has_more = False
            else:
                truncated_response = raw_response
                has_more = False
            
            # Apply formatting based on structure type
            if structure_type == 'bullet_points':
                formatted = self._format_as_bullet_points(truncated_response, formatting_params)
            elif structure_type == 'numbered_list':
                formatted = self._format_as_numbered_list(truncated_response, formatting_params)
            elif structure_type == 'summary':
                formatted = self._format_as_summary(truncated_response, formatting_params)
            else:  # default to paragraph
                formatted = self._format_as_paragraphs(truncated_response, formatting_params)
            
            # Apply tone adjustments if specified
            if tone_markers:
                formatted = self._adjust_tone(formatted, tone_markers)
            
            return formatted, has_more
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            # Return original response if formatting fails
            return raw_response, False
    
    def _smart_truncate(self, text: str, length: int) -> str:
        """
        Smartly truncate text to the specified length, ensuring coherent sentences.
        
        Args:
            text: The text to truncate
            length: Maximum length
            
        Returns:
            truncated_text: The truncated text
        """
        if len(text) <= length:
            return text
        
        # Try to truncate at sentence boundary
        truncated = text[:length]
        
        # Find the last period followed by space or end of string
        last_period = max(
            truncated.rfind('. '),
            truncated.rfind('! '),
            truncated.rfind('? ')
        )
        
        if last_period > length * 0.5:  # Only truncate at sentence if we're not losing too much
            truncated = truncated[:last_period+1]
        else:
            # Find the last space
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def _smart_truncate_with_expansion(self, text: str, length: int) -> tuple[str, bool]:
        """
        Truncate text and add an "Expand Details" link for progressive disclosure.
        
        Args:
            text: The text to truncate
            length: Maximum length
            
        Returns:
            tuple of (truncated_text, has_more): The truncated text with expand link, and whether there's more content
        """
        if len(text) <= length:
            return text, False
        
        # Store the full text in the expandable portion
        remaining_text = text[length:]
        
        # Perform smart truncation on the visible portion
        truncated = text[:length]
        
        # Find the best place to truncate
        last_period = max(
            truncated.rfind('. '),
            truncated.rfind('! '),
            truncated.rfind('? ')
        )
        
        # Choose where to truncate
        if last_period > length * 0.5:  # Only truncate at sentence if we're not losing too much
            visible_text = text[:last_period+1]
        else:
            # Find the last space
            last_space = truncated.rfind(' ')
            if last_space > 0:
                visible_text = text[:last_space]
            else:
                visible_text = truncated
        
        # Create a unique ID for this expansion
        expand_id = f"expand_{hash(text) & 0xFFFFFFFF}"
        
        # Create the expandable content
        expansion_link = f' <a href="#" class="expand-details" data-expand-id="{expand_id}">Expand Details...</a>'
        hidden_text = f'<div id="{expand_id}" class="hidden-content" style="display:none;">{remaining_text}</div>'
        
        return visible_text + expansion_link + hidden_text, True
    
    def _format_as_paragraphs(self, text: str, params: Dict[str, Any]) -> str:
        """
        Format response as paragraphs.
        
        Args:
            text: The raw response text
            params: Formatting parameters
            
        Returns:
            formatted: The formatted paragraphs
        """
        max_paragraphs = params.get('max_paragraphs', 3)
        intro_style = params.get('intro_style', 'brief')
        use_conclusion = params.get('conclusion', True)
        
        # Split into paragraphs (handle different line break patterns)
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)
        
        # Limit number of paragraphs
        if len(paragraphs) > max_paragraphs:
            # Always keep first paragraph (intro)
            selected = [paragraphs[0]]
            
            # For deep dive with many paragraphs, add headings if needed
            if params.get('use_headings') and len(paragraphs) > 3:
                for i, para in enumerate(paragraphs[1:max_paragraphs]):
                    # Add a heading if paragraph is long enough
                    if len(para) > 100:
                        heading = self._generate_heading(para, i+1)
                        selected.append(f"\n## {heading}\n\n{para}")
                    else:
                        selected.append(para)
            else:
                # Otherwise just add the paragraphs
                selected.extend(paragraphs[1:max_paragraphs])
            
            # Add conclusion for certain modes
            if use_conclusion and len(paragraphs) > max_paragraphs + 1:
                selected.append("In conclusion, " + self._extract_conclusion(paragraphs[-1]))
            
            final_text = "\n\n".join(selected)
        else:
            final_text = "\n\n".join(paragraphs)
        
        return final_text
    
    def _format_as_bullet_points(self, text: str, params: Dict[str, Any]) -> str:
        """
        Format response as bullet points.
        
        Args:
            text: The raw response text
            params: Formatting parameters
            
        Returns:
            formatted: The formatted bullet points
        """
        bullet_prefix = params.get('bullet_prefix', '• ')
        section_breaks = params.get('section_breaks', True)
        
        # Extract an introduction paragraph
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)
        introduction = paragraphs[0] if paragraphs else ""
        
        # Extract potential bullet points from text
        potential_points = self._extract_key_points(text)
        
        # Ensure we have bullet points
        if not potential_points:
            # Generate bullet points from paragraphs if none detected
            potential_points = self._generate_bullet_points(paragraphs[1:] if len(paragraphs) > 1 else paragraphs)
        
        # Format the bullet points
        formatted_points = []
        for point in potential_points:
            point = point.strip()
            if not point.startswith(bullet_prefix) and not point.startswith('-'):
                point = f"{bullet_prefix}{point}"
            formatted_points.append(point)
        
        # Combine introduction with bullet points
        if introduction and not introduction.endswith(':'):
            introduction += ':'
        
        result = f"{introduction}\n\n"
        if section_breaks:
            result += "\n".join(formatted_points)
        else:
            result += "\n".join(formatted_points)
        
        return result
    
    def _format_as_numbered_list(self, text: str, params: Dict[str, Any]) -> str:
        """
        Format response as a numbered list.
        
        Args:
            text: The raw response text
            params: Formatting parameters
            
        Returns:
            formatted: The formatted numbered list
        """
        section_breaks = params.get('section_breaks', True)
        
        # Extract an introduction paragraph
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)
        introduction = paragraphs[0] if paragraphs else ""
        
        # Extract potential bullet points from text
        potential_points = self._extract_key_points(text)
        
        # Ensure we have points for the list
        if not potential_points:
            # Generate points from paragraphs if none detected
            potential_points = self._generate_bullet_points(paragraphs[1:] if len(paragraphs) > 1 else paragraphs)
        
        # Format the numbered list
        formatted_points = []
        for i, point in enumerate(potential_points, 1):
            point = point.strip()
            # Remove existing bullet points or numbers
            point = re.sub(r'^[\d\.\•\-\*]+\s*', '', point)
            formatted_points.append(f"{i}. {point}")
        
        # Combine introduction with numbered list
        if introduction and not introduction.endswith(':'):
            introduction += ':'
        
        result = f"{introduction}\n\n"
        if section_breaks:
            result += "\n".join(formatted_points)
        else:
            result += "\n".join(formatted_points)
        
        return result
    
    def _format_as_summary(self, text: str, params: Dict[str, Any]) -> str:
        """
        Format response as a concise summary.
        
        Args:
            text: The raw response text
            params: Formatting parameters
            
        Returns:
            formatted: The formatted summary
        """
        truncation_length = params.get('truncation_length', 300)
        
        # Extract key sentences for summary
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) <= 3:
            # If there are just a few sentences, use them all
            summary = " ".join(sentences)
        else:
            # Select important sentences: first, last, and one from middle
            selected = [sentences[0]]
            
            # Add a middle sentence if there are more than 4 sentences
            if len(sentences) > 4:
                middle_idx = len(sentences) // 2
                selected.append(sentences[middle_idx])
            
            # Add final sentence
            selected.append(sentences[-1])
            
            summary = " ".join(selected)
        
        # Ensure summary isn't too long
        if len(summary) > truncation_length:
            summary = self._smart_truncate(summary, truncation_length)
        
        # Add "In summary" prefix if not already starting with similar wording
        if not any(summary.lower().startswith(prefix) for prefix in ["in summary", "to summarize", "overall", "in conclusion"]):
            summary = "In summary: " + summary
        
        return summary
    
    def _adjust_tone(self, text: str, tone_markers: List[str]) -> str:
        """
        Adjust the tone of the response using tone markers.
        
        Args:
            text: The text to adjust
            tone_markers: List of phrases that indicate the desired tone
            
        Returns:
            adjusted_text: The text with adjusted tone
        """
        if not tone_markers:
            return text
            
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)
        
        # Apply tone marker to first paragraph if it's long enough
        if paragraphs and len(paragraphs[0]) > 50:
            # Select a random tone marker
            import random
            marker = random.choice(tone_markers)
            
            # Check if the paragraph already starts with a similar phrase
            first_para = paragraphs[0].lower()
            if not any(first_para.startswith(marker.lower()) for marker in tone_markers):
                # Add the tone marker
                paragraphs[0] = f"{marker}, {paragraphs[0][0].lower()}{paragraphs[0][1:]}"
        
        return "\n\n".join(paragraphs)
    
    def _extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from text that look like they should be bullet points.
        
        Args:
            text: The text to extract points from
            
        Returns:
            points: List of extracted points
        """
        # Look for existing bullet points or numbered items
        bullet_pattern = r'(?:^|\n)(?:\s*[\•\-\*]|\s*\d+[\.\)])\s*([^\n]+)'
        matches = re.findall(bullet_pattern, text)
        
        if matches:
            return matches
        
        # Look for key phrases that often indicate points
        key_phrase_patterns = [
            r'(?:^|\n)(?:First|First of all|To begin with|Initially)[\,\:]?\s+([^\n\.]+)',
            r'(?:^|\n)(?:Second|Secondly|Next|Then|Additionally)[\,\:]?\s+([^\n\.]+)',
            r'(?:^|\n)(?:Third|Thirdly|Furthermore|Moreover|Also)[\,\:]?\s+([^\n\.]+)',
            r'(?:^|\n)(?:Finally|Lastly|In conclusion)[\,\:]?\s+([^\n\.]+)',
            r'(?:^|\n)(?:Important|Key|Essential|Critical)[\,\:]?\s+([^\n\.]+)',
            r'(?:^|\n)(?:Note that|Remember|Keep in mind)[\,\:]?\s+([^\n\.]+)'
        ]
        
        all_matches = []
        for pattern in key_phrase_patterns:
            matches = re.findall(pattern, text)
            all_matches.extend(matches)
        
        return all_matches
    
    def _generate_bullet_points(self, paragraphs: List[str]) -> List[str]:
        """
        Generate bullet points from paragraphs when no natural points are found.
        
        Args:
            paragraphs: List of paragraphs
            
        Returns:
            points: Generated bullet points
        """
        points = []
        
        for para in paragraphs:
            # Skip very short paragraphs
            if len(para) < 20:
                continue
                
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            
            for sentence in sentences:
                # Skip short sentences or questions
                if len(sentence) < 15 or sentence.endswith('?'):
                    continue
                
                # Add as a bullet point
                points.append(sentence)
                
                # Limit number of points
                if len(points) >= 5:
                    return points
        
        return points
    
    def _generate_heading(self, paragraph: str, index: int) -> str:
        """
        Generate a heading for a paragraph.
        
        Args:
            paragraph: The paragraph to generate a heading for
            index: Index of the paragraph
            
        Returns:
            heading: Generated heading
        """
        # Extract the first sentence
        first_sentence = re.split(r'(?<=[.!?])\s+', paragraph)[0]
        
        # Use the first few words as the heading
        words = first_sentence.split()
        if len(words) <= 5:
            heading = first_sentence
        else:
            heading = " ".join(words[:5]) + "..."
        
        # Default headings if the generated one is too short
        if len(heading) < 10:
            default_headings = ["Key Points", "Important Details", "Further Information", 
                               "Additional Context", "Detailed Explanation"]
            heading = default_headings[min(index, len(default_headings)-1)]
        
        return heading
    
    def _extract_conclusion(self, text: str) -> str:
        """
        Extract or generate a conclusion from text.
        
        Args:
            text: The text to extract a conclusion from
            
        Returns:
            conclusion: Extracted or generated conclusion
        """
        # Look for conclusion markers
        conclusion_pattern = r'(?:In conclusion|To summarize|Overall|Finally|In summary)[,:]?\s+([^\.]+)'
        match = re.search(conclusion_pattern, text)
        
        if match:
            return match.group(1)
        
        # Otherwise use the last sentence
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        if sentences:
            return sentences[-1]
        
        return text


# For convenience in importing
response_formatter = ResponseFormatter()
