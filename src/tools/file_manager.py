import os
import io
import re
import json
import shutil
import hashlib
import zipfile
import tarfile
import gzip
import pathlib
import mimetypes
import subprocess
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, BinaryIO, Optional, Union, Tuple, Any, Set, Iterator

# Import config system
from src.config import load_config, Config

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


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self, base_path: str = "data/files/local"):
        self.base_path = pathlib.Path(base_path)
        try:
            os.makedirs(self.base_path, exist_ok=True)
            print(f"Successfully initialized storage at {self.base_path}")
        except PermissionError:
            print(f"WARNING: Permission denied creating directory {self.base_path}")
            print(f"Will attempt to use existing directories or fallback to temporary storage")
            # Try to use a temporary directory as fallback
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_storage_path = os.path.join(temp_dir, "openmanus_storage")
            try:
                os.makedirs(temp_storage_path, exist_ok=True)
                self.base_path = pathlib.Path(temp_storage_path)
                print(f"Using fallback storage location: {self.base_path}")
            except Exception as e:
                print(f"ERROR: Failed to create fallback storage: {e}")
                # Last resort: use the current directory
                self.base_path = pathlib.Path('.')
                print(f"Using current directory as storage location")
        except Exception as e:
            print(f"ERROR: Failed to initialize storage at {self.base_path}: {e}")
            # Fallback to current directory
            self.base_path = pathlib.Path('.')
            print(f"Using current directory as storage location")
            
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
            print(f"Error searching files: {e}")
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
            print(f"Error getting file info: {e}")
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
            print(f"Error calculating file hash: {e}")
            return None


