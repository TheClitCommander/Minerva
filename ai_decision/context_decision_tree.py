"""
Context-Aware Decision Tree for AI Response Selection

This module analyzes user context, past interactions, and feedback patterns
to determine the best response approach dynamically.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextDecisionTree:
    """
    Implements a decision tree to analyze user context and determine optimal AI response strategies.
    """

    def __init__(self):
        """
        Initialize decision tree with predefined conditions.
        """
        self.rules = {
            "short_responses": ["be concise", "shorter please", "brief", "summarize", "keep it short"],
            "detailed_responses": ["explain in detail", "give more information", "elaborate", "comprehensive", "thorough"],
            "formal_tone": ["be professional", "use formal language", "formal tone", "professional language"],
            "casual_tone": ["be casual", "keep it simple", "friendly tone", "conversational"],
            "technical_explanation": [
                "explain like an expert", "use technical terms", "technical details", "technical language",
                "advanced concepts", "technical concepts", "advanced explanation", "technical description", 
                "with technical terms", "for experts", "technically accurate", "in-depth technical", 
                "highly detailed technical"
            ],
        }

    def analyze_context(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user input and determine response adjustments.
        
        Args:
            user_input: The message provided by the user.
        
        Returns:
            A dictionary of response adjustments.
        """
        adjustments = {
            "length": "standard",
            "tone": "neutral",
            "detail_level": "balanced",
        }

        for key, triggers in self.rules.items():
            if any(trigger in user_input.lower() for trigger in triggers):
                if key == "short_responses":
                    adjustments["length"] = "short"
                elif key == "detailed_responses":
                    adjustments["length"] = "long"
                elif key == "formal_tone":
                    adjustments["tone"] = "formal"
                elif key == "casual_tone":
                    adjustments["tone"] = "casual"
                elif key == "technical_explanation":
                    adjustments["detail_level"] = "technical"

        logger.info(f"Context Analysis: {adjustments}")
        return adjustments

# Create an instance of the decision tree
decision_tree = ContextDecisionTree()

if __name__ == "__main__":
    # Example usage
    test_input = "Can you be more detailed in your explanation?"
    result = decision_tree.analyze_context(test_input)
    print(f"Decision Tree Output: {json.dumps(result, indent=2)}")
