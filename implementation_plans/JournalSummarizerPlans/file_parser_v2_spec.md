# File Discovery Engine v2.0 - Developer Specification

## Executive Summary

This specification addresses a critical bug in the Work Journal Summarizer's file discovery logic that causes year-long summaries to only process one week of data instead of the full date range. The root cause is a flawed week-ending calculation that uses the entire date range's end date for all files, resulting in incorrect file paths.

## Problem Analysis

### Current Issue
- **Symptom**: Year-long summary (2024-07-01 to 2025-06-06) only generates one week summary
- **Root Cause**: `_calculate_week_ending()` uses range end date (2025-06-06) for ALL files
- **Impact**: 1.5% file discovery success rate, missing 336+ files
- **Example**: Looking for `week_ending_2025-06-06/worklog_2024-12-20.txt` instead of `week_ending_2024-12-20/worklog_2024-12-20.txt`

### Diagnostic Evidence
```bash
# Current (broken) paths being generated:
/Users/TYFong/Desktop/worklogs/worklogs_2024/worklogs_2024-12/week_ending_2025-06-06/worklog_2024-12-20.txt

# Actual file structure:
/Users/TYFong/Desktop/worklogs/worklogs_2024/worklogs_2024-12/week_ending_2024-12-20/worklog_2024-12-20.txt
```

### File Structure Analysis
Based on actual directory scanning:
```
week_ending_2024-12-13/
├── worklog_2024-12-09.txt
├── worklog_2024-12-10.txt
├── worklog_2024-12-11.txt
├── worklog_2024-12-12.txt
└── worklog_2024-12-13.txt

week_ending_2024-12-20/
├── worklog_2024-12-16.txt
├── worklog_2024-12-18.txt
├── worklog_2024-12-19.txt
└── worklog_2024-12-20.txt
```

**Key Insights:**
- Week ending dates are not always Fridays (can be any day)
- Multiple daily files exist within each week_ending directory
- Directory names are the authoritative source of week boundaries

## Proposed Solution: Directory-First Discovery

### Architecture Overview

Replace the current date-calculation approach with a **directory-first discovery pattern**:

1. **Scan for existing `week_ending_*` directories** within the date range
2. **Extract all `.txt` files** from discovered directories
3. **Use directory names** as authoritative week ending dates
4. **Filter results** by the specified date range

### Benefits
- ✅ **Eliminates complex date calculations**
- ✅ **Uses existing structure as source of truth**
- ✅ **Handles any week ending pattern naturally**
- ✅ **More robust and maintainable**
- ✅ **Fixes the 1.5% → ~95%+ success rate issue**

## Technical Requirements

### Core Components

#### 1. Directory Scanner
```python
def _discover_week_ending_directories(self, start_date: date, end_date: date) -> List[Tuple[Path, date]]:
    """
    Scan for week_ending_YYYY-MM-DD directories within date range.
    
    Returns:
        List of (directory_path, week_ending_date) tuples
    """
```

#### 2. File Extractor
```python
def _extract_files_from_directories(self, directories: List[Tuple[Path, date]], 
                                  start_date: date, end_date: date) -> Tuple[List[Path], List[Path]]:
    """
    Extract all .txt files from directories, filtering by date range.
    
    Returns:
        (found_files, missing_expected_files)
    """
```

#### 3. Date Parser
```python
def _parse_week_ending_date(self, directory_name: str) -> Optional[date]:
    """
    Parse week_ending_YYYY-MM-DD directory name to extract date.
    
    Args:
        directory_name: e.g., "week_ending_2024-12-20"
    
    Returns:
        date object or None if invalid format
    """
```

### Data Structures

#### Enhanced FileDiscoveryResult
```python
@dataclass
class FileDiscoveryResult:
    found_files: List[Path]
    missing_files: List[Path]
    total_expected: int
    date_range: Tuple[date, date]
    processing_time: float
    # New fields:
    discovered_weeks: List[Tuple[date, int]]  # (week_ending_date, file_count)
    directory_scan_stats: Dict[str, int]      # scanning statistics
```