class GitStorageBackend(StorageBackend):
    """Git repository storage backend."""
    
    def __init__(self, repo_path: str = "data/files/git", 
                 user_name: str = "OpenManus", 
                 user_email: str = "openmanus@example.com"):
        self.repo_path = pathlib.Path(repo_path)
        self.user_name = user_name
        self.user_email = user_email
        self.initialized = False
        
        try:
            # Ensure the repo path exists
            os.makedirs(self.repo_path, exist_ok=True)
            print(f"Successfully created Git repository directory at {self.repo_path}")
        except PermissionError:
            print(f"WARNING: Permission denied creating directory {self.repo_path}")
            print(f"Will attempt to use existing directories or fallback to temporary storage")
            # Try to use a temporary directory as fallback
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_storage_path = os.path.join(temp_dir, "openmanus_git_storage")
            try:
                os.makedirs(temp_storage_path, exist_ok=True)
                self.repo_path = pathlib.Path(temp_storage_path)
                print(f"Using fallback Git storage location: {self.repo_path}")
            except Exception as e:
                print(f"ERROR: Failed to create fallback Git storage: {e}")
                # Last resort: use the current directory
                self.repo_path = pathlib.Path('git_storage')
                try:
                    os.makedirs(self.repo_path, exist_ok=True)
                    print(f"Using current directory as Git storage location: {self.repo_path}")
                except Exception as e2:
                    print(f"ERROR: Could not create Git storage anywhere: {e2}")
                    self.initialized = False
                    return
        except Exception as e:
            print(f"ERROR: Failed to initialize Git storage at {self.repo_path}: {e}")
            self.initialized = False
            return
            
        # Initialize mimetypes
        mimetypes.init()
        
        # Check if it's a git repo, initialize if not
        if not (self.repo_path / ".git").exists():
            try:
                # Initialize git repo
                subprocess.run(["git", "init"], cwd=self.repo_path, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Set up git config for commits
                subprocess.run(["git", "config", "user.name", self.user_name], 
                               cwd=self.repo_path, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["git", "config", "user.email", self.user_email], 
                               cwd=self.repo_path, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Initial commit
                try:
                    with open(self.repo_path / "README.md", "w") as f:
                        f.write(f"# OpenManus Git Storage\n\nThis repository is managed by OpenManus File Manager.")
                    
                    subprocess.run(["git", "add", "README.md"], 
                                   cwd=self.repo_path, check=True, 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    subprocess.run(["git", "commit", "-m", "Initial commit"], 
                                   cwd=self.repo_path, check=True, 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    print(f"Git repository successfully initialized at {self.repo_path}")
                    self.initialized = True
                except Exception as e:
                    print(f"WARNING: Could not create initial commit: {e}")
                    self.initialized = False
            except subprocess.CalledProcessError as e:
                print(f"Error initializing git repository: {e}")
                self.initialized = False
            except Exception as e:
                print(f"Unexpected error during Git initialization: {e}")
                self.initialized = False
        else:
            self.initialized = True
            print(f"Using existing Git repository at {self.repo_path}")
    
    def _full_path(self, path: str) -> pathlib.Path:
        """Get the full path by joining with repo_path."""
        # Use normpath to handle parent directory references (..)
        normalized = os.path.normpath(path)
        if normalized.startswith(".."):
            raise ValueError("Path cannot navigate above repository directory")
        return self.repo_path / normalized
    
    def read_file(self, path: str) -> bytes:
        """Read a file and return its contents as bytes."""
        if not self.initialized:
            print("WARNING: Git repository not properly initialized")
            raise IOError("Git repository not properly initialized")
            
        try:
            with open(self._full_path(path), 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
        except PermissionError:
            print(f"Permission denied when reading {path}")
            raise PermissionError(f"Permission denied when reading {path}")
        except Exception as e:
            print(f"Unexpected error reading file {path}: {e}")
            raise
    
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
        if not self.initialized:
            print("WARNING: Git repository not properly initialized")
            # Try to write the file anyway without git operations
            try:
                full_path = self._full_path(path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write the file
                with open(full_path, 'wb') as f:
                    f.write(content)
                
                print(f"File written to {full_path} but not committed (Git not initialized)")
                return True
            except Exception as e:
                print(f"Error writing file (Git not initialized): {e}")
                return False
            
        try:
            full_path = self._full_path(path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write the file
            with open(full_path, 'wb') as f:
                f.write(content)
            
            try:
                # Stage the file
                subprocess.run(["git", "add", path], 
                               cwd=self.repo_path, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Commit the change
                message = commit_message or f"Update file: {path}"
                subprocess.run(["git", "commit", "-m", message], 
                               cwd=self.repo_path, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                print(f"File successfully written and committed: {path}")
            except Exception as git_error:
                print(f"WARNING: File written but git operations failed: {git_error}")
                # The file was written successfully even though git operations failed
                return True
            
            return True
        except PermissionError as e:
            print(f"Permission denied when writing to {path}: {e}")
            return False
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
            
    def search_files(self, path: str, pattern: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Search for files matching a pattern in the git repository.
        
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
            
            # Use git ls-files for a more git-aware search
            git_cmd = ["git", "ls-files", "--full-name"]
            if not recursive:
                # Add path with trailing slash to list only direct children
                search_path = str(pathlib.Path(path)) + ("/" if path else "")
                git_cmd.append(search_path)
            else:
                # Search recursively from the specified path
                if path:
                    git_cmd.append(path)
            
            ls_files = subprocess.run(
                git_cmd,
                cwd=self.repo_path, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            file_list = ls_files.stdout.decode().strip().split("\n")
            for file_path in file_list:
                if not file_path:
                    continue
                
                # Check if the file matches the pattern
                file_name = os.path.basename(file_path)
                if pattern_regex.search(file_name):
                    full_file_path = self._full_path(file_path)
                    
                    # Get file info
                    try:
                        stat = full_file_path.stat()
                        
                        # Get last commit timestamp for the file
                        git_info = subprocess.run(
                            ["git", "log", "-1", "--format=%at", "--", file_path],
                            cwd=self.repo_path, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE
                        )
                        last_commit_time = git_info.stdout.decode().strip()
                        
                        if last_commit_time:
                            modified = datetime.fromtimestamp(int(last_commit_time)).isoformat()
                        else:
                            modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        
                        results.append({
                            "name": file_name,
                            "path": file_path,
                            "type": "file",  # Git ls-files only returns files
                            "size": stat.st_size,
                            "modified": modified,
                            "match": "name"  # Indicate that the name matched the pattern
                        })
                    except (FileNotFoundError, subprocess.SubprocessError):
                        # Skip files that can't be accessed
                        continue
            
            return results
        except Exception as e:
            print(f"Error searching files in git repository: {e}")
            return []
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file in the git repository.
        
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
            
            # Get git-specific information
            git_info = {}
            
            # Get last commit info
            try:
                last_commit = subprocess.run(
                    ["git", "log", "-1", "--format=%H|%an|%ae|%at|%s", "--", path],
                    cwd=self.repo_path, check=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                
                commit_info = last_commit.stdout.decode().strip()
                if commit_info:
                    parts = commit_info.split("|")
                    if len(parts) == 5:
                        commit_hash, author_name, author_email, timestamp, message = parts
                        git_info["last_commit"] = {
                            "hash": commit_hash,
                            "author": author_name,
                            "email": author_email,
                            "timestamp": datetime.fromtimestamp(int(timestamp)).isoformat(),
                            "message": message
                        }
            except subprocess.SubprocessError:
                # Failed to get git info, continue without it
                pass
                
            # Build the file info dictionary
            file_info = {
                "name": full_path.name,
                "path": str(full_path.relative_to(self.repo_path)),
                "type": "directory" if full_path.is_dir() else "file",
                "size": stat.st_size if full_path.is_file() else 0,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],  # Last 3 digits of octal mode
                "git": git_info
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
            print(f"Error getting file info from git repository: {e}")
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
            
            # For git repositories, we can use git hash-object if the hash type is sha1
            if hash_type == "sha1":
                try:
                    git_hash = subprocess.run(
                        ["git", "hash-object", path],
                        cwd=self.repo_path, check=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    return git_hash.stdout.decode().strip()
                except subprocess.SubprocessError:
                    # Fall back to manual calculation
                    pass
            
            # Manual hash calculation for other hash types or as fallback
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
            print(f"Error calculating file hash in git repository: {e}")
            return None


# Note: The following two classes would need to be properly implemented with the 
# respective APIs. These are skeleton implementations.
            
class GoogleDriveStorageBackend(StorageBackend):
    """Google Drive storage backend."""
    
    def __init__(self, credentials_path: str = None, root_folder: str = "OpenManus"):
        self.authenticated = False
        self.credentials_path = credentials_path
        self.root_folder = root_folder
        self.root_folder_id = None
        self.service = None
        self.path_cache = {}  # Cache for path to file ID mapping
        
        # Import Google Drive API dependencies
        try:
            from googleapiclient.discovery import build
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            import pickle
            
            self.googleapiclient_discovery = build
            self.InstalledAppFlow = InstalledAppFlow
            self.Request = Request
            self.Credentials = Credentials
            self.pickle = pickle
            
            # APIs imported successfully
            self.imports_successful = True
        except ImportError:
            print("Error: Google Drive API dependencies not installed.")
            print("Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            self.imports_successful = False
            return
        
        if not credentials_path:
            print("Note: GoogleDriveStorageBackend requires credentials_path for authentication.")
            return
            
        if not self.imports_successful:
            print("Cannot initialize Google Drive backend due to missing dependencies.")
            return
        
        try:
            # Define the scopes required
            SCOPES = ['https://www.googleapis.com/auth/drive']
            
            # Authenticate and create the Drive service
            creds = None
            token_path = os.path.join(os.path.dirname(credentials_path), 'token.pickle')
            
            # Check if token already exists
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = self.pickle.load(token)
            
            # If credentials don't exist or are invalid, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(self.Request())
                else:
                    flow = self.InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                os.makedirs(os.path.dirname(token_path), exist_ok=True)
                with open(token_path, 'wb') as token:
                    self.pickle.dump(creds, token)
            
            # Build the Drive service
            self.service = self.googleapiclient_discovery('drive', 'v3', credentials=creds)
            
            # Find or create the root folder
            self.root_folder_id = self._get_or_create_root_folder()
            
            self.authenticated = True
            print(f"Google Drive authentication successful, using root folder: {self.root_folder} (ID: {self.root_folder_id})")
        except Exception as e:
            print(f"Error authenticating with Google Drive: {e}")
            self.authenticated = False
    
    def _get_or_create_root_folder(self) -> str:
        """Find or create the root folder and return its ID."""
        if not self.service:
            raise Exception("Google Drive service not initialized")
            
        # Check if root folder exists
        response = self.service.files().list(
            q=f"name='{self.root_folder}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        folders = response.get('files', [])
        if folders:
            # Use the first matching folder
            return folders[0]['id']
        
        # Create the root folder if it doesn't exist
        folder_metadata = {
            'name': self.root_folder,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')
    
    def _get_parent_folder_id(self, path: str) -> str:
        """
        Get the ID of the parent folder for a given path.
        Creates intermediate folders if they don't exist.
        """
        if not self.authenticated or not self.service:
            raise Exception("Google Drive authentication required")
            
        if not path or path == '/' or path == '.':
            return self.root_folder_id
            
        # Split the path into components
        path_parts = os.path.normpath(path).split(os.sep)
        path_parts = [p for p in path_parts if p and p != '.']
        
        # Start from the root folder
        current_folder_id = self.root_folder_id
        
        # Navigate through each path component
        current_path = ""
        for i, folder_name in enumerate(path_parts[:-1]):  # All except the last component (which is the file name)
            current_path = os.path.join(current_path, folder_name)
            
            # Check if this path is in cache
            if current_path in self.path_cache:
                current_folder_id = self.path_cache[current_path]
                continue
                
            # Check if the folder exists
            query = f"name='{folder_name}' and '{current_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            folders = response.get('files', [])
            if folders:
                # Use the existing folder
                current_folder_id = folders[0]['id']
            else:
                # Create a new folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [current_folder_id]
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                current_folder_id = folder.get('id')
            
            # Cache this path
            self.path_cache[current_path] = current_folder_id
            
        return current_folder_id
    
    def _get_file_id(self, path: str) -> Optional[str]:
        """Get the ID of a file at the given path."""
        if not self.authenticated or not self.service:
            return None
            
        # Handle empty/root path
        if not path or path == "/" or path == ".":
            return self.root_folder_id
            
        # Check if this path is in cache
        if path in self.path_cache:
            return self.path_cache[path]
            
        # Get parent folder ID and file name
        parent_path = os.path.dirname(path)
        file_name = os.path.basename(path)
        
        parent_id = self._get_parent_folder_id(parent_path)
        
        # Query for the file in the parent folder
        query = f"name='{file_name}' and '{parent_id}' in parents and trashed=false"
        response = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType)'
        ).execute()
        
        files = response.get('files', [])
        if not files:
            return None
            
        file_id = files[0]['id']
        
        # Cache this path
        self.path_cache[path] = file_id
        
        return file_id
    
    def read_file(self, path: str) -> bytes:
        """Read a file from Google Drive."""
        if not self.authenticated or not self.service:
            raise Exception("Google Drive authentication required")
            
        file_id = self._get_file_id(path)
        if not file_id:
            raise FileNotFoundError(f"File not found: {path}")
            
        try:
            from googleapiclient.http import MediaIoBaseDownload
            
            # Download the file content
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                
            file_content.seek(0)
            return file_content.read()
        except Exception as e:
            print(f"Error reading file from Google Drive: {e}")
            raise
    
    def write_file(self, path: str, content: bytes) -> bool:
        """Write a file to Google Drive."""
        if not self.authenticated or not self.service:
            return False
            
        try:
            from googleapiclient.http import MediaInMemoryUpload
            
            # Get parent folder ID and file name
            parent_path = os.path.dirname(path)
            file_name = os.path.basename(path)
            
            parent_id = self._get_parent_folder_id(parent_path)
            
            # Check if file already exists
            file_id = self._get_file_id(path)
            
            # Prepare the file metadata and media content
            file_metadata = {
                'name': file_name,
            }
            
            media = MediaInMemoryUpload(content)
            
            if file_id:
                # Update existing file
                self.service.files().update(
                    fileId=file_id,
                    body=file_metadata,
                    media_body=media
                ).execute()
            else:
                # Create new file
                file_metadata['parents'] = [parent_id]
                self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                # Update the path cache to invalidate this path
                if path in self.path_cache:
                    del self.path_cache[path]
                
            return True
        except Exception as e:
            print(f"Error writing file to Google Drive: {e}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from Google Drive."""
        if not self.authenticated or not self.service:
            return False
            
        try:
            file_id = self._get_file_id(path)
            if not file_id:
                # File doesn't exist
                return False
                
            # Delete the file (move to trash)
            self.service.files().delete(fileId=file_id).execute()
            
            # Update the path cache to invalidate this path
            if path in self.path_cache:
                del self.path_cache[path]
                
            return True
        except Exception as e:
            print(f"Error deleting file from Google Drive: {e}")
            return False
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """List files in Google Drive."""
        if not self.authenticated or not self.service:
            return []
            
        try:
            folder_id = self._get_file_id(path) if path else self.root_folder_id
            if not folder_id:
                # Folder doesn't exist
                return []
            
            # Get files in the folder
            query = f"'{folder_id}' in parents and trashed=false"
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, size, modifiedTime, createdTime)'
            ).execute()
            
            files = response.get('files', [])
            
            # Convert to the expected format
            result = []
            for item in files:
                file_path = os.path.join(path, item['name']) if path else item['name']
                
                # Cache this path for future lookups
                self.path_cache[file_path] = item['id']
                
                is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
                
                result.append({
                    "name": item['name'],
                    "path": file_path,
                    "type": "directory" if is_folder else "file",
                    "size": int(item.get('size', 0)) if 'size' in item else 0,
                    "modified": item.get('modifiedTime'),
                    "created": item.get('createdTime'),
                    "id": item['id']
                })
                
            return result
        except Exception as e:
            print(f"Error listing files from Google Drive: {e}")
            return []
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in Google Drive."""
        if not self.authenticated or not self.service:
            return False
            
        try:
            file_id = self._get_file_id(path)
            return file_id is not None
        except Exception as e:
            print(f"Error checking file existence in Google Drive: {e}")
            return False
    
    def create_directory(self, path: str) -> bool:
        """Create a directory in Google Drive."""
        if not self.authenticated or not self.service:
            return False
            
        try:
            # Check if directory already exists
            if self.file_exists(path):
                return True
                
            # Get parent folder ID and directory name
            parent_path = os.path.dirname(path)
            dir_name = os.path.basename(path)
            
            parent_id = self._get_parent_folder_id(parent_path)
            
            # Create the folder
            folder_metadata = {
                'name': dir_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            
            # Cache this path
            self.path_cache[path] = folder.get('id')
            
            return True
        except Exception as e:
            print(f"Error creating directory in Google Drive: {e}")
            return False
    
    def rename_file(self, old_path: str, new_path: str) -> bool:
        """Rename a file in Google Drive."""
        if not self.authenticated or not self.service:
            return False
            
        try:
            # Get the file ID for the old path
            file_id = self._get_file_id(old_path)
            if not file_id:
                return False
                
            # Get the new parent folder ID and file name
            new_parent_path = os.path.dirname(new_path)
            new_file_name = os.path.basename(new_path)
            
            new_parent_id = self._get_parent_folder_id(new_parent_path)
            
            # Update the file
            file_metadata = {
                'name': new_file_name,
            }
            
            # If the parent directory has changed, update that too
            old_parent_path = os.path.dirname(old_path)
            if old_parent_path != new_parent_path:
                # Get previous parents to remove
                file = self.service.files().get(
                    fileId=file_id, 
                    fields='parents'
                ).execute()
                previous_parents = ",".join(file.get('parents'))
                
                # Move the file to the new folder
                file = self.service.files().update(
                    fileId=file_id,
                    body=file_metadata,
                    addParents=new_parent_id,
                    removeParents=previous_parents,
                    fields='id, parents'
                ).execute()
            else:
                # Just rename the file
                file = self.service.files().update(
                    fileId=file_id,
                    body=file_metadata,
                    fields='id'
                ).execute()
            
            # Update path cache
            if old_path in self.path_cache:
                del self.path_cache[old_path]
            self.path_cache[new_path] = file_id
            
            return True
        except Exception as e:
            print(f"Error renaming file in Google Drive: {e}")
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
        if not self.authenticated or not self.service:
            return []
            
        try:
            folder_id = self._get_file_id(path) if path else self.root_folder_id
            if not folder_id:
                return []
                
            # Compile the regex pattern
            pattern_regex = re.compile(pattern)
            
            # Results list
            results = []
            
            # Helper function to search recursively
            def search_folder(folder_id, current_path):
                # Get files in the folder
                query = f"'{folder_id}' in parents and trashed=false"
                response = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name, mimeType, size, modifiedTime)'
                ).execute()
                
                files = response.get('files', [])
                
                for item in files:
                    file_path = os.path.join(current_path, item['name']) if current_path else item['name']
                    
                    # Cache this path
                    self.path_cache[file_path] = item['id']
                    
                    # Check if the name matches the pattern
                    if pattern_regex.search(item['name']):
                        is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
                        
                        results.append({
                            "name": item['name'],
                            "path": file_path,
                            "type": "directory" if is_folder else "file",
                            "size": int(item.get('size', 0)) if 'size' in item else 0,
                            "modified": item.get('modifiedTime'),
                            "id": item['id'],
                            "match": "name"
                        })
                    
                    # If it's a directory and recursive flag is set, search inside it
                    if item['mimeType'] == 'application/vnd.google-apps.folder' and recursive:
                        search_folder(item['id'], file_path)
            
            # Start the search
            search_folder(folder_id, path)
            return results
        except Exception as e:
            print(f"Error searching files in Google Drive: {e}")
            return []
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            path: Path to the file
            
        Returns:
            Dictionary with detailed file information
        """
        if not self.authenticated or not self.service:
            return {"error": "Google Drive authentication required"}
            
        try:
            file_id = self._get_file_id(path)
            if not file_id:
                raise FileNotFoundError(f"File not found: {path}")
                
            # Get file metadata
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime, parents, description'
            ).execute()
            
            # Determine if it's a directory
            is_dir = file['mimeType'] == 'application/vnd.google-apps.folder'
            
            # Organize the file info
            file_info = {
                "name": file['name'],
                "path": path,
                "type": "directory" if is_dir else "file",
                "size": int(file.get('size', 0)) if 'size' in file else 0,
                "created": file.get('createdTime'),
                "modified": file.get('modifiedTime'),
                "id": file['id'],
                "mime_type": file['mimeType'],
            }
            
            if 'description' in file and file['description']:
                file_info["description"] = file['description']
                
            if 'parents' in file:
                file_info["parent_id"] = file['parents'][0]
                
            return file_info
        except Exception as e:
            print(f"Error getting file info from Google Drive: {e}")
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
        if not self.authenticated or not self.service:
            return None
            
        try:
            # Get file content
            content = self.read_file(path)
            
            # Calculate the hash
            hash_func = None
            if hash_type == "md5":
                hash_func = hashlib.md5()
            elif hash_type == "sha1":
                hash_func = hashlib.sha1()
            elif hash_type == "sha256":
                hash_func = hashlib.sha256()
            else:
                raise ValueError(f"Unsupported hash type: {hash_type}")
                
            hash_func.update(content)
            return hash_func.hexdigest()
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error calculating file hash for Google Drive file: {e}")
            return None


class OneDriveStorageBackend(StorageBackend):
    """OneDrive storage backend (placeholder)."""
    
    def __init__(self, credentials_path: str = None, root_folder: str = "OpenManus"):
        self.authenticated = False
        self.credentials_path = credentials_path
        self.root_folder = root_folder
        
        # In a real implementation, we would:
        # 1. Load OneDrive API credentials
        # 2. Authenticate with OneDrive
        # 3. Set up a client
        
        if credentials_path:
            try:
                # Here would be the actual implementation of OneDrive API authentication
                # Using libraries like msal (Microsoft Authentication Library) and the Microsoft Graph API
                # 
                # Example code (commented out since we don't have the dependencies):
                #
                # import msal
                # import json
                # import requests
                #
                # # Load the credentials file (should contain client_id, tenant_id, etc.)
                # with open(credentials_path, 'r') as f:
                #     config = json.load(f)
                #
                # # Create the MSAL app
                # app = msal.PublicClientApplication(
                #     config["client_id"],
                #     authority=f"https://login.microsoftonline.com/{config['tenant_id']}"
                # )
                #
                # # Try to get token silently from cache
                # result = None
                # accounts = app.get_accounts()
                # if accounts:
                #     result = app.acquire_token_silent(
                #         scopes=["https://graph.microsoft.com/.default"],
                #         account=accounts[0]
                #     )
                #
                # # If no token in cache, get a new one interactively
                # if not result:
                #     result = app.acquire_token_interactive(
                #         scopes=["https://graph.microsoft.com/.default"]
                #     )
                #
                # # Check if we have an access token
                # if "access_token" in result:
                #     self.access_token = result["access_token"]
                #     self.headers = {"Authorization": f"Bearer {self.access_token}"}
                #
                #     # Check if root folder exists, create if not
                #     drive_response = requests.get(
                #         "https://graph.microsoft.com/v1.0/me/drive/root/children",
                #         headers=self.headers
                #     )
                #     
                #     if drive_response.status_code == 200:
                #         folders = [item for item in drive_response.json()["value"] 
                #                   if item["name"] == self.root_folder and item["folder"]]
                #                   
                #         if not folders:
                #             # Create the root folder
                #             folder_response = requests.post(
                #                 "https://graph.microsoft.com/v1.0/me/drive/root/children",
                #                 headers=self.headers,
                #                 json={
                #                     "name": self.root_folder,
                #                     "folder": {},
                #                     "@microsoft.graph.conflictBehavior": "rename"
                #                 }
                #             )
                #             
                #             if folder_response.status_code == 201:
                #                 self.root_folder_id = folder_response.json()["id"]
                #             else:
                #                 raise Exception(f"Failed to create root folder: {folder_response.text}")
                #         else:
                #             self.root_folder_id = folders[0]["id"]
                
                self.authenticated = True
                print(f"OneDrive authentication successful, using root folder: {self.root_folder}")
            except Exception as e:
                print(f"Error authenticating with OneDrive: {e}")
                self.authenticated = False
        else:
            # Placeholder authentication message
            print("Note: OneDriveStorageBackend requires credentials_path for authentication.")
    
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
                        print("Google Drive backend requires credentials_path to be set")
                        self.storage_backends["google_drive"] = None
                    else:
                        self.storage_backends["google_drive"] = GoogleDriveStorageBackend(
                            credentials_path=backend_config.get("credentials_path"),
                            root_folder=backend_config.get("root_folder", "OpenManus")
                        )
                        self.base_paths["google_drive"] = backend_config.get("root_folder", "OpenManus")
                
                elif backend_name == "onedrive":
                    if backend_config["requires_auth"] and not backend_config.get("credentials_path"):
                        print("OneDrive backend requires credentials_path to be set")
                        self.storage_backends["onedrive"] = None
                    else:
                        self.storage_backends["onedrive"] = OneDriveStorageBackend(
                            credentials_path=backend_config.get("credentials_path"),
                            root_folder=backend_config.get("root_folder", "OpenManus")
                        )
                        self.base_paths["onedrive"] = backend_config.get("root_folder", "OpenManus")
                
                else:
                    print(f"Unknown backend type: {backend_name}")
                    self.storage_backends[backend_name] = None
            
            except Exception as e:
                print(f"Error initializing {backend_name} backend: {e}")
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
                    print("Google Drive backend requires credentials_path")
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
                    print("OneDrive backend requires credentials_path")
                    return False
                    
                self.storage_backends["onedrive"] = OneDriveStorageBackend(
                    credentials_path=credentials_path,
                    root_folder=root_folder
                )
                self.base_paths["onedrive"] = root_folder
                return self.storage_backends["onedrive"].authenticated
                
            else:
                print(f"Unknown backend type: {backend_type}")
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
            print(f"Error searching files: {e}")
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
            print(f"Error getting file info: {e}")
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
            print(f"Error calculating file hash: {e}")
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
            print(f"Error saving tags: {e}")
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
            print(f"Error compressing file: {e}")
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
            print(f"Error decompressing file: {e}")
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
            print(f"Error synchronizing file: {e}")
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
            print(f"Error saving configuration: {e}")
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
                print(f"Configuration file not found: {config_path}")
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
            print(f"Error loading configuration: {e}")
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
            print(f"Error detecting file type: {e}")
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
            
        # Default to local storage
        return self.storage_backends.get("local")