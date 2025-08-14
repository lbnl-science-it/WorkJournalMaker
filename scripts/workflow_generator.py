# ABOUTME: GitHub Actions workflow generator for automated CI/CD pipeline creation
# ABOUTME: Generates YAML workflows with matrix builds, testing, and release automation

import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import os


@dataclass
class WorkflowConfig:
    """Configuration for GitHub Actions workflow generation."""
    
    name: str
    triggers: List[str]
    python_version: str
    platforms: List[str]
    node_version: Optional[str] = "18"
    timeout_minutes: Optional[int] = 30
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Workflow name cannot be empty")
        
        if not self.triggers:
            raise ValueError("At least one trigger must be specified")
        
        if not self.python_version:
            raise ValueError("Python version must be specified")
        
        if not self.platforms:
            raise ValueError("At least one platform must be specified")


@dataclass 
class BuildMatrix:
    """Build matrix configuration for multi-platform builds."""
    
    platforms: List[Dict[str, Any]]
    
    def __post_init__(self):
        """Validate build matrix configuration."""
        if not self.platforms:
            raise ValueError("At least one platform must be specified")
        
        required_fields = {"os", "python", "arch"}
        for i, platform in enumerate(self.platforms):
            missing_fields = required_fields - set(platform.keys())
            if missing_fields:
                raise ValueError(
                    f"Platform {i} missing required fields: {missing_fields}"
                )


class WorkflowGenerator:
    """Generates GitHub Actions workflow YAML files."""
    
    def __init__(self, config: WorkflowConfig, matrix: BuildMatrix):
        """
        Initialize workflow generator.
        
        Args:
            config: Workflow configuration
            matrix: Build matrix configuration
        """
        self.config = config
        self.matrix = matrix
    
    def generate(self) -> str:
        """
        Generate complete GitHub Actions workflow YAML.
        
        Returns:
            Complete workflow YAML as string
        """
        workflow_data = {
            "name": self.config.name,
            "on": self._generate_triggers(),
            "jobs": {
                "build": self._generate_build_job(),
                "release": self._generate_release_job()
            }
        }
        
        return yaml.dump(workflow_data, default_flow_style=False, sort_keys=False)
    
    def _generate_triggers(self) -> Dict[str, Any]:
        """Generate workflow trigger configuration."""
        triggers = {}
        
        for trigger in self.config.triggers:
            if trigger == "push":
                triggers["push"] = {
                    "branches": ["main", "master"],
                    "tags": ["v*"]
                }
            elif trigger == "pull_request":
                triggers["pull_request"] = {
                    "branches": ["main", "master"]
                }
            elif trigger == "release":
                triggers["release"] = {
                    "types": ["published"]
                }
            else:
                # Simple trigger without configuration
                triggers[trigger] = None
        
        return triggers
    
    def _generate_build_job(self) -> Dict[str, Any]:
        """Generate build job configuration."""
        return {
            "runs-on": "${{ matrix.os }}",
            "timeout-minutes": self.config.timeout_minutes,
            "strategy": {
                "fail-fast": False,
                "matrix": {
                    "include": self.matrix.platforms
                }
            },
            "steps": self._generate_build_steps()
        }
    
    def _generate_build_steps(self) -> List[Dict[str, Any]]:
        """Generate build job steps."""
        steps = [
            {
                "name": "Checkout code",
                "uses": "actions/checkout@v4"
            },
            {
                "name": "Set up Python ${{ matrix.python }}",
                "uses": "actions/setup-python@v4",
                "with": {
                    "python-version": "${{ matrix.python }}"
                }
            },
            {
                "name": "Install dependencies",
                "run": self._generate_install_command()
            },
            {
                "name": "Run tests",
                "run": self._generate_test_command()
            },
            {
                "name": "Build executable with PyInstaller",
                "run": self._generate_pyinstaller_command()
            },
            {
                "name": "Upload artifact",
                "uses": "actions/upload-artifact@v4",
                "with": {
                    "name": "${{ matrix.executable_name }}",
                    "path": "dist/${{ matrix.executable_name }}"
                }
            }
        ]
        
        return steps
    
    def _generate_install_command(self) -> str:
        """Generate dependency installation command."""
        commands = [
            "python -m pip install --upgrade pip",
            "pip install -r requirements.txt",
            "pip install pyinstaller pytest pytest-cov"
        ]
        
        # Use appropriate command separator for different platforms
        return " && ".join(commands)
    
    def _generate_test_command(self) -> str:
        """Generate test execution command."""
        return "python -m pytest tests/ -v --cov=. --cov-report=xml"
    
    def _generate_pyinstaller_command(self) -> str:
        """Generate PyInstaller build command."""
        return (
            "pyinstaller --onefile --windowed "
            "--name=${{ matrix.executable_name }} "
            "--distpath=dist "
            "server_runner.py"
        )
    
    def _generate_release_job(self) -> Dict[str, Any]:
        """Generate release job configuration."""
        return {
            "needs": ["build"],
            "runs-on": "ubuntu-latest",
            "if": "github.event_name == 'release'",
            "steps": [
                {
                    "name": "Download all artifacts",
                    "uses": "actions/download-artifact@v4",
                    "with": {
                        "path": "artifacts"
                    }
                },
                {
                    "name": "Create release assets",
                    "run": self._generate_release_command()
                },
                {
                    "name": "Upload release assets",
                    "uses": "softprops/action-gh-release@v1",
                    "with": {
                        "files": "release-assets/*"
                    },
                    "env": {
                        "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}"
                    }
                }
            ]
        }
    
    def _generate_release_command(self) -> str:
        """Generate release asset preparation command."""
        commands = [
            "mkdir -p release-assets",
            "find artifacts -name '*' -type f -exec cp {} release-assets/ \\;",
            "ls -la release-assets/"
        ]
        
        return " && ".join(commands)
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save generated workflow to file.
        
        Args:
            file_path: Path to save the workflow file
        """
        workflow_yaml = self.generate()
        
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(workflow_yaml)


def create_default_config() -> WorkflowConfig:
    """Create default workflow configuration for WorkJournal."""
    return WorkflowConfig(
        name="WorkJournal Desktop Release",
        triggers=["push", "pull_request", "release"],
        python_version="3.8",
        platforms=["ubuntu-latest", "windows-latest", "macos-latest"],
        timeout_minutes=45
    )


def create_default_matrix() -> BuildMatrix:
    """Create default build matrix for WorkJournal."""
    return BuildMatrix(platforms=[
        {
            "os": "ubuntu-latest",
            "python": "3.8",
            "arch": "x64",
            "executable_name": "workjournal-linux",
            "asset_name": "workjournal-linux-x64"
        },
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


def generate_workflow_file(output_path: str = ".github/workflows/release.yml") -> None:
    """
    Generate workflow file with default configuration.
    
    Args:
        output_path: Path to save the generated workflow file
    """
    config = create_default_config()
    matrix = create_default_matrix()
    generator = WorkflowGenerator(config, matrix)
    generator.save_to_file(output_path)


if __name__ == "__main__":
    # Generate default workflow when run directly
    generate_workflow_file()
    print("Generated GitHub Actions workflow at .github/workflows/release.yml")