### Implementation Strategy

#### Phase 1: Core Directory Discovery
```python
def discover_files(self, start_date: date, end_date: date) -> FileDiscoveryResult:
    """
    Main discovery method using directory-first approach.
    """
    start_time = time.time()
    
    # Step 1: Discover week_ending directories in range
    week_directories = self._discover_week_ending_directories(start_date, end_date)
    
    # Step 2: Extract files from directories
    found_files, missing_files = self._extract_files_from_directories(
        week_directories, start_date, end_date
    )
    
    # Step 3: Calculate statistics
    processing_time = time.time() - start_time
    
    return FileDiscoveryResult(
        found_files=found_files,
        missing_files=missing_files,
        total_expected=len(found_files) + len(missing_files),
        date_range=(start_date, end_date),
        processing_time=processing_time,
        discovered_weeks=[(week_date, len(files)) for week_date, files in week_directories],
        directory_scan_stats=self._generate_scan_stats()
    )
```

#### Phase 2: Directory Scanning Logic
```python
def _discover_week_ending_directories(self, start_date: date, end_date: date) -> List[Tuple[Path, date]]:
    """
    Scan base_path for week_ending directories within date range.
    
    Directory structure:
    ~/Desktop/worklogs/worklogs_YYYY/worklogs_YYYY-MM/week_ending_YYYY-MM-DD/
    """
    directories = []
    
    # Scan year directories (worklogs_YYYY)
    for year in range(start_date.year, end_date.year + 1):
        year_path = self.base_path / f"worklogs_{year}"
        if not year_path.exists():
            continue
            
        # Scan month directories (worklogs_YYYY-MM)
        for month_path in year_path.glob("worklogs_*"):
            if not month_path.is_dir():
                continue
                
            # Scan week_ending directories
            for week_path in month_path.glob("week_ending_*"):
                week_date = self._parse_week_ending_date(week_path.name)
                if week_date and start_date <= week_date <= end_date:
                    directories.append((week_path, week_date))
    
    return sorted(directories, key=lambda x: x[1])  # Sort by date
```

#### Phase 3: File Extraction Logic
```python
def _extract_files_from_directories(self, directories: List[Tuple[Path, date]], 
                                  start_date: date, end_date: date) -> Tuple[List[Path], List[Path]]:
    """
    Extract .txt files from directories, filtering by date range.
    """
    found_files = []
    missing_files = []
    
    for week_dir, week_ending_date in directories:
        # Find all .txt files in this week directory
        txt_files = list(week_dir.glob("worklog_*.txt"))
        
        for file_path in txt_files:
            # Parse file date from filename (worklog_YYYY-MM-DD.txt)
            file_date = self._parse_file_date(file_path.name)
            
            if file_date and start_date <= file_date <= end_date:
                if file_path.exists():
                    found_files.append(file_path)
                else:
                    missing_files.append(file_path)
    
    return found_files, missing_files
```

## Error Handling Strategy

### Graceful Degradation
- **Invalid directory names**: Log warning, skip directory
- **Corrupted file paths**: Log error, continue processing
- **Permission errors**: Log error with recovery suggestions
- **Missing year/month directories**: Expected behavior, log info

### Logging Categories
```python
# File system issues
logger.log_warning_with_category(
    ErrorCategory.FILE_SYSTEM,
    f"Invalid week_ending directory format: {dir_name}",
    recovery_action="Check directory naming convention"
)

# Discovery statistics
logger.log_info(
    f"Discovered {len(directories)} week directories, "
    f"{len(found_files)} files in date range"
)
```

### Recovery Actions
- **Low success rate (<50%)**: Suggest checking base path and date range
- **No directories found**: Verify directory structure and permissions
- **Date parsing errors**: Log specific format issues for debugging

## Testing Plan

### Unit Tests

