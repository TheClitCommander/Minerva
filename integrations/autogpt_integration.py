"""
AutoGPT Integration for Jarvis AI Assistant

This module provides enhanced integration with the AutoGPT framework.
"""

import os
import sys
import subprocess
import json
from typing import Dict, List, Optional, Any
from loguru import logger

from .base_integration import BaseIntegration

class AutoGPTIntegration(BaseIntegration):
    """Enhanced integration with AutoGPT framework."""
    
    def __init__(self, framework_path: str):
        """
        Initialize the AutoGPT integration.
        
        Args:
            framework_path: Path to the AutoGPT installation
        """
        super().__init__("AutoGPT", framework_path)
        
        self.api_available = False
        self.cli_available = False
        
        # Add these capabilities
        self.capabilities = ["autonomous_task_execution", "code_generation", "web_search"]
        
        try:
            # Check if AutoGPT is installed via pip
            try:
                import autogpt
                self.api_available = True
                logger.info("AutoGPT package is installed")
            except ImportError:
                logger.warning("AutoGPT package is not installed")
            
            # Check if CLI is available
            self.cli_available = self._check_cli_availability()
            
            logger.info(f"AutoGPT API available: {self.api_available}")
            logger.info(f"AutoGPT CLI available: {self.cli_available}")
            
        except Exception as e:
            logger.error(f"Error initializing AutoGPT integration: {str(e)}")
    
    def _check_api_availability(self) -> bool:
        """Check if the AutoGPT API is available."""
        try:
            # Placeholder for actual API availability check
            # For now, assume it's not available
            return False
        except Exception as e:
            logger.warning(f"Could not check AutoGPT API availability: {str(e)}")
            return False
    
    def _check_cli_availability(self) -> bool:
        """Check if the AutoGPT CLI is available."""
        try:
            # Check if run.py exists
            run_script = os.path.join(self.framework_path, "run.py")
            cli_available = os.path.exists(run_script)
            
            if not cli_available:
                # Also check for autogpt.py
                run_script = os.path.join(self.framework_path, "autogpt.py")
                cli_available = os.path.exists(run_script)
                
            return cli_available
        except Exception as e:
            logger.warning(f"Could not check AutoGPT CLI availability: {str(e)}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """
        Get a list of capabilities provided by this framework.
        
        Returns:
            List of capability strings
        """
        return [
            "autonomous_task_execution",
            "self_improvement",
            "goal_decomposition",
            "code_generation"
        ]
    
    def _get_version(self) -> str:
        """
        Get the version of AutoGPT.
        
        Returns:
            Version string
        """
        try:
            # Try to find version in various potential locations
            version_locations = [
                os.path.join(self.framework_path, "VERSION"),
                os.path.join(self.framework_path, "version.txt"),
                os.path.join(self.framework_path, "autogpt", "version.py"),
            ]
            
            for location in version_locations:
                if os.path.exists(location):
                    with open(location, "r") as f:
                        content = f.read().strip()
                        if content:
                            # For Python files, look for __version__ = "x.y.z"
                            if location.endswith(".py"):
                                import re
                                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                                if match:
                                    return match.group(1)
                            else:
                                return content
            
            # If version not found, check package metadata
            try:
                from importlib.metadata import version
                return version("autogpt")
            except:
                pass
                
            return "unknown"
        except Exception as e:
            logger.warning(f"Could not determine AutoGPT version: {str(e)}")
            return "unknown"
    
    def _generate_using_api(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate code using AutoGPT API.
        
        Args:
            prompt: The code generation prompt
            context: Optional context information
            
        Returns:
            Dict containing the generated code and metadata
            
        Raises:
            NotImplementedError: If the API is not available
        """
        if not self.api_available:
            raise NotImplementedError("AutoGPT API not available")
        
        # Placeholder for actual API implementation
        # This would be replaced with actual API calls when available
        raise NotImplementedError("AutoGPT API method not implemented")
    
    def _generate_using_cli(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate code using AutoGPT CLI.
        
        Args:
            prompt: The code generation prompt
            context: Optional context information
            
        Returns:
            Dict containing the generated code and metadata
            
        Raises:
            RuntimeError: If the CLI command fails
        """
        if not self.cli_available:
            raise RuntimeError("AutoGPT CLI not available")
        
        # Determine the run script path
        run_script = os.path.join(self.framework_path, "run.py")
        if not os.path.exists(run_script):
            run_script = os.path.join(self.framework_path, "autogpt.py")
        
        # Prepare the command
        cmd = [
            "python",
            run_script,
            "--objective", prompt,
            "--max_iterations", "5"
        ]
        
        if context:
            # Create a temporary file with the context
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
                f.write(context.encode("utf-8"))
                context_file = f.name
            
            cmd.extend(["--context_file", context_file])
        
        # Run the command
        try:
            result = subprocess.run(
                cmd,
                cwd=self.framework_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"AutoGPT CLI failed: {result.stderr}")
                raise RuntimeError(f"AutoGPT CLI error: {result.stderr}")
            
            # Extract code from output
            code = self._extract_code_from_output(result.stdout)
            
            # Clean up context file if created
            if context and 'context_file' in locals():
                try:
                    os.unlink(context_file)
                except:
                    pass
            
            return {
                "code": code,
                "raw_output": result.stdout,
                "note": "Generated using AutoGPT CLI"
            }
            
        except Exception as e:
            logger.error(f"Error running AutoGPT CLI: {str(e)}")
            raise RuntimeError(f"Error running AutoGPT CLI: {str(e)}")
    
    def _extract_code_from_output(self, output: str) -> str:
        """
        Extract code blocks from CLI output.
        
        Args:
            output: The raw CLI output
            
        Returns:
            Extracted code as a string
        """
        import re
        
        # Look for code blocks using various patterns
        patterns = [
            r'```python\n(.*?)```',  # Markdown code blocks
            r'```\n(.*?)```',  # Generic markdown code blocks
            r'def .*?:.*?return.*?(?=\n\n)',  # Python function definitions
            r'class .*?:.*?(?=\n\n)',  # Python class definitions
        ]
        
        code_blocks = []
        for pattern in patterns:
            matches = re.findall(pattern, output, re.DOTALL)
            code_blocks.extend(matches)
        
        if code_blocks:
            return "\n\n".join(code_blocks)
        
        # If no code blocks found, return the entire output
        return output
    
    def _simulate_code_generation(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate code generation when AutoGPT is not fully available.
        
        Args:
            prompt: The code generation prompt
            context: Optional context information
            
        Returns:
            Dict containing the generated code and metadata
        """
        # This is a fallback method when we can't use AutoGPT directly
        
        # Here we'll provide a simple implementation based on common prompts
        if "fibonacci" in prompt.lower():
            code = """def fibonacci(n):
    \"\"\"Calculate the Fibonacci sequence up to n terms.\"\"\"
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    # Initialize with first two Fibonacci numbers
    fib_sequence = [0, 1]
    
    # Generate the rest of the sequence
    while len(fib_sequence) < n:
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    
    return fib_sequence

# Example usage
if __name__ == "__main__":
    n = 10
    print(f"Fibonacci sequence with {n} terms:")
    print(fibonacci(n))
"""
        else:
            # Generic example for other prompts
            code = """# Generated code based on prompt: {0}
def example_function():
    \"\"\"This is a placeholder function generated based on your prompt.\"\"\"
    # TODO: Implement the actual functionality
    print("Function would implement: {0}")
    return "Implementation placeholder"

# Example usage
if __name__ == "__main__":
    result = example_function()
    print(result)
""".format(prompt)
        
        return {
            "code": code,
            "note": "Generated using fallback mechanism, not actual AutoGPT"
        }
    
    def is_available(self):
        """Check if AutoGPT is available for use."""
        # Log availability for debugging
        logger.info(f"Checking AutoGPT availability: API={self.api_available}, CLI={self.cli_available}")
        return self.api_available or self.cli_available
    
    def generate_code(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate code using AutoGPT.
        
        Args:
            prompt: The code generation prompt
            context: Optional context information
            
        Returns:
            Dict containing the generated code and metadata
        """
        logger.info(f"Generating code with prompt: {prompt[:50]}...")
        
        try:
            # First try to use the API
            return self._generate_using_api(prompt, context)
        except (ImportError, AttributeError, NotImplementedError) as e:
            logger.warning(f"Could not use AutoGPT API: {str(e)}")
            
            try:
                # Then try to use the CLI
                return self._generate_using_cli(prompt, context)
            except Exception as e:
                logger.warning(f"Could not use AutoGPT CLI: {str(e)}")
                
                # Fall back to simulated code generation
                logger.info("Using fallback code generation")
                return self._simulate_code_generation(prompt, context)
    
    def execute_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task using AutoGPT.
        
        Args:
            task: The task description
            context: Optional context information
            
        Returns:
            Dict containing the execution results and metadata
        """
        logger.info(f"Executing task: {task[:50]}...")
        
        # Placeholder for actual task execution
        # This would be replaced with actual implementation when available
        
        return {
            "result": f"AutoGPT would execute the task: {task}",
            "status": "Not completed",
            "note": "This is a placeholder implementation"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if AutoGPT is healthy and functioning.
        
        Returns:
            Dict containing health status information
        """
        status = "healthy" if (self.api_available or self.cli_available) else "degraded"
        
        return {
            "status": status,
            "framework": "AutoGPT",
            "details": {
                "api_available": self.api_available,
                "cli_available": self.cli_available,
                "path_exists": os.path.exists(self.framework_path)
            },
            "version": self._get_version()
        }
