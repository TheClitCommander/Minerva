"""
Framework Manager for Minerva

This module provides enhanced framework integration capabilities for Minerva,
allowing it to seamlessly work with multiple AI frameworks and utilize their
various capabilities.
"""

import os
import sys
import importlib
import importlib.util
import inspect
from typing import Dict, List, Any, Callable, Optional, Type, Union
from pathlib import Path
import json

# Set up logging with fallback
try:
    from loguru import logger
    print("[AI DEBUG] Loguru imported successfully!")
except ImportError:
    import logging
    # Create a logger that mimics loguru's interface
    class LoguruCompatLogger:
        def __init__(self):
            self.logger = logging.getLogger("minerva")
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            
        def debug(self, message, *args, **kwargs):
            self.logger.debug(message, *args, **kwargs)
            
        def info(self, message, *args, **kwargs):
            self.logger.info(message, *args, **kwargs)
            
        def warning(self, message, *args, **kwargs):
            self.logger.warning(message, *args, **kwargs)
            
        def error(self, message, *args, **kwargs):
            self.logger.error(message, *args, **kwargs)
            
        def exception(self, message, *args, **kwargs):
            self.logger.exception(message, *args, **kwargs)
    
    # Use our compatible logger instead
    logger = LoguruCompatLogger()
    print("[AI DEBUG] Created Loguru-compatible logger as fallback")

# Set up logging format
if hasattr(logger, "remove"):
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add("jarvis_logs/framework_manager.log", rotation="10 MB", level="DEBUG")

try:
    from integrations.base_integration import BaseIntegration
    print("[AI DEBUG] BaseIntegration loaded successfully!")
except ImportError:
    try:
        # Try relative import
        from .base_integration import BaseIntegration
        print("[AI DEBUG] BaseIntegration loaded via relative import!")
    except ImportError as e:
        print(f"[ERROR] Cannot import BaseIntegration: {e}")
        # Define a minimal BaseIntegration for basic functionality
        class BaseIntegration:
            """Minimal implementation for BaseIntegration"""
            def __init__(self):
                pass

