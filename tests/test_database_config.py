#!/usr/bin/env python3
"""
Test Suite for Database Path Configuration - Phase 3

This module tests database_path configuration support including:
- ProcessingConfig database_path field
- WJS_DATABASE_PATH environment variable support
- Configuration parsing and validation
- Backward compatibility with existing configurations

Tests follow TDD principles with comprehensive coverage of all database path scenarios.
"""

import pytest
import sys
import os
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Optional, Dict, Any

# Import the modules we'll be testing
from config_manager import ConfigManager, ProcessingConfig, AppConfig


class TestDatabasePathConfigurationField:
    """Test cases for database_path field in ProcessingConfig."""

    def test_processing_config_has_database_path_field(self):
        """Test that ProcessingConfig includes database_path field."""
        # This test will initially fail until we implement the field
        config = ProcessingConfig()
        assert hasattr(config, 'database_path')
        # Default should be None for backward compatibility
        assert config.database_path is None

    def test_processing_config_database_path_default_value(self):
        """Test default value for database_path field."""
        config = ProcessingConfig()
        # Default should be None to maintain backward compatibility
        expected_default = None
        assert config.database_path == expected_default

    def test_processing_config_database_path_custom_value(self):
        """Test setting custom database_path value."""
        custom_path = "/custom/database/path/journal.db"
        config = ProcessingConfig(database_path=custom_path)
        assert config.database_path == custom_path

    def test_processing_config_database_path_expanduser(self):
        """Test that database_path supports user home directory expansion."""
        config = ProcessingConfig(database_path="~/journals/database.db")
        assert config.database_path == "~/journals/database.db"
        # The actual expansion should happen during path resolution, not in config


