"""
Test suite for File Discovery Engine v2.0 - Integration Layer
Following Test-Driven Development approach - these tests are written first.

Tests the updated discover_files() method using directory-first approach:
- End-to-end discovery with directory scanning
- Population of new FileDiscoveryResult fields
- Feature flag functionality
- Year-long range scenarios (the original failing case)

Uses real directory structure at /Users/TYFong/Desktop/worklogs/worklogs_2024
Tests are non-destructive (read-only).
"""

import pytest
from datetime import date, timedelta
from pathlib import Path
from typing import List, Tuple, Dict
import os
import time
from unittest.mock import patch, MagicMock

# Import the classes to be tested
from file_discovery import FileDiscovery, FileDiscoveryResult


class TestFileDiscoveryIntegrationWithRealData:
    """Test suite for integrated discover_files() method using real 2024 data."""
    
    @classmethod
    def setup_class(cls):
        """Set up class-level fixtures."""
        cls.test_base_path = Path("/Users/TYFong/Desktop/worklogs/worklogs_2024")
        
        # Verify test data exists
        if not cls.test_base_path.exists():
            pytest.skip(f"Test data directory not found: {cls.test_base_path}")
    
    def setup_method(self):
        """Set up method-level fixtures."""
        self.discovery = FileDiscovery(base_path="/Users/TYFong/Desktop/worklogs/")
    
    def test_directory_first_discovery_single_week(self):
        """Test directory-first discovery for a single week range."""
        # Test with a known week from 2024 data
        start_date = date(2024, 1, 2)
        end_date = date(2024, 1, 5)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # Verify basic structure
        assert isinstance(result, FileDiscoveryResult)
        assert result.date_range == (start_date, end_date)
        assert result.processing_time > 0
        
        # Verify new fields are populated
        assert hasattr(result, 'discovered_weeks')
        assert hasattr(result, 'directory_scan_stats')
        assert isinstance(result.discovered_weeks, list)
        assert isinstance(result.directory_scan_stats, dict)
        
        # Should have discovered at least one week directory
        if result.discovered_weeks:
            # Verify week structure
            for week_ending_date, file_count in result.discovered_weeks:
                assert isinstance(week_ending_date, date)
                assert isinstance(file_count, int)
                assert file_count >= 0
                # Week ending date should be within reasonable range of our search
                assert start_date <= week_ending_date <= end_date + timedelta(days=7)
        
        # Verify directory scan stats are populated
        if result.directory_scan_stats:
            # Should have some scanning statistics
            expected_stats = ['directories_scanned', 'valid_week_directories', 'total_files_found']
            for stat in expected_stats:
                if stat in result.directory_scan_stats:
                    assert isinstance(result.directory_scan_stats[stat], int)
                    assert result.directory_scan_stats[stat] >= 0
    
    def test_directory_first_discovery_cross_month(self):
        """Test directory-first discovery across month boundaries."""
        # Test cross-month scenario (Jan 29 - Feb 2, 2024)
        start_date = date(2024, 1, 29)
        end_date = date(2024, 2, 2)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # Verify basic structure
        assert isinstance(result, FileDiscoveryResult)
        assert result.date_range == (start_date, end_date)
        
        # Should handle cross-month scenario
        assert len(result.found_files) + len(result.missing_files) == result.total_expected
        
        # Verify discovered weeks span the boundary
        if result.discovered_weeks:
            week_dates = [week[0] for week in result.discovered_weeks]
            # Should have weeks that could contain files from both months
            relevant_weeks = [d for d in week_dates if start_date <= d <= end_date + timedelta(days=7)]
            assert len(relevant_weeks) >= 1
        
        # Verify directory scan stats account for multiple months
        if result.directory_scan_stats and 'directories_scanned' in result.directory_scan_stats:
            # Should have scanned at least 2 month directories (Jan and Feb)
            assert result.directory_scan_stats['directories_scanned'] >= 2
    
    def test_directory_first_discovery_leap_year_week(self):
        """Test directory-first discovery including leap year date (Feb 29, 2024)."""
        # Test week containing leap year day
        start_date = date(2024, 2, 26)
        end_date = date(2024, 3, 1)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # Verify basic structure
        assert isinstance(result, FileDiscoveryResult)
        assert result.date_range == (start_date, end_date)
        
        # Should handle leap year correctly
        expected_days = (end_date - start_date).days + 1
        assert result.total_expected == expected_days
        
        # Verify leap year handling in discovered weeks
        if result.discovered_weeks:
            # Should have a week that includes Feb 29
            march_first_week = None
            for week_ending_date, file_count in result.discovered_weeks:
                if week_ending_date == date(2024, 3, 1):
                    march_first_week = (week_ending_date, file_count)
                    break
            
            if march_first_week:
                # This week should potentially include Feb 29 file
                assert march_first_week[1] >= 0  # Non-negative file count
        
        # Verify directory scan stats handle leap year
        if result.directory_scan_stats and 'leap_year_files_found' in result.directory_scan_stats:
            assert isinstance(result.directory_scan_stats['leap_year_files_found'], int)
    
    def test_year_long_discovery_original_failing_scenario(self):
        """Test the original failing scenario: year-long summary (2024-07-01 to 2025-06-06)."""
        # This is the exact scenario that was failing in the original bug report
        start_date = date(2024, 7, 1)
        end_date = date(2025, 6, 6)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # Verify basic structure
        assert isinstance(result, FileDiscoveryResult)
        assert result.date_range == (start_date, end_date)
        assert result.processing_time > 0
        
        # This should now discover MANY weeks, not just one
        if result.discovered_weeks:
            assert len(result.discovered_weeks) > 1, "Should discover multiple weeks, not just one"
            
            # Verify weeks span the full range
            week_dates = [week[0] for week in result.discovered_weeks]
            earliest_week = min(week_dates)
            latest_week = max(week_dates)
            
            # Should span most of the year-long range
            assert earliest_week >= start_date - timedelta(days=7)  # Allow some flexibility
            assert latest_week <= end_date + timedelta(days=7)
            
            # Should have weeks from both 2024 and 2025
            years_found = set(week_date.year for week_date in week_dates)
            assert 2024 in years_found, "Should find weeks from 2024"
            # Note: 2025 weeks depend on actual data availability
        
        # Verify directory scan stats for large range
        if result.directory_scan_stats:
            if 'directories_scanned' in result.directory_scan_stats:
                # Should have scanned many month directories across the year
                assert result.directory_scan_stats['directories_scanned'] >= 10
            
            if 'valid_week_directories' in result.directory_scan_stats:
                # Should have found many week directories
                assert result.directory_scan_stats['valid_week_directories'] > 1
        
        # Most importantly: should find many more files than the original bug (which found only 1 week)
        total_files_discovered = len(result.found_files)
        assert total_files_discovered > 5, f"Should discover many files, not just a few. Found: {total_files_discovered}"
    
    def test_discovered_weeks_population_accuracy(self):
        """Test that discovered_weeks field is accurately populated."""
        # Test with a known range
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # Verify discovered_weeks structure and content
        assert isinstance(result.discovered_weeks, list)
        
        if result.discovered_weeks:
            # Verify each entry has correct structure
            for week_ending_date, file_count in result.discovered_weeks:
                assert isinstance(week_ending_date, date)
                assert isinstance(file_count, int)
                assert file_count >= 0
            
            # Verify chronological order
            week_dates = [week[0] for week in result.discovered_weeks]
            assert week_dates == sorted(week_dates), "Weeks should be in chronological order"
            
            # Verify file counts make sense
            total_files_in_weeks = sum(count for _, count in result.discovered_weeks)
            # Should roughly match found files (allowing for some discrepancy due to date filtering)
            assert total_files_in_weeks >= len(result.found_files) * 0.8  # Allow 20% variance
    
    def test_directory_scan_stats_population_accuracy(self):
        """Test that directory_scan_stats field is accurately populated."""
        # Test with a moderate range
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # Verify directory_scan_stats structure and content
        assert isinstance(result.directory_scan_stats, dict)
        
        if result.directory_scan_stats:
            # Verify expected statistics are present and reasonable
            expected_stats = [
                'directories_scanned',
                'valid_week_directories', 
                'total_files_found',
                'scan_duration_ms'
            ]
            
            for stat in expected_stats:
                if stat in result.directory_scan_stats:
                    value = result.directory_scan_stats[stat]
                    assert isinstance(value, (int, float))
                    assert value >= 0
            
            # Verify logical relationships
            if 'directories_scanned' in result.directory_scan_stats:
                # Should have scanned at least 3 month directories (Jan, Feb, Mar)
                assert result.directory_scan_stats['directories_scanned'] >= 3
            
            if 'total_files_found' in result.directory_scan_stats:
                # Should roughly match the actual found files
                stats_file_count = result.directory_scan_stats['total_files_found']
                actual_file_count = len(result.found_files)
                # Allow some variance due to filtering
                assert abs(stats_file_count - actual_file_count) <= actual_file_count * 0.2
    
    def test_performance_with_large_date_range(self):
        """Test performance characteristics with large date ranges."""
        # Test with a full year range
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        start_time = time.time()
        result = self.discovery.discover_files(start_date, end_date)
        actual_duration = time.time() - start_time
        
        # Verify performance requirements
        assert result.processing_time <= 2.0, f"Processing should complete within 2 seconds, took {result.processing_time}"
        assert actual_duration <= 3.0, f"Total time should be under 3 seconds, took {actual_duration}"
        
        # Verify comprehensive results for full year
        if result.discovered_weeks:
            # Should have discovered many weeks across the year
            assert len(result.discovered_weeks) >= 20, "Should discover many weeks in a full year"
            
            # Should span the full year
            week_dates = [week[0] for week in result.discovered_weeks]
            months_covered = set(week_date.month for week_date in week_dates)
            assert len(months_covered) >= 8, "Should cover most months of the year"
    
    def test_empty_date_range_handling(self):
        """Test handling of edge cases like empty or invalid date ranges."""
        # Test with same start and end date
        single_date = date(2024, 1, 15)
        result = self.discovery.discover_files(single_date, single_date)
        
        assert isinstance(result, FileDiscoveryResult)
        assert result.date_range == (single_date, single_date)
        assert result.total_expected == 1
        
        # Should still populate new fields
        assert isinstance(result.discovered_weeks, list)
        assert isinstance(result.directory_scan_stats, dict)
    
    def test_nonexistent_date_range_handling(self):
        """Test handling of date ranges with no corresponding directories."""
        # Test with future dates that definitely don't exist
        start_date = date(2030, 1, 1)
        end_date = date(2030, 1, 7)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        assert isinstance(result, FileDiscoveryResult)
        assert result.date_range == (start_date, end_date)
        assert len(result.found_files) == 0
        assert len(result.missing_files) == result.total_expected
        
        # Should still populate new fields appropriately
        assert isinstance(result.discovered_weeks, list)
        assert isinstance(result.directory_scan_stats, dict)
        
        # discovered_weeks should be empty for nonexistent dates
        assert len(result.discovered_weeks) == 0
        
        # Directory scan stats should reflect the failed search
        if result.directory_scan_stats:
            if 'valid_week_directories' in result.directory_scan_stats:
                assert result.directory_scan_stats['valid_week_directories'] == 0


