"""
Comprehensive test suite for File Discovery Engine v2.0 - Directory Scanner Core.
Following Test-Driven Development approach - these tests are written first.

Tests the _discover_week_ending_directories() method that implements directory-first discovery
to replace the flawed date calculation approach.

File structure: /Users/TYFong/Desktop/worklogs/worklogs_YYYY/worklogs_YYYY-MM/week_ending_YYYY-MM-DD/worklog_YYYY-MM-DD.txt
"""

import pytest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import os
from typing import List, Tuple

# Import the classes we'll be testing
from file_discovery import FileDiscovery, FileDiscoveryResult


class TestDirectoryScanner:
    """Test suite for _discover_week_ending_directories() method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery = FileDiscovery(base_path="~/Desktop/test_worklogs/")

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_week_ending_directories_single_month(self, mock_iterdir, mock_exists):
        """Test directory discovery within a single month."""
        # Setup mock directory structure
        mock_exists.return_value = True
        
        # Mock year directory
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        # Mock month directory
        month_dir = MagicMock()
        month_dir.name = "worklogs_2024-04"
        month_dir.is_dir.return_value = True
        
        # Mock week directories
        week_dir1 = MagicMock()
        week_dir1.name = "week_ending_2024-04-15"
        week_dir1.is_dir.return_value = True
        
        week_dir2 = MagicMock()
        week_dir2.name = "week_ending_2024-04-19"
        week_dir2.is_dir.return_value = True
        
        # Set up iterdir on individual mock objects
        year_dir.iterdir.return_value = [month_dir]
        month_dir.iterdir.return_value = [week_dir1, week_dir2]
        
        # Setup base path iterdir to return year directories
        mock_iterdir.return_value = [year_dir]
        
        # Test date range within April 2024
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 19)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should find both week directories
        assert len(result) == 2
        assert result[0][1] == date(2024, 4, 15)  # First week ending date
        assert result[1][1] == date(2024, 4, 19)  # Second week ending date
        
        # Results should be sorted chronologically
        assert result[0][1] <= result[1][1]

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_week_ending_directories_cross_month(self, mock_iterdir, mock_exists):
        """Test directory discovery across month boundaries."""
        mock_exists.return_value = True
        
        # Mock directory structure for April and May 2024
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        april_dir = MagicMock()
        april_dir.name = "worklogs_2024-04"
        april_dir.is_dir.return_value = True
        
        may_dir = MagicMock()
        may_dir.name = "worklogs_2024-05"
        may_dir.is_dir.return_value = True
        
        # Week directories
        april_week = MagicMock()
        april_week.name = "week_ending_2024-04-30"
        april_week.is_dir.return_value = True
        
        may_week = MagicMock()
        may_week.name = "week_ending_2024-05-03"
        may_week.is_dir.return_value = True
        
        # Set up iterdir on individual mock objects
        year_dir.iterdir.return_value = [april_dir, may_dir]
        april_dir.iterdir.return_value = [april_week]
        may_dir.iterdir.return_value = [may_week]
        
        # Setup base path iterdir to return year directories
        mock_iterdir.return_value = [year_dir]
        
        # Test cross-month range
        start_date = date(2024, 4, 29)
        end_date = date(2024, 5, 3)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should find both week directories
        assert len(result) == 2
        dates = [r[1] for r in result]
        assert date(2024, 4, 30) in dates
        assert date(2024, 5, 3) in dates

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_week_ending_directories_cross_year(self, mock_iterdir, mock_exists):
        """Test directory discovery across year boundaries."""
        mock_exists.return_value = True
        
        # Mock directory structure for 2024 and 2025
        year_2024 = MagicMock()
        year_2024.name = "worklogs_2024"
        year_2024.is_dir.return_value = True
        
        year_2025 = MagicMock()
        year_2025.name = "worklogs_2025"
        year_2025.is_dir.return_value = True
        
        dec_2024 = MagicMock()
        dec_2024.name = "worklogs_2024-12"
        dec_2024.is_dir.return_value = True
        
        jan_2025 = MagicMock()
        jan_2025.name = "worklogs_2025-01"
        jan_2025.is_dir.return_value = True
        
        # Week directories
        dec_week = MagicMock()
        dec_week.name = "week_ending_2024-12-31"
        dec_week.is_dir.return_value = True
        
        jan_week = MagicMock()
        jan_week.name = "week_ending_2025-01-03"
        jan_week.is_dir.return_value = True
        
        # Set up iterdir on individual mock objects
        year_2024.iterdir.return_value = [dec_2024]
        year_2025.iterdir.return_value = [jan_2025]
        dec_2024.iterdir.return_value = [dec_week]
        jan_2025.iterdir.return_value = [jan_week]
        
        # Setup base path iterdir to return year directories
        mock_iterdir.return_value = [year_2024, year_2025]
        
        # Test cross-year range
        start_date = date(2024, 12, 30)
        end_date = date(2025, 1, 3)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should find both week directories
        assert len(result) == 2
        dates = [r[1] for r in result]
        assert date(2024, 12, 31) in dates
        assert date(2025, 1, 3) in dates

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_week_ending_directories_invalid_formats(self, mock_iterdir, mock_exists):
        """Test handling of invalid directory name formats."""
        mock_exists.return_value = True
        
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        month_dir = MagicMock()
        month_dir.name = "worklogs_2024-04"
        month_dir.is_dir.return_value = True
        
        # Mix of valid and invalid week directories
        valid_week = MagicMock()
        valid_week.name = "week_ending_2024-04-15"
        valid_week.is_dir.return_value = True
        
        invalid_week1 = MagicMock()
        invalid_week1.name = "week_ending_invalid_date"
        invalid_week1.is_dir.return_value = True
        
        invalid_week2 = MagicMock()
        invalid_week2.name = "not_week_ending_2024-04-16"
        invalid_week2.is_dir.return_value = True
        
        file_not_dir = MagicMock()
        file_not_dir.name = "week_ending_2024-04-17"
        file_not_dir.is_dir.return_value = False  # This is a file, not directory
        
        # Set up iterdir on individual mock objects
        year_dir.iterdir.return_value = [month_dir]
        month_dir.iterdir.return_value = [valid_week, invalid_week1, invalid_week2, file_not_dir]
        
        # Setup base path iterdir to return year directories
        mock_iterdir.return_value = [year_dir]
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 17)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should only find the valid week directory
        assert len(result) == 1
        assert result[0][1] == date(2024, 4, 15)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_week_ending_directories_missing_directories(self, mock_iterdir, mock_exists):
        """Test graceful handling of missing year/month directories."""
        # Mock exists to return False for some directories
        def exists_side_effect(*args, **kwargs):
            if args:
                path_str = str(args[0])
            else:
                path_str = ""
            if "worklogs_2024" in path_str and "worklogs_2024-" not in path_str:
                return True  # Year directory exists
            elif "worklogs_2024-04" in path_str:
                return True  # April exists
            elif "worklogs_2024-05" in path_str:
                return False  # May doesn't exist
            return True
        
        mock_exists.side_effect = exists_side_effect
        
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        april_dir = MagicMock()
        april_dir.name = "worklogs_2024-04"
        april_dir.is_dir.return_value = True
        
        april_week = MagicMock()
        april_week.name = "week_ending_2024-04-30"
        april_week.is_dir.return_value = True
        
        # Set up iterdir on individual mock objects
        year_dir.iterdir.return_value = [april_dir]  # Only April directory exists
        april_dir.iterdir.return_value = [april_week]
        
        # Setup base path iterdir to return year directories
        mock_iterdir.return_value = [year_dir]
        
        # Test range that spans April and May, but May directory doesn't exist
        start_date = date(2024, 4, 29)
        end_date = date(2024, 5, 3)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should only find April week directory
        assert len(result) == 1
        assert result[0][1] == date(2024, 4, 30)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_week_ending_directories_date_filtering(self, mock_iterdir, mock_exists):
        """Test that directories are properly filtered by date range."""
        mock_exists.return_value = True
        
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        month_dir = MagicMock()
        month_dir.name = "worklogs_2024-04"
        month_dir.is_dir.return_value = True
        
        # Week directories - some in range, some out of range
        week_before = MagicMock()
        week_before.name = "week_ending_2024-04-10"  # Before range
        week_before.is_dir.return_value = True
        
        week_in_range1 = MagicMock()
        week_in_range1.name = "week_ending_2024-04-15"  # In range
        week_in_range1.is_dir.return_value = True
        
        week_in_range2 = MagicMock()
        week_in_range2.name = "week_ending_2024-04-19"  # In range
        week_in_range2.is_dir.return_value = True
        
        week_after = MagicMock()
        week_after.name = "week_ending_2024-04-25"  # After range
        week_after.is_dir.return_value = True
        
        # Set up iterdir on individual mock objects
        year_dir.iterdir.return_value = [month_dir]
        month_dir.iterdir.return_value = [week_before, week_in_range1, week_in_range2, week_after]
        
        # Setup base path iterdir to return year directories
        mock_iterdir.return_value = [year_dir]
        
        # Test specific date range
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 20)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should only find directories within the date range
        assert len(result) == 2
        dates = [r[1] for r in result]
        assert date(2024, 4, 15) in dates
        assert date(2024, 4, 19) in dates
        assert date(2024, 4, 10) not in dates
        assert date(2024, 4, 25) not in dates

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_week_ending_directories_chronological_sorting(self, mock_iterdir, mock_exists):
        """Test that results are sorted chronologically."""
        mock_exists.return_value = True
        
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        month_dir = MagicMock()
        month_dir.name = "worklogs_2024-04"
        month_dir.is_dir.return_value = True
        
        # Week directories in random order
        week3 = MagicMock()
        week3.name = "week_ending_2024-04-19"
        week3.is_dir.return_value = True
        
        week1 = MagicMock()
        week1.name = "week_ending_2024-04-12"
        week1.is_dir.return_value = True
        
        week2 = MagicMock()
        week2.name = "week_ending_2024-04-15"
        week2.is_dir.return_value = True
        
        # Set up iterdir on individual mock objects
        year_dir.iterdir.return_value = [month_dir]
        month_dir.iterdir.return_value = [week3, week1, week2]  # Intentionally out of order
        
        # Setup base path iterdir to return year directories
        mock_iterdir.return_value = [year_dir]
        
        start_date = date(2024, 4, 10)
        end_date = date(2024, 4, 20)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should be sorted chronologically
        assert len(result) == 3
        dates = [r[1] for r in result]
        assert dates == [date(2024, 4, 12), date(2024, 4, 15), date(2024, 4, 19)]

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_week_ending_directories_file_system_errors(self, mock_iterdir, mock_exists):
        """Test handling of file system errors."""
        mock_exists.return_value = True
        
        # Mock iterdir to raise PermissionError for one directory
        def iterdir_side_effect():
            call_str = str(mock_iterdir.call_args) if mock_iterdir.call_args else ""
            if "test_worklogs" in call_str:
                year_dir = MagicMock()
                year_dir.name = "worklogs_2024"
                year_dir.is_dir.return_value = True
                return [year_dir]
            elif "worklogs_2024" in call_str and "worklogs_2024-" not in call_str:
                raise PermissionError("Access denied")
            return []
        
        mock_iterdir.side_effect = iterdir_side_effect
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 19)
        
        # Should handle the error gracefully and return empty result
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        assert len(result) == 0

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_week_ending_directories_performance_large_range(self, mock_iterdir, mock_exists):
        """Test performance with large date ranges."""
        mock_exists.return_value = True
        
        # Mock a year's worth of directories
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        # Create month directories for the whole year
        month_dirs = []
        for month in range(1, 13):
            month_dir = MagicMock()
            month_dir.name = f"worklogs_2024-{month:02d}"
            month_dir.is_dir.return_value = True
            
            # Create one week directory per month
            week_dir = MagicMock()
            week_dir.name = f"week_ending_2024-{month:02d}-15"
            week_dir.is_dir.return_value = True
            
            # Set up iterdir for this month directory
            month_dir.iterdir.return_value = [week_dir]
            
            month_dirs.append(month_dir)
        
        # Set up iterdir on individual mock objects
        year_dir.iterdir.return_value = month_dirs
        
        # Setup base path iterdir to return year directories
        mock_iterdir.return_value = [year_dir]
        
        # Test year-long range
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        import time
        start_time = time.time()
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        end_time = time.time()
        
        # Should complete within reasonable time
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should be fast even for large ranges
        
        # Should find directories for each month
        assert len(result) == 12

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_discover_week_ending_directories_empty_directories(self, mock_iterdir, mock_exists):
        """Test handling of empty directories."""
        mock_exists.return_value = True
        
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        month_dir = MagicMock()
        month_dir.name = "worklogs_2024-04"
        month_dir.is_dir.return_value = True
        
        def iterdir_side_effect():
            call_str = str(mock_iterdir.call_args) if mock_iterdir.call_args else ""
            if "test_worklogs" in call_str:
                return [year_dir]
            elif "worklogs_2024" in call_str and "worklogs_2024-" not in call_str:
                return [month_dir]
            elif "worklogs_2024-04" in call_str:
                return []  # Empty month directory
            return []
        
        mock_iterdir.side_effect = iterdir_side_effect
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 19)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should handle empty directories gracefully
        assert len(result) == 0

    def test_discover_week_ending_directories_method_signature(self):
        """Test that the method has the correct signature."""
        # Verify method exists and has correct signature
        method = getattr(self.discovery, '_discover_week_ending_directories', None)
        assert method is not None, "_discover_week_ending_directories method should exist"
        
        # Test with minimal valid input to verify signature
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 19)
        
        # Should not raise TypeError for correct signature
        try:
            with patch('pathlib.Path.exists', return_value=False):
                with patch('pathlib.Path.iterdir', return_value=[]):
                    result = self.discovery._discover_week_ending_directories(start_date, end_date)
                    assert isinstance(result, list)
        except TypeError as e:
            pytest.fail(f"Method signature is incorrect: {e}")


class TestDirectoryScannerEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery = FileDiscovery(base_path="~/Desktop/test_worklogs/")

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_leap_year_february_29_directory(self, mock_iterdir, mock_exists):
        """Test handling of February 29 in leap year directories."""
        mock_exists.return_value = True
        
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        month_dir = MagicMock()
        month_dir.name = "worklogs_2024-02"
        month_dir.is_dir.return_value = True
        
        feb29_week = MagicMock()
        feb29_week.name = "week_ending_2024-02-29"
        feb29_week.is_dir.return_value = True
        
        # Set up iterdir on individual mock objects
        year_dir.iterdir.return_value = [month_dir]
        month_dir.iterdir.return_value = [feb29_week]
        
        # Setup base path iterdir to return year directories
        mock_iterdir.return_value = [year_dir]
        
        # Test range including February 29
        start_date = date(2024, 2, 28)
        end_date = date(2024, 2, 29)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should find the February 29 directory
        assert len(result) == 1
        assert result[0][1] == date(2024, 2, 29)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_single_day_range_directory_discovery(self, mock_iterdir, mock_exists):
        """Test directory discovery for single day range."""
        mock_exists.return_value = True
        
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        month_dir = MagicMock()
        month_dir.name = "worklogs_2024-04"
        month_dir.is_dir.return_value = True
        
        week_dir = MagicMock()
        week_dir.name = "week_ending_2024-04-15"
        week_dir.is_dir.return_value = True
        
        # Set up iterdir on individual mock objects
        year_dir.iterdir.return_value = [month_dir]
        month_dir.iterdir.return_value = [week_dir]
        
        # Setup base path iterdir to return year directories
        mock_iterdir.return_value = [year_dir]
        
        # Single day range
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 15)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should find the single directory
        assert len(result) == 1
        assert result[0][1] == date(2024, 4, 15)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_no_matching_directories_in_range(self, mock_iterdir, mock_exists):
        """Test when no directories match the date range."""
        mock_exists.return_value = True
        
        year_dir = MagicMock()
        year_dir.name = "worklogs_2024"
        year_dir.is_dir.return_value = True
        
        month_dir = MagicMock()
        month_dir.name = "worklogs_2024-04"
        month_dir.is_dir.return_value = True
        
        # Week directories outside the range
        week_before = MagicMock()
        week_before.name = "week_ending_2024-04-10"
        week_before.is_dir.return_value = True
        
        week_after = MagicMock()
        week_after.name = "week_ending_2024-04-25"
        week_after.is_dir.return_value = True
        
        def iterdir_side_effect():
            call_str = str(mock_iterdir.call_args) if mock_iterdir.call_args else ""
            if "test_worklogs" in call_str:
                return [year_dir]
            elif "worklogs_2024" in call_str and "worklogs_2024-" not in call_str:
                return [month_dir]
            elif "worklogs_2024-04" in call_str:
                return [week_before, week_after]
            return []
        
        mock_iterdir.side_effect = iterdir_side_effect
        
        # Range that doesn't match any directories
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 20)
        
        result = self.discovery._discover_week_ending_directories(start_date, end_date)
        
        # Should find no directories in the range
        assert len(result) == 0