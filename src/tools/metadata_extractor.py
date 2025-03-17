"""
Metadata Extractor Tool for OpenManus.

This tool provides capabilities to extract metadata from various file types:
- Documents: PDF, DOCX, TXT, etc.
- Images: JPG, PNG, GIF, etc.
- Audio: MP3, WAV, etc.
- Video: MP4, AVI, etc.
- Archives: ZIP, TAR, etc.
- Structured data: CSV, JSON, XML, etc.

It also provides summarization and content analysis features.
"""

import os
import io
import re
import json
import hashlib
import mimetypes
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class MetadataExtractorTool:
    """
    Tool for extracting metadata from various file types and performing content analysis.
    Provides capabilities for file type detection, metadata extraction, and content summarization.
    """
    
    def __init__(self, 
                base_path: str = "data/metadata_cache",
                enable_summarization: bool = False,
                enable_advanced_analysis: bool = False):
        """
        Initialize the metadata extractor tool.
        
        Args:
            base_path: Path for caching extracted metadata
            enable_summarization: Whether to enable content summarization
            enable_advanced_analysis: Whether to enable advanced content analysis
        """
        self.base_path = Path(base_path)
        self.enable_summarization = enable_summarization
        self.enable_advanced_analysis = enable_advanced_analysis
        
        # Ensure directories exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize supported file types and their handlers
        self._init_file_type_handlers()
        
    def _init_file_type_handlers(self):
        """Initialize file type handlers and their dependencies."""
        # Basic file type detection
        self.handlers = {
            # Document formats
            'text/plain': self._extract_text_metadata,
            'application/pdf': self._extract_pdf_metadata,
            'application/msword': self._extract_doc_metadata,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._extract_docx_metadata,
            
            # Image formats
            'image/jpeg': self._extract_image_metadata,
            'image/png': self._extract_image_metadata,
            'image/gif': self._extract_image_metadata,
            'image/webp': self._extract_image_metadata,
            
            # Audio formats
            'audio/mpeg': self._extract_audio_metadata,
            'audio/wav': self._extract_audio_metadata,
            
            # Video formats
            'video/mp4': self._extract_video_metadata,
            'video/quicktime': self._extract_video_metadata,
            
            # Archive formats
            'application/zip': self._extract_archive_metadata,
            'application/x-tar': self._extract_archive_metadata,
            'application/x-gzip': self._extract_archive_metadata,
            
            # Structured data formats
            'application/json': self._extract_json_metadata,
            'text/csv': self._extract_csv_metadata,
            'application/xml': self._extract_xml_metadata,
        }
        
        # Try to import optional dependencies
        try:
            import PyPDF2
            self.pdf_extractor = PyPDF2
            logger.info("PyPDF2 loaded successfully")
        except ImportError:
            self.pdf_extractor = None
            logger.warning("PyPDF2 not available - PDF metadata extraction will be limited")
            
        try:
            from PIL import Image, ExifTags
            self.image_extractor = Image
            self.exif_tags = ExifTags
            logger.info("Pillow loaded successfully")
        except ImportError:
            self.image_extractor = None
            logger.warning("Pillow not available - image metadata extraction will be limited")
            
        # More optional dependencies can be added here
    
    def detect_file_type(self, file_path: str, content: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Detect file type and basic properties.
        
        Args:
            file_path: Path to the file
            content: Optional file content (if already loaded)
            
        Returns:
            Dictionary with file type information
        """
        result = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "extension": os.path.splitext(file_path)[1].lower(),
            "mimetype": None,
            "detected_type": None,
            "size_bytes": 0,
            "detection_confidence": 0.0
        }
        
        # Get MIME type from extension
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            result["mimetype"] = mime_type
            result["detection_confidence"] = 0.7  # Reasonable confidence from extension
        
        # If content is provided, try to analyze the file header
        if content and len(content) > 0:
            result["size_bytes"] = len(content)
            
            # Enhance detection with file signature analysis
            enhanced_mime = self._analyze_file_signature(content)
            if enhanced_mime:
                result["mimetype"] = enhanced_mime
                result["detection_confidence"] = 0.9  # Higher confidence with signature
        
        # Map MIME type to a more user-friendly type
        if mime_type:
            if mime_type.startswith('text/'):
                result["detected_type"] = "text"
            elif mime_type.startswith('image/'):
                result["detected_type"] = "image"
            elif mime_type.startswith('audio/'):
                result["detected_type"] = "audio"
            elif mime_type.startswith('video/'):
                result["detected_type"] = "video"
            elif mime_type.startswith('application/pdf'):
                result["detected_type"] = "pdf"
            elif 'word' in mime_type or 'document' in mime_type:
                result["detected_type"] = "document"
            elif 'zip' in mime_type or 'tar' in mime_type or 'gzip' in mime_type:
                result["detected_type"] = "archive"
            elif 'json' in mime_type:
                result["detected_type"] = "json"
            elif 'csv' in mime_type:
                result["detected_type"] = "csv"
            elif 'xml' in mime_type:
                result["detected_type"] = "xml"
            else:
                result["detected_type"] = "unknown"
                
        return result
    
    def _analyze_file_signature(self, content: bytes) -> Optional[str]:
        """
        Analyze file content signature to determine file type.
        
        Args:
            content: File content bytes
            
        Returns:
            MIME type based on file signature, or None if undetected
        """
        if not content or len(content) < 8:
            return None
            
        # Common file signatures (magic numbers)
        signatures = {
            b'\xFF\xD8\xFF': 'image/jpeg',
            b'\x89PNG\r\n\x1A\n': 'image/png',
            b'GIF87a': 'image/gif',
            b'GIF89a': 'image/gif',
            b'%PDF': 'application/pdf',
            b'PK\x03\x04': 'application/zip',
            b'\x1F\x8B\x08': 'application/x-gzip',
            b'ID3': 'audio/mpeg',
            b'RIFF': 'audio/wav',  # Also could be video/avi
            b'ftyp': 'video/mp4',  # Simplified - should check for position and subtypes
            b'\x50\x4B\x03\x04\x14\x00\x06\x00': 'application/vnd.openxmlformats-officedocument',
        }
        
        for signature, mime_type in signatures.items():
            if content.startswith(signature):
                return mime_type
                
            # Special case for MP4 (ftyp at offset 4)
            if signature == b'ftyp' and len(content) > 12 and content[4:8] == signature:
                return mime_type
                
        # Check for text files
        if self._is_text_file(content):
            # JSON detection
            if content.strip().startswith(b'{') and content.strip().endswith(b'}'):
                return 'application/json'
            # XML detection
            elif content.strip().startswith(b'<?xml') or content.strip().startswith(b'<'):
                return 'application/xml'
            # CSV detection (simplified)
            elif b',' in content and b'\n' in content:
                return 'text/csv'
            else:
                return 'text/plain'
                
        return None
    
    def _is_text_file(self, content: bytes, sample_size: int = 1024) -> bool:
        """
        Check if content appears to be a text file by analyzing byte patterns.
        
        Args:
            content: File content bytes
            sample_size: Number of bytes to sample
            
        Returns:
            True if the content appears to be text, False otherwise
        """
        # Sample a portion of the file
        sample = content[:sample_size]
        if not sample:
            return False
            
        # Check for null bytes which are rare in text files
        if b'\x00' in sample:
            return False
            
        # Count printable ASCII and common Unicode characters
        printable_chars = 0
        for byte in sample:
            # ASCII printable range + common whitespace
            if (32 <= byte <= 126) or byte in (9, 10, 13):  # tab, LF, CR
                printable_chars += 1
                
        # If more than 90% of bytes are printable, consider it text
        return printable_chars / len(sample) > 0.9
    
    def extract_metadata(self, file_path: str, content: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Extract metadata from a file.
        
        Args:
            file_path: Path to the file
            content: Optional file content (if already loaded)
            
        Returns:
            Dictionary with extracted metadata
        """
        # First detect file type
        file_info = self.detect_file_type(file_path, content)
        
        # Basic metadata
        metadata = {
            "file_path": file_path,
            "file_name": file_info["file_name"],
            "file_type": file_info["detected_type"],
            "mime_type": file_info["mimetype"],
            "extension": file_info["extension"],
            "size_bytes": file_info["size_bytes"] or os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "created_time": None,
            "modified_time": None,
            "hash": None,
            "content_type_specific": {},
        }
        
        # Try to get file times
        try:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                metadata["created_time"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
                metadata["modified_time"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except:
            pass
            
        # Load content if not provided
        if not content and os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                metadata["size_bytes"] = len(content)
                
                # Calculate hash
                metadata["hash"] = hashlib.sha256(content).hexdigest()
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                return metadata
        elif content:
            # Calculate hash from provided content
            metadata["hash"] = hashlib.sha256(content).hexdigest()
        
        # Extract type-specific metadata using handlers
        mime_type = file_info["mimetype"]
        if mime_type and mime_type in self.handlers:
            try:
                type_metadata = self.handlers[mime_type](file_path, content)
                if type_metadata:
                    metadata["content_type_specific"] = type_metadata
            except Exception as e:
                logger.error(f"Error extracting metadata for {file_path}: {e}")
        
        # Add summarization if enabled
        if self.enable_summarization:
            try:
                summary = self._generate_summary(file_path, content, file_info)
                if summary:
                    metadata["summary"] = summary
            except Exception as e:
                logger.error(f"Error generating summary for {file_path}: {e}")
        
        return metadata
    
    def batch_extract_metadata(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Extract metadata from multiple files.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary mapping file paths to their metadata
        """
        results = {}
        for file_path in file_paths:
            try:
                metadata = self.extract_metadata(file_path)
                results[file_path] = metadata
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results[file_path] = {"error": str(e)}
                
        return results
    
    def extract_metadata_from_directory(self, 
                                       directory_path: str, 
                                       recursive: bool = True,
                                       file_pattern: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Extract metadata from all files in a directory.
        
        Args:
            directory_path: Path to the directory
            recursive: Whether to process subdirectories
            file_pattern: Optional regex pattern to filter files
            
        Returns:
            Dictionary mapping file paths to their metadata
        """
        all_files = []
        
        # Compile regex pattern if provided
        pattern = None
        if file_pattern:
            try:
                pattern = re.compile(file_pattern)
            except re.error:
                logger.error(f"Invalid regex pattern: {file_pattern}")
        
        # Walk directory
        if recursive:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if not pattern or pattern.search(file_path):
                        all_files.append(file_path)
        else:
            with os.scandir(directory_path) as entries:
                for entry in entries:
                    if entry.is_file():
                        if not pattern or pattern.search(entry.path):
                            all_files.append(entry.path)
        
        # Process all collected files
        return self.batch_extract_metadata(all_files)
    
    def generate_metadata_report(self, metadata: Dict[str, Any], format: str = "json") -> str:
        """
        Generate a formatted report from metadata.
        
        Args:
            metadata: Extracted metadata
            format: Report format ('json', 'markdown', or 'text')
            
        Returns:
            Formatted metadata report
        """
        if format.lower() == 'json':
            return json.dumps(metadata, indent=2)
            
        elif format.lower() == 'markdown':
            md_report = f"# Metadata Report: {metadata.get('file_name', 'Unknown File')}\n\n"
            
            md_report += "## Basic Information\n\n"
            md_report += f"- **File Name**: {metadata.get('file_name', 'Unknown')}\n"
            md_report += f"- **File Type**: {metadata.get('file_type', 'Unknown')}\n"
            md_report += f"- **MIME Type**: {metadata.get('mime_type', 'Unknown')}\n"
            md_report += f"- **Extension**: {metadata.get('extension', 'None')}\n"
            md_report += f"- **Size**: {metadata.get('size_bytes', 0)} bytes\n"
            md_report += f"- **Created**: {metadata.get('created_time', 'Unknown')}\n"
            md_report += f"- **Modified**: {metadata.get('modified_time', 'Unknown')}\n"
            md_report += f"- **SHA-256 Hash**: {metadata.get('hash', 'Not calculated')}\n\n"
            
            # Add content-specific metadata
            if "content_type_specific" in metadata and metadata["content_type_specific"]:
                md_report += "## Content-Specific Metadata\n\n"
                for key, value in metadata["content_type_specific"].items():
                    if isinstance(value, dict):
                        md_report += f"### {key.replace('_', ' ').title()}\n\n"
                        for sub_key, sub_value in value.items():
                            md_report += f"- **{sub_key.replace('_', ' ').title()}**: {sub_value}\n"
                        md_report += "\n"
                    else:
                        md_report += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                
            # Add summary if available
            if "summary" in metadata and metadata["summary"]:
                md_report += "## Content Summary\n\n"
                md_report += f"{metadata['summary']}\n\n"
                
            return md_report
            
        else:  # text format
            text_report = f"Metadata Report: {metadata.get('file_name', 'Unknown File')}\n"
            text_report += "="*50 + "\n\n"
            
            text_report += "Basic Information:\n"
            text_report += f"  File Name: {metadata.get('file_name', 'Unknown')}\n"
            text_report += f"  File Type: {metadata.get('file_type', 'Unknown')}\n"
            text_report += f"  MIME Type: {metadata.get('mime_type', 'Unknown')}\n"
            text_report += f"  Extension: {metadata.get('extension', 'None')}\n"
            text_report += f"  Size: {metadata.get('size_bytes', 0)} bytes\n"
            text_report += f"  Created: {metadata.get('created_time', 'Unknown')}\n"
            text_report += f"  Modified: {metadata.get('modified_time', 'Unknown')}\n"
            text_report += f"  SHA-256 Hash: {metadata.get('hash', 'Not calculated')}\n\n"
            
            # Add content-specific metadata
            if "content_type_specific" in metadata and metadata["content_type_specific"]:
                text_report += "Content-Specific Metadata:\n"
                for key, value in metadata["content_type_specific"].items():
                    if isinstance(value, dict):
                        text_report += f"  {key.replace('_', ' ').title()}:\n"
                        for sub_key, sub_value in value.items():
                            text_report += f"    {sub_key.replace('_', ' ').title()}: {sub_value}\n"
                    else:
                        text_report += f"  {key.replace('_', ' ').title()}: {value}\n"
                text_report += "\n"
                
            # Add summary if available
            if "summary" in metadata and metadata["summary"]:
                text_report += "Content Summary:\n"
                text_report += f"  {metadata['summary']}\n\n"
                
            return text_report
    
    def cache_metadata(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Cache extracted metadata to disk.
        
        Args:
            file_path: Original file path
            metadata: Extracted metadata to cache
            
        Returns:
            True if successful, False otherwise
        """
        # Generate cache file path
        file_hash = metadata.get("hash") or hashlib.md5(file_path.encode()).hexdigest()
        cache_path = self.base_path / f"{file_hash}.json"
        
        try:
            # Ensure parent directory exists
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Store metadata with timestamp
            cache_data = {
                "original_path": file_path,
                "cached_time": datetime.now().isoformat(),
                "metadata": metadata
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error caching metadata for {file_path}: {e}")
            return False
    
    def get_cached_metadata(self, file_path: str, max_age_days: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata from cache if available.
        
        Args:
            file_path: File path to look up
            max_age_days: Maximum age of cached data in days
            
        Returns:
            Cached metadata or None if not found or too old
        """
        # Try finding by file path hash
        path_hash = hashlib.md5(file_path.encode()).hexdigest()
        cache_path = self.base_path / f"{path_hash}.json"
        
        if not cache_path.exists():
            # If file exists, calculate its hash and try finding by content hash
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        content_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    content_cache_path = self.base_path / f"{content_hash}.json"
                    if content_cache_path.exists():
                        cache_path = content_cache_path
                    else:
                        return None
                except:
                    return None
            else:
                return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                
            # Check cache age if max_age_days is specified
            if max_age_days is not None:
                cache_time = datetime.fromisoformat(cache_data.get("cached_time", "2000-01-01"))
                age_days = (datetime.now() - cache_time).days
                
                if age_days > max_age_days:
                    return None
                    
            return cache_data.get("metadata")
            
        except Exception as e:
            logger.error(f"Error retrieving cached metadata for {file_path}: {e}")
            return None
    
    # ------ Content Summarization ------
    
    def _generate_summary(self, 
                         file_path: str, 
                         content: Optional[bytes], 
                         file_info: Dict[str, Any]) -> Optional[str]:
        """
        Generate a summary of file content.
        
        Args:
            file_path: Path to the file
            content: File content bytes
            file_info: File type information
            
        Returns:
            Generated summary or None if summarization fails
        """
        if not self.enable_summarization:
            return None
            
        # Placeholder for future LLM-based summarization
        # This would typically use an LLM service to generate summaries
        mime_type = file_info.get("mimetype")
        
        if mime_type:
            if mime_type.startswith('text/plain'):
                return self._summarize_text(content)
            elif mime_type == 'application/pdf' and self.pdf_extractor:
                return self._summarize_pdf(file_path, content)
            elif mime_type.startswith('image/') and self.image_extractor:
                return self._summarize_image(file_path, content)
                
        # Default basic summary for unsupported types
        return f"File of type '{mime_type}' with size {file_info.get('size_bytes', 0)} bytes"
    
    def _summarize_text(self, content: bytes) -> Optional[str]:
        """Generate summary for text content."""
        try:
            # Basic text summarization - first few lines and character count
            text = content.decode('utf-8', errors='replace')
            lines = text.split('\n')
            preview = '\n'.join(lines[:3]) if len(lines) > 3 else text
            
            if len(preview) > 100:
                preview = preview[:100] + "..."
                
            char_count = len(text)
            line_count = len(lines)
            word_count = len(text.split())
            
            return f"Text document with {line_count} lines, {word_count} words, and {char_count} characters. Preview: {preview}"
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return None
    
    def _summarize_pdf(self, file_path: str, content: Optional[bytes]) -> Optional[str]:
        """Generate summary for PDF content."""
        # Placeholder for PDF summarization
        # Would extract text and generate summary
        return "PDF document (detailed summarization not implemented)"
    
    def _summarize_image(self, file_path: str, content: Optional[bytes]) -> Optional[str]:
        """Generate summary for image content."""
        # Placeholder for image summarization
        # Would analyze image properties and generate description
        return "Image file (detailed description not implemented)"
    
    # ------ Type-specific Metadata Extractors ------
    
    def _extract_text_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from text files."""
        try:
            if not content:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
            # Decode text and analyze
            text = content.decode('utf-8', errors='replace')
            lines = text.split('\n')
            
            return {
                "character_count": len(text),
                "line_count": len(lines),
                "word_count": len(text.split()),
                "encoding": "utf-8",  # Simplified, in reality would detect encoding
                "has_bom": content.startswith(b'\xef\xbb\xbf'),  # UTF-8 BOM check
            }
        except Exception as e:
            logger.error(f"Error extracting text metadata: {e}")
            return {}
    
    def _extract_pdf_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from PDF files."""
        # Placeholder - would use PyPDF2 or similar library
        if not self.pdf_extractor:
            return {"note": "PDF extraction not available - install PyPDF2"}
        return {"format": "PDF"}
    
    def _extract_doc_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from DOC files."""
        # Placeholder - would use python-docx or similar library
        return {"format": "DOC"}
    
    def _extract_docx_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from DOCX files."""
        # Placeholder - would use python-docx or similar library
        return {"format": "DOCX"}
    
    def _extract_image_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from image files."""
        # Placeholder - would use Pillow to extract EXIF data etc.
        if not self.image_extractor:
            return {"note": "Image extraction not available - install Pillow"}
        return {"format": "Image"}
    
    def _extract_audio_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from audio files."""
        # Placeholder - would use mutagen or similar library
        return {"format": "Audio"}
    
    def _extract_video_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from video files."""
        # Placeholder - would use ffmpeg binding or similar
        return {"format": "Video"}
    
    def _extract_archive_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from archive files."""
        # Basic archive analysis without content extraction
        try:
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    file_count = len(file_list)
                    total_size = sum(zip_info.file_size for zip_info in zip_ref.infolist())
                    compressed_size = sum(zip_info.compress_size for zip_info in zip_ref.infolist())
                    
                    return {
                        "format": "ZIP",
                        "file_count": file_count,
                        "total_uncompressed_size": total_size,
                        "total_compressed_size": compressed_size,
                        "compression_ratio": round(total_size / compressed_size, 2) if compressed_size > 0 else 0,
                        "files": file_list[:10] + ["..."] if file_count > 10 else file_list,
                    }
            elif file_path.endswith('.tar'):
                with tarfile.open(file_path, 'r') as tar_ref:
                    file_list = tar_ref.getnames()
                    return {
                        "format": "TAR",
                        "file_count": len(file_list),
                        "files": file_list[:10] + ["..."] if len(file_list) > 10 else file_list,
                    }
            elif file_path.endswith('.gz'):
                # Basic info for gzip files
                return {
                    "format": "GZIP",
                    "note": "GZIP archive typically contains a single compressed file",
                }
            else:
                return {"format": "Unknown Archive"}
        except Exception as e:
            logger.error(f"Error extracting archive metadata: {e}")
            return {"format": "Archive", "error": str(e)}
    
    def _extract_json_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from JSON files."""
        try:
            if not content:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
            # Parse JSON
            json_data = json.loads(content.decode('utf-8', errors='replace'))
            
            # Analyze structure
            if isinstance(json_data, dict):
                return {
                    "format": "JSON",
                    "root_type": "object",
                    "keys_count": len(json_data),
                    "top_level_keys": list(json_data.keys())[:10] + ["..."] if len(json_data) > 10 else list(json_data.keys()),
                }
            elif isinstance(json_data, list):
                return {
                    "format": "JSON",
                    "root_type": "array",
                    "items_count": len(json_data),
                    "first_item_type": type(json_data[0]).__name__ if json_data else "empty",
                }
            else:
                return {
                    "format": "JSON",
                    "root_type": type(json_data).__name__,
                }
        except Exception as e:
            logger.error(f"Error extracting JSON metadata: {e}")
            return {"format": "JSON", "error": str(e)}
    
    def _extract_csv_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from CSV files."""
        try:
            if not content:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
            # Parse CSV (basic analysis without pandas)
            text = content.decode('utf-8', errors='replace')
            lines = text.split('\n')
            
            # Try to detect delimiter
            first_line = lines[0] if lines else ""
            delimiter = ','
            if first_line:
                comma_count = first_line.count(',')
                tab_count = first_line.count('\t')
                semicolon_count = first_line.count(';')
                pipe_count = first_line.count('|')
                
                if tab_count > comma_count and tab_count > semicolon_count and tab_count > pipe_count:
                    delimiter = '\t'
                elif semicolon_count > comma_count and semicolon_count > tab_count and semicolon_count > pipe_count:
                    delimiter = ';'
                elif pipe_count > comma_count and pipe_count > tab_count and pipe_count > semicolon_count:
                    delimiter = '|'
            
            # Get column count and row count
            row_count = len([line for line in lines if line.strip()])
            if first_line:
                column_count = len(first_line.split(delimiter))
            else:
                column_count = 0
                
            # Get column names (assuming first row is header)
            header = lines[0].split(delimiter) if lines else []
            
            return {
                "format": "CSV",
                "delimiter": delimiter,
                "row_count": row_count,
                "column_count": column_count,
                "columns": header,
            }
        except Exception as e:
            logger.error(f"Error extracting CSV metadata: {e}")
            return {"format": "CSV", "error": str(e)}
    
    def _extract_xml_metadata(self, file_path: str, content: Optional[bytes]) -> Dict[str, Any]:
        """Extract metadata from XML files."""
        try:
            if not content:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
            # Basic XML analysis without full parsing
            text = content.decode('utf-8', errors='replace')
            
            # Try to identify root element
            root_match = re.search(r'<([^\s>/?]+)[^>]*>', text)
            root_element = root_match.group(1) if root_match else "unknown"
            
            # Count elements (very basic)
            element_count = len(re.findall(r'<[^/!][^>]*>', text))
            
            return {
                "format": "XML",
                "root_element": root_element,
                "element_count": element_count,
                "has_namespace": "xmlns" in text,
            }
        except Exception as e:
            logger.error(f"Error extracting XML metadata: {e}")
            return {"format": "XML", "error": str(e)}