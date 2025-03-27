"""
Tool for managing files across different storage backends.
Provides a unified interface for file operations with multiple storage options.
"""
import os
import io
import re
import json
import shutil
import hashlib
import zipfile
import tarfile
import gzip
import mimetypes
import logging
from datetime import datetime
from typing import Dict, List, BinaryIO, Optional, Union, Tuple, Any, Set, Iterator

# Import config system
from src.config import load_config, Config

# Import storage backends
from src.tools.storage_backends import (
    StorageBackend,
    LocalStorageBackend,
    GitStorageBackend,
    GoogleDriveStorageBackend,
    OneDriveStorageBackend,
    FileManagerError,
    StorageBackendError,
    FileOperationError
)

# Set up logging
logger = logging.getLogger(__name__)

class FileManagerTool:
    """
    Tool for managing files across different storage backends.
    Provides a unified interface for file operations with multiple storage options.
    """
    
    def __init__(self, config_path: str = None, config_obj: Config = None):
        """
        Initialize the file manager tool with different storage backends.
        
        Args:
            config_path: Path to the configuration file. If None, uses environment variables or default settings.
            config_obj: Config object. If provided, this takes precedence over config_path.
        """
        # First try to get the configuration from the provided Config object
        if config_obj:
            self.config = config_obj.get_file_manager_config()
        else:
            # Get the system-wide config object
            system_config = load_config()
            
            # If config_path is provided, use it (with env var override)
            if config_path and os.path.exists(config_path):
                # Store the path for potential reference
                os.environ["OPENMANUS_FILE_MANAGER_CONFIG_PATH"] = config_path
            
            # Get file manager configuration from env vars and/or config file
            self.config = system_config.get_file_manager_config()
        
        # Initialize storage backends based on configuration
        self.storage_backends = {}
        self.base_paths = {}
        self._initialize_storage_backends()
        
        # Set storage preferences from config
        self.storage_preferences = self.config["storage_preferences"]
        
        # Initialize MIME type detection
        mimetypes.init()
        
        # File tagging system
        self.tags_file_path = os.path.join(
            self.config["backends"]["local"]["base_path"], 
            ".file_tags.json"
        )
        
        # Load existing tags if available
        self.file_tags = {}
        if os.path.exists(self.tags_file_path):
            try:
                with open(self.tags_file_path, 'r') as f:
                    self.file_tags = json.load(f)
            except json.JSONDecodeError:
                # Initialize with empty dict if the file is corrupted
                self.file_tags = {}
    
    def _merge_config(self, loaded_config: Dict[str, Any]) -> None:
        """
        Merge loaded configuration with default configuration.
        
        Args:
            loaded_config: Configuration loaded from file
        """
        # Merge backends configuration
        if "backends" in loaded_config:
            for backend_name, backend_config in loaded_config["backends"].items():
                if backend_name in self.config["backends"]:
                    self.config["backends"][backend_name].update(backend_config)
                else:
                    self.config["backends"][backend_name] = backend_config
        
        # Merge storage preferences
        if "storage_preferences" in loaded_config:
            self.config["storage_preferences"].update(loaded_config["storage_preferences"])
    
    def _initialize_storage_backends(self) -> None:
        """Initialize storage backends based on configuration."""
        # Initialize each backend that is enabled
        for backend_name, backend_config in self.config["backends"].items():
            if not backend_config.get("enabled", False):
                self.storage_backends[backend_name] = None
                continue
            
            try:
                if backend_name == "local":
                    base_path = backend_config["base_path"]
                    self.base_paths["local"] = base_path
                    self.storage_backends["local"] = LocalStorageBackend(base_path)
                
                elif backend_name == "git":
                    base_path = backend_config["base_path"]
                    self.base_paths["git"] = base_path
                    self.storage_backends["git"] = GitStorageBackend(
                        repo_path=base_path,
                        user_name=backend_config.get("user_name", "OpenManus"),
                        user_email=backend_config.get("user_email", "openmanus@example.com")
                    )
                
                elif backend_name == "google_drive":
                    if backend_config["requires_auth"] and not backend_config.get("credentials_path"):
                        logger.warning("Google Drive backend requires credentials_path to be set")
                        self.storage_backends["google_drive"] = None
                    else:
                        self.storage_backends["google_drive"] = GoogleDriveStorageBackend(
                            credentials_path=backend_config.get("credentials_path"),
                            root_folder=backend_config.get("root_folder", "OpenManus")
                        )
                        self.base_paths["google_drive"] = backend_config.get("root_folder", "OpenManus")
                
                elif backend_name == "onedrive":
                    if backend_config["requires_auth"] and not backend_config.get("credentials_path"):
                        logger.warning("OneDrive backend requires credentials_path to be set")
                        self.storage_backends["onedrive"] = None
                    else:
                        self.storage_backends["onedrive"] = OneDriveStorageBackend(
                            credentials_path=backend_config.get("credentials_path"),
                            root_folder=backend_config.get("root_folder", "OpenManus")
                        )
                        self.base_paths["onedrive"] = backend_config.get("root_folder", "OpenManus")
                
                else:
                    logger.warning(f"Unknown backend type: {backend_name}")
                    self.storage_backends[backend_name] = None
            
            except Exception as e:
                logger.error(f"Error initializing {backend_name} backend: {e}", exc_info=True)
                self.storage_backends[backend_name] = None
    
    def initialize_backend(self, backend_type: str, **kwargs) -> bool:
        """
        Initialize or update a specific storage backend.
        
        Args:
            backend_type: The backend to initialize ('local', 'git', 'google_drive', 'onedrive')
            **kwargs: Backend-specific initialization parameters
                For local: base_path
                For git: base_path, user_name, user_email
                For google_drive: credentials_path, root_folder
                For onedrive: credentials_path, root_folder
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure the backend exists in the config
            if backend_type not in self.config["backends"]:
                self.config["backends"][backend_type] = {
                    "enabled": True,
                    "requires_auth": backend_type in ["google_drive", "onedrive"]
                }
            
            # Enable the backend
            self.config["backends"][backend_type]["enabled"] = True
            
            # Update the backend config with any provided parameters
            for key, value in kwargs.items():
                self.config["backends"][backend_type][key] = value
            
            # Initialize the backend based on the updated config
            if backend_type == "local":
                base_path = self.config["backends"]["local"].get("base_path", "data/files/local")
                self.base_paths["local"] = base_path
                self.storage_backends["local"] = LocalStorageBackend(base_path)
                return True
                
            elif backend_type == "git":
                base_path = self.config["backends"]["git"].get("base_path", "data/files/git")
                user_name = self.config["backends"]["git"].get("user_name", "OpenManus")
                user_email = self.config["backends"]["git"].get("user_email", "openmanus@example.com")
                
                self.base_paths["git"] = base_path
                self.storage_backends["git"] = GitStorageBackend(
                    repo_path=base_path,
                    user_name=user_name,
                    user_email=user_email
                )
                return True
                
            elif backend_type == "google_drive":
                credentials_path = self.config["backends"]["google_drive"].get("credentials_path")
                root_folder = self.config["backends"]["google_drive"].get("root_folder", "OpenManus")
                
                if not credentials_path:
                    logger.warning("Google Drive backend requires credentials_path")
                    return False
                    
                self.storage_backends["google_drive"] = GoogleDriveStorageBackend(
                    credentials_path=credentials_path,
                    root_folder=root_folder
                )
                self.base_paths["google_drive"] = root_folder
                return self.storage_backends["google_drive"].authenticated
                
            elif backend_type == "onedrive":
                credentials_path = self.config["backends"]["onedrive"].get("credentials_path")
                root_folder = self.config["backends"]["onedrive"].get("root_folder", "OpenManus")
                
                if not credentials_path:
                    logger.warning("OneDrive backend requires credentials_path")
                    return False
                    
                self.storage_backends["onedrive"] = OneDriveStorageBackend(
                    credentials_path=credentials_path,
                    root_folder=root_folder
                )
                self.base_paths["onedrive"] = root_folder
                return self.storage_backends["onedrive"].authenticated
                
            else:
                logger.warning(f"Unknown backend type: {backend_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing backend {backend_type}: {e}", exc_info=True)
            return False
    
    def set_storage_preference(self, file_type: str, storage_type: str) -> bool:
        """
        Set the preferred storage type for a specific file type.
        
        Args:
            file_type: Type of file (temp, code, knowledge, image, video, etc.)
            storage_type: Preferred storage backend (local, git, google_drive, onedrive)
            
        Returns:
            True if successful, False otherwise
        """
        if storage_type not in self.storage_backends:
            return False
            
        # Check if the backend is initialized
        if self.storage_backends[storage_type] is None:
            return False
            
        self.storage_preferences[file_type] = storage_type
        return True
    
    def get_storage_preferences(self) -> Dict[str, str]:
        """
        Get the current storage preferences.
        
        Returns:
            Dictionary mapping file types to preferred storage backends
        """
        return self.storage_preferences
    
    def read_file(self, path: str, storage_type: Optional[str] = None, file_type: Optional[str] = None) -> Optional[bytes]:
        """
        Read a file from the specified storage.
        
        Args:
            path: Path to the file
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            
        Returns:
            File contents as bytes, or None if read failed
        """
        # Determine which storage to use
        storage = self._get_storage(storage_type, file_type)
        if storage is None:
            return None
            
        try:
            return storage.read_file(path)
        except Exception as e:
            logger.error(f"Error reading file: {e}", exc_info=True)
            return None
    
    def write_file(self, 
                  path: str, 
                  content: Union[str, bytes], 
                  storage_type: Optional[str] = None, 
                  file_type: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Write a file to the specified storage.
        
        Args:
            path: Path to write the file to
            content: Content to write (string or bytes)
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            metadata: Optional metadata for the storage backend
            
        Returns:
            True if successful, False otherwise
        """
        # Determine which storage to use
        storage = self._get_storage(storage_type, file_type)
        if storage is None:
            return False
            
        # Convert string to bytes if needed
        if isinstance(content, str):
            content = content.encode('utf-8')
            
        try:
            # Handle special parameters for git backend
            if isinstance(storage, GitStorageBackend) and metadata and "commit_message" in metadata:
                return storage.write_file(path, content, metadata["commit_message"])
            else:
                return storage.write_file(path, content)
        except Exception as e:
            logger.error(f"Error writing file: {e}", exc_info=True)
            return False
    
    def delete_file(self, 
                   path: str, 
                   storage_type: Optional[str] = None, 
                   file_type: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Delete a file from the specified storage.
        
        Args:
            path: Path to the file to delete
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            metadata: Optional metadata for the storage backend
            
        Returns:
            True if successful, False otherwise
        """
        # Determine which storage to use
        storage = self._get_storage(storage_type, file_type)
        if storage is None:
            return False
            
        try:
            # Handle special parameters for git backend
            if isinstance(storage, GitStorageBackend) and metadata and "commit_message" in metadata:
                return storage.delete_file(path, metadata["commit_message"])
            else:
                return storage.delete_file(path)
        except Exception as e:
            logger.error(f"Error deleting file: {e}", exc_info=True)
            return False
    
    def list_files(self, 
                  path: str = "", 
                  storage_type: Optional[str] = None,
                  file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in a directory from the specified storage.
        
        Args:
            path: Path to the directory
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            
        Returns:
            List of file information dictionaries
        """
        # Determine which storage to use
        storage = self._get_storage(storage_type, file_type)
        if storage is None:
            return []
            
        try:
            return storage.list_files(path)
        except Exception as e:
            logger.error(f"Error listing files: {e}", exc_info=True)
            return []
    
    def file_exists(self, 
                   path: str, 
                   storage_type: Optional[str] = None,
                   file_type: Optional[str] = None) -> bool:
        """
        Check if a file exists in the specified storage.
        
        Args:
            path: Path to the file
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            
        Returns:
            True if the file exists, False otherwise
        """
        # Determine which storage to use
        storage = self._get_storage(storage_type, file_type)
        if storage is None:
            return False
            
        try:
            return storage.file_exists(path)
        except Exception as e:
            logger.error(f"Error checking if file exists: {e}", exc_info=True)
            return False
    
    def create_directory(self, 
                        path: str, 
                        storage_type: Optional[str] = None,
                        file_type: Optional[str] = None) -> bool:
        """
        Create a directory in the specified storage.
        
        Args:
            path: Path to the directory to create
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            
        Returns:
            True if successful, False otherwise
        """
        # Determine which storage to use
        storage = self._get_storage(storage_type, file_type)
        if storage is None:
            return False
            
        try:
            return storage.create_directory(path)
        except Exception as e:
            logger.error(f"Error creating directory: {e}", exc_info=True)
            return False
    
    def rename_file(self, 
                   old_path: str, 
                   new_path: str, 
                   storage_type: Optional[str] = None,
                   file_type: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Rename or move a file in the specified storage.
        
        Args:
            old_path: Current path to the file
            new_path: New path for the file
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            metadata: Optional metadata for the storage backend
            
        Returns:
            True if successful, False otherwise
        """
        # Determine which storage to use
        storage = self._get_storage(storage_type, file_type)
        if storage is None:
            return False
            
        try:
            # Handle special parameters for git backend
            if isinstance(storage, GitStorageBackend) and metadata and "commit_message" in metadata:
                return storage.rename_file(old_path, new_path, metadata["commit_message"])
            else:
                return storage.rename_file(old_path, new_path)
        except Exception as e:
            logger.error(f"Error renaming file: {e}", exc_info=True)
            return False
    
    def read_text(self, 
                 path: str, 
                 storage_type: Optional[str] = None,
                 file_type: Optional[str] = None,
                 encoding: str = 'utf-8') -> Optional[str]:
        """
        Read a text file from the specified storage.
        
        Args:
            path: Path to the file
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            encoding: Text encoding to use
            
        Returns:
            File contents as string, or None if read failed
        """
        content = self.read_file(path, storage_type, file_type)
        if content is None:
            return None
            
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            logger.error(f"Error decoding file as {encoding}")
            return None
    
    def write_text(self, 
                  path: str, 
                  content: str, 
                  storage_type: Optional[str] = None,
                  file_type: Optional[str] = None,
                  encoding: str = 'utf-8',
                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Write a text file to the specified storage.
        
        Args:
            path: Path to write the file to
            content: Text content to write
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            encoding: Text encoding to use
            metadata: Optional metadata for the storage backend
            
        Returns:
            True if successful, False otherwise
        """
        try:
            binary_content = content.encode(encoding)
            return self.write_file(path, binary_content, storage_type, file_type, metadata)
        except Exception as e:
            logger.error(f"Error writing text file: {e}", exc_info=True)
            return False
    
    def get_file_history(self, 
                        path: str, 
                        max_entries: int = 10) -> List[Dict[str, Any]]:
        """
        Get file history if supported by the storage backend.
        Currently only implemented for Git backend.
        
        Args:
            path: Path to the file
            max_entries: Maximum number of history entries to return
            
        Returns:
            List of file history entries, or empty list if not supported
        """
        # This is a Git-specific feature
        storage = self.storage_backends.get("git")
        if storage is None:
            return []
            
        try:
            return storage.get_file_history(path, max_entries)
        except Exception as e:
            logger.error(f"Error getting file history: {e}", exc_info=True)
            return []
            
    def search_files(self, 
                    pattern: str, 
                    storage_type: Optional[str] = None,
                    file_type: Optional[str] = None,
                    path: str = "",
                    recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Search for files matching a pattern.
        
        Args:
            pattern: Regular expression pattern to match against file names
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            path: Base directory to search in
            recursive: Whether to search recursively through subdirectories
            
        Returns:
            List of matching file information dictionaries
        """
        # Determine which storage to use
        storage = self._get_storage(storage_type, file_type)
        if storage is None:
            return []
            
        try:
            return storage.search_files(path, pattern, recursive)
        except Exception as e:
            logger.error(f"Error searching files: {e}", exc_info=True)
            return []
            
    def get_file_info(self,
                     path: str,
                     storage_type: Optional[str] = None,
                     file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            path: Path to the file
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            
        Returns:
            Dictionary with detailed file information
        """
        # Determine which storage to use
        storage = self._get_storage(storage_type, file_type)
        if storage is None:
            return {"error": "No storage available"}
            
        try:
            file_info = storage.get_file_info(path)
            
            # Add tags if available
            storage_name = storage_type if storage_type else (
                self.storage_preferences.get(file_type) if file_type else "local"
            )
            file_key = f"{storage_name}:{path}"
            if file_key in self.file_tags:
                file_info["tags"] = self.file_tags[file_key]
                
            return file_info
        except Exception as e:
            logger.error(f"Error getting file info: {e}", exc_info=True)
            return {"error": str(e)}
            
    def get_file_hash(self,
                     path: str,
                     hash_type: str = "sha256",
                     storage_type: Optional[str] = None,
                     file_type: Optional[str] = None) -> Optional[str]:
        """
        Calculate a hash of the file contents.
        
        Args:
            path: Path to the file
            hash_type: Type of hash to calculate (md5, sha1, sha256, etc.)
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            
        Returns:
            Hex digest of the hash, or None if the file doesn't exist
        """
        # Determine which storage to use
        storage = self._get_storage(storage_type, file_type)
        if storage is None:
            return None
            
        try:
            return storage.get_file_hash(path, hash_type)
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}", exc_info=True)
            return None
            
    # File tagging system
    def add_tags(self,
                path: str,
                tags: List[str],
                storage_type: Optional[str] = None,
                file_type: Optional[str] = None) -> bool:
        """
        Add tags to a file.
        
        Args:
            path: Path to the file
            tags: List of tags to add
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            
        Returns:
            True if successful, False otherwise
        """
        # Check if the file exists
        if not self.file_exists(path, storage_type, file_type):
            return False
            
        # Determine the storage type
        storage_name = storage_type if storage_type else (
            self.storage_preferences.get(file_type) if file_type else "local"
        )
        
        # Create a unique key for the file
        file_key = f"{storage_name}:{path}"
        
        # Add or update tags
        if file_key not in self.file_tags:
            self.file_tags[file_key] = []
            
        # Add new tags without duplicates
        self.file_tags[file_key] = list(set(self.file_tags[file_key] + tags))
        
        # Save the tags file
        return self._save_tags()
    
    def remove_tags(self,
                   path: str,
                   tags: List[str],
                   storage_type: Optional[str] = None,
                   file_type: Optional[str] = None) -> bool:
        """
        Remove tags from a file.
        
        Args:
            path: Path to the file
            tags: List of tags to remove
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            
        Returns:
            True if successful, False otherwise
        """
        # Determine the storage type
        storage_name = storage_type if storage_type else (
            self.storage_preferences.get(file_type) if file_type else "local"
        )
        
        # Create a unique key for the file
        file_key = f"{storage_name}:{path}"
        
        # Remove tags if they exist
        if file_key in self.file_tags:
            self.file_tags[file_key] = [tag for tag in self.file_tags[file_key] if tag not in tags]
            
            # Save the tags file
            return self._save_tags()
            
        return True  # Nothing to remove
    
    def get_tags(self,
                path: str,
                storage_type: Optional[str] = None,
                file_type: Optional[str] = None) -> List[str]:
        """
        Get tags for a file.
        
        Args:
            path: Path to the file
            storage_type: Specific storage to use (overrides file_type preference)
            file_type: Type of file (used to determine storage if storage_type not specified)
            
        Returns:
            List of tags
        """
        # Determine the storage type
        storage_name = storage_type if storage_type else (
            self.storage_preferences.get(file_type) if file_type else "local"
        )
        
        # Create a unique key for the file
        file_key = f"{storage_name}:{path}"
        
        # Return tags or empty list
        return self.file_tags.get(file_key, [])
    
    def search_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict[str, Any]]:
        """
        Search for files with specific tags.
        
        Args:
            tags: List of tags to search for
            match_all: If True, files must have all specified tags; if False, files can have any of the specified tags
            
        Returns:
            List of file information dictionaries
        """
        results = []
        
        for file_key, file_tags in self.file_tags.items():
            match = False
            
            if match_all:
                # All specified tags must be present
                match = all(tag in file_tags for tag in tags)
            else:
                # Any of the specified tags can be present
                match = any(tag in file_tags for tag in tags)
                
            if match:
                # Parse the file key to get storage and path
                storage_name, path = file_key.split(":", 1)
                
                # Get the storage backend
                storage = self.storage_backends.get(storage_name)
                if storage and storage.file_exists(path):
                    try:
                        # Get file info
                        file_info = storage.get_file_info(path)
                        file_info["tags"] = file_tags
                        file_info["storage"] = storage_name
                        results.append(file_info)
                    except:
                        # Skip files that can't be accessed
                        pass
                        
        return results
    
    def _save_tags(self) -> bool:
        """Save file tags to the tags file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.tags_file_path), exist_ok=True)
            
            # Write tags to file
            with open(self.tags_file_path, 'w') as f:
                json.dump(self.file_tags, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving tags: {e}", exc_info=True)
            return False
            
    # File compression and archiving
    def compress_file(self,
                     source_path: str,
                     target_path: Optional[str] = None,
                     compression_type: str = "zip",
                     source_storage_type: Optional[str] = None,
                     source_file_type: Optional[str] = None,
                     target_storage_type: Optional[str] = None,
                     target_file_type: Optional[str] = None) -> Optional[str]:
        """
        Compress a file or directory using the specified compression method.
        
        Args:
            source_path: Path to the file or directory to compress
            target_path: Output path for the compressed file (if None, derived from source path)
            compression_type: Type of compression to use ('zip', 'tar', 'gzip', 'tar.gz')
            source_storage_type: Storage type for the source file
            source_file_type: File type for the source file
            target_storage_type: Storage type for the target file
            target_file_type: File type for the target file
            
        Returns:
            Path to the compressed file if successful, None otherwise
        """
        # Determine source storage
        source_storage = self._get_storage(source_storage_type, source_file_type)
        if source_storage is None:
            return None
            
        # Determine target storage (default to same as source)
        target_storage_type = target_storage_type or source_storage_type
        target_file_type = target_file_type or "temp"  # Default compressed files to temp
        target_storage = self._get_storage(target_storage_type, target_file_type)
        if target_storage is None:
            return None
            
        # Check if source exists
        if not source_storage.file_exists(source_path):
            return None
            
        # Determine target path if not specified
        if target_path is None:
            # Add appropriate extension
            if compression_type == "zip":
                target_path = f"{source_path}.zip"
            elif compression_type == "tar":
                target_path = f"{source_path}.tar"
            elif compression_type == "gzip":
                target_path = f"{source_path}.gz"
            elif compression_type == "tar.gz":
                target_path = f"{source_path}.tar.gz"
            else:
                return None  # Unsupported compression type
                
        try:
            # Read the source file or directory
            source_content = source_storage.read_file(source_path)
            
            compressed_content = None
            
            # Compress using the specified method
            if compression_type == "zip":
                # Create a zip file in memory
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.writestr(os.path.basename(source_path), source_content)
                buffer.seek(0)
                compressed_content = buffer.read()
                
            elif compression_type == "tar":
                # Create a tar file in memory
                buffer = io.BytesIO()
                with tarfile.open(fileobj=buffer, mode='w') as tar_file:
                    info = tarfile.TarInfo(name=os.path.basename(source_path))
                    info.size = len(source_content)
                    tar_file.addfile(info, io.BytesIO(source_content))
                buffer.seek(0)
                compressed_content = buffer.read()
                
            elif compression_type == "gzip":
                # Create a gzip file in memory
                buffer = io.BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
                    gz_file.write(source_content)
                buffer.seek(0)
                compressed_content = buffer.read()
                
            elif compression_type == "tar.gz":
                # Create a tar.gz file in memory
                buffer = io.BytesIO()
                with tarfile.open(fileobj=buffer, mode='w:gz') as tar_gz_file:
                    info = tarfile.TarInfo(name=os.path.basename(source_path))
                    info.size = len(source_content)
                    tar_gz_file.addfile(info, io.BytesIO(source_content))
                buffer.seek(0)
                compressed_content = buffer.read()
                
            else:
                # Unsupported compression type
                return None
            
            # Write the compressed content to the target
            if compressed_content:
                target_storage.write_file(target_path, compressed_content)
                return target_path
                
            return None
        except Exception as e:
            logger.error(f"Error compressing file: {e}", exc_info=True)
            return None
    
    def decompress_file(self,
                       source_path: str,
                       target_dir: Optional[str] = None,
                       source_storage_type: Optional[str] = None,
                       source_file_type: Optional[str] = None,
                       target_storage_type: Optional[str] = None,
                       target_file_type: Optional[str] = None) -> List[str]:
        """
        Decompress a file using the specified compression method.
        
        Args:
            source_path: Path to the compressed file
            target_dir: Directory to extract files to (if None, derived from source path)
            source_storage_type: Storage type for the source file
            source_file_type: File type for the source file
            target_storage_type: Storage type for the target directory
            target_file_type: File type for the extracted files
            
        Returns:
            List of extracted file paths if successful, empty list otherwise
        """
        # Determine source storage
        source_storage = self._get_storage(source_storage_type, source_file_type)
        if source_storage is None:
            return []
            
        # Determine target storage (default to same as source)
        target_storage_type = target_storage_type or source_storage_type
        target_file_type = target_file_type or "temp"  # Default extracted files to temp
        target_storage = self._get_storage(target_storage_type, target_file_type)
        if target_storage is None:
            return []
            
        # Check if source exists
        if not source_storage.file_exists(source_path):
            return []
            
        # Determine target directory if not specified
        if target_dir is None:
            # Use source filename without extension as target directory
            base_name = os.path.basename(source_path)
            target_dir = os.path.splitext(base_name)[0]
            
            # Handle double extensions like .tar.gz
            if target_dir.endswith('.tar'):
                target_dir = os.path.splitext(target_dir)[0]
                
        # Create target directory
        target_storage.create_directory(target_dir)
        
        try:
            # Read the compressed file
            source_content = source_storage.read_file(source_path)
            
            extracted_files = []
            
            # Determine compression type from file extension
            ext = os.path.splitext(source_path)[1].lower()
            if ext == '.zip':
                # Extract zip file
                buffer = io.BytesIO(source_content)
                with zipfile.ZipFile(buffer, 'r') as zip_file:
                    for file_info in zip_file.infolist():
                        if file_info.filename.endswith('/'):  # Directory
                            target_storage.create_directory(os.path.join(target_dir, file_info.filename))
                        else:  # File
                            file_content = zip_file.read(file_info.filename)
                            target_path = os.path.join(target_dir, file_info.filename)
                            target_storage.write_file(target_path, file_content)
                            extracted_files.append(target_path)
                            
            elif ext == '.tar':
                # Extract tar file
                buffer = io.BytesIO(source_content)
                with tarfile.open(fileobj=buffer, mode='r') as tar_file:
                    for member in tar_file.getmembers():
                        if member.isdir():  # Directory
                            target_storage.create_directory(os.path.join(target_dir, member.name))
                        else:  # File
                            file_content = tar_file.extractfile(member).read()
                            target_path = os.path.join(target_dir, member.name)
                            target_storage.write_file(target_path, file_content)
                            extracted_files.append(target_path)
                            
            elif ext == '.gz':
                # Extract gzip file
                # Gzip only compresses single files
                buffer = io.BytesIO(source_content)
                with gzip.GzipFile(fileobj=buffer, mode='rb') as gz_file:
                    file_content = gz_file.read()
                    # Remove .gz extension for target path
                    base_name = os.path.basename(source_path)
                    target_filename = os.path.splitext(base_name)[0]
                    target_path = os.path.join(target_dir, target_filename)
                    target_storage.write_file(target_path, file_content)
                    extracted_files.append(target_path)
            
            elif source_path.endswith('.tar.gz'):
                # Extract tar.gz file
                buffer = io.BytesIO(source_content)
                with tarfile.open(fileobj=buffer, mode='r:gz') as tar_gz_file:
                    for member in tar_gz_file.getmembers():
                        if member.isdir():  # Directory
                            target_storage.create_directory(os.path.join(target_dir, member.name))
                        else:  # File
                            file_content = tar_gz_file.extractfile(member).read()
                            target_path = os.path.join(target_dir, member.name)
                            target_storage.write_file(target_path, file_content)
                            extracted_files.append(target_path)
            
            return extracted_files
        except Exception as e:
            logger.error(f"Error decompressing file: {e}", exc_info=True)
            return []
    
    def sync_file(self,
                 source_path: str,
                 target_path: Optional[str] = None,
                 source_storage_type: Optional[str] = None,
                 source_file_type: Optional[str] = None,
                 target_storage_type: Optional[str] = None,
                 target_file_type: Optional[str] = None,
                 sync_tags: bool = True,
                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Synchronize (copy) a file between different storage backends.
        
        Args:
            source_path: Path to the source file
            target_path: Path to write the file to (if None, uses the same as source_path)
            source_storage_type: Storage type for the source file
            source_file_type: File type for the source file
            target_storage_type: Storage type for the target file
            target_file_type: File type for the target file
            sync_tags: Whether to copy tags from source to target
            metadata: Optional metadata for the target backend
            
        Returns:
            True if successful, False otherwise
        """
        if target_path is None:
            target_path = source_path
            
        # Source and target must be different
        if source_storage_type == target_storage_type and source_path == target_path:
            return False
            
        # Determine source storage
        source_storage = self._get_storage(source_storage_type, source_file_type)
        if source_storage is None:
            return False
            
        # Determine target storage
        target_storage = self._get_storage(target_storage_type, target_file_type)
        if target_storage is None:
            return False
            
        # Check if source exists
        if not source_storage.file_exists(source_path):
            return False
            
        try:
            # Read the source file
            source_content = source_storage.read_file(source_path)
            
            # Write to the target
            if isinstance(target_storage, GitStorageBackend) and metadata and "commit_message" in metadata:
                target_storage.write_file(target_path, source_content, metadata["commit_message"])
            else:
                target_storage.write_file(target_path, source_content)
                
            # Sync tags if requested
            if sync_tags:
                source_storage_name = source_storage_type if source_storage_type else (
                    self.storage_preferences.get(source_file_type) if source_file_type else "local"
                )
                target_storage_name = target_storage_type if target_storage_type else (
                    self.storage_preferences.get(target_file_type) if target_file_type else "local"
                )
                
                # Create file keys
                source_key = f"{source_storage_name}:{source_path}"
                target_key = f"{target_storage_name}:{target_path}"
                
                # Copy tags if source has any
                if source_key in self.file_tags:
                    self.file_tags[target_key] = self.file_tags[source_key].copy()
                    self._save_tags()
                    
            return True
        except Exception as e:
            logger.error(f"Error synchronizing file: {e}", exc_info=True)
            return False
    
    def save_config(self, config_path: str) -> bool:
        """
        Save the current configuration to a file.
        
        Args:
            config_path: Path to save the configuration to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directory if needed
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Write the config file
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            return False
    
    def load_config(self, config_path: str) -> bool:
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(config_path):
                logger.warning(f"Configuration file not found: {config_path}")
                return False
                
            # Load the configuration file
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                
            # Merge with default config
            self._merge_config(loaded_config)
            
            # Re-initialize storage backends
            self._initialize_storage_backends()
            
            # Update storage preferences
            self.storage_preferences = self.config["storage_preferences"]
            
            return True
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            Dictionary containing the current configuration
        """
        return self.config
    
    def detect_file_type(self, path: str, storage_type: Optional[str] = None) -> str:
        """
        Detect the type of a file based on its extension and content.
        
        Args:
            path: Path to the file
            storage_type: Storage type where the file is located
            
        Returns:
            Detected file type (code, document, image, etc.)
        """
        # Get storage backend
        storage = self._get_storage(storage_type, None)
        if storage is None:
            return "general"
            
        try:
            # Check if file exists
            if not storage.file_exists(path):
                return "general"
                
            # Get file info
            file_info = storage.get_file_info(path)
            
            # Get extension
            filename = file_info.get("name", "")
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            # Determine file type based on extension and MIME type
            mime_type = file_info.get("mime_type", "")
            
            # Code files
            if ext in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs', '.go', '.rb', '.php', '.html', '.css', '.sql']:
                return "code"
                
            # Document files
            if ext in ['.md', '.txt', '.doc', '.docx', '.pdf', '.odt', '.rtf']:
                return "document"
                
            # Knowledge files
            if ext in ['.json', '.yaml', '.yml', '.xml', '.csv', '.xlsx', '.xls']:
                return "knowledge"
                
            # Image files
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'] or mime_type.startswith('image/'):
                return "image"
                
            # Video files
            if ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'] or mime_type.startswith('video/'):
                return "video"
                
            # Audio files
            if ext in ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'] or mime_type.startswith('audio/'):
                return "audio"
                
            # Compressed files
            if ext in ['.zip', '.tar', '.gz', '.rar', '.7z', '.tar.gz']:
                return "compressed"
                
            # Default to general
            return "general"
        except Exception as e:
            logger.error(f"Error detecting file type: {e}", exc_info=True)
            return "general"
    
    def _get_storage(self, storage_type: Optional[str], file_type: Optional[str]) -> Optional[StorageBackend]:
        """
        Determine which storage backend to use based on specified parameters.
        
        Args:
            storage_type: Explicitly specified storage type
            file_type: File type for preference-based selection
            
        Returns:
            Storage backend instance or None if not available
        """
        # If storage_type is explicitly specified, use that
        if storage_type is not None:
            return self.storage_backends.get(storage_type)
            
        # If file_type is specified, use the preferred storage for that type
        if file_type is not None and file_type in self.storage_preferences:
            backend_name = self.storage_preferences[file_type]
            return self.storage_backends.get(backend_name)