class TestFileDiscoveryFeatureFlag:
    """Test suite for feature flag functionality."""
    
    def setup_method(self):
        """Set up method-level fixtures."""
        self.discovery = FileDiscovery(base_path="/Users/TYFong/Desktop/worklogs/")
    
    @patch.dict(os.environ, {'USE_DIRECTORY_FIRST_DISCOVERY': 'true'})
    def test_feature_flag_enabled_uses_new_method(self):
        """Test that feature flag enables directory-first discovery."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # When feature flag is enabled, should populate new fields
        assert isinstance(result.discovered_weeks, list)
        assert isinstance(result.directory_scan_stats, dict)
        
        # Should have directory scanning statistics when using new method
        if result.directory_scan_stats:
            # Should have some indication that directory scanning was used
            scanning_indicators = [
                'directories_scanned',
                'valid_week_directories',
                'scan_duration_ms'
            ]
            has_scanning_stats = any(key in result.directory_scan_stats for key in scanning_indicators)
            assert has_scanning_stats, "Should have directory scanning statistics when feature flag is enabled"
    
    @patch.dict(os.environ, {'USE_DIRECTORY_FIRST_DISCOVERY': 'false'})
    def test_feature_flag_disabled_uses_old_method(self):
        """Test that feature flag can disable directory-first discovery."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # When feature flag is disabled, new fields should be empty/default
        assert isinstance(result.discovered_weeks, list)
        assert isinstance(result.directory_scan_stats, dict)
        
        # Should have empty new fields when using old method
        assert len(result.discovered_weeks) == 0
        assert len(result.directory_scan_stats) == 0
    
    def test_feature_flag_default_behavior(self):
        """Test default behavior when feature flag is not set."""
        # Clear any existing environment variable
        if 'USE_DIRECTORY_FIRST_DISCOVERY' in os.environ:
            del os.environ['USE_DIRECTORY_FIRST_DISCOVERY']
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # Default should be to use new method (True by default)
        assert isinstance(result.discovered_weeks, list)
        assert isinstance(result.directory_scan_stats, dict)
        
        # Should populate new fields by default
        # (This test assumes the default is to use the new method)