class FrameworkManager:
    """
    Enhanced manager for AI framework integrations.
    
    Provides capabilities for:
    1. Dynamic loading of AI frameworks
    2. Capability-based routing of tasks
    3. Resource optimization and load balancing
    4. Unified interface for all framework interactions
    """
    
    def __init__(self, registry_path=None):
        """Initialize the FrameworkManager."""
        # Set up logging
        self.logger = logger
        
        # Set the registry path
        if registry_path is None:
            registry_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config/framework_registry.json"
            )
        self.registry_path = registry_path
        
        # Initialize data structures
        self.framework_paths = {}        # Maps framework names to module paths
        self.loaded_frameworks = {}      # Maps framework names to loaded instances
        self.framework_capabilities = {} # Maps framework names to capabilities
        self.capability_scores = {}      # Maps capabilities to framework scores
        
        # Load the registry
        self._load_registry()
        
        # Check AI model availability
        self._check_model_availability()
        
        # Initialize built-in integrations
        try:
            from integrations.autogpt_integration import AutoGPTIntegration
            # Fix: Provide the framework_path parameter
            default_autogpt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frameworks/autogpt")
            self._load_builtin_integration(AutoGPTIntegration(framework_path=default_autogpt_path))
        except ImportError:
            logger.warning("AutoGPT integration not available")
            
        try:
            from integrations.langchain_integration import LangChainIntegration
            self._load_builtin_integration(LangChainIntegration())
        except ImportError:
            logger.warning("LangChain integration not available")
            
        try:
            from integrations.huggingface_integration import HuggingFaceIntegration
            self._load_builtin_integration(HuggingFaceIntegration())
        except ImportError:
            logger.warning("HuggingFace integration not available")
                    
    def _check_model_availability(self):
        """Check and log which AI models are available."""
        print("[AI DEBUG] Checking available AI models...")
        
        # Check AutoGPT
        autogpt_available = False
        try:
            import autogpt
            autogpt_available = True
            print("[AI DEBUG] AutoGPT is available.")
        except ImportError:
            # Look for AutoGPT in known directories
            autogpt_dirs = []
            for name, framework in self.loaded_frameworks.items():
                if "autogpt" in name.lower():
                    autogpt_available = True
                    autogpt_dirs.append(name)
            
            if autogpt_available:
                print(f"[AI DEBUG] AutoGPT is available via loaded frameworks: {', '.join(autogpt_dirs)}")
            else:
                print("[ERROR] AutoGPT is NOT available!")
        
        # Check GPT-4All
        gpt4all_available = False
        try:
            import gpt4all
            gpt4all_available = True
            print("[AI DEBUG] GPT-4All is available.")
        except ImportError:
            # Look for GPT4All in known directories
            gpt4all_dirs = []
            for name, framework in self.loaded_frameworks.items():
                if "gpt4all" in name.lower():
                    gpt4all_available = True
                    gpt4all_dirs.append(name)
            
            if gpt4all_available:
                print(f"[AI DEBUG] GPT-4All is available via loaded frameworks: {', '.join(gpt4all_dirs)}")
            else:
                print("[ERROR] GPT-4All is NOT available!")
        
        # Check Hugging Face
        huggingface_available = False
        try:
            import transformers
            huggingface_available = True
            print(f"[AI DEBUG] Hugging Face Transformers is available (version {transformers.__version__}).")
        except ImportError:
            # Look for Hugging Face in known directories
            hf_dirs = []
            for name, framework in self.loaded_frameworks.items():
                if "huggingface" in name.lower():
                    huggingface_available = True
                    hf_dirs.append(name)
            
            if huggingface_available:
                print(f"[AI DEBUG] Hugging Face is available via loaded frameworks: {', '.join(hf_dirs)}")
            else:
                print("[ERROR] Hugging Face is NOT available!")
        
        # Store availability status
        self.model_availability = {
            "autogpt": autogpt_available,
            "gpt4all": gpt4all_available,
            "huggingface": huggingface_available
        }
        
        # Summary
        available_models = sum(self.model_availability.values())
        if available_models == 0:
            print("[CRITICAL] No AI models are available! Minerva will use fallback templates only.")
        elif available_models == 1:
            print("[WARNING] Only one AI model is available. Multi-model selection will be limited.")
        else:
            print(f"[SUCCESS] {available_models} AI models are available. Multi-model selection is enabled.")
    
    def _load_registry(self) -> None:
        """Load the framework registry from disk."""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r') as f:
                    registry_data = json.load(f)
                    
                # Extract framework paths from registry
                self.framework_paths = registry_data.get('framework_paths', {})
                self.capability_scores = registry_data.get('capability_scores', {})
                
                logger.info(f"Loaded framework registry from {self.registry_path}")
                
                # Preload registered frameworks
                for framework_name, framework_path in self.framework_paths.items():
                    self.load_framework(framework_name, framework_path)
                    
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading registry: {str(e)}")
        else:
            logger.warning(f"Registry file not found at {self.registry_path}")
            self._create_empty_registry()
            
        # Auto-discover frameworks from integrations config
        self._load_from_integrations_config()
            
    def _load_from_integrations_config(self) -> None:
        """Load frameworks from the integrations.json config file"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config/integrations.json"
        )
        
        if not os.path.exists(config_path):
            logger.warning(f"Integrations configuration not found: {config_path}")
            return
            
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                
            # Load frameworks from integrations config
            for integration_type, settings in config.get("integrations", {}).items():
                if settings.get("enabled", False):
                    for path in settings.get("paths", []):
                        if os.path.exists(path):
                            # Extract framework name from path
                            framework_name = os.path.basename(path)
                            self.register_framework(framework_name, path)
                            logger.info(f"Auto-registered framework {framework_name} from {path}")
                            
        except Exception as e:
            logger.error(f"Error loading from integrations config: {str(e)}")
    
    def _create_empty_registry(self) -> None:
        """Create an empty registry file if none exists."""
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump({
                'framework_paths': {},
                'capability_scores': {}
            }, f, indent=4)
        logger.info(f"Created empty framework registry at {self.registry_path}")
    
    def _save_registry(self) -> None:
        """Save the current registry to disk."""
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump({
                'framework_paths': self.framework_paths,
                'capability_scores': self.capability_scores
            }, f, indent=4)
        logger.info(f"Saved framework registry to {self.registry_path}")
    
    def discover_frameworks(self, search_path: str) -> List[Dict[str, Any]]:
        """
        Discover available AI frameworks in the specified directory.
        
        Args:
            search_path: Directory to search for frameworks
            
        Returns:
            List of discovered framework info dictionaries
        """
        discovered = []
        search_path = os.path.abspath(search_path)
        
        if not os.path.isdir(search_path):
            logger.error(f"Search path does not exist: {search_path}")
            return discovered
        
        # Find potential framework directories
        for item in os.listdir(search_path):
            item_path = os.path.join(search_path, item)
            
            if os.path.isdir(item_path):
                # Check if this looks like a framework
                if self._is_potential_framework(item_path, item):
                    framework_info = {
                        'name': self._normalize_framework_name(item),
                        'path': item_path
                    }
                    discovered.append(framework_info)
        
        logger.info(f"Discovered {len(discovered)} potential frameworks in {search_path}")
        return discovered
    
    def _normalize_framework_name(self, name: str) -> str:
        """Normalize framework name for consistent reference.
        
        This method ensures case-insensitive lookups by converting all framework names
        to a standard PascalCase format, regardless of input format.
        """
        # Convert kebab-case or snake_case to PascalCase for framework names
        components = name.replace('-', '_').split('_')
        normalized = ''.join(word.capitalize() for word in components)
        
        # Try to find an exact match in loaded_frameworks
        if normalized in self.loaded_frameworks:
            return normalized
            
        # Try to find a case-insensitive match
        for framework_name in self.loaded_frameworks:
            if framework_name.lower() == normalized.lower():
                print(f"[DEBUG] Found case-insensitive match for '{name}': '{framework_name}'")
                return framework_name
        
        # If no match found, return the normalized name anyway
        print(f"[DEBUG] No exact or case-insensitive match found for '{name}', returning '{normalized}'")
        return normalized
    
    def _is_potential_framework(self, path: str, name: str) -> bool:
        """
        Check if a directory potentially contains an AI framework.
        
        Args:
            path: Path to the directory
            name: Name of the directory
            
        Returns:
            True if the directory looks like it contains an AI framework
        """
        # Simple heuristic: Check if common AI framework markers are present
        markers = [
            'setup.py',
            'requirements.txt',
            'README.md',
            os.path.join('src', name),
            os.path.join(name, '__init__.py'),
            'main.py',
            'agent.py',
            'model.py'
        ]
        
        return any(os.path.exists(os.path.join(path, marker)) for marker in markers)
    
    def register_framework(self, name: str, path: str) -> bool:
        """
        Register a framework with the manager.
        
        Args:
            name: Name of the framework
            path: Path to the framework directory
            
        Returns:
            True if registration was successful
        """
        if not os.path.isdir(path):
            logger.error(f"Framework path does not exist: {path}")
            return False
        
        normalized_name = self._normalize_framework_name(name)
        self.framework_paths[normalized_name] = path
        
        # Save updated registry
        self._save_registry()
        
        # Try to load the framework
        return self.load_framework(normalized_name, path)
    
    def load_framework(self, name: str, path: str = None) -> bool:
        """
        Load a framework into the system.
        
        Args:
            name: Name of the framework
            path: Path to the framework (optional if already registered)
            
        Returns:
            True if loading was successful
        """
        normalized_name = self._normalize_framework_name(name)
        
        # If already loaded, return success
        if normalized_name in self.loaded_frameworks:
            logger.debug(f"Framework {normalized_name} already loaded")
            return True
        
        # Get path if not provided
        if path is None:
            if normalized_name in self.framework_paths:
                path = self.framework_paths[normalized_name]
            else:
                logger.error(f"No path available for framework: {normalized_name}")
                return False
        
        # Validate the path exists
        if not os.path.isdir(path):
            logger.error(f"Framework path not found: {path}")
            return False
            
        try:
            # Import the integration module for this framework
            module_name = f"{normalized_name.lower()}_integration"
            integration_path = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
            
            # If the integration file doesn't exist, create a template
            if not os.path.exists(integration_path):
                self._create_integration_template(normalized_name, path, integration_path)
            
            # Import the module
            sys.path.insert(0, os.path.dirname(__file__))
            integration_module = importlib.import_module(module_name)
            
            # Get the integration class
            integration_class_name = f"{normalized_name}Integration"
            integration_class = getattr(integration_module, integration_class_name)
            
            # Instantiate the integration
            integration_instance = integration_class(path)
            
            # Store the loaded framework
            self.loaded_frameworks[normalized_name] = integration_instance
            
            # Store capabilities
            self.framework_capabilities[normalized_name] = integration_instance.get_capabilities()
            
            logger.info(f"Successfully loaded framework: {normalized_name}")
            return True
            
        except (ImportError, AttributeError, ModuleNotFoundError) as e:
            logger.error(f"Failed to load framework {normalized_name}: {str(e)}")
            return False
    
    def _load_builtin_integration(self, integration_instance):
        """Load a built-in integration directly from its instance."""
        try:
            if integration_instance.is_available():
                framework_name = integration_instance.name
                self.loaded_frameworks[framework_name] = integration_instance
                self.framework_capabilities[framework_name] = integration_instance.capabilities
                logger.info(f"Loaded built-in integration: {framework_name}")
                return True
            else:
                logger.warning(f"Built-in integration {integration_instance.name} is not available")
                return False
        except Exception as e:
            logger.error(f"Error loading built-in integration: {str(e)}")
            return False
            
    def ensure_huggingface_loaded(self):
        """Force load the HuggingFace integration with error handling.
        
        This method provides a more robust way to ensure HuggingFace is loaded
        by attempting multiple initialization strategies and providing detailed error logs.
        """
        # Check if it's already loaded
        if "huggingface" in self.loaded_frameworks or "HuggingFace" in self.loaded_frameworks:
            logger.info("HuggingFace integration already loaded")
            return True
            
        try:
            # Attempt standard import
            from integrations.huggingface_integration import HuggingFaceIntegration
            
            # Create integration instance with explicit model path
            framework_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frameworks/huggingface")
            integration = HuggingFaceIntegration(framework_path=framework_path)
            
            # Ensure directory exists
            os.makedirs(framework_path, exist_ok=True)
            
            # Check if transformers is available
            try:
                import transformers
                logger.info(f"Found transformers v{transformers.__version__}")
                integration.api_available = True
            except ImportError:
                logger.error("Transformers package not found - HuggingFace integration will not function properly")
                return False
                
            # Force load it regardless of is_available result
            framework_name = integration.name
            self.loaded_frameworks[framework_name] = integration
            self.framework_capabilities[framework_name] = integration.capabilities
            logger.info(f"Successfully loaded HuggingFace integration")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load HuggingFace integration: {str(e)}")
            return False
    
    def _create_integration_template(self, framework_name: str, framework_path: str, output_path: str) -> None:
        """
        Create a template integration file for a framework.
        
        Args:
            framework_name: Name of the framework
            framework_path: Path to the framework
            output_path: Path to write the integration file
        """
        template = f'''"""
{framework_name} Integration for Minerva

