"""
Document Processing Tool for OpenManus.

This tool provides capabilities for processing various document formats:
- PDF parsing and analysis
- Word document processing
- Extract structured data from documents
- Document content analysis and transformation
- Advanced document search capabilities
"""

import os
import io
import re
import json
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple, BinaryIO

# Import config system
from src.config import load_config, Config

# Configure logging
logger = logging.getLogger(__name__)

class DocumentProcessingTool:
    """
    Tool for processing and analyzing documents in various formats.
    Provides capabilities for structured extraction, content analysis,
    and document transformation.
    """
    
    def __init__(self, 
                cache_dir: str = None,
                enable_ocr: bool = None,
                enable_advanced_analysis: bool = None,
                config_obj: Config = None):
        """
        Initialize the document processing tool.
        
        Args:
            cache_dir: Directory for caching processed documents (overrides config)
            enable_ocr: Whether to enable OCR capabilities (overrides config)
            enable_advanced_analysis: Whether to enable advanced document analysis (overrides config)
            config_obj: Config object for configuration
        """
        # Load configuration
        if config_obj is None:
            config_obj = load_config()
            
        # Get configuration or use defaults
        if cache_dir is None:
            cache_dir = config_obj.get_tool_config(
                "document_processing", 
                "cache_dir", 
                os.environ.get("OPENMANUS_DOCUMENT_CACHE_DIR", "data/document_cache")
            )
            
        if enable_ocr is None:
            enable_ocr = config_obj.get_tool_config(
                "document_processing", 
                "enable_ocr", 
                os.environ.get("OPENMANUS_DOCUMENT_ENABLE_OCR", "0").lower() in ("1", "true", "yes")
            )
            
        if enable_advanced_analysis is None:
            enable_advanced_analysis = config_obj.get_tool_config(
                "document_processing", 
                "enable_advanced_analysis", 
                os.environ.get("OPENMANUS_DOCUMENT_ENABLE_ADVANCED", "0").lower() in ("1", "true", "yes")
            )
        
        self.cache_dir = os.path.abspath(cache_dir)
        self.enable_ocr = enable_ocr
        self.enable_advanced_analysis = enable_advanced_analysis
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize document handlers
        self._init_document_handlers()
    
    def _init_document_handlers(self):
        """Initialize document format handlers with appropriate dependencies."""
        self.handlers = {}
        
        # Try to import PDF libraries
        try:
            import PyPDF2
            self.handlers['pdf'] = {
                'library': PyPDF2,
                'available': True,
                'parse': self._parse_pdf_with_pypdf2,
                'extract_text': self._extract_text_from_pdf,
                'get_metadata': self._get_pdf_metadata,
                'split': self._split_pdf,
                'merge': self._merge_pdfs
            }
            logger.info("PyPDF2 loaded successfully")
        except ImportError:
            self.handlers['pdf'] = {
                'library': None,
                'available': False,
                'error': "PyPDF2 not installed. Install with: pip install PyPDF2"
            }
            logger.warning("PyPDF2 not available - PDF processing will be limited")
        
        # Try to import Word document libraries
        try:
            import docx
            self.handlers['docx'] = {
                'library': docx,
                'available': True,
                'parse': self._parse_docx,
                'extract_text': self._extract_text_from_docx,
                'get_metadata': self._get_docx_metadata,
                'create': self._create_docx
            }
            logger.info("python-docx loaded successfully")
        except ImportError:
            self.handlers['docx'] = {
                'library': None,
                'available': False,
                'error': "python-docx not installed. Install with: pip install python-docx"
            }
            logger.warning("python-docx not available - DOCX processing will be limited")
        
        # Try to import OCR libraries
        if self.enable_ocr:
            try:
                import pytesseract
                from PIL import Image
                self.handlers['ocr'] = {
                    'library': pytesseract,
                    'image_library': Image,
                    'available': True,
                    'process': self._process_image_with_ocr
                }
                logger.info("Tesseract OCR support loaded successfully")
            except ImportError:
                self.handlers['ocr'] = {
                    'library': None,
                    'available': False,
                    'error': "pytesseract not installed. Install with: pip install pytesseract pillow"
                }
                logger.warning("pytesseract not available - OCR processing will be limited")
        
        # Add plain text handling
        self.handlers['text'] = {
            'library': None,
            'available': True,
            'parse': self._parse_text,
            'extract_text': lambda content, **kwargs: content.decode('utf-8', errors='replace') if isinstance(content, bytes) else content
        }
    
    def _check_handler(self, doc_type: str) -> bool:
        """
        Check if a document handler is available.
        
        Args:
            doc_type: Document type to check
            
        Returns:
            True if handler is available, False otherwise
        """
        if doc_type not in self.handlers:
            logger.error(f"No handler defined for document type: {doc_type}")
            return False
            
        if not self.handlers[doc_type].get('available', False):
            error_msg = self.handlers[doc_type].get('error', f"Handler for {doc_type} not available")
            logger.error(error_msg)
            return False
            
        return True
    
    def _get_document_type(self, file_path: str) -> str:
        """
        Determine document type from file extension.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document type string (pdf, docx, text, etc.)
        """
        ext = os.path.splitext(file_path.lower())[1]
        
        if ext == '.pdf':
            return 'pdf'
        elif ext in ('.docx', '.doc'):
            return 'docx'
        elif ext in ('.txt', '.md', '.csv', '.json', '.xml', '.html', '.css', '.js'):
            return 'text'
        else:
            return 'unknown'
    
    # === PDF Processing Methods ===
    
    def _parse_pdf_with_pypdf2(self, content: Union[bytes, str, BinaryIO], **kwargs) -> Dict[str, Any]:
        """
        Parse a PDF document using PyPDF2.
        
        Args:
            content: PDF content as bytes, file path, or file-like object
            kwargs: Additional parsing options
            
        Returns:
            Dictionary with parsed PDF structure
        """
        if not self._check_handler('pdf'):
            return {"error": "PDF handler not available"}
        
        PyPDF2 = self.handlers['pdf']['library']
        pdf_reader = None
        temp_file = None
        
        try:
            # Create PDF reader based on input type
            if isinstance(content, bytes):
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(content)
                temp_file.close()
                pdf_reader = PyPDF2.PdfReader(temp_file.name)
            elif isinstance(content, str) and os.path.exists(content):
                pdf_reader = PyPDF2.PdfReader(content)
            elif hasattr(content, 'read'):
                pdf_reader = PyPDF2.PdfReader(content)
            else:
                return {"error": "Invalid PDF content format"}
            
            # Extract basic structure and metadata
            result = {
                "page_count": len(pdf_reader.pages),
                "metadata": pdf_reader.metadata if hasattr(pdf_reader, 'metadata') else {},
                "pages": []
            }
            
            # Process each page if requested
            if kwargs.get("extract_pages", True):
                max_pages = kwargs.get("max_pages", len(pdf_reader.pages))
                for i in range(min(max_pages, len(pdf_reader.pages))):
                    page = pdf_reader.pages[i]
                    page_data = {
                        "page_number": i + 1,
                        "text": page.extract_text() if hasattr(page, 'extract_text') else ""
                    }
                    result["pages"].append(page_data)
            
            return result
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            return {"error": f"PDF parsing error: {str(e)}"}
        finally:
            # Clean up temporary file if created
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def _extract_text_from_pdf(self, content: Union[bytes, str, BinaryIO], **kwargs) -> str:
        """
        Extract all text from a PDF document.
        
        Args:
            content: PDF content as bytes, file path, or file-like object
            kwargs: Additional extraction options
            
        Returns:
            Extracted text as string
        """
        if not self._check_handler('pdf'):
            return "Error: PDF handler not available"
        
        try:
            pdf_data = self._parse_pdf_with_pypdf2(content, extract_pages=True)
            
            if "error" in pdf_data:
                return f"Error: {pdf_data['error']}"
            
            # Combine text from all pages
            all_text = ""
            for page in pdf_data.get("pages", []):
                all_text += page.get("text", "") + "\n\n"
            
            return all_text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return f"Error extracting text: {str(e)}"
    
    def _get_pdf_metadata(self, content: Union[bytes, str, BinaryIO]) -> Dict[str, Any]:
        """
        Extract metadata from a PDF document.
        
        Args:
            content: PDF content as bytes, file path, or file-like object
            
        Returns:
            Dictionary with PDF metadata
        """
        if not self._check_handler('pdf'):
            return {"error": "PDF handler not available"}
        
        try:
            pdf_data = self._parse_pdf_with_pypdf2(content, extract_pages=False)
            
            if "error" in pdf_data:
                return {"error": pdf_data["error"]}
            
            # Format metadata properly
            raw_metadata = pdf_data.get("metadata", {})
            metadata = {}
            
            # Handle both attribute access and dict access
            for key in dir(raw_metadata):
                if not key.startswith('_') and not callable(getattr(raw_metadata, key)):
                    value = getattr(raw_metadata, key)
                    if value:
                        metadata[key] = str(value)
            
            # Add basic document info
            metadata.update({
                "page_count": pdf_data.get("page_count", 0)
            })
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {str(e)}")
            return {"error": f"Metadata extraction error: {str(e)}"}
    
    def _split_pdf(self, content: Union[bytes, str, BinaryIO], 
                  page_ranges: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """
        Split a PDF into multiple documents by page ranges.
        
        Args:
            content: PDF content as bytes, file path, or file-like object
            page_ranges: List of tuples with start and end page numbers (1-indexed)
            
        Returns:
            List of dictionaries with split PDFs
        """
        if not self._check_handler('pdf'):
            return [{"error": "PDF handler not available"}]
        
        PyPDF2 = self.handlers['pdf']['library']
        pdf_reader = None
        temp_file = None
        result_files = []
        
        try:
            # Create PDF reader based on input type
            if isinstance(content, bytes):
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(content)
                temp_file.close()
                pdf_reader = PyPDF2.PdfReader(temp_file.name)
            elif isinstance(content, str) and os.path.exists(content):
                pdf_reader = PyPDF2.PdfReader(content)
            elif hasattr(content, 'read'):
                pdf_reader = PyPDF2.PdfReader(content)
            else:
                return [{"error": "Invalid PDF content format"}]
            
            # Process each page range
            for i, (start, end) in enumerate(page_ranges):
                # Adjust for 0-indexed pages
                start_idx = max(0, start - 1)
                end_idx = min(len(pdf_reader.pages), end)
                
                if start_idx >= end_idx or start_idx < 0 or end_idx > len(pdf_reader.pages):
                    result_files.append({
                        "error": f"Invalid page range: {start}-{end}",
                        "range": f"{start}-{end}"
                    })
                    continue
                
                # Create a new PDF writer and add pages
                pdf_writer = PyPDF2.PdfWriter()
                for page_num in range(start_idx, end_idx):
                    pdf_writer.add_page(pdf_reader.pages[page_num])
                
                # Write to temporary file
                output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                
                with open(output_file.name, 'wb') as output_stream:
                    pdf_writer.write(output_stream)
                
                # Read back the split PDF into memory
                with open(output_file.name, 'rb') as f:
                    split_content = f.read()
                
                # Add to results
                result_files.append({
                    "range": f"{start}-{end}",
                    "content": split_content,
                    "page_count": end_idx - start_idx,
                    "temp_path": output_file.name  # Caller should handle cleanup
                })
                
            return result_files
        except Exception as e:
            logger.error(f"Error splitting PDF: {str(e)}")
            return [{"error": f"PDF splitting error: {str(e)}"}]
        finally:
            # Clean up temporary file if created
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def _merge_pdfs(self, contents: List[Union[bytes, str, BinaryIO]]) -> Dict[str, Any]:
        """
        Merge multiple PDFs into a single document.
        
        Args:
            contents: List of PDF contents as bytes, file paths, or file-like objects
            
        Returns:
            Dictionary with merged PDF content
        """
        if not self._check_handler('pdf'):
            return {"error": "PDF handler not available"}
        
        PyPDF2 = self.handlers['pdf']['library']
        temp_files = []
        
        try:
            # Create a PDF merger
            pdf_merger = PyPDF2.PdfMerger()
            
            # Add each document
            for i, content in enumerate(contents):
                if isinstance(content, bytes):
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    temp_file.write(content)
                    temp_file.close()
                    temp_files.append(temp_file.name)
                    pdf_merger.append(temp_file.name)
                elif isinstance(content, str) and os.path.exists(content):
                    pdf_merger.append(content)
                elif hasattr(content, 'read'):
                    pdf_merger.append(content)
                else:
                    logger.warning(f"Skipping invalid PDF content at index {i}")
            
            # Write to temporary file
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            
            with open(output_file.name, 'wb') as output_stream:
                pdf_merger.write(output_stream)
            
            # Read back the merged PDF
            with open(output_file.name, 'rb') as f:
                merged_content = f.read()
            
            return {
                "content": merged_content,
                "page_count": sum(len(PyPDF2.PdfReader(pdf).pages) for pdf in temp_files) if temp_files else -1,
                "temp_path": output_file.name  # Caller should handle cleanup
            }
        except Exception as e:
            logger.error(f"Error merging PDFs: {str(e)}")
            return {"error": f"PDF merging error: {str(e)}"}
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    # === DOCX Processing Methods ===
    
    def _parse_docx(self, content: Union[bytes, str, BinaryIO], **kwargs) -> Dict[str, Any]:
        """
        Parse a DOCX document.
        
        Args:
            content: DOCX content as bytes, file path, or file-like object
            kwargs: Additional parsing options
            
        Returns:
            Dictionary with parsed DOCX structure
        """
        if not self._check_handler('docx'):
            return {"error": "DOCX handler not available"}
        
        docx = self.handlers['docx']['library']
        temp_file = None
        
        try:
            # Create document object based on input type
            if isinstance(content, bytes):
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
                temp_file.write(content)
                temp_file.close()
                doc = docx.Document(temp_file.name)
            elif isinstance(content, str) and os.path.exists(content):
                doc = docx.Document(content)
            elif hasattr(content, 'read'):
                doc = docx.Document(content)
            else:
                return {"error": "Invalid DOCX content format"}
            
            # Extract basic structure
            result = {
                "paragraphs": len(doc.paragraphs),
                "sections": len(doc.sections),
                "tables": len(doc.tables),
                "content": []
            }
            
            # Get document properties if available
            try:
                core_properties = doc.core_properties
                result["metadata"] = {
                    "author": core_properties.author,
                    "created": core_properties.created.isoformat() if core_properties.created else None,
                    "modified": core_properties.modified.isoformat() if core_properties.modified else None,
                    "title": core_properties.title,
                    "subject": core_properties.subject,
                    "keywords": core_properties.keywords,
                    "language": core_properties.language,
                    "category": core_properties.category,
                    "comments": core_properties.comments,
                    "identifier": core_properties.identifier,
                    "last_modified_by": core_properties.last_modified_by,
                    "revision": core_properties.revision,
                    "version": core_properties.version
                }
            except:
                result["metadata"] = {}
            
            # Process document content if requested
            if kwargs.get("extract_content", True):
                # Extract paragraphs
                for para in doc.paragraphs:
                    if para.text.strip():
                        result["content"].append({
                            "type": "paragraph",
                            "text": para.text,
                            "style": para.style.name
                        })
                
                # Extract tables
                for table in doc.tables:
                    table_data = []
                    for row in table.rows:
                        table_data.append([cell.text for cell in row.cells])
                    
                    result["content"].append({
                        "type": "table",
                        "data": table_data
                    })
            
            return result
        except Exception as e:
            logger.error(f"Error parsing DOCX: {str(e)}")
            return {"error": f"DOCX parsing error: {str(e)}"}
        finally:
            # Clean up temporary file if created
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def _extract_text_from_docx(self, content: Union[bytes, str, BinaryIO], **kwargs) -> str:
        """
        Extract all text from a DOCX document.
        
        Args:
            content: DOCX content as bytes, file path, or file-like object
            kwargs: Additional extraction options
            
        Returns:
            Extracted text as string
        """
        if not self._check_handler('docx'):
            return "Error: DOCX handler not available"
        
        try:
            docx_data = self._parse_docx(content, extract_content=True)
            
            if "error" in docx_data:
                return f"Error: {docx_data['error']}"
            
            # Combine text from all content items
            all_text = ""
            for item in docx_data.get("content", []):
                if item["type"] == "paragraph":
                    all_text += item["text"] + "\n\n"
                elif item["type"] == "table":
                    for row in item["data"]:
                        all_text += " | ".join(row) + "\n"
                    all_text += "\n"
            
            return all_text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            return f"Error extracting text: {str(e)}"
    
    def _get_docx_metadata(self, content: Union[bytes, str, BinaryIO]) -> Dict[str, Any]:
        """
        Extract metadata from a DOCX document.
        
        Args:
            content: DOCX content as bytes, file path, or file-like object
            
        Returns:
            Dictionary with DOCX metadata
        """
        if not self._check_handler('docx'):
            return {"error": "DOCX handler not available"}
        
        try:
            docx_data = self._parse_docx(content, extract_content=False)
            
            if "error" in docx_data:
                return {"error": docx_data["error"]}
            
            # Return metadata with additional document info
            metadata = docx_data.get("metadata", {})
            metadata.update({
                "paragraphs": docx_data.get("paragraphs", 0),
                "sections": docx_data.get("sections", 0),
                "tables": docx_data.get("tables", 0)
            })
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting DOCX metadata: {str(e)}")
            return {"error": f"Metadata extraction error: {str(e)}"}
    
    def _create_docx(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new DOCX document from structured content.
        
        Args:
            content: Dictionary with document structure and content
            
        Returns:
            Dictionary with created DOCX content
        """
        if not self._check_handler('docx'):
            return {"error": "DOCX handler not available"}
        
        docx = self.handlers['docx']['library']
        
        try:
            # Create a new document
            doc = docx.Document()
            
            # Set document metadata if provided
            if "metadata" in content:
                metadata = content["metadata"]
                properties = doc.core_properties
                
                for key, value in metadata.items():
                    if hasattr(properties, key) and value is not None:
                        setattr(properties, key, value)
            
            # Add content items
            for item in content.get("content", []):
                item_type = item.get("type")
                
                if item_type == "paragraph":
                    p = doc.add_paragraph(item.get("text", ""))
                    
                    # Apply style if specified
                    if "style" in item and item["style"] in doc.styles:
                        p.style = item["style"]
                        
                    # Apply formatting if specified
                    if item.get("bold"):
                        for run in p.runs:
                            run.bold = True
                    if item.get("italic"):
                        for run in p.runs:
                            run.italic = True
                
                elif item_type == "heading":
                    level = min(item.get("level", 1), 9)  # Word supports heading levels 1-9
                    doc.add_heading(item.get("text", ""), level=level)
                
                elif item_type == "table":
                    if "data" in item and isinstance(item["data"], list):
                        # Create table with appropriate dimensions
                        rows = len(item["data"])
                        cols = max(len(row) for row in item["data"]) if rows > 0 else 0
                        
                        if rows > 0 and cols > 0:
                            table = doc.add_table(rows=rows, cols=cols)
                            
                            # Populate table cells
                            for i, row_data in enumerate(item["data"]):
                                for j, cell_text in enumerate(row_data):
                                    if j < cols:  # Ensure we don't exceed column count
                                        table.cell(i, j).text = str(cell_text)
                
                elif item_type == "list":
                    if "items" in item and isinstance(item["items"], list):
                        for list_item in item["items"]:
                            p = doc.add_paragraph(style='List Bullet')
                            p.add_run(str(list_item))
                
                elif item_type == "page_break":
                    doc.add_page_break()
            
            # Save to temporary file
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
            doc.save(output_file.name)
            
            # Read back the document
            with open(output_file.name, 'rb') as f:
                docx_content = f.read()
            
            return {
                "content": docx_content,
                "temp_path": output_file.name  # Caller should handle cleanup
            }
        except Exception as e:
            logger.error(f"Error creating DOCX: {str(e)}")
            return {"error": f"DOCX creation error: {str(e)}"}
    
    # === Text Processing Methods ===
    
    def _parse_text(self, content: Union[bytes, str], **kwargs) -> Dict[str, Any]:
        """
        Parse a text document.
        
        Args:
            content: Text content as bytes or string
            kwargs: Additional parsing options
            
        Returns:
            Dictionary with parsed text structure
        """
        try:
            # Ensure content is string
            if isinstance(content, bytes):
                text = content.decode('utf-8', errors='replace')
            else:
                text = str(content)
            
            # Split into lines
            lines = text.splitlines()
            
            # Basic text analysis
            result = {
                "line_count": len(lines),
                "character_count": len(text),
                "word_count": len(text.split()),
                "is_empty": len(text.strip()) == 0
            }
            
            # Extract content if requested
            if kwargs.get("extract_content", True):
                result["content"] = text
                
                # Attempt to detect structure
                structure = self._detect_text_structure(text)
                if structure:
                    result.update(structure)
            
            return result
        except Exception as e:
            logger.error(f"Error parsing text: {str(e)}")
            return {"error": f"Text parsing error: {str(e)}"}
    
    def _detect_text_structure(self, text: str) -> Dict[str, Any]:
        """
        Attempt to detect structure in a text document.
        
        Args:
            text: Text content
            
        Returns:
            Dictionary with detected structure
        """
        result = {}
        
        # Check for common formats
        
        # JSON
        if text.strip().startswith('{') and text.strip().endswith('}'):
            try:
                json_data = json.loads(text)
                result["format"] = "json"
                result["json_structure"] = {
                    "type": "object",
                    "keys": list(json_data.keys()) if isinstance(json_data, dict) else []
                }
                return result
            except:
                pass
        
        # CSV/TSV
        if '\n' in text:
            lines = text.strip().split('\n')
            if len(lines) > 1:
                first_line = lines[0]
                delimiters = {',': 0, '\t': 0, ';': 0, '|': 0}
                
                for delimiter, count in delimiters.items():
                    delimiters[delimiter] = first_line.count(delimiter)
                
                most_common = max(delimiters.items(), key=lambda x: x[1])
                if most_common[1] > 0:
                    result["format"] = "csv"
                    result["delimiter"] = most_common[0]
                    result["possible_header"] = first_line
                    result["row_count"] = len(lines)
                    return result
        
        # Markdown or similar
        if '# ' in text or '## ' in text:
            # Count headings
            headings = {
                "h1": len(re.findall(r'^# .*$', text, re.MULTILINE)),
                "h2": len(re.findall(r'^## .*$', text, re.MULTILINE)),
                "h3": len(re.findall(r'^### .*$', text, re.MULTILINE))
            }
            
            if sum(headings.values()) > 0:
                result["format"] = "markdown"
                result["headings"] = headings
                return result
        
        # No specific structure detected
        result["format"] = "plain_text"
        return result
    
    # === OCR Processing Methods ===
    
    def _process_image_with_ocr(self, image_content: Union[bytes, str, BinaryIO], 
                              lang: str = 'eng',
                              **kwargs) -> Dict[str, Any]:
        """
        Process an image with OCR to extract text.
        
        Args:
            image_content: Image content as bytes, file path, or file-like object
            lang: OCR language (default: English)
            kwargs: Additional OCR options
            
        Returns:
            Dictionary with OCR results
        """
        if not self.enable_ocr or not self._check_handler('ocr'):
            return {"error": "OCR functionality not enabled or available"}
        
        pytesseract = self.handlers['ocr']['library']
        Image = self.handlers['ocr']['image_library']
        temp_file = None
        
        try:
            # Load image based on input type
            if isinstance(image_content, bytes):
                img = Image.open(io.BytesIO(image_content))
            elif isinstance(image_content, str) and os.path.exists(image_content):
                img = Image.open(image_content)
            elif hasattr(image_content, 'read'):
                img = Image.open(image_content)
            else:
                return {"error": "Invalid image content format"}
            
            # Process image
            ocr_config = kwargs.get('config', '')
            
            # Extract text
            text = pytesseract.image_to_string(img, lang=lang, config=ocr_config)
            
            # Get additional data if requested
            data = {"text": text}
            
            if kwargs.get("get_boxes", False):
                # Get bounding boxes for words
                boxes = pytesseract.image_to_data(img, lang=lang, config=ocr_config)
                data["boxes"] = boxes
            
            if kwargs.get("get_hocr", False):
                # Get hOCR output (HTML representation with position info)
                hocr = pytesseract.image_to_pdf_or_hocr(img, extension='hocr', lang=lang, config=ocr_config)
                data["hocr"] = hocr
            
            return data
        except Exception as e:
            logger.error(f"Error processing image with OCR: {str(e)}")
            return {"error": f"OCR processing error: {str(e)}"}
        finally:
            # Clean up temporary file if created
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    # === Main Public Methods ===
    
    def load_document(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a document from file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with parsed document data
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # Determine document type
            doc_type = self._get_document_type(file_path)
            
            # Check if type is supported
            if doc_type == 'unknown':
                return {"error": f"Unsupported document type: {os.path.splitext(file_path)[1]}"}
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Select appropriate parser based on type
            if doc_type == 'pdf' and self._check_handler('pdf'):
                data = self._parse_pdf_with_pypdf2(content)
            elif doc_type == 'docx' and self._check_handler('docx'):
                data = self._parse_docx(content)
            elif doc_type == 'text':
                data = self._parse_text(content)
            else:
                return {"error": f"No handler available for document type: {doc_type}"}
            
            # Add file metadata
            data.update({
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path),
                "document_type": doc_type
            })
            
            return data
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            return {"error": f"Document loading error: {str(e)}"}
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text content from a document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text as string
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return f"Error: File not found: {file_path}"
            
            # Determine document type
            doc_type = self._get_document_type(file_path)
            
            # Check if type is supported
            if doc_type == 'unknown':
                return f"Error: Unsupported document type: {os.path.splitext(file_path)[1]}"
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Extract text based on document type
            if doc_type == 'pdf' and self._check_handler('pdf'):
                return self._extract_text_from_pdf(content)
            elif doc_type == 'docx' and self._check_handler('docx'):
                return self._extract_text_from_docx(content)
            elif doc_type == 'text':
                if isinstance(content, bytes):
                    return content.decode('utf-8', errors='replace')
                return content
            else:
                return f"Error: No text extraction handler available for document type: {doc_type}"
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return f"Error extracting text: {str(e)}"
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with document metadata
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # Determine document type
            doc_type = self._get_document_type(file_path)
            
            # Check if type is supported
            if doc_type == 'unknown':
                return {"error": f"Unsupported document type: {os.path.splitext(file_path)[1]}"}
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Extract metadata based on document type
            specific_metadata = {}
            if doc_type == 'pdf' and self._check_handler('pdf'):
                specific_metadata = self._get_pdf_metadata(content)
            elif doc_type == 'docx' and self._check_handler('docx'):
                specific_metadata = self._get_docx_metadata(content)
            elif doc_type == 'text':
                text_data = self._parse_text(content, extract_content=False)
                specific_metadata = {
                    "line_count": text_data.get("line_count", 0),
                    "character_count": text_data.get("character_count", 0),
                    "word_count": text_data.get("word_count", 0)
                }
            
            # Add file metadata
            metadata = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path),
                "document_type": doc_type,
                "created_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                "modified_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            }
            
            # Combine with specific metadata
            if isinstance(specific_metadata, dict) and "error" not in specific_metadata:
                metadata.update(specific_metadata)
            elif isinstance(specific_metadata, dict) and "error" in specific_metadata:
                metadata["extraction_error"] = specific_metadata["error"]
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            return {"error": f"Metadata extraction error: {str(e)}"}
    
    def process_documents_in_directory(self, directory_path: str, recursive: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Process all documents in a directory.
        
        Args:
            directory_path: Path to the directory
            recursive: Whether to process subdirectories
            
        Returns:
            Dictionary mapping file paths to document data
        """
        results = {}
        
        try:
            # Check if directory exists
            if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
                return {"error": f"Directory not found: {directory_path}"}
            
            # Collect files
            if recursive:
                for root, _, files in os.walk(directory_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        doc_type = self._get_document_type(file_path)
                        if doc_type != 'unknown':
                            results[file_path] = self.extract_metadata(file_path)
            else:
                with os.scandir(directory_path) as entries:
                    for entry in entries:
                        if entry.is_file():
                            doc_type = self._get_document_type(entry.path)
                            if doc_type != 'unknown':
                                results[entry.path] = self.extract_metadata(entry.path)
            
            return results
        except Exception as e:
            logger.error(f"Error processing documents in {directory_path}: {str(e)}")
            return {"error": f"Directory processing error: {str(e)}"}
    
    def convert_document(self, 
                        input_path: str, 
                        output_format: str,
                        output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert a document to another format.
        
        Args:
            input_path: Path to the input document
            output_format: Target format (text, pdf, docx)
            output_path: Optional path for the output file
            
        Returns:
            Dictionary with conversion result
        """
        try:
            # Check if input file exists
            if not os.path.exists(input_path):
                return {"error": f"Input file not found: {input_path}"}
            
            # Create default output path if not provided
            if not output_path:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}.{output_format.lower()}"
            
            # Determine source type
            source_type = self._get_document_type(input_path)
            if source_type == 'unknown':
                return {"error": f"Unsupported source document type: {os.path.splitext(input_path)[1]}"}
            
            # Extract text as common intermediate format
            text_content = self.extract_text(input_path)
            if text_content.startswith("Error:"):
                return {"error": text_content}
            
            # Convert to target format
            if output_format.lower() == 'text' or output_format.lower() == 'txt':
                # Write text directly
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                return {
                    "success": True,
                    "source_path": input_path,
                    "output_path": output_path,
                    "conversion": f"{source_type} to {output_format}"
                }
            
            elif output_format.lower() == 'docx':
                if not self._check_handler('docx'):
                    return {"error": "DOCX conversion not available - install python-docx"}
                
                # Create DOCX with the text content
                docx_content = {
                    "content": [
                        {"type": "paragraph", "text": paragraph.strip()}
                        for paragraph in text_content.split('\n\n')
                        if paragraph.strip()
                    ]
                }
                
                # Get metadata if possible
                metadata = self.extract_metadata(input_path)
                if isinstance(metadata, dict) and "error" not in metadata:
                    docx_content["metadata"] = {
                        "title": os.path.splitext(os.path.basename(input_path))[0],
                        "author": metadata.get("author", "Document Processor"),
                        "comments": f"Converted from {source_type} using OpenManus Document Processor"
                    }
                
                # Create the document
                result = self._create_docx(docx_content)
                if "error" in result:
                    return result
                
                # Copy to output path
                with open(output_path, 'wb') as f:
                    f.write(result["content"])
                
                # Clean up temp file
                if "temp_path" in result and os.path.exists(result["temp_path"]):
                    os.unlink(result["temp_path"])
                
                return {
                    "success": True,
                    "source_path": input_path,
                    "output_path": output_path,
                    "conversion": f"{source_type} to {output_format}"
                }
            
            # Add more conversion types as needed
            
            else:
                return {"error": f"Unsupported output format: {output_format}"}
            
        except Exception as e:
            logger.error(f"Error converting document {input_path}: {str(e)}")
            return {"error": f"Document conversion error: {str(e)}"}
    
    def extract_structured_data(self, file_path: str) -> Dict[str, Any]:
        """
        Extract structured data from a document (tables, forms, fields, etc.)
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with extracted structured data
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # Determine document type
            doc_type = self._get_document_type(file_path)
            
            # Check if type is supported
            if doc_type == 'unknown':
                return {"error": f"Unsupported document type: {os.path.splitext(file_path)[1]}"}
            
            structured_data = {
                "document_type": doc_type,
                "file_path": file_path,
                "tables": [],
                "forms": [],
                "fields": {}
            }
            
            # Extract data based on document type
            if doc_type == 'pdf' and self._check_handler('pdf'):
                # Simple table detection in PDF (placeholder)
                pdf_text = self.extract_text(file_path)
                
                # Look for tables based on character patterns
                table_sections = re.findall(r'([^\n]+\|[^\n]+\n)+([\s\S]+?)\n\n', pdf_text)
                for table_match in table_sections:
                    table_text = table_match[0] + table_match[1]
                    structured_data["tables"].append({
                        "text": table_text,
                        "format": "text",
                        "rows": table_text.count('\n') + 1
                    })
                
                # Field detection (simple key-value pattern)
                field_matches = re.findall(r'([A-Z][A-Za-z\s]+):\s+([^\n]+)', pdf_text)
                for key, value in field_matches:
                    structured_data["fields"][key.strip()] = value.strip()
                
            elif doc_type == 'docx' and self._check_handler('docx'):
                # Extract tables from DOCX
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                docx_data = self._parse_docx(content, extract_content=True)
                if "error" not in docx_data:
                    # Find tables in content
                    for item in docx_data.get("content", []):
                        if item.get("type") == "table":
                            structured_data["tables"].append({
                                "data": item.get("data", []),
                                "format": "array",
                                "rows": len(item.get("data", []))
                            })
            
            # If no structured data found
            if not any([
                structured_data["tables"], 
                structured_data["forms"], 
                structured_data["fields"]
            ]):
                structured_data["message"] = "No structured data detected in document"
            
            return structured_data
        except Exception as e:
            logger.error(f"Error extracting structured data from {file_path}: {str(e)}")
            return {"error": f"Structured data extraction error: {str(e)}"}
    
    # === Advanced Processing ===
    
    def search_in_document(self, file_path: str, query: str, context_size: int = 2) -> Dict[str, Any]:
        """
        Search for content in a document with context.
        
        Args:
            file_path: Path to the document file
            query: Search query
            context_size: Number of lines/paragraphs of context to include
            
        Returns:
            Dictionary with search results
        """
        try:
            # Extract text from document
            text = self.extract_text(file_path)
            if text.startswith("Error:"):
                return {"error": text}
            
            # Prepare results
            results = {
                "document": os.path.basename(file_path),
                "query": query,
                "matches": []
            }
            
            # Split text into paragraphs for context
            paragraphs = [p for p in text.split('\n\n') if p.strip()]
            
            # Search for query
            for i, paragraph in enumerate(paragraphs):
                if query.lower() in paragraph.lower():
                    # Get context paragraphs
                    start_idx = max(0, i - context_size)
                    end_idx = min(len(paragraphs), i + context_size + 1)
                    
                    # Extract context
                    context = paragraphs[start_idx:end_idx]
                    
                    # Highlight matches
                    highlighted = paragraph.replace(query, f"**{query}**")
                    
                    # Add to results
                    results["matches"].append({
                        "paragraph_index": i,
                        "match": highlighted,
                        "context": context
                    })
            
            # Add summary
            results["match_count"] = len(results["matches"])
            
            return results
        except Exception as e:
            logger.error(f"Error searching in document {file_path}: {str(e)}")
            return {"error": f"Document search error: {str(e)}"}
    
    def split_document(self, 
                      file_path: str, 
                      output_dir: str, 
                      split_type: str = 'pages',
                      segments: Optional[List[Union[int, Tuple[int, int]]]] = None) -> Dict[str, Any]:
        """
        Split a document into multiple parts.
        
        Args:
            file_path: Path to the document file
            output_dir: Directory for output files
            split_type: Type of split (pages, sections, etc.)
            segments: Optional list of page numbers or ranges
            
        Returns:
            Dictionary with split results
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine document type
            doc_type = self._get_document_type(file_path)
            
            # Check if splitting is supported for this document type
            if doc_type != 'pdf':
                return {"error": f"Document splitting not implemented for type: {doc_type}"}
            
            # Handle PDF splitting
            if doc_type == 'pdf' and self._check_handler('pdf'):
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Parse PDF to get page count
                pdf_data = self._parse_pdf_with_pypdf2(content, extract_pages=False)
                if "error" in pdf_data:
                    return {"error": pdf_data["error"]}
                
                page_count = pdf_data.get("page_count", 0)
                
                # Determine page ranges to split
                page_ranges = []
                if segments:
                    for segment in segments:
                        if isinstance(segment, tuple) and len(segment) == 2:
                            # Handle page range
                            start, end = segment
                            if 1 <= start <= page_count and start <= end <= page_count:
                                page_ranges.append((start, end))
                        elif isinstance(segment, int):
                            # Handle single page
                            if 1 <= segment <= page_count:
                                page_ranges.append((segment, segment))
                else:
                    # Default: Split into individual pages
                    page_ranges = [(i, i) for i in range(1, page_count + 1)]
                
                # Split PDF
                result_files = self._split_pdf(content, page_ranges)
                
                # Check for errors
                if result_files and isinstance(result_files[0], dict) and "error" in result_files[0]:
                    return result_files[0]
                
                # Save split files
                output_files = []
                for i, result in enumerate(result_files):
                    # Create output filename
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    range_str = result["range"].replace("-", "to")
                    output_name = f"{base_name}_pages_{range_str}.pdf"
                    output_path = os.path.join(output_dir, output_name)
                    
                    # Save the file
                    with open(output_path, 'wb') as f:
                        f.write(result["content"])
                    
                    output_files.append({
                        "path": output_path,
                        "pages": result["range"],
                        "page_count": result["page_count"]
                    })
                    
                    # Clean up temp file
                    if "temp_path" in result and os.path.exists(result["temp_path"]):
                        os.unlink(result["temp_path"])
                
                return {
                    "success": True,
                    "source_document": file_path,
                    "output_directory": output_dir,
                    "split_type": split_type,
                    "output_files": output_files
                }
            
            return {"error": "Document splitting not supported for this document type"}
        except Exception as e:
            logger.error(f"Error splitting document {file_path}: {str(e)}")
            return {"error": f"Document splitting error: {str(e)}"}
    
    def merge_documents(self, 
                       file_paths: List[str], 
                       output_path: str) -> Dict[str, Any]:
        """
        Merge multiple documents into one.
        
        Args:
            file_paths: List of paths to documents to merge
            output_path: Path for the merged document
            
        Returns:
            Dictionary with merge results
        """
        try:
            # Verify files exist
            missing_files = [path for path in file_paths if not os.path.exists(path)]
            if missing_files:
                return {"error": f"Files not found: {', '.join(missing_files)}"}
            
            # Check file types
            doc_types = [self._get_document_type(path) for path in file_paths]
            
            # Currently only support merging files of same type
            if len(set(doc_types)) > 1:
                return {"error": "Cannot merge documents of different types"}
            
            doc_type = doc_types[0]
            
            # Handle PDF merging
            if doc_type == 'pdf' and self._check_handler('pdf'):
                # Read all PDF content
                contents = []
                for path in file_paths:
                    with open(path, 'rb') as f:
                        contents.append(f.read())
                
                # Merge PDFs
                result = self._merge_pdfs(contents)
                
                if "error" in result:
                    return result
                
                # Save merged document
                with open(output_path, 'wb') as f:
                    f.write(result["content"])
                
                # Clean up temp file
                if "temp_path" in result and os.path.exists(result["temp_path"]):
                    os.unlink(result["temp_path"])
                
                return {
                    "success": True,
                    "source_documents": file_paths,
                    "output_path": output_path,
                    "document_type": doc_type,
                    "page_count": result.get("page_count", -1)
                }
            
            # Handle text merging
            elif doc_type == 'text':
                # Read all text content
                texts = []
                for path in file_paths:
                    with open(path, 'r', encoding='utf-8') as f:
                        texts.append(f.read())
                
                # Merge with separator
                merged_text = "\n\n--- Document Break ---\n\n".join(texts)
                
                # Write merged document
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(merged_text)
                
                return {
                    "success": True,
                    "source_documents": file_paths,
                    "output_path": output_path,
                    "document_type": doc_type
                }
            
            return {"error": f"Document merging not implemented for type: {doc_type}"}
        except Exception as e:
            logger.error(f"Error merging documents: {str(e)}")
            return {"error": f"Document merging error: {str(e)}"}
    
    def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        Perform advanced analysis on a document (structure, content types, etc.)
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with document analysis
        """
        try:
            # Load document
            doc_data = self.load_document(file_path)
            if "error" in doc_data:
                return doc_data
            
            # Extract text
            text = self.extract_text(file_path)
            if text.startswith("Error:"):
                doc_data["text_extraction_error"] = text
                text = ""
            
            # Perform basic analysis
            analysis = {
                "file_info": {
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "file_size": os.path.getsize(file_path),
                    "document_type": doc_data.get("document_type", "unknown")
                },
                "metadata": self.extract_metadata(file_path)
            }
            
            # Extract document structure
            if doc_data["document_type"] == "pdf":
                analysis["structure"] = {
                    "page_count": doc_data.get("page_count", 0),
                    "has_text": len(text.strip()) > 0,
                    "pages": []
                }
                
                # Basic page analysis
                for page in doc_data.get("pages", []):
                    page_text = page.get("text", "")
                    words = len(page_text.split())
                    
                    analysis["structure"]["pages"].append({
                        "page_number": page.get("page_number", 0),
                        "word_count": words,
                        "empty": words == 0
                    })
                
            elif doc_data["document_type"] == "docx":
                analysis["structure"] = {
                    "paragraphs": doc_data.get("paragraphs", 0),
                    "sections": doc_data.get("sections", 0),
                    "tables": doc_data.get("tables", 0),
                    "has_text": len(text.strip()) > 0
                }
            
            # Add text statistics
            if text:
                analysis["text_statistics"] = {
                    "character_count": len(text),
                    "word_count": len(text.split()),
                    "line_count": text.count('\n') + 1,
                    "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
                    "average_word_length": sum(len(word) for word in text.split()) / len(text.split()) if text.split() else 0,
                    "longest_paragraph": max(len(p) for p in text.split('\n\n') if p.strip()) if text.split('\n\n') else 0
                }
            
            # Find potential structured data
            analysis["structured_data"] = self.extract_structured_data(file_path)
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing document {file_path}: {str(e)}")
            return {"error": f"Document analysis error: {str(e)}"}