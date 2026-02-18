#!/usr/bin/env python3
# ABOUTME: Google GenAI LLM client for content analysis using Gemini models on Vertex AI.
# ABOUTME: Inherits shared logic from BaseLLMClient; provides Google-specific API calls.
"""
Google GenAI Client - Google Vertex AI Gemini API integration.

This module implements the Google GenAI API client that provides content
analysis functionality using Google's Gemini models through the Vertex AI
platform. Shared analysis logic (prompt building, JSON parsing, deduplication,
stats) is inherited from BaseLLMClient.
"""

from typing import List, Dict, Any
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

from base_llm_client import BaseLLMClient
from config_manager import GoogleGenAIConfig
from llm_data_structures import AnalysisResult, APIStats


class GoogleGenAIClient(BaseLLMClient):
    """
    Google GenAI API client with configuration management support.

    This client handles entity extraction from journal entries using Gemini
    models on Google's Vertex AI platform, providing the same interface as
    BedrockClient for seamless provider switching.
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
        self.client = self._create_genai_client()
        super().__init__()

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

            logger = logging.getLogger(__name__)
            logger.debug("Successfully created Google GenAI client")
            return client

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create Google GenAI client: {e}")
            raise ValueError(f"Failed to create Google GenAI client: {e}")

    def _make_api_call(self, prompt: str) -> str:
        """
        Make Google GenAI API call with retry logic and return response text.

        Args:
            prompt: Analysis prompt for Gemini

        Returns:
            str: Text content from the API response

        Raises:
            Exception: If all retry attempts fail
        """
        return self._make_api_call_with_retry(prompt)

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

    def test_connection(self) -> bool:
        """
        Test the Google GenAI connection with a simple API call.

        Returns:
            bool: True if connection successful, False otherwise
        """
        start_time = time.time()
        self.stats.total_calls += 1

        try:
            # Simple test prompt to minimize token usage
            test_prompt = "Respond with valid JSON: {\"test\": \"success\"}"

            # Add diagnostic logging
            self.logger.info(f"Testing Google GenAI connection with model: {self.config.model}")
            self.logger.info(f"Project: {self.config.project}")
            self.logger.info(f"Location: {self.config.location}")

            # Make a simple API call with retry logic (but only 1 retry for connection test)
            response_text = self._make_api_call_with_retry(test_prompt, max_retries=1)

            # Update statistics for successful connection test
            call_time = time.time() - start_time
            self.stats.successful_calls += 1
            self.stats.total_time += call_time
            self.stats.average_response_time = self.stats.total_time / self.stats.successful_calls

            # If we get here, the connection works
            self.logger.info("Google GenAI connection test successful")
            return True

        except Exception as e:
            # Update statistics for failed connection test
            self.stats.failed_calls += 1
            call_time = time.time() - start_time
            self.stats.total_time += call_time

            # Update average response time even for failed requests
            if self.stats.total_calls > 0:
                self.stats.average_response_time = self.stats.total_time / self.stats.total_calls

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

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider-specific configuration information.

        Returns:
            Dict[str, Any]: Google GenAI-specific configuration information
                           including project, location, and model
        """
        return {
            "provider": "google_genai",
            "project": self.config.project,
            "location": self.config.location,
            "model": self.config.model
        }
