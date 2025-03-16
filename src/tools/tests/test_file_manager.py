import unittest
import os
import tempfile
import shutil
from pathlib import Path
from src.tools.file_manager import FileManagerTool, LocalStorageBackend, GitStorageBackend

class TestLocalStorageBackend(unittest.TestCase):
    """Tests for the LocalStorageBackend class."""
    
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.storage = LocalStorageBackend(self.test_dir)
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_write_read_file(self):
        # Test writing and reading a file
        content = b"Test content"
        path = "test_file.txt"
        
        # Write the file
        result = self.storage.write_file(path, content)
        self.assertTrue(result)
        
        # Check that the file exists
        full_path = os.path.join(self.test_dir, path)
        self.assertTrue(os.path.exists(full_path))
        
        # Read the file
        read_content = self.storage.read_file(path)
        self.assertEqual(read_content, content)
    
    def test_list_files(self):
        # Test listing files
        # Create some files
        self.storage.write_file("file1.txt", b"Content 1")
        self.storage.write_file("file2.txt", b"Content 2")
        self.storage.create_directory("subdir")
        self.storage.write_file("subdir/file3.txt", b"Content 3")
        
        # List files in root directory
        files = self.storage.list_files()
        self.assertEqual(len(files), 3)
        
        # Check that the files have the expected properties
        file_names = [f["name"] for f in files]
        self.assertIn("file1.txt", file_names)
        self.assertIn("file2.txt", file_names)
        self.assertIn("subdir", file_names)
        
        # List files in subdirectory
        subdir_files = self.storage.list_files("subdir")
        self.assertEqual(len(subdir_files), 1)
        self.assertEqual(subdir_files[0]["name"], "file3.txt")
    
    def test_delete_file(self):
        # Test deleting a file
        path = "to_delete.txt"
        self.storage.write_file(path, b"Delete me")
        
        # Check that the file exists
        self.assertTrue(self.storage.file_exists(path))
        
        # Delete the file
        result = self.storage.delete_file(path)
        self.assertTrue(result)
        
        # Check that the file no longer exists
        self.assertFalse(self.storage.file_exists(path))
    
    def test_rename_file(self):
        # Test renaming a file
        old_path = "original.txt"
        new_path = "renamed.txt"
        content = b"Test content"
        
        # Create a file
        self.storage.write_file(old_path, content)
        
        # Rename the file
        result = self.storage.rename_file(old_path, new_path)
        self.assertTrue(result)
        
        # Check that the old file no longer exists
        self.assertFalse(self.storage.file_exists(old_path))
        
        # Check that the new file exists and has the same content
        self.assertTrue(self.storage.file_exists(new_path))
        read_content = self.storage.read_file(new_path)
        self.assertEqual(read_content, content)
    
    def test_create_directory(self):
        # Test creating a directory
        path = "new_dir/nested_dir"
        
        # Create directory
        result = self.storage.create_directory(path)
        self.assertTrue(result)
        
        # Check that the directory exists
        full_path = os.path.join(self.test_dir, path)
        self.assertTrue(os.path.isdir(full_path))


class TestGitStorageBackend(unittest.TestCase):
    """Tests for the GitStorageBackend class."""
    
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.storage = GitStorageBackend(self.test_dir)
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_write_read_file(self):
        # Test writing and reading a file with commit
        content = b"Test content for git"
        path = "test_git_file.txt"
        commit_message = "Test commit"
        
        # Write the file with a commit message
        result = self.storage.write_file(path, content, commit_message)
        self.assertTrue(result)
        
        # Check that the file exists
        full_path = os.path.join(self.test_dir, path)
        self.assertTrue(os.path.exists(full_path))
        
        # Read the file
        read_content = self.storage.read_file(path)
        self.assertEqual(read_content, content)
        
        # Check that the commit was made
        history = self.storage.get_file_history(path)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[0]["message"], commit_message)
    
    def test_file_history(self):
        # Test file history tracking
        path = "history_test.txt"
        
        # Make multiple updates to the file
        self.storage.write_file(path, b"Version 1", "Initial version")
        self.storage.write_file(path, b"Version 2", "Update to version 2")
        self.storage.write_file(path, b"Version 3", "Update to version 3")
        
        # Get file history
        history = self.storage.get_file_history(path)
        
        # Check that we have the expected number of history entries
        self.assertEqual(len(history), 3)
        
        # Check that the history entries have the expected messages in reverse order
        self.assertEqual(history[0]["message"], "Update to version 3")
        self.assertEqual(history[1]["message"], "Update to version 2")
        self.assertEqual(history[2]["message"], "Initial version")


