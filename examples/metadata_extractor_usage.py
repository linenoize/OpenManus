#!/usr/bin/env python3
"""
Example script demonstrating the usage of the Metadata Extractor Tool.

This script shows various ways to extract and analyze metadata from different file types.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Metadata Extractor Tool
from src.tools.metadata_extractor import MetadataExtractorTool

def main():
    """Main function demonstrating Metadata Extractor Tool usage."""
    print("Metadata Extractor Tool Usage Example")
    print("=" * 50)
    
    # Initialize the tool
    print("\nInitializing Metadata Extractor Tool...")
    extractor = MetadataExtractorTool(
        base_path="data/metadata_cache",
        enable_summarization=True  # Enable basic content summarization
    )
    
    # Create example files for testing if they don't exist
    examples_dir = Path("examples/sample_files")
    examples_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample text file
    text_file_path = examples_dir / "sample.txt"
    if not text_file_path.exists():
        with open(text_file_path, "w") as f:
            f.write("This is a sample text file.\nIt contains multiple lines.\nUsed for testing metadata extraction.")
    
    # Create sample JSON file
    json_file_path = examples_dir / "sample.json"
    if not json_file_path.exists():
        sample_data = {
            "name": "Sample JSON",
            "version": 1.0,
            "items": [
                {"id": 1, "value": "first"},
                {"id": 2, "value": "second"},
                {"id": 3, "value": "third"}
            ],
            "metadata": {
                "created": "2025-03-17",
                "author": "OpenManus"
            }
        }
        with open(json_file_path, "w") as f:
            json.dump(sample_data, f, indent=2)
    
    # Create sample CSV file
    csv_file_path = examples_dir / "sample.csv"
    if not csv_file_path.exists():
        with open(csv_file_path, "w") as f:
            f.write("id,name,value,date\n")
            f.write("1,Item 1,100,2025-01-01\n")
            f.write("2,Item 2,200,2025-01-02\n")
            f.write("3,Item 3,300,2025-01-03\n")
    
    # Basic file type detection
    print("\n1. File Type Detection")
    print("-" * 50)
    for file_path in [text_file_path, json_file_path, csv_file_path]:
        file_info = extractor.detect_file_type(str(file_path))
        print(f"\nFile: {file_path.name}")
        print(f"  Detected Type: {file_info['detected_type']}")
        print(f"  MIME Type: {file_info['mimetype']}")
        print(f"  Confidence: {file_info['detection_confidence']}")
    
    # Extract metadata from individual files
    print("\n\n2. Metadata Extraction (Individual Files)")
    print("-" * 50)
    
    # Text file metadata
    text_metadata = extractor.extract_metadata(str(text_file_path))
    print(f"\nText File Metadata: {text_file_path.name}")
    print(f"  Size: {text_metadata['size_bytes']} bytes")
    print(f"  File Type: {text_metadata['file_type']}")
    print(f"  Content Type: {text_metadata['content_type_specific'].get('format', 'Unknown')}")
    
    if 'character_count' in text_metadata['content_type_specific']:
        print(f"  Characters: {text_metadata['content_type_specific']['character_count']}")
        print(f"  Lines: {text_metadata['content_type_specific']['line_count']}")
        print(f"  Words: {text_metadata['content_type_specific']['word_count']}")
    
    if 'summary' in text_metadata:
        print(f"  Summary: {text_metadata['summary']}")
    
    # JSON file metadata
    json_metadata = extractor.extract_metadata(str(json_file_path))
    print(f"\nJSON File Metadata: {json_file_path.name}")
    print(f"  Size: {json_metadata['size_bytes']} bytes")
    print(f"  File Type: {json_metadata['file_type']}")
    
    if 'root_type' in json_metadata['content_type_specific']:
        print(f"  Root Type: {json_metadata['content_type_specific']['root_type']}")
        
        if json_metadata['content_type_specific']['root_type'] == 'object':
            print(f"  Keys: {', '.join(json_metadata['content_type_specific'].get('top_level_keys', []))[:100]}...")
    
    # CSV file metadata
    csv_metadata = extractor.extract_metadata(str(csv_file_path))
    print(f"\nCSV File Metadata: {csv_file_path.name}")
    print(f"  Size: {csv_metadata['size_bytes']} bytes")
    print(f"  File Type: {csv_metadata['file_type']}")
    
    if 'delimiter' in csv_metadata['content_type_specific']:
        print(f"  Delimiter: '{csv_metadata['content_type_specific']['delimiter']}'")
        print(f"  Rows: {csv_metadata['content_type_specific']['row_count']}")
        print(f"  Columns: {csv_metadata['content_type_specific']['column_count']}")
        print(f"  Headers: {', '.join(csv_metadata['content_type_specific'].get('columns', []))}")
    
    # Batch metadata extraction
    print("\n\n3. Batch Metadata Extraction")
    print("-" * 50)
    batch_files = [str(text_file_path), str(json_file_path), str(csv_file_path)]
    batch_results = extractor.batch_extract_metadata(batch_files)
    
    print(f"\nProcessed {len(batch_results)} files:")
    for file_path, metadata in batch_results.items():
        print(f"  - {Path(file_path).name}: {metadata['file_type']} ({metadata['size_bytes']} bytes)")
    
    # Directory metadata extraction
    print("\n\n4. Directory Metadata Extraction")
    print("-" * 50)
    dir_results = extractor.extract_metadata_from_directory(str(examples_dir), recursive=True)
    
    print(f"\nProcessed directory with {len(dir_results)} files:")
    for file_path, metadata in dir_results.items():
        print(f"  - {Path(file_path).name}: {metadata['file_type']}")
    
    # Generate formatted reports
    print("\n\n5. Metadata Reports")
    print("-" * 50)
    
    # JSON report
    print("\nJSON Report (sample):")
    json_report = extractor.generate_metadata_report(text_metadata, format="json")
    print(json_report[:200] + "... (truncated)")
    
    # Markdown report
    print("\nMarkdown Report (sample):")
    md_report = extractor.generate_metadata_report(json_metadata, format="markdown")
    print("\n".join(md_report.split("\n")[:10]) + "\n... (truncated)")
    
    # Text report
    print("\nText Report (sample):")
    text_report = extractor.generate_metadata_report(csv_metadata, format="text")
    print("\n".join(text_report.split("\n")[:10]) + "\n... (truncated)")
    
    # Caching demonstration
    print("\n\n6. Metadata Caching")
    print("-" * 50)
    
    # Cache the metadata
    print("\nCaching metadata...")
    extractor.cache_metadata(str(text_file_path), text_metadata)
    
    # Retrieve from cache
    print("Retrieving metadata from cache...")
    cached_metadata = extractor.get_cached_metadata(str(text_file_path))
    
    if cached_metadata:
        print("Successfully retrieved metadata from cache!")
        print(f"  File: {cached_metadata['file_name']}")
        print(f"  Hash: {cached_metadata['hash'][:16]}...")
    else:
        print("Failed to retrieve metadata from cache.")

if __name__ == "__main__":
    main()