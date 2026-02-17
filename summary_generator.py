#!/usr/bin/env python3
"""
Summary Generator - Phase 5: Summary Generation System

This module implements intelligent summary generation with time period grouping 
and LLM-powered synthesis for work journal entries.

Author: Work Journal Summarizer Project
Version: Phase 5 - Summary Generation System
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Dict, Tuple
from collections import defaultdict
import calendar
import logging
import time
import re
from pathlib import Path

from llm_data_structures import AnalysisResult, LLMClientProtocol


@dataclass
class PeriodSummary:
    """Summary for a specific time period (week or month)."""
    period_name: str
    start_date: date
    end_date: date
    projects: List[str]
    participants: List[str]
    tasks: List[str]
    themes: List[str]
    summary_text: str
    entry_count: int
    generation_time: float
    word_count: int


@dataclass
class SummaryStats:
    """Statistics for summary generation process."""
    total_periods: int
    successful_summaries: int
    failed_summaries: int
    total_entries_processed: int
    total_generation_time: float
    average_summary_length: int


class SummaryGenerator:
    """
    Generator for intelligent work journal summaries.
    
    This class groups journal analysis results by time periods (weekly or monthly)
    and generates coherent narrative summaries using LLM synthesis.
    """
    
    # Summary generation prompt template
    SUMMARY_PROMPT = """
Generate a professional work summary paragraph for the following period:

PERIOD: {period_name}
DATE RANGE: {start_date} to {end_date}
JOURNAL ENTRIES: {entry_count}

EXTRACTED INFORMATION:
Projects: {projects}
Participants: {participants}
Key Tasks: {tasks}
Major Themes: {themes}

Requirements:
- Write a single, coherent paragraph (200-400 words)
- Professional, narrative tone (avoid bullet points)
- Highlight major themes and focus areas
- Mention key projects and initiatives
- Acknowledge important collaborations
- Summarize significant accomplishments
- Flow naturally and maintain readability

