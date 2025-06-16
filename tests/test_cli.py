"""
Comprehensive test suite for Work Journal Summarizer CLI interface.
Following Test-Driven Development approach - these tests are written first.
"""

import pytest
import sys
import io
from unittest.mock import patch
from datetime import date
import argparse

# Import the functions we'll be testing (these don't exist yet)
from work_journal_summarizer import parse_arguments, validate_date_range


class TestCLIArguments:
    """Test suite for command line argument parsing and validation."""

    def test_valid_arguments_weekly(self):
        """Test parsing valid arguments for weekly summary."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-04-01',
            '--end-date', '2024-04-30',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            args = parse_arguments()
            assert args.start_date == date(2024, 4, 1)
            assert args.end_date == date(2024, 4, 30)
            assert args.summary_type == 'weekly'

    def test_valid_arguments_monthly(self):
        """Test parsing valid arguments for monthly summary."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-01-01',
            '--end-date', '2024-12-31',
            '--summary-type', 'monthly'
        ]
        
        with patch('sys.argv', test_args):
            args = parse_arguments()
            assert args.start_date == date(2024, 1, 1)
            assert args.end_date == date(2024, 12, 31)
            assert args.summary_type == 'monthly'

    def test_valid_cross_year_range(self):
        """Test parsing valid cross-year date range."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-12-01',
            '--end-date', '2025-01-31',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            args = parse_arguments()
            assert args.start_date == date(2024, 12, 1)
            assert args.end_date == date(2025, 1, 31)
            assert args.summary_type == 'weekly'

    def test_invalid_date_format_slash_separator(self):
        """Test invalid date format with slash separators."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024/04/01',
            '--end-date', '2024-04-30',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_invalid_date_format_dot_separator(self):
        """Test invalid date format with dot separators."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024.04.01',
            '--end-date', '2024-04-30',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_invalid_date_format_missing_day(self):
        """Test invalid date format missing day component."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-04',
            '--end-date', '2024-04-30',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_invalid_date_format_missing_month(self):
        """Test invalid date format missing month component."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-01',
            '--end-date', '2024-04-30',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_invalid_date_nonexistent_date(self):
        """Test invalid date that doesn't exist (Feb 30)."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-02-30',
            '--end-date', '2024-04-30',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_invalid_date_invalid_month(self):
        """Test invalid month (13th month)."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-13-01',
            '--end-date', '2024-04-30',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_invalid_date_non_numeric(self):
        """Test invalid date with non-numeric components."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-ab-01',
            '--end-date', '2024-04-30',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_invalid_summary_type_daily(self):
        """Test invalid summary type 'daily'."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-04-01',
            '--end-date', '2024-04-30',
            '--summary-type', 'daily'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_invalid_summary_type_yearly(self):
        """Test invalid summary type 'yearly'."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-04-01',
            '--end-date', '2024-04-30',
            '--summary-type', 'yearly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_invalid_summary_type_case_sensitive(self):
        """Test that summary type is case-sensitive (WEEKLY should fail)."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-04-01',
            '--end-date', '2024-04-30',
            '--summary-type', 'WEEKLY'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_missing_required_argument_start_date(self):
        """Test missing required start-date argument."""
        test_args = [
            'work_journal_summarizer.py',
            '--end-date', '2024-04-30',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_missing_required_argument_end_date(self):
        """Test missing required end-date argument."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-04-01',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_missing_required_argument_summary_type(self):
        """Test missing required summary-type argument."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-04-01',
            '--end-date', '2024-04-30'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_help_message_content(self):
        """Test that help message contains required information."""
        test_args = ['work_journal_summarizer.py', '--help']
        
        with patch('sys.argv', test_args):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                with pytest.raises(SystemExit):
                    parse_arguments()
                
                help_output = mock_stdout.getvalue()
                assert '--start-date' in help_output
                assert '--end-date' in help_output
                assert '--summary-type' in help_output
                assert 'YYYY-MM-DD' in help_output
                assert 'weekly' in help_output
                assert 'monthly' in help_output


class TestDateRangeValidation:
    """Test suite for date range validation logic."""

    def test_valid_date_range_two_days(self):
        """Test valid date range with minimum 2-day span."""
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 2)
        
        # Should not raise any exception
        validate_date_range(start_date, end_date)

    def test_valid_date_range_one_month(self):
        """Test valid date range spanning one month."""
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 30)
        
        # Should not raise any exception
        validate_date_range(start_date, end_date)

    def test_valid_date_range_cross_year(self):
        """Test valid date range crossing year boundary."""
        start_date = date(2024, 12, 1)
        end_date = date(2025, 1, 31)
        
        # Should not raise any exception
        validate_date_range(start_date, end_date)

    def test_invalid_date_range_same_date(self):
        """Test invalid date range with same start and end date."""
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 1)
        
        with pytest.raises(ValueError) as exc_info:
            validate_date_range(start_date, end_date)
        
        assert "End date must be after start date" in str(exc_info.value)

    def test_invalid_date_range_end_before_start(self):
        """Test invalid date range with end date before start date."""
        start_date = date(2024, 4, 30)
        end_date = date(2024, 4, 1)
        
        with pytest.raises(ValueError) as exc_info:
            validate_date_range(start_date, end_date)
        
        assert "End date must be after start date" in str(exc_info.value)

    def test_invalid_date_range_error_message_format(self):
        """Test that error message includes both dates."""
        start_date = date(2024, 4, 30)
        end_date = date(2024, 4, 1)
        
        with pytest.raises(ValueError) as exc_info:
            validate_date_range(start_date, end_date)
        
        error_message = str(exc_info.value)
        assert "2024-04-30" in error_message
        assert "2024-04-01" in error_message


class TestLeapYearHandling:
    """Test suite for leap year date handling."""

    def test_leap_year_valid_feb_29(self):
        """Test valid Feb 29 in leap year 2024."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2024-02-29',
            '--end-date', '2024-03-01',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            args = parse_arguments()
            assert args.start_date == date(2024, 2, 29)

    def test_non_leap_year_invalid_feb_29(self):
        """Test invalid Feb 29 in non-leap year 2023."""
        test_args = [
            'work_journal_summarizer.py',
            '--start-date', '2023-02-29',
            '--end-date', '2023-03-01',
            '--summary-type', 'weekly'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                parse_arguments()