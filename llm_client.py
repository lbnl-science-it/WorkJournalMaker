#!/usr/bin/env python3
"""
LLM Client - Phase 4: LLM API Integration

This module implements robust LLM API integration for content analysis and entity extraction
using AWS Bedrock Claude API with comprehensive error handling and retry logic.

Author: Work Journal Summarizer Project
Version: Phase 4 - LLM API Integration
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import json
import time
import logging
import os
import re


@dataclass
class AnalysisResult:
    """Result of LLM analysis for a single journal file."""
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
    """Statistics for API usage across all calls."""
    total_calls: int
    successful_calls: int
    failed_calls: int
    total_time: float
    average_response_time: float
    rate_limit_hits: int


class LLMClient:
    """
    LLM client for analyzing journal content using AWS Bedrock Claude API.
    
    This client handles entity extraction from journal entries, identifying:
    - Projects (formal and informal references)
    - Participants (people mentioned in various formats)
    - Tasks (specific activities and work items)
    - Themes (major topics and focus areas)
    """
    
    # Analysis prompt template for Claude
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

    def __init__(self, region: str = "us-west-2",
                 model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        """
        Initialize LLM client with AWS Bedrock configuration.
        
        Args:
            region: AWS region for Bedrock service
            model_id: Claude model identifier on Bedrock
        """
        self.region = region
        self.model_id = model_id
        self.client = self._create_bedrock_client()
        self.logger = logging.getLogger(__name__)
        self.stats = APIStats(0, 0, 0, 0.0, 0.0, 0)
        
    def _create_bedrock_client(self):
        """
        Create Bedrock client with proper credentials.
        
        Returns:
            boto3.client: Configured Bedrock Runtime client
            
        Raises:
            ValueError: If AWS credentials are not available
        """
        try:
            # Check for required environment variables
            aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            
            if not aws_access_key or not aws_secret_key:
                raise ValueError(
                    "AWS credentials not found. Please set AWS_ACCESS_KEY_ID and "
                    "AWS_SECRET_ACCESS_KEY environment variables."
                )
            
            return boto3.client(
                'bedrock-runtime',
                region_name=self.region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        except Exception as e:
            # Logger not yet initialized, use print for error
            print(f"Failed to create Bedrock client: {e}")
            raise
            
    def analyze_content(self, content: str, file_path: Path) -> AnalysisResult:
        """
        Analyze journal content and extract entities using Claude on Bedrock.
        
        Args:
            content: Journal content to analyze
            file_path: Path to the source file for tracking
            
        Returns:
            AnalysisResult: Extracted entities and metadata
            
        Raises:
            Exception: If API call fails after retries
        """
        start_time = time.time()
        self.stats.total_calls += 1
        
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(content)
            
            # Format request for Bedrock
            request_body = self._format_bedrock_request(prompt)
            
            # Make API call with retry logic
            response = self._make_api_call_with_retry(request_body)
            
            # Parse response
            entities = self._parse_bedrock_response(response)
            
            # Deduplicate entities
            entities = self._deduplicate_entities(entities)
            
            # Calculate call time
            call_time = time.time() - start_time
            self.stats.successful_calls += 1
            self.stats.total_time += call_time
            self.stats.average_response_time = self.stats.total_time / self.stats.successful_calls
            
            return AnalysisResult(
                file_path=file_path,
                projects=entities.get('projects', []),
                participants=entities.get('participants', []),
                tasks=entities.get('tasks', []),
                themes=entities.get('themes', []),
                api_call_time=call_time,
                raw_response=json.dumps(entities)
            )
            
        except Exception as e:
            self.stats.failed_calls += 1
            call_time = time.time() - start_time
            self.stats.total_time += call_time
            
            self.logger.error(f"Failed to analyze content from {file_path}: {e}")
            
            # Return empty result on failure
            return AnalysisResult(
                file_path=file_path,
                projects=[],
                participants=[],
                tasks=[],
                themes=[],
                api_call_time=call_time,
                raw_response=f"ERROR: {str(e)}"
            )
    
    def _create_analysis_prompt(self, content: str) -> str:
        """
        Create structured prompt for entity extraction.
        
        Args:
            content: Journal content to analyze
            
        Returns:
            str: Formatted prompt for Claude
        """
        # Truncate content if too long (Claude has token limits)
        max_content_length = 8000  # Conservative limit for context
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n[Content truncated for analysis]"
        
        return self.ANALYSIS_PROMPT.format(content=content)
    
    def _format_bedrock_request(self, prompt: str) -> Dict[str, Any]:
        """
        Format request for Bedrock API.
        
        Args:
            prompt: Analysis prompt for Claude
            
        Returns:
            Dict: Formatted request body for Bedrock
        """
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent extraction
            "top_p": 0.9
        }
    
    def _make_api_call_with_retry(self, request_body: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        Make API call with exponential backoff retry logic.
        
        Args:
            request_body: Formatted request for Bedrock
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dict: API response from Bedrock
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(max_retries + 1):
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body),
                    contentType='application/json',
                    accept='application/json'
                )
                
                return json.loads(response['body'].read())
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                if error_code == 'ThrottlingException':
                    self.stats.rate_limit_hits += 1
                    if attempt < max_retries:
                        wait_time = (2 ** attempt) + 1  # Exponential backoff
                        self.logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                        time.sleep(wait_time)
                        continue
                
                self.logger.error(f"Bedrock API error: {error_code} - {e}")
                raise
                
            except BotoCoreError as e:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + 1
                    self.logger.warning(f"Network error, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                raise
                
            except Exception as e:
                self.logger.error(f"Unexpected error in API call: {e}")
                raise
        
        raise Exception(f"Failed to complete API call after {max_retries + 1} attempts")
    
    def _parse_bedrock_response(self, response: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Parse Bedrock response and validate structure.
        
        Args:
            response: Raw response from Bedrock API
            
        Returns:
            Dict: Parsed entities with validated structure
        """
        try:
            # Extract content from Bedrock response format
            content = response.get('content', [])
            if not content:
                raise ValueError("No content in response")
            
            # Get the text from the first content block
            text_content = content[0].get('text', '')
            if not text_content:
                raise ValueError("No text content in response")
            
            # Parse JSON from the text content
            # Claude sometimes wraps JSON in markdown code blocks
            json_text = self._extract_json_from_text(text_content)
            entities = json.loads(json_text)
            
            # Validate required fields
            required_fields = ['projects', 'participants', 'tasks', 'themes']
            for field in required_fields:
                if field not in entities:
                    entities[field] = []
                elif not isinstance(entities[field], list):
                    entities[field] = []
            
            return entities
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse API response: {e}")
            # Return empty structure on parse failure
            return {
                'projects': [],
                'participants': [],
                'tasks': [],
                'themes': []
            }
    
    def _extract_json_from_text(self, text: str) -> str:
        """
        Extract JSON from text that might contain markdown formatting.
        
        Args:
            text: Text that may contain JSON
            
        Returns:
            str: Extracted JSON string
        """
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
        
        # If no JSON found, return the text as-is and let JSON parser handle the error
        return text
    
    def _deduplicate_entities(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Remove duplicates and normalize entity names.
        
        Args:
            entities: Raw entities from API response
            
        Returns:
            Dict: Deduplicated and normalized entities
        """
        deduplicated = {}
        
        for category, items in entities.items():
            if not isinstance(items, list):
                deduplicated[category] = []
                continue
            
            # Remove duplicates while preserving order
            seen = set()
            unique_items = []
            
            for item in items:
                if not isinstance(item, str):
                    continue
                
                # Normalize: strip whitespace and convert to title case for comparison
                normalized = item.strip()
                if not normalized:
                    continue
                
                # Use lowercase for duplicate detection
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
            APIStats: Current statistics
        """
        return self.stats
    
    def reset_stats(self) -> None:
        """Reset API usage statistics."""
        self.stats = APIStats(0, 0, 0, 0.0, 0.0, 0)