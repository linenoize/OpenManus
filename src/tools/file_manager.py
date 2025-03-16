import os
import json
import shutil
import pathlib
from typing import Dict, List, BinaryIO, Optional, Union, Tuple, Any
from datetime import datetime
from abc import ABC, abstractmethod
import subprocess

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


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self, base_path: str = "data/files/local"):
        self.base_path = pathlib.Path(base_path)
        os.makedirs(self.base_path, exist_ok=True)
    
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
            print(f"Error writing file: {e}")
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
            print(f"Error deleting file: {e}")
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
            print(f"Error listing files: {e}")
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
            print(f"Error creating directory: {e}")
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
            print(f"Error renaming file: {e}")
            return False


class GitStorageBackend(StorageBackend):
    """Git repository storage backend."""
    
    def __init__(self, repo_path: str = "data/files/git"):
        self.repo_path = pathlib.Path(repo_path)
        
        # Ensure the repo path exists
        os.makedirs(self.repo_path, exist_ok=True)
        
        # Check if it's a git repo, initialize if not
        if not (self.repo_path / ".git").exists():
            try:
                # Initialize git repo
                subprocess.run(["git", "init"], cwd=self.repo_path, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Set up git config for commits
                subprocess.run(["git", "config", "user.name", "OpenManus"], 
                               cwd=self.repo_path, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["git", "config", "user.email", "openmanus@example.com"], 
                               cwd=self.repo_path, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Initial commit
                with open(self.repo_path / "README.md", "w") as f:
                    f.write("# OpenManus Git Storage\n\nThis repository is managed by OpenManus File Manager.")
                
                subprocess.run(["git", "add", "README.md"], 
                               cwd=self.repo_path, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["git", "commit", "-m", "Initial commit"], 
                               cwd=self.repo_path, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                print(f"Error initializing git repository: {e}")
    
    def _full_path(self, path: str) -> pathlib.Path:
        """Get the full path by joining with repo_path."""
        # Use normpath to handle parent directory references (..)
        normalized = os.path.normpath(path)
        if normalized.startswith(".."):
            raise ValueError("Path cannot navigate above repository directory")
        return self.repo_path / normalized
    
    def read_file(self, path: str) -> bytes:
        """Read a file and return its contents as bytes."""
        try:
            with open(self._full_path(path), 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
    
    def write_file(self, path: str, content: bytes, commit_message: Optional[str] = None) -> bool:
        """
        Write content to a file and commit it.
        
        Args:
            path: File path
            content: File content
            commit_message: Optional commit message. If None, a default message is used.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self._full_path(path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write the file
            with open(full_path, 'wb') as f:
                f.write(content)
            
            # Stage the file
            subprocess.run(["git", "add", path], 
                           cwd=self.repo_path, check=True, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Commit the change
            message = commit_message or f"Update file: {path}"
            subprocess.run(["git", "commit", "-m", message], 
                           cwd=self.repo_path, check=True, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return True
        except Exception as e:
            print(f"Error writing to git repository: {e}")
            return False
    
    def delete_file(self, path: str, commit_message: Optional[str] = None) -> bool:
        """
        Delete a file and commit the change.
        
        Args:
            path: File path
            commit_message: Optional commit message. If None, a default message is used.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self._full_path(path)
            
            if not full_path.exists():
                return False
            
            # Remove the file
            subprocess.run(["git", "rm", path], 
                           cwd=self.repo_path, check=True, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Commit the change
            message = commit_message or f"Delete file: {path}"
            subprocess.run(["git", "commit", "-m", message], 
                           cwd=self.repo_path, check=True, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return True
        except Exception as e:
            print(f"Error deleting from git repository: {e}")
            return False
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """List files in a directory within the git repository."""
        try:
            full_path = self._full_path(path)
            if not full_path.exists():
                return []
            
            result = []
            for item in full_path.iterdir():
                # Skip .git directory
                if item.name == ".git":
                    continue
                    
                stat = item.stat()
                relative_path = str(item.relative_to(self.repo_path))
                
                # Get last modification info from git
                try:
                    git_info = subprocess.run(
                        ["git", "log", "-1", "--format=%at", "--", relative_path],
                        cwd=self.repo_path, check=True, 
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    last_commit_time = git_info.stdout.decode().strip()
                    if last_commit_time:
                        modified = datetime.fromtimestamp(int(last_commit_time)).isoformat()
                    else:
                        modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                except:
                    modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                result.append({
                    "name": item.name,
                    "path": relative_path,
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": modified
                })
            return result
        except Exception as e:
            print(f"Error listing files in git repository: {e}")
            return []
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the repository."""
        return self._full_path(path).exists()
    
    def create_directory(self, path: str) -> bool:
        """
        Create a directory in the repository.
        Git doesn't track empty directories, so we create a .gitkeep file.
        """
        try:
            full_path = self._full_path(path)
            os.makedirs(full_path, exist_ok=True)
            
            # Create .gitkeep to ensure directory is tracked
            gitkeep_path = full_path / ".gitkeep"
            with open(gitkeep_path, 'w') as f:
                pass
            
            # Stage and commit
            subprocess.run(["git", "add", f"{path}/.gitkeep"], 
                           cwd=self.repo_path, check=True, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["git", "commit", "-m", f"Create directory: {path}"], 
                           cwd=self.repo_path, check=True, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return True
        except Exception as e:
            print(f"Error creating directory in git repository: {e}")
            return False
    
    def rename_file(self, old_path: str, new_path: str, commit_message: Optional[str] = None) -> bool:
        """
        Rename or move a file in the repository.
        
        Args:
            old_path: Current file path
            new_path: New file path
            commit_message: Optional commit message. If None, a default message is used.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.file_exists(old_path):
                return False
                
            # Create parent directories for the new path if needed
            new_full_path = self._full_path(new_path)
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
            
            # Use git mv to move/rename the file
            subprocess.run(["git", "mv", old_path, new_path], 
                           cwd=self.repo_path, check=True, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Commit the change
            message = commit_message or f"Rename file: {old_path} → {new_path}"
            subprocess.run(["git", "commit", "-m", message], 
                           cwd=self.repo_path, check=True, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return True
        except Exception as e:
            print(f"Error renaming file in git repository: {e}")
            return False
    
    def get_file_history(self, path: str, max_entries: int = 10) -> List[Dict[str, Any]]:
        """
        Get the commit history for a file.
        
        Args:
            path: File path
            max_entries: Maximum number of history entries to return
            
        Returns:
            List of commit information dictionaries
        """
        try:
            # Check if file exists
            if not self.file_exists(path):
                return []
                
            # Get git log
            git_log = subprocess.run(
                ["git", "log", f"-{max_entries}", "--format=%H|%an|%at|%s", "--", path],
                cwd=self.repo_path, check=True, 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            log_entries = git_log.stdout.decode().strip().split("\n")
            history = []
            
            for entry in log_entries:
                if not entry:
                    continue
                    
                parts = entry.split("|")
                if len(parts) != 4:
                    continue
                    
                commit_hash, author, timestamp, message = parts
                history.append({
                    "commit_hash": commit_hash,
                    "author": author,
                    "timestamp": datetime.fromtimestamp(int(timestamp)).isoformat(),
                    "message": message
                })
                
            return history
        except Exception as e:
            print(f"Error getting file history: {e}")
            return []


# Note: The following two classes would need to be properly implemented with the 
# respective APIs. These are skeleton implementations.
            
class GoogleDriveStorageBackend(StorageBackend):
    """Google Drive storage backend (placeholder)."""
    
    def __init__(self, credentials_path: str = None):
        self.authenticated = False
        
        # In a real implementation, we would:
        # 1. Load Google Drive API credentials
        # 2. Authenticate with Google Drive
        # 3. Set up a client
        
        # Placeholder authentication message
        print("Note: GoogleDriveStorageBackend is a placeholder. Actual authentication required.")
    
    def read_file(self, path: str) -> bytes:
        """Read a file from Google Drive."""
        raise NotImplementedError("Google Drive backend not fully implemented")
    
    def write_file(self, path: str, content: bytes) -> bool:
        """Write a file to Google Drive."""
        raise NotImplementedError("Google Drive backend not fully implemented")
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from Google Drive."""
        raise NotImplementedError("Google Drive backend not fully implemented")
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """List files in Google Drive."""
        raise NotImplementedError("Google Drive backend not fully implemented")
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in Google Drive."""
        raise NotImplementedError("Google Drive backend not fully implemented")
    
    def create_directory(self, path: str) -> bool:
        """Create a directory in Google Drive."""
        raise NotImplementedError("Google Drive backend not fully implemented")
    
    def rename_file(self, old_path: str, new_path: str) -> bool:
        """Rename a file in Google Drive."""
        raise NotImplementedError("Google Drive backend not fully implemented")


class OneDriveStorageBackend(StorageBackend):
    """OneDrive storage backend (placeholder)."""
    
    def __init__(self, credentials_path: str = None):
        self.authenticated = False
        
        # In a real implementation, we would:
        # 1. Load OneDrive API credentials
        # 2. Authenticate with OneDrive
        # 3. Set up a client
        
        # Placeholder authentication message
        print("Note: OneDriveStorageBackend is a placeholder. Actual authentication required.")
    
    def read_file(self, path: str) -> bytes:
        """Read a file from OneDrive."""
        raise NotImplementedError("OneDrive backend not fully implemented")
    
    def write_file(self, path: str, content: bytes) -> bool:
        """Write a file to OneDrive."""
        raise NotImplementedError("OneDrive backend not fully implemented")
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from OneDrive."""
        raise NotImplementedError("OneDrive backend not fully implemented")
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """List files in OneDrive."""
        raise NotImplementedError("OneDrive backend not fully implemented")
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in OneDrive."""
        raise NotImplementedError("OneDrive backend not fully implemented")
    
    def create_directory(self, path: str) -> bool:
        """Create a directory in OneDrive."""
        raise NotImplementedError("OneDrive backend not fully implemented")
    
    def rename_file(self, old_path: str, new_path: str) -> bool:
        """Rename a file in OneDrive."""
        raise NotImplementedError("OneDrive backend not fully implemented")


class FileManagerTool:
    """
    Tool for managing files across different storage backends.
    Provides a unified interface for file operations with multiple storage options.
    """
    
    def __init__(self):
        """
        Initialize the file manager tool with different storage backends.
        """
        # Initialize default storage base paths
        self.base_paths = {
            "local": "data/files/local",
            "git": "data/files/git",
            "google_drive": None,  # Would use credentials in a real implementation
            "onedrive": None       # Would use credentials in a real implementation
        }
        
        # Create and store storage backends
        self.storage_backends = {
            "local": LocalStorageBackend(self.base_paths["local"]),
            "git": GitStorageBackend(self.base_paths["git"]),
            # These would be properly initialized in a real implementation
            "google_drive": None,
            "onedrive": None
        }
        
        # Default storage preferences for different file types
        self.storage_preferences = {
            # Default for temporary or short-term files
            "temp": "local",
            
            # Default for code and knowledge base files
            "code": "git",
            "knowledge": "git",
            "document": "git",
            
            # Default for media files (would be Google Drive in full implementation)
            "image": "local",
            "video": "local",
            "audio": "local",
            
            # Default for general files
            "general": "local"
        }
    
    def initialize_backend(self, backend_type: str, **kwargs) -> bool:
        """
        Initialize or update a specific storage backend.
        
        Args:
            backend_type: The backend to initialize ('google_drive', 'onedrive')
            **kwargs: Backend-specific initialization parameters
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if backend_type == "google_drive":
                credentials_path = kwargs.get("credentials_path")
                if not credentials_path:
                    return False
                self.storage_backends["google_drive"] = GoogleDriveStorageBackend(credentials_path)
                return True
            elif backend_type == "onedrive":
                credentials_path = kwargs.get("credentials_path")
                if not credentials_path:
                    return False
                self.storage_backends["onedrive"] = OneDriveStorageBackend(credentials_path)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error initializing backend {backend_type}: {e}")
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
            print(f"Error reading file: {e}")
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
            print(f"Error writing file: {e}")
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
            print(f"Error deleting file: {e}")
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
            print(f"Error listing files: {e}")
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
            print(f"Error checking if file exists: {e}")
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
            print(f"Error creating directory: {e}")
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
            print(f"Error renaming file: {e}")
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
            print(f"Error decoding file as {encoding}")
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
            print(f"Error writing text file: {e}")
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
            print(f"Error getting file history: {e}")
            return []
    
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
            
        # Default to local storage
        return self.storage_backends.get("local")