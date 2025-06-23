#!/usr/bin/env python3
"""
Unified LLM Client - Multi-Provider LLM Interface

This module implements a unified interface that can switch between different LLM
providers (AWS Bedrock, Google GenAI) based on configuration. It provides a
transparent abstraction layer that allows the application to use different
LLM providers without changing the calling code.

Author: Work Journal Summarizer Project
Version: Multi-Provider Support
"""

from typing import Union, Dict, Any
from pathlib import Path
import logging

from config_manager import AppConfig
from bedrock_client import BedrockClient
from google_genai_client import GoogleGenAIClient
from llm_data_structures import AnalysisResult, APIStats


class UnifiedLLMClient:
    """
    Unified LLM client that can switch between different providers based on configuration.
    
    This client provides a transparent interface that delegates all calls to the
    appropriate underlying LLM client (BedrockClient or GoogleGenAIClient) based
    on the configured provider. The interface is identical to the individual clients,
    making it a drop-in replacement.
    
    Supported providers:
    - "bedrock": AWS Bedrock with Claude models
    - "google_genai": Google GenAI with Gemini models
    
    The client automatically creates and manages the underlying provider client
    based on the configuration, handling all provider-specific initialization
    and error handling.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the unified LLM client with the specified configuration.
        
        Args:
            config (AppConfig): Complete application configuration including
                               LLM provider selection and provider-specific configs
        
        Raises:
            ValueError: If an unsupported provider is specified in config.llm.provider
            Exception: If the underlying client fails to initialize
        """
        self.config = config
        self.provider_name = config.llm.provider
        self.logger = logging.getLogger(__name__)
        
        # Create the appropriate underlying client
        self.client = self._create_client()
        
        self.logger.info(f"UnifiedLLMClient initialized with provider: {self.provider_name}")
    
    def _create_client(self) -> Union[BedrockClient, GoogleGenAIClient]:
        """
        Create the appropriate LLM client based on the configured provider.
        
        Returns:
            Union[BedrockClient, GoogleGenAIClient]: The initialized client instance
        
        Raises:
            ValueError: If the provider is not supported
            Exception: If client initialization fails
        """
        try:
            if self.provider_name == "bedrock":
                self.logger.debug("Creating BedrockClient")
                return BedrockClient(self.config.bedrock)
            elif self.provider_name == "google_genai":
                self.logger.debug("Creating GoogleGenAIClient")
                return GoogleGenAIClient(self.config.google_genai)
            else:
                supported_providers = ["bedrock", "google_genai"]
                raise ValueError(
                    f"Unsupported LLM provider: '{self.provider_name}'. "
                    f"Supported providers: {supported_providers}"
                )
        except Exception as e:
            self.logger.error(f"Failed to create {self.provider_name} client: {e}")
            raise
    
    def analyze_content(self, content: str, file_path: Path) -> AnalysisResult:
        """
        Analyze journal content and extract structured information.
        
        This method delegates to the underlying provider client to perform
        content analysis and entity extraction from journal entries.
        
        Args:
            content (str): The journal content to analyze
            file_path (Path): Path to the source file being analyzed
        
        Returns:
            AnalysisResult: Structured analysis results containing extracted
                          projects, participants, tasks, themes, and metadata
        
        Raises:
            Exception: Any exceptions from the underlying provider client
        """
        self.logger.debug(f"Analyzing content using {self.provider_name} provider")
        return self.client.analyze_content(content, file_path)
    
    def get_stats(self) -> APIStats:
        """
        Get API usage statistics from the underlying client.
        
        Returns:
            APIStats: Statistics including call counts, timing, and error rates
        """
        return self.client.get_stats()
    
    def reset_stats(self) -> None:
        """
        Reset API usage statistics in the underlying client.
        
        This clears all accumulated statistics including call counts,
        timing information, and error counters.
        """
        self.logger.debug(f"Resetting stats for {self.provider_name} provider")
        self.client.reset_stats()
    
    def test_connection(self) -> bool:
        """
        Test connection to the configured LLM provider.
        
        This method attempts to make a simple test call to verify that
        the client can successfully connect to and communicate with the
        configured LLM provider.
        
        Returns:
            bool: True if connection test succeeds, False otherwise
        """
        self.logger.debug(f"Testing connection for {self.provider_name} provider")
        try:
            result = self.client.test_connection()
            if result:
                self.logger.info(f"Connection test successful for {self.provider_name}")
            else:
                self.logger.warning(f"Connection test failed for {self.provider_name}")
            return result
        except Exception as e:
            self.logger.error(f"Connection test error for {self.provider_name}: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """
        Get the name of the currently configured provider.
        
        Returns:
            str: The provider name ("bedrock" or "google_genai")
        """
        return self.provider_name
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider-specific configuration information.
        
        Returns provider-specific configuration details that are useful
        for debugging, logging, and displaying current settings.
        This method delegates to the underlying client's get_provider_info() method.
        
        Returns:
            Dict[str, Any]: Provider-specific configuration information
                           - For bedrock: provider, region, model_id
                           - For google_genai: provider, project, location, model
        """
        return self.client.get_provider_info()