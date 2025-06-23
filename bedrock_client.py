#!/usr/bin/env python3
"""
Bedrock Client - Phase 8: Configuration Management & API Fallback

This module implements the AWS Bedrock Claude API client with configuration
management support, replacing the original LLMClient with enhanced configuration
and error handling capabilities.

Author: Work Journal Summarizer Project
Version: Phase 8 - Configuration Management & API Fallback
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import json
import time
import logging
import os
import re

from config_manager import BedrockConfig
from llm_data_structures import AnalysisResult, APIStats


class BedrockClient:
    """
    AWS Bedrock Claude API client with configuration management support.
    
    This client handles entity extraction from journal entries using Claude
    on AWS Bedrock, with comprehensive configuration management and error handling.
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

    def __init__(self, config: BedrockConfig):
        """
        Initialize Bedrock client with configuration.
        
        Args:
            config: Bedrock configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.stats = APIStats(0, 0, 0, 0.0, 0.0, 0)
        self.client = self._create_bedrock_client()
        
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
            self.logger.error(f"Failed to create Bedrock client: {e}")
            raise
            
    def analyze_content(self, content: str, file_path: Path) -> AnalysisResult:
        """
        Analyze journal content and extract entities using Claude on Bedrock.
        
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
        
        Returns provider-specific configuration details that are useful
        for debugging, logging, and displaying current settings.
        
        Returns:
            Dict[str, Any]: Bedrock-specific configuration information
                           including region and model_id
        """
        return {
            "provider": "bedrock",
            "region": self.config.region,
            "model_id": self.config.model_id
        }