Generate only the summary paragraph, no additional text.
"""
    
    def __init__(self, llm_client: LLMClientProtocol):
        """
        Initialize SummaryGenerator with LLM client.
        
        Args:
            llm_client: Configured LLM client for summary generation
        """
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        
    def generate_summaries(self, analysis_results: List[AnalysisResult], 
                          summary_type: str, start_date: date, end_date: date) -> Tuple[List[PeriodSummary], SummaryStats]:
        """
        Generate weekly or monthly summaries from analysis results.
        
        Args:
            analysis_results: List of analysis results from journal processing
            summary_type: Either "weekly" or "monthly"
            start_date: Start date of the range
            end_date: End date of the range
            
        Returns:
            Tuple of (list of period summaries, generation statistics)
        """
        start_time = time.time()
        
        # Initialize statistics
        stats = SummaryStats(
            total_periods=0,
            successful_summaries=0,
            failed_summaries=0,
            total_entries_processed=len(analysis_results),
            total_generation_time=0.0,
            average_summary_length=0
        )
        
        if not analysis_results:
            self.logger.info("No analysis results provided for summary generation")
            return [], stats
        
        self.logger.info(f"Generating {summary_type} summaries for {len(analysis_results)} entries")
        
        # Group analysis results by time periods
        grouped_results = self._group_by_periods(analysis_results, summary_type)
        stats.total_periods = len(grouped_results)
        
        summaries = []
        total_word_count = 0
        
        # Generate summary for each period
        for period_name, period_results in grouped_results.items():
            try:
                self.logger.info(f"Generating summary for {period_name} ({len(period_results)} entries)")
                
                # Calculate period dates
                if summary_type == "weekly":
                    # Extract date from period name and calculate week range
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', period_name)
                    if date_match:
                        period_date = date.fromisoformat(date_match.group(1))
                        period_name_formatted, period_start, period_end = self._calculate_week_period(period_date)
                    else:
                        # Fallback: use first result's date
                        period_date = self._extract_date_from_path(period_results[0].file_path)
                        period_name_formatted, period_start, period_end = self._calculate_week_period(period_date)
                else:  # monthly
                    # Extract date from period name
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', period_name)
                    if date_match:
                        period_date = date.fromisoformat(date_match.group(1))
                        period_name_formatted, period_start, period_end = self._calculate_month_period(period_date)
                    else:
                        # Fallback: use first result's date
                        period_date = self._extract_date_from_path(period_results[0].file_path)
                        period_name_formatted, period_start, period_end = self._calculate_month_period(period_date)
                
                # Aggregate entities for the period
                aggregated_entities = self._aggregate_entities(period_results)
                
                # Generate summary text
                summary_text = self._generate_period_summary(
                    period_name_formatted, period_start, period_end,
                    aggregated_entities, len(period_results)
                )
                
                # Calculate word count
                word_count = len(summary_text.split()) if summary_text else 0
                total_word_count += word_count
                
                # Create period summary
                period_summary = PeriodSummary(
                    period_name=period_name_formatted,
                    start_date=period_start,
                    end_date=period_end,
                    projects=aggregated_entities['projects'],
                    participants=aggregated_entities['participants'],
                    tasks=aggregated_entities['tasks'],
                    themes=aggregated_entities['themes'],
                    summary_text=summary_text,
                    entry_count=len(period_results),
                    generation_time=time.time() - start_time,
                    word_count=word_count
                )
                
                summaries.append(period_summary)
                stats.successful_summaries += 1
                
            except Exception as e:
                self.logger.error(f"Failed to generate summary for {period_name}: {e}")
                stats.failed_summaries += 1
                continue
        
        # Calculate final statistics
        stats.total_generation_time = time.time() - start_time
        if stats.successful_summaries > 0:
            stats.average_summary_length = total_word_count // stats.successful_summaries
        
        self.logger.info(f"Summary generation complete: {stats.successful_summaries} successful, "
                        f"{stats.failed_summaries} failed")
        
        return summaries, stats
        
    def _group_by_periods(self, analysis_results: List[AnalysisResult], 
                         summary_type: str) -> Dict[str, List[AnalysisResult]]:
        """
        Group analysis results by time periods.
        
        Args:
            analysis_results: List of analysis results to group
            summary_type: Either "weekly" or "monthly"
            
        Returns:
            Dictionary mapping period names to lists of analysis results
        """
        grouped = defaultdict(list)
        
        for result in analysis_results:
            try:
                # Extract date from file path
                result_date = self._extract_date_from_path(result.file_path)
                
                if summary_type == "weekly":
                    period_name, _, _ = self._calculate_week_period(result_date)
                else:  # monthly
                    period_name, _, _ = self._calculate_month_period(result_date)
                
                grouped[period_name].append(result)
                
            except Exception as e:
                self.logger.warning(f"Failed to group result {result.file_path}: {e}")
                continue
        
        # Sort groups by period name (chronological order)
        return dict(sorted(grouped.items()))
        
    def _calculate_week_period(self, target_date: date) -> Tuple[str, date, date]:
        """
        Calculate week period name and date range.
        
        Args:
            target_date: Date within the target week
            
        Returns:
            Tuple of (period_name, start_date, end_date)
        """
        # Calculate Monday of the week (start of week)
        days_since_monday = target_date.weekday()
        monday = target_date - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        
        period_name = f"Week of {monday.strftime('%Y-%m-%d')}"
        
        return period_name, monday, sunday
        
    def _calculate_month_period(self, target_date: date) -> Tuple[str, date, date]:
        """
        Calculate month period name and date range.
        
        Args:
            target_date: Date within the target month
            
        Returns:
            Tuple of (period_name, start_date, end_date)
        """
        # First day of the month
        start_date = target_date.replace(day=1)
        
        # Last day of the month
        _, last_day = calendar.monthrange(target_date.year, target_date.month)
        end_date = target_date.replace(day=last_day)
        
        period_name = target_date.strftime('%B %Y')
        
        return period_name, start_date, end_date
        
    def _aggregate_entities(self, results: List[AnalysisResult]) -> Dict[str, List[str]]:
        """
        Aggregate and deduplicate entities across period.
        
        Args:
            results: List of analysis results for the period
            
        Returns:
            Dictionary of aggregated entities by category
        """
        aggregated = {
            'projects': [],
            'participants': [],
            'tasks': [],
            'themes': []
        }
        
        # Use sets to track unique entities (case-insensitive)
        unique_entities = {
            'projects': set(),
            'participants': set(),
            'tasks': set(),
            'themes': set()
        }
        
        for result in results:
            # Aggregate each entity type
            for category in aggregated.keys():
                entities = getattr(result, category, [])
                for entity in entities:
                    if entity and isinstance(entity, str):
                        # Use lowercase for deduplication, but preserve original case
                        entity_lower = entity.strip().lower()
                        if entity_lower not in unique_entities[category]:
                            unique_entities[category].add(entity_lower)
                            aggregated[category].append(entity.strip())
        
        # Sort entities for consistent output
        for category in aggregated.keys():
            aggregated[category].sort()
        
        return aggregated
        
    def _generate_period_summary(self, period_name: str, start_date: date, 
                                end_date: date, aggregated_entities: Dict[str, List[str]], 
                                entry_count: int) -> str:
        """
        Generate narrative summary for a time period.
        
        Args:
            period_name: Name of the time period
            start_date: Start date of the period
            end_date: End date of the period
            aggregated_entities: Aggregated entities for the period
            entry_count: Number of journal entries in the period
            
        Returns:
            Generated summary text
        """
        try:
            # Format entities for prompt
            projects_str = ", ".join(aggregated_entities['projects']) if aggregated_entities['projects'] else "None identified"
            participants_str = ", ".join(aggregated_entities['participants']) if aggregated_entities['participants'] else "None identified"
            tasks_str = ", ".join(aggregated_entities['tasks']) if aggregated_entities['tasks'] else "None identified"
            themes_str = ", ".join(aggregated_entities['themes']) if aggregated_entities['themes'] else "None identified"
            
            # Create summary prompt
            prompt = self.SUMMARY_PROMPT.format(
                period_name=period_name,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                entry_count=entry_count,
                projects=projects_str,
                participants=participants_str,
                tasks=tasks_str,
                themes=themes_str
            )
            
            # Generate summary using LLM
            analysis_result = self.llm_client.analyze_content(prompt, Path("summary_generation"))
            
            # Extract summary text from response
            if analysis_result.raw_response:
                # Try to extract clean text from the response
                summary_text = self._extract_summary_text(analysis_result.raw_response)
                if summary_text:
                    return summary_text
            
            # Fallback: generate basic summary from entities
            return self._generate_fallback_summary(period_name, aggregated_entities, entry_count)
            
        except Exception as e:
            self.logger.error(f"Failed to generate LLM summary for {period_name}: {e}")
            # Return fallback summary
            return self._generate_fallback_summary(period_name, aggregated_entities, entry_count)
    
    def _extract_summary_text(self, raw_response: str) -> str:
        """
        Extract clean summary text from LLM response.
        
        Args:
            raw_response: Raw response from LLM
            
        Returns:
            Cleaned summary text
        """
        try:
            # If it's JSON, try to parse it
            if raw_response.strip().startswith('{'):
                import json
                parsed = json.loads(raw_response)
                # Look for common summary fields
                for field in ['summary', 'text', 'content', 'response']:
                    if field in parsed and isinstance(parsed[field], str):
                        return parsed[field].strip()
            
            # Otherwise, treat as plain text
            # Remove common prefixes and clean up
            text = raw_response.strip()
            
            # Remove common response prefixes
            prefixes_to_remove = [
                "Here is the summary:",
                "Summary:",
                "The summary is:",
                "Generated summary:",
            ]
            
            for prefix in prefixes_to_remove:
                if text.lower().startswith(prefix.lower()):
                    text = text[len(prefix):].strip()
            
            return text
            
        except Exception as e:
            self.logger.warning(f"Failed to extract summary text: {e}")
            return raw_response.strip()
    
    def _generate_fallback_summary(self, period_name: str, 
                                  aggregated_entities: Dict[str, List[str]], 
                                  entry_count: int) -> str:
        """
        Generate a basic fallback summary when LLM generation fails.
        
        Args:
            period_name: Name of the time period
            aggregated_entities: Aggregated entities for the period
            entry_count: Number of journal entries
            
        Returns:
            Basic summary text
        """
        summary_parts = [f"During {period_name}, {entry_count} journal entries were processed."]
        
        if aggregated_entities['projects']:
            projects = aggregated_entities['projects'][:3]  # Limit to top 3
            summary_parts.append(f"Key projects included {', '.join(projects)}.")
        
        if aggregated_entities['participants']:
            participants = aggregated_entities['participants'][:3]  # Limit to top 3
            summary_parts.append(f"Collaboration involved {', '.join(participants)}.")
        
        if aggregated_entities['themes']:
            themes = aggregated_entities['themes'][:3]  # Limit to top 3
            summary_parts.append(f"Major themes focused on {', '.join(themes)}.")
        
        return " ".join(summary_parts)
    
    def _extract_date_from_path(self, file_path: Path) -> date:
        """
        Extract date from file path.
        
        Args:
            file_path: Path to journal file
            
        Returns:
            Extracted date
            
        Raises:
            ValueError: If date cannot be extracted
        """
        # Look for date pattern in filename (YYYY-MM-DD)
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, str(file_path))
        
        if match:
            return date.fromisoformat(match.group(1))
        
        raise ValueError(f"Could not extract date from file path: {file_path}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # This would normally be called from the main application
    print("SummaryGenerator module loaded successfully")