This module provides integration with the {framework_name} framework.
"""

import os
import sys
from typing import Dict, List, Any
from loguru import logger

class {framework_name}Integration:
    """Integration with {framework_name} framework."""
    
    def __init__(self, framework_path: str):
        """
        Initialize the {framework_name} integration.
        
        Args:
            framework_path: Path to the {framework_name} installation
        """
        self.framework_path = framework_path
        
        # Set up logging
        logger.info(f"{framework_name} integration initialized at {{framework_path}}")
        
        # Add the framework to the Python path
        sys.path.append(framework_path)
        logger.info(f"Added {{framework_path}} to system path")
        
        try:
            # Import necessary modules from the framework
            # TODO: Import specific modules from {framework_name}
            
            logger.info(f"Successfully imported {framework_name} modules")
        except ImportError as e:
            logger.error(f"Failed to import {framework_name} modules: {{str(e)}}")
            
    def get_capabilities(self) -> List[str]:
        """
        Get a list of capabilities provided by this framework.
        
        Returns:
            List of capability strings
        """
        # TODO: Define actual capabilities for {framework_name}
        return [
            "task_execution",
            "code_generation"
        ]
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this framework.
        
        Returns:
            Dictionary of framework information
        """
        return {{
            "name": "{framework_name}",
            "path": self.framework_path,
            "capabilities": self.get_capabilities(),
            "version": "0.1.0",  # TODO: Extract actual version
            "description": "{framework_name} Integration"
        }}
    
    def generate_code(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate code using this framework.
        
        Args:
            prompt: The code generation prompt
            context: Optional context information
            
        Returns:
            Dict containing the generated code and metadata
        """
        # TODO: Implement code generation for {framework_name}
        return {{
            "code": f"# TODO: Generated code would appear here\\n# This is a fallback method when {framework_name} is not fully integrated",
            "note": "Generated using fallback mechanism, not actual {framework_name}"
        }}
    
    def execute_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task using this framework.
        
        Args:
            task: The task description
            context: Optional context information
            
        Returns:
            Dict containing the execution results and metadata
        """
        # TODO: Implement task execution for {framework_name}
        return {{
            "result": f"{framework_name} would execute the task: {{task}}",
            "status": "Not completed",
            "note": "This is a placeholder implementation"
        }}
'''
        
        # Create the directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the template
        with open(output_path, 'w') as f:
            f.write(template)
            
        logger.info(f"Created integration template for {framework_name} at {output_path}")
    
    def get_all_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all loaded frameworks.
        
        Returns:
            Dictionary of framework information
        """
        info = {}
        for name, integration in self.loaded_frameworks.items():
            info[name] = integration.get_info()
        return info
    
    def get_framework_info(self, framework_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific framework.
        
        Args:
            framework_name: Name of the framework
            
        Returns:
            Dictionary of framework information or None if not found
        """
        normalized_name = self._normalize_framework_name(framework_name)
        
        if normalized_name in self.loaded_frameworks:
            return self.loaded_frameworks[normalized_name].get_info()
        
        return None
    
    def get_all_capabilities(self) -> Dict[str, List[str]]:
        """
        Get a mapping of all capabilities to the frameworks that provide them.
        
        Returns:
            Dictionary mapping capability names to lists of framework names
        """
        capability_map = {}
        
        for framework, capabilities in self.framework_capabilities.items():
            for capability in capabilities:
                if capability not in capability_map:
                    capability_map[capability] = []
                capability_map[capability].append(framework)
                
        return capability_map
    
    def get_frameworks_for_capability(self, capability: str) -> List[str]:
        """
        Get a list of frameworks that provide a specific capability.
        
        Args:
            capability: The capability to look for
            
        Returns:
            List of framework names
        """
        frameworks = []
        
        for framework, capabilities in self.framework_capabilities.items():
            if capability in capabilities:
                frameworks.append(framework)
                
        # Sort by capability score if available
        if capability in self.capability_scores:
            scores = self.capability_scores[capability]
            frameworks.sort(key=lambda f: scores.get(f, 0), reverse=True)
        
        return frameworks
    
    def get_best_framework_for_capability(self, capability: str) -> Optional[str]:
        """
        Get the best framework for a specific capability.
        
        Args:
            capability: The capability to look for
            
        Returns:
            Name of the best framework or None if no framework provides the capability
        """
        frameworks = self.get_frameworks_for_capability(capability)
        return frameworks[0] if frameworks else None
    
    def execute_with_framework(self, framework_name: str, method: str, *args, **kwargs) -> Any:
        """
        Execute a method on a specific framework with improved error handling and case-insensitivity.
        
        Args:
            framework_name: Name of the framework
            method: Name of the method to execute
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method
            
        Returns:
            Result of the method execution
        
        Raises:
            ValueError: If the framework is not loaded or doesn't have the method
        """
        print(f"[DEBUG] Attempting to execute {method} with framework: {framework_name}")
        
        # Try to normalize the name and find the framework
        normalized_name = self._normalize_framework_name(framework_name)
        
        # If normalization didn't find a match, try a direct lookup in loaded_frameworks
        if normalized_name not in self.loaded_frameworks:
            # Let's try a manual case-insensitive search
            for loaded_name in self.loaded_frameworks:
                if loaded_name.lower() == framework_name.lower():
                    print(f"[DEBUG] Found direct case-insensitive match: '{loaded_name}' for '{framework_name}'")
                    normalized_name = loaded_name
                    break
        
        # Check if framework is loaded after all our attempts        
        if normalized_name not in self.loaded_frameworks:
            print(f"[ERROR] Framework not found: {framework_name} (normalized: {normalized_name})")
            print(f"[DEBUG] Available frameworks: {list(self.loaded_frameworks.keys())}")
            raise ValueError(f"Framework not loaded: {framework_name}")
        
        integration = self.loaded_frameworks[normalized_name]
        print(f"[DEBUG] Successfully found framework: {normalized_name}")
        
        if not hasattr(integration, method):
            available_methods = [m for m in dir(integration) if not m.startswith('_')]
            print(f"[ERROR] Method '{method}' not found in framework {normalized_name}")
            print(f"[DEBUG] Available methods: {available_methods}")
            raise ValueError(f"Framework {framework_name} doesn't have method: {method}")
        
        method_func = getattr(integration, method)
        print(f"[DEBUG] Executing {normalized_name}.{method}()")
        return method_func(*args, **kwargs)
    
    def execute_with_capability(self, capability: str, method: str, *args, **kwargs) -> Any:
        """
        Execute a method using the best framework for a capability.
        
        Args:
            capability: The required capability
            method: Name of the method to execute
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method
            
        Returns:
            Result of the method execution
        
        Raises:
            ValueError: If no framework provides the capability
        """
        framework = self.get_best_framework_for_capability(capability)
        
        if not framework:
            raise ValueError(f"No framework available for capability: {capability}")
        
        return self.execute_with_framework(framework, method, *args, **kwargs)
    
    def update_capability_score(self, capability: str, framework: str, score: float) -> None:
        """
        Update the score for a framework's capability.
        
        Args:
            capability: The capability to update
            framework: The framework providing the capability
            score: New score value (0-100)
        """
        normalized_name = self._normalize_framework_name(framework)
        
        if capability not in self.capability_scores:
            self.capability_scores[capability] = {}
            
        self.capability_scores[capability][normalized_name] = max(0, min(100, score))
        
        # Save updated registry
        self._save_registry()
        
        logger.info(f"Updated capability score for {normalized_name}.{capability} to {score}")
    
    def unregister_framework(self, framework_name: str) -> bool:
        """
        Unregister a framework from the manager.
        
        Args:
            framework_name: Name of the framework to unregister
            
        Returns:
            True if unregistration was successful
        """
        normalized_name = self._normalize_framework_name(framework_name)
        
        if normalized_name in self.loaded_frameworks:
            del self.loaded_frameworks[normalized_name]
            
        if normalized_name in self.framework_capabilities:
            del self.framework_capabilities[normalized_name]
            
        if normalized_name in self.framework_paths:
            del self.framework_paths[normalized_name]
            
        # Update capability scores
        for capability, scores in self.capability_scores.items():
            if normalized_name in scores:
                del scores[normalized_name]
        
        # Save updated registry
        self._save_registry()
        
        logger.info(f"Unregistered framework: {normalized_name}")
        return True
    
    def get_framework_by_name(self, name: str) -> Optional[Any]:
        """
        Get a framework integration by name.
        
        Args:
            name: Name of the framework (case-insensitive)
            
        Returns:
            Framework integration instance or None if not found
        """
        # Hardcoded AI model paths
        AI_MODEL_PATHS = {
            "AutoGPT": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frameworks/autogpt"),
            "GPT4All": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frameworks/gpt4all"),
            "HuggingFace": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frameworks/huggingface"),
        }
        
        # Normalize the name for case-insensitive comparison
        name_lower = name.lower()
        
        # Direct match based on loaded frameworks
        for framework_name, instance in self.loaded_frameworks.items():
            if framework_name.lower() == name_lower:
                return instance
        
        # Check for special built-in frameworks not yet loaded
        if name_lower in ["huggingface", "hugging_face", "hugging-face"]:
            logger.info("Using improved HuggingFace loading method...")
            if self.ensure_huggingface_loaded():
                # It should be in loaded_frameworks now
                for framework_name, instance in self.loaded_frameworks.items():
                    if framework_name.lower() == "huggingface":
                        logger.info(f"Successfully loaded HuggingFace integration from robust loader")
                        return instance
                        
            # If that didn't work, try the original method
            try:
                from integrations.huggingface_integration import HuggingFaceIntegration
                integration = HuggingFaceIntegration()
                self.loaded_frameworks["huggingface"] = integration
                logger.info(f"Successfully loaded HuggingFace integration from {AI_MODEL_PATHS['HuggingFace']}")
                return integration
            except ImportError as e:
                logger.warning(f"HuggingFace integration not available: {e}")
                # Create the directory if it doesn't exist
                os.makedirs(AI_MODEL_PATHS['HuggingFace'], exist_ok=True)
        elif name_lower == "gpt4all":
            try:
                from integrations.gpt4all_integration import GPT4AllIntegration
                integration = GPT4AllIntegration()
                self.loaded_frameworks["gpt4all"] = integration
                logger.info(f"Successfully loaded GPT4All integration from {AI_MODEL_PATHS['GPT4All']}")
                return integration
            except ImportError as e:
                logger.warning(f"GPT4All integration not available: {e}")
                # Create the directory if it doesn't exist
                os.makedirs(AI_MODEL_PATHS['GPT4All'], exist_ok=True)
        elif name_lower == "autogpt":
            try:
                from integrations.autogpt_integration import AutoGPTIntegration
                integration = AutoGPTIntegration(framework_path=AI_MODEL_PATHS['AutoGPT'])
                self.loaded_frameworks["autogpt"] = integration
                logger.info(f"Successfully loaded AutoGPT integration from {AI_MODEL_PATHS['AutoGPT']}")
                return integration
            except ImportError as e:
                logger.warning(f"AutoGPT integration not available: {e}")
                # Create the directory if it doesn't exist
                os.makedirs(AI_MODEL_PATHS['AutoGPT'], exist_ok=True)
        
        # Framework not found
        logger.warning(f"Framework '{name}' not found")
        return None

# Initialize a global instance of the framework manager
_framework_manager = None

def get_framework_manager():
    """Get the global framework manager instance."""
    global _framework_manager
    if _framework_manager is None:
        _framework_manager = FrameworkManager()
    return _framework_manager

def get_framework_by_name(name):
    """Get a framework integration by name (standalone function).
    
    This function handles case-insensitive lookups and provides detailed debugging output.
    """
    print(f"[DEBUG] Checking framework: {name}")
    # Try exact match first
    framework = get_framework_manager().get_framework_by_name(name)
    if framework:
        return framework
        
    # If not found, try case-insensitive match
    frameworks = get_framework_manager().get_all_frameworks()
    for framework_name, framework_instance in frameworks.items():
        if framework_name.lower() == name.lower():
            print(f"[DEBUG] Found case-insensitive match for '{name}': '{framework_name}'")
            return framework_instance
            
    print(f"[ERROR] Framework not found: {name} (not even with case-insensitive search)")
    return None

# Initialize a global instance to be imported directly
framework_manager = get_framework_manager()

def ensure_huggingface_loaded():
    """Standalone function to ensure HuggingFace is loaded."""
    return framework_manager.ensure_huggingface_loaded()
