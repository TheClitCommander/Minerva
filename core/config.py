#!/usr/bin/env python3
"""
Minerva Core Configuration

Central configuration management for environment variables,
default settings, and application constants.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Optional dotenv import
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    def load_dotenv(*args, **kwargs):
        """Fallback function when dotenv is not available."""
        pass


class MinervaConfig:
    """Configuration manager for Minerva application."""
    
    def __init__(self):
        """Initialize configuration from environment variables and defaults."""
        self.project_root = Path(__file__).parent.parent.absolute()
        self._load_environment()
        self._setup_logging()
        
    def _load_environment(self):
        """Load environment variables from .env file if it exists."""
        env_file = self.project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            logging.info(f"Loaded environment from {env_file}")
        else:
            logging.info("No .env file found, using system environment variables")
    
    def _setup_logging(self):
        """Set up basic logging configuration."""
        log_level = self.get('LOG_LEVEL', 'INFO').upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value from environment or default."""
        return os.getenv(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value."""
        value = self.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value."""
        try:
            return int(self.get(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a float configuration value."""
        try:
            return float(self.get(key, default))
        except (ValueError, TypeError):
            return default
    
    @property
    def api_keys(self) -> Dict[str, str]:
        """Get all API keys from environment."""
        return {
            'openai': self.get('OPENAI_API_KEY', ''),
            'anthropic': self.get('ANTHROPIC_API_KEY', ''),
            'mistral': self.get('MISTRAL_API_KEY', ''),
            'huggingface': self.get('HUGGINGFACE_API_KEY', ''),
            'cohere': self.get('COHERE_API_KEY', ''),
            'gemini': self.get('GEMINI_API_KEY', '')
        }
    
    @property
    def server_config(self) -> Dict[str, Any]:
        """Get server configuration."""
        return {
            'host': self.get('MINERVA_HOST', '0.0.0.0'),
            'port': self.get_int('MINERVA_PORT', 5000),
            'debug': self.get_bool('MINERVA_DEBUG', False),
            'cors_enabled': self.get_bool('MINERVA_CORS', True)
        }
    
    @property
    def database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            'url': self.get('DATABASE_URL', f'sqlite:///{self.project_root}/data/minerva.db'),
            'echo': self.get_bool('DATABASE_ECHO', False),
            'pool_size': self.get_int('DATABASE_POOL_SIZE', 5)
        }
    
    @property
    def memory_config(self) -> Dict[str, Any]:
        """Get memory system configuration."""
        return {
            'vector_store_type': self.get('MEMORY_VECTOR_STORE', 'chroma'),
            'max_memory_items': self.get_int('MEMORY_MAX_ITEMS', 10000),
            'embedding_model': self.get('MEMORY_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
            'store_path': self.get('MEMORY_STORE_PATH', str(self.project_root / 'data' / 'memory_store'))
        }
    
    @property
    def ai_config(self) -> Dict[str, Any]:
        """Get AI model configuration."""
        return {
            'default_model': self.get('AI_DEFAULT_MODEL', 'gpt-4o'),
            'max_tokens': self.get_int('AI_MAX_TOKENS', 4000),
            'temperature': self.get_float('AI_TEMPERATURE', 0.7),
            'timeout': self.get_int('AI_TIMEOUT', 30),
            'retry_attempts': self.get_int('AI_RETRY_ATTEMPTS', 3)
        }
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            'level': self.get('LOG_LEVEL', 'INFO'),
            'file_path': self.get('LOG_FILE', str(self.project_root / 'minerva_logs' / 'minerva.log')),
            'max_size': self.get('LOG_MAX_SIZE', '10 MB'),
            'retention': self.get('LOG_RETENTION', '7 days'),
            'format': self.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        }
    
    @property
    def framework_config(self) -> Dict[str, Any]:
        """Get framework integration configuration."""
        return {
            'registry_path': self.get('FRAMEWORK_REGISTRY', str(self.project_root / 'frameworks' / 'registry.json')),
            'auto_discovery': self.get_bool('FRAMEWORK_AUTO_DISCOVERY', True),
            'discovery_paths': self.get('FRAMEWORK_DISCOVERY_PATHS', '').split(':') if self.get('FRAMEWORK_DISCOVERY_PATHS') else []
        }
    
    @property
    def security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            'secret_key': self.get('SECRET_KEY', 'dev-key-change-in-production'),
            'session_timeout': self.get_int('SESSION_TIMEOUT', 3600),
            'rate_limit': self.get('RATE_LIMIT', '100/hour'),
            'cors_origins': self.get('CORS_ORIGINS', '*').split(',')
        }
    
    def get_data_directory(self, subdir: str = '') -> Path:
        """Get path to data directory or subdirectory."""
        data_dir = self.project_root / 'data'
        if subdir:
            data_dir = data_dir / subdir
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def get_log_directory(self) -> Path:
        """Get path to log directory."""
        log_dir = self.project_root / 'minerva_logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status."""
        issues = []
        warnings = []
        
        # Check API keys
        api_keys = self.api_keys
        valid_keys = [k for k, v in api_keys.items() if v and len(v) > 8]
        
        if not valid_keys:
            warnings.append("No valid API keys found - will run in simulation mode")
        else:
            logging.info(f"Found valid API keys for: {', '.join(valid_keys)}")
        
        # Check required directories
        required_dirs = [
            self.get_data_directory(),
            self.get_log_directory(),
            self.project_root / 'static',
            self.project_root / 'templates'
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create directory {dir_path}: {e}")
        
        # Check server config
        server = self.server_config
        if not (1 <= server['port'] <= 65535):
            issues.append(f"Invalid port number: {server['port']}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'api_keys_available': valid_keys,
            'project_root': str(self.project_root)
        }


# Create global configuration instance
config = MinervaConfig()

# Export commonly used configurations
API_KEYS = config.api_keys
SERVER_CONFIG = config.server_config
AI_CONFIG = config.ai_config
MEMORY_CONFIG = config.memory_config

# Module exports
__all__ = [
    'MinervaConfig', 'config', 
    'API_KEYS', 'SERVER_CONFIG', 'AI_CONFIG', 'MEMORY_CONFIG'
] 