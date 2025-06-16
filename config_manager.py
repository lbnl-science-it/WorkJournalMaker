#!/usr/bin/env python3
"""
Configuration Manager - Phase 8: Configuration Management & API Fallback

This module implements comprehensive configuration management for the Work Journal
Summarizer with support for YAML/JSON config files, environment variable overrides,
and validation of all configuration parameters.

Author: Work Journal Summarizer Project
Version: Phase 8 - Configuration Management & API Fallback
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml
import json
import os
from enum import Enum

# Import logger components for configuration
from logger import LogConfig, LogLevel


@dataclass
class BedrockConfig:
    """Configuration for AWS Bedrock API integration."""
    region: str = "us-east-2"
    model_id: str = "anthropic.claude-sonnet-4-20250514-v1:0"
    aws_access_key_env: str = "AWS_ACCESS_KEY_ID"
    aws_secret_key_env: str = "AWS_SECRET_ACCESS_KEY"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0


@dataclass
class ProcessingConfig:
    """Configuration for file processing and content handling."""
    base_path: str = "~/Desktop/worklogs/"
    output_path: str = "~/Desktop/worklogs/summaries/"
    max_file_size_mb: int = 50
    batch_size: int = 10
    rate_limit_delay: float = 1.0


@dataclass
class AppConfig:
    """Complete application configuration."""
    bedrock: BedrockConfig = field(default_factory=BedrockConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LogConfig = field(default_factory=LogConfig)


class ConfigManager:
    """
    Configuration manager for the Work Journal Summarizer.
    
    Handles loading configuration from files, environment variables,
    and command-line overrides with comprehensive validation.
    """
    
    # Standard configuration file locations
    CONFIG_LOCATIONS = [
        Path("./config.yaml"),
        Path("./config.yml"),
        Path("./config.json"),
        Path("~/.config/work-journal-summarizer/config.yaml"),
        Path("~/.config/work-journal-summarizer/config.yml"),
        Path("~/.config/work-journal-summarizer/config.json"),
    ]
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional explicit path to configuration file
        """
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self._validate_config(self.config)
        
    def _find_config_file(self) -> Optional[Path]:
        """
        Find configuration file in standard locations.
        
        Returns:
            Optional[Path]: Path to found config file, None if not found
        """
        for location in self.CONFIG_LOCATIONS:
            expanded_path = location.expanduser()
            if expanded_path.exists() and expanded_path.is_file():
                return expanded_path
        return None
    
    def _load_config(self) -> AppConfig:
        """
        Load configuration from file with fallback to defaults.
        
        Returns:
            AppConfig: Loaded configuration with defaults applied
        """
        # Start with default configuration
        config_dict = {}
        
        # Load from file if available
        if self.config_path:
            try:
                config_dict = self._load_config_file(self.config_path)
            except Exception as e:
                print(f"Warning: Failed to load config file {self.config_path}: {e}")
                print("Using default configuration...")
        
        # Apply environment variable overrides
        config_dict = self._apply_env_overrides(config_dict)
        
        # Convert to AppConfig object
        return self._dict_to_config(config_dict)
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """
        Load configuration from YAML or JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dict[str, Any]: Loaded configuration dictionary
            
        Raises:
            ValueError: If file format is unsupported
            FileNotFoundError: If file doesn't exist
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f) or {}
            elif config_path.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
    
    def _apply_env_overrides(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Args:
            config_dict: Base configuration dictionary
            
        Returns:
            Dict[str, Any]: Configuration with environment overrides applied
        """
        # Environment variable mappings
        env_mappings = {
            'WJS_BEDROCK_REGION': ['bedrock', 'region'],
            'WJS_BEDROCK_MODEL_ID': ['bedrock', 'model_id'],
            'WJS_BASE_PATH': ['processing', 'base_path'],
            'WJS_OUTPUT_PATH': ['processing', 'output_path'],
            'WJS_MAX_FILE_SIZE_MB': ['processing', 'max_file_size_mb'],
            'WJS_LOG_LEVEL': ['logging', 'level'],
            'WJS_LOG_DIR': ['logging', 'log_dir'],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Navigate to the nested dictionary location
                current = config_dict
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Convert value to appropriate type
                final_key = config_path[-1]
                if final_key == 'max_file_size_mb':
                    current[final_key] = int(value)
                elif final_key == 'level':
                    current[final_key] = value.upper()
                else:
                    current[final_key] = value
        
        return config_dict
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> AppConfig:
        """
        Convert configuration dictionary to AppConfig object.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            AppConfig: Structured configuration object
        """
        # Extract bedrock configuration
        bedrock_dict = config_dict.get('bedrock', {})
        bedrock_config = BedrockConfig(
            region=bedrock_dict.get('region', BedrockConfig.region),
            model_id=bedrock_dict.get('model_id', BedrockConfig.model_id),
            aws_access_key_env=bedrock_dict.get('aws_access_key_env', BedrockConfig.aws_access_key_env),
            aws_secret_key_env=bedrock_dict.get('aws_secret_key_env', BedrockConfig.aws_secret_key_env),
            timeout=bedrock_dict.get('timeout', BedrockConfig.timeout),
            max_retries=bedrock_dict.get('max_retries', BedrockConfig.max_retries),
            rate_limit_delay=bedrock_dict.get('rate_limit_delay', BedrockConfig.rate_limit_delay)
        )
        
        # Extract processing configuration
        processing_dict = config_dict.get('processing', {})
        processing_config = ProcessingConfig(
            base_path=processing_dict.get('base_path', ProcessingConfig.base_path),
            output_path=processing_dict.get('output_path', ProcessingConfig.output_path),
            max_file_size_mb=processing_dict.get('max_file_size_mb', ProcessingConfig.max_file_size_mb),
            batch_size=processing_dict.get('batch_size', ProcessingConfig.batch_size),
            rate_limit_delay=processing_dict.get('rate_limit_delay', ProcessingConfig.rate_limit_delay)
        )
        
        # Extract logging configuration
        logging_dict = config_dict.get('logging', {})
        
        # Convert string log level to LogLevel enum
        log_level_str = logging_dict.get('level', 'INFO')
        try:
            log_level = LogLevel(log_level_str.upper())
        except ValueError:
            log_level = LogLevel.INFO
        
        logging_config = LogConfig(
            level=log_level,
            console_output=logging_dict.get('console_output', LogConfig.console_output),
            file_output=logging_dict.get('file_output', LogConfig.file_output),
            log_dir=logging_dict.get('log_dir', LogConfig.log_dir),
            include_timestamps=logging_dict.get('include_timestamps', LogConfig.include_timestamps),
            include_module_names=logging_dict.get('include_module_names', LogConfig.include_module_names),
            max_file_size_mb=logging_dict.get('max_file_size_mb', LogConfig.max_file_size_mb),
            backup_count=logging_dict.get('backup_count', LogConfig.backup_count)
        )
        
        return AppConfig(
            bedrock=bedrock_config,
            processing=processing_config,
            logging=logging_config
        )
    
    def _validate_config(self, config: AppConfig) -> None:
        """
        Validate configuration and check environment variables.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate paths exist or can be created
        base_path = Path(config.processing.base_path).expanduser()
        output_path = Path(config.processing.output_path).expanduser()
        
        # Check base path accessibility (don't create it)
        if not base_path.exists():
            print(f"Warning: Base path does not exist: {base_path}")
        
        # Ensure output directory can be created
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Cannot create output directory {output_path}: {e}")
        
        # Validate numeric values
        if config.processing.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        
        if config.bedrock.timeout <= 0:
            raise ValueError("bedrock timeout must be positive")
        
        if config.bedrock.max_retries < 0:
            raise ValueError("bedrock max_retries cannot be negative")
        
        # Check API credentials availability
        self._check_api_credentials(config)
    
    def _check_api_credentials(self, config: AppConfig) -> None:
        """
        Verify API credentials are available.
        
        Args:
            config: Configuration to check
            
        Raises:
            ValueError: If required credentials are missing
        """
        aws_access_key = os.getenv(config.bedrock.aws_access_key_env)
        aws_secret_key = os.getenv(config.bedrock.aws_secret_key_env)
        
        if not aws_access_key:
            raise ValueError(
                f"AWS access key not found in environment variable: {config.bedrock.aws_access_key_env}"
            )
        
        if not aws_secret_key:
            raise ValueError(
                f"AWS secret key not found in environment variable: {config.bedrock.aws_secret_key_env}"
            )
    
    def get_config(self) -> AppConfig:
        """
        Get the current configuration.
        
        Returns:
            AppConfig: Current configuration
        """
        return self.config
    
    def save_example_config(self, path: Path) -> None:
        """
        Save an example configuration file.
        
        Args:
            path: Path where to save the example config
        """
        example_config = {
            'bedrock': {
                'region': 'us-east-2',
                'model_id': 'anthropic.claude-sonnet-4-20250514-v1:0',
                'timeout': 30,
                'max_retries': 3,
                'rate_limit_delay': 1.0
            },
            'processing': {
                'base_path': '~/Desktop/worklogs/',
                'output_path': '~/Desktop/worklogs/summaries/',
                'max_file_size_mb': 50,
                'batch_size': 10,
                'rate_limit_delay': 1.0
            },
            'logging': {
                'level': 'INFO',
                'console_output': True,
                'file_output': True,
                'log_dir': '~/Desktop/worklogs/summaries/error_logs/',
                'include_timestamps': True,
                'include_module_names': True,
                'max_file_size_mb': 10,
                'backup_count': 5
            }
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(example_config, f, default_flow_style=False, indent=2)
            else:
                json.dump(example_config, f, indent=2)
    
    def print_config_summary(self) -> None:
        """Print a summary of the current configuration."""
        print("📋 Configuration Summary:")
        print("=" * 40)
        
        if self.config_path:
            print(f"Config file: {self.config_path}")
        else:
            print("Config file: Using defaults (no config file found)")
        
        print(f"AWS Region: {self.config.bedrock.region}")
        print(f"Model ID: {self.config.bedrock.model_id}")
        print(f"Base Path: {self.config.processing.base_path}")
        print(f"Output Path: {self.config.processing.output_path}")
        print(f"Log Level: {self.config.logging.level.value}")
        print(f"Max File Size: {self.config.processing.max_file_size_mb} MB")
        print()