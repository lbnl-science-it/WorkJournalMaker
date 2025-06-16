#!/usr/bin/env python3
"""
Work Journal Summarizer - Phase 3: Content Processing System

A Python program that generates weekly and monthly summaries of daily work journal
text files using LLM APIs. This module implements the command-line interface with
comprehensive argument validation, robust file discovery, and content processing.

Author: Work Journal Summarizer Project
Version: Phase 3 - Content Processing System
"""

import argparse
import datetime
import sys
from pathlib import Path
from typing import Tuple

# Import Phase 2 components
from file_discovery import FileDiscovery, FileDiscoveryResult

# Import Phase 3 components
from content_processor import ContentProcessor, ProcessedContent, ProcessingStats


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
    3. Process and validate file content with encoding detection
    4. Display comprehensive processing statistics
    5. Prepare processed content for future LLM analysis
    """
    try:
        # Parse and validate arguments
        args = parse_arguments()
        
        # Display successful validation message
        print("✅ Work Journal Summarizer - Phase 3")
        print("=" * 50)
        print(f"Start Date: {args.start_date}")
        print(f"End Date: {args.end_date}")
        print(f"Summary Type: {args.summary_type}")
        print(f"Base Path: {args.base_path}")
        print(f"Date Range: {(args.end_date - args.start_date).days + 1} days")
        print()
        
        # Phase 2: File Discovery
        print("🔍 Phase 2: Discovering journal files...")
        file_discovery = FileDiscovery(base_path=args.base_path)
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
        
        # Phase 3: Content Processing
        if len(discovery_result.found_files) > 0:
            print("📝 Phase 3: Processing file content...")
            content_processor = ContentProcessor(max_file_size_mb=50)
            
            # Process all found files
            processed_content, processing_stats = content_processor.process_files(discovery_result.found_files)
            
            # Display processing statistics
            print("📊 Content Processing Results:")
            print("-" * 30)
            print(f"Files processed: {processing_stats.total_files}")
            print(f"Successfully processed: {processing_stats.successful}")
            print(f"Failed to process: {processing_stats.failed}")
            print(f"Success rate: {processing_stats.successful/processing_stats.total_files*100:.1f}%")
            print(f"Total content size: {processing_stats.total_size_bytes:,} bytes")
            print(f"Total words extracted: {processing_stats.total_words:,}")
            print(f"Processing time: {processing_stats.processing_time:.3f} seconds")
            print(f"Average processing speed: {processing_stats.total_files/processing_stats.processing_time:.1f} files/second")
            print()
            
            # Display sample processed content
            if processed_content:
                print("📄 Sample Processed Content (first file):")
                print("-" * 40)
                sample = processed_content[0]
                print(f"File: {sample.file_path.name}")
                print(f"Date: {sample.date}")
                print(f"Encoding: {sample.encoding}")
                print(f"Word count: {sample.word_count}")
                print(f"Line count: {sample.line_count}")
                print(f"Processing time: {sample.processing_time:.3f}s")
                
                # Show first 200 characters of content
                content_preview = sample.content[:200]
                if len(sample.content) > 200:
                    content_preview += "..."
                print(f"Content preview: {content_preview}")
                
                if sample.errors:
                    print(f"Errors: {', '.join(sample.errors)}")
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
            print("✅ Phase 3 Complete - Content processing successful!")
            print("📋 Ready for Phase 4: LLM API Integration")
            print()
            print("Next steps:")
            print("- Integrate with LLM API for entity extraction")
            print("- Extract projects, participants, tasks, and themes")
            print("- Implement API error handling and retry logic")
            print("- Prepare for summary generation")
            
            # Display processing quality metrics
            if processed_content:
                avg_words_per_file = sum(c.word_count for c in processed_content) / len(processed_content)
                avg_lines_per_file = sum(c.line_count for c in processed_content) / len(processed_content)
                print()
                print("📈 Content Quality Metrics:")
                print(f"Average words per file: {avg_words_per_file:.1f}")
                print(f"Average lines per file: {avg_lines_per_file:.1f}")
                
                # Check for encoding diversity
                encodings = set(c.encoding for c in processed_content)
                print(f"Encodings detected: {', '.join(encodings)}")
                
                # Check for files with errors
                files_with_errors = [c for c in processed_content if c.errors]
                if files_with_errors:
                    print(f"Files with processing warnings: {len(files_with_errors)}")
        
        else:
            print("⚠️  No files found for processing!")
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