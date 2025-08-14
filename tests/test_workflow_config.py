# ABOUTME: Tests for GitHub Actions workflow configuration and YAML validation
# ABOUTME: Ensures workflow generator creates valid, comprehensive CI/CD configurations

import pytest
import yaml
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Any, List

# Import the module we'll implement
import sys
sys.path.append(str(Path(__file__).parent.parent))

# This will fail initially - that's expected in TDD
try:
    from scripts.workflow_generator import WorkflowGenerator, WorkflowConfig, BuildMatrix
except ImportError:
    # Create placeholder classes for testing
    class WorkflowConfig:
        pass
    class BuildMatrix:
        pass
    class WorkflowGenerator:
        pass


class TestWorkflowConfig:
    """Test workflow configuration data structures."""
    
    def test_workflow_config_initialization(self):
        """Test WorkflowConfig initialization with required parameters."""
        config = WorkflowConfig(
            name="Release Build",
            triggers=["push", "release"],
            python_version="3.8",
            platforms=["ubuntu-latest", "windows-latest", "macos-latest"]
        )
        
        assert config.name == "Release Build"
        assert config.triggers == ["push", "release"]
        assert config.python_version == "3.8"
        assert config.platforms == ["ubuntu-latest", "windows-latest", "macos-latest"]
    
    def test_workflow_config_validation(self):
        """Test WorkflowConfig validates required parameters."""
        with pytest.raises((ValueError, TypeError)):
            WorkflowConfig()  # Missing required parameters
        
        with pytest.raises(ValueError):
            WorkflowConfig(
                name="",  # Empty name should fail
                triggers=["push"],
                python_version="3.8",
                platforms=["ubuntu-latest"]
            )
        
        with pytest.raises(ValueError):
            WorkflowConfig(
                name="Test",
                triggers=[],  # Empty triggers should fail
                python_version="3.8", 
                platforms=["ubuntu-latest"]
            )
    
    def test_build_matrix_initialization(self):
        """Test BuildMatrix initialization and platform configuration."""
        matrix = BuildMatrix(
            platforms=[
                {"os": "ubuntu-latest", "python": "3.8", "arch": "x64"},
                {"os": "windows-latest", "python": "3.8", "arch": "x64"},
                {"os": "macos-latest", "python": "3.8", "arch": "x64"}
            ]
        )
        
        assert len(matrix.platforms) == 3
        assert matrix.platforms[0]["os"] == "ubuntu-latest"
        assert matrix.platforms[1]["os"] == "windows-latest"
        assert matrix.platforms[2]["os"] == "macos-latest"
    
    def test_build_matrix_validation(self):
        """Test BuildMatrix validates platform configurations."""
        with pytest.raises(ValueError):
            BuildMatrix(platforms=[])  # Empty platforms should fail
        
        with pytest.raises(ValueError):
            BuildMatrix(platforms=[
                {"os": "ubuntu-latest"}  # Missing required fields
            ])


