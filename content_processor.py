"""
Content Processing System for Work Journal Summarizer - Phase 3

This module implements robust content processing with encoding detection,
content sanitization, and comprehensive error handling. It processes journal
files discovered by the FileDiscovery system and prepares them for LLM analysis.

Key features:
- Automatic encoding detection using chardet
- Content sanitization and normalization
- File size limits and memory management
- Comprehensive error handling and recovery
- Processing statistics and performance tracking
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import chardet
import logging
import time
import re


@dataclass
class ProcessedContent:
    """
    Represents processed content from a single journal file.
    
    Contains the file content along with metadata about the processing
    operation, including statistics and any errors encountered.
    """
    file_path: Path
    date: date
    content: str
    word_count: int
    line_count: int
    encoding: str
    processing_time: float
    errors: List[str]


@dataclass
class ProcessingStats:
    """
    Statistics about the overall content processing operation.
    
    Provides comprehensive metrics about the processing performance,
    success rates, and aggregate statistics across all files.
    """
    total_files: int
    successful: int
    failed: int
    total_size_bytes: int
    total_words: int
    processing_time: float


class ContentProcessor:
    """
    Handles processing of journal files with encoding detection and content sanitization.
    
    This class provides robust file processing capabilities including:
    - Automatic encoding detection with fallback strategies
    - Content sanitization and normalization
    - File size validation and memory management
    - Comprehensive error handling and recovery
    - Performance tracking and statistics
    """
    
    def __init__(self, max_file_size_mb: int = 50):
        """
        Initialize ContentProcessor with configuration.
        
        Args:
            max_file_size_mb: Maximum file size in MB to process (default: 50MB)
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.logger = logging.getLogger(__name__)
    
    def process_files(self, file_paths: List[Path]) -> Tuple[List[ProcessedContent], ProcessingStats]:
        """
        Process all files and return content with comprehensive statistics.
        
        Files are processed in chronological order based on their filenames.
        Individual file failures do not stop the overall processing.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Tuple containing:
            - List of ProcessedContent objects for successfully processed files
            - ProcessingStats with comprehensive processing metrics
        """
        start_time = time.time()
        
        # Sort files chronologically based on filename
        sorted_files = self._sort_files_chronologically(file_paths)
        
        processed_content = []
        total_size_bytes = 0
        total_words = 0
        successful_count = 0
        failed_count = 0
        
        for file_path in sorted_files:
            try:
                # Process individual file
                content = self._process_single_file(file_path)
                
                if content:
                    processed_content.append(content)
                    total_size_bytes += file_path.stat().st_size if file_path.exists() else 0
                    total_words += content.word_count
                    successful_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to process file {file_path}: {e}")
                failed_count += 1
        
        processing_time = time.time() - start_time
        
        stats = ProcessingStats(
            total_files=len(file_paths),
            successful=successful_count,
            failed=failed_count,
            total_size_bytes=total_size_bytes,
            total_words=total_words,
            processing_time=processing_time
        )
        
        return processed_content, stats
    
    def _sort_files_chronologically(self, file_paths: List[Path]) -> List[Path]:
        """
        Sort files chronologically based on date in filename.
        
        Expects filenames in format: worklog_YYYY-MM-DD.txt
        
        Args:
            file_paths: List of file paths to sort
            
        Returns:
            List of file paths sorted chronologically
        """
        def extract_date(file_path: Path) -> date:
            """Extract date from filename for sorting."""
            try:
                # Extract date from filename like worklog_2024-04-15.txt
                filename = file_path.name
                date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
                if date_match:
                    year, month, day = map(int, date_match.groups())
                    return date(year, month, day)
                else:
                    # Fallback: use file modification time
                    return date.fromtimestamp(file_path.stat().st_mtime)
            except Exception:
                # Ultimate fallback: use epoch
                return date(1970, 1, 1)
        
        return sorted(file_paths, key=extract_date)
    
    def _process_single_file(self, file_path: Path) -> Optional[ProcessedContent]:
        """
        Process a single file with comprehensive error handling.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            ProcessedContent object if successful, None if failed
        """
        start_time = time.time()
        errors = []
        
        try:
            # Check if file exists
            if not file_path.exists():
                errors.append(f"File does not exist: {file_path}")
                return None
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size_bytes:
                errors.append(f"File too large: {file_size} bytes (max: {self.max_file_size_bytes})")
                return None
            
            if file_size == 0:
                errors.append("File is empty")
                return None
            
            # Detect encoding
            encoding = self._detect_encoding(file_path)
            if not encoding:
                errors.append("Could not detect file encoding")
                encoding = 'utf-8'  # Fallback
            
            # Read file content
            content = self._read_file_content(file_path, encoding)
            if not content:
                errors.append("File content is empty or unreadable")
                return None
            
            # Sanitize content
            sanitized_content = self._sanitize_content(content)
            
            # Validate content
            if not self._validate_content(sanitized_content):
                errors.append("Content validation failed - no meaningful content")
                return None
            
            # Calculate statistics
            word_count = len(sanitized_content.split())
            line_count = len([line for line in sanitized_content.split('\n') if line.strip()])
            
            # Extract date from filename
            file_date = self._extract_date_from_filename(file_path)
            
            processing_time = time.time() - start_time
            
            return ProcessedContent(
                file_path=file_path,
                date=file_date,
                content=sanitized_content,
                word_count=word_count,
                line_count=line_count,
                encoding=encoding,
                processing_time=processing_time,
                errors=errors
            )
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return None
    
    def _detect_encoding(self, file_path: Path) -> str:
        """
        Detect file encoding using chardet with fallback strategies.
        
        Fallback sequence: chardet detection → utf-8 → latin-1 → cp1252
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Detected encoding string
        """
        try:
            # Read a sample of the file for encoding detection
            with open(file_path, 'rb') as f:
                raw_data = f.read(min(32768, file_path.stat().st_size))  # Read up to 32KB
            
            # Use chardet for detection
            detection_result = chardet.detect(raw_data)
            
            if detection_result and detection_result['encoding']:
                confidence = detection_result.get('confidence', 0)
                if confidence > 0.7:  # High confidence threshold
                    return detection_result['encoding']
            
            # Fallback sequence
            fallback_encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in fallback_encodings:
                try:
                    raw_data.decode(encoding)
                    return encoding
                except UnicodeDecodeError:
                    continue
            
            # Ultimate fallback
            return 'utf-8'
            
        except Exception as e:
            self.logger.warning(f"Encoding detection failed for {file_path}: {e}")
            return 'utf-8'
    
    def _read_file_content(self, file_path: Path, encoding: str = None) -> str:
        """
        Read file content with proper encoding handling.
        
        Args:
            file_path: Path to the file to read
            encoding: Encoding to use (if None, will detect)
            
        Returns:
            File content as string
            
        Raises:
            IOError: If file cannot be read
            UnicodeDecodeError: If encoding is incorrect
        """
        if not encoding:
            encoding = self._detect_encoding(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with error replacement
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                return f.read()
    
    def _sanitize_content(self, content: str) -> str:
        """
        Clean and normalize content for LLM processing.
        
        Sanitization includes:
        - Normalize line endings to \n
        - Remove excessive whitespace (>2 consecutive blank lines)
        - Strip leading/trailing whitespace from lines
        - Preserve structure (headers, bullet points)
        
        Args:
            content: Raw content to sanitize
            
        Returns:
            Sanitized content string
        """
        if not content:
            return ""
        
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split into lines for processing
        lines = content.split('\n')
        
        # Process each line
        processed_lines = []
        consecutive_empty = 0
        
        for line in lines:
            # Strip trailing whitespace but preserve leading whitespace for structure
            cleaned_line = line.rstrip()
            
            # Track consecutive empty lines
            if not cleaned_line.strip():
                consecutive_empty += 1
                # Allow maximum 2 consecutive empty lines
                if consecutive_empty <= 2:
                    processed_lines.append(cleaned_line)
            else:
                consecutive_empty = 0
                processed_lines.append(cleaned_line)
        
        # Join lines back together
        sanitized = '\n'.join(processed_lines)
        
        # Remove leading and trailing whitespace from entire content
        sanitized = sanitized.strip()
        
        return sanitized
    
    def _validate_content(self, content: str) -> bool:
        """
        Validate content is meaningful (not empty/whitespace only).
        
        Args:
            content: Content to validate
            
        Returns:
            True if content is meaningful, False otherwise
        """
        if not content:
            return False
        
        # Check if content is only whitespace
        if not content.strip():
            return False
        
        # Check if content has meaningful text (at least some alphanumeric characters)
        alphanumeric_chars = sum(1 for char in content if char.isalnum())
        if alphanumeric_chars < 3:  # Require at least 3 alphanumeric characters
            return False
        
        return True
    
    def _extract_date_from_filename(self, file_path: Path) -> date:
        """
        Extract date from filename in format worklog_YYYY-MM-DD.txt.
        
        Args:
            file_path: Path to extract date from
            
        Returns:
            Date object extracted from filename
        """
        try:
            filename = file_path.name
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
            if date_match:
                year, month, day = map(int, date_match.groups())
                return date(year, month, day)
            else:
                # Fallback: use current date
                return date.today()
        except Exception:
            # Ultimate fallback
            return date.today()