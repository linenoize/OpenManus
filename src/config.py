import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration manager for OpenManus."""
    
    def __init__(self, config_data: Dict[str, Any] = None):
        """Initialize with optional config data."""
        self.config_data = config_data or {}
        
    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> 'Config':
        """Load configuration from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            return Config(config_data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Failed to load config from {file_path}: {e}")
            return Config({})
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value, with environment variable override."""
        # First check for environment variable
        env_key = f"OPENMANUS_{key.upper()}"
        if env_key in os.environ:
            value = os.environ[env_key]
            # Try to convert to appropriate type
            if value.lower() in ('true', 'yes', '1'):
                return True
            if value.lower() in ('false', 'no', '0'):
                return False
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                return value
        
        # Then check config file data
        keys = key.split('.')
        data = self.config_data
        for k in keys:
            if not isinstance(data, dict) or k not in data:
                return default
            data = data[k]
        return data
    
    def get_tool_config(self, tool_name: str, key: str, default: Any = None) -> Any:
        """Get a tool-specific configuration value."""
        return self.get(f"tools.{tool_name}.{key}", default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        keys = key.split('.')
        data = self.config_data
        for i, k in enumerate(keys[:-1]):
            if k not in data:
                data[k] = {}
            elif not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value
    
    def set_tool_config(self, tool_name: str, key: str, value: Any) -> None:
        """Set a tool-specific configuration value."""
        self.set(f"tools.{tool_name}.{key}", value)
    
    def save(self, file_path: Union[str, Path]) -> bool:
        """Save configuration to a JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.config_data, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving config to {file_path}: {e}")
            return False
    
    def get_file_manager_config(self) -> Dict[str, Any]:
        """Generate file manager configuration from environment variables or config file."""
        # Start with default configuration
        config = {
            "backends": {
                "local": {
                    "enabled": True,
                    "base_path": self.get("FILE_STORAGE_PATH", "data/files/local"),
                    "requires_auth": False
                },
                "git": {
                    "enabled": True,
                    "base_path": self.get("GIT_STORAGE_PATH", "data/files/git"),
                    "requires_auth": False,
                    "user_name": self.get("GIT_USER_NAME", "OpenManus"),
                    "user_email": self.get("GIT_USER_EMAIL", "openmanus@example.com")
                },
                "google_drive": {
                    "enabled": "GOOGLE_DRIVE_CLIENT_ID" in os.environ,
                    "requires_auth": True,
                    "credentials_path": self.get("GDRIVE_CREDENTIALS_PATH", "credentials/gdrive_credentials.json"),
                    "root_folder": self.get("GDRIVE_ROOT_FOLDER", "OpenManus")
                }
            },
            "storage_preferences": {
                "temp": self.get("STORAGE_TEMP", "local"),
                "code": self.get("STORAGE_CODE", "git"),
                "knowledge": self.get("STORAGE_KNOWLEDGE", "git"),
                "document": self.get("STORAGE_DOCUMENT", "local"),
                "image": self.get("STORAGE_IMAGE", "local"),
                "video": self.get("STORAGE_VIDEO", "local"),
                "audio": self.get("STORAGE_AUDIO", "local"),
                "general": self.get("STORAGE_GENERAL", "local")
            }
        }
        
        # Try to load JSON file configuration if it exists
        file_config_path = self.get("FILE_MANAGER_CONFIG_PATH", "file_manager_config.json")
        if os.path.exists(file_config_path):
            try:
                with open(file_config_path, 'r') as f:
                    file_config = json.load(f)
                
                # Merge configurations, with environment variables taking precedence
                for backend, backend_config in file_config.get("backends", {}).items():
                    if backend in config["backends"]:
                        # Update only if not overridden by environment variables
                        for key, value in backend_config.items():
                            env_key = f"OPENMANUS_{backend.upper()}_{key.upper()}"
                            if env_key not in os.environ:
                                config["backends"][backend][key] = value
                
                # Update storage preferences if not set in environment
                for file_type, storage_type in file_config.get("storage_preferences", {}).items():
                    env_key = f"OPENMANUS_STORAGE_{file_type.upper()}"
                    if env_key not in os.environ:
                        config["storage_preferences"][file_type] = storage_type
            except Exception as e:
                logging.error(f"Error loading file manager config from {file_config_path}: {e}")
        
        return config

def load_config() -> Config:
    """Load configuration from file, with possible environment variable override."""
    config_path = os.environ.get('OPENMANUS_CONFIG_PATH', 'config.json')
    
    if os.path.exists(config_path):
        return Config.load_from_file(config_path)
    else:
        logging.warning(f"Config file {config_path} not found, using default configuration.")
        return Config({})

def save_config(config: Config, file_path: Optional[str] = None) -> bool:
    """Save configuration to a file."""
    if file_path is None:
        file_path = os.environ.get('OPENMANUS_CONFIG_PATH', 'config.json')
    return config.save(file_path)