#!/usr/bin/env python3
# ABOUTME: AWS Bedrock LLM client for content analysis using Claude models.
# ABOUTME: Inherits shared logic from BaseLLMClient; provides Bedrock-specific API calls.
"""
Bedrock Client - AWS Bedrock Claude API integration.

This module implements the AWS Bedrock Claude API client with configuration
management support, retry logic, and comprehensive error handling. Shared
analysis logic (prompt building, JSON parsing, deduplication, stats) is
inherited from BaseLLMClient.
"""

from typing import List, Dict, Any
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import json
import time
import logging
import os

from base_llm_client import BaseLLMClient
from config_manager import BedrockConfig
from llm_data_structures import AnalysisResult, APIStats


class BedrockClient(BaseLLMClient):
    """
    AWS Bedrock Claude API client with configuration management support.

    This client handles entity extraction from journal entries using Claude
    on AWS Bedrock, with comprehensive configuration management and error handling.
    """

    def __init__(self, config: BedrockConfig):
        """
        Initialize Bedrock client with configuration.

        Args:
            config: Bedrock configuration object
        """
        self.config = config
        self.client = self._create_bedrock_client()
        super().__init__()

    def _create_bedrock_client(self):
        """
        Create Bedrock client with proper credentials from configuration.

        Returns:
            boto3.client: Configured Bedrock Runtime client

        Raises:
            ValueError: If AWS credentials are not available
        """
        try:
            # Get credentials from environment using configured variable names
            aws_access_key = os.getenv(self.config.aws_access_key_env)
            aws_secret_key = os.getenv(self.config.aws_secret_key_env)

            if not aws_access_key or not aws_secret_key:
                raise ValueError(
                    f"AWS credentials not found. Please set {self.config.aws_access_key_env} and "
                    f"{self.config.aws_secret_key_env} environment variables."
                )

            return boto3.client(
                'bedrock-runtime',
                region_name=self.config.region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        except Exception as e:
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"Failed to create Bedrock client: {e}")
            raise

    def _make_api_call(self, prompt: str) -> str:
        """
        Make Bedrock API call with retry logic and return the response text.

        Formats the request, calls invoke_model with exponential backoff,
        and extracts the text content from the Bedrock response format.

        Args:
            prompt: Analysis prompt for Claude

        Returns:
            str: Text content from the API response

        Raises:
            Exception: If all retry attempts fail
        """
        request_body = self._format_bedrock_request(prompt)
        response = self._make_api_call_with_retry(request_body)
        return self._extract_text_from_response(response)

    def _format_bedrock_request(self, prompt: str) -> Dict[str, Any]:
        """
        Format request for Bedrock API using current model configuration.

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

    def _make_api_call_with_retry(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API call with exponential backoff retry logic using configured parameters.

        Args:
            request_body: Formatted request for Bedrock

        Returns:
            Dict: API response from Bedrock

        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.client.invoke_model(
                    modelId=self.config.model_id,
                    body=json.dumps(request_body),
                    contentType='application/json',
                    accept='application/json'
                )

                return json.loads(response['body'].read())

            except ClientError as e:
                error_code = e.response['Error']['Code']

                if error_code == 'ThrottlingException':
                    self.stats.rate_limit_hits += 1
                    if attempt < self.config.max_retries:
                        wait_time = max(self.config.rate_limit_delay, (2 ** attempt) + 1)
                        self.logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                        time.sleep(wait_time)
                        continue

                self.logger.error(f"Bedrock API error: {error_code} - {e}")
                raise

            except BotoCoreError as e:
                if attempt < self.config.max_retries:
                    wait_time = (2 ** attempt) + 1
                    self.logger.warning(f"Network error, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                raise

            except Exception as e:
                self.logger.error(f"Unexpected error in API call: {e}")
                raise

        raise Exception(f"Failed to complete API call after {self.config.max_retries + 1} attempts")

    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """
        Extract text content from the Bedrock API response format.

        Args:
            response: Raw response dict from Bedrock API

        Returns:
            str: Text content from the response

        Raises:
            ValueError: If no text content is found
        """
        content = response.get('content', [])
        if not content:
            raise ValueError("No content in response")

        text_content = content[0].get('text', '')
        if not text_content:
            raise ValueError("No text content in response")

        return text_content

    def test_connection(self) -> bool:
        """
        Test the Bedrock connection with a simple API call.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Simple test prompt
            test_prompt = "Respond with valid JSON: {\"test\": \"success\"}"
            request_body = self._format_bedrock_request(test_prompt)

            # Add diagnostic logging
            self.logger.info(f"Testing Bedrock connection with model: {self.config.model_id}")
            self.logger.info(f"Region: {self.config.region}")
            self.logger.debug(f"Request body: {json.dumps(request_body, indent=2)}")

            response = self.client.invoke_model(
                modelId=self.config.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )

            # If we get here, the connection works
            self.logger.info("Bedrock connection test successful")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']

            self.logger.error(f"Bedrock connection test failed: {error_code} - {error_message}")

            # Provide specific guidance based on error type
            if error_code == 'ValidationException' and 'on-demand throughput' in error_message:
                self.logger.error("DIAGNOSIS: Model doesn't support on-demand throughput")
                self.logger.error("SOLUTION: Try using an inference profile or different model version")
                self.logger.error("Available alternatives:")
                self.logger.error("  - anthropic.claude-3-5-sonnet-20241022-v2:0")
                self.logger.error("  - anthropic.claude-3-sonnet-20240229-v1:0")
                self.logger.error("  - Use inference profile ARN instead of model ID")
            elif error_code == 'AccessDeniedException':
                self.logger.error("DIAGNOSIS: Access denied - check model permissions")
                self.logger.error("SOLUTION: Verify model access in AWS Bedrock console")
            elif error_code == 'ResourceNotFoundException':
                self.logger.error("DIAGNOSIS: Model not found in this region")
                self.logger.error(f"SOLUTION: Check if model {self.config.model_id} is available in {self.config.region}")

            return False

        except BotoCoreError as e:
            self.logger.error(f"Bedrock connection test failed (network/auth): {e}")
            self.logger.error("DIAGNOSIS: Network or authentication issue")
            self.logger.error("SOLUTION: Check AWS credentials and network connectivity")
            return False

        except Exception as e:
            self.logger.error(f"Bedrock connection test failed (unexpected): {e}")
            self.logger.error("DIAGNOSIS: Unexpected error occurred")
            return False

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider-specific configuration information.

        Returns:
            Dict[str, Any]: Bedrock-specific configuration information
                           including region and model_id
        """
        return {
            "provider": "bedrock",
            "region": self.config.region,
            "model_id": self.config.model_id
        }
