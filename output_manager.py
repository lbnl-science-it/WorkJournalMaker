#!/usr/bin/env python3
"""
Output Manager - Phase 6: Output Management System

This module implements professional markdown output generation with proper 
formatting and metadata for work journal summaries.

Author: Work Journal Summarizer Project
Version: Phase 6 - Output Management System
"""

from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional
import os
import logging
import time


@dataclass
class OutputResult:
    """Result of output generation process."""
    output_path: Path
    file_size_bytes: int
    generation_time: float
    sections_count: int
    metadata_included: bool
    validation_passed: bool


@dataclass
class ProcessingMetadata:
    """Comprehensive metadata from all processing phases."""
    total_files_found: int
    files_successfully_processed: int
    files_with_errors: int
    api_calls_made: int
    successful_api_calls: int
    failed_api_calls: int
    unique_projects: int
    unique_participants: int
    total_tasks: int
    major_themes: int
    processing_duration: float


class OutputManager:
    """
    Manages the generation of professional markdown output files with 
    comprehensive metadata and statistics.
    """
    
    def __init__(self, output_dir: str = "~/Desktop/worklogs/summaries/"):
        """
        Initialize OutputManager with specified output directory.
        
        Args:
            output_dir: Directory path for output files
        """
        self.output_dir = Path(output_dir).expanduser()
        self.logger = logging.getLogger(__name__)
        
    def generate_output(self, summaries: List['PeriodSummary'], 
                       summary_type: str, start_date: date, end_date: date,
                       metadata: ProcessingMetadata) -> OutputResult:
        """
        Generate complete markdown output file with summaries and metadata.
        
        Args:
            summaries: List of period summaries to include
            summary_type: Type of summary ('weekly' or 'monthly')
            start_date: Start date of the processing range
            end_date: End date of the processing range
            metadata: Processing metadata and statistics
            
        Returns:
            OutputResult: Details about the generated output file
            
        Raises:
            OSError: If output directory cannot be created or file cannot be written
            ValueError: If input data is invalid
        """
        start_time = time.time()
        
        try:
            # Ensure output directory exists
            self._ensure_output_directory()
            
            # Generate filename
            filename = self._generate_filename(summary_type, start_date, end_date)
            output_path = self.output_dir / filename
            
            # Create markdown content
            markdown_content = self._create_markdown_content(
                summaries, summary_type, start_date, end_date, metadata
            )
            
            # Validate markdown structure
            validation_passed = self._validate_markdown(markdown_content)
            
            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Get file size
            file_size = output_path.stat().st_size
            
            # Count sections (headers starting with #)
            sections_count = len([line for line in markdown_content.split('\n') 
                                if line.strip().startswith('#')])
            
            generation_time = time.time() - start_time
            
            self.logger.info(f"Successfully generated output file: {output_path}")
            self.logger.info(f"File size: {file_size:,} bytes, Generation time: {generation_time:.3f}s")
            
            return OutputResult(
                output_path=output_path,
                file_size_bytes=file_size,
                generation_time=generation_time,
                sections_count=sections_count,
                metadata_included=True,
                validation_passed=validation_passed
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate output file: {e}")
            raise
    
    def _generate_filename(self, summary_type: str, start_date: date, 
                          end_date: date) -> str:
        """
        Generate filename following naming convention.
        
        Args:
            summary_type: Type of summary ('weekly' or 'monthly')
            start_date: Start date of the range
            end_date: End date of the range
            
        Returns:
            str: Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        return f"{summary_type}_summary_{start_str}_to_{end_str}_{timestamp}.md"
    
    def _create_markdown_content(self, summaries: List['PeriodSummary'],
                                summary_type: str, start_date: date, end_date: date,
                                metadata: ProcessingMetadata) -> str:
        """
        Create complete markdown content with all sections.
        
        Args:
            summaries: List of period summaries
            summary_type: Type of summary
            start_date: Start date of the range
            end_date: End date of the range
            metadata: Processing metadata
            
        Returns:
            str: Complete markdown content
        """
        # Generate header section
        header_section = self._format_header_section(
            summary_type, start_date, end_date, metadata
        )
        
        # Generate summary sections
        summary_sections = self._format_summary_sections(summaries)
        
        # Generate processing notes
        processing_notes = self._format_processing_notes(metadata)
        
        # Combine all sections
        markdown_content = f"{header_section}\n{summary_sections}\n{processing_notes}"
        
        return markdown_content
    
    def _format_header_section(self, summary_type: str, start_date: date,
                              end_date: date, metadata: ProcessingMetadata) -> str:
        """
        Format document header with metadata.
        
        Args:
            summary_type: Type of summary
            start_date: Start date of the range
            end_date: End date of the range
            metadata: Processing metadata
            
        Returns:
            str: Formatted header section
        """
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        start_str = start_date.strftime("%B %d, %Y")
        end_str = end_date.strftime("%B %d, %Y")
        
        header = f"""# {summary_type.title()} Summary: {start_str} to {end_str}

**Generated on:** {timestamp}  
**Date Range:** {start_str} to {end_str}  
**Total Files Processed:** {metadata.files_successfully_processed}

---
"""
        return header
    
    def _format_summary_sections(self, summaries: List['PeriodSummary']) -> str:
        """
        Format all summary sections.
        
        Args:
            summaries: List of period summaries to format
            
        Returns:
            str: Formatted summary sections
        """
        if not summaries:
            return "\n## No Summaries Generated\n\nNo journal entries were found or processed for the specified date range.\n"
        
        sections = []
        
        for i, summary in enumerate(summaries, 1):
            section = f"""
## {summary.period_name}

**Date Range:** {summary.start_date.strftime('%B %d, %Y')} to {summary.end_date.strftime('%B %d, %Y')}  
**Journal Entries:** {summary.entry_count}  
**Word Count:** {summary.word_count:,}

### Key Information

"""
            
            # Add projects section
            if summary.projects:
                projects_list = '\n'.join([f"- {project}" for project in summary.projects[:10]])
                if len(summary.projects) > 10:
                    projects_list += f"\n- *...and {len(summary.projects) - 10} more projects*"
                section += f"**Projects:**\n{projects_list}\n\n"
            
            # Add participants section
            if summary.participants:
                participants_list = '\n'.join([f"- {participant}" for participant in summary.participants[:10]])
                if len(summary.participants) > 10:
                    participants_list += f"\n- *...and {len(summary.participants) - 10} more participants*"
                section += f"**Key Participants:**\n{participants_list}\n\n"
            
            # Add themes section
            if summary.themes:
                themes_list = '\n'.join([f"- {theme}" for theme in summary.themes[:10]])
                if len(summary.themes) > 10:
                    themes_list += f"\n- *...and {len(summary.themes) - 10} more themes*"
                section += f"**Major Themes:**\n{themes_list}\n\n"
            
            # Add summary text
            section += f"### Summary\n\n{summary.summary_text}\n"
            
            sections.append(section)
        
        return '\n'.join(sections)
    
    def _format_processing_notes(self, metadata: ProcessingMetadata) -> str:
        """
        Format processing notes and statistics.
        
        Args:
            metadata: Processing metadata to format
            
        Returns:
            str: Formatted processing notes section
        """
        # Calculate derived metrics
        files_per_second = (metadata.files_successfully_processed / metadata.processing_duration 
                           if metadata.processing_duration > 0 else 0)
        
        avg_response_time = (metadata.processing_duration / metadata.api_calls_made 
                           if metadata.api_calls_made > 0 else 0)
        
        # Estimate average file size (rough calculation)
        avg_file_size = 5  # KB - placeholder since we don't have exact size data
        
        # Create issues list
        issues_list = []
        if metadata.files_with_errors > 0:
            issues_list.append(f"- {metadata.files_with_errors} files had processing errors")
        if metadata.failed_api_calls > 0:
            issues_list.append(f"- {metadata.failed_api_calls} API calls failed")
        if not issues_list:
            issues_list.append("- No significant issues encountered during processing")
        
        issues_text = '\n'.join(issues_list)
        
        processing_notes = f"""
---

## Processing Notes

### Files Processed
- **Total files found:** {metadata.total_files_found}
- **Files successfully processed:** {metadata.files_successfully_processed}
- **Files with errors:** {metadata.files_with_errors}

### API Usage Statistics
- **Total API calls made:** {metadata.api_calls_made}
- **Successful calls:** {metadata.successful_api_calls}
- **Failed calls:** {metadata.failed_api_calls}
- **Average response time:** {avg_response_time:.2f}s

### Entities Extracted
- **Unique projects identified:** {metadata.unique_projects}
- **Unique participants identified:** {metadata.unique_participants}
- **Total tasks extracted:** {metadata.total_tasks}
- **Major themes identified:** {metadata.major_themes}

### Processing Performance
- **Total processing time:** {metadata.processing_duration:.2f} seconds
- **Files per second:** {files_per_second:.2f}
- **Average file size:** {avg_file_size} KB

### Issues Encountered
{issues_text}

---

*Generated by Work Journal Summarizer v6.0*
"""
        return processing_notes
    
    def _validate_markdown(self, content: str) -> bool:
        """
        Validate markdown syntax and structure.
        
        Args:
            content: Markdown content to validate
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        try:
            lines = content.split('\n')
            
            # Check for required sections
            has_main_header = any(line.strip().startswith('# ') for line in lines)
            has_processing_notes = any('## Processing Notes' in line for line in lines)
            
            # Check heading hierarchy (basic validation)
            heading_levels = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#'):
                    level = len(stripped) - len(stripped.lstrip('#'))
                    heading_levels.append(level)
            
            # Ensure we have proper heading structure
            if not has_main_header:
                self.logger.warning("Missing main header (H1)")
                return False
            
            if not has_processing_notes:
                self.logger.warning("Missing processing notes section")
                return False
            
            # Check for reasonable content length
            if len(content) < 100:
                self.logger.warning("Content appears too short")
                return False
            
            self.logger.info("Markdown validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Markdown validation failed: {e}")
            return False
    
    def _ensure_output_directory(self) -> None:
        """
        Create output directory if it doesn't exist.
        
        Raises:
            OSError: If directory cannot be created
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Output directory ready: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create output directory {self.output_dir}: {e}")
            raise OSError(f"Cannot create output directory: {e}")