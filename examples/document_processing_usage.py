#!/usr/bin/env python3
"""
Example script demonstrating the usage of the Document Processing Tool.

This script shows various ways to process and analyze documents in different formats.
"""

import os
import sys
import json
from pathlib import Path
import tempfile

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Document Processing Tool
from src.tools.document_processing import DocumentProcessingTool

def main():
    """Main function demonstrating Document Processing Tool usage."""
    print("Document Processing Tool Usage Example")
    print("=" * 50)
    
    # Initialize the tool
    print("\nInitializing Document Processing Tool...")
    doc_processor = DocumentProcessingTool(
        cache_dir="data/document_cache",
        enable_ocr=False  # Set to True if you have OCR dependencies installed
    )
    
    # Create example files for testing if they don't exist
    examples_dir = Path("examples/sample_files")
    examples_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample text file
    text_file_path = examples_dir / "sample_document.txt"
    if not text_file_path.exists():
        with open(text_file_path, "w") as f:
            f.write("# Sample Document\n\n")
            f.write("This is a sample document used for testing the Document Processing Tool.\n\n")
            f.write("## Features\n\n")
            f.write("- Metadata extraction\n")
            f.write("- Text extraction\n")
            f.write("- Document conversion\n")
            f.write("- Structured data extraction\n\n")
            f.write("The tool supports various document formats like PDF, DOCX, and plain text.\n")
    
    # Create CSV file for structured data extraction demo
    csv_file_path = examples_dir / "sample_data.csv"
    if not csv_file_path.exists():
        with open(csv_file_path, "w") as f:
            f.write("id,name,value,date\n")
            f.write("1,Item 1,100,2025-01-01\n")
            f.write("2,Item 2,200,2025-01-02\n")
            f.write("3,Item 3,300,2025-01-03\n")
    
    # Basic document loading and analysis
    print("\n1. Document Loading and Analysis")
    print("-" * 50)
    
    # Load and analyze the text document
    print(f"\nLoading document: {text_file_path}")
    doc_data = doc_processor.load_document(str(text_file_path))
    
    if "error" in doc_data:
        print(f"Error: {doc_data['error']}")
    else:
        print(f"Document Type: {doc_data.get('document_type', 'Unknown')}")
        print(f"Document Size: {doc_data.get('file_size', 0)} bytes")
        
        # Display document structure
        if "line_count" in doc_data:
            print(f"Line Count: {doc_data['line_count']}")
            print(f"Word Count: {doc_data['word_count']}")
            
        if "content" in doc_data:
            content_sample = doc_data["content"][:100] + "..." if len(doc_data["content"]) > 100 else doc_data["content"]
            print(f"Content Sample: {content_sample}")
    
    # Extract metadata from documents
    print("\n\n2. Metadata Extraction")
    print("-" * 50)
    
    print(f"\nExtracting metadata from: {text_file_path}")
    metadata = doc_processor.extract_metadata(str(text_file_path))
    
    if "error" in metadata:
        print(f"Error: {metadata['error']}")
    else:
        print("Metadata:")
        for key, value in metadata.items():
            if key not in ["file_path"]:  # Skip long fields
                print(f"  {key}: {value}")
    
    # Text extraction
    print("\n\n3. Text Extraction")
    print("-" * 50)
    
    print(f"\nExtracting text from: {text_file_path}")
    text = doc_processor.extract_text(str(text_file_path))
    
    if text.startswith("Error:"):
        print(text)
    else:
        print("Extracted Text (first 200 chars):")
        print(text[:200] + "..." if len(text) > 200 else text)
    
    # Document conversion
    print("\n\n4. Document Conversion")
    print("-" * 50)
    
    # Convert text to another format
    output_dir = examples_dir / "converted"
    output_dir.mkdir(exist_ok=True)
    
    docx_output = output_dir / "converted_document.docx"
    
    print(f"\nConverting {text_file_path} to DOCX format")
    result = doc_processor.convert_document(
        str(text_file_path),
        "docx",
        str(docx_output)
    )
    
    if "error" in result:
        print(f"Conversion Error: {result['error']}")
    else:
        print(f"Conversion successful: {result.get('conversion')}")
        print(f"Output file: {result.get('output_path')}")
    
    # Structured data extraction
    print("\n\n5. Structured Data Extraction")
    print("-" * 50)
    
    print(f"\nExtracting structured data from: {csv_file_path}")
    structured_data = doc_processor.extract_structured_data(str(csv_file_path))
    
    if "error" in structured_data:
        print(f"Error: {structured_data['error']}")
    else:
        print(f"Document Type: {structured_data.get('document_type', 'Unknown')}")
        
        # Show detected format
        if "format" in structured_data:
            print(f"Detected Format: {structured_data.get('format')}")
            
        # Show detected tables
        if structured_data.get("tables"):
            print(f"Found {len(structured_data['tables'])} tables")
            for i, table in enumerate(structured_data["tables"]):
                print(f"  Table {i+1}: {table.get('rows', 0)} rows, Format: {table.get('format', 'Unknown')}")
        
        # Show detected fields
        if structured_data.get("fields"):
            print(f"Found {len(structured_data['fields'])} fields/form elements")
            for key, value in list(structured_data["fields"].items())[:3]:  # Show first 3 fields
                print(f"  {key}: {value}")
            
            if len(structured_data["fields"]) > 3:
                print(f"  ... and {len(structured_data['fields']) - 3} more fields")
    
    # Document searching
    print("\n\n6. Document Searching")
    print("-" * 50)
    
    search_term = "document"
    print(f"\nSearching for '{search_term}' in {text_file_path}")
    
    search_results = doc_processor.search_in_document(
        str(text_file_path),
        search_term,
        context_size=1
    )
    
    if "error" in search_results:
        print(f"Search Error: {search_results['error']}")
    else:
        print(f"Found {search_results.get('match_count', 0)} matches")
        
        for i, match in enumerate(search_results.get("matches", [])[:2]):  # Show first 2 matches
            print(f"\nMatch {i+1}:")
            print(f"  {match.get('match', '')}")
            
            if "context" in match:
                print("  Context:")
                for ctx in match["context"]:
                    print(f"    {ctx[:50]}..." if len(ctx) > 50 else f"    {ctx}")
        
        if len(search_results.get("matches", [])) > 2:
            print(f"\n... and {len(search_results['matches']) - 2} more matches")
    
    # Process documents in directory
    print("\n\n7. Directory Processing")
    print("-" * 50)
    
    print(f"\nProcessing all documents in: {examples_dir}")
    dir_results = doc_processor.process_documents_in_directory(str(examples_dir), recursive=False)
    
    if isinstance(dir_results, dict) and "error" in dir_results:
        print(f"Error: {dir_results['error']}")
    else:
        print(f"Processed {len(dir_results)} documents")
        for path, metadata in list(dir_results.items())[:3]:  # Show first 3 results
            print(f"  {os.path.basename(path)}: {metadata.get('document_type', 'Unknown')}, " 
                  f"{metadata.get('file_size', 0)} bytes")
            
        if len(dir_results) > 3:
            print(f"  ... and {len(dir_results) - 3} more documents")
    
    # Document merging (text files only in this example)
    print("\n\n8. Document Merging")
    print("-" * 50)
    
    # Create another text file for merging
    text_file2_path = examples_dir / "sample_document2.txt"
    if not text_file2_path.exists():
        with open(text_file2_path, "w") as f:
            f.write("# Second Sample Document\n\n")
            f.write("This is another document that will be merged with the first one.\n\n")
            f.write("## Additional Information\n\n")
            f.write("The merge operation combines multiple documents into a single output file.\n")
    
    merged_output = output_dir / "merged_document.txt"
    print(f"\nMerging documents into: {merged_output}")
    merge_result = doc_processor.merge_documents(
        [str(text_file_path), str(text_file2_path)],
        str(merged_output)
    )
    
    if "error" in merge_result:
        print(f"Merge Error: {merge_result['error']}")
    else:
        print(f"Merge successful: {merge_result.get('document_type', 'Unknown')} format")
        print(f"Output file: {merge_result.get('output_path')}")
        
        # Show content of merged file
        with open(merged_output, 'r') as f:
            merged_content = f.read()
            print("\nMerged content (first 200 chars):")
            print(merged_content[:200] + "..." if len(merged_content) > 200 else merged_content)
    
    # Advanced document analysis
    print("\n\n9. Advanced Document Analysis")
    print("-" * 50)
    
    print(f"\nPerforming advanced analysis on: {text_file_path}")
    analysis = doc_processor.analyze_document(str(text_file_path))
    
    if "error" in analysis:
        print(f"Analysis Error: {analysis['error']}")
    else:
        print("Analysis Results:")
        
        # File info
        if "file_info" in analysis:
            file_info = analysis["file_info"]
            print(f"  Document: {file_info.get('file_name')}")
            print(f"  Type: {file_info.get('document_type')}")
            print(f"  Size: {file_info.get('file_size')} bytes")
        
        # Text statistics
        if "text_statistics" in analysis:
            stats = analysis["text_statistics"]
            print("\n  Text Statistics:")
            print(f"    Character Count: {stats.get('character_count', 0)}")
            print(f"    Word Count: {stats.get('word_count', 0)}")
            print(f"    Line Count: {stats.get('line_count', 0)}")
            print(f"    Paragraph Count: {stats.get('paragraph_count', 0)}")
        
        # Document structure
        if "structure" in analysis:
            structure = analysis["structure"]
            print("\n  Document Structure:")
            for key, value in structure.items():
                if not isinstance(value, list):
                    print(f"    {key}: {value}")
        
        # Structured data summary
        if "structured_data" in analysis:
            sd = analysis["structured_data"]
            print("\n  Structured Data:")
            if sd.get("tables"):
                print(f"    Tables: {len(sd['tables'])}")
            if sd.get("fields"):
                print(f"    Fields/Form Elements: {len(sd['fields'])}")
            if sd.get("message"):
                print(f"    {sd['message']}")

if __name__ == "__main__":
    main()