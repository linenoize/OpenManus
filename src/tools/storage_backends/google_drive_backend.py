"""
Google Drive storage backend.
"""
import os
import re
import io
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, BinaryIO

from src.tools.storage_backends.base import StorageBackend, StorageBackendError

# Set up logging
logger = logging.getLogger(__name__)

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
            logger.error("Google Drive API dependencies not installed.")
            logger.error("Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            self.imports_successful = False
            return
        
        if not credentials_path:
            logger.warning("GoogleDriveStorageBackend requires credentials_path for authentication.")
            return
            
        if not self.imports_successful:
            logger.error("Cannot initialize Google Drive backend due to missing dependencies.")
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
            logger.info(f"Google Drive authentication successful, using root folder: {self.root_folder} (ID: {self.root_folder_id})")
        except Exception as e:
            logger.error(f"Error authenticating with Google Drive: {e}", exc_info=True)
            self.authenticated = False
    
    def _get_or_create_root_folder(self) -> str:
        """Find or create the root folder and return its ID."""
        if not self.service:
            raise StorageBackendError("Google Drive service not initialized")
            
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
            raise StorageBackendError("Google Drive authentication required")
            
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
            raise StorageBackendError("Google Drive authentication required")
            
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
            logger.error(f"Error reading file from Google Drive: {e}", exc_info=True)
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
            logger.error(f"Error writing file to Google Drive: {e}", exc_info=True)
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
            logger.error(f"Error deleting file from Google Drive: {e}", exc_info=True)
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
            logger.error(f"Error listing files from Google Drive: {e}", exc_info=True)
            return []
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in Google Drive."""
        if not self.authenticated or not self.service:
            return False
            
        try:
            file_id = self._get_file_id(path)
            return file_id is not None
        except Exception as e:
            logger.error(f"Error checking file existence in Google Drive: {e}", exc_info=True)
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
            logger.error(f"Error creating directory in Google Drive: {e}", exc_info=True)
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
            logger.error(f"Error renaming file in Google Drive: {e}", exc_info=True)
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
            logger.error(f"Error searching files in Google Drive: {e}", exc_info=True)
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
            logger.error(f"Error getting file info from Google Drive: {e}", exc_info=True)
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
            logger.error(f"Error calculating file hash for Google Drive file: {e}", exc_info=True)
            return None