#### 1. Directory Discovery Tests
```python
def test_discover_week_ending_directories():
    """Test directory scanning with various date ranges."""
    # Test single month
    # Test cross-year range
    # Test invalid directories
    # Test empty directories
```

#### 2. Date Parsing Tests
```python
def test_parse_week_ending_date():
    """Test parsing of directory names."""
    # Valid formats: "week_ending_2024-12-20"
    # Invalid formats: "week_ending_invalid", "not_week_ending"
    # Edge cases: leap years, month boundaries
```

#### 3. File Extraction Tests
```python
def test_extract_files_from_directories():
    """Test file extraction and filtering."""
    # Test date range filtering
    # Test file existence checking
    # Test multiple files per directory
```

### Integration Tests

#### 1. End-to-End Discovery Test
```python
def test_year_long_discovery():
    """Test the exact failing scenario: 2024-07-01 to 2025-06-06."""
    discovery = FileDiscovery()
    result = discovery.discover_files(date(2024, 7, 1), date(2025, 6, 6))
    
    # Should find significantly more than 5 files
    assert len(result.found_files) > 100
    # Should have high success rate
    assert (len(result.found_files) / result.total_expected) > 0.8
```

#### 2. Performance Test
```python
def test_large_date_range_performance():
    """Test performance with multi-year ranges."""
    # Should complete within reasonable time
    # Should handle memory efficiently
```

### Validation Tests

#### 1. File Structure Validation
```python
def test_actual_file_structure():
    """Validate against known good file."""
    # Test with known file: /Users/TYFong/Desktop/worklogs/worklogs_2024/worklogs_2024-12/week_ending_2024-12-20/worklog_2024-12-20.txt
    # Verify it's discovered correctly
```

#### 2. Comparison Test
```python
def test_old_vs_new_discovery():
    """Compare old and new discovery methods."""
    # Run both methods on same date range
    # New method should find significantly more files
```

## Migration Strategy

### Backward Compatibility
- Keep existing `_calculate_week_ending()` method for compatibility
- Mark as deprecated with clear migration path
- Maintain existing `FileDiscoveryResult` structure

### Rollout Plan
1. **Phase 1**: Implement new methods alongside existing ones
2. **Phase 2**: Add feature flag to switch between old/new logic
3. **Phase 3**: Default to new logic after testing
4. **Phase 4**: Remove deprecated methods in next major version

### Risk Mitigation
- **Extensive testing** with actual file structure
- **Gradual rollout** with fallback capability
- **Comprehensive logging** for debugging
- **Performance monitoring** for large date ranges

## Success Metrics

### Primary Metrics
- **File discovery success rate**: 1.5% → 95%+
- **Year-long summary completeness**: 1 week → full year
- **Processing time**: Should remain under 1 second for year-long ranges

### Secondary Metrics
- **Error rate reduction**: Fewer file system warnings
- **Code maintainability**: Simpler logic, fewer edge cases
- **User satisfaction**: Correct summary output format

## Implementation Timeline

### Week 1: Core Implementation
- [ ] Implement directory scanning logic
- [ ] Add date parsing utilities
- [ ] Create file extraction methods
- [ ] Update main discovery method

### Week 2: Testing & Validation
- [ ] Write comprehensive unit tests
- [ ] Test with actual file structure
- [ ] Performance testing with large ranges
- [ ] Integration testing with summarizer

### Week 3: Integration & Deployment
- [ ] Integrate with existing codebase
- [ ] Add feature flag for gradual rollout
- [ ] Update documentation
- [ ] Deploy and monitor

## Conclusion

This specification provides a complete roadmap for fixing the critical file discovery bug by replacing complex date calculations with a simple, robust directory-first approach. The solution leverages the existing file structure as the source of truth, eliminating edge cases and significantly improving reliability.

The proposed architecture is more maintainable, handles any week ending pattern naturally, and should increase the file discovery success rate from 1.5% to 95%+, enabling proper year-long summaries with multiple weekly entries as desired.