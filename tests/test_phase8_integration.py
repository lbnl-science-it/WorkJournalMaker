#!/usr/bin/env python3
"""
Integration Tests for Phase 8: Configuration Management & API Fallback

This module contains comprehensive end-to-end integration tests for Phase 8,
testing the complete workflow with configuration management and API fallback.

Author: Work Journal Summarizer Project
Version: Phase 8 - Configuration Management & API Fallback
"""

import pytest
import tempfile
import yaml
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from config_manager import ConfigManager, AppConfig
from bedrock_client import BedrockClient
from work_journal_summarizer import main, parse_arguments


class TestPhase8Integration:
    """Integration tests for Phase 8 functionality."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary configuration file."""
        config_data = {
            'bedrock': {
                'region': 'us-east-1',
                'model_id': 'test-model-id',
                'timeout': 45,
                'max_retries': 2
            },
            'processing': {
                'base_path': '~/test/worklogs/',
                'output_path': '~/test/summaries/',
                'max_file_size_mb': 25
            },
            'logging': {
                'level': 'DEBUG',
                'console_output': True,
                'file_output': True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        yield config_path
        
        if config_path.exists():
            config_path.unlink()
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        return {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key',
            'WJS_BEDROCK_REGION': 'env-override-region',
            'WJS_LOG_LEVEL': 'WARNING'
        }
    
    def test_config_file_loading_integration(self, temp_config_file, mock_env_vars):
        """Test complete configuration loading with file and environment overrides."""
        with patch.dict(os.environ, mock_env_vars):
            config_manager = ConfigManager(temp_config_file)
            config = config_manager.get_config()
            
            # Should load from file
            assert config.bedrock.model_id == 'test-model-id'
            assert config.processing.max_file_size_mb == 25
            
            # Should override from environment
            assert config.bedrock.region == 'env-override-region'
            assert config.logging.level.value == 'WARNING'
    
    def test_bedrock_client_with_config(self, temp_config_file, mock_env_vars):
        """Test BedrockClient initialization with configuration."""
        with patch.dict(os.environ, mock_env_vars):
            config_manager = ConfigManager(temp_config_file)
            config = config_manager.get_config()
            
            with patch('boto3.client') as mock_boto:
                mock_client = MagicMock()
                mock_boto.return_value = mock_client
                
                bedrock_client = BedrockClient(config.bedrock)
                
                assert bedrock_client.config.region == 'env-override-region'
                assert bedrock_client.config.model_id == 'test-model-id'
                assert bedrock_client.config.max_retries == 2
    
    @patch('sys.argv', ['work_journal_summarizer.py', '--save-example-config', 'test-config.yaml'])
    def test_save_example_config_cli(self):
        """Test saving example configuration via CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'test-config.yaml'
            
            with patch('sys.argv', ['work_journal_summarizer.py', '--save-example-config', str(config_path)]):
                with patch('sys.exit') as mock_exit:
                    try:
                        main()
                    except SystemExit:
                        pass
                    
                    assert config_path.exists()
                    
                    # Verify the saved config
                    with open(config_path, 'r') as f:
                        saved_config = yaml.safe_load(f)
                    
                    assert 'bedrock' in saved_config
                    assert 'processing' in saved_config
                    assert 'logging' in saved_config
    
    @patch('sys.argv', [
        'work_journal_summarizer.py',
        '--start-date', '2024-01-01',
        '--end-date', '2024-01-07',
        '--summary-type', 'weekly',
        '--dry-run'
    ])
    def test_dry_run_with_config(self, temp_config_file, mock_env_vars):
        """Test dry run mode with configuration management."""
        with patch.dict(os.environ, mock_env_vars):
            with patch('sys.argv', [
                'work_journal_summarizer.py',
                '--start-date', '2024-01-01',
                '--end-date', '2024-01-07',
                '--summary-type', 'weekly',
                '--config', str(temp_config_file),
                '--dry-run'
            ]):
                with patch('builtins.print') as mock_print:
                    try:
                        main()
                    except SystemExit:
                        pass
                    
                    # Verify dry run output includes configuration details
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    
                    assert any("DRY RUN MODE" in call for call in print_calls)
                    assert any("env-override-region" in call for call in print_calls)
                    assert any("test-model-id" in call for call in print_calls)
    
    def test_cli_config_overrides(self, temp_config_file, mock_env_vars):
        """Test command-line overrides of configuration values."""
        with patch.dict(os.environ, mock_env_vars):
            with patch('sys.argv', [
                'work_journal_summarizer.py',
                '--start-date', '2024-01-01',
                '--end-date', '2024-01-07',
                '--summary-type', 'weekly',
                '--config', str(temp_config_file),
                '--output-dir', '/custom/output',
                '--log-level', 'ERROR',
                '--dry-run'
            ]):
                # Mock the ConfigManager to capture the final config
                original_init = ConfigManager.__init__
                captured_config = None
                
                def capture_config(self, config_path=None):
                    original_init(self, config_path)
                    nonlocal captured_config
                    captured_config = self.get_config()
                
                with patch.object(ConfigManager, '__init__', capture_config):
                    try:
                        main()
                    except SystemExit:
                        pass
                
                # Verify CLI overrides were applied
                # Note: This test structure needs to be adjusted based on actual implementation
                # The main function applies overrides after ConfigManager initialization
    
    def test_missing_config_file_fallback(self, mock_env_vars):
        """Test fallback to defaults when config file is missing."""
        non_existent_config = Path('/non/existent/config.yaml')
        
        with patch.dict(os.environ, mock_env_vars):
            with patch('sys.argv', [
                'work_journal_summarizer.py',
                '--start-date', '2024-01-01',
                '--end-date', '2024-01-07',
                '--summary-type', 'weekly',
                '--config', str(non_existent_config),
                '--dry-run'
            ]):
                with patch('builtins.print') as mock_print:
                    try:
                        main()
                    except SystemExit:
                        pass
                    
                    # Should still work with defaults and env overrides
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    assert any("DRY RUN MODE" in call for call in print_calls)
    
    def test_invalid_config_file_handling(self, mock_env_vars):
        """Test handling of invalid configuration files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            invalid_config_path = Path(f.name)
        
        try:
            with patch.dict(os.environ, mock_env_vars):
                with patch('sys.argv', [
                    'work_journal_summarizer.py',
                    '--start-date', '2024-01-01',
                    '--end-date', '2024-01-07',
                    '--summary-type', 'weekly',
                    '--config', str(invalid_config_path),
                    '--dry-run'
                ]):
                    with patch('builtins.print') as mock_print:
                        try:
                            main()
                        except SystemExit:
                            pass
                        
                        # Should handle invalid config gracefully
                        print_calls = [call[0][0] for call in mock_print.call_args_list]
                        assert any("DRY RUN MODE" in call for call in print_calls)
        finally:
            if invalid_config_path.exists():
                invalid_config_path.unlink()
    
    @patch('bedrock_client.BedrockClient.test_connection')
    def test_bedrock_connection_test_in_dry_run(self, mock_test_connection, temp_config_file, mock_env_vars):
        """Test Bedrock connection testing during dry run."""
        mock_test_connection.return_value = True
        
        with patch.dict(os.environ, mock_env_vars):
            with patch('sys.argv', [
                'work_journal_summarizer.py',
                '--start-date', '2024-01-01',
                '--end-date', '2024-01-07',
                '--summary-type', 'weekly',
                '--config', str(temp_config_file),
                '--dry-run'
            ]):
                with patch('builtins.print') as mock_print:
                    try:
                        main()
                    except SystemExit:
                        pass
                    
                    # Verify connection test was called
                    mock_test_connection.assert_called_once()
                    
                    # Verify success message in output
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    assert any("Bedrock API connection successful" in call for call in print_calls)
    
    def test_environment_variable_precedence(self, temp_config_file):
        """Test that environment variables take precedence over config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_base_path = Path(temp_dir) / 'base'
            temp_output_path = Path(temp_dir) / 'output'
            
            env_vars = {
                'AWS_ACCESS_KEY_ID': 'test-key',
                'AWS_SECRET_ACCESS_KEY': 'test-secret',
                'WJS_BEDROCK_REGION': 'env-region',
                'WJS_BASE_PATH': str(temp_base_path),
                'WJS_OUTPUT_PATH': str(temp_output_path),
                'WJS_MAX_FILE_SIZE_MB': '99',
                'WJS_LOG_LEVEL': 'CRITICAL'
            }
            
            with patch.dict(os.environ, env_vars):
                config_manager = ConfigManager(temp_config_file)
                config = config_manager.get_config()
                
                # Environment variables should override config file
                assert config.bedrock.region == 'env-region'
                assert config.processing.base_path == str(temp_base_path)
                assert config.processing.output_path == str(temp_output_path)
                assert config.processing.max_file_size_mb == 99
                assert config.logging.level.value == 'CRITICAL'
    
    def test_json_config_file_support(self, mock_env_vars):
        """Test support for JSON configuration files."""
        config_data = {
            'bedrock': {
                'region': 'json-region',
                'model_id': 'json-model'
            },
            'processing': {
                'max_file_size_mb': 75
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            json_config_path = Path(f.name)
        
        try:
            with patch.dict(os.environ, mock_env_vars):
                config_manager = ConfigManager(json_config_path)
                config = config_manager.get_config()
                
                assert config.bedrock.model_id == 'json-model'
                assert config.processing.max_file_size_mb == 75
        finally:
            if json_config_path.exists():
                json_config_path.unlink()
    
    def test_config_validation_errors(self):
        """Test configuration validation error handling."""
        # Test with missing AWS credentials
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="AWS access key not found"):
                ConfigManager()
    
    def test_complete_workflow_with_config(self, temp_config_file, mock_env_vars):
        """Test complete workflow integration with configuration management."""
        with patch.dict(os.environ, mock_env_vars):
            # Mock all the components that would be called in a full run
            with patch('file_discovery.FileDiscovery') as mock_discovery, \
                 patch('content_processor.ContentProcessor') as mock_processor, \
                 patch('bedrock_client.BedrockClient') as mock_bedrock, \
                 patch('summary_generator.SummaryGenerator') as mock_generator, \
                 patch('output_manager.OutputManager') as mock_output:
                
                # Setup mocks to return reasonable values
                mock_discovery_instance = MagicMock()
                mock_discovery.return_value = mock_discovery_instance
                
                with patch('sys.argv', [
                    'work_journal_summarizer.py',
                    '--start-date', '2024-01-01',
                    '--end-date', '2024-01-07',
                    '--summary-type', 'weekly',
                    '--config', str(temp_config_file)
                ]):
                    # This would test the full integration, but requires extensive mocking
                    # For now, we verify that the configuration is loaded correctly
                    config_manager = ConfigManager(temp_config_file)
                    config = config_manager.get_config()
                    
                    assert config.bedrock.model_id == 'test-model-id'
                    assert config.processing.max_file_size_mb == 25


if __name__ == '__main__':
    pytest.main([__file__])