"""
Test suite for File Discovery Engine v2.0 - Foundation Data Structures
Following Test-Driven Development approach - these tests are written first.

Tests the enhanced FileDiscoveryResult dataclass with new directory scanning fields:
- discovered_weeks: List[Tuple[date, int]]  # (week_ending_date, file_count)
- directory_scan_stats: Dict[str, int]      # scanning statistics

Uses real directory structure at /Users/TYFong/Desktop/worklogs/worklogs_2024
Tests are non-destructive (read-only).
"""

import pytest
from datetime import date, timedelta
from pathlib import Path
from typing import List, Tuple, Dict
import os

# Import the enhanced classes (will be implemented after tests)
from file_discovery import FileDiscoveryResult


class TestEnhancedFileDiscoveryResultWithRealData:
    """Test suite for enhanced FileDiscoveryResult dataclass using real 2024 data."""
    
    @classmethod
    def setup_class(cls):
        """Set up class-level fixtures."""
        cls.test_base_path = Path("/Users/TYFong/Desktop/worklogs/worklogs_2024")
        
        # Verify test data exists
        if not cls.test_base_path.exists():
            pytest.skip(f"Test data directory not found: {cls.test_base_path}")
    
    def test_backward_compatibility_with_real_paths(self):
        """Test that original fields work with real file paths from 2024 data."""
        # Use actual files from the 2024 directory
        found_files = [
            self.test_base_path / "worklogs_2024-01/week_ending_2024-01-05/worklog_2024-01-02.txt",
            self.test_base_path / "worklogs_2024-01/week_ending_2024-01-05/worklog_2024-01-03.txt",
        ]
        missing_files = [
            self.test_base_path / "worklogs_2024-01/week_ending_2024-01-05/worklog_2024-01-01.txt",  # New Year's Day
        ]
        
        # Create result with only original fields
        result = FileDiscoveryResult(
            found_files=found_files,
            missing_files=missing_files,
            total_expected=3,
            date_range=(date(2024, 1, 1), date(2024, 1, 3)),
            processing_time=0.123
        )
        
        # Original fields should work exactly as before
        assert result.found_files == found_files
        assert result.missing_files == missing_files
        assert result.total_expected == 3
        assert result.date_range == (date(2024, 1, 1), date(2024, 1, 3))
        assert result.processing_time == 0.123
        
        # Verify paths are real and exist
        for file_path in found_files:
            assert file_path.exists(), f"Test file should exist: {file_path}"

    def test_new_fields_with_default_values(self):
        """Test that new fields have appropriate default values for backward compatibility."""
        found_files = [
            self.test_base_path / "worklogs_2024-01/week_ending_2024-01-12/worklog_2024-01-08.txt"
        ]
        
        # Create result with only original fields
        result = FileDiscoveryResult(
            found_files=found_files,
            missing_files=[],
            total_expected=1,
            date_range=(date(2024, 1, 8), date(2024, 1, 8)),
            processing_time=0.05
        )
        
        # New fields should have sensible defaults
        assert hasattr(result, 'discovered_weeks')
        assert hasattr(result, 'directory_scan_stats')
        assert isinstance(result.discovered_weeks, list)
        assert isinstance(result.directory_scan_stats, dict)
        assert result.discovered_weeks == []  # Empty list by default
        assert result.directory_scan_stats == {}  # Empty dict by default

    def test_discovered_weeks_with_real_2024_data(self):
        """Test discovered_weeks field with actual 2024 week data."""
        # Real weeks from 2024 data with actual file counts
        discovered_weeks = [
            (date(2024, 1, 5), 3),   # week_ending_2024-01-05 has 3 files
            (date(2024, 1, 12), 5),  # week_ending_2024-01-12 has 5 files  
            (date(2024, 1, 19), 4),  # week_ending_2024-01-19 has 4 files
            (date(2024, 1, 26), 3),  # week_ending_2024-01-26 has 3 files
        ]
        
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[],
            total_expected=15,
            date_range=(date(2024, 1, 1), date(2024, 1, 31)),
            processing_time=0.2,
            discovered_weeks=discovered_weeks
        )
        
        # Verify structure and data
        assert len(result.discovered_weeks) == 4
        assert result.discovered_weeks[0] == (date(2024, 1, 5), 3)
        assert result.discovered_weeks[1] == (date(2024, 1, 12), 5)
        
        # Verify chronological order
        dates = [week[0] for week in result.discovered_weeks]
        assert dates == sorted(dates)

    def test_cross_month_weeks_in_discovered_weeks(self):
        """Test discovered_weeks with cross-month boundaries from real data."""
        # Real cross-month week from 2024 data
        discovered_weeks = [
            (date(2024, 2, 2), 5),   # week_ending_2024-02-02 contains files from Jan 29-31 and Feb 1-2
            (date(2024, 3, 1), 5),   # week_ending_2024-03-01 contains files from Feb 26-29 and Mar 1
            (date(2024, 5, 3), 5),   # week_ending_2024-05-03 contains files from Apr 29-30 and May 1-3
        ]
        
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[],
            total_expected=15,
            date_range=(date(2024, 1, 29), date(2024, 5, 3)),
            processing_time=0.3,
            discovered_weeks=discovered_weeks
        )
        
        # Verify cross-month weeks are handled correctly
        assert len(result.discovered_weeks) == 3
        
        # Check that we have weeks spanning different months
        months_represented = set(week[0].month for week in result.discovered_weeks)
        assert len(months_represented) == 3  # February, March, May

    def test_leap_year_handling_in_discovered_weeks(self):
        """Test discovered_weeks with leap year date (Feb 29, 2024)."""
        # Real leap year week from 2024 data
        discovered_weeks = [
            (date(2024, 3, 1), 5),   # week_ending_2024-03-01 includes Feb 29, 2024
        ]
        
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[],
            total_expected=5,
            date_range=(date(2024, 2, 26), date(2024, 3, 1)),
            processing_time=0.1,
            discovered_weeks=discovered_weeks
        )
        
        # Verify leap year week is handled correctly
        assert len(result.discovered_weeks) == 1
        assert result.discovered_weeks[0][0] == date(2024, 3, 1)
        assert result.discovered_weeks[0][1] == 5  # Should include Feb 29 file

    def test_directory_scan_stats_with_real_patterns(self):
        """Test directory_scan_stats with patterns observed in real 2024 data."""
        # Stats based on actual 2024 directory structure patterns
        directory_scan_stats = {
            'directories_scanned': 12,  # 12 month directories
            'valid_week_directories': 45,  # Approximate number of week directories
            'invalid_directories_skipped': 2,  # .DS_Store and other non-week dirs
            'total_files_found': 200,  # Approximate file count
            'cross_month_weeks': 8,  # Weeks that span month boundaries
            'format_variations_found': 2,  # week_ending_2024_04_05 vs week_ending_2024-04-07
            'leap_year_files': 1,  # Feb 29, 2024 file
            'missing_weekends': 15,  # Estimated weekend gaps
        }
        
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[],
            total_expected=250,
            date_range=(date(2024, 1, 1), date(2024, 12, 31)),
            processing_time=1.5,
            directory_scan_stats=directory_scan_stats
        )
        
        # Verify all stats are preserved
        assert result.directory_scan_stats == directory_scan_stats
        assert result.directory_scan_stats['format_variations_found'] == 2
        assert result.directory_scan_stats['leap_year_files'] == 1

    def test_format_variations_in_directory_scan_stats(self):
        """Test handling of directory name format variations found in real data."""
        # Real format variations from 2024 data:
        # - week_ending_2024-01-05 (standard format)
        # - week_ending_2024_04_05 (underscore format)
        directory_scan_stats = {
            'standard_format_directories': 40,  # week_ending_YYYY-MM-DD
            'underscore_format_directories': 5,  # week_ending_YYYY_MM_DD
            'invalid_format_directories': 1,    # Any malformed names
            'total_format_variations': 2,
        }
        
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[],
            total_expected=0,
            date_range=(date(2024, 1, 1), date(2024, 12, 31)),
            processing_time=0.8,
            directory_scan_stats=directory_scan_stats
        )
        
        # Verify format variation tracking
        total_dirs = (result.directory_scan_stats['standard_format_directories'] + 
                     result.directory_scan_stats['underscore_format_directories'] + 
                     result.directory_scan_stats['invalid_format_directories'])
        assert total_dirs == 46

    def test_comprehensive_real_data_scenario(self):
        """Test comprehensive scenario using patterns from real 2024 data."""
        # Simulate a quarter's worth of real data (Q1 2024)
        found_files = [
            # January files
            self.test_base_path / "worklogs_2024-01/week_ending_2024-01-05/worklog_2024-01-02.txt",
            self.test_base_path / "worklogs_2024-01/week_ending_2024-01-12/worklog_2024-01-08.txt",
            # February files (including leap year)
            self.test_base_path / "worklogs_2024-02/week_ending_2024-02-02/worklog_2024-01-29.txt",
            self.test_base_path / "worklogs_2024-03/week_ending_2024-03-01/worklog_2024-02-29.txt",  # Leap year
            # March files
            self.test_base_path / "worklogs_2024-03/week_ending_2024-03-08/worklog_2024-03-04.txt",
        ]
        
        missing_files = [
            self.test_base_path / "worklogs_2024-01/week_ending_2024-01-05/worklog_2024-01-01.txt",  # New Year
            self.test_base_path / "worklogs_2024-02/week_ending_2024-02-16/worklog_2024-02-14.txt",  # Valentine's Day
        ]
        
        discovered_weeks = [
            (date(2024, 1, 5), 3),
            (date(2024, 1, 12), 5),
            (date(2024, 2, 2), 5),   # Cross-month week
            (date(2024, 3, 1), 5),   # Includes leap year day
            (date(2024, 3, 8), 5),
        ]
        
        directory_scan_stats = {
            'directories_scanned': 3,  # Jan, Feb, Mar
            'valid_week_directories': 15,
            'cross_month_weeks': 2,
            'leap_year_files_found': 1,
            'format_variations': 0,  # Q1 uses standard format
            'total_files_found': len(found_files),
            'total_files_missing': len(missing_files),
        }
        
        result = FileDiscoveryResult(
            found_files=found_files,
            missing_files=missing_files,
            total_expected=len(found_files) + len(missing_files),
            date_range=(date(2024, 1, 1), date(2024, 3, 31)),
            processing_time=0.45,
            discovered_weeks=discovered_weeks,
            directory_scan_stats=directory_scan_stats
        )
        
        # Verify comprehensive data
        assert len(result.found_files) == 5
        assert len(result.missing_files) == 2
        assert len(result.discovered_weeks) == 5
        assert result.directory_scan_stats['leap_year_files_found'] == 1
        assert result.directory_scan_stats['cross_month_weeks'] == 2
        
        # Verify all found files actually exist
        for file_path in result.found_files:
            assert file_path.exists(), f"Test file should exist: {file_path}"

    def test_empty_discovered_weeks_with_real_missing_data(self):
        """Test empty discovered_weeks when no valid week directories found."""
        # Simulate scenario where directory scan found no valid week directories
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[
                self.test_base_path / "worklogs_2024-99/week_ending_2024-99-01/worklog_2024-99-01.txt"  # Invalid path
            ],
            total_expected=1,
            date_range=(date(2024, 12, 1), date(2024, 12, 1)),  # Valid date range for testing
            processing_time=0.01,
            discovered_weeks=[],  # No valid weeks found
            directory_scan_stats={
                'directories_scanned': 1,
                'valid_week_directories': 0,
                'invalid_directories_skipped': 1,
                'scan_errors': 1
            }
        )
        
        assert result.discovered_weeks == []
        assert result.directory_scan_stats['valid_week_directories'] == 0
        assert result.directory_scan_stats['scan_errors'] == 1

    def test_dataclass_equality_with_real_data(self):
        """Test dataclass equality using real file paths."""
        real_file = self.test_base_path / "worklogs_2024-01/week_ending_2024-01-05/worklog_2024-01-02.txt"
        
        base_data = {
            'found_files': [real_file],
            'missing_files': [],
            'total_expected': 1,
            'date_range': (date(2024, 1, 2), date(2024, 1, 2)),
            'processing_time': 0.1
        }
        
        # Two identical results
        result1 = FileDiscoveryResult(
            **base_data,
            discovered_weeks=[(date(2024, 1, 5), 3)],
            directory_scan_stats={'directories_scanned': 1}
        )
        
        result2 = FileDiscoveryResult(
            **base_data,
            discovered_weeks=[(date(2024, 1, 5), 3)],
            directory_scan_stats={'directories_scanned': 1}
        )
        
        # Should be equal
        assert result1 == result2
        
        # Different discovered_weeks should not be equal
        result3 = FileDiscoveryResult(
            **base_data,
            discovered_weeks=[(date(2024, 1, 12), 5)],  # Different week
            directory_scan_stats={'directories_scanned': 1}
        )
        
        assert result1 != result3

    def test_large_date_range_discovered_weeks(self):
        """Test discovered_weeks with large date range (full year 2024)."""
        # Generate weekly data for entire year 2024
        discovered_weeks = []
        
        # Sample weeks throughout 2024 based on real data patterns
        sample_weeks = [
            (date(2024, 1, 5), 3),
            (date(2024, 1, 12), 5),
            (date(2024, 2, 2), 5),   # Cross-month
            (date(2024, 3, 1), 5),   # Leap year week
            (date(2024, 5, 3), 5),   # Cross-month
            (date(2024, 7, 5), 3),   # Summer
            (date(2024, 8, 2), 5),   # Cross-month
            (date(2024, 9, 6), 1),   # Light week
            (date(2024, 11, 1), 5),  # Cross-month
        ]
        
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[],
            total_expected=0,
            date_range=(date(2024, 1, 1), date(2024, 12, 31)),
            processing_time=2.1,
            discovered_weeks=sample_weeks
        )
        
        # Verify year-long data handling
        assert len(result.discovered_weeks) == 9
        
        # Verify date range spans full year
        week_dates = [week[0] for week in result.discovered_weeks]
        assert min(week_dates).year == 2024
        assert max(week_dates).year == 2024
        assert min(week_dates).month == 1
        assert max(week_dates).month == 11

    def test_zero_file_counts_with_real_empty_weeks(self):
        """Test discovered weeks with zero file counts (real empty week scenarios)."""
        # Some weeks might have no files due to holidays, vacations, etc.
        discovered_weeks = [
            (date(2024, 1, 5), 3),   # Normal week
            (date(2024, 1, 12), 0),  # Empty week (vacation?)
            (date(2024, 7, 5), 0),   # Empty week (July 4th holiday?)
            (date(2024, 11, 1), 5),  # Normal week
        ]
        
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[],
            total_expected=0,
            date_range=(date(2024, 1, 1), date(2024, 11, 30)),
            processing_time=0.3,
            discovered_weeks=discovered_weeks
        )
        
        # Zero counts should be valid and preserved
        zero_count_weeks = [week for week in result.discovered_weeks if week[1] == 0]
        assert len(zero_count_weeks) == 2
        
        # Verify specific empty weeks
        empty_dates = [week[0] for week in zero_count_weeks]
        assert date(2024, 1, 12) in empty_dates
        assert date(2024, 7, 5) in empty_dates


