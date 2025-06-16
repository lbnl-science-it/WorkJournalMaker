"""
Comprehensive test suite for File Discovery Engine.
Following Test-Driven Development approach - these tests are written first.

Tests the FileDiscovery class that handles the complex directory structure:
~/Desktop/worklogs/worklogs_YYYY/worklogs_YYYY-MM/week_ending_YYYY-MM-DD/worklog_YYYY-MM-DD.txt

Note: week_ending_YYYY-MM-DD uses the last day of the work period, not calendar Sunday.
"""

import pytest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

# Import the classes we'll be testing (these don't exist yet)
from file_discovery import FileDiscovery, FileDiscoveryResult


class TestFileDiscovery:
    """Test suite for FileDiscovery class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery = FileDiscovery(base_path="~/Desktop/test_worklogs/")

    def test_date_range_generation_single_day(self):
        """Test date range generation for a single day."""
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 15)
        
        date_range = self.discovery._generate_date_range(start_date, end_date)
        
        assert len(date_range) == 1
        assert date_range[0] == date(2024, 4, 15)

    def test_date_range_generation_multiple_days(self):
        """Test date range generation for multiple days."""
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 18)
        
        date_range = self.discovery._generate_date_range(start_date, end_date)
        
        expected = [
            date(2024, 4, 15),
            date(2024, 4, 16),
            date(2024, 4, 17),
            date(2024, 4, 18)
        ]
        assert date_range == expected

    def test_date_range_generation_cross_month(self):
        """Test date range generation crossing month boundary."""
        start_date = date(2024, 4, 29)
        end_date = date(2024, 5, 2)
        
        date_range = self.discovery._generate_date_range(start_date, end_date)
        
        expected = [
            date(2024, 4, 29),
            date(2024, 4, 30),
            date(2024, 5, 1),
            date(2024, 5, 2)
        ]
        assert date_range == expected

    def test_date_range_generation_cross_year(self):
        """Test date range generation crossing year boundary."""
        start_date = date(2024, 12, 30)
        end_date = date(2025, 1, 2)
        
        date_range = self.discovery._generate_date_range(start_date, end_date)
        
        expected = [
            date(2024, 12, 30),
            date(2024, 12, 31),
            date(2025, 1, 1),
            date(2025, 1, 2)
        ]
        assert date_range == expected

    def test_calculate_week_ending_same_as_end_date(self):
        """Test that week ending calculation returns the end date of the range."""
        # This is the key change - week ending is based on the work period, not calendar
        start_date = date(2024, 4, 15)  # Monday
        end_date = date(2024, 4, 19)    # Friday
        
        week_ending = self.discovery._calculate_week_ending(start_date, end_date)
        
        # Should return the end date (Friday)
        assert week_ending == end_date

    def test_calculate_week_ending_single_day(self):
        """Test week ending calculation for single day range."""
        target_date = date(2024, 4, 15)
        
        week_ending = self.discovery._calculate_week_ending(target_date, target_date)
        
        # Should return the same date
        assert week_ending == target_date

    def test_calculate_week_ending_cross_month(self):
        """Test week ending calculation when range spans months."""
        start_date = date(2024, 4, 29)  # Monday
        end_date = date(2024, 5, 3)     # Friday
        
        week_ending = self.discovery._calculate_week_ending(start_date, end_date)
        
        # Should return May 3 (the end date)
        assert week_ending == date(2024, 5, 3)

    def test_calculate_week_ending_cross_year(self):
        """Test week ending calculation when range spans years."""
        start_date = date(2024, 12, 30)  # Monday
        end_date = date(2025, 1, 3)      # Friday
        
        week_ending = self.discovery._calculate_week_ending(start_date, end_date)
        
        # Should return January 3, 2025 (the end date)
        assert week_ending == date(2025, 1, 3)

    def test_file_path_construction_regular_date(self):
        """Test file path construction for a regular date."""
        target_date = date(2024, 4, 15)  # Monday
        week_ending_date = date(2024, 4, 19)  # Friday (end of work week)
        
        file_path = self.discovery._construct_file_path(target_date, week_ending_date)
        
        # Expected path structure:
        # ~/Desktop/test_worklogs/worklogs_2024/worklogs_2024-04/week_ending_2024-04-19/worklog_2024-04-15.txt
        expected_path = (
            self.discovery.base_path / 
            "worklogs_2024" / 
            "worklogs_2024-04" / 
            "week_ending_2024-04-19" / 
            "worklog_2024-04-15.txt"
        )
        assert file_path == expected_path

    def test_file_path_construction_cross_month_week(self):
        """Test file path construction when work week spans months."""
        target_date = date(2024, 4, 29)      # Monday (file date)
        week_ending_date = date(2024, 5, 3)  # Friday (end of work week)
        
        file_path = self.discovery._construct_file_path(target_date, week_ending_date)
        
        # File should be in April directory (based on file date), week ending is May 3
        expected_path = (
            self.discovery.base_path / 
            "worklogs_2024" / 
            "worklogs_2024-04" / 
            "week_ending_2024-05-03" / 
            "worklog_2024-04-29.txt"
        )
        assert file_path == expected_path

    def test_file_path_construction_cross_year_week(self):
        """Test file path construction when work week spans years."""
        target_date = date(2024, 12, 30)     # Monday (file date)
        week_ending_date = date(2025, 1, 3)  # Friday (end of work week)
        
        file_path = self.discovery._construct_file_path(target_date, week_ending_date)
        
        # File should be in 2024 directory (based on file date), week ending is Jan 3, 2025
        expected_path = (
            self.discovery.base_path / 
            "worklogs_2024" / 
            "worklogs_2024-12" / 
            "week_ending_2025-01-03" / 
            "worklog_2024-12-30.txt"
        )
        assert file_path == expected_path

    def test_file_path_construction_new_year_day(self):
        """Test file path construction for New Year's Day."""
        target_date = date(2025, 1, 1)       # Wednesday (file date)
        week_ending_date = date(2025, 1, 3)  # Friday (end of work week)
        
        file_path = self.discovery._construct_file_path(target_date, week_ending_date)
        
        expected_path = (
            self.discovery.base_path / 
            "worklogs_2025" / 
            "worklogs_2025-01" / 
            "week_ending_2025-01-03" / 
            "worklog_2025-01-01.txt"
        )
        assert file_path == expected_path

    @patch('pathlib.Path.exists')
    def test_discover_files_all_exist(self, mock_exists):
        """Test file discovery when all files exist."""
        mock_exists.return_value = True
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 17)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        assert isinstance(result, FileDiscoveryResult)
        assert len(result.found_files) == 3
        assert len(result.missing_files) == 0
        assert result.total_expected == 3
        assert result.date_range == (start_date, end_date)
        assert isinstance(result.processing_time, float)

    @patch('pathlib.Path.exists')
    def test_discover_files_some_missing(self, mock_exists):
        """Test file discovery when some files are missing."""
        # Mock exists to return True for first file, False for others
        mock_exists.side_effect = [True, False, False]
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 17)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        assert len(result.found_files) == 1
        assert len(result.missing_files) == 2
        assert result.total_expected == 3

    @patch('pathlib.Path.exists')
    def test_discover_files_none_exist(self, mock_exists):
        """Test file discovery when no files exist."""
        mock_exists.return_value = False
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 17)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        assert len(result.found_files) == 0
        assert len(result.missing_files) == 3
        assert result.total_expected == 3

    @patch('pathlib.Path.exists')
    def test_cross_year_discovery(self, mock_exists):
        """Test file discovery across year boundaries."""
        mock_exists.return_value = True
        
        start_date = date(2024, 12, 30)
        end_date = date(2025, 1, 2)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        assert len(result.found_files) == 4  # Dec 30, 31, Jan 1, 2
        assert len(result.missing_files) == 0
        assert result.total_expected == 4
        
        # Verify files are from different years
        file_paths = [str(f) for f in result.found_files]
        assert any("worklogs_2024" in path for path in file_paths)
        assert any("worklogs_2025" in path for path in file_paths)
        
        # All files should be in the same week_ending directory (2025-01-02)
        assert all("week_ending_2025-01-02" in path for path in file_paths)

    @patch('pathlib.Path.exists')
    def test_performance_with_large_ranges(self, mock_exists):
        """Test performance with year-long ranges."""
        mock_exists.return_value = True
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        start_time = time.time()
        result = self.discovery.discover_files(start_date, end_date)
        end_time = time.time()
        
        # Should complete within reasonable time (less than 1 second for year-long range)
        processing_time = end_time - start_time
        assert processing_time < 1.0
        
        # Should handle 366 days (2024 is leap year)
        assert result.total_expected == 366
        assert len(result.found_files) == 366

    def test_missing_file_tracking_preserves_order(self):
        """Test that missing files are tracked in chronological order."""
        with patch('pathlib.Path.exists') as mock_exists:
            # Mock pattern: first file exists, second missing, third exists, fourth missing
            mock_exists.side_effect = [True, False, True, False]
            
            start_date = date(2024, 4, 15)
            end_date = date(2024, 4, 18)
            
            result = self.discovery.discover_files(start_date, end_date)
            
            assert len(result.found_files) == 2
            assert len(result.missing_files) == 2
            
            # Check that files are in chronological order
            found_dates = [self._extract_date_from_path(f) for f in result.found_files]
            missing_dates = [self._extract_date_from_path(f) for f in result.missing_files]
            
            assert found_dates == [date(2024, 4, 15), date(2024, 4, 17)]
            assert missing_dates == [date(2024, 4, 16), date(2024, 4, 18)]

    def test_base_path_expansion(self):
        """Test that base path is properly expanded."""
        discovery = FileDiscovery(base_path="~/Desktop/worklogs/")
        
        # Should expand ~ to home directory
        assert str(discovery.base_path).startswith("/")
        assert "Desktop/worklogs" in str(discovery.base_path)

    def test_custom_base_path(self):
        """Test initialization with custom base path."""
        custom_path = "/custom/path/to/worklogs/"
        discovery = FileDiscovery(base_path=custom_path)
        
        assert discovery.base_path == Path(custom_path)

    def test_file_discovery_result_dataclass(self):
        """Test FileDiscoveryResult dataclass structure."""
        found_files = [Path("/test/file1.txt"), Path("/test/file2.txt")]
        missing_files = [Path("/test/file3.txt")]
        
        result = FileDiscoveryResult(
            found_files=found_files,
            missing_files=missing_files,
            total_expected=3,
            date_range=(date(2024, 4, 15), date(2024, 4, 17)),
            processing_time=0.123
        )
        
        assert result.found_files == found_files
        assert result.missing_files == missing_files
        assert result.total_expected == 3
        assert result.date_range == (date(2024, 4, 15), date(2024, 4, 17))
        assert result.processing_time == 0.123

    def _extract_date_from_path(self, file_path: Path) -> date:
        """Helper method to extract date from file path."""
        # Extract date from filename like "worklog_2024-04-15.txt"
        filename = file_path.name
        date_str = filename.replace("worklog_", "").replace(".txt", "")
        year, month, day = date_str.split("-")
        return date(int(year), int(month), int(day))


class TestFileDiscoveryEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_leap_year_february_29(self):
        """Test file discovery for February 29 in leap year."""
        discovery = FileDiscovery()
        
        # 2024 is a leap year
        feb_29 = date(2024, 2, 29)
        week_ending = date(2024, 2, 29)  # Single day range
        file_path = discovery._construct_file_path(feb_29, week_ending)
        
        # Should construct valid path
        assert "worklog_2024-02-29.txt" in str(file_path)
        assert "worklogs_2024-02" in str(file_path)
        assert "week_ending_2024-02-29" in str(file_path)

    def test_single_day_range(self):
        """Test discovery with single day range."""
        discovery = FileDiscovery()
        
        with patch('pathlib.Path.exists', return_value=True):
            start_date = date(2024, 4, 15)
            end_date = date(2024, 4, 15)
            
            result = discovery.discover_files(start_date, end_date)
            
            assert result.total_expected == 1
            assert len(result.found_files) == 1
            # Single day should use same date for week_ending
            assert "week_ending_2024-04-15" in str(result.found_files[0])

    def test_work_week_patterns(self):
        """Test various work week patterns."""
        discovery = FileDiscovery()
        
        # Monday to Friday (typical work week)
        start_date = date(2024, 4, 15)  # Monday
        end_date = date(2024, 4, 19)    # Friday
        week_ending = discovery._calculate_week_ending(start_date, end_date)
        assert week_ending == date(2024, 4, 19)
        
        # Tuesday to Thursday (short week)
        start_date = date(2024, 4, 16)  # Tuesday
        end_date = date(2024, 4, 18)    # Thursday
        week_ending = discovery._calculate_week_ending(start_date, end_date)
        assert week_ending == date(2024, 4, 18)
        
        # Wednesday to Tuesday (unusual pattern)
        start_date = date(2024, 4, 17)  # Wednesday
        end_date = date(2024, 4, 23)    # Tuesday
        week_ending = discovery._calculate_week_ending(start_date, end_date)
        assert week_ending == date(2024, 4, 23)

    @patch('pathlib.Path.exists')
    def test_processing_time_measurement(self, mock_exists):
        """Test that processing time is accurately measured."""
        mock_exists.return_value = True
        discovery = FileDiscovery()
        
        start_date = date(2024, 4, 15)
        end_date = date(2024, 4, 17)
        
        result = discovery.discover_files(start_date, end_date)
        
        # Processing time should be a positive float
        assert isinstance(result.processing_time, float)
        assert result.processing_time > 0
        assert result.processing_time < 1.0  # Should be very fast for small ranges

    def test_directory_structure_consistency(self):
        """Test that all files in a date range use the same week_ending directory."""
        discovery = FileDiscovery()
        
        start_date = date(2024, 4, 15)  # Monday
        end_date = date(2024, 4, 19)    # Friday
        week_ending = discovery._calculate_week_ending(start_date, end_date)
        
        # All files should be in week_ending_2024-04-19 directory
        for single_date in [date(2024, 4, 15), date(2024, 4, 16), date(2024, 4, 17), 
                           date(2024, 4, 18), date(2024, 4, 19)]:
            file_path = discovery._construct_file_path(single_date, week_ending)
            assert "week_ending_2024-04-19" in str(file_path)