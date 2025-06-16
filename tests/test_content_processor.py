"""
Test suite for Content Processing System - Phase 3

This module provides comprehensive tests for the ContentProcessor class,
including encoding detection, content sanitization, error handling,
and performance validation.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
from datetime import date

# Import the modules we'll be testing
from content_processor import ContentProcessor, ProcessedContent, ProcessingStats


class TestContentProcessor:
    """Test suite for ContentProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.processor = ContentProcessor(max_file_size_mb=50)
        self.test_date = date(2024, 4, 15)
    
    def test_encoding_detection_utf8(self):
        """Test UTF-8 encoding detection."""
        test_content = "Hello, world! 🌍"
        utf8_bytes = test_content.encode('utf-8')
        
        with patch('builtins.open', mock_open(read_data=utf8_bytes)):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = len(utf8_bytes)
                encoding = self.processor._detect_encoding(Path("test.txt"))
                assert encoding == 'utf-8'
    
    def test_encoding_detection_latin1(self):
        """Test Latin-1 encoding detection."""
        test_content = "Café résumé"
        latin1_bytes = test_content.encode('latin-1')
        
        with patch('chardet.detect') as mock_detect:
            mock_detect.return_value = {'encoding': 'latin-1', 'confidence': 0.8}
            with patch('builtins.open', mock_open(read_data=latin1_bytes)):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_size = len(latin1_bytes)
                    encoding = self.processor._detect_encoding(Path("test.txt"))
                    assert encoding == 'latin-1'
    
    def test_encoding_detection_fallback(self):
        """Test encoding detection fallback sequence."""
        with patch('chardet.detect') as mock_detect:
            mock_detect.return_value = {'encoding': None, 'confidence': 0.0}
            with patch('builtins.open', mock_open(read_data=b'test')):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_size = 4
                    encoding = self.processor._detect_encoding(Path("test.txt"))
                    assert encoding == 'utf-8'  # Should fallback to utf-8
    
    def test_content_sanitization_whitespace(self):
        """Test whitespace removal and normalization."""
        test_content = """
        
        
        Line 1 with trailing spaces   
        
        
        
        Line 2 with tabs\t\t
        
        
        Line 3 normal
        
        
        
        """
        
        sanitized = self.processor._sanitize_content(test_content)
        lines = sanitized.split('\n')
        
        # Should remove excessive blank lines (>2 consecutive)
        consecutive_blanks = 0
        max_consecutive = 0
        for line in lines:
            if line.strip() == '':
                consecutive_blanks += 1
                max_consecutive = max(max_consecutive, consecutive_blanks)
            else:
                consecutive_blanks = 0
        
        assert max_consecutive <= 2
        assert 'Line 1 with trailing spaces' in sanitized
        assert 'Line 2 with tabs' in sanitized
        assert 'Line 3 normal' in sanitized
    
    def test_content_sanitization_line_endings(self):
        """Test line ending normalization."""
        test_content = "Line 1\r\nLine 2\rLine 3\nLine 4"
        sanitized = self.processor._sanitize_content(test_content)
        
        # All line endings should be normalized to \n
        assert '\r\n' not in sanitized
        assert '\r' not in sanitized
        assert sanitized.count('\n') == 3
    
    def test_content_validation_meaningful(self):
        """Test validation of meaningful content."""
        meaningful_content = "This is a meaningful work journal entry with actual content."
        assert self.processor._validate_content(meaningful_content) is True
    
    def test_content_validation_empty(self):
        """Test validation of empty content."""
        empty_content = ""
        assert self.processor._validate_content(empty_content) is False
    
    def test_content_validation_whitespace_only(self):
        """Test validation of whitespace-only content."""
        whitespace_content = "   \n\t\n   \n\t\t   "
        assert self.processor._validate_content(whitespace_content) is False
    
    def test_empty_file_handling(self):
        """Test handling of empty files."""
        empty_files = [Path("empty1.txt"), Path("empty2.txt")]
        
        with patch.object(self.processor, '_read_file_content') as mock_read:
            mock_read.return_value = ""
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 0
                
                results, stats = self.processor.process_files(empty_files)
                
                assert len(results) == 0  # Empty files should be filtered out
                assert stats.failed == 2
                assert stats.successful == 0
    
    def test_large_file_handling(self):
        """Test file size limits and memory management."""
        large_file = Path("large_file.txt")
        
        with patch('pathlib.Path.stat') as mock_stat:
            # Simulate file larger than max_file_size_mb (50MB)
            mock_stat.return_value.st_size = 60 * 1024 * 1024  # 60MB
            
            results, stats = self.processor.process_files([large_file])
            
            assert len(results) == 0
            assert stats.failed == 1
            assert "File too large" in str(results) or stats.failed > 0
    
    def test_corrupted_file_handling(self):
        """Test handling of binary/corrupted files."""
        corrupted_file = Path("corrupted.txt")
        
        with patch.object(self.processor, '_read_file_content') as mock_read:
            mock_read.side_effect = UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 100
                
                results, stats = self.processor.process_files([corrupted_file])
                
                assert len(results) == 0
                assert stats.failed == 1
    
    @patch('builtins.open', new_callable=mock_open)
    def test_permission_errors(self, mock_file):
        """Test permission denied scenarios."""
        mock_file.side_effect = PermissionError("Permission denied")
        
        protected_file = Path("protected.txt")
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 100
            
            results, stats = self.processor.process_files([protected_file])
            
            assert len(results) == 0
            assert stats.failed == 1
    
    def test_processing_statistics_accuracy(self):
        """Test accurate statistics generation."""
        # Create mock files with different outcomes
        files = [
            Path("success1.txt"),
            Path("success2.txt"),
            Path("fail1.txt"),
            Path("fail2.txt")
        ]
        
        def mock_read_side_effect(file_path, encoding=None):
            if "success" in str(file_path):
                return "Valid content for processing"
            else:
                raise IOError("File read error")
        
        with patch.object(self.processor, '_read_file_content', side_effect=mock_read_side_effect):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_size = 100
                    
                    results, stats = self.processor.process_files(files)
                    
                    assert stats.total_files == 4
                    assert stats.successful == 2
                    assert stats.failed == 2
                    assert len(results) == 2
                    assert stats.total_words > 0
    
    def test_processed_content_structure(self):
        """Test ProcessedContent dataclass structure."""
        test_file = Path("test.txt")
        test_content = "This is test content for validation."
        
        with patch.object(self.processor, '_read_file_content', return_value=test_content):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = len(test_content)
                
                results, stats = self.processor.process_files([test_file])
                
                assert len(results) == 1
                result = results[0]
                
                assert isinstance(result, ProcessedContent)
                assert result.file_path == test_file
                assert result.content == test_content
                assert result.word_count > 0
                assert result.line_count > 0
                assert result.encoding is not None
                assert result.processing_time >= 0
                assert isinstance(result.errors, list)
    
    def test_word_count_calculation(self):
        """Test word count calculation accuracy."""
        test_content = "This is a test sentence with exactly ten words here."
        
        with patch.object(self.processor, '_read_file_content', return_value=test_content):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = len(test_content)
                
                results, stats = self.processor.process_files([Path("test.txt")])
                
                assert len(results) == 1
                # Should count 10 words
                assert results[0].word_count == 10
    
    def test_line_count_calculation(self):
        """Test line count calculation accuracy."""
        test_content = "Line 1\nLine 2\nLine 3\n"
        
        with patch.object(self.processor, '_read_file_content', return_value=test_content):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = len(test_content)
                
                results, stats = self.processor.process_files([Path("test.txt")])
                
                assert len(results) == 1
                # Should count 3 lines (excluding final empty line)
                assert results[0].line_count == 3
    
    def test_chronological_ordering(self):
        """Test that files are processed in chronological order."""
        files = [
            Path("worklog_2024-04-03.txt"),
            Path("worklog_2024-04-01.txt"),
            Path("worklog_2024-04-02.txt")
        ]
        
        with patch.object(self.processor, '_read_file_content', return_value="test content"):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 100
                
                results, stats = self.processor.process_files(files)
                
                # Results should be in chronological order
                assert len(results) == 3
                assert "2024-04-01" in str(results[0].file_path)
                assert "2024-04-02" in str(results[1].file_path)
                assert "2024-04-03" in str(results[2].file_path)
    
    def test_error_accumulation(self):
        """Test that errors are properly accumulated in ProcessedContent."""
        test_file = Path("test.txt")
        
        # Mock a scenario where encoding detection has issues but processing continues
        with patch.object(self.processor, '_detect_encoding', return_value='utf-8'):
            with patch.object(self.processor, '_read_file_content', return_value="test content"):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_size = 100
                    
                    results, stats = self.processor.process_files([test_file])
                    
                    assert len(results) == 1
                    assert isinstance(results[0].errors, list)
    
    def test_performance_with_multiple_files(self):
        """Test processing performance with multiple files."""
        # Create 10 mock files
        files = [Path(f"test_{i}.txt") for i in range(10)]
        
        with patch.object(self.processor, '_read_file_content', return_value="test content"):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 100
                
                results, stats = self.processor.process_files(files)
                
                assert len(results) == 10
                assert stats.total_files == 10
                assert stats.successful == 10
                assert stats.failed == 0
                assert stats.processing_time > 0
                
                # Performance check: should process reasonably quickly
                assert stats.processing_time < 5.0  # Should complete within 5 seconds


