#!/usr/bin/env python3
"""
Example usage of the FileManagerTool with Google Drive integration.
This example demonstrates how to:
1. Load configuration from a file
2. Work with files in Google Drive
3. Configure storage preferences for different file types
4. Synchronize files between different storage backends
"""

import os
import sys
import argparse
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the file manager
from src.tools.file_manager import FileManagerTool

def setup_credentials():
    """Create credentials directory if it doesn't exist."""
    credentials_dir = os.path.join(os.path.dirname(__file__), '..', 'credentials')
    os.makedirs(credentials_dir, exist_ok=True)
    
    # Check for Google Drive credentials
    google_drive_creds = os.path.join(credentials_dir, 'google_drive_credentials.json')
    if not os.path.exists(google_drive_creds):
        print(f"Google Drive credentials file not found: {google_drive_creds}")
        print("To use Google Drive, you need to:")
        print("1. Go to the Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a project and enable the Google Drive API")
        print("3. Create OAuth credentials (Desktop client)")
        print("4. Download the credentials JSON file")
        print(f"5. Save it as {google_drive_creds}")
        print("\nNote: Google Drive features will be unavailable in this example")

def demonstrate_basic_operations(file_manager, storage_type=None):
    """Demonstrate basic file operations."""
    print(f"\n--- Basic File Operations {'with ' + storage_type if storage_type else ''} ---")
    
    # Create a test file
    test_content = f"Test file created at {datetime.now().isoformat()}"
    test_file = "test/example.txt"
    
    # Write the file
    success = file_manager.write_text_file(
        test_file,
        test_content,
        storage_type=storage_type
    )
    print(f"Write file: {'Success' if success else 'Failed'}")
    
    # Read the file
    content = file_manager.read_text_file(test_file, storage_type=storage_type)
    print(f"Read file: {content}")
    
    # List files
    files = file_manager.list_files("test", storage_type=storage_type)
    print(f"Files in directory: {[f['name'] for f in files]}")
    
    # Get file info
    file_info = file_manager.get_file_info(test_file, storage_type=storage_type)
    print(f"File info: {file_info}")
    
    # Add tags to the file
    file_manager.add_tags(test_file, ["example", "test"], storage_type=storage_type)
    print(f"Tags added: {file_manager.get_tags(test_file, storage_type=storage_type)}")
    
    # Rename the file
    new_path = "test/renamed_example.txt"
    success = file_manager.rename_file(test_file, new_path, storage_type=storage_type)
    print(f"Rename file: {'Success' if success else 'Failed'}")
    
    # Delete the file
    success = file_manager.delete_file(new_path, storage_type=storage_type)
    print(f"Delete file: {'Success' if success else 'Failed'}")

def demonstrate_file_sync(file_manager):
    """Demonstrate file synchronization between backends."""
    print("\n--- File Synchronization Between Backends ---")
    
    # Create a test file in the local storage
    test_content = f"Sync test file created at {datetime.now().isoformat()}"
    test_file = "sync_test/sync_example.txt"
    
    # Write to local storage
    file_manager.write_text_file(test_file, test_content, storage_type="local")
    print(f"File created in local storage: {test_file}")
    
    # Sync to Git storage
    success = file_manager.sync_file(
        test_file, 
        source_storage_type="local",
        target_storage_type="git",
        sync_tags=True,
        metadata={"commit_message": "Synced file from local storage"}
    )
    print(f"Sync to Git: {'Success' if success else 'Failed'}")
    
    # Check if file exists in Git
    exists = file_manager.file_exists(test_file, storage_type="git")
    print(f"File exists in Git: {exists}")
    
    # Try to sync to Google Drive if enabled
    google_drive_config = file_manager.config["backends"]["google_drive"]
    if google_drive_config["enabled"] and file_manager.storage_backends["google_drive"].authenticated:
        success = file_manager.sync_file(
            test_file, 
            source_storage_type="local",
            target_storage_type="google_drive"
        )
        print(f"Sync to Google Drive: {'Success' if success else 'Failed'}")
        
        # Check if file exists in Google Drive
        exists = file_manager.file_exists(test_file, storage_type="google_drive")
        print(f"File exists in Google Drive: {exists}")
    else:
        print("Google Drive sync skipped - not configured or not authenticated")
    
    # Clean up - delete from all storages
    file_manager.delete_file(test_file, storage_type="local")
    file_manager.delete_file(test_file, storage_type="git")
    
    if google_drive_config["enabled"] and file_manager.storage_backends["google_drive"].authenticated:
        file_manager.delete_file(test_file, storage_type="google_drive")

def demonstrate_storage_preferences(file_manager):
    """Demonstrate storage preferences based on file types."""
    print("\n--- Storage Preferences Based on File Types ---")
    
    # Show current preferences
    print("Current storage preferences:")
    for file_type, storage in file_manager.storage_preferences.items():
        print(f"  {file_type}: {storage}")
    
    # Create different file types and see where they get stored
    file_types = {
        "code": "test_code.py",
        "document": "test_doc.md",
        "image": "test_image.png",
        "general": "test_general.dat"
    }
    
    for file_type, filename in file_types.items():
        path = f"preferences_test/{filename}"
        content = f"Example {file_type} file"
        
        # Write using file type preference
        file_manager.write_text_file(path, content, file_type=file_type)
        
        # Check where it was stored
        for storage_name in file_manager.storage_backends:
            if not file_manager.storage_backends[storage_name]:
                continue
            exists = file_manager.file_exists(path, storage_type=storage_name)
            if exists:
                print(f"{file_type} file was stored in {storage_name}")
                # Clean up
                file_manager.delete_file(path, storage_type=storage_name)

def main():
    parser = argparse.ArgumentParser(description="File Manager Example")
    parser.add_argument("--storage", choices=["local", "git", "google_drive", "onedrive"],
                      help="Specify a storage backend to test")
    args = parser.parse_args()
    
    # Setup credentials directory
    setup_credentials()
    
    # Get the config path
    config_path = os.path.join(os.path.dirname(__file__), 'file_manager_config.json')
    
    # Initialize the file manager with the config
    print(f"Initializing FileManagerTool with config from: {config_path}")
    file_manager = FileManagerTool(config_path=config_path)
    
    # Display the active backends
    print("\nActive storage backends:")
    for backend_name, backend in file_manager.storage_backends.items():
        if backend:
            status = "Ready"
            if backend_name in ["google_drive", "onedrive"] and hasattr(backend, 'authenticated'):
                status = "Authenticated" if backend.authenticated else "Not authenticated"
            print(f"  {backend_name}: {status}")
        else:
            print(f"  {backend_name}: Disabled")
    
    if args.storage:
        # Run basic operations on the specified storage
        if not file_manager.storage_backends.get(args.storage):
            print(f"Error: {args.storage} storage is not available")
            return
        
        if args.storage in ["google_drive", "onedrive"]:
            backend = file_manager.storage_backends[args.storage]
            if hasattr(backend, 'authenticated') and not backend.authenticated:
                print(f"Error: {args.storage} is not authenticated")
                return
                
        demonstrate_basic_operations(file_manager, args.storage)
    else:
        # Run the full demo
        # Basic operations on local storage
        demonstrate_basic_operations(file_manager, "local")
        
        # File synchronization demonstration
        demonstrate_file_sync(file_manager)
        
        # Storage preferences demonstration
        demonstrate_storage_preferences(file_manager)
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main()