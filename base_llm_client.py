#!/usr/bin/env python3
# ABOUTME: Abstract base class for LLM provider clients.
# ABOUTME: Owns shared prompt templates, JSON parsing, entity dedup, and stats tracking.
"""
Base LLM Client - Shared logic for all LLM provider implementations.

This module provides a BaseLLMClient abstract base class that implements the
common flow for content analysis: prompt building, JSON extraction from
LLM responses, entity deduplication, and API statistics tracking. Concrete
subclasses only need to implement the provider-specific API call.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
import json
import time
import logging
import re

from llm_data_structures import AnalysisResult, APIStats


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM provider clients.

    Subclasses implement _make_api_call (and optionally test_connection and
    get_provider_info) while this class owns the shared analysis pipeline:
    prompt formatting, JSON extraction, entity deduplication, stats tracking,
    and the analyze_content orchestration.
    """

    # Analysis prompt template for entity extraction
    ANALYSIS_PROMPT = """
Analyze the following work journal entry and extract structured information.

JOURNAL CONTENT:
{content}

Extract the following information and respond with valid JSON only:

{{
  "projects": ["list of project names, both formal and informal"],
  "participants": ["list of people mentioned in any format"],
  "tasks": ["list of specific tasks, activities, or work items"],
  "themes": ["list of major topics, themes, or focus areas"]
}}

Guidelines:
- Include both formal project names and informal references
- Capture names in various formats (full names, first names, initials)
- Focus on concrete tasks and activities, not abstract concepts
- Identify recurring themes and topics
- Return empty arrays if no entities found in a category
- Ensure response is valid JSON format
"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__module__)
        self.stats = APIStats(0, 0, 0, 0.0, 0.0, 0)

    @abstractmethod
    def _make_api_call(self, prompt: str) -> str:
        """
        Make a provider-specific API call and return the response text.

        Subclasses handle both the raw API call and extracting the text
        content from the provider's response format.

        Args:
            prompt: The formatted analysis prompt.

        Returns:
            str: The text content from the API response.

        Raises:
            Exception: On API call failure.
        """
        ...

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connectivity to the configured LLM provider.

        Returns:
            bool: True if connection is successful.
        """
        ...

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Return provider-specific configuration metadata.

        Returns:
            Dict[str, Any]: Provider name, model, region, etc.
        """
        ...

    def analyze_content(self, content: str, file_path: Path) -> AnalysisResult:
        """
        Analyze journal content and extract entities.

        Orchestrates the shared analysis pipeline: prompt creation, API call,
        JSON parsing, field validation, entity deduplication, and stats tracking.

        Args:
            content: Journal text to analyze.
            file_path: Source file path for tracking.

        Returns:
            AnalysisResult: Extracted entities, or an empty result on failure.
        """
        start_time = time.time()
        self.stats.total_calls += 1

        try:
            prompt = self._create_analysis_prompt(content)
            response_text = self._make_api_call(prompt)
            entities = self._parse_response(response_text)
            entities = self._deduplicate_entities(entities)

            call_time = time.time() - start_time
            self.stats.successful_calls += 1
            self.stats.total_time += call_time
            self.stats.average_response_time = (
                self.stats.total_time / self.stats.successful_calls
            )

            return AnalysisResult(
                file_path=file_path,
                projects=entities.get("projects", []),
                participants=entities.get("participants", []),
                tasks=entities.get("tasks", []),
                themes=entities.get("themes", []),
                api_call_time=call_time,
                raw_response=json.dumps(entities),
            )

        except Exception as e:
            self.stats.failed_calls += 1
            call_time = time.time() - start_time
            self.stats.total_time += call_time

            error_type = type(e).__name__
            self.logger.error(f"Failed to analyze content from {file_path}: {error_type} - {e}")

            return AnalysisResult(
                file_path=file_path,
                projects=[],
                participants=[],
                tasks=[],
                themes=[],
                api_call_time=call_time,
                raw_response=f"ERROR ({error_type}): {str(e)}",
            )

    def _create_analysis_prompt(self, content: str) -> str:
        """
        Build the analysis prompt with content embedded.

        Truncates content exceeding 8000 characters to stay within
        provider token limits.

        Args:
            content: Journal text to embed.

        Returns:
            str: Formatted prompt ready for the LLM.
        """
        max_content_length = 8000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n[Content truncated for analysis]"
        return self.ANALYSIS_PROMPT.format(content=content)

    def _parse_response(self, response_text: str) -> Dict[str, List[str]]:
        """
        Parse LLM response text into a validated entity dictionary.

        Extracts JSON from the response, validates that each expected field
        is a list of strings, and fills missing fields with empty lists.

        Args:
            response_text: Raw text from the LLM response.

        Returns:
            Dict: Validated entity dictionary.
        """
        try:
            json_text = self._extract_json_from_text(response_text)
            entities = json.loads(json_text)

            required_fields = ["projects", "participants", "tasks", "themes"]
            for field in required_fields:
                if field not in entities:
                    entities[field] = []
                elif not isinstance(entities[field], list):
                    entities[field] = []

            return entities

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse API response: {e}")
            return {
                "projects": [],
                "participants": [],
                "tasks": [],
                "themes": [],
            }

    def _extract_json_from_text(self, text: str) -> str:
        """
        Extract a JSON object from text that may contain markdown formatting.

        Tries markdown code blocks first, then bare JSON objects, and falls
        back to returning the text as-is.

        Args:
            text: Text that may contain JSON.

        Returns:
            str: Extracted JSON string.
        """
        if not isinstance(text, str):
            return str(text)

        if not text or not text.strip():
            return text

        # Try to find JSON in markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            return match.group(1)

        # Try to find JSON object directly
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            return match.group(0)

        # If no JSON found, return the text as-is
        return text

    def _deduplicate_entities(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Remove duplicate and empty entity strings, preserving order.

        Uses case-insensitive comparison for duplicate detection but keeps
        the casing of the first occurrence.

        Args:
            entities: Raw entity dictionary from the LLM response.

        Returns:
            Dict: Deduplicated entity dictionary.
        """
        deduplicated = {}

        for category, items in entities.items():
            if not isinstance(items, list):
                deduplicated[category] = []
                continue

            seen = set()
            unique_items = []

            for item in items:
                if not isinstance(item, str):
                    continue

                normalized = item.strip()
                if not normalized:
                    continue

                key = normalized.lower()
                if key not in seen:
                    seen.add(key)
                    unique_items.append(normalized)

            deduplicated[category] = unique_items

        return deduplicated

    def get_stats(self) -> APIStats:
        """
        Get current API usage statistics.

        Returns:
            APIStats: Live statistics instance.
        """
        return self.stats

    def reset_stats(self) -> None:
        """Reset API usage statistics to zero."""
        self.stats = APIStats(0, 0, 0, 0.0, 0.0, 0)
