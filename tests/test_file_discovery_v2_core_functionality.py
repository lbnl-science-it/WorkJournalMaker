"""
Test suite for File Discovery Engine v2.0 core functionality.

This module tests the core directory-first discovery functionality including:
- Directory scanning and file extraction
- Performance monitoring and logging
"""

import pytest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from typing import List, Tuple

from file_discovery import FileDiscovery, FileDiscoveryResult


class TestCoreDiscoveryFunctionality:
    """Test core directory-first discovery functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.discovery = FileDiscovery(base_path=self.temp_dir)
        self.start_date = date(2024, 4, 15)
        self.end_date = date(2024, 4, 17)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_discover_files_returns_enhanced_result(self):
        """Test that discover_files returns FileDiscoveryResult with enhanced fields."""
        result = self.discovery.discover_files(self.start_date, self.end_date)
        
        # Verify all fields are present
        assert hasattr(result, 'found_files')
        assert hasattr(result, 'missing_files')
        assert hasattr(result, 'total_expected')
        assert hasattr(result, 'date_range')
        assert hasattr(result, 'processing_time')
        assert hasattr(result, 'discovered_weeks')
        assert hasattr(result, 'directory_scan_stats')
        
        # Verify enhanced fields are populated
        assert isinstance(result.discovered_weeks, list)
        assert isinstance(result.directory_scan_stats, dict)
    
    def test_directory_scan_stats_populated(self):
        """Test that directory scan statistics are properly populated."""
        result = self.discovery.discover_files(self.start_date, self.end_date)
        
        stats = result.directory_scan_stats
        expected_keys = [
            'directories_scanned', 'valid_week_directories', 'invalid_directories_skipped',
            'total_files_found', 'scan_duration_ms'
        ]
        
        for key in expected_keys:
            assert key in stats
            assert isinstance(stats[key], int)
    
    def test_discovered_weeks_format(self):
        """Test that discovered_weeks has correct format."""
        # Create test directory structure
        self._create_test_directory_structure()
        
        result = self.discovery.discover_files(self.start_date, self.end_date)
        
        # Verify discovered_weeks format
        for week_entry in result.discovered_weeks:
            assert isinstance(week_entry, tuple)
            assert len(week_entry) == 2
            assert isinstance(week_entry[0], date)  # week_ending_date
            assert isinstance(week_entry[1], int)   # file_count
    
    def test_processing_time_recorded(self):
        """Test that processing time is recorded."""
        result = self.discovery.discover_files(self.start_date, self.end_date)
        
        assert isinstance(result.processing_time, float)
        assert result.processing_time >= 0
    
    def test_date_range_preserved(self):
        """Test that date range is preserved in result."""
        result = self.discovery.discover_files(self.start_date, self.end_date)
        
        assert result.date_range == (self.start_date, self.end_date)
    
    def test_with_actual_files(self):
        """Test discovery with actual test files."""
        # Create test directory structure with files
        self._create_test_directory_structure()
        
        result = self.discovery.discover_files(self.start_date, self.end_date)
        
        # Should find at least one file
        assert len(result.found_files) >= 1
        assert result.total_expected >= 1
        
        # Should have discovered at least one week
        assert len(result.discovered_weeks) >= 1
    
    def test_cross_date_range_handling(self):
        """Test handling of cross-month and cross-year date ranges."""
        # Test cross-month range
        cross_month_start = date(2024, 4, 28)
        cross_month_end = date(2024, 5, 3)
        
        result = self.discovery.discover_files(cross_month_start, cross_month_end)
        
        assert isinstance(result, FileDiscoveryResult)
        assert result.date_range == (cross_month_start, cross_month_end)
        
        # Test cross-year range
        cross_year_start = date(2024, 12, 28)
        cross_year_end = date(2025, 1, 3)
        
        result = self.discovery.discover_files(cross_year_start, cross_year_end)
        
        assert isinstance(result, FileDiscoveryResult)
        assert result.date_range == (cross_year_start, cross_year_end)
    
    def _create_test_directory_structure(self):
        """Create minimal test directory structure."""
        year_dir = Path(self.temp_dir) / "worklogs_2024"
        month_dir = year_dir / "worklogs_2024-04"
        week_dir = month_dir / "week_ending_2024-04-15"
        
        week_dir.mkdir(parents=True, exist_ok=True)
        (week_dir / "worklog_2024-04-15.txt").write_text("test content")


class TestPerformanceAndLogging:
    """Test performance monitoring and logging functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.discovery = FileDiscovery(base_path=self.temp_dir)
        self.start_date = date(2024, 4, 15)
        self.end_date = date(2024, 4, 17)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('file_discovery.logging')
    def test_discovery_operation_logging(self, mock_logging):
        """Test that discovery operations are logged."""
        result = self.discovery.discover_files(self.start_date, self.end_date)
        
        # Verify logging was called (implementation logs discovery operations)
        assert mock_logging.info.called
    
    def test_performance_metrics_captured(self):
        """Test that performance metrics are captured."""
        result = self.discovery.discover_files(self.start_date, self.end_date)
        
        # Verify performance metrics are captured
        assert result.processing_time >= 0
        assert 'scan_duration_ms' in result.directory_scan_stats
        assert result.directory_scan_stats['scan_duration_ms'] >= 0
    
    def test_error_handling_graceful(self):
        """Test that errors are handled gracefully."""
        # Test with invalid base path to trigger error handling
        invalid_discovery = FileDiscovery(base_path="/nonexistent/path")
        
        # Should not raise exception but handle gracefully
        result = invalid_discovery.discover_files(self.start_date, self.end_date)
        
        # Verify graceful handling
        assert isinstance(result, FileDiscoveryResult)
        assert result.found_files == []
    
    def test_large_date_range_performance(self):
        """Test performance with large date ranges."""
        # Test with year-long range (the original problem scenario)
        large_start = date(2024, 1, 1)
        large_end = date(2024, 12, 31)
        
        result = self.discovery.discover_files(large_start, large_end)
        
        # Should complete in reasonable time
        assert result.processing_time < 5.0  # Should be much faster than 5 seconds
        assert isinstance(result, FileDiscoveryResult)
        assert result.date_range == (large_start, large_end)