class TestEnhancedFileDiscoveryResultEdgeCases:
    """Test edge cases using real 2024 data patterns."""
    
    @classmethod
    def setup_class(cls):
        """Set up class-level fixtures."""
        cls.test_base_path = Path("/Users/TYFong/Desktop/worklogs/worklogs_2024")
        
        if not cls.test_base_path.exists():
            pytest.skip(f"Test data directory not found: {cls.test_base_path}")

    def test_mixed_directory_formats_in_stats(self):
        """Test directory_scan_stats with mixed formats found in real data."""
        # Based on actual format variations in 2024 data
        directory_scan_stats = {
            'standard_hyphen_format': 40,    # week_ending_2024-01-05
            'underscore_format': 5,          # week_ending_2024_04_05
            'malformed_directories': 1,      # Any invalid formats
            'ds_store_files_ignored': 12,    # .DS_Store files found and ignored
            'empty_directories': 2,          # Directories with no .txt files
        }
        
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[],
            total_expected=0,
            date_range=(date(2024, 1, 1), date(2024, 12, 31)),
            processing_time=1.2,
            directory_scan_stats=directory_scan_stats
        )
        
        # Verify mixed format handling
        assert result.directory_scan_stats['standard_hyphen_format'] == 40
        assert result.directory_scan_stats['underscore_format'] == 5
        assert result.directory_scan_stats['ds_store_files_ignored'] == 12

    def test_partial_weeks_in_discovered_weeks(self):
        """Test discovered_weeks with partial weeks (common at month boundaries)."""
        # Real partial weeks from 2024 data
        discovered_weeks = [
            (date(2024, 1, 5), 3),   # Partial week (Jan 2, 3, 5 - no Jan 1, 4)
            (date(2024, 1, 26), 3),  # Partial week (Jan 23, 24, 26 - missing some days)
            (date(2024, 5, 31), 3),  # Partial week at month end
        ]
        
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[],
            total_expected=0,
            date_range=(date(2024, 1, 1), date(2024, 5, 31)),
            processing_time=0.2,
            discovered_weeks=discovered_weeks
        )
        
        # Verify partial weeks are handled correctly
        assert len(result.discovered_weeks) == 3
        
        # All partial weeks should have fewer than 5 files (typical work week)
        for week_date, file_count in result.discovered_weeks:
            assert file_count <= 5
            assert file_count >= 0

    def test_very_large_directory_scan_numbers(self):
        """Test with very large numbers that might occur in extensive scans."""
        large_stats = {
            'total_directories_traversed': 50000,
            'total_files_examined': 1000000,
            'bytes_processed': 5000000000,  # 5GB
            'scan_duration_milliseconds': 30000,  # 30 seconds
        }
        
        result = FileDiscoveryResult(
            found_files=[],
            missing_files=[],
            total_expected=0,
            date_range=(date(2020, 1, 1), date(2024, 12, 31)),  # 5 year range
            processing_time=30.0,
            directory_scan_stats=large_stats
        )
        
        # Should handle large numbers correctly
        assert result.directory_scan_stats['bytes_processed'] == 5000000000
        assert result.directory_scan_stats['total_files_examined'] == 1000000

    def test_string_representation_with_real_data(self):
        """Test string representation includes real file paths and data."""
        real_file = self.test_base_path / "worklogs_2024-01/week_ending_2024-01-05/worklog_2024-01-02.txt"
        
        result = FileDiscoveryResult(
            found_files=[real_file],
            missing_files=[],
            total_expected=1,
            date_range=(date(2024, 1, 2), date(2024, 1, 2)),
            processing_time=0.05,
            discovered_weeks=[(date(2024, 1, 5), 3)],
            directory_scan_stats={'directories_scanned': 1}
        )
        
        repr_str = repr(result)
        
        # Should include new field names and real data
        assert 'discovered_weeks' in repr_str
        assert 'directory_scan_stats' in repr_str
        assert '2024-01-05' in repr_str
        assert 'directories_scanned' in repr_str
        assert 'worklogs_2024' in repr_str

    def test_type_annotations_validation(self):
        """Test that type annotations are correctly defined."""
        import typing
        
        # Get type hints for FileDiscoveryResult
        hints = typing.get_type_hints(FileDiscoveryResult)
        
        # Verify new field type annotations exist
        assert 'discovered_weeks' in hints
        assert 'directory_scan_stats' in hints
        
        # Verify the types are as expected
        discovered_weeks_type = hints['discovered_weeks']
        directory_scan_stats_type = hints['directory_scan_stats']
        
        # These should be List and Dict types respectively
        assert hasattr(discovered_weeks_type, '__origin__')
        assert hasattr(directory_scan_stats_type, '__origin__')