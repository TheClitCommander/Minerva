"""Improvements for Minerva's AI response handling"""

import re
from datetime import datetime

def get_template_response(message):
    """Generate a templated response for common question patterns."""
    message_lower = message.lower().strip()
    
    # Greeting patterns
    if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
        return "Hello! I'm Minerva, your AI assistant. How can I help you today?"
    
    # Questions about capabilities
    if "what can you do" in message_lower or "your capabilities" in message_lower:
        return "I can answer questions, provide information, and assist with various tasks. Feel free to ask me anything, and I'll do my best to help!"
    
    # Time/date related
    if "what time" in message_lower or "current time" in message_lower or "what day" in message_lower:
        return f"I don't have access to real-time data, but I can tell you that when this response was generated, it was {datetime.now().strftime('%H:%M on %B %d, %Y')}."
    
    # Self-identity questions
    if "who are you" in message_lower or "your name" in message_lower:
        return "I am Minerva, an AI assistant designed to provide helpful information and engage in conversations."
    
    # General knowledge
    if "what is" in message_lower:
        topic = message_lower.split("what is")[1].strip().rstrip("?")
        return f"{topic.capitalize()} refers to a concept or entity in our world. To provide you with accurate information about {topic}, I would need more specifics about what aspect you're interested in."
    
    # How-to questions
    if message_lower.startswith("how to"):
        topic = message_lower[7:].strip().rstrip("?")
        return f"To {topic}, you would typically follow a process that involves several steps. The specific approach depends on your exact goals and context. Could you provide more details about what you're trying to accomplish?"
    
    # Why questions
    if message_lower.startswith("why"):
        topic = message_lower[3:].strip().rstrip("?")
        return f"There are several possible reasons for {topic}. The most common explanations involve various factors including context, history, and specific circumstances. Would you like me to explore any particular aspect of this question?"
    
    # Very short queries
    if len(message_lower.split()) < 3:
        return "I need a bit more information to provide a helpful response. Could you please ask a more detailed question?"
    
    # No template matched
    return None

def process_gpt_response_improved(message):
    """Process a message and return a reliable AI response."""
    print(f"[AI DEBUG] Processing message: {message}")
    
    # Prevent duplicate processing of the same message
    if hasattr(process_gpt_response_improved, "last_message") and process_gpt_response_improved.last_message == message:
        print(f"[WARNING] Prevented duplicate AI processing for: {message}")
        return "I've already processed this message. Please try a different question."
    
    # Track this message to prevent duplicates
    process_gpt_response_improved.last_message = message
    
    # Try to use a template response first
    template_response = get_template_response(message)
    if template_response:
        print(f"[AI DEBUG] Used template response for: {message}")
        return template_response
    
    # If no template matches and no AI model is available, return a generic response
        print("[ERROR] No AI models available.")
        return "I understand you're interested in this topic. To provide a more helpful response, could you rephrase your question or provide additional details about what you'd like to know?"
    
    try:
        # Format the prompt for better results
        formatted_prompt = f"User: {message}\nAssistant:"
        print(f"[AI DEBUG] Using formatted prompt: {formatted_prompt}")
        
        # Generate with more conservative parameters
            formatted_prompt,
            max_length=80,  # Shorter for coherence
            do_sample=True,
            temperature=0.2,  # Lower for consistency
            top_k=30,
            top_p=0.85
        )
        
        print(f"[AI DEBUG] Model raw output: {output}")
        
        # Extract response
        if output and isinstance(output, list) and len(output) > 0:
            generated_text = output[0]['generated_text'].strip()
            
            # Basic response extraction
            if "Assistant:" in generated_text:
                response = generated_text.split("Assistant:")[1].strip()
            else:
                response = generated_text.replace(formatted_prompt, "").strip()
            
            # Check if the response is too similar to the input
            if message.lower() in response.lower() or len(response) < 10:
                # Fall back to template
                return get_template_response(message) or "I'd like to provide a more specific answer to your question. Could you please provide more details or rephrase your question?"
                
            return response
        else:
            print("[ERROR] Invalid model output structure")
    except Exception as e:
        print(f"[ERROR] Error processing response: {e}")
        import traceback
        traceback.print_exc()
    
    # Default fallback
    return "I understand you're interested in this topic. To provide a more helpful response, could you rephrase your question or provide additional details about what you'd like to know?"
