"""
Test suite for File Discovery Engine v2.0 - File Extraction Engine
Following Test-Driven Development approach - these tests are written first.

Tests the _extract_files_from_directories() method that extracts actual worklog files
from discovered directories and filters them by date range.

This builds on the directory scanner and date parsing utilities to complete
the directory-first discovery system.
"""

import pytest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import List, Tuple
import os

# Import the classes we'll be testing
from file_discovery import FileDiscovery, FileDiscoveryResult


class TestFileExtractionEngine:
    """Test suite for _extract_files_from_directories() method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery = FileDiscovery(base_path="~/Desktop/test_worklogs/")

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_single_directory_all_in_range(self, mock_is_file, mock_exists, mock_iterdir):
        """Test file extraction from single directory with all files in date range."""
        # Setup mock directory
        week_dir = Path("/test/week_ending_2024-04-15")
        directories = [(week_dir, date(2024, 4, 15))]
        
        # Mock files in the directory
        file1 = MagicMock()
        file1.name = "worklog_2024-04-15.txt"
        file1.is_file.return_value = True
        file1.suffix = ".txt"
        
        file2 = MagicMock()
        file2.name = "worklog_2024-04-16.txt"
        file2.is_file.return_value = True
        file2.suffix = ".txt"
        
        # Non-txt file should be ignored
        file3 = MagicMock()
        file3.name = "notes.md"
        file3.is_file.return_value = True
        file3.suffix = ".md"
        
        mock_iterdir.return_value = [file1, file2, file3]
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        # Test date range that includes both files
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 16)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should find both .txt files
        assert len(found_files) == 2
        assert len(missing_files) == 0
        
        # Verify files are the expected ones
        found_names = [f.name for f in found_files]
        assert "worklog_2024-04-15.txt" in found_names
        assert "worklog_2024-04-16.txt" in found_names

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_date_filtering(self, mock_is_file, mock_exists, mock_iterdir):
        """Test that files are properly filtered by date range."""
        week_dir = Path("/test/week_ending_2024-04-19")
        directories = [(week_dir, date(2024, 4, 19))]
        
        # Mock files with various dates
        file_before = MagicMock()
        file_before.name = "worklog_2024-04-10.txt"
        file_before.is_file.return_value = True
        file_before.suffix = ".txt"
        
        file_in_range1 = MagicMock()
        file_in_range1.name = "worklog_2024-04-15.txt"
        file_in_range1.is_file.return_value = True
        file_in_range1.suffix = ".txt"
        
        file_in_range2 = MagicMock()
        file_in_range2.name = "worklog_2024-04-17.txt"
        file_in_range2.is_file.return_value = True
        file_in_range2.suffix = ".txt"
        
        file_after = MagicMock()
        file_after.name = "worklog_2024-04-25.txt"
        file_after.is_file.return_value = True
        file_after.suffix = ".txt"
        
        mock_iterdir.return_value = [file_before, file_in_range1, file_in_range2, file_after]
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        # Test specific date range
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 20)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should only find files within the date range
        assert len(found_files) == 2
        found_names = [f.name for f in found_files]
        assert "worklog_2024-04-15.txt" in found_names
        assert "worklog_2024-04-17.txt" in found_names
        assert "worklog_2024-04-10.txt" not in found_names
        assert "worklog_2024-04-25.txt" not in found_names

    def test_extract_files_multiple_directories(self):
        """Test file extraction from multiple directories."""
        # Create mock directories
        week_dir1 = MagicMock(spec=Path)
        week_dir1.__str__ = lambda self: "/test/week_ending_2024-04-15"
        week_dir2 = MagicMock(spec=Path)
        week_dir2.__str__ = lambda self: "/test/week_ending_2024-04-22"
        
        directories = [
            (week_dir1, date(2024, 4, 15)),
            (week_dir2, date(2024, 4, 22))
        ]
        
        # Mock files for first directory
        file1_dir1 = MagicMock()
        file1_dir1.name = "worklog_2024-04-15.txt"
        file1_dir1.is_file.return_value = True
        file1_dir1.suffix = ".txt"
        
        file2_dir1 = MagicMock()
        file2_dir1.name = "worklog_2024-04-16.txt"
        file2_dir1.is_file.return_value = True
        file2_dir1.suffix = ".txt"
        
        # Mock files for second directory
        file1_dir2 = MagicMock()
        file1_dir2.name = "worklog_2024-04-22.txt"
        file1_dir2.is_file.return_value = True
        file1_dir2.suffix = ".txt"
        
        file2_dir2 = MagicMock()
        file2_dir2.name = "worklog_2024-04-23.txt"
        file2_dir2.is_file.return_value = True
        file2_dir2.suffix = ".txt"
        
        # Setup mock behavior
        week_dir1.exists.return_value = True
        week_dir2.exists.return_value = True
        week_dir1.iterdir.return_value = [file1_dir1, file2_dir1]
        week_dir2.iterdir.return_value = [file1_dir2, file2_dir2]
        
        # Test date range that includes files from both directories
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 23)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should find all files from both directories
        assert len(found_files) == 4
        found_names = [f.name for f in found_files]
        assert "worklog_2024-04-15.txt" in found_names
        assert "worklog_2024-04-16.txt" in found_names
        assert "worklog_2024-04-22.txt" in found_names
        assert "worklog_2024-04-23.txt" in found_names

    def test_extract_files_missing_files_tracking(self):
        """Test tracking of missing expected files."""
        # Create mock directory
        week_dir = MagicMock(spec=Path)
        week_dir.__str__ = lambda self: "/test/week_ending_2024-04-19"
        directories = [(week_dir, date(2024, 4, 19))]
        
        # Mock only some files exist
        existing_file = MagicMock()
        existing_file.name = "worklog_2024-04-15.txt"
        existing_file.is_file.return_value = True
        existing_file.suffix = ".txt"
        
        # Setup mock behavior
        week_dir.exists.return_value = True
        week_dir.iterdir.return_value = [existing_file]
        
        # Test date range that expects more files than exist
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 17)  # Expects 3 files but only 1 exists
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should find 1 file and track 2 missing
        assert len(found_files) == 1
        assert len(missing_files) == 2
        
        # Verify the found file
        assert found_files[0].name == "worklog_2024-04-15.txt"
        
        # Verify missing files are tracked
        missing_names = [f.name for f in missing_files]
        assert "worklog_2024-04-16.txt" in missing_names
        assert "worklog_2024-04-17.txt" in missing_names

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_invalid_filenames(self, mock_is_file, mock_exists, mock_iterdir):
        """Test handling of invalid filename formats."""
        week_dir = Path("/test/week_ending_2024-04-15")
        directories = [(week_dir, date(2024, 4, 15))]
        
        # Mock files with various formats
        valid_file = MagicMock()
        valid_file.name = "worklog_2024-04-15.txt"
        valid_file.is_file.return_value = True
        valid_file.suffix = ".txt"
        
        invalid_file1 = MagicMock()
        invalid_file1.name = "worklog_invalid_date.txt"
        invalid_file1.is_file.return_value = True
        invalid_file1.suffix = ".txt"
        
        invalid_file2 = MagicMock()
        invalid_file2.name = "not_worklog_2024-04-16.txt"
        invalid_file2.is_file.return_value = True
        invalid_file2.suffix = ".txt"
        
        non_txt_file = MagicMock()
        non_txt_file.name = "worklog_2024-04-17.log"
        non_txt_file.is_file.return_value = True
        non_txt_file.suffix = ".log"
        
        mock_iterdir.return_value = [valid_file, invalid_file1, invalid_file2, non_txt_file]
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 17)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should only find the valid file
        assert len(found_files) == 1
        assert found_files[0].name == "worklog_2024-04-15.txt"
        
        # Should track missing files for expected dates
        assert len(missing_files) == 2  # 2024-04-16 and 2024-04-17

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_file_system_errors(self, mock_is_file, mock_exists, mock_iterdir):
        """Test graceful handling of file system errors."""
        week_dir1 = Path("/test/week_ending_2024-04-15")
        week_dir2 = Path("/test/week_ending_2024-04-22")
        directories = [
            (week_dir1, date(2024, 4, 15)),
            (week_dir2, date(2024, 4, 22))
        ]
        
        # Mock first directory to work normally
        valid_file = MagicMock()
        valid_file.name = "worklog_2024-04-15.txt"
        valid_file.is_file.return_value = True
        valid_file.suffix = ".txt"
        
        # Mock second directory to raise PermissionError
        # Use a different approach - track calls and return appropriate values
        iterdir_calls = []
        
        def iterdir_side_effect():
            # Track which call this is based on the directory order
            call_index = len(iterdir_calls)
            iterdir_calls.append(call_index)
            
            if call_index == 0:  # First directory (week_ending_2024-04-15)
                return [valid_file]
            elif call_index == 1:  # Second directory (week_ending_2024-04-22)
                raise PermissionError("Access denied")
            return []
        
        mock_iterdir.side_effect = iterdir_side_effect
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 22)
        
        # Should handle the error gracefully
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should find file from accessible directory
        assert len(found_files) == 1
        assert found_files[0].name == "worklog_2024-04-15.txt"
        
        # Should track missing files from inaccessible directory
        assert len(missing_files) >= 1  # At least the expected file from 2024-04-22

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_empty_directories(self, mock_is_file, mock_exists, mock_iterdir):
        """Test handling of empty directories."""
        week_dir1 = Path("/test/week_ending_2024-04-15")
        week_dir2 = Path("/test/week_ending_2024-04-22")
        directories = [
            (week_dir1, date(2024, 4, 15)),
            (week_dir2, date(2024, 4, 22))
        ]
        
        # Mock first directory to have files
        valid_file = MagicMock()
        valid_file.name = "worklog_2024-04-15.txt"
        valid_file.is_file.return_value = True
        valid_file.suffix = ".txt"
        
        # Mock second directory to be empty
        iterdir_calls = []
        
        def iterdir_side_effect():
            call_index = len(iterdir_calls)
            iterdir_calls.append(call_index)
            
            if call_index == 0:  # First directory (week_ending_2024-04-15)
                return [valid_file]
            elif call_index == 1:  # Second directory (week_ending_2024-04-22)
                return []  # Empty directory
            return []
        
        mock_iterdir.side_effect = iterdir_side_effect
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 22)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should find file from non-empty directory
        assert len(found_files) == 1
        assert found_files[0].name == "worklog_2024-04-15.txt"
        
        # Should track missing files from empty directory
        missing_names = [f.name for f in missing_files]
        assert "worklog_2024-04-22.txt" in missing_names

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_cross_month_week(self, mock_is_file, mock_exists, mock_iterdir):
        """Test file extraction from cross-month week directories."""
        # Week ending May 3rd contains files from both April and May
        week_dir = Path("/test/week_ending_2024-05-03")
        directories = [(week_dir, date(2024, 5, 3))]
        
        # Mock files spanning month boundary
        april_file1 = MagicMock()
        april_file1.name = "worklog_2024-04-29.txt"
        april_file1.is_file.return_value = True
        april_file1.suffix = ".txt"
        
        april_file2 = MagicMock()
        april_file2.name = "worklog_2024-04-30.txt"
        april_file2.is_file.return_value = True
        april_file2.suffix = ".txt"
        
        may_file1 = MagicMock()
        may_file1.name = "worklog_2024-05-01.txt"
        may_file1.is_file.return_value = True
        may_file1.suffix = ".txt"
        
        may_file2 = MagicMock()
        may_file2.name = "worklog_2024-05-02.txt"
        may_file2.is_file.return_value = True
        may_file2.suffix = ".txt"
        
        may_file3 = MagicMock()
        may_file3.name = "worklog_2024-05-03.txt"
        may_file3.is_file.return_value = True
        may_file3.suffix = ".txt"
        
        mock_iterdir.return_value = [april_file1, april_file2, may_file1, may_file2, may_file3]
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        # Test range that includes the cross-month period
        start_date = date(2024, 4, 29)
        end_date = date(2024, 5, 3)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should find all files in the range
        assert len(found_files) == 5
        found_names = [f.name for f in found_files]
        assert "worklog_2024-04-29.txt" in found_names
        assert "worklog_2024-04-30.txt" in found_names
        assert "worklog_2024-05-01.txt" in found_names
        assert "worklog_2024-05-02.txt" in found_names
        assert "worklog_2024-05-03.txt" in found_names

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_leap_year_handling(self, mock_is_file, mock_exists, mock_iterdir):
        """Test file extraction with leap year dates."""
        week_dir = Path("/test/week_ending_2024-03-01")
        directories = [(week_dir, date(2024, 3, 1))]
        
        # Mock files including February 29, 2024 (leap year)
        feb28_file = MagicMock()
        feb28_file.name = "worklog_2024-02-28.txt"
        feb28_file.is_file.return_value = True
        feb28_file.suffix = ".txt"
        
        feb29_file = MagicMock()
        feb29_file.name = "worklog_2024-02-29.txt"  # Leap year day
        feb29_file.is_file.return_value = True
        feb29_file.suffix = ".txt"
        
        mar01_file = MagicMock()
        mar01_file.name = "worklog_2024-03-01.txt"
        mar01_file.is_file.return_value = True
        mar01_file.suffix = ".txt"
        
        mock_iterdir.return_value = [feb28_file, feb29_file, mar01_file]
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        # Test range that includes leap year day
        start_date = date(2024, 2, 28)
        end_date = date(2024, 3, 1)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should find all files including leap year day
        assert len(found_files) == 3
        found_names = [f.name for f in found_files]
        assert "worklog_2024-02-28.txt" in found_names
        assert "worklog_2024-02-29.txt" in found_names
        assert "worklog_2024-03-01.txt" in found_names

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_performance_large_directories(self, mock_is_file, mock_exists, mock_iterdir):
        """Test performance with large directories."""
        week_dir = Path("/test/week_ending_2024-04-30")
        directories = [(week_dir, date(2024, 4, 30))]
        
        # Mock a large number of files
        mock_files = []
        for day in range(1, 31):  # 30 files
            mock_file = MagicMock()
            mock_file.name = f"worklog_2024-04-{day:02d}.txt"
            mock_file.is_file.return_value = True
            mock_file.suffix = ".txt"
            mock_files.append(mock_file)
        
        mock_iterdir.return_value = mock_files
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        # Test with full month range
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 30)
        
        import time
        start_time = time.time()
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        end_time = time.time()
        
        # Should complete quickly even with many files
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should be fast
        
        # Should find all files
        assert len(found_files) == 30
        assert len(missing_files) == 0

    def test_extract_files_method_signature(self):
        """Test that the method has the correct signature."""
        # Verify method exists and has correct signature
        method = getattr(self.discovery, '_extract_files_from_directories', None)
        assert method is not None, "_extract_files_from_directories method should exist"
        
        # Test with minimal valid input to verify signature
        directories = [(Path("/test"), date(2024, 4, 15))]
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 15)
        
        # Should not raise TypeError for correct signature
        try:
            with patch('pathlib.Path.iterdir', return_value=[]):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('pathlib.Path.is_file', return_value=True):
                        result = self.discovery._extract_files_from_directories(
                            directories, start_date, end_date
                        )
                        assert isinstance(result, tuple)
                        assert len(result) == 2
                        assert isinstance(result[0], list)  # found_files
                        assert isinstance(result[1], list)  # missing_files
        except TypeError as e:
            pytest.fail(f"Method signature is incorrect: {e}")


class TestFileExtractionEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery = FileDiscovery(base_path="~/Desktop/test_worklogs/")

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_single_day_range(self, mock_is_file, mock_exists, mock_iterdir):
        """Test file extraction for single day range."""
        week_dir = Path("/test/week_ending_2024-04-15")
        directories = [(week_dir, date(2024, 4, 15))]
        
        target_file = MagicMock()
        target_file.name = "worklog_2024-04-15.txt"
        target_file.is_file.return_value = True
        target_file.suffix = ".txt"
        
        other_file = MagicMock()
        other_file.name = "worklog_2024-04-16.txt"
        other_file.is_file.return_value = True
        other_file.suffix = ".txt"
        
        mock_iterdir.return_value = [target_file, other_file]
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        # Single day range
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 15)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should find only the target file
        assert len(found_files) == 1
        assert found_files[0].name == "worklog_2024-04-15.txt"

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_no_directories(self, mock_is_file, mock_exists, mock_iterdir):
        """Test file extraction with empty directory list."""
        directories = []  # No directories
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 17)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should return empty lists
        assert len(found_files) == 0
        assert len(missing_files) == 0

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_mixed_file_types(self, mock_is_file, mock_exists, mock_iterdir):
        """Test handling of mixed file types in directories."""
        week_dir = Path("/test/week_ending_2024-04-15")
        directories = [(week_dir, date(2024, 4, 15))]
        
        # Mix of files and directories
        txt_file = MagicMock()
        txt_file.name = "worklog_2024-04-15.txt"
        txt_file.is_file.return_value = True
        txt_file.suffix = ".txt"
        
        subdirectory = MagicMock()
        subdirectory.name = "backup"
        subdirectory.is_file.return_value = False  # This is a directory
        
        log_file = MagicMock()
        log_file.name = "debug.log"
        log_file.is_file.return_value = True
        log_file.suffix = ".log"
        
        mock_iterdir.return_value = [txt_file, subdirectory, log_file]
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 15)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should only find .txt files, ignore directories and other file types
        assert len(found_files) == 1
        assert found_files[0].name == "worklog_2024-04-15.txt"

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_date_range_validation(self, mock_is_file, mock_exists, mock_iterdir):
        """Test that start_date <= end_date is handled correctly."""
        week_dir = Path("/test/week_ending_2024-04-15")
        directories = [(week_dir, date(2024, 4, 15))]
        
        target_file = MagicMock()
        target_file.name = "worklog_2024-04-15.txt"
        target_file.is_file.return_value = True
        target_file.suffix = ".txt"
        
        mock_iterdir.return_value = [target_file]
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        # Test with start_date > end_date (invalid range)
        start_date = date(2024, 4, 20)
        end_date = date(2024, 4, 15)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should handle gracefully (likely return empty results)
        assert isinstance(found_files, list)
        assert isinstance(missing_files, list)

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_files_comprehensive_scenario(self, mock_is_file, mock_exists, mock_iterdir):
        """Test comprehensive scenario with multiple directories and mixed conditions."""
        # Multiple week directories
        week_dir1 = Path("/test/week_ending_2024-04-15")
        week_dir2 = Path("/test/week_ending_2024-04-22")
        week_dir3 = Path("/test/week_ending_2024-04-29")
        directories = [
            (week_dir1, date(2024, 4, 15)),
            (week_dir2, date(2024, 4, 22)),
            (week_dir3, date(2024, 4, 29))
        ]
        
        # Files for first directory (all exist)
        file1_dir1 = MagicMock()
        file1_dir1.name = "worklog_2024-04-15.txt"
        file1_dir1.is_file.return_value = True
        file1_dir1.suffix = ".txt"
        
        file2_dir1 = MagicMock()
        file2_dir1.name = "worklog_2024-04-16.txt"
        file2_dir1.is_file.return_value = True
        file2_dir1.suffix = ".txt"
        
        # Files for second directory (mixed - some exist, some don't)
        file1_dir2 = MagicMock()
        file1_dir2.name = "worklog_2024-04-22.txt"
        file1_dir2.is_file.return_value = True
        file1_dir2.suffix = ".txt"
        
        # Third directory will be empty (no files)
        
        iterdir_calls = []
        
        def iterdir_side_effect():
            call_index = len(iterdir_calls)
            iterdir_calls.append(call_index)
            
            if call_index == 0:  # First directory (week_ending_2024-04-15)
                return [file1_dir1, file2_dir1]
            elif call_index == 1:  # Second directory (week_ending_2024-04-22)
                return [file1_dir2]
            elif call_index == 2:  # Third directory (week_ending_2024-04-29)
                return []  # Empty directory
            return []
        
        mock_iterdir.side_effect = iterdir_side_effect
        mock_is_file.return_value = True
        mock_exists.return_value = True
        
        # Test range that spans all directories
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 29)
        
        found_files, missing_files = self.discovery._extract_files_from_directories(
            directories, start_date, end_date
        )
        
        # Should find files from first two directories
        assert len(found_files) == 3
        found_names = [f.name for f in found_files]
        assert "worklog_2024-04-15.txt" in found_names
        assert "worklog_2024-04-16.txt" in found_names
        assert "worklog_2024-04-22.txt" in found_names
        
        # Should track missing files from all directories
        missing_names = [f.name for f in missing_files]
        expected_missing = [
            "worklog_2024-04-17.txt", "worklog_2024-04-18.txt", "worklog_2024-04-19.txt",
            "worklog_2024-04-20.txt", "worklog_2024-04-21.txt", "worklog_2024-04-23.txt",
            "worklog_2024-04-24.txt", "worklog_2024-04-25.txt", "worklog_2024-04-26.txt",
            "worklog_2024-04-27.txt", "worklog_2024-04-28.txt", "worklog_2024-04-29.txt"
        ]
        
        # Should have tracked missing files
        assert len(missing_files) >= 10  # At least most of the expected missing files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])