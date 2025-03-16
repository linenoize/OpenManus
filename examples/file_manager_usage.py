#!/usr/bin/env python3
"""
Example usage of the FileManagerTool.

This script demonstrates how to use the FileManagerTool for file operations
with different storage backends. It shows storing files in different backends
based on file type, setting storage preferences, and backend-specific features.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.file_manager import FileManagerTool

def main():
    # Initialize the FileManagerTool
    file_manager = FileManagerTool()
    
    print("OpenManus File Manager Tool Example")
    print("===================================")
    
    # Display current storage preferences
    print("\n1. Current storage preferences:")
    preferences = file_manager.get_storage_preferences()
    for file_type, storage in preferences.items():
        print(f"  - {file_type}: {storage}")
    
    # Store a text file as code (will go to git by default)
    print("\n2. Storing a Python file as 'code' (should use git):")
    code_content = """
def hello():
    print("Hello from OpenManus!")

if __name__ == "__main__":
    hello()
"""
    file_manager.write_text("hello.py", code_content, file_type="code", 
                          metadata={"commit_message": "Add hello function"})
    print("  - File stored successfully")
    
    # Store a temporary file (will go to local by default)
    print("\n3. Storing a temporary file (should use local):")
    temp_content = "This is temporary data that doesn't need version control."
    file_manager.write_text("temp_data.txt", temp_content, file_type="temp")
    print("  - File stored successfully")
    
    # List files in different storage backends
    print("\n4. Listing files in git storage:")
    git_files = file_manager.list_files(storage_type="git")
    for file in git_files:
        print(f"  - {file['path']} ({file['type']}, {file['size']} bytes)")
    
    print("\n5. Listing files in local storage:")
    local_files = file_manager.list_files(storage_type="local")
    for file in local_files:
        print(f"  - {file['path']} ({file['type']}, {file['size']} bytes)")
    
    # Update a file in git storage with explicit commit message
    print("\n6. Updating a file in git storage with custom commit message:")
    updated_code = code_content + "\n# Added a comment\n"
    file_manager.write_text("hello.py", updated_code, file_type="code", 
                          metadata={"commit_message": "Add comment to hello.py"})
    print("  - File updated successfully")
    
    # Get file history (git-specific feature)
    print("\n7. Getting file history from git:")
    history = file_manager.get_file_history("hello.py")
    for entry in history:
        print(f"  - {entry['timestamp']}: {entry['message']} ({entry['author']})")
    
    # Change storage preference for a file type
    print("\n8. Changing storage preference for 'code' files to local:")
    file_manager.set_storage_preference("code", "local")
    print("  - Preference updated")
    
    # Create another code file (should now go to local)
    print("\n9. Creating another code file after preference change (should use local):")
    file_manager.write_text("another.py", "# This should go to local now", file_type="code")
    print("  - File created successfully")
    
    # Verify that the file went to local storage
    print("\n10. Verifying the new file exists in local storage:")
    exists_in_local = file_manager.file_exists("another.py", storage_type="local")
    exists_in_git = file_manager.file_exists("another.py", storage_type="git")
    print(f"  - Exists in local: {exists_in_local}")
    print(f"  - Exists in git: {exists_in_git}")
    
    # Demonstrate reading files
    print("\n11. Reading files from different storages:")
    hello_content = file_manager.read_text("hello.py", file_type="code")
    temp_content = file_manager.read_text("temp_data.txt", file_type="temp")
    print(f"  - Content from git: {hello_content.splitlines()[0]}...")
    print(f"  - Content from local: {temp_content}")
    
    # Create directories in different storages
    print("\n12. Creating directories in different storages:")
    file_manager.create_directory("docs/api", storage_type="git")
    file_manager.create_directory("temp/cache", storage_type="local")
    print("  - Directories created successfully")
    
    # Clean up (optional, uncomment to test deletion)
    """
    print("\n13. Cleaning up files:")
    file_manager.delete_file("hello.py", file_type="code", 
                            metadata={"commit_message": "Remove hello.py"})
    file_manager.delete_file("another.py", storage_type="local")
    file_manager.delete_file("temp_data.txt", storage_type="local")
    print("  - Files deleted successfully")
    """
    
    print("\nDemo completed!")

if __name__ == "__main__":
    main()