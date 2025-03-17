"""
Unit tests for the Metadata Extractor Tool.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path

from src.tools.metadata_extractor import MetadataExtractorTool

class TestMetadataExtractorTool(unittest.TestCase):
    """Test cases for the Metadata Extractor Tool."""
    
    def setUp(self):
        """Set up test environment before each test method."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Initialize the tool with a test cache path
        self.cache_dir = self.test_dir / "cache"
        self.extractor = MetadataExtractorTool(
            base_path=str(self.cache_dir),
            enable_summarization=True
        )
        
        # Create test files
        self._create_test_files()
        
    def tearDown(self):
        """Clean up after each test method."""
        self.temp_dir.cleanup()
        
    def _create_test_files(self):
        """Create various test files for metadata extraction."""
        # Text file
        self.text_file = self.test_dir / "test.txt"
        with open(self.text_file, "w") as f:
            f.write("This is a test file.\nIt has multiple lines.\nUsed for testing metadata extraction.")
        
        # JSON file
        self.json_file = self.test_dir / "test.json"
        test_data = {
            "name": "Test JSON",
            "version": 1.0,
            "items": [
                {"id": 1, "value": "one"},
                {"id": 2, "value": "two"}
            ]
        }
        with open(self.json_file, "w") as f:
            json.dump(test_data, f)
        
        # CSV file
        self.csv_file = self.test_dir / "test.csv"
        with open(self.csv_file, "w") as f:
            f.write("id,name,value\n")
            f.write("1,Test A,100\n")
            f.write("2,Test B,200\n")
            
        # Create a nested directory structure
        self.nested_dir = self.test_dir / "nested"
        self.nested_dir.mkdir()
        
        self.nested_file = self.nested_dir / "nested.txt"
        with open(self.nested_file, "w") as f:
            f.write("This is a nested test file.")
    
    def test_detect_file_type(self):
        """Test file type detection functionality."""
        # Test text file detection
        text_info = self.extractor.detect_file_type(str(self.text_file))
        self.assertEqual(text_info["detected_type"], "text")
        self.assertEqual(text_info["extension"], ".txt")
        self.assertTrue(text_info["detection_confidence"] > 0.5)
        
        # Test JSON file detection
        json_info = self.extractor.detect_file_type(str(self.json_file))
        self.assertEqual(json_info["detected_type"], "json")
        self.assertEqual(json_info["extension"], ".json")
        
        # Test CSV file detection
        csv_info = self.extractor.detect_file_type(str(self.csv_file))
        self.assertEqual(csv_info["detected_type"], "csv")
        self.assertEqual(csv_info["extension"], ".csv")
    
    def test_extract_text_metadata(self):
        """Test text file metadata extraction."""
        metadata = self.extractor.extract_metadata(str(self.text_file))
        
        # Basic file info
        self.assertEqual(metadata["file_name"], "test.txt")
        self.assertEqual(metadata["file_type"], "text")
        self.assertTrue(metadata["size_bytes"] > 0)
        
        # Content-specific metadata
        self.assertIn("character_count", metadata["content_type_specific"])
        self.assertIn("line_count", metadata["content_type_specific"])
        self.assertIn("word_count", metadata["content_type_specific"])
        
        # Line count validation
        self.assertEqual(metadata["content_type_specific"]["line_count"], 3)
        
        # Ensure hash is calculated
        self.assertIsNotNone(metadata["hash"])
        self.assertTrue(len(metadata["hash"]) > 0)
    
    def test_extract_json_metadata(self):
        """Test JSON file metadata extraction."""
        metadata = self.extractor.extract_metadata(str(self.json_file))
        
        # Basic file info
        self.assertEqual(metadata["file_name"], "test.json")
        self.assertEqual(metadata["file_type"], "json")
        
        # Content-specific metadata
        self.assertEqual(metadata["content_type_specific"]["format"], "JSON")
        self.assertEqual(metadata["content_type_specific"]["root_type"], "object")
        
        # Key count validation
        self.assertEqual(metadata["content_type_specific"]["keys_count"], 3)
        
        # Top level keys validation
        keys = metadata["content_type_specific"]["top_level_keys"]
        self.assertIn("name", keys)
        self.assertIn("version", keys)
        self.assertIn("items", keys)
    
    def test_extract_csv_metadata(self):
        """Test CSV file metadata extraction."""
        metadata = self.extractor.extract_metadata(str(self.csv_file))
        
        # Basic file info
        self.assertEqual(metadata["file_name"], "test.csv")
        self.assertEqual(metadata["file_type"], "csv")
        
        # Content-specific metadata
        self.assertEqual(metadata["content_type_specific"]["format"], "CSV")
        self.assertEqual(metadata["content_type_specific"]["delimiter"], ",")
        
        # Structure validation
        self.assertEqual(metadata["content_type_specific"]["row_count"], 3)  # Header + 2 data rows
        self.assertEqual(metadata["content_type_specific"]["column_count"], 3)
        
        # Column validation
        columns = metadata["content_type_specific"]["columns"]
        self.assertEqual(len(columns), 3)
        self.assertIn("id", columns)
        self.assertIn("name", columns)
        self.assertIn("value", columns)
    
    def test_batch_extraction(self):
        """Test batch metadata extraction."""
        files = [str(self.text_file), str(self.json_file), str(self.csv_file)]
        results = self.extractor.batch_extract_metadata(files)
        
        # Check all files were processed
        self.assertEqual(len(results), 3)
        
        # Check each file has metadata
        for file_path in files:
            self.assertIn(file_path, results)
            self.assertIn("file_type", results[file_path])
            self.assertIn("size_bytes", results[file_path])
            self.assertIn("hash", results[file_path])
    
    def test_directory_extraction(self):
        """Test directory metadata extraction."""
        # Test with recursion enabled
        results = self.extractor.extract_metadata_from_directory(
            str(self.test_dir), 
            recursive=True
        )
        
        # Should find all files including nested
        self.assertEqual(len(results), 4)
        self.assertIn(str(self.nested_file), results)
        
        # Test with recursion disabled
        results_no_recursion = self.extractor.extract_metadata_from_directory(
            str(self.test_dir), 
            recursive=False
        )
        
        # Should only find top-level files
        self.assertEqual(len(results_no_recursion), 3)
        self.assertNotIn(str(self.nested_file), results_no_recursion)
        
        # Test with pattern filter
        results_filtered = self.extractor.extract_metadata_from_directory(
            str(self.test_dir),
            recursive=True,
            file_pattern=r"\.txt$"  # Only .txt files
        )
        
        # Should only find .txt files
        self.assertEqual(len(results_filtered), 2)
        for file_path in results_filtered:
            self.assertTrue(file_path.endswith(".txt"))
    
    def test_metadata_caching(self):
        """Test metadata caching and retrieval."""
        # Extract metadata
        metadata = self.extractor.extract_metadata(str(self.text_file))
        
        # Cache the metadata
        result = self.extractor.cache_metadata(str(self.text_file), metadata)
        self.assertTrue(result)
        
        # Verify cache directory was created
        self.assertTrue(self.cache_dir.exists())
        
        # Retrieve from cache
        cached = self.extractor.get_cached_metadata(str(self.text_file))
        
        # Verify retrieved metadata matches original
        self.assertIsNotNone(cached)
        self.assertEqual(cached["file_name"], metadata["file_name"])
        self.assertEqual(cached["hash"], metadata["hash"])
        self.assertEqual(cached["file_type"], metadata["file_type"])
        
        # Test cache with max age constraint
        old_cached = self.extractor.get_cached_metadata(str(self.text_file), max_age_days=0)
        self.assertIsNone(old_cached)  # Should be None since we're requiring a 0-day max age
    
    def test_metadata_reports(self):
        """Test metadata report generation."""
        metadata = self.extractor.extract_metadata(str(self.text_file))
        
        # Test JSON format
        json_report = self.extractor.generate_metadata_report(metadata, format="json")
        self.assertTrue(json_report.startswith("{"))
        self.assertTrue(json_report.endswith("}"))
        
        # Verify JSON report can be parsed back to dict
        parsed = json.loads(json_report)
        self.assertEqual(parsed["file_name"], metadata["file_name"])
        
        # Test markdown format
        md_report = self.extractor.generate_metadata_report(metadata, format="markdown")
        self.assertTrue(md_report.startswith("# Metadata Report"))
        self.assertIn("## Basic Information", md_report)
        
        # Test text format
        text_report = self.extractor.generate_metadata_report(metadata, format="text")
        self.assertTrue("Metadata Report:" in text_report)
        self.assertTrue("Basic Information:" in text_report)
    
    def test_empty_file(self):
        """Test handling of empty files."""
        # Create an empty file
        empty_file = self.test_dir / "empty.txt"
        open(empty_file, "w").close()
        
        # Extract metadata
        metadata = self.extractor.extract_metadata(str(empty_file))
        
        # Basic checks
        self.assertEqual(metadata["file_name"], "empty.txt")
        self.assertEqual(metadata["size_bytes"], 0)
        self.assertIsNotNone(metadata["hash"])  # Should have a hash value even for empty file
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent files."""
        nonexistent = self.test_dir / "nonexistent.txt"
        
        # Should not raise an exception but return limited metadata
        metadata = self.extractor.extract_metadata(str(nonexistent))
        
        self.assertEqual(metadata["file_name"], "nonexistent.txt")
        self.assertEqual(metadata["size_bytes"], 0)
        self.assertIsNone(metadata["hash"])
        self.assertEqual(metadata["content_type_specific"], {})
    
    def test_invalid_cache_retrieval(self):
        """Test retrieval from cache with invalid inputs."""
        # Nonexistent file
        cached = self.extractor.get_cached_metadata("nonexistent_file.txt")
        self.assertIsNone(cached)
        
        # Invalid max_age
        metadata = self.extractor.extract_metadata(str(self.text_file))
        self.extractor.cache_metadata(str(self.text_file), metadata)
        
        cached = self.extractor.get_cached_metadata(str(self.text_file), max_age_days=-1)
        self.assertIsNotNone(cached)  # Negative max_age should be ignored

if __name__ == "__main__":
    unittest.main()