class TestDatabasePathEnvironmentVariable:
    """Test cases for WJS_DATABASE_PATH environment variable support."""

    def test_wjs_database_path_env_var_support(self):
        """Test that WJS_DATABASE_PATH environment variable is recognized."""
        test_db_path = "/env/database/path/test.db"
        
        with patch.dict(os.environ, {'WJS_DATABASE_PATH': test_db_path}):
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            assert config.processing.database_path == test_db_path

    def test_wjs_database_path_env_var_overrides_config_file(self):
        """Test that environment variable overrides config file database_path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file with database_path
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                'processing': {
                    'database_path': '/config/file/database.db',
                    'base_path': '~/worklogs'
                }
            }
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            # Environment variable should override
            env_db_path = "/env/override/database.db"
            with patch.dict(os.environ, {'WJS_DATABASE_PATH': env_db_path}):
                config_manager = ConfigManager(config_path=config_file)
                config = config_manager.get_config()
                
                assert config.processing.database_path == env_db_path

    def test_wjs_database_path_env_var_empty_value(self):
        """Test behavior when WJS_DATABASE_PATH is empty string."""
        with patch.dict(os.environ, {'WJS_DATABASE_PATH': ''}):
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # Empty string should be treated as a valid value (explicit no database path)
            assert config.processing.database_path == ''

    def test_wjs_database_path_env_var_not_set(self):
        """Test behavior when WJS_DATABASE_PATH is not set."""
        # Ensure the environment variable is not set
        if 'WJS_DATABASE_PATH' in os.environ:
            del os.environ['WJS_DATABASE_PATH']
            
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Should use default value (None) when env var not set
        assert config.processing.database_path is None


class TestDatabasePathConfigurationParsing:
    """Test cases for parsing database_path from configuration files."""

    def test_database_path_from_yaml_config(self):
        """Test parsing database_path from YAML configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                'processing': {
                    'database_path': '/yaml/database/path.db',
                    'base_path': '~/worklogs',
                    'output_path': '~/worklogs/summaries'
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            
            assert config.processing.database_path == '/yaml/database/path.db'
            assert config.processing.base_path == '~/worklogs'

    def test_database_path_from_json_config(self):
        """Test parsing database_path from JSON configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_content = {
                "processing": {
                    "database_path": "/json/database/path.db",
                    "base_path": "~/worklogs",
                    "output_path": "~/worklogs/summaries"
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_content, f)
            
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            
            assert config.processing.database_path == '/json/database/path.db'
            assert config.processing.base_path == '~/worklogs'

    def test_database_path_missing_from_config_file(self):
        """Test behavior when database_path is missing from config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                'processing': {
                    'base_path': '~/worklogs',
                    'output_path': '~/worklogs/summaries'
                    # database_path intentionally missing
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            
            # Should use default value when missing from config
            assert config.processing.database_path is None

    def test_database_path_null_in_config_file(self):
        """Test behavior when database_path is explicitly null in config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                'processing': {
                    'database_path': None,
                    'base_path': '~/worklogs'
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            
            assert config.processing.database_path is None


class TestDatabasePathValidation:
    """Test cases for database_path validation logic."""

    def test_database_path_validation_valid_path(self):
        """Test validation accepts valid database paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            valid_db_path = str(Path(temp_dir) / "valid_database.db")
            
            config_content = {
                'processing': {
                    'database_path': valid_db_path,
                    'base_path': temp_dir,
                    'output_path': temp_dir
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            # Should not raise any validation errors
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            assert config.processing.database_path == valid_db_path

    def test_database_path_validation_relative_path(self):
        """Test validation accepts relative database paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            
            config_content = {
                'processing': {
                    'database_path': 'relative/database.db',
                    'base_path': temp_dir,
                    'output_path': temp_dir
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            # Should accept relative paths (resolution happens later)
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            assert config.processing.database_path == 'relative/database.db'

    def test_database_path_validation_expanduser_path(self):
        """Test validation accepts paths with ~ user expansion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            
            config_content = {
                'processing': {
                    'database_path': '~/journals/database.db',
                    'base_path': temp_dir,
                    'output_path': temp_dir
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            # Should accept paths with ~ expansion
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            assert config.processing.database_path == '~/journals/database.db'


class TestBackwardCompatibility:
    """Test cases for backward compatibility with existing configurations."""

    def test_existing_configs_without_database_path_work(self):
        """Test that existing config files without database_path continue to work."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a legacy config file (no database_path)
            config_file = Path(temp_dir) / "config.yaml"
            legacy_config = {
                'llm': {
                    'provider': 'bedrock'
                },
                'processing': {
                    'base_path': '~/worklogs',
                    'output_path': '~/worklogs/summaries',
                    'max_file_size_mb': 50
                },
                'logging': {
                    'level': 'INFO'
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(legacy_config, f)
            
            # Should load successfully with default database_path
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            
            assert config.llm.provider == 'bedrock'
            assert config.processing.base_path == '~/worklogs'
            assert config.processing.database_path is None  # Default value

    def test_mixed_new_and_legacy_config_elements(self):
        """Test config with both new database_path and legacy elements."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            mixed_config = {
                'llm': {
                    'provider': 'google_genai'  # Legacy element
                },
                'processing': {
                    'base_path': '~/worklogs',  # Legacy element
                    'database_path': '/new/database/path.db',  # New element
                    'output_path': '~/worklogs/summaries',
                    'max_file_size_mb': 100
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(mixed_config, f)
            
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            
            # Should handle both legacy and new elements
            assert config.llm.provider == 'google_genai'
            assert config.processing.base_path == '~/worklogs'
            assert config.processing.database_path == '/new/database/path.db'
            assert config.processing.max_file_size_mb == 100

    def test_default_processing_config_unchanged(self):
        """Test that default ProcessingConfig values remain unchanged except for database_path."""
        config = ProcessingConfig()
        
        # Existing defaults should remain the same
        assert config.base_path == "~/Desktop/worklogs/"
        assert config.output_path == "~/Desktop/worklogs/summaries/"
        assert config.max_file_size_mb == 50
        assert config.batch_size == 10
        
        # Only new field should be None by default
        assert config.database_path is None


class TestConfigurationIntegration:
    """Test integration of database_path with existing configuration system."""

    def test_database_path_with_executable_directory_config(self):
        """Test database_path works with executable directory configuration discovery."""
        from config_manager import ExecutableDetector
        
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Config co-located with executable
            exe_config = exe_dir / "config.yaml"
            config_content = {
                'processing': {
                    'database_path': '/exe/dir/database.db',
                    'base_path': '~/worklogs'
                }
            }
            
            with open(exe_config, 'w') as f:
                yaml.dump(config_content, f)
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                config_manager = ConfigManager()
                config = config_manager.get_config()
                
                assert config.processing.database_path == '/exe/dir/database.db'

    def test_database_path_priority_order(self):
        """Test priority order: env var > config file > defaults."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file with database_path
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                'processing': {
                    'database_path': '/config/database.db'
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            # Test 1: Config file value (no env var)
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            assert config.processing.database_path == '/config/database.db'
            
            # Test 2: Environment variable overrides config file
            with patch.dict(os.environ, {'WJS_DATABASE_PATH': '/env/database.db'}):
                config_manager = ConfigManager(config_path=config_file)
                config = config_manager.get_config()
                assert config.processing.database_path == '/env/database.db'

    def test_database_path_in_example_config_generation(self):
        """Test that database_path is included when generating example configs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            example_config_path = Path(temp_dir) / "example_config.yaml"
            
            config_manager = ConfigManager()
            config_manager.save_example_config(example_config_path)
            
            # Load and verify the generated example config
            with open(example_config_path, 'r') as f:
                example_config = yaml.safe_load(f)
            
            # Should include database_path in processing section
            assert 'processing' in example_config
            assert 'database_path' in example_config['processing']
            # Default should be None or a reasonable example path
            db_path = example_config['processing']['database_path']
            assert db_path is None or isinstance(db_path, str)


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases for database_path configuration."""

    def test_database_path_with_invalid_config_file(self):
        """Test behavior when config file is invalid but has database_path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            # Invalid YAML content
            config_file.write_text("processing:\n  database_path: /valid/path.db\ninvalid: yaml: [unclosed")
            
            # Should handle gracefully and use defaults
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            
            # Should fall back to defaults when config is invalid
            assert config.processing.database_path is None

    def test_database_path_type_conversion(self):
        """Test that database_path handles different input types correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            
            # Test with different path representations
            test_cases = [
                "/absolute/path/database.db",
                "relative/path/database.db", 
                "~/user/home/database.db",
                "./current/dir/database.db"
            ]
            
            for test_path in test_cases:
                config_content = {
                    'processing': {
                        'database_path': test_path,
                        'base_path': temp_dir,
                        'output_path': temp_dir
                    }
                }
                
                with open(config_file, 'w') as f:
                    yaml.dump(config_content, f)
                
                config_manager = ConfigManager(config_path=config_file)
                config = config_manager.get_config()
                
                assert config.processing.database_path == test_path
                assert isinstance(config.processing.database_path, str)

    def test_database_path_empty_processing_section(self):
        """Test behavior when processing section is empty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                'llm': {'provider': 'bedrock'},
                'processing': {}  # Empty processing section
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            
            # Should use all defaults when processing section is empty
            assert config.processing.database_path is None
            assert config.processing.base_path == ProcessingConfig.base_path

    def test_database_path_no_processing_section(self):
        """Test behavior when processing section is completely missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_content = {
                'llm': {'provider': 'bedrock'}
                # No processing section at all
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            config_manager = ConfigManager(config_path=config_file)
            config = config_manager.get_config()
            
            # Should create processing config with defaults when section is missing
            assert config.processing.database_path is None
            assert config.processing.base_path == ProcessingConfig.base_path


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])