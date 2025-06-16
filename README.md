# Work Journal Summarizer

A Python program that generates weekly and monthly summaries of daily work journal text files using LLM APIs. The program processes free-form journal entries, automatically identifies projects and participants, and creates consolidated markdown summaries.

## Current Status: Phase 2 Complete ✅

**Phase 1: Foundation & CLI Interface** - ✅ Complete
- Robust command-line interface with comprehensive validation
- Date format and range validation
- Summary type validation
- Comprehensive test suite with 100% coverage
- Professional error handling and user feedback

**Phase 2: File Discovery Engine** - ✅ Complete
- Robust file discovery system for complex directory structures
- Work-period-based week ending directories (uses end date of your work period)
- Cross-year file discovery with proper directory navigation
- Missing file tracking without processing failure
- Comprehensive discovery statistics and reporting
- Configurable base path with `--base-path` argument
- Performance optimized for large date ranges
- Full test coverage with 26 additional tests

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup
1. Clone or download this repository
2. Navigate to the project directory
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line Interface

```bash
python work_journal_summarizer.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD --summary-type TYPE [--base-path PATH]
```

### Required Arguments

- `--start-date`: Start date in YYYY-MM-DD format (inclusive)
- `--end-date`: End date in YYYY-MM-DD format (inclusive)
- `--summary-type`: Either "weekly" or "monthly"

### Optional Arguments

- `--base-path`: Base directory path for journal files (default: `~/Desktop/worklogs/`)

### Examples

```bash
# Generate weekly summaries for April 2024 (default base path)
python work_journal_summarizer.py --start-date 2024-04-15 --end-date 2024-04-19 --summary-type weekly

# Generate monthly summaries with custom base path
python work_journal_summarizer.py --start-date 2024-01-01 --end-date 2024-12-31 --summary-type monthly --base-path /custom/path/

# Generate weekly summaries across year boundary
python work_journal_summarizer.py --start-date 2024-12-30 --end-date 2025-01-03 --summary-type weekly
```

### Help

```bash
python work_journal_summarizer.py --help
```

## Validation Rules

### Date Format
- Must be in YYYY-MM-DD format exactly
- Invalid formats will be rejected with clear error messages
- Examples of valid dates: `2024-04-01`, `2024-12-31`
- Examples of invalid dates: `2024/04/01`, `2024.04.01`, `2024-4-1`

### Date Range
- End date must be **after** start date (minimum 2-day range)
- Same start and end dates are not allowed
- Cross-year ranges are supported
- Invalid dates (like Feb 30) are rejected

### Summary Type
- Must be exactly "weekly" or "monthly" (case-sensitive)
- Invalid values like "daily", "yearly", "WEEKLY" are rejected

## Error Handling

The program provides clear, specific error messages for common issues:

### Date Format Errors
```
Invalid date format for start-date. Expected YYYY-MM-DD, got: 2024/04/01
```

### Date Range Errors
```
End date must be after start date. Start: 2024-04-30, End: 2024-04-01
```

### Summary Type Errors
```
Invalid summary type. Must be 'weekly' or 'monthly', got: 'daily'
```

### Invalid Dates
```
Invalid date for end-date: 2024-02-30. Please check that the date exists (e.g., Feb 30 is invalid).
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=work_journal_summarizer --cov-report=term-missing

# Run tests with HTML coverage report
pytest --cov=work_journal_summarizer --cov-report=html

# Run specific test class
pytest tests/test_cli.py::TestCLIArguments -v
```

### Test Coverage

The project maintains 100% test coverage with comprehensive test suites covering:

- ✅ Valid argument parsing for both weekly and monthly summaries
- ✅ Date format validation (various invalid formats)
- ✅ Date range validation (end before start, same dates)
- ✅ Summary type validation (invalid values, case sensitivity)
- ✅ Missing required arguments
- ✅ Help message content verification
- ✅ Leap year handling
- ✅ Cross-year date ranges
- ✅ Error message formatting

