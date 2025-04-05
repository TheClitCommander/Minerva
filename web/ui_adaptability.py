"""
UI Adaptability Module

This module implements UI improvements for real-time feedback handling and 
dynamic response display. It ensures feedback UI is responsive and handles
preference syncing without causing UI lag.
"""

import json
import logging
import os
import sys
from typing import Dict, Any, Optional, List

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UIAdaptabilityManager:
    """
    Manages UI adaptability features for smooth feedback handling and
    response rendering with dynamic content adjustments.
    """
    
    def __init__(self):
        """Initialize the UI adaptability manager."""
        # Configuration parameters
        self.config = {
            # Default collapse threshold (characters)
            "collapse_threshold": 1000,
            
            # Default section size for progressive disclosure
            "section_size": 300,
            
            # Expansion levels
            "expansion_levels": ["summary", "details", "comprehensive"],
            
            # Expansion thresholds
            "expansion_thresholds": {
                "summary": 500,      # First expansion at 500 chars
                "details": 1500,     # Second expansion at 1500 chars
                "comprehensive": 3000 # Third expansion at 3000 chars
            },
            
            # UI performance settings
            "max_initial_render_length": 5000,  # Maximum content to render initially
            "async_render_threshold": 2000,     # Threshold for async rendering
            "render_chunk_size": 500,           # Size of chunks for progressive rendering
            "render_delay_ms": 10               # Delay between chunk renders (ms)
        }
        
        logger.info("UI Adaptability Manager initialized")
    
    def prepare_response_for_display(self, response: str, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a response for display in the UI, applying dynamic collapsing
        and progressive disclosure based on user preferences.
        
        Args:
            response: Raw response text
            user_preferences: User preferences including length settings
            
        Returns:
            Dict with prepared response and display metadata
        """
        # Get response length preference
        response_length = user_preferences.get("response_length", "medium")
        
        # Determine collapse threshold based on length preference
        collapse_thresholds = {
            "short": 500,
            "medium": 1000,
            "long": 2000
        }
        collapse_threshold = collapse_thresholds.get(response_length, 1000)
        
        # Check if response needs collapsing
        needs_collapsing = len(response) > collapse_threshold
        
        # Determine initial display and expandable content
        if needs_collapsing:
            # Split into visible and expandable content
            visible_content = self._get_initial_content(response, collapse_threshold)
            expandable_content = response[len(visible_content):]
            
            # Generate progressive disclosure sections if needed
            expanded_sections = self._create_progressive_sections(
                expandable_content, 
                user_preferences
            )
            
            prepared_response = {
                "initial_content": visible_content,
                "has_more": True,
                "expandable_content": expandable_content,
                "expanded_sections": expanded_sections,
                "total_length": len(response),
                "visible_length": len(visible_content),
                "collapse_threshold": collapse_threshold
            }
        else:
            # No collapsing needed
            prepared_response = {
                "initial_content": response,
                "has_more": False,
                "expandable_content": "",
                "expanded_sections": [],
                "total_length": len(response),
                "visible_length": len(response),
                "collapse_threshold": collapse_threshold
            }
        
        # Add rendering performance metadata
        prepared_response["rendering"] = self._get_rendering_metadata(response, user_preferences)
        
        return prepared_response
    
    def generate_feedback_ui(self, message_id: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate feedback UI elements based on response data and message ID.
        
        Args:
            message_id: Unique identifier for the message
            response_data: Response data including content and metadata
            
        Returns:
            Dict containing feedback UI elements
        """
        # Determine what feedback options to show based on response
        total_length = response_data.get("total_length", 0)
        has_expandable = response_data.get("has_more", False)
        
        # Basic feedback buttons (always present)
        feedback_ui = {
            "message_id": message_id,
            "feedback_buttons": [
                {
                    "id": f"feedback-positive-{message_id}",
                    "type": "positive",
                    "label": "Helpful",
                    "icon": "thumbs-up"
                },
                {
                    "id": f"feedback-negative-{message_id}",
                    "type": "negative",
                    "label": "Not Helpful",
                    "icon": "thumbs-down"
                }
            ],
            "feedback_form": self._get_feedback_form(message_id)
        }
        
        # Add expand/collapse buttons if needed
        if has_expandable:
            # Add expansion UI elements
            sections = response_data.get("expanded_sections", [])
            expansion_controls = []
            
            if sections:
                # Add controls for each section
                for idx, section in enumerate(sections):
                    expansion_controls.append({
                        "id": f"expand-section-{idx}-{message_id}",
                        "type": "expand_section",
                        "label": f"Show {section.get('label', 'more')}",
                        "section_id": idx
                    })
            else:
                # Simple expand button for the whole content
                expansion_controls.append({
                    "id": f"expand-all-{message_id}",
                    "type": "expand_all",
                    "label": "Show more"
                })
            
            feedback_ui["expansion_controls"] = expansion_controls
        
        # Add specific feedback options based on response characteristics
        if total_length > 1000:
            # For longer responses, add length feedback options
            feedback_ui["length_feedback"] = {
                "id": f"length-feedback-{message_id}",
                "options": [
                    {"value": "too_long", "label": "Too long"},
                    {"value": "good_length", "label": "Good length"},
                    {"value": "too_short", "label": "Too short"}
                ]
            }
        
        return feedback_ui
    
    def handle_expansion_tracking(self, message_id: str, expansion_type: str, 
                                user_id: str) -> Dict[str, Any]:
        """
        Track expansion interactions to improve future responses.
        
        Args:
            message_id: Unique identifier for the message
            expansion_type: Type of expansion (e.g., "show_more", "section_1", etc.)
            user_id: Unique identifier for the user
            
        Returns:
            Dict containing tracking confirmation and metadata
        """
        # This would integrate with the feedback system
        # For now, just return confirmation
        return {
            "tracked": True,
            "message_id": message_id,
            "expansion_type": expansion_type,
            "timestamp": "now"  # This would be a real timestamp in production
        }
    
    def get_granular_feedback_options(self, feedback_type: str) -> List[Dict[str, Any]]:
        """
        Get granular feedback options based on the initial feedback type.
        
        Args:
            feedback_type: Initial feedback type (e.g., "negative")
            
        Returns:
            List of feedback options for the specified type
        """
        if feedback_type == "negative":
            return [
                {"id": "irrelevant", "label": "The response wasn't relevant"},
                {"id": "inaccurate", "label": "The information was inaccurate"},
                {"id": "too_verbose", "label": "The response was too long"},
                {"id": "too_brief", "label": "The response was too short"},
                {"id": "poor_formatting", "label": "The formatting was difficult to read"},
                {"id": "wrong_tone", "label": "The tone wasn't appropriate"}
            ]
        elif feedback_type == "positive":
            return [
                {"id": "very_relevant", "label": "The response was very relevant"},
                {"id": "well_explained", "label": "The explanation was clear"},
                {"id": "good_length", "label": "The length was perfect"},
                {"id": "well_formatted", "label": "The formatting was helpful"},
                {"id": "appropriate_tone", "label": "The tone was appropriate"}
            ]
        else:
            return []
    
    def _get_initial_content(self, response: str, threshold: int) -> str:
        """
        Get the initial visible content up to a logical breakpoint near the threshold.
        
        Args:
            response: Full response text
            threshold: Character threshold
            
        Returns:
            Initial visible portion of the response
        """
        # If response is shorter than threshold, return it all
        if len(response) <= threshold:
            return response
        
        # Try to find a paragraph break near the threshold
        paragraph_break = response.rfind('\n\n', 0, threshold)
        if paragraph_break != -1 and paragraph_break > threshold * 0.7:
            return response[:paragraph_break + 2]
        
        # Try to find a sentence break
        sentence_end_chars = ['.', '!', '?']
        for i in range(threshold, threshold - 200, -1):
            if i < 0 or i >= len(response):
                continue
            if response[i] in sentence_end_chars and (i + 1 >= len(response) or response[i + 1].isspace()):
                return response[:i + 1]
        
        # If no good breakpoint, just use the threshold
        return response[:threshold]
    
    def _create_progressive_sections(self, content: str, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split expandable content into progressive disclosure sections.
        
        Args:
            content: Expandable content
            user_preferences: User preferences
            
        Returns:
            List of sections for progressive disclosure
        """
        # Get preferred expansion style
        expansion_style = user_preferences.get("expansion_style", "progressive")
        
        if expansion_style == "all_at_once" or len(content) < 500:
            # Single expansion
            return [{
                "id": "full_content",
                "content": content,
                "label": "more",
                "size": len(content)
            }]
        
        # Split into sections
        sections = []
        
        # Determine section boundaries (try to split at paragraph breaks)
        remaining = content
        target_size = self.config["section_size"]
        
        while remaining:
            if len(remaining) <= target_size:
                # Last section
                sections.append({
                    "id": f"section_{len(sections)}",
                    "content": remaining,
                    "label": "remaining content",
                    "size": len(remaining)
                })
                break
            
            # Find paragraph break
            end_pos = min(len(remaining), target_size)
            break_pos = remaining.rfind('\n\n', 0, end_pos)
            
            if break_pos == -1 or break_pos < target_size * 0.5:
                # No good paragraph break, try sentence break
                for i in range(end_pos, end_pos - 200, -1):
                    if i < 0 or i >= len(remaining):
                        continue
                    if remaining[i] in ['.', '!', '?'] and (i + 1 >= len(remaining) or remaining[i + 1].isspace()):
                        break_pos = i + 1
                        break
                
                # If still no good break, just use the target size
                if break_pos == -1:
                    break_pos = end_pos
            else:
                break_pos += 2  # Include the paragraph break
            
            # Create section
            section_content = remaining[:break_pos]
            sections.append({
                "id": f"section_{len(sections)}",
                "content": section_content,
                "label": f"more ({len(sections) + 1}/{(len(content) // target_size) + 1})",
                "size": len(section_content)
            })
            
            # Update remaining content
            remaining = remaining[break_pos:]
        
        return sections
    
    def _get_rendering_metadata(self, response: str, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate rendering metadata to optimize UI performance.
        
        Args:
            response: Full response text
            user_preferences: User preferences
            
        Returns:
            Dict with rendering metadata
        """
        # Determine if we need async rendering
        total_length = len(response)
        needs_async = total_length > self.config["async_render_threshold"]
        
        rendering_metadata = {
            "async_render": needs_async,
            "total_length": total_length
        }
        
        if needs_async:
            # Calculate rendering chunks for progressive loading
            chunk_size = self.config["render_chunk_size"]
            chunk_count = (total_length + chunk_size - 1) // chunk_size  # Ceiling division
            
            rendering_metadata.update({
                "chunk_size": chunk_size,
                "chunk_count": chunk_count,
                "render_delay_ms": self.config["render_delay_ms"]
            })
        
        return rendering_metadata
    
    def _get_feedback_form(self, message_id: str) -> Dict[str, Any]:
        """
        Generate a feedback form configuration.
        
        Args:
            message_id: Unique identifier for the message
            
        Returns:
            Dict with feedback form configuration
        """
        return {
            "id": f"feedback-form-{message_id}",
            "fields": [
                {
                    "id": "feedback_type",
                    "type": "radio",
                    "label": "What was wrong with this response?",
                    "options": [
                        {"value": "irrelevant", "label": "Not relevant to my question"},
                        {"value": "incomplete", "label": "Incomplete information"},
                        {"value": "incorrect", "label": "Incorrect information"},
                        {"value": "formatting", "label": "Poor formatting"},
                        {"value": "other", "label": "Other issue"}
                    ]
                },
                {
                    "id": "comments",
                    "type": "textarea",
                    "label": "Additional comments",
                    "placeholder": "Please provide any additional feedback..."
                }
            ]
        }


# Create a singleton instance
ui_adaptability_manager = UIAdaptabilityManager()


def test_ui_adaptability():
    """Test the UIAdaptabilityManager functionality."""
    print("Testing UI Adaptability Manager...")
    
    # Sample response
    sample_response = """
    Quantum computing leverages principles of quantum mechanics to process information in ways that classical computers cannot. 
    
    At its core, quantum computing uses quantum bits or "qubits" instead of traditional binary bits. While classical bits can only be in a state of 0 or 1, qubits can exist in a superposition of both states simultaneously, enabling quantum computers to process a vastly greater number of possibilities at once.
    
    Key principles include:
    1. Superposition: Qubits can represent multiple states at the same time
    2. Entanglement: Qubits can be correlated in ways that have no classical analogue
    3. Quantum interference: Allows amplification of correct solutions and cancellation of incorrect ones
    
    Current quantum computers are still in early stages, with challenges in maintaining qubit coherence and scaling systems to practical sizes. However, they show promise for applications in cryptography, drug discovery, optimization problems, and simulating quantum systems.
    
    IBM, Google, and other companies have developed quantum processors with increasing numbers of qubits. Google's Sycamore processor achieved quantum supremacy in 2019 by performing a specific calculation that would be practically impossible for classical supercomputers.
    
    Quantum algorithms like Shor's algorithm for factoring large numbers and Grover's algorithm for searching unsorted databases offer theoretical speedups over classical methods. These could potentially revolutionize fields like cryptography and database searching.
    
    Quantum error correction remains a significant challenge, as qubits are highly susceptible to environmental noise and decoherence. Various error correction codes and fault-tolerant methods are being developed to address this.
    
    The field continues to advance rapidly, with researchers exploring new qubit technologies, error correction methods, and potential applications across science and industry.
    """
    
    # Test with different user preferences
    test_preferences = [
        {"response_length": "short"},
        {"response_length": "medium"},
        {"response_length": "long"}
    ]
    
    for prefs in test_preferences:
        print(f"\nTesting with preferences: {prefs}")
        prepared = ui_adaptability_manager.prepare_response_for_display(sample_response, prefs)
        print(f"Initial content length: {len(prepared['initial_content'])}")
        print(f"Has more content: {prepared['has_more']}")
        print(f"Total sections: {len(prepared.get('expanded_sections', []))}")
    
    # Test feedback UI generation
    message_id = "test_message_123"
    feedback_ui = ui_adaptability_manager.generate_feedback_ui(message_id, prepared)
    print("\nFeedback UI elements:")
    print(f"Basic feedback buttons: {len(feedback_ui['feedback_buttons'])}")
    if "expansion_controls" in feedback_ui:
        print(f"Expansion controls: {len(feedback_ui['expansion_controls'])}")
    
    print("\nTest completed.")


if __name__ == "__main__":
    test_ui_adaptability()
