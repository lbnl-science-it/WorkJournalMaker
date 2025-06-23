#!/usr/bin/env python3
"""
Tests for Updated Dry-Run Functionality

This module tests the updated _perform_dry_run function to ensure it properly
displays provider-specific information and tests connections for both AWS Bedrock
and Google GenAI providers.

Author: Work Journal Summarizer Project
Version: Multi-Provider Support
"""

import pytest
import argparse
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import date
import os
from io import StringIO
import sys

# Import the modules we need to test
from work_journal_summarizer import _perform_dry_run
from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig, ProcessingConfig
from logger import LogConfig, LogLevel, ErrorCategory
from logger import JournalSummarizerLogger
from unified_llm_client import UnifiedLLMClient
from llm_data_structures import APIStats


class TestDryRunFunctionality:
    """Test suite for the updated dry-run functionality."""
    
    @pytest.fixture
    def mock_args(self):
        """Create mock command line arguments for testing."""
        args = argparse.Namespace()
        args.start_date = date(2024, 1, 1)
        args.end_date = date(2024, 1, 7)
        args.summary_type = 'weekly'
        return args
    
    @pytest.fixture
    def bedrock_config(self):
        """Create a configuration with bedrock provider."""
        return AppConfig(
            bedrock=BedrockConfig(
                region="us-east-1",
                model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                aws_access_key_env="AWS_ACCESS_KEY_ID",
                aws_secret_key_env="AWS_SECRET_ACCESS_KEY"
            ),
            google_genai=GoogleGenAIConfig(),
            llm=LLMConfig(provider="bedrock"),
            processing=ProcessingConfig(
                base_path="~/test_journals",
                output_path="~/test_output",
                max_file_size_mb=10
            ),
            logging=LogConfig(level=LogLevel.INFO)
        )
    
    @pytest.fixture
    def google_genai_config(self):
        """Create a configuration with google_genai provider."""
        return AppConfig(
            bedrock=BedrockConfig(),
            google_genai=GoogleGenAIConfig(
                project="test-project-123",
                location="us-central1",
                model="gemini-2.0-flash-001"
            ),
            llm=LLMConfig(provider="google_genai"),
            processing=ProcessingConfig(
                base_path="~/test_journals",
                output_path="~/test_output",
                max_file_size_mb=10
            ),
            logging=LogConfig(level=LogLevel.INFO)
        )
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = Mock(spec=JournalSummarizerLogger)
        logger.error_reports = []
        logger.log_file_path = Path("/tmp/test.log")
        logger.log_error_with_category = Mock()
        return logger
    
    @pytest.fixture
    def mock_unified_client(self):
        """Create a mock unified LLM client."""
        client = Mock(spec=UnifiedLLMClient)
        client.get_provider_name = Mock()
        client.get_provider_info = Mock()
        client.test_connection = Mock()
        return client

    def capture_output(self, func, *args, **kwargs):
        """Capture stdout output from a function call."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        try:
            func(*args, **kwargs)
            return captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

    @patch('work_journal_summarizer.UnifiedLLMClient')
    @patch('os.getenv')
    def test_dry_run_with_bedrock_provider_success(self, mock_getenv, mock_client_class, 
                                                  mock_args, bedrock_config, mock_logger):
        """Test dry-run with bedrock provider and successful connection."""
        # Setup mocks
        mock_client = Mock()
        mock_client.get_provider_name.return_value = "bedrock"
        mock_client.get_provider_info.return_value = {
            "provider": "bedrock",
            "region": "us-east-1",
            "model_id": "anthropic.claude-3-sonnet-20240229-v1:0"
        }
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        # Mock AWS credentials found
        mock_getenv.side_effect = lambda key: "test_value" if key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"] else None
        
        # Mock path operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")):
            
            # Capture output
            output = self.capture_output(_perform_dry_run, mock_args, bedrock_config, mock_logger)
        
        # Verify output contains expected information
        assert "🤖 LLM Provider: bedrock" in output
        assert "📝 Provider: bedrock" in output
        assert "📝 Region: us-east-1" in output
        assert "📝 Model Id: anthropic.claude-3-sonnet-20240229-v1:0" in output
        assert "✅ AWS credentials found in environment" in output
        assert "✅ Bedrock API connection successful" in output
        
        # Verify client was created with correct config
        mock_client_class.assert_called_once_with(bedrock_config)
        mock_client.get_provider_name.assert_called_once()
        mock_client.get_provider_info.assert_called_once()
        mock_client.test_connection.assert_called_once()

    @patch('work_journal_summarizer.UnifiedLLMClient')
    @patch('os.getenv')
    def test_dry_run_with_google_genai_provider_success(self, mock_getenv, mock_client_class,
                                                       mock_args, google_genai_config, mock_logger):
        """Test dry-run with google_genai provider and successful connection."""
        # Setup mocks
        mock_client = Mock()
        mock_client.get_provider_name.return_value = "google_genai"
        mock_client.get_provider_info.return_value = {
            "provider": "google_genai",
            "project": "test-project-123",
            "location": "us-central1",
            "model": "gemini-2.0-flash-001"
        }
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        # Mock path operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")):
            
            # Capture output
            output = self.capture_output(_perform_dry_run, mock_args, google_genai_config, mock_logger)
        
        # Verify output contains expected information
        assert "🤖 LLM Provider: google_genai" in output
        assert "📝 Provider: google_genai" in output
        assert "📝 Project: test-project-123" in output
        assert "📝 Location: us-central1" in output
        assert "📝 Model: gemini-2.0-flash-001" in output
        assert "✅ Google GenAI provider configured" in output
        assert "✅ Google_Genai API connection successful" in output
        
        # Verify client was created with correct config
        mock_client_class.assert_called_once_with(google_genai_config)
        mock_client.get_provider_name.assert_called_once()
        mock_client.get_provider_info.assert_called_once()
        mock_client.test_connection.assert_called_once()

    @patch('work_journal_summarizer.UnifiedLLMClient')
    @patch('os.getenv')
    def test_dry_run_bedrock_missing_credentials(self, mock_getenv, mock_client_class,
                                               mock_args, bedrock_config, mock_logger):
        """Test dry-run with bedrock provider but missing AWS credentials."""
        # Setup mocks
        mock_client = Mock()
        mock_client.get_provider_name.return_value = "bedrock"
        mock_client.get_provider_info.return_value = {
            "provider": "bedrock",
            "region": "us-east-1",
            "model_id": "anthropic.claude-3-sonnet-20240229-v1:0"
        }
        mock_client.test_connection.return_value = False
        mock_client_class.return_value = mock_client
        
        # Mock missing AWS credentials
        mock_getenv.return_value = None
        
        # Mock path operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")):
            
            # Capture output
            output = self.capture_output(_perform_dry_run, mock_args, bedrock_config, mock_logger)
        
        # Verify output shows missing credentials
        assert "❌ AWS credentials not found" in output
        assert "❌ Bedrock API connection failed" in output
        
        # Verify error was logged
        mock_logger.log_error_with_category.assert_called()

    @patch('work_journal_summarizer.UnifiedLLMClient')
    def test_dry_run_connection_failure(self, mock_client_class, mock_args, bedrock_config, mock_logger):
        """Test dry-run when connection test fails."""
        # Setup mocks
        mock_client = Mock()
        mock_client.get_provider_name.return_value = "bedrock"
        mock_client.get_provider_info.return_value = {"provider": "bedrock", "region": "us-east-1"}
        mock_client.test_connection.return_value = False
        mock_client_class.return_value = mock_client
        
        # Mock path operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")), \
             patch('os.getenv', return_value="test_value"):
            
            # Capture output
            output = self.capture_output(_perform_dry_run, mock_args, bedrock_config, mock_logger)
        
        # Verify connection failure is reported
        assert "❌ Bedrock API connection failed" in output
        assert "💡 Check the log file for detailed error analysis and solutions" in output

    @patch('work_journal_summarizer.UnifiedLLMClient')
    def test_dry_run_client_creation_error(self, mock_client_class, mock_args, bedrock_config, mock_logger):
        """Test dry-run when UnifiedLLMClient creation fails."""
        # Setup mock to raise exception
        mock_client_class.side_effect = Exception("Invalid provider configuration")
        
        # Mock path operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")):
            
            # Capture output
            output = self.capture_output(_perform_dry_run, mock_args, bedrock_config, mock_logger)
        
        # Verify error handling
        assert "LLM connection test failed: Invalid provider configuration" in output
        assert "❌ LLM API connection failed" in output
        
        # Verify error was logged
        mock_logger.log_error_with_category.assert_called()

    @patch('work_journal_summarizer.UnifiedLLMClient')
    def test_dry_run_provider_info_display_formatting(self, mock_client_class, mock_args, bedrock_config, mock_logger):
        """Test that provider information is displayed with proper formatting."""
        # Setup mocks with various key formats
        mock_client = Mock()
        mock_client.get_provider_name.return_value = "bedrock"
        mock_client.get_provider_info.return_value = {
            "provider": "bedrock",
            "aws_region": "us-east-1",
            "model_id": "test-model",
            "max_tokens": 4096
        }
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        # Mock path operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")), \
             patch('os.getenv', return_value="test_value"):
            
            # Capture output
            output = self.capture_output(_perform_dry_run, mock_args, bedrock_config, mock_logger)
        
        # Verify formatting of different key types
        assert "📝 Provider: bedrock" in output
        assert "📝 Aws Region: us-east-1" in output  # underscore replaced with space and title case
        assert "📝 Model Id: test-model" in output
        assert "📝 Max Tokens: 4096" in output

    def test_dry_run_date_range_validation(self, mock_args, bedrock_config, mock_logger):
        """Test that date range validation works correctly."""
        # Test weekly summary calculation
        mock_args.summary_type = 'weekly'
        mock_args.start_date = date(2024, 1, 1)
        mock_args.end_date = date(2024, 1, 14)  # 14 days = 2 weeks
        
        with patch('work_journal_summarizer.UnifiedLLMClient'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")):
            
            output = self.capture_output(_perform_dry_run, mock_args, bedrock_config, mock_logger)
        
        assert "✅ Date range valid: 2024-01-01 to 2024-01-14 (14 days)" in output
        assert "📊 Estimated weekly summaries: 2" in output

    def test_dry_run_monthly_summary_calculation(self, mock_args, bedrock_config, mock_logger):
        """Test monthly summary calculation."""
        # Test monthly summary calculation
        mock_args.summary_type = 'monthly'
        mock_args.start_date = date(2024, 1, 1)
        mock_args.end_date = date(2024, 3, 31)  # 3 months
        
        with patch('work_journal_summarizer.UnifiedLLMClient'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")):
            
            output = self.capture_output(_perform_dry_run, mock_args, bedrock_config, mock_logger)
        
        assert "📊 Estimated monthly summaries: 3" in output

    def test_dry_run_path_validation_errors(self, mock_args, bedrock_config, mock_logger):
        """Test handling of path validation errors."""
        with patch('work_journal_summarizer.UnifiedLLMClient'), \
             patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")):
            
            output = self.capture_output(_perform_dry_run, mock_args, bedrock_config, mock_logger)
        
        # Verify path errors are reported
        assert "❌ Base path not found:" in output
        assert "❌ Output path not accessible:" in output
        
        # Verify errors were logged
        assert mock_logger.log_error_with_category.call_count >= 2

    def test_dry_run_error_report_summary(self, mock_args, bedrock_config, mock_logger):
        """Test that error reports are displayed at the end."""
        # Setup mock error reports
        mock_error_report = Mock()
        mock_error_report.message = "Test error message"
        mock_error_report.recovery_action = "Test recovery action"
        mock_logger.error_reports = [mock_error_report]
        
        with patch('work_journal_summarizer.UnifiedLLMClient'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")):
            
            output = self.capture_output(_perform_dry_run, mock_args, bedrock_config, mock_logger)
        
        # Verify error summary is displayed
        assert "⚠️  Found 1 configuration issues:" in output
        assert "- Test error message" in output
        assert "Recovery: Test recovery action" in output

    @patch('work_journal_summarizer.UnifiedLLMClient')
    def test_dry_run_configuration_summary(self, mock_client_class, mock_args, bedrock_config, mock_logger):
        """Test that configuration summary is displayed correctly."""
        # Setup basic mocks
        mock_client = Mock()
        mock_client.get_provider_name.return_value = "bedrock"
        mock_client.get_provider_info.return_value = {"provider": "bedrock"}
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.object(Path, 'expanduser', return_value=Path("/expanded/test_journals")), \
             patch('os.getenv', return_value="test_value"):
            
            output = self.capture_output(_perform_dry_run, mock_args, bedrock_config, mock_logger)
        
        # Verify configuration summary
        assert "📁 Max file size: 10 MB" in output
        assert "📝 Log level: INFO" in output
        assert "📁 Log directory:" in output
        assert "📄 Log file: test.log" in output
        assert "🎯 Dry run complete - configuration validated" in output


if __name__ == "__main__":
    pytest.main([__file__])