### Project Structure

```
JournalSummarizer/
├── work_journal_summarizer.py    # Main CLI module
├── file_discovery.py             # File discovery engine (Phase 2)
├── tests/                        # Test directory
│   ├── test_cli.py              # CLI tests (Phase 1)
│   └── test_file_discovery.py   # File discovery tests (Phase 2)
├── requirements.txt             # Project dependencies
├── README.md                    # This file
├── .gitignore                   # Python gitignore
└── phase1_implementation_plan.md # Implementation documentation
```

## Future Phases

### Phase 2: File Discovery Engine ✅ Complete
- ✅ Robust file discovery system for complex directory structures
- ✅ Work-period-based week ending directories
- ✅ Cross-year file discovery with proper directory navigation
- ✅ Missing file tracking without processing failure
- ✅ Comprehensive discovery statistics and reporting
- ✅ Configurable base path support
- ✅ Performance optimized for large date ranges

### Phase 3: Content Processing System (Planned)
- Encoding detection and handling
- Content sanitization and validation
- Error handling for corrupted files
- Memory-efficient processing

### Phase 4: LLM API Integration (Planned)
- AWS Bedrock API integration
- Entity extraction (projects, participants, tasks, themes)
- Robust error handling and retry logic
- API response validation

### Phase 5: Summary Generation System (Planned)
- Time period grouping (weekly/monthly)
- LLM-powered narrative summary generation
- Entity aggregation and deduplication
- Quality controls for summary content

### Phase 6: Output Management System (Planned)
- Professional markdown output generation
- Comprehensive metadata inclusion
- File naming conventions
- Processing statistics

### Phase 7: Error Handling & Logging (Planned)
- Production-grade logging system
- Progress tracking and user feedback
- Graceful degradation strategies
- Comprehensive error reporting

### Phase 8: Configuration Management & API Fallback (Planned)
- Configuration file support
- Dual API support (CBORG + Bedrock)
- Circuit breaker pattern
- Environment-based configuration

## Directory Structure (Phase 2 Implementation)

The system expects journal files in this structure:
```
~/Desktop/worklogs/
├── worklogs_2024/
│   ├── worklogs_2024-04/
│   │   └── week_ending_2024-04-19/        # End date of work period
│   │       ├── worklog_2024-04-15.txt
│   │       ├── worklog_2024-04-16.txt
│   │       ├── worklog_2024-04-17.txt
│   │       ├── worklog_2024-04-18.txt
│   │       └── worklog_2024-04-19.txt
│   └── worklogs_2024-12/
│       └── week_ending_2025-01-03/        # Cross-year work period
│           ├── worklog_2024-12-30.txt
│           └── worklog_2024-12-31.txt
└── worklogs_2025/
    └── worklogs_2025-01/
        └── week_ending_2025-01-03/        # Same work period, different year
            ├── worklog_2025-01-01.txt
            ├── worklog_2025-01-02.txt
            └── worklog_2025-01-03.txt
```

**Key Features:**
- `week_ending_YYYY-MM-DD` uses the **end date** of your work period (not calendar Sunday)
- Files are organized by their actual date in year/month directories
- Cross-year work periods are handled seamlessly
- Missing files are tracked but don't stop processing

## Expected Output Structure (Future Phases)

```
~/Desktop/worklogs/summaries/
├── weekly_summary_2024-04-01_to_2024-04-30_20250616_121600.md
├── monthly_summary_2024-01-01_to_2024-12-31_20250616_121700.md
└── error_logs/
    └── summarizer_20250616_121600.log
```

## Contributing

This project follows Test-Driven Development (TDD) principles:

1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor for clarity and maintainability
4. Maintain 100% test coverage
5. Add comprehensive docstrings and type hints

## License

This project is part of the Work Journal Summarizer implementation following the detailed blueprint specification.

---

**Current Phase**: 2/8 Complete ✅  
**Next Phase**: Content Processing System (Planned)
**Status**: Ready for Phase 3 implementation