"""
Test suite for File Discovery Engine v2.0 - Date Parsing Utilities

This module tests the date parsing functionality that extracts dates from
directory names and filenames in the work journal file structure.

Test Coverage:
- Valid date formats for both directory names and filenames
- Invalid formats and malformed input strings
- Edge cases like leap years and month boundaries
- Boundary testing for date validation
- Consistent error handling across functions
"""

import pytest
from datetime import date
import os

from file_discovery import FileDiscovery


class TestDateParsingUtilities:
    """Test suite for date parsing utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.file_discovery = FileDiscovery()
    
    # Tests for _parse_week_ending_date()
    
    def test_parse_week_ending_date_valid_formats(self):
        """Test parsing valid week_ending directory names."""
        test_cases = [
            ("week_ending_2024-01-15", date(2024, 1, 15)),
            ("week_ending_2023-12-31", date(2023, 12, 31)),
            ("week_ending_2024-02-29", date(2024, 2, 29)),  # Leap year
            ("week_ending_2025-06-06", date(2025, 6, 6)),
            ("week_ending_2020-01-01", date(2020, 1, 1)),
            ("week_ending_2024-07-04", date(2024, 7, 4)),
        ]
        
        for directory_name, expected_date in test_cases:
            result = self.file_discovery._parse_week_ending_date(directory_name)
            assert result == expected_date, f"Failed to parse {directory_name}"
    
    def test_parse_week_ending_date_invalid_formats(self):
        """Test parsing invalid week_ending directory names returns None."""
        invalid_cases = [
            "week_ending_2024-13-01",  # Invalid month
            "week_ending_2024-02-30",  # Invalid day for February
            "week_ending_2023-02-29",  # Not a leap year
            "week_ending_2024-04-31",  # Invalid day for April
            "week_ending_2024-00-15",  # Invalid month (0)
            "week_ending_2024-01-00",  # Invalid day (0)
            "week_ending_2024/01/15",  # Wrong separator
            "week_ending_2024-01",     # Missing day
            "week_ending_2024",        # Missing month and day
            "week_ending_",            # Empty date part
            "ending_2024-01-15",       # Wrong prefix
            "week_2024-01-15",         # Missing "ending"
            "2024-01-15",              # No prefix
            "",                        # Empty string
            "week_ending_abc-def-ghi", # Non-numeric
            "week_ending_2024-ab-15",  # Non-numeric month
            "week_ending_2024-01-cd",  # Non-numeric day
        ]
        
        for invalid_name in invalid_cases:
            result = self.file_discovery._parse_week_ending_date(invalid_name)
            assert result is None, f"Should return None for invalid format: {invalid_name}"
    
    def test_parse_week_ending_date_flexible_formats(self):
        """Test parsing flexible week_ending directory names that should be valid."""
        flexible_cases = [
            ("week_ending_2024-1-15", date(2024, 1, 15)),   # Single digit month
            ("week_ending_2024-01-5", date(2024, 1, 5)),    # Single digit day
            ("week_ending_2024-1-5", date(2024, 1, 5)),     # Both single digit
            ("week_ending_2024-12-1", date(2024, 12, 1)),   # Single digit day in December
        ]
        
        for directory_name, expected_date in flexible_cases:
            result = self.file_discovery._parse_week_ending_date(directory_name)
            assert result == expected_date, f"Failed to parse flexible format {directory_name}"
    
    def test_parse_week_ending_date_edge_cases(self):
        """Test edge cases for week_ending date parsing."""
        edge_cases = [
            # Leap year boundaries
            ("week_ending_2024-02-29", date(2024, 2, 29)),  # Valid leap year
            ("week_ending_2023-02-29", None),               # Invalid leap year
            ("week_ending_2000-02-29", date(2000, 2, 29)),  # Century leap year
            ("week_ending_1900-02-29", None),               # Century non-leap year
            
            # Month boundaries
            ("week_ending_2024-01-31", date(2024, 1, 31)),  # January 31st
            ("week_ending_2024-04-30", date(2024, 4, 30)),  # April 30th
            ("week_ending_2024-04-31", None),               # Invalid April 31st
            ("week_ending_2024-06-30", date(2024, 6, 30)),  # June 30th
            ("week_ending_2024-06-31", None),               # Invalid June 31st
            
            # Year boundaries
            ("week_ending_2024-12-31", date(2024, 12, 31)),  # End of year
            ("week_ending_2025-01-01", date(2025, 1, 1)),    # Start of year
            
            # Extreme values
            ("week_ending_1000-01-01", date(1000, 1, 1)),    # Very old date
            ("week_ending_9999-12-31", date(9999, 12, 31)),  # Very future date
        ]
        
        for directory_name, expected_result in edge_cases:
            result = self.file_discovery._parse_week_ending_date(directory_name)
            assert result == expected_result, f"Edge case failed: {directory_name}"
    
    def test_parse_week_ending_date_malformed_input(self):
        """Test parsing with malformed and unusual input strings."""
        malformed_cases = [
            None,                                    # None input
            123,                                     # Integer input
            [],                                      # List input
            {},                                      # Dict input
            "week_ending_2024-01-15-extra",         # Extra parts
            "week_ending_2024--01-15",              # Double dash
            "week_ending_2024-01--15",              # Double dash
            "week_ending_2024.01.15",               # Dots instead of dashes
            "week_ending_2024_01_15",               # Underscores
            "WEEK_ENDING_2024-01-15",               # Uppercase
            "Week_Ending_2024-01-15",               # Mixed case
        ]
        
        for malformed_input in malformed_cases:
            result = self.file_discovery._parse_week_ending_date(malformed_input)
            assert result is None, f"Should return None for malformed input: {malformed_input}"
    
    def test_parse_week_ending_date_acceptable_variations(self):
        """Test parsing variations that should be acceptable in real usage."""
        acceptable_cases = [
            ("week_ending_2024-01-15 ", date(2024, 1, 15)),  # Trailing space (common typo)
            ("week_ending_+2024-01-15", date(2024, 1, 15)),  # Plus sign (int() accepts this)
            ("week_ending_2024-+01-15", date(2024, 1, 15)),  # Plus month (int() accepts this)
            ("week_ending_2024-01-+15", date(2024, 1, 15)),  # Plus day (int() accepts this)
        ]
        
        for directory_name, expected_result in acceptable_cases:
            result = self.file_discovery._parse_week_ending_date(directory_name)
            assert result == expected_result, f"Should accept variation: {directory_name}"
    
    # Tests for _parse_file_date()
    
    def test_parse_file_date_valid_formats(self):
        """Test parsing valid worklog filenames."""
        test_cases = [
            ("worklog_2024-01-15.txt", date(2024, 1, 15)),
            ("worklog_2023-12-31.txt", date(2023, 12, 31)),
            ("worklog_2024-02-29.txt", date(2024, 2, 29)),  # Leap year
            ("worklog_2025-06-06.txt", date(2025, 6, 6)),
            ("worklog_2020-01-01.txt", date(2020, 1, 1)),
            ("worklog_2024-07-04.txt", date(2024, 7, 4)),
        ]
        
        for filename, expected_date in test_cases:
            result = self.file_discovery._parse_file_date(filename)
            assert result == expected_date, f"Failed to parse {filename}"
    
    def test_parse_file_date_invalid_formats(self):
        """Test parsing invalid worklog filenames returns None."""
        invalid_cases = [
            "worklog_2024-13-01.txt",  # Invalid month
            "worklog_2024-02-30.txt",  # Invalid day for February
            "worklog_2023-02-29.txt",  # Not a leap year
            "worklog_2024-04-31.txt",  # Invalid day for April
            "worklog_2024-00-15.txt",  # Invalid month (0)
            "worklog_2024-01-00.txt",  # Invalid day (0)
            "worklog_2024/01/15.txt",  # Wrong separator
            "worklog_2024-01.txt",     # Missing day
            "worklog_2024.txt",        # Missing month and day
            "worklog_.txt",            # Empty date part
            "log_2024-01-15.txt",      # Wrong prefix
            "work_2024-01-15.txt",     # Missing "log"
            "2024-01-15.txt",          # No prefix
            "worklog_2024-01-15",      # Missing extension
            "worklog_2024-01-15.log",  # Wrong extension
            "",                        # Empty string
            "worklog_abc-def-ghi.txt", # Non-numeric
            "worklog_2024-ab-15.txt",  # Non-numeric month
            "worklog_2024-01-cd.txt",  # Non-numeric day
        ]
        
        for invalid_name in invalid_cases:
            result = self.file_discovery._parse_file_date(invalid_name)
            assert result is None, f"Should return None for invalid format: {invalid_name}"
    
    def test_parse_file_date_flexible_formats(self):
        """Test parsing flexible worklog filenames that should be valid."""
        flexible_cases = [
            ("worklog_2024-1-15.txt", date(2024, 1, 15)),   # Single digit month
            ("worklog_2024-01-5.txt", date(2024, 1, 5)),    # Single digit day
            ("worklog_2024-1-5.txt", date(2024, 1, 5)),     # Both single digit
            ("worklog_2024-12-1.txt", date(2024, 12, 1)),   # Single digit day in December
        ]
        
        for filename, expected_date in flexible_cases:
            result = self.file_discovery._parse_file_date(filename)
            assert result == expected_date, f"Failed to parse flexible format {filename}"
    
    def test_parse_file_date_edge_cases(self):
        """Test edge cases for file date parsing."""
        edge_cases = [
            # Leap year boundaries
            ("worklog_2024-02-29.txt", date(2024, 2, 29)),  # Valid leap year
            ("worklog_2023-02-29.txt", None),               # Invalid leap year
            ("worklog_2000-02-29.txt", date(2000, 2, 29)),  # Century leap year
            ("worklog_1900-02-29.txt", None),               # Century non-leap year
            
            # Month boundaries
            ("worklog_2024-01-31.txt", date(2024, 1, 31)),  # January 31st
            ("worklog_2024-04-30.txt", date(2024, 4, 30)),  # April 30th
            ("worklog_2024-04-31.txt", None),               # Invalid April 31st
            ("worklog_2024-06-30.txt", date(2024, 6, 30)),  # June 30th
            ("worklog_2024-06-31.txt", None),               # Invalid June 31st
            
            # Year boundaries
            ("worklog_2024-12-31.txt", date(2024, 12, 31)),  # End of year
            ("worklog_2025-01-01.txt", date(2025, 1, 1)),    # Start of year
            
            # Extreme values
            ("worklog_1000-01-01.txt", date(1000, 1, 1)),    # Very old date
            ("worklog_9999-12-31.txt", date(9999, 12, 31)),  # Very future date
        ]
        
        for filename, expected_result in edge_cases:
            result = self.file_discovery._parse_file_date(filename)
            assert result == expected_result, f"Edge case failed: {filename}"
    
    def test_parse_file_date_malformed_input(self):
        """Test parsing with malformed and unusual input strings."""
        malformed_cases = [
            None,                                    # None input
            123,                                     # Integer input
            [],                                      # List input
            {},                                      # Dict input
            "worklog_2024-01-15-extra.txt",         # Extra parts
            "worklog_2024--01-15.txt",              # Double dash
            "worklog_2024-01--15.txt",              # Double dash
            "worklog_-2024-01-15.txt",              # Negative year
            "worklog_2024.01.15.txt",               # Dots instead of dashes
            "worklog_2024_01_15.txt",               # Underscores
            "WORKLOG_2024-01-15.TXT",               # Uppercase
            "Worklog_2024-01-15.Txt",               # Mixed case
            "worklog_2024-01-15.TXT",               # Uppercase extension
        ]
        
        for malformed_input in malformed_cases:
            result = self.file_discovery._parse_file_date(malformed_input)
            assert result is None, f"Should return None for malformed input: {malformed_input}"
    
    def test_parse_file_date_acceptable_variations(self):
        """Test parsing variations that should be acceptable in real usage."""
        acceptable_cases = [
            ("worklog_2024-01-15.txt ", date(2024, 1, 15)),  # Trailing space (common typo)
            (" worklog_2024-01-15.txt", date(2024, 1, 15)),  # Leading space (common typo)
            ("worklog_+2024-01-15.txt", date(2024, 1, 15)),  # Plus sign (int() accepts this)
            ("worklog_2024-+01-15.txt", date(2024, 1, 15)),  # Plus month (int() accepts this)
            ("worklog_2024-01-+15.txt", date(2024, 1, 15)),  # Plus day (int() accepts this)
        ]
        
        for filename, expected_date in acceptable_cases:
            result = self.file_discovery._parse_file_date(filename)
            assert result == expected_date, f"Should accept variation: {filename}"
    
    # Consistency tests between both functions
    
    def test_date_parsing_consistency(self):
        """Test that both parsing functions handle dates consistently."""
        test_dates = [
            date(2024, 1, 15),
            date(2024, 2, 29),  # Leap year
            date(2023, 12, 31),
            date(2025, 6, 6),
        ]
        
        for test_date in test_dates:
            # Format as directory name and filename
            dir_name = f"week_ending_{test_date.year}-{test_date.month:02d}-{test_date.day:02d}"
            filename = f"worklog_{test_date.year}-{test_date.month:02d}-{test_date.day:02d}.txt"
            
            # Parse both
            parsed_dir_date = self.file_discovery._parse_week_ending_date(dir_name)
            parsed_file_date = self.file_discovery._parse_file_date(filename)
            
            # Both should return the same date
            assert parsed_dir_date == test_date, f"Directory parsing failed for {test_date}"
            assert parsed_file_date == test_date, f"File parsing failed for {test_date}"
            assert parsed_dir_date == parsed_file_date, f"Inconsistent parsing for {test_date}"
    
    def test_error_handling_consistency(self):
        """Test that both functions handle errors consistently."""
        invalid_dates = [
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid day
            "2023-02-29",  # Invalid leap year
            "abc-def-ghi", # Non-numeric
        ]
        
        for invalid_date in invalid_dates:
            # Format as directory name and filename
            dir_name = f"week_ending_{invalid_date}"
            filename = f"worklog_{invalid_date}.txt"
            
            # Both should return None
            parsed_dir_date = self.file_discovery._parse_week_ending_date(dir_name)
            parsed_file_date = self.file_discovery._parse_file_date(filename)
            
            assert parsed_dir_date is None, f"Directory parsing should return None for {invalid_date}"
            assert parsed_file_date is None, f"File parsing should return None for {invalid_date}"
    
    # Performance and boundary tests
    
    def test_parsing_performance(self):
        """Test that parsing functions perform well with many inputs."""
        import time
        
        # Generate test data
        valid_dirs = [f"week_ending_2024-{month:02d}-15" for month in range(1, 13)]
        valid_files = [f"worklog_2024-{month:02d}-15.txt" for month in range(1, 13)]
        
        # Time directory parsing
        start_time = time.time()
        for _ in range(100):  # Repeat for better measurement
            for dir_name in valid_dirs:
                self.file_discovery._parse_week_ending_date(dir_name)
        dir_time = time.time() - start_time
        
        # Time file parsing
        start_time = time.time()
        for _ in range(100):  # Repeat for better measurement
            for filename in valid_files:
                self.file_discovery._parse_file_date(filename)
        file_time = time.time() - start_time
        
        # Both should complete quickly (under 1 second for 1200 operations each)
        assert dir_time < 1.0, f"Directory parsing too slow: {dir_time:.3f}s"
        assert file_time < 1.0, f"File parsing too slow: {file_time:.3f}s"
    
    def test_memory_efficiency(self):
        """Test that parsing functions don't leak memory."""
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Parse many dates
        for i in range(1000):
            day = (i % 28) + 1  # Keep within valid day range
            dir_name = f"week_ending_2024-01-{day:02d}"
            filename = f"worklog_2024-01-{day:02d}.txt"
            
            self.file_discovery._parse_week_ending_date(dir_name)
            self.file_discovery._parse_file_date(filename)
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count shouldn't grow significantly
        object_growth = final_objects - initial_objects
        assert object_growth < 100, f"Too many objects created: {object_growth}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])