class TestFileManagerTool(unittest.TestCase):
    """Tests for the FileManagerTool class."""
    
    def setUp(self):
        # Create a FileManagerTool instance with custom paths for testing
        self.test_local_dir = tempfile.mkdtemp()
        self.test_git_dir = tempfile.mkdtemp()
        
        self.file_manager = FileManagerTool()
        
        # Replace the storage backends with ones that use our test directories
        self.file_manager.storage_backends["local"] = LocalStorageBackend(self.test_local_dir)
        self.file_manager.storage_backends["git"] = GitStorageBackend(self.test_git_dir)
        
    def tearDown(self):
        # Clean up the temporary directories
        shutil.rmtree(self.test_local_dir)
        shutil.rmtree(self.test_git_dir)
    
    def test_storage_preference_selection(self):
        # Test that the correct storage is selected based on preferences
        
        # Create test files in each storage
        self.file_manager.write_file("local_file.txt", "Local content", storage_type="local")
        self.file_manager.write_file("git_file.txt", "Git content", storage_type="git")
        
        # Test with explicit storage type
        local_content = self.file_manager.read_text("local_file.txt", storage_type="local")
        git_content = self.file_manager.read_text("git_file.txt", storage_type="git")
        
        self.assertEqual(local_content, "Local content")
        self.assertEqual(git_content, "Git content")
        
        # Test with file type preferences
        self.file_manager.write_file("code_file.py", "Code content", file_type="code")
        self.file_manager.write_file("temp_file.tmp", "Temp content", file_type="temp")
        
        # By default, "code" files go to git and "temp" files go to local
        # Check that the files were written to the correct storage
        self.assertTrue(self.file_manager.file_exists("code_file.py", storage_type="git"))
        self.assertTrue(self.file_manager.file_exists("temp_file.tmp", storage_type="local"))
        
        # Test changing preferences
        # Change preference for "code" files to local
        self.file_manager.set_storage_preference("code", "local")
        
        # Write a new code file and check that it goes to local
        self.file_manager.write_file("another_code_file.py", "More code", file_type="code")
        self.assertTrue(self.file_manager.file_exists("another_code_file.py", storage_type="local"))
    
    def test_text_file_operations(self):
        # Test text file operations
        path = "text_file.txt"
        content = "Hello, world!"
        
        # Write a text file
        result = self.file_manager.write_text(path, content)
        self.assertTrue(result)
        
        # Read the text file
        read_content = self.file_manager.read_text(path)
        self.assertEqual(read_content, content)
        
        # Update the text file
        new_content = "Updated content"
        self.file_manager.write_text(path, new_content)
        
        # Read the updated content
        read_content = self.file_manager.read_text(path)
        self.assertEqual(read_content, new_content)
    
    def test_file_operations_with_metadata(self):
        # Test file operations with metadata (only works with git storage)
        path = "metadata_file.txt"
        content = "File with metadata"
        commit_message = "Custom commit message"
        
        # Write a file with custom commit message
        result = self.file_manager.write_text(
            path, content, 
            storage_type="git", 
            metadata={"commit_message": commit_message}
        )
        self.assertTrue(result)
        
        # Check that the file was committed with the custom message
        history = self.file_manager.get_file_history(path)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[0]["message"], commit_message)


if __name__ == '__main__':
    unittest.main()