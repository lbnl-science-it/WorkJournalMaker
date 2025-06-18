#!/usr/bin/env python3
"""
Google GenAI Client - Multi-Provider LLM Support

This module implements the Google GenAI API client that mirrors the BedrockClient
interface, providing content analysis functionality using Google's Gemini models
through the Vertex AI platform.

Author: Work Journal Summarizer Project
Version: Multi-Provider Support
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import time
import logging
import random

try:
    import google.genai as genai
    from google.genai import errors as genai_errors
except ImportError:
    genai = None
    genai_errors = None

from config_manager import GoogleGenAIConfig
from llm_data_structures import AnalysisResult, APIStats


class GoogleGenAIClient:
    """
    Google GenAI API client with configuration management support.
    
    This client handles entity extraction from journal entries using Gemini
    models on Google's Vertex AI platform, providing the same interface as
    BedrockClient for seamless provider switching.
    """
    
    # Analysis prompt template for Gemini (same structure as BedrockClient)
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

    def __init__(self, config: GoogleGenAIConfig):
        """
        Initialize Google GenAI client with configuration.
        
        Args:
            config: Google GenAI configuration object
            
        Raises:
            ImportError: If google.genai is not available
            ValueError: If configuration is invalid
        """
        if genai is None:
            raise ImportError(
                "google.genai is not available. Please install with: pip install google-genai"
            )
            
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.stats = APIStats(0, 0, 0, 0.0, 0.0, 0)
        self.client = self._create_genai_client()
        
        self.logger.info(f"Initialized Google GenAI client with model: {config.model}")
        self.logger.info(f"Project: {config.project}, Location: {config.location}")
        
    def _create_genai_client(self):
        """
        Create Google GenAI client with proper configuration.
        
        Returns:
            genai.Client: Configured Google GenAI client
            
        Raises:
            ValueError: If client creation fails
        """
        try:
            # Create client with Vertex AI configuration
            client = genai.Client(
                vertexai=True,
                project=self.config.project,
                location=self.config.location
            )
            
            self.logger.debug("Successfully created Google GenAI client")
            return client
            
        except Exception as e:
            self.logger.error(f"Failed to create Google GenAI client: {e}")
            raise ValueError(f"Failed to create Google GenAI client: {e}")
    
    def analyze_content(self, content: str, file_path: Path) -> AnalysisResult:
        """
        Analyze journal content and extract entities using Google GenAI.
        
        Args:
            content: Journal content to analyze
            file_path: Path to the source file for tracking
            
        Returns:
            AnalysisResult: Extracted entities and metadata
        """
        start_time = time.time()
        self.stats.total_calls += 1
        
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(content)
            
            # Make API call with retry logic
            response_text = self._make_api_call_with_retry(prompt)
            
            # Parse response
            entities = self._parse_response(response_text)
            
            # Deduplicate entities (using same logic as BedrockClient)
            entities = self._deduplicate_entities(entities)
            
            # Calculate call time
            call_time = time.time() - start_time
            self.stats.successful_calls += 1
            self.stats.total_time += call_time
            self.stats.average_response_time = self.stats.total_time / self.stats.successful_calls
            
            self.logger.debug(f"Successfully analyzed content from {file_path}")
            
            return AnalysisResult(
                file_path=file_path,
                projects=entities.get('projects', []),
                participants=entities.get('participants', []),
                tasks=entities.get('tasks', []),
                themes=entities.get('themes', []),
                api_call_time=call_time,
                raw_response=response_text
            )
            
        except Exception as e:
            self.stats.failed_calls += 1
            call_time = time.time() - start_time
            self.stats.total_time += call_time
            
            # Update average response time even for failed requests
            if self.stats.total_calls > 0:
                self.stats.average_response_time = self.stats.total_time / self.stats.total_calls
            
            error_type = type(e).__name__
            self.logger.error(f"Failed to analyze content from {file_path}: {error_type} - {str(e)}")
            
            # Log additional context for different error types
            if self._is_rate_limit_error(e):
                self.logger.warning("Rate limit hit during content analysis")
            elif self._is_authentication_error(e):
                self.logger.error("Authentication error during content analysis")
            elif self._is_network_error(e):
                self.logger.warning("Network error during content analysis")
            
            # Return empty result on failure with detailed error information
            return AnalysisResult(
                file_path=file_path,
                projects=[],
                participants=[],
                tasks=[],
                themes=[],
                api_call_time=call_time,
                raw_response=f"ERROR ({error_type}): {str(e)}"
            )
    
    def _create_analysis_prompt(self, content: str) -> str:
        """
        Create structured prompt for entity extraction.
        
        Args:
            content: Journal content to analyze
            
        Returns:
            str: Formatted prompt for Gemini
        """
        # Truncate content if too long (Gemini has token limits)
        max_content_length = 8000  # Conservative limit for context
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n[Content truncated for analysis]"
        
        return self.ANALYSIS_PROMPT.format(content=content)
    
    def _make_api_call_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Make API call to Google GenAI with exponential backoff retry logic.
        
        Args:
            prompt: Analysis prompt for Gemini
            max_retries: Maximum number of retry attempts
            
        Returns:
            str: Response text from the API
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(max_retries + 1):
            try:
                # Use the configured model to generate content with timeout
                response = self.client.models.generate_content(
                    model=self.config.model,
                    contents=prompt,
                    config={
                        'temperature': 0.1,  # Low temperature for consistent extraction
                        'top_p': 0.9,
                        'max_output_tokens': 1000
                    }
                )
                
                # Extract text from response
                if hasattr(response, 'text') and response.text:
                    return response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    # Handle structured response format
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts and hasattr(parts[0], 'text'):
                            return parts[0].text
                
                raise ValueError("No text content found in API response")
                
            except Exception as e:
                error_type = type(e).__name__
                error_message = str(e)
                
                # Handle different types of Google GenAI API errors
                if self._is_rate_limit_error(e):
                    self.stats.rate_limit_hits += 1
                    if attempt < max_retries:
                        # Exponential backoff with jitter for rate limiting
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        self.logger.warning(f"Rate limited, waiting {wait_time:.1f}s before retry {attempt + 1}")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"Rate limit exceeded after {max_retries + 1} attempts")
                        raise
                
                elif self._is_authentication_error(e):
                    # Authentication errors should not be retried
                    self.logger.error(f"Authentication error - not retrying: {error_message}")
                    raise
                
                elif self._is_network_error(e):
                    if attempt < max_retries:
                        # Network errors should be retried with exponential backoff
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        self.logger.warning(f"Network error, retrying in {wait_time:.1f}s: {error_message}")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"Network error after {max_retries + 1} attempts: {error_message}")
                        raise
                
                elif self._is_invalid_request_error(e):
                    # Invalid request errors should not be retried
                    self.logger.error(f"Invalid request error - not retrying: {error_message}")
                    raise
                
                elif self._is_timeout_error(e):
                    if attempt < max_retries:
                        # Timeout errors should be retried
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        self.logger.warning(f"Timeout error, retrying in {wait_time:.1f}s: {error_message}")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"Timeout error after {max_retries + 1} attempts: {error_message}")
                        raise
                
                else:
                    # Unknown errors - log and don't retry
                    self.logger.error(f"Unknown error ({error_type}) - not retrying: {error_message}")
                    raise
        
        raise Exception(f"Failed to complete API call after {max_retries + 1} attempts")
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """
        Check if the error is a rate limiting error.
        
        Args:
            error: Exception to check
            
        Returns:
            bool: True if this is a rate limiting error
        """
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        # Common rate limiting indicators for Google GenAI
        rate_limit_indicators = [
            'rate limit',
            'quota exceeded',
            'too many requests',
            'throttled',
            'resource exhausted',
            '429'
        ]
        
        return any(indicator in error_message for indicator in rate_limit_indicators)
    
    def _is_authentication_error(self, error: Exception) -> bool:
        """
        Check if the error is an authentication error.
        
        Args:
            error: Exception to check
            
        Returns:
            bool: True if this is an authentication error
        """
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        # Common authentication error indicators
        auth_indicators = [
            'authentication',
            'unauthorized',
            'permission denied',
            'access denied',
            'invalid credentials',
            'unauthenticated',
            '401',
            '403'
        ]
        
        return any(indicator in error_message for indicator in auth_indicators)
    
    def _is_network_error(self, error: Exception) -> bool:
        """
        Check if the error is a network-related error.
        
        Args:
            error: Exception to check
            
        Returns:
            bool: True if this is a network error
        """
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        # Common network error indicators
        network_indicators = [
            'connection',
            'network',
            'timeout',
            'unreachable',
            'dns',
            'socket',
            'ssl',
            'tls',
            'certificate'
        ]
        
        # Also check for specific exception types that indicate network issues
        network_exception_types = [
            'ConnectionError',
            'TimeoutError',
            'URLError',
            'HTTPError',
            'SSLError'
        ]
        
        return (any(indicator in error_message for indicator in network_indicators) or
                error_type in network_exception_types)
    
    def _is_invalid_request_error(self, error: Exception) -> bool:
        """
        Check if the error is an invalid request error.
        
        Args:
            error: Exception to check
            
        Returns:
            bool: True if this is an invalid request error
        """
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        # Common invalid request error indicators
        invalid_request_indicators = [
            'invalid request',
            'bad request',
            'malformed',
            'invalid parameter',
            'invalid model',
            'invalid input',
            '400'
        ]
        
        return any(indicator in error_message for indicator in invalid_request_indicators)
    
    def _is_timeout_error(self, error: Exception) -> bool:
        """
        Check if the error is a timeout error.
        
        Args:
            error: Exception to check
            
        Returns:
            bool: True if this is a timeout error
        """
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        # Common timeout error indicators
        timeout_indicators = [
            'timeout',
            'timed out',
            'deadline exceeded',
            'request timeout'
        ]
        
        timeout_exception_types = [
            'TimeoutError',
            'ReadTimeoutError',
            'ConnectTimeoutError'
        ]
        
        return (any(indicator in error_message for indicator in timeout_indicators) or
                error_type in timeout_exception_types)
    
    def _parse_response(self, response_text: str) -> Dict[str, List[str]]:
        """
        Parse Google GenAI response and validate structure.
        
        Args:
            response_text: Raw response text from Google GenAI API
            
        Returns:
            Dict: Parsed entities with validated structure
        """
        try:
            # Parse JSON from the response text
            # Gemini sometimes wraps JSON in markdown code blocks
            json_text = self._extract_json_from_text(response_text)
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
            self.logger.debug(f"Raw response text: {response_text}")
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
        import re
        
        # Handle edge cases
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
        self.logger.debug("Reset API usage statistics")
    
    def test_connection(self) -> bool:
        """
        Test the Google GenAI connection with a simple API call.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Simple test prompt to minimize token usage
            test_prompt = "Respond with valid JSON: {\"test\": \"success\"}"
            
            # Add diagnostic logging
            self.logger.info(f"Testing Google GenAI connection with model: {self.config.model}")
            self.logger.info(f"Project: {self.config.project}")
            self.logger.info(f"Location: {self.config.location}")
            
            # Make a simple API call with retry logic (but only 1 retry for connection test)
            response_text = self._make_api_call_with_retry(test_prompt, max_retries=1)
            
            # If we get here, the connection works
            self.logger.info("Google GenAI connection test successful")
            return True
            
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            
            self.logger.error(f"Google GenAI connection test failed: {error_type} - {error_message}")
            
            # Provide specific guidance based on error type
            if self._is_authentication_error(e):
                self.logger.error("DIAGNOSIS: Authentication error - check Google Cloud credentials")
                self.logger.error("SOLUTION: Verify Google Cloud authentication and project permissions")
                self.logger.error("  - Check if Application Default Credentials are set up")
                self.logger.error("  - Verify project ID and location are correct")
                self.logger.error("  - Ensure Vertex AI API is enabled for the project")
            elif self._is_invalid_request_error(e):
                self.logger.error("DIAGNOSIS: Invalid request - check model configuration")
                self.logger.error(f"SOLUTION: Verify model {self.config.model} is available in {self.config.location}")
                self.logger.error("  - Check if the model name is correct")
                self.logger.error("  - Verify the model is available in the specified region")
            elif self._is_network_error(e):
                self.logger.error("DIAGNOSIS: Network error - check connectivity")
                self.logger.error("SOLUTION: Check network connectivity to Google Cloud services")
                self.logger.error("  - Verify internet connection")
                self.logger.error("  - Check firewall settings")
            elif self._is_rate_limit_error(e):
                self.logger.error("DIAGNOSIS: Rate limit exceeded")
                self.logger.error("SOLUTION: Wait a moment and try again, or check quota limits")
            else:
                self.logger.error("DIAGNOSIS: Unexpected error occurred")
                self.logger.error("SOLUTION: Check Google GenAI service status and configuration")
            
            return False