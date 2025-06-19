"""
File Discovery Engine for Work Journal Summarizer - Phase 2

This module implements robust file discovery for the complex directory structure:
~/Desktop/worklogs/worklogs_YYYY/worklogs_YYYY-MM/week_ending_YYYY-MM-DD/worklog_YYYY-MM-DD.txt

Key features:
- Handles cross-year date ranges
- Uses work period end date for week_ending directory names
- Tracks missing files without failing
- Provides comprehensive discovery statistics
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import List, Tuple, Dict
import time


@dataclass
class FileDiscoveryResult:
    """
    Result of file discovery operation with comprehensive statistics.
    
    Enhanced for File Discovery Engine v2.0 with directory scanning capabilities.
    Maintains backward compatibility with existing code.
    """
    # Original fields (maintained for backward compatibility)
    found_files: List[Path]
    missing_files: List[Path]
    total_expected: int
    date_range: Tuple[date, date]
    processing_time: float
    
    # New fields for directory-first discovery (v2.0)
    discovered_weeks: List[Tuple[date, int]] = field(default_factory=list)
    """
    List of discovered week directories with file counts.
    Each tuple contains (week_ending_date, file_count).
    Empty list by default for backward compatibility.
    """
    
    directory_scan_stats: Dict[str, int] = field(default_factory=dict)
    """
    Directory scanning statistics for debugging and monitoring.
    Contains metrics like directories_scanned, valid_week_directories, etc.
    Empty dict by default for backward compatibility.
    """


class FileDiscovery:
    """
    Handles discovery of journal files in the complex directory structure.
    
    Directory Structure:
    - Base: ~/Desktop/worklogs/
    - Year: worklogs_YYYY/
    - Month: worklogs_YYYY-MM/
    - Week: week_ending_YYYY-MM-DD/ (end date of work period)
    - File: worklog_YYYY-MM-DD.txt
    """
    
    def __init__(self, base_path: str = "~/Desktop/worklogs/"):
        """
        Initialize FileDiscovery with base path.
        
        Args:
            base_path: Base directory path for worklogs (supports ~ expansion)
        """
        self.base_path = Path(base_path).expanduser()
    
    def discover_files(self, start_date: date, end_date: date) -> FileDiscoveryResult:
        """
        Discover all journal files in the specified date range.
        
        Args:
            start_date: Start date of the range (inclusive)
            end_date: End date of the range (inclusive)
            
        Returns:
            FileDiscoveryResult: Complete discovery results with statistics
        """
        start_time = time.time()
        
        # Generate all dates in the range
        date_range = self._generate_date_range(start_date, end_date)
        
        # Discover files for each date
        found_files = []
        missing_files = []
        
        for target_date in date_range:
            # Calculate week ending date for THIS specific file
            week_ending_date = self._calculate_week_ending_for_date(target_date)
            file_path = self._construct_file_path(target_date, week_ending_date)
            
            if file_path.exists():
                found_files.append(file_path)
            else:
                missing_files.append(file_path)
        
        processing_time = time.time() - start_time
        
        return FileDiscoveryResult(
            found_files=found_files,
            missing_files=missing_files,
            total_expected=len(date_range),
            date_range=(start_date, end_date),
            processing_time=processing_time
        )
    
    def _generate_date_range(self, start_date: date, end_date: date) -> List[date]:
        """
        Generate all dates in the range (inclusive).
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range
            
        Returns:
            List[date]: All dates in the range in chronological order
        """
        dates = []
        current_date = start_date
        
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        
        return dates
    
    def _calculate_week_ending(self, start_date: date, end_date: date) -> date:
        """
        DEPRECATED: Calculate week ending date based on the work period end date.
        
        This method is kept for backward compatibility but should not be used
        for file discovery. Use _calculate_week_ending_for_date instead.
        
        Args:
            start_date: Start date of the work period
            end_date: End date of the work period
            
        Returns:
            date: The end date of the work period (used for week_ending directory)
        """
        return end_date
    
    def _calculate_week_ending_for_date(self, target_date: date) -> date:
        """
        Calculate the proper week ending date for a specific file date.
        
        Based on your file structure example (week_ending_2024-12-20), it appears
        that the week_ending date corresponds to the actual file date when the
        file represents the end of a work week.
        
        For now, we'll use the target_date itself as the week_ending date,
        but this can be adjusted based on your actual weekly structure.
        
        Args:
            target_date: The date of the specific journal file
            
        Returns:
            date: The week ending date for this file's directory structure
        """
        # For now, use the target date itself as week ending
        # This matches your example: worklog_2024-12-20.txt in week_ending_2024-12-20/
        return target_date
    
    def _construct_file_path(self, target_date: date, week_ending_date: date) -> Path:
        """
        Construct expected file path for the given date.
        
        Path structure:
        base_path/worklogs_YYYY/worklogs_YYYY-MM/week_ending_YYYY-MM-DD/worklog_YYYY-MM-DD.txt
        
        Args:
            target_date: Date of the journal file
            week_ending_date: End date of the work period (for directory name)
            
        Returns:
            Path: Complete path to the expected journal file
        """
        # Year directory (based on file date)
        year_dir = f"worklogs_{target_date.year}"
        
        # Month directory (based on file date)
        month_dir = f"worklogs_{target_date.year}-{target_date.month:02d}"
        
        # Week directory (based on work period end date)
        week_dir = f"week_ending_{week_ending_date.year}-{week_ending_date.month:02d}-{week_ending_date.day:02d}"
        
        # File name (based on file date)
        filename = f"worklog_{target_date.year}-{target_date.month:02d}-{target_date.day:02d}.txt"
        
        # Construct complete path
        return self.base_path / year_dir / month_dir / week_dir / filename