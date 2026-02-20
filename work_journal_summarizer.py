#!/usr/bin/env python3
"""
Work Journal Summarizer - Phase 8: Configuration Management & API Fallback

A Python program that generates weekly and monthly summaries of daily work journal
text files using LLM APIs. This module implements the command-line interface with
comprehensive argument validation, robust file discovery, content processing,
intelligent summary generation, professional markdown output generation,
production-grade error handling with comprehensive logging, and complete
configuration management with API fallback support.

Author: Work Journal Summarizer Project
Version: Phase 8 - Configuration Management & API Fallback
"""

import argparse
import datetime
import sys
from pathlib import Path
from typing import Optional, Tuple

# Import Phase 2 components
from file_discovery import FileDiscovery, FileDiscoveryResult
# Import Phase 3 components
from content_processor import ContentProcessor, ProcessedContent, ProcessingStats
# Import Phase 4 components (updated for Phase 8)
from unified_llm_client import UnifiedLLMClient
from llm_data_structures import AnalysisResult, APIStats
# Import Phase 5 components
from summary_generator import SummaryGenerator, PeriodSummary, SummaryStats
# Import Phase 6 components
from output_manager import OutputManager, OutputResult, ProcessingMetadata
# Import Phase 7 components
from logger import (
    JournalSummarizerLogger, LogConfig, LogLevel, ErrorCategory,
    create_logger_with_config
)
# Import Phase 8 components
from config_manager import ConfigManager, AppConfig
# Import database components for CLI integration
from web.database import DatabaseManager


def fallback_notification(message: str) -> None:
    """
    Print a fallback notification to stdout so the user sees provider transitions.

    Args:
        message: Description of the provider switch (from UnifiedLLMClient)
    """
    print(f"⚠ {message}")


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
  %(prog)s --start-date 2024-04-01 --end-date 2024-04-30 --summary-type weekly --log-level DEBUG

Date Format:
  All dates must be in YYYY-MM-DD format (e.g., 2024-04-01)
  End date must be after start date (minimum 2-day range)

Summary Types:
  weekly  - Generate weekly summaries grouped by calendar weeks
  monthly - Generate monthly summaries grouped by calendar months

