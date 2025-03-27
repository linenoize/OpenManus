"""
Base classes and exceptions for storage backends.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

# Set up logging
logger = logging.getLogger(__name__)

class FileManagerError(Exception):
    """Base exception for all file manager errors."""
    pass

class StorageBackendError(FileManagerError):
    """Exception raised for errors in storage backends."""
    pass

class FileOperationError(FileManagerError):
    """Exception raised for errors during file operations."""
    pass

class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def read_file(self, path: str) -> bytes:
        """Read a file and return its contents as bytes."""
        pass
    
    @abstractmethod
    def write_file(self, path: str, content: bytes) -> bool:
        """Write content to a file."""
        pass
    
    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        pass
    
    @abstractmethod
    def list_files(self, path: str) -> List[Dict[str, Any]]:
        """List files in a directory."""
        pass
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        pass
    
    @abstractmethod
    def create_directory(self, path: str) -> bool:
        """Create a directory."""
        pass
    
    @abstractmethod
    def rename_file(self, old_path: str, new_path: str) -> bool:
        """Rename or move a file."""
        pass
    
    @abstractmethod
    def search_files(self, path: str, pattern: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Search for files matching a pattern.
        
        Args:
            path: Base directory to search in
            pattern: Regular expression pattern to match against file names
            recursive: Whether to search recursively through subdirectories
            
        Returns:
            List of matching file information dictionaries
        """
        pass
    
    @abstractmethod
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            path: Path to the file
            
        Returns:
            Dictionary with detailed file information
        """
        pass
    
    @abstractmethod
    def get_file_hash(self, path: str, hash_type: str = "sha256") -> Optional[str]:
        """
        Calculate a hash of the file contents.
        
        Args:
            path: Path to the file
            hash_type: Type of hash to calculate (md5, sha1, sha256, etc.)
            
        Returns:
            Hex digest of the hash, or None if the file doesn't exist
        """
        pass