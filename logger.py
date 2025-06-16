"""
Comprehensive Error Handling & Logging System for Work Journal Summarizer - Phase 7

This module implements production-grade error handling, logging, and progress tracking
with categorized error reporting, graceful degradation, and comprehensive progress
indicators throughout the processing pipeline.

Key features:
- Categorized error handling and reporting
- Progress tracking with time estimation
- Console and file logging with rotation
- Graceful degradation strategies
- Professional error messages and recovery guidance
"""

import logging
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import time


class LogLevel(Enum):
    """Logging levels for the application."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Categories for error classification and reporting."""
    FILE_SYSTEM = "file_system"
    API_FAILURE = "api_failure"
    PROCESSING_ERROR = "processing_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"


@dataclass
class LogConfig:
    """Configuration for the logging system."""
    level: LogLevel = LogLevel.INFO
    console_output: bool = True
    file_output: bool = True
    log_dir: str = "~/Desktop/worklogs/summaries/error_logs/"
    include_timestamps: bool = True
    include_module_names: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class ProcessingProgress:
    """Tracks processing progress across all phases."""
    current_phase: str
    total_phases: int
    current_phase_progress: float
    overall_progress: float
    estimated_time_remaining: Optional[float] = None
    files_processed: int = 0
    total_files: int = 0
    errors_encountered: int = 0
    start_time: float = field(default_factory=time.time)


@dataclass
class ErrorReport:
    """Detailed error report with categorization and recovery guidance."""
    category: ErrorCategory
    message: str
    file_path: Optional[Path] = None
    timestamp: datetime = field(default_factory=datetime.now)
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    recovery_action: Optional[str] = None
    phase: Optional[str] = None


