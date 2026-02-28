# ABOUTME: Pure pipeline functions for the 4-phase summarization workflow.
# ABOUTME: Shared by both the CLI and web interfaces with no display logic.
"""
Summarization Pipeline

Four pure functions encapsulating the core summarization workflow:
discover → process → analyze → generate. Each function delegates to
the appropriate component class and returns structured results with
no print/display side effects.
"""

import logging
from datetime import date
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from config_manager import AppConfig
from content_processor import ContentProcessor, ProcessedContent, ProcessingStats
from file_discovery import FileDiscovery, FileDiscoveryResult
from llm_data_structures import AnalysisResult, APIStats
from summary_generator import PeriodSummary, SummaryGenerator, SummaryStats
from unified_llm_client import UnifiedLLMClient

logger = logging.getLogger(__name__)


def discover_files(
    base_path: str, start_date: date, end_date: date
) -> FileDiscoveryResult:
    """
    Phase 1: Discover journal files in the given date range.

    Args:
        base_path: Root directory containing journal file hierarchy.
        start_date: Inclusive start of the date range.
        end_date: Inclusive end of the date range.

    Returns:
        FileDiscoveryResult with found/missing file lists and statistics.
    """
    file_discovery = FileDiscovery(base_path=base_path)
    return file_discovery.discover_files(start_date, end_date)


def process_content(
    file_paths: List[Path], max_file_size_mb: int = 50
) -> Tuple[List[ProcessedContent], ProcessingStats]:
    """
    Phase 2: Read and sanitize journal file content.

    Args:
        file_paths: Paths to journal files discovered in phase 1.
        max_file_size_mb: Maximum individual file size to process.

    Returns:
        Tuple of (processed content list, processing statistics).
    """
    content_processor = ContentProcessor(max_file_size_mb=max_file_size_mb)
    return content_processor.process_files(file_paths)


def analyze_content(
    processed_content: List[ProcessedContent],
    config: AppConfig,
    on_fallback: Optional[Callable[[str], None]] = None,
) -> Tuple[List[AnalysisResult], APIStats, UnifiedLLMClient]:
    """
    Phase 3: Analyze processed content with LLM for entity extraction.

    Args:
        processed_content: Content items from phase 2.
        config: Application configuration (selects LLM provider).
        on_fallback: Optional callback for provider fallback notifications.

    Returns:
        Tuple of (analysis results, API statistics, LLM client instance).
        The client is returned so it can be reused in phase 4.
    """
    llm_client = UnifiedLLMClient(config, on_fallback=on_fallback)

    analysis_results: List[AnalysisResult] = []
    for content in processed_content:
        logger.debug("Analyzing %s", content.file_path.name)
        result = llm_client.analyze_content(content.content, content.file_path)
        analysis_results.append(result)

    api_stats = llm_client.get_stats()
    return analysis_results, api_stats, llm_client


def generate_summaries(
    analysis_results: List[AnalysisResult],
    llm_client: UnifiedLLMClient,
    summary_type: str,
    start_date: date,
    end_date: date,
) -> Tuple[List[PeriodSummary], SummaryStats]:
    """
    Phase 4: Generate period summaries from LLM analysis results.

    Args:
        analysis_results: Entity-extraction results from phase 3.
        llm_client: LLM client instance (reused from phase 3).
        summary_type: Either "weekly" or "monthly".
        start_date: Inclusive start of the summary range.
        end_date: Inclusive end of the summary range.

    Returns:
        Tuple of (period summaries, generation statistics).
    """
    summary_generator = SummaryGenerator(llm_client)
    return summary_generator.generate_summaries(
        analysis_results, summary_type, start_date, end_date
    )
