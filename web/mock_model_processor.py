"""
Mock model processor for testing Minerva's Boss AI functionality.
This simulates different AI models with various capabilities and performance characteristics.
"""

import asyncio
import random
import logging
import time
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class MockModelProcessor:
    """
    A mock model processor that simulates responses from different AI models
    with configurable capabilities, failures, and response patterns.
    """
    
    def __init__(self, model_name: str):
        """
        Initialize the mock model processor.
        
        Args:
            model_name: Name of the model to simulate
        """
        self.model_name = model_name
        
        # Configurable model characteristics
        self.capability_score = 7.0  # Default capability (1-10 scale)
        self.research_capability = 6.0  # Research-specific capability
        self.technical_capability = 6.0  # Technical knowledge capability
        self.creative_capability = 6.0  # Creative capability
        self.reasoning_capability = 6.0  # Logical reasoning capability
        
        # Failure simulation
        self.failure_rate = 0.05  # 5% chance of failure
        self.slow_response_rate = 0.10  # 10% chance of slow response
        self.token_limit = 4000  # Simulated token limit
        
        # Performance characteristics
        self.avg_response_time = 2.0  # Average response time in seconds
        self.response_time_variance = 0.5  # Variance in response time
        
        # Set model-specific defaults
        self._set_model_defaults()
    
    def _set_model_defaults(self):
        """Set default capabilities based on model name."""
        if "gpt-4" in self.model_name.lower():
            self.capability_score = 9.0
            self.research_capability = 8.5
            self.technical_capability = 9.0
            self.creative_capability = 8.0
            self.reasoning_capability = 9.0
            self.token_limit = 8000
        
        elif "claude" in self.model_name.lower():
            self.capability_score = 8.5
            self.research_capability = 8.0
            self.technical_capability = 8.0
            self.creative_capability = 8.5
            self.reasoning_capability = 8.5
            self.token_limit = 9000
        
        elif "gemini" in self.model_name.lower():
            self.capability_score = 8.0
            self.research_capability = 7.5
            self.technical_capability = 8.0
            self.creative_capability = 7.0
            self.reasoning_capability = 8.0
            self.token_limit = 7000
        
        elif "mistral" in self.model_name.lower():
            self.capability_score = 7.5
            self.research_capability = 7.0
            self.technical_capability = 7.5
            self.creative_capability = 6.5
            self.reasoning_capability = 7.0
            self.token_limit = 6000
        
        elif "llama" in self.model_name.lower():
            self.capability_score = 7.0
            self.research_capability = 6.5
            self.technical_capability = 7.0
            self.creative_capability = 6.0
            self.reasoning_capability = 7.0
            self.token_limit = 5000
    
    def __call__(self, message: str, **kwargs) -> Dict[str, Any]:
        """Make the MockModelProcessor directly callable.
        This allows it to be used as a processor function."""
        # Extract keywords from the message
        keywords = self._extract_keywords(message)
        
        # Simulate processing time
        response_time = self._calculate_response_time()
        
        # Generate response using the appropriate method
        response_text = self._generate_general_response(keywords, message)
        
        # Return a formatted response dictionary
        return {
            "error": False,
            "model": self.model_name,
            "response": response_text,
            "processing_time": response_time,
            "confidence": self._calculate_confidence(message),
            "metadata": {
                "tokens_used": len(response_text) // 4,  # Rough token estimation
                "capability_score": self.capability_score
            }
        }
        
    async def process_message(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Simulate processing a message with the mock model.
        
        Args:
            message: Input message to process
            **kwargs: Additional arguments
            
        Returns:
            Dict containing the simulated response and metadata
        """
        # Simulate processing time
        response_time = self._calculate_response_time()
        await asyncio.sleep(response_time)
        
        # Check for simulated failure
        if random.random() < self.failure_rate:
            logger.warning(f"Simulated failure for model {self.model_name}")
            return {
                "error": True,
                "error_message": f"Model {self.model_name} failed to process the request",
                "model": self.model_name,
                "processing_time": response_time
            }
        
        # Generate a simulated response
        response = self._generate_simulated_response(message, **kwargs)
        
        return {
            "error": False,
            "model": self.model_name,
            "response": response,
            "processing_time": response_time,
            "confidence": self._calculate_confidence(message),
            "metadata": {
                "tokens_used": len(response) // 4,  # Rough token estimation
                "capability_score": self.capability_score,
                "research_capability": self.research_capability,
                "technical_capability": self.technical_capability
            }
        }
    
    def _calculate_response_time(self) -> float:
        """Calculate a simulated response time."""
        base_time = self.avg_response_time
        
        # Add variance
        time_with_variance = base_time + random.uniform(
            -self.response_time_variance, 
            self.response_time_variance
        )
        
        # Occasionally simulate a slow response
        if random.random() < self.slow_response_rate:
            time_with_variance *= 3
        
        return max(0.1, time_with_variance)  # Ensure minimum response time
    
    def _calculate_confidence(self, message: str) -> float:
        """
        Calculate a simulated confidence score based on message content and model capabilities.
        
        Args:
            message: Input message
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence derived from capability score
        base_confidence = self.capability_score / 10.0
        
        # Adjust based on message length and complexity
        length_factor = min(1.0, len(message) / 1000)  # Longer messages might reduce confidence
        
        # Detect query type and adjust based on specialized capabilities
        msg_lower = message.lower()
        
        if any(term in msg_lower for term in ["research", "analyze", "study", "investigate"]):
            specialty_factor = self.research_capability / 10.0
        elif any(term in msg_lower for term in ["code", "program", "algorithm", "function"]):
            specialty_factor = self.technical_capability / 10.0
        elif any(term in msg_lower for term in ["create", "design", "imagine", "generate"]):
            specialty_factor = self.creative_capability / 10.0
        elif any(term in msg_lower for term in ["reason", "logic", "solve", "evaluate"]):
            specialty_factor = self.reasoning_capability / 10.0
        else:
            specialty_factor = base_confidence
        
        # Random variance factor (±10%)
        variance = random.uniform(-0.1, 0.1)
        
        # Calculate final confidence score
        confidence = (base_confidence * 0.6) + (specialty_factor * 0.4) + variance
        
        # Clamp between 0.1 and 1.0
        return max(0.1, min(1.0, confidence))
    
    def _generate_simulated_response(self, message: str, **kwargs) -> str:
        """
        Generate a simulated response based on the input message.
        
        Args:
            message: Input message
            **kwargs: Additional context
            
        Returns:
            Simulated response text
        """
        # Extract keywords to make response seem relevant
        keywords = self._extract_keywords(message)
        task_type = kwargs.get("task_type", "general")
        
        # Structure responses based on task type
        if task_type == "research":
            return self._generate_research_response(keywords, message)
        elif task_type == "technical":
            return self._generate_technical_response(keywords, message)
        elif task_type == "creative":
            return self._generate_creative_response(keywords, message)
        else:
            return self._generate_general_response(keywords, message)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from the text."""
        # Simple keyword extraction
        words = text.lower().split()
        # Filter out common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about", "is", "are"}
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Return up to 10 keywords
        return keywords[:10]
    
    def _generate_research_response(self, keywords: List[str], message: str) -> str:
        """Generate a research-focused response."""
        # Research response structure
        quality_level = self.research_capability
        
        # Structure improves with higher capability models
        if quality_level > 8.0:
            sections = ["Introduction", "Background", "Methodology", "Findings", "Analysis", "Conclusion"]
        elif quality_level > 6.0:
            sections = ["Introduction", "Findings", "Analysis", "Conclusion"]
        else:
            sections = ["Introduction", "Findings", "Conclusion"]
        
        response = f"# Research Report on {' '.join(keywords[:3]).title()}\n\n"
        
        for section in sections:
            response += f"## {section}\n\n"
            # Generate 1-3 paragraphs per section based on quality
            paragraphs = max(1, int(quality_level / 3))
            
            for _ in range(paragraphs):
                # Generate paragraph with keywords
                para_length = random.randint(3, 6) * int(quality_level)
                paragraph = f"This section addresses {random.choice(keywords)} "
                paragraph += f"and its relationship to {random.choice(keywords)}. "
                paragraph += f"Analysis shows important connections between {', '.join(random.sample(keywords, min(3, len(keywords))))}. "
                
                # Add some data points for higher quality responses
                if quality_level > 7.0:
                    paragraph += f"Research indicates a {random.randint(20, 80)}% increase in {random.choice(keywords)} "
                    paragraph += f"over the past {random.randint(2, 5)} years. "
                
                response += paragraph + "\n\n"
            
            # Add bullet points for some sections
            if section in ["Findings", "Analysis"] and quality_level > 6.5:
                response += "Key points:\n"
                for i in range(3):
                    response += f"* {random.choice(keywords).title()} demonstrates significant impact on outcomes\n"
                response += "\n"
        
        return response
    
    def _generate_technical_response(self, keywords: List[str], message: str) -> str:
        """Generate a technical/code-focused response."""
        quality_level = self.technical_capability
        
        response = f"# Technical Analysis: {' '.join(keywords[:2]).title()}\n\n"
        
        # Introduction
        response += "## Overview\n\n"
        response += f"This technical analysis explores {' and '.join(keywords[:3])}. "
        response += f"The implementation approach focuses on efficiency and scalability.\n\n"
        
        # Technical details
        response += "## Technical Details\n\n"
        response += f"The {keywords[0] if keywords else 'system'} architecture consists of several components:\n\n"
        
        for i in range(min(4, len(keywords))):
            response += f"### {keywords[i].title()} Component\n\n"
            response += f"This component handles the {keywords[i]} functionality through a modular design.\n\n"
        
        # Add code example for higher quality responses
        if quality_level > 7.0:
            response += "## Implementation Example\n\n"
            response += "```python\n"
            response += f"def process_{keywords[0] if keywords else 'data'}(input_data):\n"
            response += "    # Initialize processing\n"
            response += "    results = []\n"
            response += f"    for item in input_data:\n"
            response += f"        # Process each {keywords[1] if len(keywords) > 1 else 'item'}\n"
            response += f"        processed = analyze_{keywords[1] if len(keywords) > 1 else 'item'}(item)\n"
            response += "        results.append(processed)\n"
            response += "    \n"
            response += "    # Combine results\n"
            response += "    return {\n"
            response += "        'status': 'success',\n"
            response += "        'processed_count': len(results),\n"
            response += "        'results': results\n"
            response += "    }\n"
            response += "```\n\n"
        
        # Conclusion
        response += "## Summary\n\n"
        response += f"The approach outlined above provides an efficient solution for {' and '.join(keywords[:2])}. "
        response += "Implementation should follow best practices for maintainability and scalability."
        
        return response
    
    def _generate_creative_response(self, keywords: List[str], message: str) -> str:
        """Generate a creative-focused response."""
        quality_level = self.creative_capability
        
        response = f"# Creative Concept: {' '.join(keywords[:3]).title()}\n\n"
        
        # Introduction
        response += "## Vision\n\n"
        response += f"This creative concept explores {' and '.join(keywords[:3])} from a unique perspective. "
        response += f"The approach aims to inspire and engage through innovative design.\n\n"
        
        # Main sections
        sections = ["Concept Development", "Design Elements", "Narrative Structure", "Audience Engagement"]
        for section in sections[:int(quality_level / 2)]:
            response += f"## {section}\n\n"
            response += f"The {section.lower()} phase incorporates {random.choice(keywords)} as a central element, "
            response += f"with {random.choice(keywords)} providing contextual richness. "
            
            if quality_level > 7.5:
                response += "Key considerations include:\n\n"
                for i in range(3):
                    response += f"* {random.choice(keywords).title()} integration through visual motifs\n"
                response += "\n"
            else:
                response += f"This creates a cohesive experience centered around {random.choice(keywords)}.\n\n"
        
        # Visual description for higher quality responses
        if quality_level > 7.0:
            response += "## Visual Direction\n\n"
            response += "The proposed visual style balances:\n\n"
            response += f"* **Color Palette**: Dominated by tones that evoke {random.choice(keywords)}\n"
            response += f"* **Typography**: Clean, modern fonts that enhance readability while conveying {random.choice(keywords)}\n"
            response += f"* **Imagery**: Abstract representations of {' and '.join(random.sample(keywords, min(2, len(keywords))))}\n\n"
        
        # Conclusion
        response += "## Implementation Roadmap\n\n"
        response += f"The creative concept can be implemented through a phased approach, prioritizing {random.choice(keywords)} "
        response += f"in the initial stage, followed by integration of {' and '.join(random.sample(keywords, min(2, len(keywords))))}."
        
        return response
    
    def _generate_general_response(self, keywords: List[str], message: str) -> str:
        """Generate a general purpose response."""
        quality_level = self.capability_score
        
        response = f"# Analysis: {' '.join(keywords[:3]).title()}\n\n"
        
        # Introduction
        response += "## Overview\n\n"
        response += f"This analysis addresses {' and '.join(keywords[:3])}. "
        response += f"The key aspects examined include relevance, impact, and future implications.\n\n"
        
        # Main content
        response += "## Key Findings\n\n"
        
        # Generate more detailed content for higher capability models
        if quality_level > 7.5:
            response += "The analysis reveals several important insights:\n\n"
            for i in range(4):
                response += f"### {keywords[i % len(keywords)].title()} Analysis\n\n"
                response += f"Examination of {keywords[i % len(keywords)]} shows significant patterns. "
                response += f"The relationship between {keywords[i % len(keywords)]} and {keywords[(i+1) % len(keywords)]} "
                response += f"demonstrates {random.choice(['positive', 'negative', 'complex', 'neutral'])} correlation. "
                response += f"This suggests implications for {keywords[(i+2) % len(keywords)]}.\n\n"
        else:
            for i in range(3):
                response += f"* {keywords[i % len(keywords)].title()}: Shows {random.choice(['increasing', 'decreasing', 'stable', 'variable'])} trends\n"
            response += "\n"
            response += f"These findings indicate that {random.choice(keywords)} plays a central role in the overall system.\n\n"
        
        # Recommendations
        response += "## Recommendations\n\n"
        response += f"Based on the analysis of {', '.join(keywords[:3])}, the following recommendations are proposed:\n\n"
        
        for i in range(3):
            response += f"{i+1}. Implement strategies to enhance {keywords[i % len(keywords)]}\n"
        
        # Conclusion
        response += "\n## Conclusion\n\n"
        response += f"The analysis provides valuable insights into {' and '.join(keywords[:2])}. "
        response += f"By addressing the recommendations outlined above, significant improvements can be achieved."
        
        return response
