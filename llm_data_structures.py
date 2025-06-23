#!/usr/bin/env python3
"""
LLM Data Structures - Shared data structures for LLM clients

This module defines shared data structures that are used by multiple LLM client
implementations (BedrockClient, GoogleGenAIClient, etc.) to ensure consistency
across different providers.

Author: Work Journal Summarizer Project
Version: Multi-Provider Support
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class AnalysisResult:
    """
    Result of LLM analysis for a single journal file.
    
    This dataclass represents the structured output from analyzing a work journal
    entry, containing extracted entities and metadata about the analysis process.
    It is provider-agnostic and used by all LLM client implementations.
    
    Attributes:
        file_path (Path): Path to the source journal file that was analyzed
        projects (List[str]): List of project names mentioned in the journal entry,
            including both formal project names and informal references
        participants (List[str]): List of people mentioned in the journal entry,
            captured in various formats (full names, first names, initials)
        tasks (List[str]): List of specific tasks, activities, or work items
            mentioned in the journal entry
        themes (List[str]): List of major topics, themes, or focus areas
            identified in the journal entry
        api_call_time (float): Time in seconds taken for the API call to complete
        confidence_score (Optional[float]): Optional confidence score for the
            analysis results (0.0 to 1.0), if provided by the LLM
        raw_response (Optional[str]): Optional raw response from the LLM API,
            useful for debugging and validation purposes
    
    Example:
        >>> result = AnalysisResult(
        ...     file_path=Path("journal_2024_01_15.md"),
        ...     projects=["Project Alpha", "Beta Initiative"],
        ...     participants=["John Smith", "Sarah"],
        ...     tasks=["Code review", "Meeting preparation"],
        ...     themes=["Development", "Planning"],
        ...     api_call_time=1.23,
        ...     confidence_score=0.85,
        ...     raw_response='{"projects": [...], ...}'
        ... )
    """
    file_path: Path
    projects: List[str]
    participants: List[str]
    tasks: List[str]
    themes: List[str]
    api_call_time: float
    confidence_score: Optional[float] = None
    raw_response: Optional[str] = None


@dataclass
class APIStats:
    """
    Statistics for API usage across all calls for an LLM client.
    
    This dataclass tracks comprehensive statistics about API usage, including
    call counts, timing information, and error rates. It provides insights into
    the performance and reliability of LLM API interactions.
    
    Attributes:
        total_calls (int): Total number of API calls made (successful + failed)
        successful_calls (int): Number of API calls that completed successfully
        failed_calls (int): Number of API calls that failed with errors
        total_time (float): Total time in seconds spent on all API calls
        average_response_time (float): Average response time per successful call
            in seconds, calculated as total_time / successful_calls
        rate_limit_hits (int): Number of times the client hit rate limits and
            had to retry with backoff
    
    Properties:
        - Success rate can be calculated as: successful_calls / total_calls
        - Failure rate can be calculated as: failed_calls / total_calls
        - Total processing time includes both successful and failed calls
    
    Example:
        >>> stats = APIStats(
        ...     total_calls=100,
        ...     successful_calls=95,
        ...     failed_calls=5,
        ...     total_time=150.5,
        ...     average_response_time=1.58,
        ...     rate_limit_hits=2
        ... )
        >>> success_rate = stats.successful_calls / stats.total_calls  # 0.95
    """
    total_calls: int
    successful_calls: int
    failed_calls: int
    total_time: float
    average_response_time: float
    rate_limit_hits: int