class JournalSummarizerLogger:
    """
    Comprehensive logging system for the Work Journal Summarizer.
    
    Provides categorized error handling, progress tracking, and graceful
    degradation with detailed reporting and recovery guidance.
    """
    
    def __init__(self, config: LogConfig):
        """
        Initialize the logging system.
        
        Args:
            config: Configuration for logging behavior
        """
        self.config = config
        self.log_file_path = self._setup_log_file()
        self.logger = self._setup_logger()
        self.progress = ProcessingProgress("Initialization", 8, 0.0, 0.0)
        self.error_reports: List[ErrorReport] = []
        self.phase_start_times: Dict[str, float] = {}
        
    def _setup_log_file(self) -> Path:
        """
        Setup log file with timestamp in the filename.
        
        Returns:
            Path to the log file
        """
        log_dir = Path(self.config.log_dir).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"journal_summarizer_{timestamp}.log"
        
        return log_dir / log_filename
    
    def _setup_logger(self) -> logging.Logger:
        """
        Configure logger with file and console handlers.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger("journal_summarizer")
        logger.setLevel(getattr(logging, self.config.level.value))
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create formatter
        if self.config.include_timestamps and self.config.include_module_names:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        elif self.config.include_timestamps:
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
        else:
            formatter = logging.Formatter('%(levelname)s - %(message)s')
        
        # Console handler
        if self.config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.config.file_output:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                self.log_file_path,
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def start_phase(self, phase_name: str) -> None:
        """
        Mark the start of a processing phase.
        
        Args:
            phase_name: Name of the phase being started
        """
        self.phase_start_times[phase_name] = time.time()
        self.progress.current_phase = phase_name
        self.logger.info(f"Starting {phase_name}")
    
    def complete_phase(self, phase_name: str) -> None:
        """
        Mark the completion of a processing phase.
        
        Args:
            phase_name: Name of the phase being completed
        """
        if phase_name in self.phase_start_times:
            duration = time.time() - self.phase_start_times[phase_name]
            self.logger.info(f"Completed {phase_name} in {duration:.3f} seconds")
        else:
            self.logger.info(f"Completed {phase_name}")
    
    def update_progress(self, phase: str, phase_progress: float, 
                       files_processed: int = 0, total_files: int = 0) -> None:
        """
        Update processing progress and display.
        
        Args:
            phase: Current phase name
            phase_progress: Progress within current phase (0.0 to 1.0)
            files_processed: Number of files processed so far
            total_files: Total number of files to process
        """
        # Calculate overall progress (assuming 8 phases total)
        phase_weights = {
            "Initialization": 0.05,
            "File Discovery": 0.10,
            "Content Processing": 0.25,
            "LLM Analysis": 0.35,
            "Summary Generation": 0.15,
            "Output Management": 0.05,
            "Error Handling": 0.03,
            "Finalization": 0.02
        }
        
        # Calculate base progress from completed phases
        completed_weight = 0.0
        current_weight = phase_weights.get(phase, 0.125)  # Default 1/8 if not found
        
        for phase_name, weight in phase_weights.items():
            if phase_name == phase:
                break
            completed_weight += weight
        
        overall_progress = completed_weight + (current_weight * phase_progress)
        
        # Update progress object
        self.progress.current_phase = phase
        self.progress.current_phase_progress = phase_progress
        self.progress.overall_progress = min(overall_progress, 1.0)
        self.progress.files_processed = files_processed
        self.progress.total_files = total_files
        
        # Calculate time estimation
        elapsed_time = time.time() - self.progress.start_time
        if overall_progress > 0:
            estimated_total_time = elapsed_time / overall_progress
            self.progress.estimated_time_remaining = max(0, estimated_total_time - elapsed_time)
        
        # Display progress if significant change
        if phase_progress in [0.0, 0.25, 0.5, 0.75, 1.0] or files_processed % 10 == 0:
            self._display_progress()
    
    def _display_progress(self) -> None:
        """Display current progress to console."""
        progress_bar = self._create_progress_bar(
            self.progress.overall_progress, 
            prefix=f"{self.progress.current_phase}",
            suffix=f"{self.progress.overall_progress*100:.1f}%"
        )
        
        # Add file progress if available
        if self.progress.total_files > 0:
            file_info = f" ({self.progress.files_processed}/{self.progress.total_files} files)"
            progress_bar += file_info
        
        # Add time estimate if available
        if self.progress.estimated_time_remaining:
            eta_minutes = int(self.progress.estimated_time_remaining / 60)
            eta_seconds = int(self.progress.estimated_time_remaining % 60)
            if eta_minutes > 0:
                progress_bar += f" ETA: {eta_minutes}m {eta_seconds}s"
            else:
                progress_bar += f" ETA: {eta_seconds}s"
        
        print(f"\r{progress_bar}", end="", flush=True)
        
        # Print newline at completion
        if self.progress.overall_progress >= 1.0:
            print()
    
    def _create_progress_bar(self, progress: float, width: int = 30, 
                           prefix: str = "", suffix: str = "") -> str:
        """
        Create a visual progress bar.
        
        Args:
            progress: Progress value between 0.0 and 1.0
            width: Width of the progress bar in characters
            prefix: Text to display before the progress bar
            suffix: Text to display after the progress bar
            
        Returns:
            Formatted progress bar string
        """
        filled_width = int(width * progress)
        bar = "█" * filled_width + "░" * (width - filled_width)
        return f"{prefix} |{bar}| {suffix}"
    
    def log_error_with_category(self, category: ErrorCategory, message: str, 
                               exception: Optional[Exception] = None,
                               file_path: Optional[Path] = None,
                               recovery_action: Optional[str] = None) -> None:
        """
        Log error with categorization for reporting.
        
        Args:
            category: Error category for classification
            message: Error message
            exception: Optional exception object
            file_path: Optional file path related to the error
            recovery_action: Optional recovery guidance
        """
        # Create error report
        error_report = ErrorReport(
            category=category,
            message=message,
            file_path=file_path,
            exception_type=type(exception).__name__ if exception else None,
            stack_trace=traceback.format_exc() if exception else None,
            recovery_action=recovery_action,
            phase=self.progress.current_phase
        )
        
        self.error_reports.append(error_report)
        self.progress.errors_encountered += 1
        
        # Log the error
        log_message = f"[{category.value.upper()}] {message}"
        if file_path:
            log_message += f" (File: {file_path})"
        
        if exception:
            self.logger.error(log_message, exc_info=True)
        else:
            self.logger.error(log_message)
        
        # Display recovery action if provided
        if recovery_action:
            self.logger.info(f"Recovery suggestion: {recovery_action}")
    
    def log_warning_with_category(self, category: ErrorCategory, message: str,
                                 file_path: Optional[Path] = None) -> None:
        """
        Log warning with categorization.
        
        Args:
            category: Warning category
            message: Warning message
            file_path: Optional file path related to the warning
        """
        log_message = f"[{category.value.upper()}] {message}"
        if file_path:
            log_message += f" (File: {file_path})"
        
        self.logger.warning(log_message)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of all errors encountered.
        
        Returns:
            Dictionary with error statistics and categorization
        """
        if not self.error_reports:
            return {"total_errors": 0, "categories": {}}
        
        # Count errors by category
        category_counts = {}
        for report in self.error_reports:
            category = report.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Get recent errors (last 5)
        recent_errors = self.error_reports[-5:] if len(self.error_reports) > 5 else self.error_reports
        
        return {
            "total_errors": len(self.error_reports),
            "categories": category_counts,
            "recent_errors": [
                {
                    "category": report.category.value,
                    "message": report.message,
                    "timestamp": report.timestamp.isoformat(),
                    "phase": report.phase,
                    "recovery_action": report.recovery_action
                }
                for report in recent_errors
            ]
        }
    
    def should_continue_processing(self, critical_error_threshold: int = 10) -> bool:
        """
        Determine if processing should continue based on error count.
        
        Args:
            critical_error_threshold: Maximum number of errors before stopping
            
        Returns:
            True if processing should continue, False otherwise
        """
        critical_errors = sum(1 for report in self.error_reports 
                            if report.category in [ErrorCategory.API_FAILURE, 
                                                 ErrorCategory.CONFIGURATION_ERROR])
        
        return critical_errors < critical_error_threshold
    
    def generate_error_report(self) -> str:
        """
        Generate a comprehensive error report for inclusion in output.
        
        Returns:
            Formatted error report string
        """
        if not self.error_reports:
            return "No errors encountered during processing."
        
        report_lines = [
            "## Error Report",
            "",
            f"**Total Errors:** {len(self.error_reports)}",
            f"**Processing Time:** {time.time() - self.progress.start_time:.2f} seconds",
            ""
        ]
        
        # Group errors by category
        category_groups = {}
        for report in self.error_reports:
            category = report.category.value
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(report)
        
        # Add category summaries
        for category, reports in category_groups.items():
            report_lines.extend([
                f"### {category.replace('_', ' ').title()} Errors ({len(reports)})",
                ""
            ])
            
            for i, report in enumerate(reports[:3], 1):  # Show first 3 of each category
                report_lines.extend([
                    f"{i}. **{report.message}**",
                    f"   - Time: {report.timestamp.strftime('%H:%M:%S')}",
                    f"   - Phase: {report.phase or 'Unknown'}"
                ])
                
                if report.file_path:
                    report_lines.append(f"   - File: {report.file_path}")
                
                if report.recovery_action:
                    report_lines.append(f"   - Recovery: {report.recovery_action}")
                
                report_lines.append("")
            
            if len(reports) > 3:
                report_lines.append(f"   ... and {len(reports) - 3} more {category} errors")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def close(self) -> None:
        """Close the logger and clean up resources."""
        # Log final statistics
        total_time = time.time() - self.progress.start_time
        self.logger.info(f"Processing completed in {total_time:.2f} seconds")
        self.logger.info(f"Total errors encountered: {len(self.error_reports)}")
        
        # Close handlers
        for handler in self.logger.handlers:
            handler.close()
        
        self.logger.handlers.clear()


def create_default_logger() -> JournalSummarizerLogger:
    """
    Create a logger with default configuration.
    
    Returns:
        Configured JournalSummarizerLogger instance
    """
    config = LogConfig()
    return JournalSummarizerLogger(config)


def create_logger_with_config(log_level: str = "INFO", 
                            log_dir: Optional[str] = None,
                            console_output: bool = True,
                            file_output: bool = True) -> JournalSummarizerLogger:
    """
    Create a logger with custom configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        console_output: Whether to output to console
        file_output: Whether to output to file
        
    Returns:
        Configured JournalSummarizerLogger instance
    """
    config = LogConfig(
        level=LogLevel(log_level.upper()),
        console_output=console_output,
        file_output=file_output
    )
    
    if log_dir:
        config.log_dir = log_dir
    
    return JournalSummarizerLogger(config)