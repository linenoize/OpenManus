"""
Local filesystem storage backend.
"""
import os
import re
import hashlib
import pathlib
import shutil
import mimetypes
import tempfile
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.tools.storage_backends.base import StorageBackend, FileOperationError

# Set up logging
logger = logging.getLogger(__name__)

class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self, base_path: str = "data/files/local"):
        self.base_path = pathlib.Path(base_path)
        try:
            os.makedirs(self.base_path, exist_ok=True)
            logger.info(f"Successfully initialized storage at {self.base_path}")
        except PermissionError:
            logger.warning(f"Permission denied creating directory {self.base_path}")
            logger.warning(f"Will attempt to use existing directories or fallback to temporary storage")
            # Try to use a temporary directory as fallback
            temp_dir = tempfile.gettempdir()
            temp_storage_path = os.path.join(temp_dir, "openmanus_storage")
            try:
                os.makedirs(temp_storage_path, exist_ok=True)
                self.base_path = pathlib.Path(temp_storage_path)
                logger.info(f"Using fallback storage location: {self.base_path}")
            except Exception as e:
                logger.error(f"Failed to create fallback storage: {e}")
                # Last resort: use the current directory
                self.base_path = pathlib.Path('.')
                logger.warning(f"Using current directory as storage location")
        except Exception as e:
            logger.error(f"Failed to initialize storage at {self.base_path}: {e}", exc_info=True)
            # Fallback to current directory
            self.base_path = pathlib.Path('.')
            logger.warning(f"Using current directory as storage location")
            
        # Initialize mimetypes
        mimetypes.init()
    
    def _full_path(self, path: str) -> pathlib.Path:
        """Get the full path by joining with base_path."""
        # Use normpath to handle parent directory references (..)
        normalized = os.path.normpath(path)
        if normalized.startswith(".."):
            raise ValueError("Path cannot navigate above base directory")
        return self.base_path / normalized
    
    def read_file(self, path: str) -> bytes:
        """Read a file and return its contents as bytes."""
        try:
            with open(self._full_path(path), 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
    
    def write_file(self, path: str, content: bytes) -> bool:
        """Write content to a file."""
        try:
            full_path = self._full_path(path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing file: {e}", exc_info=True)
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        try:
            full_path = self._full_path(path)
            if full_path.is_file():
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}", exc_info=True)
            return False
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """List files in a directory."""
        try:
            full_path = self._full_path(path)
            if not full_path.exists():
                return []
            
            result = []
            for item in full_path.iterdir():
                stat = item.stat()
                relative_path = str(item.relative_to(self.base_path))
                result.append({
                    "name": item.name,
                    "path": relative_path,
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            return result
        except Exception as e:
            logger.error(f"Error listing files: {e}", exc_info=True)
            return []
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        return self._full_path(path).exists()
    
    def create_directory(self, path: str) -> bool:
        """Create a directory."""
        try:
            full_path = self._full_path(path)
            os.makedirs(full_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory: {e}", exc_info=True)
            return False
    
    def rename_file(self, old_path: str, new_path: str) -> bool:
        """Rename or move a file."""
        try:
            old_full_path = self._full_path(old_path)
            new_full_path = self._full_path(new_path)
            
            if not old_full_path.exists():
                return False
                
            # Create parent directories for the new path if needed
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
            
            # Move the file
            shutil.move(old_full_path, new_full_path)
            return True
        except Exception as e:
            logger.error(f"Error renaming file: {e}", exc_info=True)
            return False
    
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
        try:
            full_path = self._full_path(path)
            if not full_path.exists():
                return []
            
            results = []
            pattern_regex = re.compile(pattern)
            
            # Define a recursive function to walk directories
            def walk_directory(current_path):
                for item in current_path.iterdir():
                    # Check if the item name matches the pattern
                    if pattern_regex.search(item.name):
                        stat = item.stat()
                        relative_path = str(item.relative_to(self.base_path))
                        results.append({
                            "name": item.name,
                            "path": relative_path,
                            "type": "directory" if item.is_dir() else "file",
                            "size": stat.st_size if item.is_file() else 0,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "match": "name"  # Indicate that the name matched the pattern
                        })
                    
                    # If it's a directory and we're searching recursively, search inside it
                    if item.is_dir() and recursive:
                        walk_directory(item)
            
            # Start the search
            walk_directory(full_path)
            return results
        except Exception as e:
            logger.error(f"Error searching files: {e}", exc_info=True)
            return []
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            path: Path to the file
            
        Returns:
            Dictionary with detailed file information
        """
        try:
            full_path = self._full_path(path)
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            stat = full_path.stat()
            file_info = {
                "name": full_path.name,
                "path": str(full_path.relative_to(self.base_path)),
                "type": "directory" if full_path.is_dir() else "file",
                "size": stat.st_size if full_path.is_file() else 0,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],  # Last 3 digits of octal mode
            }
            
            # Add additional information for files
            if full_path.is_file():
                # Guess MIME type
                mime_type, encoding = mimetypes.guess_type(full_path)
                file_info["mime_type"] = mime_type or "application/octet-stream"
                if encoding:
                    file_info["encoding"] = encoding
                
                # Check if it's a text file (simple heuristic)
                try:
                    with open(full_path, 'rb') as f:
                        sample = f.read(1024)  # Read a sample of the file
                        # Check if it's likely to be text
                        is_text = True
                        for byte in sample:
                            if byte < 9 or (byte > 13 and byte < 32 and byte != 127):
                                is_text = False
                                break
                        file_info["is_text"] = is_text
                except:
                    file_info["is_text"] = False
            
            return file_info
        except Exception as e:
            logger.error(f"Error getting file info: {e}", exc_info=True)
            return {"error": str(e)}
    
    def get_file_hash(self, path: str, hash_type: str = "sha256") -> Optional[str]:
        """
        Calculate a hash of the file contents.
        
        Args:
            path: Path to the file
            hash_type: Type of hash to calculate (md5, sha1, sha256, etc.)
            
        Returns:
            Hex digest of the hash, or None if the file doesn't exist
        """
        try:
            full_path = self._full_path(path)
            if not full_path.exists() or not full_path.is_file():
                return None
            
            hash_func = None
            if hash_type == "md5":
                hash_func = hashlib.md5()
            elif hash_type == "sha1":
                hash_func = hashlib.sha1()
            elif hash_type == "sha256":
                hash_func = hashlib.sha256()
            else:
                raise ValueError(f"Unsupported hash type: {hash_type}")
            
            with open(full_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}", exc_info=True)
            return None