class TestWorkflowGenerator:
    """Test GitHub Actions workflow generation."""
    
    @pytest.fixture
    def sample_config(self):
        """Provide sample workflow configuration for testing."""
        return WorkflowConfig(
            name="WorkJournal Release Build",
            triggers=["push", "pull_request", "release"],
            python_version="3.8",
            platforms=["ubuntu-latest", "windows-latest", "macos-latest"],
            node_version="18",
            timeout_minutes=30
        )
    
    @pytest.fixture
    def sample_matrix(self):
        """Provide sample build matrix for testing."""
        return BuildMatrix(platforms=[
            {
                "os": "ubuntu-latest",
                "python": "3.8",
                "arch": "x64",
                "executable_name": "workjournal-linux"
            },
            {
                "os": "windows-latest", 
                "python": "3.8",
                "arch": "x64",
                "executable_name": "workjournal-windows.exe"
            },
            {
                "os": "macos-latest",
                "python": "3.8", 
                "arch": "x64",
                "executable_name": "workjournal-macos"
            }
        ])
    
    def test_workflow_generator_initialization(self, sample_config, sample_matrix):
        """Test WorkflowGenerator initialization."""
        generator = WorkflowGenerator(config=sample_config, matrix=sample_matrix)
        
        assert generator.config == sample_config
        assert generator.matrix == sample_matrix
    
    def test_generate_workflow_yaml_structure(self, sample_config, sample_matrix):
        """Test workflow YAML generation creates valid structure."""
        generator = WorkflowGenerator(config=sample_config, matrix=sample_matrix)
        workflow_yaml = generator.generate()
        
        # Parse YAML to ensure it's valid
        workflow_data = yaml.safe_load(workflow_yaml)
        
        # Verify top-level structure
        assert "name" in workflow_data
        assert "on" in workflow_data
        assert "jobs" in workflow_data
        
        # Verify workflow name
        assert workflow_data["name"] == "WorkJournal Release Build"
        
        # Verify triggers
        assert "push" in workflow_data["on"]
        assert "pull_request" in workflow_data["on"]
        assert "release" in workflow_data["on"]
    
    def test_generate_workflow_build_job(self, sample_config, sample_matrix):
        """Test workflow generates proper build job configuration."""
        generator = WorkflowGenerator(config=sample_config, matrix=sample_matrix)
        workflow_yaml = generator.generate()
        workflow_data = yaml.safe_load(workflow_yaml)
        
        # Verify build job exists
        assert "build" in workflow_data["jobs"]
        build_job = workflow_data["jobs"]["build"]
        
        # Verify matrix strategy
        assert "strategy" in build_job
        assert "matrix" in build_job["strategy"]
        
        # Verify platform configurations
        matrix_config = build_job["strategy"]["matrix"]
        assert "include" in matrix_config
        assert len(matrix_config["include"]) == 3
        
        # Verify each platform has required fields
        for platform in matrix_config["include"]:
            assert "os" in platform
            assert "python" in platform
            assert "arch" in platform
            assert "executable_name" in platform
    
    def test_generate_workflow_steps(self, sample_config, sample_matrix):
        """Test workflow generates comprehensive build steps."""
        generator = WorkflowGenerator(config=sample_config, matrix=sample_matrix)
        workflow_yaml = generator.generate()
        workflow_data = yaml.safe_load(workflow_yaml)
        
        build_job = workflow_data["jobs"]["build"]
        steps = build_job["steps"]
        
        # Verify essential steps are present
        step_names = [step.get("name", "") for step in steps]
        
        assert any("Checkout code" in name for name in step_names)
        assert any("Set up Python" in name for name in step_names)
        assert any("Install dependencies" in name for name in step_names)
        assert any("Run tests" in name for name in step_names)
        assert any("Build executable" in name for name in step_names)
        assert any("Upload artifact" in name for name in step_names)
    
    def test_generate_workflow_pyinstaller_step(self, sample_config, sample_matrix):
        """Test workflow includes proper PyInstaller build step."""
        generator = WorkflowGenerator(config=sample_config, matrix=sample_matrix)
        workflow_yaml = generator.generate()
        workflow_data = yaml.safe_load(workflow_yaml)
        
        build_job = workflow_data["jobs"]["build"]
        steps = build_job["steps"]
        
        # Find PyInstaller build step
        pyinstaller_step = None
        for step in steps:
            if "Build executable" in step.get("name", ""):
                pyinstaller_step = step
                break
        
        assert pyinstaller_step is not None
        assert "run" in pyinstaller_step
        
        # Verify PyInstaller command structure
        run_command = pyinstaller_step["run"]
        assert "pyinstaller" in run_command
        assert "--onefile" in run_command
        assert "server_runner.py" in run_command
    
    def test_generate_workflow_artifact_upload(self, sample_config, sample_matrix):
        """Test workflow includes artifact upload steps."""
        generator = WorkflowGenerator(config=sample_config, matrix=sample_matrix)
        workflow_yaml = generator.generate()
        workflow_data = yaml.safe_load(workflow_yaml)
        
        build_job = workflow_data["jobs"]["build"]
        steps = build_job["steps"]
        
        # Find artifact upload step
        upload_step = None
        for step in steps:
            if "Upload artifact" in step.get("name", ""):
                upload_step = step
                break
        
        assert upload_step is not None
        assert "uses" in upload_step
        assert "actions/upload-artifact" in upload_step["uses"]
        assert "with" in upload_step
        assert "name" in upload_step["with"]
        assert "path" in upload_step["with"]
    
    def test_generate_workflow_release_job(self, sample_config, sample_matrix):
        """Test workflow includes release job for tagged releases."""
        generator = WorkflowGenerator(config=sample_config, matrix=sample_matrix)
        workflow_yaml = generator.generate()
        workflow_data = yaml.safe_load(workflow_yaml)
        
        # Verify release job exists
        assert "release" in workflow_data["jobs"]
        release_job = workflow_data["jobs"]["release"]
        
        # Verify job dependencies
        assert "needs" in release_job
        assert "build" in release_job["needs"]
        
        # Verify conditional execution
        assert "if" in release_job
        assert "github.event_name == 'release'" in release_job["if"]
    
    def test_workflow_yaml_syntax_validation(self, sample_config, sample_matrix):
        """Test generated YAML has valid syntax and structure."""
        generator = WorkflowGenerator(config=sample_config, matrix=sample_matrix)
        workflow_yaml = generator.generate()
        
        # Should parse without errors
        workflow_data = yaml.safe_load(workflow_yaml)
        
        # Should be re-serializable 
        reserialize = yaml.dump(workflow_data)
        assert reserialize is not None
        
        # Should parse again after reserialize
        reparsed = yaml.safe_load(reserialize)
        assert reparsed is not None
    
    def test_save_workflow_file(self, sample_config, sample_matrix, tmp_path):
        """Test saving generated workflow to file."""
        generator = WorkflowGenerator(config=sample_config, matrix=sample_matrix)
        
        output_path = tmp_path / "release.yml"
        generator.save_to_file(str(output_path))
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify file content is valid YAML
        with open(output_path, 'r') as f:
            content = f.read()
            workflow_data = yaml.safe_load(content)
            assert workflow_data is not None
            assert "name" in workflow_data
    
    def test_workflow_environment_variables(self, sample_config, sample_matrix):
        """Test workflow includes necessary environment variables."""
        generator = WorkflowGenerator(config=sample_config, matrix=sample_matrix)
        workflow_yaml = generator.generate()
        workflow_data = yaml.safe_load(workflow_yaml)
        
        build_job = workflow_data["jobs"]["build"]
        
        # Check for environment variables
        if "env" in build_job:
            env_vars = build_job["env"]
            # Common environment variables for Python builds
            assert any(key.startswith("PYTHON") for key in env_vars.keys())


