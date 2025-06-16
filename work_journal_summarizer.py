#!/usr/bin/env python3
"""
Work Journal Summarizer - Phase 5: Summary Generation System

A Python program that generates weekly and monthly summaries of daily work journal
text files using LLM APIs. This module implements the command-line interface with
comprehensive argument validation, robust file discovery, content processing,
and intelligent summary generation.

Author: Work Journal Summarizer Project
Version: Phase 5 - Summary Generation System
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

# Import Phase 4 components
from llm_client import LLMClient, AnalysisResult, APIStats

# Import Phase 5 components
from summary_generator import SummaryGenerator, PeriodSummary, SummaryStats


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
    4. Analyze content using LLM API for entity extraction
    5. Extract projects, participants, tasks, and themes
    6. Display comprehensive analysis statistics and results
    """
    try:
        # Parse and validate arguments
        args = parse_arguments()
        
        # Display successful validation message
        print("✅ Work Journal Summarizer - Phase 5")
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
            
            # Phase 4: LLM API Integration
            print("🤖 Phase 4: Analyzing content with LLM API...")
            try:
                # Initialize LLM client
                llm_client = LLMClient()
                
                # Process content through LLM for entity extraction
                analysis_results = []
                total_files = len(processed_content)
                
                print(f"📊 Analyzing {total_files} files for entity extraction...")
                
                for i, content in enumerate(processed_content, 1):
                    print(f"  Processing file {i}/{total_files}: {content.file_path.name}")
                    
                    # Analyze content with LLM
                    analysis_result = llm_client.analyze_content(content.content, content.file_path)
                    analysis_results.append(analysis_result)
                    
                    # Show progress for every 10 files or last file
                    if i % 10 == 0 or i == total_files:
                        print(f"    Progress: {i}/{total_files} files analyzed")
                
                # Display LLM analysis statistics
                api_stats = llm_client.get_stats()
                print()
                print("📊 LLM API Analysis Results:")
                print("-" * 30)
                print(f"Total API calls: {api_stats.total_calls}")
                print(f"Successful calls: {api_stats.successful_calls}")
                print(f"Failed calls: {api_stats.failed_calls}")
                print(f"Success rate: {api_stats.successful_calls/api_stats.total_calls*100:.1f}%")
                print(f"Total API time: {api_stats.total_time:.3f} seconds")
                print(f"Average response time: {api_stats.average_response_time:.3f} seconds")
                if api_stats.rate_limit_hits > 0:
                    print(f"Rate limit hits: {api_stats.rate_limit_hits}")
                print()
                
                # Aggregate extracted entities across all files
                all_projects = set()
                all_participants = set()
                all_tasks = set()
                all_themes = set()
                
                for result in analysis_results:
                    all_projects.update(result.projects)
                    all_participants.update(result.participants)
                    all_tasks.update(result.tasks)
                    all_themes.update(result.themes)
                
                # Display aggregated entity extraction results
                print("🎯 Entity Extraction Summary:")
                print("-" * 30)
                print(f"Unique projects identified: {len(all_projects)}")
                print(f"Unique participants identified: {len(all_participants)}")
                print(f"Total tasks extracted: {len(all_tasks)}")
                print(f"Major themes identified: {len(all_themes)}")
                print()
                
                # Display sample entities (first 5 of each type)
                if all_projects:
                    projects_list = sorted(list(all_projects))
                    print("📋 Sample Projects (showing first 5):")
                    for i, project in enumerate(projects_list[:5]):
                        print(f"  {i+1}. {project}")
                    if len(projects_list) > 5:
                        print(f"  ... and {len(projects_list) - 5} more projects")
                    print()
                
                if all_participants:
                    participants_list = sorted(list(all_participants))
                    print("👥 Sample Participants (showing first 5):")
                    for i, participant in enumerate(participants_list[:5]):
                        print(f"  {i+1}. {participant}")
                    if len(participants_list) > 5:
                        print(f"  ... and {len(participants_list) - 5} more participants")
                    print()
                
                if all_themes:
                    themes_list = sorted(list(all_themes))
                    print("🎨 Sample Themes (showing first 5):")
                    for i, theme in enumerate(themes_list[:5]):
                        print(f"  {i+1}. {theme}")
                    if len(themes_list) > 5:
                        print(f"  ... and {len(themes_list) - 5} more themes")
                    print()
                
                print("✅ Phase 4 Complete - LLM API integration successful!")
                print()
                
                # Phase 5: Summary Generation
                print("📝 Phase 5: Generating intelligent summaries...")
                try:
                    # Initialize summary generator
                    summary_generator = SummaryGenerator(llm_client)
                    
                    # Generate summaries
                    summaries, summary_stats = summary_generator.generate_summaries(
                        analysis_results, args.summary_type, args.start_date, args.end_date
                    )
                    
                    # Display summary generation statistics
                    print("📊 Summary Generation Results:")
                    print("-" * 30)
                    print(f"Total periods processed: {summary_stats.total_periods}")
                    print(f"Successful summaries: {summary_stats.successful_summaries}")
                    print(f"Failed summaries: {summary_stats.failed_summaries}")
                    print(f"Success rate: {summary_stats.successful_summaries/summary_stats.total_periods*100:.1f}%" if summary_stats.total_periods > 0 else "N/A")
                    print(f"Total entries processed: {summary_stats.total_entries_processed}")
                    print(f"Generation time: {summary_stats.total_generation_time:.3f} seconds")
                    print(f"Average summary length: {summary_stats.average_summary_length} words")
                    print()
                    
                    # Display generated summaries
                    if summaries:
                        print("📋 Generated Summaries:")
                        print("=" * 50)
                        
                        for i, summary in enumerate(summaries, 1):
                            print(f"\n{i}. {summary.period_name}")
                            print(f"   Date Range: {summary.start_date} to {summary.end_date}")
                            print(f"   Journal Entries: {summary.entry_count}")
                            print(f"   Word Count: {summary.word_count}")
                            print(f"   Generation Time: {summary.generation_time:.3f}s")
                            print()
                            
                            # Display key entities
                            if summary.projects:
                                print(f"   📋 Projects: {', '.join(summary.projects[:3])}")
                                if len(summary.projects) > 3:
                                    print(f"        ... and {len(summary.projects) - 3} more")
                            
                            if summary.participants:
                                print(f"   👥 Participants: {', '.join(summary.participants[:3])}")
                                if len(summary.participants) > 3:
                                    print(f"        ... and {len(summary.participants) - 3} more")
                            
                            if summary.themes:
                                print(f"   🎨 Themes: {', '.join(summary.themes[:3])}")
                                if len(summary.themes) > 3:
                                    print(f"        ... and {len(summary.themes) - 3} more")
                            
                            print()
                            print("   📄 Summary:")
                            print("   " + "-" * 40)
                            
                            # Display summary text with proper wrapping
                            summary_lines = summary.summary_text.split('\n')
                            for line in summary_lines:
                                if len(line) <= 70:
                                    print(f"   {line}")
                                else:
                                    # Simple word wrapping
                                    words = line.split()
                                    current_line = "   "
                                    for word in words:
                                        if len(current_line + word) <= 70:
                                            current_line += word + " "
                                        else:
                                            print(current_line.rstrip())
                                            current_line = "   " + word + " "
                                    if current_line.strip():
                                        print(current_line.rstrip())
                            
                            print()
                            print("   " + "=" * 40)
                        
                        print()
                        print("✅ Phase 5 Complete - Summary generation successful!")
                        print("📋 Ready for Phase 6: Output Management")
                        print()
                        print("Next steps:")
                        print("- Generate markdown output files")
                        print("- Include processing metadata and statistics")
                        print("- Create professional formatted summaries")
                        print("- Save to designated output directory")
                    
                    else:
                        print("⚠️  No summaries were generated")
                        print("This could be due to:")
                        print("- No journal entries found in the specified date range")
                        print("- All summary generation attempts failed")
                        print("- Issues with LLM API responses")
                
                except Exception as e:
                    print(f"❌ Summary Generation Error: {e}")
                    print()
                    print("Summary generation failed, but entity extraction was successful.")
                    print("You can review the extracted entities above.")
                
            except ValueError as e:
                print(f"❌ LLM API Configuration Error: {e}")
                print()
                print("Please ensure AWS credentials are properly configured:")
                print("- Set AWS_ACCESS_KEY_ID environment variable")
                print("- Set AWS_SECRET_ACCESS_KEY environment variable")
                print("- Verify AWS Bedrock access permissions")
                print()
                print("Continuing with content processing results only...")
                
            except Exception as e:
                print(f"❌ LLM API Integration Error: {e}")
                print()
                print("LLM analysis failed, but content processing was successful.")
                print("You can still proceed with manual summary generation.")
            
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