class TestProcessingStats:
    """Test suite for ProcessingStats dataclass."""
    
    def test_processing_stats_structure(self):
        """Test ProcessingStats dataclass structure."""
        stats = ProcessingStats(
            total_files=10,
            successful=8,
            failed=2,
            total_size_bytes=1024,
            total_words=500,
            processing_time=1.5
        )
        
        assert stats.total_files == 10
        assert stats.successful == 8
        assert stats.failed == 2
        assert stats.total_size_bytes == 1024
        assert stats.total_words == 500
        assert stats.processing_time == 1.5


class TestProcessedContent:
    """Test suite for ProcessedContent dataclass."""
    
    def test_processed_content_structure(self):
        """Test ProcessedContent dataclass structure."""
        test_path = Path("test.txt")
        test_date = date(2024, 4, 15)
        
        content = ProcessedContent(
            file_path=test_path,
            date=test_date,
            content="Test content",
            word_count=2,
            line_count=1,
            encoding="utf-8",
            processing_time=0.1,
            errors=[]
        )
        
        assert content.file_path == test_path
        assert content.date == test_date
        assert content.content == "Test content"
        assert content.word_count == 2
        assert content.line_count == 1
        assert content.encoding == "utf-8"
        assert content.processing_time == 0.1
        assert content.errors == []