#!/usr/bin/env python3
"""
Debug script for file extraction engine testing.
"""

from pathlib import Path
from datetime import date
from unittest.mock import patch, MagicMock
from file_discovery import FileDiscovery

def test_simple_extraction():
    """Simple test to debug the file extraction."""
    discovery = FileDiscovery(base_path="~/Desktop/test_worklogs/")
    
    # Create mock directory and files
    week_dir = Path("/test/week_ending_2024-04-15")
    directories = [(week_dir, date(2024, 4, 15))]
    
    # Mock file
    mock_file = MagicMock()
    mock_file.name = "worklog_2024-04-15.txt"
    mock_file.is_file.return_value = True
    mock_file.suffix = ".txt"
    
    print(f"Testing with directory: {week_dir}")
    print(f"Mock file: {mock_file.name}")
    
    # Test the method directly with mocking
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'iterdir', return_value=[mock_file]):
            found_files, missing_files = discovery._extract_files_from_directories(
                directories, date(2024, 4, 15), date(2024, 4, 15)
            )
            
            print(f"Found files: {len(found_files)}")
            print(f"Missing files: {len(missing_files)}")
            
            if found_files:
                print(f"Found file names: {[f.name for f in found_files]}")
            
            return len(found_files) > 0

if __name__ == "__main__":
    success = test_simple_extraction()
    print(f"Test {'PASSED' if success else 'FAILED'}")