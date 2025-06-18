"""
Minerva AI - Base Plugin Classes

This module defines the base classes for the Minerva plugin system.
"""

import os
import sys
import json
import importlib
import importlib.util
import inspect
import logging
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union
from pathlib import Path

logger = logging.getLogger("minerva.plugins")


@dataclass
class PluginMetadata:
    """Metadata for a Minerva plugin."""
    
    id: str
    name: str
    version: str
    description: str
    author: str = ""
    url: str = ""
    license: str = ""
    requirements: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginMetadata":
        """Create metadata from a dictionary."""
        # Filter out unknown fields
        known_fields = set(inspect.signature(cls).parameters.keys())
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)


class Plugin(ABC):
    """Base class for all Minerva plugins."""
    
    def __init__(self):
        """Initialize the plugin."""
        # Set up default metadata based on class attributes
        self.metadata = self._get_default_metadata()
        self._is_initialized = False
    
    def _get_default_metadata(self) -> PluginMetadata:
        """Get default metadata from class attributes."""
        # Get class attributes for metadata
        attrs = {
            "id": getattr(self.__class__, "plugin_id", self.__class__.__name__.lower()),
            "name": getattr(self.__class__, "plugin_name", self.__class__.__name__),
            "version": getattr(self.__class__, "plugin_version", "0.1.0"),
            "description": getattr(self.__class__, "plugin_description", ""),
            "author": getattr(self.__class__, "plugin_author", ""),
            "url": getattr(self.__class__, "plugin_url", ""),
            "license": getattr(self.__class__, "plugin_license", ""),
            "requirements": getattr(self.__class__, "plugin_requirements", []),
            "dependencies": getattr(self.__class__, "plugin_dependencies", []),
            "tags": getattr(self.__class__, "plugin_tags", []),
            "enabled": True
        }
        return PluginMetadata(**attrs)
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the plugin. Must be implemented by subclasses.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass
    
    def shutdown(self) -> bool:
        """
        Shut down the plugin and clean up resources.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        self._is_initialized = False
        return True
    
    @property
    def is_initialized(self) -> bool:
        """Check if the plugin is initialized."""
        return self._is_initialized
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return self.metadata
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update plugin metadata."""
        current_data = self.metadata.to_dict()
        current_data.update(metadata)
        self.metadata = PluginMetadata.from_dict(current_data)


