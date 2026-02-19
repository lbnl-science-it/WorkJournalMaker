# ABOUTME: Multi-provider LLM interface with ordered fallback chain.
# ABOUTME: Delegates to Google GenAI, AWS Bedrock, or CBORG with lazy initialization and user-visible notifications.
"""
Unified LLM Client - Multi-Provider LLM Interface with Fallback

This module implements a unified interface that can switch between different LLM
providers (AWS Bedrock, Google GenAI, CBORG) based on configuration. When the
active provider fails, it falls back to the next provider in a configurable chain,
notifying the user on every transition.
"""

from typing import Union, Dict, Any, Optional, Callable, List
from pathlib import Path
import logging

from config_manager import AppConfig
from bedrock_client import BedrockClient
from google_genai_client import GoogleGenAIClient
from cborg_client import CBORGClient
from llm_data_structures import AnalysisResult, APIStats


class UnifiedLLMClient:
    """
    Unified LLM client with ordered provider fallback.

    Manages a chain of LLM providers (e.g. Google GenAI → Bedrock → CBORG).
    The primary provider is created at init time; fallback providers are created
    lazily only when needed. On every provider transition, a user-visible
    notification is emitted via the on_fallback callback.
    """

    SUPPORTED_PROVIDERS = ["bedrock", "google_genai", "cborg"]

    def __init__(self, config: AppConfig, on_fallback: Optional[Callable[[str], None]] = None):
        """
        Initialize the unified LLM client with provider fallback support.

        Args:
            config: Complete application configuration
            on_fallback: Callback invoked with a message string when switching
                        providers. Defaults to logging.warning.

        Raises:
            ValueError: If an unsupported provider is specified
            Exception: If the primary client fails to initialize
        """
        self.config = config
        self.provider_name = config.llm.provider
        self.logger = logging.getLogger(__name__)
        self.on_fallback = on_fallback or logging.warning

        # Build the ordered provider chain: [primary, fallback1, fallback2, ...]
        self._provider_chain: List[str] = [config.llm.provider] + list(
            config.llm.fallback_providers
        )

        # Cache for lazily initialized provider clients
        self._clients: Dict[str, Union[BedrockClient, GoogleGenAIClient, CBORGClient]] = {}

        # Create the primary client eagerly
        self.client = self._create_client_for_provider(config.llm.provider)
        self._clients[config.llm.provider] = self.client
        self.active_provider_name = config.llm.provider

        self.logger.info(f"UnifiedLLMClient initialized with provider: {self.provider_name}")

    def _create_client_for_provider(
        self, provider_name: str
    ) -> Union[BedrockClient, GoogleGenAIClient, CBORGClient]:
        """
        Create an LLM client for the given provider name.

        Args:
            provider_name: One of "bedrock", "google_genai", or "cborg"

        Returns:
            The initialized client instance

        Raises:
            ValueError: If the provider is not supported
            Exception: If client initialization fails
        """
        try:
            if provider_name == "bedrock":
                self.logger.debug("Creating BedrockClient")
                return BedrockClient(self.config.bedrock)
            elif provider_name == "google_genai":
                self.logger.debug("Creating GoogleGenAIClient")
                return GoogleGenAIClient(self.config.google_genai)
            elif provider_name == "cborg":
                self.logger.debug("Creating CBORGClient")
                return CBORGClient(self.config.cborg)
            else:
                raise ValueError(
                    f"Unsupported LLM provider: '{provider_name}'. "
                    f"Supported providers: {self.SUPPORTED_PROVIDERS}"
                )
        except Exception as e:
            self.logger.error(f"Failed to create {provider_name} client: {e}")
            raise

    def _get_or_create_client(
        self, provider_name: str
    ) -> Union[BedrockClient, GoogleGenAIClient, CBORGClient]:
        """
        Get a cached client or create a new one for the given provider.

        Args:
            provider_name: Provider to get or create a client for

        Returns:
            The client instance
        """
        if provider_name not in self._clients:
            self._clients[provider_name] = self._create_client_for_provider(provider_name)
        return self._clients[provider_name]

    def analyze_content(self, content: str, file_path: Path) -> AnalysisResult:
        """
        Analyze journal content, falling back to alternate providers on failure.

        Tries the active provider first. On failure, walks the remaining fallback
        chain, notifying the user at each transition. If all providers fail, the
        last exception is raised.

        Args:
            content: The journal content to analyze
            file_path: Path to the source file being analyzed

        Returns:
            AnalysisResult: Structured analysis results

        Raises:
            Exception: If all providers in the chain fail
        """
        last_exception: Optional[Exception] = None
        failed_provider: Optional[str] = None
        active_index = self._provider_chain.index(self.active_provider_name)

        for i in range(active_index, len(self._provider_chain)):
            provider_name = self._provider_chain[i]

            # Notify on transition from a previously failed provider
            if failed_provider is not None:
                self.on_fallback(
                    f"Provider '{failed_provider}' failed: {last_exception}. "
                    f"Falling back to '{provider_name}'."
                )

            try:
                client = self._get_or_create_client(provider_name)
            except Exception as init_err:
                self.logger.warning(
                    f"Failed to initialize fallback provider '{provider_name}': {init_err}"
                )
                failed_provider = provider_name
                last_exception = init_err
                continue

            try:
                self.logger.debug(f"Analyzing content using {provider_name} provider")
                result = client.analyze_content(content, file_path)
                self.active_provider_name = provider_name
                self.client = client
                return result
            except Exception as e:
                failed_provider = provider_name
                last_exception = e
                self.logger.warning(f"Provider '{provider_name}' failed: {e}")

        raise last_exception

    def get_stats(self) -> APIStats:
        """
        Get API usage statistics from the active client.

        Returns:
            APIStats: Statistics including call counts, timing, and error rates
        """
        return self.client.get_stats()

    def reset_stats(self) -> None:
        """
        Reset API usage statistics in the active client.
        """
        self.logger.debug(f"Resetting stats for {self.active_provider_name} provider")
        self.client.reset_stats()

    def test_connection(self) -> bool:
        """
        Test connection to the active provider, falling back on failure.

        Returns:
            bool: True if any provider in the chain connects successfully
        """
        self.logger.debug(f"Testing connection for {self.active_provider_name} provider")
        active_index = self._provider_chain.index(self.active_provider_name)

        for i in range(active_index, len(self._provider_chain)):
            provider_name = self._provider_chain[i]

            if i > active_index:
                self.on_fallback(
                    f"Provider '{self._provider_chain[i - 1]}' connection failed. "
                    f"Falling back to '{provider_name}'."
                )

            try:
                client = self._get_or_create_client(provider_name)
            except Exception as init_err:
                self.logger.warning(
                    f"Failed to initialize provider '{provider_name}': {init_err}"
                )
                continue

            try:
                result = client.test_connection()
                if result:
                    self.logger.info(f"Connection test successful for {provider_name}")
                    self.active_provider_name = provider_name
                    self.client = client
                    return True
                else:
                    self.logger.warning(f"Connection test failed for {provider_name}")
            except Exception as e:
                self.logger.error(f"Connection test error for {provider_name}: {e}")

        return False

    def get_provider_name(self) -> str:
        """
        Get the name of the currently active provider.

        Returns:
            str: The active provider name
        """
        return self.active_provider_name

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider configuration info including fallback chain.

        Returns:
            Dict[str, Any]: Active provider info plus fallback metadata
        """
        info = self.client.get_provider_info()
        info["active_provider"] = self.active_provider_name
        info["fallback_providers"] = list(self.config.llm.fallback_providers)
        return info
