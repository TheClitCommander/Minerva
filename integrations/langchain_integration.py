"""
LangChain Integration for Minerva

This module provides integration with the LangChain framework,
allowing Minerva to leverage LangChain's capabilities for
building applications with LLMs.
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger
from pydantic import BaseModel

# Import base integration
from integrations.base_integration import BaseIntegration

class LangChainIntegration(BaseIntegration):
    """Integration with LangChain framework."""
    
    def __init__(self, framework_path: str = None):
        """Initialize LangChain integration."""
        # Use default framework path if not provided
        if framework_path is None:
            # Default to a directory in the project for LangChain
            framework_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                         "frameworks/langchain")
            
        super().__init__(
            framework_name="LangChain",
            framework_path=framework_path
        )
        
        self.capabilities = ["code_generation", "task_execution", "chain_of_thought", "agent_creation"]
        
        # Check if LangChain is installed
        self.api_available = False
        self.cli_available = False
        
        # Check for API availability
        try:
            import langchain
            
            self.api_available = True
            logger.info("LangChain API is available")
        except ImportError:
            logger.warning("LangChain API is not available. Install with: pip install langchain")
        
        # Check for OpenAI API key - but don't make it a requirement
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key and self.api_available:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable for complete functionality.")
            # Don't disable API just because OpenAI is not available
            # self.api_available = False
    
    def is_available(self) -> bool:
        """Check if LangChain is available for use."""
        return self.api_available or self.cli_available
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the LangChain integration."""
        status = {
            "name": self.name,
            "api_available": self.api_available,
            "cli_available": self.cli_available,
            "openai_api_key": bool(self.openai_api_key),
            "status": "operational" if self.is_available() else "unavailable"
        }
        
        # Attempt to make a simple call if API is available
        if self.api_available and self.openai_api_key:
            try:
                from langchain.llms import OpenAI
                from langchain.chains import LLMChain
                from langchain.prompts import PromptTemplate
                
                # Create a simple prompt template
                template = "Say hello to {name}."
                prompt = PromptTemplate(template=template, input_variables=["name"])
                
                # Initialize OpenAI LLM with minimal tokens
                llm = OpenAI(temperature=0, max_tokens=10)
                
                # Create chain
                chain = LLMChain(llm=llm, prompt=prompt)
                
                # Run chain with minimal input
                result = chain.run(name="Minerva")
                
                status["test_result"] = result
                status["test_success"] = True
            except Exception as e:
                status["test_success"] = False
                status["error"] = str(e)
        
        return status
    
    def generate_code(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate code using LangChain.
        
        Args:
            prompt: The prompt for code generation
            context: Optional context for the code generation
            
        Returns:
            Dictionary with code generation results
        """
        if not self.api_available:
            return {
                "status": "error",
                "code": "",
                "note": "LangChain API is not available. Install with: pip install langchain"
            }
        
        try:
            from langchain.llms import OpenAI
            from langchain.chains import LLMChain
            from langchain.prompts import PromptTemplate
            
            # Create a code generation prompt template
            template = """You are an expert programmer. Your task is to generate high-quality, functional code based on the given prompt.
            
            {context_text}
            
            Prompt: {prompt}
            
            Generate only the code without explanations:
            ```{language}
            """
            
            # Determine language or default to Python
            language = "python"
            if context and "language:" in context.lower():
                for line in context.split("\n"):
                    if line.lower().startswith("language:"):
                        language = line.split(":", 1)[1].strip()
            
            # Set up context text
            context_text = ""
            if context:
                context_text = f"Additional context:\n{context}\n"
            
            # Create the prompt template
            prompt_template = PromptTemplate(
                template=template,
                input_variables=["prompt", "context_text", "language"]
            )
            
            # Initialize OpenAI LLM
            llm = OpenAI(temperature=0.2, max_tokens=1500)
            
            # Create and run the chain
            chain = LLMChain(llm=llm, prompt=prompt_template)
            raw_result = chain.run(prompt=prompt, context_text=context_text, language=language)
            
            # Process the result to extract code
            code = raw_result.strip()
            
            # Clean up any trailing backticks
            if "```" in code:
                parts = code.split("```", 1)
                if len(parts) > 1:
                    code = parts[0]
                else:
                    code = code.replace("```", "")
            
            return {
                "status": "success",
                "code": code,
                "language": language,
                "note": "Code generated using LangChain"
            }
            
        except Exception as e:
            logger.error(f"Error generating code with LangChain: {str(e)}")
            return {
                "status": "error",
                "code": "",
                "error": str(e),
                "note": "Failed to generate code with LangChain"
            }
    
    def execute_task(self, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a task using LangChain.
        
        Args:
            task: The task to execute
            context: Optional context for the task
            
        Returns:
            Dictionary with task execution results
        """
        if not self.api_available:
            return {
                "status": "error",
                "result": "",
                "note": "LangChain API is not available. Install with: pip install langchain"
            }
        
        try:
            from langchain.agents import load_tools, initialize_agent, AgentType
            from langchain.llms import OpenAI
            from langchain.memory import ConversationBufferMemory
            
            # Initialize OpenAI LLM
            llm = OpenAI(temperature=0)
            
            # Load tools for the agent
            tools = load_tools(["llm-math"], llm=llm)
            
            # Initialize conversation memory
            memory = ConversationBufferMemory(memory_key="chat_history")
            
            # Initialize agent
            agent = initialize_agent(
                tools, 
                llm, 
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION, 
                verbose=True,
                memory=memory
            )
            
            # Add context to the task if provided
            full_task = task
            if context:
                full_task = f"Context: {context}\nTask: {task}"
            
            # Run the agent
            result = agent.run(full_task)
            
            return {
                "status": "success",
                "result": result,
                "note": "Task executed using LangChain agent"
            }
            
        except Exception as e:
            logger.error(f"Error executing task with LangChain: {str(e)}")
            return {
                "status": "error",
                "result": "",
                "error": str(e),
                "note": "Failed to execute task with LangChain"
            }
    
    def create_agent(self, agent_type: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a LangChain agent with specific capabilities.
        
        Args:
            agent_type: Type of agent to create (e.g., 'zero-shot', 'react', 'conversational')
            options: Options for agent creation
            
        Returns:
            Dictionary with agent creation results
        """
        if not self.api_available:
            return {
                "status": "error",
                "note": "LangChain API is not available. Install with: pip install langchain"
            }
            
        if options is None:
            options = {}
        
        try:
            from langchain.agents import load_tools, initialize_agent, AgentType
            from langchain.llms import OpenAI
            
            # Map agent type string to AgentType enum
            agent_types = {
                "zero-shot": AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                "react": AgentType.REACT_DOCSTORE,
                "conversational": AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                "structured-chat": AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                "openai-functions": AgentType.OPENAI_FUNCTIONS
            }
            
            if agent_type not in agent_types:
                return {
                    "status": "error",
                    "note": f"Unknown agent type: {agent_type}. Available types: {', '.join(agent_types.keys())}"
                }
            
            # Get agent type
            agent_enum = agent_types[agent_type]
            
            # Initialize OpenAI LLM
            temperature = options.get("temperature", 0)
            model_name = options.get("model_name", "text-davinci-003")
            llm = OpenAI(temperature=temperature, model_name=model_name)
            
            # Load tools based on options
            tool_names = options.get("tools", ["llm-math", "terminal"])
            tools = load_tools(tool_names, llm=llm)
            
            # Initialize agent
            agent = initialize_agent(
                tools, 
                llm, 
                agent=agent_enum, 
                verbose=options.get("verbose", True)
            )
            
            return {
                "status": "success",
                "agent_type": agent_type,
                "tools": tool_names,
                "note": f"Successfully created {agent_type} agent with LangChain"
            }
            
        except Exception as e:
            logger.error(f"Error creating agent with LangChain: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "note": "Failed to create agent with LangChain"
            }
