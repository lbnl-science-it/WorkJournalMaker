#!/usr/bin/env python3
"""
Tests for Output Manager - Phase 6: Output Management System

Comprehensive test suite for the OutputManager class including filename generation,
markdown structure, metadata formatting, and file operations.

Author: Work Journal Summarizer Project
Version: Phase 6 - Output Management System
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from datetime import date, datetime
from dataclasses import dataclass
from typing import List

from output_manager import OutputManager, OutputResult, ProcessingMetadata


# Mock PeriodSummary for testing (since it's defined in summary_generator)
@dataclass
class MockPeriodSummary:
    """Mock PeriodSummary for testing purposes."""
    period_name: str
    start_date: date
    end_date: date
    projects: List[str]
    participants: List[str]
    tasks: List[str]
    themes: List[str]
    summary_text: str
    entry_count: int
    generation_time: float
    word_count: int


class TestOutputManager:
    """Test suite for OutputManager class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_manager = OutputManager(output_dir=self.temp_dir)
        
        # Sample test data
        self.sample_metadata = ProcessingMetadata(
            total_files_found=10,
            files_successfully_processed=8,
            files_with_errors=2,
            api_calls_made=8,
            successful_api_calls=7,
            failed_api_calls=1,
            unique_projects=5,
            unique_participants=12,
            total_tasks=25,
            major_themes=8,
            processing_duration=45.5
        )
        
        self.sample_summaries = [
            MockPeriodSummary(
                period_name="Week of April 1, 2024",
                start_date=date(2024, 4, 1),
                end_date=date(2024, 4, 7),
                projects=["Project Alpha", "Project Beta"],
                participants=["John Doe", "Jane Smith"],
                tasks=["Task 1", "Task 2", "Task 3"],
                themes=["Development", "Testing"],
                summary_text="This week focused on development activities with significant progress on Project Alpha.",
                entry_count=5,
                generation_time=2.5,
                word_count=150
            ),
            MockPeriodSummary(
                period_name="Week of April 8, 2024",
                start_date=date(2024, 4, 8),
                end_date=date(2024, 4, 14),
                projects=["Project Beta", "Project Gamma"],
                participants=["Jane Smith", "Bob Wilson"],
                tasks=["Task 4", "Task 5"],
                themes=["Testing", "Deployment"],
                summary_text="This week emphasized testing and deployment preparation for Project Beta.",
                entry_count=3,
                generation_time=1.8,
                word_count=120
            )
        ]
    
    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_filename_generation(self):
        """Test filename format and timestamp generation."""
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 30)
        summary_type = "weekly"
        
        with patch('output_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 6, 16, 12, 30, 45)
            mock_datetime.strftime = datetime.strftime
            
            filename = self.output_manager._generate_filename(summary_type, start_date, end_date)
            
            expected = "weekly_summary_2024-04-01_to_2024-04-30_20240616_123045.md"
            assert filename == expected
    
    def test_filename_generation_monthly(self):
        """Test filename generation for monthly summaries."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        summary_type = "monthly"
        
        with patch('output_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 6, 16, 9, 15, 30)
            mock_datetime.strftime = datetime.strftime
            
            filename = self.output_manager._generate_filename(summary_type, start_date, end_date)
            
            expected = "monthly_summary_2024-01-01_to_2024-12-31_20240616_091530.md"
            assert filename == expected
    
    def test_header_formatting(self):
        """Test header section formatting."""
        summary_type = "weekly"
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 30)
        
        with patch('output_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 6, 16, 14, 30, 0)
            mock_datetime.strftime = datetime.strftime
            
            header = self.output_manager._format_header_section(
                summary_type, start_date, end_date, self.sample_metadata
            )
            
            assert "# Weekly Summary: April 01, 2024 to April 30, 2024" in header
            assert "**Generated on:** June 16, 2024 at 02:30 PM" in header
            assert "**Date Range:** April 01, 2024 to April 30, 2024" in header
            assert "**Total Files Processed:** 8" in header
            assert "---" in header
    
    def test_summary_section_formatting(self):
        """Test summary sections formatting."""
        sections = self.output_manager._format_summary_sections(self.sample_summaries)
        
        # Check for proper section headers
        assert "## Week of April 1, 2024" in sections
        assert "## Week of April 8, 2024" in sections
        
        # Check for metadata
        assert "**Date Range:** April 01, 2024 to April 07, 2024" in sections
        assert "**Journal Entries:** 5" in sections
        assert "**Word Count:** 150" in sections
        
        # Check for entity lists
        assert "**Projects:**" in sections
        assert "- Project Alpha" in sections
        assert "- Project Beta" in sections
        
        assert "**Key Participants:**" in sections
        assert "- John Doe" in sections
        assert "- Jane Smith" in sections
        
        assert "**Major Themes:**" in sections
        assert "- Development" in sections
        assert "- Testing" in sections
        
        # Check for summary text
        assert "### Summary" in sections
        assert "This week focused on development activities" in sections
    
    def test_summary_section_formatting_empty(self):
        """Test summary sections formatting with empty summaries list."""
        sections = self.output_manager._format_summary_sections([])
        
        assert "## No Summaries Generated" in sections
        assert "No journal entries were found or processed" in sections
    
    def test_summary_section_formatting_large_lists(self):
        """Test summary sections formatting with large entity lists."""
        # Create a summary with many entities
        large_summary = MockPeriodSummary(
            period_name="Week of April 1, 2024",
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 7),
            projects=[f"Project {i}" for i in range(15)],  # 15 projects
            participants=[f"Person {i}" for i in range(12)],  # 12 participants
            tasks=[f"Task {i}" for i in range(8)],
            themes=[f"Theme {i}" for i in range(6)],
            summary_text="Test summary with many entities.",
            entry_count=5,
            generation_time=2.5,
            word_count=150
        )
        
        sections = self.output_manager._format_summary_sections([large_summary])
        
        # Should show first 10 projects and indicate more
        assert "- Project 0" in sections
        assert "- Project 9" in sections
        assert "...and 5 more projects" in sections
        
        # Should show first 10 participants and indicate more
        assert "- Person 0" in sections
        assert "- Person 9" in sections
        assert "...and 2 more participants" in sections
    
    def test_processing_notes_formatting(self):
        """Test processing notes formatting."""
        notes = self.output_manager._format_processing_notes(self.sample_metadata)
        
        # Check for main sections
        assert "## Processing Notes" in notes
        assert "### Files Processed" in notes
        assert "### API Usage Statistics" in notes
        assert "### Entities Extracted" in notes
        assert "### Processing Performance" in notes
        assert "### Issues Encountered" in notes
        
        # Check for specific values
        assert "**Total files found:** 10" in notes
        assert "**Files successfully processed:** 8" in notes
        assert "**Files with errors:** 2" in notes
        assert "**Total API calls made:** 8" in notes
        assert "**Successful calls:** 7" in notes
        assert "**Failed calls:** 1" in notes
        assert "**Unique projects identified:** 5" in notes
        assert "**Unique participants identified:** 12" in notes
        assert "**Total tasks extracted:** 25" in notes
        assert "**Major themes identified:** 8" in notes
        assert "**Total processing time:** 45.50 seconds" in notes
        
        # Check for calculated metrics
        assert "**Files per second:** 0.18" in notes  # 8/45.5
        assert "**Average response time:** 5.69s" in notes  # 45.5/8
        
        # Check for issues
        assert "- 2 files had processing errors" in notes
        assert "- 1 API calls failed" in notes
        
        # Check for footer
        assert "*Generated by Work Journal Summarizer v6.0*" in notes
    
    def test_processing_notes_formatting_no_issues(self):
        """Test processing notes formatting with no issues."""
        clean_metadata = ProcessingMetadata(
            total_files_found=5,
            files_successfully_processed=5,
            files_with_errors=0,
            api_calls_made=5,
            successful_api_calls=5,
            failed_api_calls=0,
            unique_projects=3,
            unique_participants=8,
            total_tasks=15,
            major_themes=5,
            processing_duration=20.0
        )
        
        notes = self.output_manager._format_processing_notes(clean_metadata)
        
        assert "- No significant issues encountered during processing" in notes
    
    def test_markdown_validation(self):
        """Test markdown syntax validation."""
        # Valid markdown content
        valid_content = """# Main Header

## Section Header

Some content here.

### Subsection

More content.

## Processing Notes

Final section.
"""
        
        assert self.output_manager._validate_markdown(valid_content) is True
    
    def test_markdown_validation_missing_header(self):
        """Test markdown validation with missing main header."""
        invalid_content = """## Section Header

Some content without main header.
"""
        
        assert self.output_manager._validate_markdown(invalid_content) is False
    
    def test_markdown_validation_missing_processing_notes(self):
        """Test markdown validation with missing processing notes."""
        invalid_content = """# Main Header

## Some Section

Content without processing notes.
"""
        
        assert self.output_manager._validate_markdown(invalid_content) is False
    
    def test_markdown_validation_too_short(self):
        """Test markdown validation with content too short."""
        short_content = "# Header"
        
        assert self.output_manager._validate_markdown(short_content) is False
    
    @patch('pathlib.Path.mkdir')
    def test_ensure_output_directory(self, mock_mkdir):
        """Test output directory creation."""
        self.output_manager._ensure_output_directory()
        
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    @patch('pathlib.Path.mkdir')
    def test_ensure_output_directory_error(self, mock_mkdir):
        """Test output directory creation with error."""
        mock_mkdir.side_effect = OSError("Permission denied")
        
        with pytest.raises(OSError, match="Cannot create output directory"):
            self.output_manager._ensure_output_directory()
    
    def test_generate_output_success(self):
        """Test successful output generation."""
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 30)
        summary_type = "weekly"
        
        result = self.output_manager.generate_output(
            self.sample_summaries, summary_type, start_date, end_date, self.sample_metadata
        )
        
        # Check result properties
        assert isinstance(result, OutputResult)
        assert result.output_path.exists()
        assert result.file_size_bytes > 0
        assert result.generation_time > 0
        assert result.sections_count > 0
        assert result.metadata_included is True
        assert result.validation_passed is True
        
        # Check file content
        content = result.output_path.read_text(encoding='utf-8')
        assert "# Weekly Summary:" in content
        assert "## Week of April 1, 2024" in content
        assert "## Processing Notes" in content
        assert "Project Alpha" in content
        assert "John Doe" in content
    
    def test_generate_output_empty_summaries(self):
        """Test output generation with empty summaries."""
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 30)
        summary_type = "monthly"
        
        result = self.output_manager.generate_output(
            [], summary_type, start_date, end_date, self.sample_metadata
        )
        
        assert result.output_path.exists()
        
        content = result.output_path.read_text(encoding='utf-8')
        assert "# Monthly Summary:" in content
        assert "## No Summaries Generated" in content
        assert "## Processing Notes" in content
    
    @patch('builtins.open', side_effect=OSError("Permission denied"))
    def test_generate_output_file_write_error(self, mock_open):
        """Test output generation with file write error."""
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 30)
        summary_type = "weekly"
        
        with pytest.raises(OSError):
            self.output_manager.generate_output(
                self.sample_summaries, summary_type, start_date, end_date, self.sample_metadata
            )
    
    def test_complete_markdown_structure(self):
        """Test complete markdown structure generation."""
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 30)
        summary_type = "weekly"
        
        content = self.output_manager._create_markdown_content(
            self.sample_summaries, summary_type, start_date, end_date, self.sample_metadata
        )
        
        # Check overall structure
        lines = content.split('\n')
        
        # Should have main header
        main_headers = [line for line in lines if line.startswith('# ')]
        assert len(main_headers) == 1
        assert "Weekly Summary:" in main_headers[0]
        
        # Should have section headers
        section_headers = [line for line in lines if line.startswith('## ')]
        assert len(section_headers) >= 3  # At least summary sections + Processing Notes
        
        # Should have subsection headers
        subsection_headers = [line for line in lines if line.startswith('### ')]
        assert len(subsection_headers) >= 2  # At least Key Information + Summary per period
        
        # Check for required content
        assert "**Generated on:**" in content
        assert "**Date Range:**" in content
        assert "**Total Files Processed:**" in content
        assert "Project Alpha" in content
        assert "John Doe" in content
        assert "This week focused on development activities" in content
        assert "Files Processed" in content
        assert "API Usage Statistics" in content
        assert "Entities Extracted" in content
        assert "Processing Performance" in content
        assert "Issues Encountered" in content
        assert "*Generated by Work Journal Summarizer v6.0*" in content


class TestProcessingMetadata:
    """Test suite for ProcessingMetadata dataclass."""
    
    def test_processing_metadata_creation(self):
        """Test ProcessingMetadata creation and attributes."""
        metadata = ProcessingMetadata(
            total_files_found=20,
            files_successfully_processed=18,
            files_with_errors=2,
            api_calls_made=18,
            successful_api_calls=17,
            failed_api_calls=1,
            unique_projects=8,
            unique_participants=15,
            total_tasks=45,
            major_themes=12,
            processing_duration=120.5
        )
        
        assert metadata.total_files_found == 20
        assert metadata.files_successfully_processed == 18
        assert metadata.files_with_errors == 2
        assert metadata.api_calls_made == 18
        assert metadata.successful_api_calls == 17
        assert metadata.failed_api_calls == 1
        assert metadata.unique_projects == 8
        assert metadata.unique_participants == 15
        assert metadata.total_tasks == 45
        assert metadata.major_themes == 12
        assert metadata.processing_duration == 120.5


class TestOutputResult:
    """Test suite for OutputResult dataclass."""
    
    def test_output_result_creation(self):
        """Test OutputResult creation and attributes."""
        output_path = Path("/tmp/test_output.md")
        
        result = OutputResult(
            output_path=output_path,
            file_size_bytes=1024,
            generation_time=2.5,
            sections_count=5,
            metadata_included=True,
            validation_passed=True
        )
        
        assert result.output_path == output_path
        assert result.file_size_bytes == 1024
        assert result.generation_time == 2.5
        assert result.sections_count == 5
        assert result.metadata_included is True
        assert result.validation_passed is True