class TestRealWorldScenarios:
    """Test real-world scenarios and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.discovery = FileDiscovery(base_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_original_failing_scenario(self):
        """Test the original failing scenario: 2024-07-01 to 2025-06-06."""
        start_date = date(2024, 7, 1)
        end_date = date(2025, 6, 6)
        
        result = self.discovery.discover_files(start_date, end_date)
        
        # Should handle the full date range without issues
        assert result.date_range == (start_date, end_date)
        assert isinstance(result.discovered_weeks, list)
        assert isinstance(result.directory_scan_stats, dict)
        
        # Should have reasonable performance
        assert result.processing_time < 2.0
    
    def test_empty_directory_structure(self):
        """Test with completely empty directory structure."""
        result = self.discovery.discover_files(date(2024, 4, 15), date(2024, 4, 17))
        
        assert result.found_files == []
        assert len(result.missing_files) >= 0  # May have expected files
        assert result.discovered_weeks == []
        assert result.directory_scan_stats['valid_week_directories'] == 0
    
    def test_partial_directory_structure(self):
        """Test with partial directory structure (missing some levels)."""
        # Create only year directory, no month or week directories
        year_dir = Path(self.temp_dir) / "worklogs_2024"
        year_dir.mkdir(exist_ok=True)
        
        result = self.discovery.discover_files(date(2024, 4, 15), date(2024, 4, 17))
        
        assert isinstance(result, FileDiscoveryResult)
        assert result.found_files == []
        assert result.discovered_weeks == []
    
    def test_mixed_valid_invalid_directories(self):
        """Test with mix of valid and invalid directory names."""
        base_path = Path(self.temp_dir)
        
        # Create valid structure
        valid_year = base_path / "worklogs_2024"
        valid_month = valid_year / "worklogs_2024-04"
        valid_week = valid_month / "week_ending_2024-04-15"
        valid_week.mkdir(parents=True, exist_ok=True)
        (valid_week / "worklog_2024-04-15.txt").write_text("valid content")
        
        # Create invalid directories that should be skipped
        (base_path / "invalid_year_dir").mkdir(exist_ok=True)
        (valid_year / "invalid_month_dir").mkdir(exist_ok=True)
        (valid_month / "invalid_week_dir").mkdir(exist_ok=True)
        
        result = self.discovery.discover_files(date(2024, 4, 15), date(2024, 4, 17))
        
        # Should find valid files and skip invalid directories
        assert len(result.found_files) >= 1
        assert len(result.discovered_weeks) >= 1
        assert result.directory_scan_stats['valid_week_directories'] >= 1


if __name__ == "__main__":
    pytest.main([__file__])