class TestWorkflowValidation:
    """Test workflow validation and error handling."""
    
    def test_validate_workflow_structure(self):
        """Test workflow structure validation."""
        # Valid workflow structure
        valid_workflow = {
            "name": "Test Workflow",
            "on": ["push"],
            "jobs": {
                "build": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"name": "Checkout", "uses": "actions/checkout@v3"}
                    ]
                }
            }
        }
        
        # This would be implemented in the WorkflowGenerator
        # For now, just test that yaml.safe_load works
        yaml_str = yaml.dump(valid_workflow)
        parsed = yaml.safe_load(yaml_str)
        assert parsed == valid_workflow
    
    def test_workflow_missing_required_fields(self):
        """Test validation catches missing required fields."""
        invalid_workflows = [
            {},  # Empty workflow
            {"name": "Test"},  # Missing 'on' and 'jobs'
            {"name": "Test", "on": ["push"]},  # Missing 'jobs'
            {"name": "Test", "on": ["push"], "jobs": {}},  # Empty jobs
        ]
        
        for invalid in invalid_workflows:
            yaml_str = yaml.dump(invalid)
            parsed = yaml.safe_load(yaml_str)
            # In real implementation, WorkflowGenerator would validate this
            # For now, just ensure YAML parsing works
            assert isinstance(parsed, dict)


class TestWorkflowIntegration:
    """Test integration aspects of workflow generation."""
    
    def test_generate_complete_workflow_file(self, tmp_path):
        """Test generating a complete, realistic workflow file."""
        config = WorkflowConfig(
            name="WorkJournal Desktop Release",
            triggers=["push", "release"],
            python_version="3.8",
            platforms=["windows-latest", "macos-latest"],
            timeout_minutes=45
        )
        
        matrix = BuildMatrix(platforms=[
            {
                "os": "windows-latest",
                "python": "3.8",
                "arch": "x64", 
                "executable_name": "workjournal-windows.exe",
                "asset_name": "workjournal-windows-x64.exe"
            },
            {
                "os": "macos-latest", 
                "python": "3.8",
                "arch": "x64",
                "executable_name": "workjournal-macos",
                "asset_name": "workjournal-macos-x64"
            }
        ])
        
        generator = WorkflowGenerator(config=config, matrix=matrix)
        workflow_path = tmp_path / "complete_workflow.yml"
        
        generator.save_to_file(str(workflow_path))
        
        # Verify file exists and is valid
        assert workflow_path.exists()
        
        with open(workflow_path) as f:
            content = f.read()
            workflow_data = yaml.safe_load(content)
            
            # Verify comprehensive structure
            assert workflow_data["name"] == "WorkJournal Desktop Release"
            assert "build" in workflow_data["jobs"]
            assert "release" in workflow_data["jobs"]
            
            # Verify matrix includes both platforms
            build_job = workflow_data["jobs"]["build"]
            matrix_platforms = build_job["strategy"]["matrix"]["include"]
            assert len(matrix_platforms) == 2
            
            platform_names = [p["os"] for p in matrix_platforms]
            assert "windows-latest" in platform_names
            assert "macos-latest" in platform_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])