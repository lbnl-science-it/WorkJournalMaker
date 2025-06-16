#!/usr/bin/env python3
"""
Work Journal Summarizer - Phase 2: Foundation & File Discovery

A Python program that generates weekly and monthly summaries of daily work journal
text files using LLM APIs. This module implements the command-line interface with
comprehensive argument validation and robust file discovery.

Author: Work Journal Summarizer Project
Version: Phase 2 - File Discovery Engine
"""

import argparse
import datetime
import sys
from pathlib import Path
from typing import Tuple

# Import Phase 2 components
from file_discovery import FileDiscovery, FileDiscoveryResult


def parse_arguments() -> argparse.Namespace:
    """
    Parse and validate command line arguments.
    
    Returns:
        argparse.Namespace: Parsed and validated arguments with date objects
        
    Raises:
        SystemExit: If arguments are invalid or help is requested
    """
    parser = argparse.ArgumentParser(
        description='Generate weekly or monthly summaries of work journal entries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --start-date 2024-04-01 --end-date 2024-04-30 --summary-type weekly
  %(prog)s --start-date 2024-01-01 --end-date 2024-12-31 --summary-type monthly
  %(prog)s --start-date 2024-12-01 --end-date 2025-01-31 --summary-type weekly

Date Format:
  All dates must be in YYYY-MM-DD format (e.g., 2024-04-01)
  End date must be after start date (minimum 2-day range)

Summary Types:
  weekly  - Generate weekly summaries grouped by calendar weeks
  monthly - Generate monthly summaries grouped by calendar months
        """
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        required=True,
        help='Start date in YYYY-MM-DD format (inclusive)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        required=True,
        help='End date in YYYY-MM-DD format (inclusive)'
    )
    
    parser.add_argument(
        '--summary-type',
        type=str,
        required=True,
        choices=['weekly', 'monthly'],
        help='Type of summary to generate: weekly or monthly'
    )
    
    parser.add_argument(
        '--base-path',
        type=str,
        default="~/Desktop/worklogs/",
        help='Base directory path for journal files (default: ~/Desktop/worklogs/)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate and convert date strings to date objects
    try:
        start_date = _parse_date_string(args.start_date, 'start-date')
        end_date = _parse_date_string(args.end_date, 'end-date')
    except ValueError as e:
        parser.error(str(e))
    
    # Validate date range
    try:
        validate_date_range(start_date, end_date)
    except ValueError as e:
        parser.error(str(e))
    
    # Replace string dates with date objects
    args.start_date = start_date
    args.end_date = end_date
    
    return args


def _parse_date_string(date_string: str, field_name: str) -> datetime.date:
    """
    Parse a date string in YYYY-MM-DD format.
    
    Args:
        date_string: Date string to parse
        field_name: Name of the field for error messages
        
    Returns:
        datetime.date: Parsed date object
        
    Raises:
        ValueError: If date format is invalid or date doesn't exist
    """
    try:
        return datetime.datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError as e:
        if 'does not match format' in str(e):
            raise ValueError(
                f"Invalid date format for {field_name}. "
                f"Expected YYYY-MM-DD, got: {date_string}"
            )
        else:
            # Handle invalid dates like 2024-02-30, 2024-13-01
            raise ValueError(
                f"Invalid date for {field_name}: {date_string}. "
                f"Please check that the date exists (e.g., Feb 30 is invalid)."
            )


def validate_date_range(start_date: datetime.date, end_date: datetime.date) -> None:
    """
    Validate that the date range is logical (end_date > start_date).
    
    Args:
        start_date: Start date of the range
        end_date: End date of the range
        
    Raises:
        ValueError: If end_date is not after start_date
    """
    if end_date <= start_date:
        raise ValueError(
            f"End date must be after start date. "
            f"Start: {start_date}, End: {end_date}"
        )


def main() -> None:
    """
    Main entry point for the Work Journal Summarizer.
    
    This function handles the complete workflow:
    1. Parse and validate command line arguments
    2. Discover journal files in the specified date range
    3. Display discovery statistics
    4. Prepare for future phase integration
    """
    try:
        # Parse and validate arguments
        args = parse_arguments()
        
        # Display successful validation message
        print("✅ Work Journal Summarizer - Phase 2")
        print("=" * 50)
        print(f"Start Date: {args.start_date}")
        print(f"End Date: {args.end_date}")
        print(f"Summary Type: {args.summary_type}")
        print(f"Base Path: {args.base_path}")
        print(f"Date Range: {(args.end_date - args.start_date).days + 1} days")
        print()
        
        # Initialize file discovery system
        print("🔍 Discovering journal files...")
        file_discovery = FileDiscovery(base_path=args.base_path)
        
        # Discover files in the specified date range
        discovery_result = file_discovery.discover_files(args.start_date, args.end_date)
        
        # Display discovery statistics
        print("📊 File Discovery Results:")
        print("-" * 30)
        print(f"Total files expected: {discovery_result.total_expected}")
        print(f"Files found: {len(discovery_result.found_files)}")
        print(f"Files missing: {len(discovery_result.missing_files)}")
        print(f"Discovery success rate: {len(discovery_result.found_files)/discovery_result.total_expected*100:.1f}%")
        print(f"Processing time: {discovery_result.processing_time:.3f} seconds")
        print()
        
        # Display found files (first 5 for brevity)
        if discovery_result.found_files:
            print("📁 Found Files (showing first 5):")
            for i, file_path in enumerate(discovery_result.found_files[:5]):
                print(f"  {i+1}. {file_path}")
            if len(discovery_result.found_files) > 5:
                print(f"  ... and {len(discovery_result.found_files) - 5} more files")
            print()
        
        # Display missing files (first 5 for brevity)
        if discovery_result.missing_files:
            print("❌ Missing Files (showing first 5):")
            for i, file_path in enumerate(discovery_result.missing_files[:5]):
                print(f"  {i+1}. {file_path}")
            if len(discovery_result.missing_files) > 5:
                print(f"  ... and {len(discovery_result.missing_files) - 5} more missing files")
            print()
        
        # Calculate summary estimates
        total_days = (args.end_date - args.start_date).days + 1
        if args.summary_type == 'weekly':
            estimated_weeks = (total_days + 6) // 7  # Round up
            print(f"📈 Estimated weekly summaries: {estimated_weeks}")
        else:  # monthly
            start_month = args.start_date.replace(day=1)
            end_month = args.end_date.replace(day=1)
            months = (end_month.year - start_month.year) * 12 + (end_month.month - start_month.month) + 1
            print(f"📈 Estimated monthly summaries: {months}")
        
        print()
        if len(discovery_result.found_files) > 0:
            print("✅ Phase 2 Complete - File discovery successful!")
            print("📋 Ready for Phase 3: Content Processing System")
            print()
            print("Next steps:")
            print("- Process and validate file content")
            print("- Implement encoding detection")
            print("- Add content sanitization")
            print("- Integrate LLM API for analysis")
        else:
            print("⚠️  Phase 2 Complete - No files found!")
            print("📋 Please check your base path and date range")
            print()
            print("Troubleshooting:")
            print(f"- Verify files exist in: {args.base_path}")
            print("- Check directory structure matches expected format")
            print("- Ensure date range covers existing journal entries")
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()