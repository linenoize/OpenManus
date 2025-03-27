"""
Git repository storage backend.
"""
import os
import re
import hashlib
import pathlib
import mimetypes
import subprocess
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.tools.storage_backends.base import StorageBackend, StorageBackendError

# Set up logging
logger = logging.getLogger(__name__)

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
            logger.info(f"Successfully created Git repository directory at {self.repo_path}")
        except PermissionError:
            logger.warning(f"Permission denied creating directory {self.repo_path}")
            logger.warning(f"Will attempt to use existing directories or fallback to temporary storage")
            # Try to use a temporary directory as fallback
            temp_dir = tempfile.gettempdir()
            temp_storage_path = os.path.join(temp_dir, "openmanus_git_storage")
            try:
                os.makedirs(temp_storage_path, exist_ok=True)
                self.repo_path = pathlib.Path(temp_storage_path)
                logger.info(f"Using fallback Git storage location: {self.repo_path}")
            except Exception as e:
                logger.error(f"Failed to create fallback Git storage: {e}")
                # Last resort: use the current directory
                self.repo_path = pathlib.Path('git_storage')
                try:
                    os.makedirs(self.repo_path, exist_ok=True)
                    logger.info(f"Using current directory as Git storage location: {self.repo_path}")
                except Exception as e2:
                    logger.error(f"Could not create Git storage anywhere: {e2}")
                    self.initialized = False
                    return
        except Exception as e:
            logger.error(f"Failed to initialize Git storage at {self.repo_path}: {e}", exc_info=True)
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
                    logger.info(f"Git repository successfully initialized at {self.repo_path}")
                    self.initialized = True
                except Exception as e:
                    logger.warning(f"Could not create initial commit: {e}")
                    self.initialized = False
            except subprocess.CalledProcessError as e:
                logger.error(f"Error initializing git repository: {e}")
                self.initialized = False
            except Exception as e:
                logger.error(f"Unexpected error during Git initialization: {e}", exc_info=True)
                self.initialized = False
        else:
            self.initialized = True
            logger.info(f"Using existing Git repository at {self.repo_path}")
    
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
            logger.warning("Git repository not properly initialized")
            raise StorageBackendError("Git repository not properly initialized")
            
        try:
            with open(self._full_path(path), 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
        except PermissionError:
            logger.error(f"Permission denied when reading {path}")
            raise PermissionError(f"Permission denied when reading {path}")
        except Exception as e:
            logger.error(f"Unexpected error reading file {path}: {e}", exc_info=True)
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
            logger.warning("Git repository not properly initialized")
            # Try to write the file anyway without git operations
            try:
                full_path = self._full_path(path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write the file
                with open(full_path, 'wb') as f:
                    f.write(content)
                
                logger.info(f"File written to {full_path} but not committed (Git not initialized)")
                return True
            except Exception as e:
                logger.error(f"Error writing file (Git not initialized): {e}", exc_info=True)
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
                
                logger.info(f"File successfully written and committed: {path}")
            except Exception as git_error:
                logger.warning(f"File written but git operations failed: {git_error}")
                # The file was written successfully even though git operations failed
                return True
            
            return True
        except PermissionError as e:
            logger.error(f"Permission denied when writing to {path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error writing to git repository: {e}", exc_info=True)
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
            logger.error(f"Error deleting from git repository: {e}", exc_info=True)
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
            logger.error(f"Error listing files in git repository: {e}", exc_info=True)
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
            logger.error(f"Error creating directory in git repository: {e}", exc_info=True)
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
            logger.error(f"Error renaming file in git repository: {e}", exc_info=True)
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
            logger.error(f"Error getting file history: {e}", exc_info=True)
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
            logger.error(f"Error searching files in git repository: {e}", exc_info=True)
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
            logger.error(f"Error getting file info from git repository: {e}", exc_info=True)
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
            logger.error(f"Error calculating file hash in git repository: {e}", exc_info=True)
            return None