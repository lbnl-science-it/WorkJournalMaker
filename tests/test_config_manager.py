#!/usr/bin/env python3
"""
Tests for Configuration Manager - Phase 8: Configuration Management & API Fallback

This module contains comprehensive tests for the configuration management system,
including file loading, environment variable overrides, validation, and error handling.

Author: Work Journal Summarizer Project
Version: Phase 8 - Configuration Management & API Fallback
"""

import pytest
import tempfile
import os
import yaml
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from config_manager import ConfigManager, AppConfig, BedrockConfig, ProcessingConfig
from logger import LogConfig, LogLevel


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def test_default_configuration(self):
        """Test that default configuration is created when no config file exists."""
        with patch.object(ConfigManager, '_find_config_file', return_value=None):
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            assert isinstance(config, AppConfig)
            assert isinstance(config.bedrock, BedrockConfig)
            assert isinstance(config.processing, ProcessingConfig)
            assert isinstance(config.logging, LogConfig)
            
            # Check default values
            assert config.bedrock.region == "us-east-2"
            assert config.bedrock.model_id == "anthropic.claude-sonnet-4-20250514-v1:0"
            assert config.processing.base_path == "~/Desktop/worklogs/"
            assert config.processing.max_file_size_mb == 50
    
    def test_yaml_config_loading(self):
        """Test loading configuration from YAML file."""
        yaml_config = {
            'bedrock': {
                'region': 'us-west-1',
                'model_id': 'test-model',
                'timeout': 60
            },
            'processing': {
                'base_path': '/custom/path',
                'max_file_size_mb': 100
            },
            'logging': {
                'level': 'DEBUG',
                'console_output': False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_config, f)
            config_path = Path(f.name)
        
        try:
            config_manager = ConfigManager(config_path)
            config = config_manager.get_config()
            
            assert config.bedrock.region == 'us-west-1'
            assert config.bedrock.model_id == 'test-model'
            assert config.bedrock.timeout == 60
            assert config.processing.base_path == '/custom/path'
            assert config.processing.max_file_size_mb == 100
            assert config.logging.level == LogLevel.DEBUG
            assert config.logging.console_output == False
        finally:
            config_path.unlink()
    
    def test_json_config_loading(self):
        """Test loading configuration from JSON file."""
        json_config = {
            'bedrock': {
                'region': 'eu-west-1',
                'max_retries': 5
            },
            'processing': {
                'batch_size': 20
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_config, f)
            config_path = Path(f.name)
        
        try:
            config_manager = ConfigManager(config_path)
            config = config_manager.get_config()
            
            assert config.bedrock.region == 'eu-west-1'
            assert config.bedrock.max_retries == 5
            assert config.processing.batch_size == 20
        finally:
            config_path.unlink()
    
    def test_environment_variable_overrides(self):
        """Test that environment variables override configuration values."""
        env_vars = {
            'WJS_BEDROCK_REGION': 'ap-southeast-1',
            'WJS_BASE_PATH': '/env/override/path',
            'WJS_MAX_FILE_SIZE_MB': '75',
            'WJS_LOG_LEVEL': 'WARNING'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch.object(ConfigManager, '_find_config_file', return_value=None):
                config_manager = ConfigManager()
                config = config_manager.get_config()
                
                assert config.bedrock.region == 'ap-southeast-1'
                assert config.processing.base_path == '/env/override/path'
                assert config.processing.max_file_size_mb == 75
                assert config.logging.level == LogLevel.WARNING
    
    def test_config_file_not_found(self):
        """Test handling of missing configuration file."""
        non_existent_path = Path('/non/existent/config.yaml')
        
        # Should not raise exception, should use defaults
        with patch.object(ConfigManager, '_find_config_file', return_value=None):
            config_manager = ConfigManager(non_existent_path)
            config = config_manager.get_config()
            
            # Should have default values
            assert config.bedrock.region == "us-east-2"
    
    def test_invalid_yaml_file(self):
        """Test handling of invalid YAML configuration file."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            config_path = Path(f.name)
        
        try:
            # Should not raise exception, should use defaults
            config_manager = ConfigManager(config_path)
            config = config_manager.get_config()
            
            # Should have default values despite invalid file
            assert config.bedrock.region == "us-east-2"
        finally:
            config_path.unlink()
    
    def test_invalid_json_file(self):
        """Test handling of invalid JSON configuration file."""
        invalid_json = '{"invalid": json, "missing": quote}'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(invalid_json)
            config_path = Path(f.name)
        
        try:
            # Should not raise exception, should use defaults
            config_manager = ConfigManager(config_path)
            config = config_manager.get_config()
            
            # Should have default values despite invalid file
            assert config.bedrock.region == "us-east-2"
        finally:
            config_path.unlink()
    
    def test_unsupported_file_format(self):
        """Test handling of unsupported configuration file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some content")
            config_path = Path(f.name)
        
        try:
            # Should not raise exception, should use defaults
            config_manager = ConfigManager(config_path)
            config = config_manager.get_config()
            
            # Should have default values
            assert config.bedrock.region == "us-east-2"
        finally:
            config_path.unlink()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_aws_credentials_validation(self):
        """Test validation fails when AWS credentials are missing."""
        with patch.object(ConfigManager, '_find_config_file', return_value=None):
            with pytest.raises(ValueError, match="AWS access key not found"):
                ConfigManager()
    
    @patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test-key'}, clear=True)
    def test_missing_aws_secret_validation(self):
        """Test validation fails when AWS secret key is missing."""
        with patch.object(ConfigManager, '_find_config_file', return_value=None):
            with pytest.raises(ValueError, match="AWS secret key not found"):
                ConfigManager()
    
    @patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret'
    })
    def test_valid_aws_credentials(self):
        """Test successful validation with valid AWS credentials."""
        with patch.object(ConfigManager, '_find_config_file', return_value=None):
            # Should not raise exception
            config_manager = ConfigManager()
            config = config_manager.get_config()
            assert config is not None
    
    def test_invalid_numeric_values(self):
        """Test validation of invalid numeric configuration values."""
        yaml_config = {
            'processing': {
                'max_file_size_mb': -10  # Invalid negative value
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_config, f)
            config_path = Path(f.name)
        
        try:
            with patch.dict(os.environ, {
                'AWS_ACCESS_KEY_ID': 'test-key',
                'AWS_SECRET_ACCESS_KEY': 'test-secret'
            }):
                with pytest.raises(ValueError, match="max_file_size_mb must be positive"):
                    ConfigManager(config_path)
        finally:
            config_path.unlink()
    
    def test_save_example_config_yaml(self):
        """Test saving example configuration as YAML."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            config_path = Path(f.name)
        
        try:
            config_manager = ConfigManager()
            config_manager.save_example_config(config_path)
            
            assert config_path.exists()
            
            # Load and verify the saved config
            with open(config_path, 'r') as f:
                saved_config = yaml.safe_load(f)
            
            assert 'bedrock' in saved_config
            assert 'processing' in saved_config
            assert 'logging' in saved_config
            assert saved_config['bedrock']['region'] == 'us-east-2'
        finally:
            if config_path.exists():
                config_path.unlink()
    
    def test_save_example_config_json(self):
        """Test saving example configuration as JSON."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            config_path = Path(f.name)
        
        try:
            config_manager = ConfigManager()
            config_manager.save_example_config(config_path)
            
            assert config_path.exists()
            
            # Load and verify the saved config
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
            
            assert 'bedrock' in saved_config
            assert 'processing' in saved_config
            assert 'logging' in saved_config
            assert saved_config['bedrock']['model_id'] == 'anthropic.claude-sonnet-4-20250514-v1:0'
        finally:
            if config_path.exists():
                config_path.unlink()
    
    def test_config_file_discovery(self):
        """Test automatic discovery of configuration files."""
        # Test with a temporary config file in current directory
        config_content = {'bedrock': {'region': 'discovered-region'}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, dir='.') as f:
            yaml.dump(config_content, f)
            config_path = Path(f.name)
        
        try:
            # Mock the CONFIG_LOCATIONS to include our temp file
            with patch.object(ConfigManager, 'CONFIG_LOCATIONS', [config_path]):
                with patch.dict(os.environ, {
                    'AWS_ACCESS_KEY_ID': 'test-key',
                    'AWS_SECRET_ACCESS_KEY': 'test-secret'
                }):
                    config_manager = ConfigManager()
                    config = config_manager.get_config()
                    
                    assert config.bedrock.region == 'discovered-region'
        finally:
            if config_path.exists():
                config_path.unlink()
    
    @patch('builtins.print')
    def test_print_config_summary(self, mock_print):
        """Test configuration summary printing."""
        with patch.object(ConfigManager, '_find_config_file', return_value=None):
            with patch.dict(os.environ, {
                'AWS_ACCESS_KEY_ID': 'test-key',
                'AWS_SECRET_ACCESS_KEY': 'test-secret'
            }):
                config_manager = ConfigManager()
                config_manager.print_config_summary()
                
                # Verify print was called with configuration details
                mock_print.assert_called()
                print_calls = []
                for call in mock_print.call_args_list:
                    if call[0]:  # Check if args exist
                        print_calls.append(call[0][0])
                
                assert any("Configuration Summary" in call for call in print_calls)
                assert any("us-east-2" in call for call in print_calls)
    
    def test_partial_configuration_merge(self):
        """Test that partial configuration files merge with defaults properly."""
        partial_config = {
            'bedrock': {
                'region': 'custom-region'
                # Missing other bedrock settings
            }
            # Missing processing and logging sections
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(partial_config, f)
            config_path = Path(f.name)
        
        try:
            with patch.dict(os.environ, {
                'AWS_ACCESS_KEY_ID': 'test-key',
                'AWS_SECRET_ACCESS_KEY': 'test-secret'
            }):
                config_manager = ConfigManager(config_path)
                config = config_manager.get_config()
                
                # Should have custom region
                assert config.bedrock.region == 'custom-region'
                
                # Should have default values for missing settings
                assert config.bedrock.model_id == "anthropic.claude-sonnet-4-20250514-v1:0"
                assert config.processing.base_path == "~/Desktop/worklogs/"
                assert config.logging.level == LogLevel.INFO
        finally:
            config_path.unlink()


if __name__ == '__main__':
    pytest.main([__file__])