class PluginManager:
    """
    Manager for Minerva plugins.
    
    Handles plugin discovery, loading, and lifecycle management.
    """
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """
        Initialize the plugin manager.
        
        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_classes: Dict[str, Type[Plugin]] = {}
        self.plugin_dirs = plugin_dirs or []
        
        # Add the default plugin directories
        base_dir = Path(__file__).parent.parent.parent
        default_dirs = [
            base_dir / "plugins" / "core",
            base_dir / "plugins" / "custom"
        ]
        for dir_path in default_dirs:
            if dir_path.exists() and str(dir_path) not in self.plugin_dirs:
                self.plugin_dirs.append(str(dir_path))
        
        # Plugin hooks registry
        self.hooks: Dict[str, List[Callable]] = {}
        
        # Set of enabled plugin IDs
        self.enabled_plugins: Set[str] = set()
        
        # Load plugin settings
        self.settings_file = base_dir / "config" / "plugins.json"
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load plugin settings from file."""
        if not self.settings_file.exists():
            # Create default settings
            self.settings_file.parent.mkdir(exist_ok=True)
            with open(self.settings_file, "w") as f:
                json.dump({"enabled": []}, f)
        
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                self.enabled_plugins = set(settings.get("enabled", []))
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading plugin settings: {e}")
            self.enabled_plugins = set()
    
    def _save_settings(self) -> None:
        """Save plugin settings to file."""
        try:
            with open(self.settings_file, "w") as f:
                json.dump({
                    "enabled": list(self.enabled_plugins)
                }, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving plugin settings: {e}")
    
    def discover_plugins(self) -> List[Type[Plugin]]:
        """
        Discover available plugins in the plugin directories.
        
        Returns:
            List of plugin classes
        """
        discovered_plugins = []
        
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue
            
            # Add plugin directory to path if not already there
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
            
            # Look for Python modules in the plugin directory
            for _, name, is_pkg in pkgutil.iter_modules([plugin_dir]):
                if is_pkg and not name.startswith("_"):
                    # This is a package, try to load it as a plugin
                    try:
                        # Import the module
                        module = importlib.import_module(name)
                        
                        # Look for Plugin subclasses
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (inspect.isclass(attr) and 
                                issubclass(attr, Plugin) and 
                                attr is not Plugin):
                                # Found a plugin class
                                plugin_class = attr
                                plugin_id = getattr(
                                    plugin_class, "plugin_id", 
                                    plugin_class.__name__.lower()
                                )
                                
                                self.plugin_classes[plugin_id] = plugin_class
                                discovered_plugins.append(plugin_class)
                                logger.info(f"Discovered plugin: {plugin_id}")
                    except (ImportError, AttributeError) as e:
                        logger.error(f"Error loading plugin {name}: {e}")
        
        return discovered_plugins
    
    def load_plugins(self) -> List[str]:
        """
        Load and initialize discovered plugins.
        
        Returns:
            List of IDs of successfully loaded plugins
        """
        loaded_plugins = []
        
        # Make sure we've discovered plugins
        if not self.plugin_classes:
            self.discover_plugins()
        
        # Determine which plugins to load
        to_load = {}
        for plugin_id, plugin_class in self.plugin_classes.items():
            if plugin_id in self.enabled_plugins or not self.enabled_plugins:
                to_load[plugin_id] = plugin_class
        
        # Load plugins in dependency order
        while to_load:
            loaded_this_round = False
            
            for plugin_id, plugin_class in list(to_load.items()):
                # Check if dependencies are satisfied
                dependencies = getattr(plugin_class, "plugin_dependencies", [])
                if all(dep in self.plugins for dep in dependencies):
                    try:
                        # Instantiate and initialize plugin
                        plugin_instance = plugin_class()
                        if plugin_instance.initialize():
                            self.plugins[plugin_id] = plugin_instance
                            loaded_plugins.append(plugin_id)
                            loaded_this_round = True
                            logger.info(f"Loaded plugin: {plugin_id}")
                        else:
                            logger.error(f"Failed to initialize plugin: {plugin_id}")
                    except Exception as e:
                        logger.error(f"Error loading plugin {plugin_id}: {e}")
                    
                    # Remove from to_load dict
                    del to_load[plugin_id]
            
            # If we couldn't load any plugins this round, we're stuck in a dependency cycle
            if not loaded_this_round and to_load:
                unloaded = list(to_load.keys())
                logger.error(f"Dependency cycle detected in plugins: {unloaded}")
                break
        
        return loaded_plugins
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a specific plugin.
        
        Args:
            plugin_id: ID of the plugin to unload
            
        Returns:
            True if the plugin was unloaded, False otherwise
        """
        if plugin_id in self.plugins:
            try:
                plugin = self.plugins[plugin_id]
                if plugin.shutdown():
                    del self.plugins[plugin_id]
                    logger.info(f"Unloaded plugin: {plugin_id}")
                    return True
                else:
                    logger.error(f"Failed to shut down plugin: {plugin_id}")
            except Exception as e:
                logger.error(f"Error unloading plugin {plugin_id}: {e}")
        return False
    
    def unload_all_plugins(self) -> None:
        """Unload all plugins."""
        for plugin_id in list(self.plugins.keys()):
            self.unload_plugin(plugin_id)
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """
        Get a plugin by ID.
        
        Args:
            plugin_id: ID of the plugin to get
            
        Returns:
            The plugin instance or None if not found
        """
        return self.plugins.get(plugin_id)
    
    def get_plugins(self) -> List[Plugin]:
        """
        Get all loaded plugins.
        
        Returns:
            List of plugin instances
        """
        return list(self.plugins.values())
    
    def get_plugin_metadata(self) -> List[Dict[str, Any]]:
        """
        Get metadata for all loaded plugins.
        
        Returns:
            List of plugin metadata dictionaries
        """
        return [plugin.get_metadata().to_dict() for plugin in self.plugins.values()]
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin by ID.
        
        Args:
            plugin_id: ID of the plugin to enable
            
        Returns:
            True if the plugin was enabled, False otherwise
        """
        if plugin_id in self.plugin_classes and plugin_id not in self.plugins:
            self.enabled_plugins.add(plugin_id)
            self._save_settings()
            
            # Instantiate and initialize plugin
            plugin_class = self.plugin_classes[plugin_id]
            try:
                plugin_instance = plugin_class()
                if plugin_instance.initialize():
                    self.plugins[plugin_id] = plugin_instance
                    logger.info(f"Enabled plugin: {plugin_id}")
                    return True
                else:
                    logger.error(f"Failed to initialize plugin: {plugin_id}")
            except Exception as e:
                logger.error(f"Error enabling plugin {plugin_id}: {e}")
            
            return False
        elif plugin_id in self.plugins:
            # Already enabled
            return True
        else:
            logger.error(f"Plugin not found: {plugin_id}")
            return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin by ID.
        
        Args:
            plugin_id: ID of the plugin to disable
            
        Returns:
            True if the plugin was disabled, False otherwise
        """
        if plugin_id in self.plugins:
            if self.unload_plugin(plugin_id):
                self.enabled_plugins.discard(plugin_id)
                self._save_settings()
                logger.info(f"Disabled plugin: {plugin_id}")
                return True
        return False
    
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """
        Register a callback for a hook.
        
        Args:
            hook_name: Name of the hook
            callback: Callback function to register
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
    
    def unregister_hook(self, hook_name: str, callback: Callable) -> bool:
        """
        Unregister a callback for a hook.
        
        Args:
            hook_name: Name of the hook
            callback: Callback function to unregister
            
        Returns:
            True if the callback was unregistered, False otherwise
        """
        if hook_name in self.hooks and callback in self.hooks[hook_name]:
            self.hooks[hook_name].remove(callback)
            return True
        return False
    
    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Call all callbacks registered for a hook.
        
        Args:
            hook_name: Name of the hook
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
            
        Returns:
            List of results from all callbacks
        """
        results = []
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in hook {hook_name}: {e}")
        return results
