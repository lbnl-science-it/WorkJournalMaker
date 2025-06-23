#!/usr/bin/env python3
"""
Fixed debug script for file extraction engine testing.
"""

from pathlib import Path
from datetime import date
from unittest.mock import patch, MagicMock
from file_discovery import FileDiscovery

def test_fixed_extraction():
    """Fixed test using proper mocking approach."""
    discovery = FileDiscovery(base_path="~/Desktop/test_worklogs/")
    
    # Create mock directories and files
    week_dir1 = Path("/test/week_ending_2024-04-15")
    week_dir2 = Path("/test/week_ending_2024-04-22")
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
    
    print(f"Testing with directories: {[str(d[0]) for d in directories]}")
    
    # Mock the specific Path instances
    week_dir1.exists.return_value = True
    week_dir2.exists.return_value = True
    
    week_dir1.iterdir.return_value = [file1_dir1, file2_dir1]
    week_dir2.iterdir.return_value = [file1_dir2, file2_dir2]
    
    print("Starting file extraction...")
    found_files, missing_files = discovery._extract_files_from_directories(
        directories, date(2024, 4, 15), date(2024, 4, 23)
    )
    
    print(f"Found files: {len(found_files)}")
    print(f"Missing files: {len(missing_files)}")
    
    if found_files:
        print(f"Found file names: {[f.name for f in found_files]}")
    
    return len(found_files) > 0

if __name__ == "__main__":
    success = test_fixed_extraction()
    print(f"Test {'PASSED' if success else 'FAILED'}")