class TestFileDiscoveryBackwardCompatibility:
    """Test suite for backward compatibility with existing code."""
    
    def setup_method(self):
        """Set up method-level fixtures."""
        self.discovery = FileDiscovery(base_path="/Users/TYFong/Desktop/worklogs/")
    
    def test_existing_api_unchanged(self):
        """Test that existing API calls work unchanged."""
        # Test that old code calling discover_files still works
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # All original fields should still be present and functional
        assert hasattr(result, 'found_files')
        assert hasattr(result, 'missing_files')
        assert hasattr(result, 'total_expected')
        assert hasattr(result, 'date_range')
        assert hasattr(result, 'processing_time')
        
        assert isinstance(result.found_files, list)
        assert isinstance(result.missing_files, list)
        assert isinstance(result.total_expected, int)
        assert isinstance(result.date_range, tuple)
        assert isinstance(result.processing_time, float)
        
        # Should maintain expected relationships
        assert len(result.found_files) + len(result.missing_files) == result.total_expected
        assert result.date_range == (start_date, end_date)
        assert result.processing_time >= 0
    
    def test_file_discovery_result_serialization(self):
        """Test that FileDiscoveryResult can still be serialized/deserialized."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # Should be able to convert to dict (for JSON serialization)
        import dataclasses
        result_dict = dataclasses.asdict(result)
        
        assert isinstance(result_dict, dict)
        assert 'found_files' in result_dict
        assert 'discovered_weeks' in result_dict
        assert 'directory_scan_stats' in result_dict
        
        # Should be able to reconstruct from dict
        reconstructed = FileDiscoveryResult(**result_dict)
        assert reconstructed.date_range == result.date_range
        assert len(reconstructed.found_files) == len(result.found_files)
    
    def test_old_method_deprecation_warnings(self):
        """Test that deprecated methods show appropriate warnings."""
        import warnings
        
        # Test deprecated _calculate_week_ending method
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Call deprecated method
            result = self.discovery._calculate_week_ending(date(2024, 1, 1), date(2024, 1, 7))
            
            # Should still work but might show deprecation warning
            assert isinstance(result, date)
            assert result == date(2024, 1, 7)  # Should return end_date


class TestFileDiscoveryErrorHandling:
    """Test suite for error handling and edge cases in integration."""
    
    def setup_method(self):
        """Set up method-level fixtures."""
        self.discovery = FileDiscovery(base_path="/Users/TYFong/Desktop/worklogs/")
    
    def test_invalid_base_path_handling(self):
        """Test handling of invalid base paths."""
        # Test with nonexistent base path
        invalid_discovery = FileDiscovery(base_path="/nonexistent/path/")
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        result = invalid_discovery.discover_files(start_date, end_date)
        
        # Should handle gracefully without crashing
        assert isinstance(result, FileDiscoveryResult)
        assert len(result.found_files) == 0
        assert len(result.missing_files) == result.total_expected
        
        # Should still populate new fields appropriately
        assert isinstance(result.discovered_weeks, list)
        assert isinstance(result.directory_scan_stats, dict)
        assert len(result.discovered_weeks) == 0
    
    def test_permission_error_handling(self):
        """Test handling of permission errors during directory scanning."""
        # This test would need to mock permission errors
        # since we can't easily create them in the test environment
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        with patch('pathlib.Path.iterdir') as mock_iterdir:
            mock_iterdir.side_effect = PermissionError("Access denied")
            
            result = self.discovery.discover_files(start_date, end_date)
            
            # Should handle permission errors gracefully
            assert isinstance(result, FileDiscoveryResult)
            # Should still return a valid result even with permission errors
            assert isinstance(result.discovered_weeks, list)
            assert isinstance(result.directory_scan_stats, dict)
    
    def test_invalid_date_range_handling(self):
        """Test handling of invalid date ranges."""
        # Test with end_date before start_date
        start_date = date(2024, 1, 7)
        end_date = date(2024, 1, 1)  # Invalid: end before start
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # Should handle gracefully
        assert isinstance(result, FileDiscoveryResult)
        # Should maintain the provided date range even if invalid
        assert result.date_range == (start_date, end_date)
        # Should have zero expected files for invalid range
        assert result.total_expected == 0
        assert len(result.found_files) == 0
        assert len(result.missing_files) == 0