Logging:
  --log-level controls verbosity: DEBUG, INFO, WARNING, ERROR, CRITICAL
  --log-dir specifies custom directory for log files
  --no-console disables console output (file logging only)
        """
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date in YYYY-MM-DD format (inclusive)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date in YYYY-MM-DD format (inclusive)'
    )
    
    parser.add_argument(
        '--summary-type',
        type=str,
        choices=['weekly', 'monthly'],
        help='Type of summary to generate: weekly or monthly'
    )
    
    parser.add_argument(
        '--base-path',
        type=str,
        default="~/Desktop/worklogs/",
        help='Base directory path for journal files (default: ~/Desktop/worklogs/)'
    )
    
    # Phase 7: Logging and error handling options
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-dir',
        type=str,
        help='Custom directory for log files (default: ~/Desktop/worklogs/summaries/error_logs/)'
    )
    
    parser.add_argument(
        '--no-console',
        action='store_true',
        help='Disable console output (log to file only)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration and show processing plan without execution'
    )
    
    # Phase 8: Configuration management options
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (YAML or JSON)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Override output directory from configuration'
    )
    
    parser.add_argument(
        '--save-example-config',
        type=str,
        help='Save an example configuration file to the specified path and exit'
    )
    
    parser.add_argument(
        '--database-path',
        type=str,
        help='Path to database file (overrides configuration file setting)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # If saving example config, skip other validations
    if args.save_example_config:
        return args
    
    # Check required arguments for normal operation
    if not args.start_date:
        parser.error("--start-date is required")
    if not args.end_date:
        parser.error("--end-date is required")
    if not args.summary_type:
        parser.error("--summary-type is required")
    
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


def resolve_database_path_priority(cli_path: str = None, config_path: str = None) -> str:
    """
    Resolve database path with priority: CLI > config file > environment > None.
    
    Args:
        cli_path: Database path from CLI argument
        config_path: Path to configuration file
        
    Returns:
        str: Resolved database path or None for defaults
    """
    import os
    from pathlib import Path
    
    # Priority 1: CLI argument
    if cli_path:
        return cli_path
    
    # Priority 2: Configuration file
    if config_path and Path(config_path).exists():
        try:
            # Temporarily clear environment to avoid interference
            orig_env = os.environ.get('WJS_DATABASE_PATH')
            if 'WJS_DATABASE_PATH' in os.environ:
                del os.environ['WJS_DATABASE_PATH']
            
            config_manager = ConfigManager(Path(config_path))
            config = config_manager.get_config()
            
            # Restore environment variable
            if orig_env is not None:
                os.environ['WJS_DATABASE_PATH'] = orig_env
            
            if config.processing.database_path:
                return config.processing.database_path
        except Exception:
            # Restore environment variable on error
            if orig_env is not None:
                os.environ['WJS_DATABASE_PATH'] = orig_env
    
    # Priority 3: Environment variable
    env_path = os.getenv('WJS_DATABASE_PATH')
    if env_path:
        return env_path
    
    # Priority 4: Default (None)
    return None


def initialize_database_manager(database_path: str = None) -> DatabaseManager:
    """
    Initialize DatabaseManager with optional database path.
    
    Args:
        database_path: Optional path to database file
        
    Returns:
        DatabaseManager: Initialized database manager instance
    """
    return DatabaseManager(database_path=database_path)


def _perform_dry_run(args: argparse.Namespace, config: AppConfig, logger: JournalSummarizerLogger) -> None:
    """
    Perform a dry run to validate configuration without executing the full pipeline.
    
    Args:
        args: Parsed command line arguments
        config: Application configuration
        logger: Logger instance for reporting
    """
    print("🔍 DRY RUN MODE - Configuration Validation")
    print("=" * 50)
    
    # Validate date range
    total_days = (args.end_date - args.start_date).days + 1
    print(f"✅ Date range valid: {args.start_date} to {args.end_date} ({total_days} days)")
    
    # Check base path from configuration
    base_path = Path(config.processing.base_path).expanduser()
    if base_path.exists():
        print(f"✅ Base path accessible: {base_path}")
    else:
        print(f"❌ Base path not found: {base_path}")
        logger.log_error_with_category(
            ErrorCategory.FILE_SYSTEM,
            f"Base path not accessible: {base_path}",
            recovery_action="Create the directory or check the path"
        )
    
    # Check output path from configuration
    output_path = Path(config.processing.output_path).expanduser()
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Output path accessible: {output_path}")
    except Exception as e:
        print(f"❌ Output path not accessible: {output_path}")
        logger.log_error_with_category(
            ErrorCategory.FILE_SYSTEM,
            f"Output path not accessible: {output_path} - {e}",
            recovery_action="Check permissions or create the directory manually"
        )
    
    # Estimate processing scope
    if args.summary_type == 'weekly':
        estimated_periods = (total_days + 6) // 7
        print(f"📊 Estimated weekly summaries: {estimated_periods}")
    else:
        start_month = args.start_date.replace(day=1)
        end_month = args.end_date.replace(day=1)
        months = (end_month.year - start_month.year) * 12 + (end_month.month - start_month.month) + 1
        print(f"📊 Estimated monthly summaries: {months}")
    
    # Check provider credentials and test connection
    import os
    
    # Test LLM connection using unified client
    try:
        llm_client = UnifiedLLMClient(config, on_fallback=fallback_notification)
        provider_name = llm_client.get_provider_name()
        provider_info = llm_client.get_provider_info()
        
        print(f"🤖 LLM Provider: {provider_name}")
        for key, value in provider_info.items():
            print(f"📝 {key.replace('_', ' ').title()}: {value}")
        
        # Check provider-specific credentials
        if provider_name == "bedrock":
            aws_key = os.getenv(config.bedrock.aws_access_key_env)
            aws_secret = os.getenv(config.bedrock.aws_secret_key_env)
            if aws_key and aws_secret:
                print("✅ AWS credentials found in environment")
            else:
                print("❌ AWS credentials not found")
                logger.log_error_with_category(
                    ErrorCategory.CONFIGURATION_ERROR,
                    f"AWS credentials not configured: {config.bedrock.aws_access_key_env}, {config.bedrock.aws_secret_key_env}",
                    recovery_action=f"Set {config.bedrock.aws_access_key_env} and {config.bedrock.aws_secret_key_env} environment variables"
                )
        elif provider_name == "google_genai":
            # For Google GenAI, credentials are typically handled via service account or application default credentials
            print("✅ Google GenAI provider configured")
        
        if llm_client.test_connection():
            print(f"✅ {provider_name.title()} API connection successful")
        else:
            print(f"❌ {provider_name.title()} API connection failed")
            # Print additional diagnostic info from logger
            print("💡 Check the log file for detailed error analysis and solutions")
    except Exception as e:
        print(f"LLM connection test failed: {e}")
        print("❌ LLM API connection failed")
        logger.log_error_with_category(
            ErrorCategory.API_FAILURE,
            f"Failed to create LLM client: {e}",
            recovery_action="Check LLM provider credentials and configuration"
        )
    
    # Configuration summary
    print(f"📁 Max file size: {config.processing.max_file_size_mb} MB")
    print(f"📝 Log level: {config.logging.level.value}")
    print(f"📁 Log directory: {logger.log_file_path.parent}")
    print(f"📄 Log file: {logger.log_file_path.name}")
    
    print("\n🎯 Dry run complete - configuration validated")
    
    # Show any errors found
    if logger.error_reports:
        print(f"\n⚠️  Found {len(logger.error_reports)} configuration issues:")
        for report in logger.error_reports:
            print(f"  - {report.message}")
            if report.recovery_action:
                print(f"    Recovery: {report.recovery_action}")


def _run_file_discovery(
    config: 'AppConfig',
    args: argparse.Namespace,
    logger: 'JournalSummarizerLogger',
) -> Optional[FileDiscoveryResult]:
    """
    Discover journal files in the configured date range.

    Returns a FileDiscoveryResult on success, an empty result for recoverable
    failures, or None when the logger indicates processing should stop.
    """
    logger.start_phase("File Discovery")
    print("🔍 Phase 2: Discovering journal files...")

    try:
        file_discovery = FileDiscovery(base_path=config.processing.base_path)
        discovery_result = file_discovery.discover_files(args.start_date, args.end_date)

        logger.update_progress("File Discovery", 0.8, 0, discovery_result.total_expected)

        # Log missing files as warnings
        if discovery_result.missing_files:
            for missing_file in discovery_result.missing_files:
                logger.log_warning_with_category(
                    ErrorCategory.FILE_SYSTEM,
                    f"Expected journal file not found: {missing_file.name}",
                    file_path=missing_file
                )

        # Display discovery statistics
        print("📊 File Discovery Results:")
        print("-" * 30)
        print(f"Total files expected: {discovery_result.total_expected}")
        print(f"Files found: {len(discovery_result.found_files)}")
        print(f"Files missing: {len(discovery_result.missing_files)}")

        if discovery_result.total_expected > 0:
            success_rate = len(discovery_result.found_files)/discovery_result.total_expected*100
            print(f"Discovery success rate: {success_rate:.1f}%")

            # Log low success rate as warning
            if success_rate < 50:
                logger.log_warning_with_category(
                    ErrorCategory.FILE_SYSTEM,
                    f"Low file discovery success rate: {success_rate:.1f}%",
                )

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

        logger.update_progress("File Discovery", 1.0, 0, discovery_result.total_expected)
        logger.complete_phase("File Discovery")
        return discovery_result

    except Exception as e:
        logger.log_error_with_category(
            ErrorCategory.FILE_SYSTEM,
            f"File discovery failed: {str(e)}",
            exception=e,
            recovery_action="Check base path exists and is accessible"
        )

        if not logger.should_continue_processing():
            print("❌ Critical file discovery error - stopping processing")
            return None

        # Empty result for graceful degradation
        return FileDiscoveryResult([], [], 0, (args.start_date, args.end_date), 0.0)


def main() -> None:
    """
    Main entry point for the Work Journal Summarizer.
    
    This function handles the complete workflow with comprehensive error handling:
    1. Parse and validate command line arguments
    2. Initialize configuration management system
    3. Initialize logging system with progress tracking
    4. Discover journal files in the specified date range
    5. Process and validate file content with encoding detection
    6. Analyze content using LLM API for entity extraction
    7. Generate intelligent summaries with graceful error handling
    8. Create professional markdown output with error reporting
    9. Provide comprehensive processing statistics and error analysis
    """
    logger = None
    config = None
    try:
        # Parse and validate arguments
        args = parse_arguments()
        
        # Handle save example config option
        if args.save_example_config:
            try:
                config_manager = ConfigManager()
                config_path = Path(args.save_example_config)
                config_manager.save_example_config(config_path)
                print(f"✅ Example configuration saved to: {config_path}")
                return
            except Exception as e:
                print(f"❌ Failed to save example config: {e}")
                sys.exit(1)
        
        # Initialize configuration management
        try:
            config_path = Path(args.config) if args.config else None
            config_manager = ConfigManager(config_path)
            config = config_manager.get_config()
            
            # Apply command-line overrides
            if args.base_path:
                config.processing.base_path = args.base_path
            if args.output_dir:
                config.processing.output_path = args.output_dir
            if args.log_level:
                config.logging.level = LogLevel(args.log_level)
            if args.log_dir:
                config.logging.log_dir = args.log_dir
            if args.no_console:
                config.logging.console_output = False
                
        except Exception as e:
            print(f"❌ Configuration Error: {e}")
            print("\nTroubleshooting:")
            print("- Check configuration file syntax (YAML/JSON)")
            print("- Verify environment variables are set correctly")
            print("- Use --save-example-config to create a template")
            sys.exit(1)
        
        # Initialize comprehensive logging system using configuration
        logger = create_logger_with_config(
            log_level=config.logging.level.value,
            log_dir=config.logging.log_dir,
            console_output=config.logging.console_output,
            file_output=config.logging.file_output
        )
        
        logger.start_phase("Initialization")
        logger.logger.info("Work Journal Summarizer - Phase 8: Configuration Management & API Fallback")
        
        # Display configuration summary
        if not args.dry_run:
            config_manager.print_config_summary()
        
        # Handle dry run mode
        if args.dry_run:
            logger.logger.info("DRY RUN MODE - Validating configuration without execution")
            _perform_dry_run(args, config, logger)
            return
        
        # Display successful validation message
        print("✅ Work Journal Summarizer - Phase 8")
        print("=" * 50)
        print(f"Start Date: {args.start_date}")
        print(f"End Date: {args.end_date}")
        print(f"Summary Type: {args.summary_type}")
        print(f"Base Path: {config.processing.base_path}")
        print(f"Output Path: {config.processing.output_path}")
        print(f"Date Range: {(args.end_date - args.start_date).days + 1} days")
        llm_client = UnifiedLLMClient(config, on_fallback=fallback_notification)
        provider_info = llm_client.get_provider_info()
        for key, value in provider_info.items():
            if key not in ("fallback_providers",):
                print(f"{key.replace('_', ' ').title()}: {value}")
        print()
        
        logger.update_progress("Initialization", 1.0)
        logger.complete_phase("Initialization")
        
        # Phase 2: File Discovery
        discovery_result = _run_file_discovery(config, args, logger)
        if discovery_result is None:
            return
        
        # Phase 3: Content Processing
        if len(discovery_result.found_files) > 0:
            print("📝 Phase 3: Processing file content...")
            content_processor = ContentProcessor(max_file_size_mb=config.processing.max_file_size_mb)
            
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
                # Initialize Unified LLM client with configuration
                llm_client = UnifiedLLMClient(config, on_fallback=fallback_notification)
                
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
                        print()
                        
                        # Phase 6: Output Management
                        print("📄 Phase 6: Generating markdown output...")
                        try:
                            # Create processing metadata
                            processing_metadata = ProcessingMetadata(
                                total_files_found=discovery_result.total_expected,
                                files_successfully_processed=processing_stats.successful,
                                files_with_errors=processing_stats.failed,
                                api_calls_made=api_stats.total_calls,
                                successful_api_calls=api_stats.successful_calls,
                                failed_api_calls=api_stats.failed_calls,
                                unique_projects=len(all_projects),
                                unique_participants=len(all_participants),
                                total_tasks=len(all_tasks),
                                major_themes=len(all_themes),
                                processing_duration=(discovery_result.processing_time +
                                                   processing_stats.processing_time +
                                                   api_stats.total_time +
                                                   summary_stats.total_generation_time)
                            )
                            
                            # Initialize output manager with configuration
                            output_manager = OutputManager(output_dir=config.processing.output_path)
                            
                            # Generate output file
                            output_result = output_manager.generate_output(
                                summaries, args.summary_type, args.start_date, args.end_date, processing_metadata
                            )
                            
                            # Display output generation results
                            print("📊 Output Generation Results:")
                            print("-" * 30)
                            print(f"Output file: {output_result.output_path}")
                            print(f"File size: {output_result.file_size_bytes:,} bytes")
                            print(f"Generation time: {output_result.generation_time:.3f} seconds")
                            print(f"Sections count: {output_result.sections_count}")
                            print(f"Metadata included: {'Yes' if output_result.metadata_included else 'No'}")
                            print(f"Validation passed: {'Yes' if output_result.validation_passed else 'No'}")
                            print()
                            
                            print("✅ Phase 6 Complete - Output management successful!")
                            print()
                            print("🎉 Work Journal Summarizer - All Phases Complete!")
                            print("=" * 50)
                            print(f"📁 Summary file created: {output_result.output_path}")
                            print(f"📊 Total processing time: {processing_metadata.processing_duration:.2f} seconds")
                            print(f"📈 Files processed: {processing_metadata.files_successfully_processed}/{processing_metadata.total_files_found}")
                            print(f"🤖 API calls made: {processing_metadata.successful_api_calls}/{processing_metadata.api_calls_made}")
                            print(f"📋 Summaries generated: {summary_stats.successful_summaries}")
                            print()
                            print("Your professional work journal summary is ready!")
                            
                        except Exception as e:
                            print(f"❌ Output Generation Error: {e}")
                            print()
                            print("Output generation failed, but summaries were created successfully.")
                            print("You can review the generated summaries above.")
                    
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