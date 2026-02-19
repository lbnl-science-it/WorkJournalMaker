#!/usr/bin/env python3
# ABOUTME: LLM client for the CBORG service (OpenAI-compatible API at cborg.lbl.gov).
# ABOUTME: Tertiary fallback provider behind Google GenAI and AWS Bedrock.
"""
CBORG Client - OpenAI-compatible API integration for LBNL's CBORG service.

This module implements the CBORG API client using the openai Python package
with a custom base_url. Shared analysis logic (prompt building, JSON parsing,
deduplication, stats) is inherited from BaseLLMClient.
"""

from typing import Dict, Any
import os
import time
import logging

try:
    import openai
except ImportError:
    openai = None

from base_llm_client import BaseLLMClient
from config_manager import CBORGConfig


class CBORGClient(BaseLLMClient):
    """
    CBORG API client for content analysis via an OpenAI-compatible endpoint.

    Uses the openai Python SDK pointed at cborg.lbl.gov. Provides the same
    interface as BedrockClient and GoogleGenAIClient for seamless provider
    switching through UnifiedLLMClient.
    """

    def __init__(self, config: CBORGConfig):
        """
        Initialize CBORG client with configuration.

        Args:
            config: CBORG configuration object

        Raises:
            ImportError: If the openai package is not installed
            ValueError: If the API key environment variable is not set
        """
        if openai is None:
            raise ImportError(
                "openai is not available. Please install with: pip install openai"
            )

        self.config = config
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(
                f"API key not found. Please set the {config.api_key_env} environment variable."
            )

        self.client = openai.OpenAI(
            base_url=config.endpoint,
            api_key=api_key,
            timeout=config.timeout,
        )
        super().__init__()

        self.logger.info(f"Initialized CBORG client with model: {config.model}")
        self.logger.info(f"Endpoint: {config.endpoint}")

    def _make_api_call(self, prompt: str) -> str:
        """
        Make CBORG API call with retry logic and return the response text.

        Args:
            prompt: Analysis prompt

        Returns:
            str: Text content from the API response

        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=1000,
                )
                return response.choices[0].message.content

            except Exception as e:
                error_message = str(e).lower()

                if self._is_retryable(error_message):
                    if attempt < self.config.max_retries:
                        wait_time = (2 ** attempt) + 1
                        self.logger.warning(
                            f"Retryable error, waiting {wait_time}s before retry {attempt + 1}: {e}"
                        )
                        time.sleep(wait_time)
                        continue

                # Non-retryable or exhausted retries
                self.logger.error(f"CBORG API error: {e}")
                raise

        raise Exception(
            f"Failed to complete API call after {self.config.max_retries + 1} attempts"
        )

    def _is_retryable(self, error_message: str) -> bool:
        """Check if an error should be retried (rate limits, network issues)."""
        retryable_indicators = [
            "rate limit",
            "too many requests",
            "429",
            "timeout",
            "timed out",
            "connection",
            "network",
        ]
        return any(indicator in error_message for indicator in retryable_indicators)

    def test_connection(self) -> bool:
        """
        Test the CBORG connection with a simple API call.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Testing CBORG connection with model: {self.config.model}")
            self.logger.info(f"Endpoint: {self.config.endpoint}")

            self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": 'Respond with: {"test":"ok"}'}],
                temperature=0.1,
                max_tokens=50,
            )

            self.logger.info("CBORG connection test successful")
            return True

        except Exception as e:
            self.logger.error(f"CBORG connection test failed: {e}")
            return False

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider-specific configuration information.

        Returns:
            Dict[str, Any]: CBORG-specific configuration
        """
        return {
            "provider": "cborg",
            "endpoint": self.config.endpoint,
            "model": self.config.model,
        }
