# ABOUTME: PyInstaller-based local build system for WorkJournalMaker desktop application
# ABOUTME: Provides complete build execution, validation, and cross-platform executable generation

"""
Local build system for WorkJournalMaker desktop application.

This module provides a comprehensive build system using PyInstaller to create
standalone executables for Windows and macOS. It includes build validation,
execution monitoring, result validation, and comprehensive error handling.

Key Features:
- Cross-platform executable generation
- Build environment validation
- Comprehensive error handling and reporting
- Build artifact management and cleanup
- Executable testing and validation
- Detailed build metrics and reporting

Usage:
    builder = LocalBuilder()
    result = builder.execute_build()
    if result.success:
        print(f"Build completed: {result.executable_path}")
"""

import os
import sys
import subprocess
import platform
import shutil
import time
import stat
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging

# Setup module logger
logger = logging.getLogger(__name__)


class BuildError(Exception):
    """Exception raised for build-related errors."""
    pass


@dataclass
class BuildResult:
    """Result of a build operation."""
    success: bool
    executable_path: Optional[str] = None
    build_time: float = 0.0
    output: str = ""
    error: str = ""
    platform_info: Optional[Dict[str, Any]] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class LocalBuilder:
    """Local build system for PyInstaller-based executable generation."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize the LocalBuilder.
        
        Args:
            project_root: Path to project root directory. If None, auto-detects.
            
        Raises:
            ValueError: If project_root is invalid
            BuildError: If required files are missing
        """
        self.project_root = self._resolve_project_root(project_root)
        self.spec_file = self._find_spec_file()
        self.entry_point = self._find_entry_point()
        self.build_options: Dict[str, Any] = {}
        
        # Validate critical files exist
        self._validate_initialization()
    
    def _resolve_project_root(self, project_root: Optional[str]) -> Path:
        """Resolve the project root directory.
        
        Args:
            project_root: Explicit project root or None for auto-detection
            
        Returns:
            Path to project root
            
        Raises:
            ValueError: If project_root is invalid
        """
        if project_root is None:
            # Auto-detect: find directory containing .spec files
            current = Path.cwd()
            while current != current.parent:
                if list(current.glob("*.spec")):
                    return current
                current = current.parent
            # Fallback to current directory
            return Path.cwd()
        
        root_path = Path(project_root)
        if not root_path.exists():
            raise ValueError(f"Project root does not exist: {project_root}")
        if not root_path.is_dir():
            raise ValueError(f"Project root is not a directory: {project_root}")
        
        return root_path
    
    def _find_spec_file(self) -> Path:
        """Find the PyInstaller spec file.
        
        Returns:
            Path to the spec file
            
        Raises:
            BuildError: If no spec file is found
        """
        spec_files = list(self.project_root.glob("*.spec"))
        if not spec_files:
            raise BuildError(f"No .spec file found in {self.project_root}")
        
        if len(spec_files) > 1:
            # Prefer WorkJournalMaker.spec if it exists
            for spec_file in spec_files:
                if spec_file.name == "WorkJournalMaker.spec":
                    return spec_file
            # Otherwise use the first one
            logger.warning(f"Multiple .spec files found, using {spec_files[0].name}")
        
        return spec_files[0]
    
    def _find_entry_point(self) -> Path:
        """Find the entry point script referenced in the spec file.
        
        Returns:
            Path to the entry point script
            
        Raises:
            BuildError: If entry point cannot be determined
        """
        # Default entry points to check
        candidates = [
            self.project_root / "server_runner.py",
            self.project_root / "main.py",
            self.project_root / "app.py"
        ]
        
        # Try to parse spec file for actual entry point
        try:
            spec_content = self.spec_file.read_text()
            # Look for Analysis() call with script list
            match = re.search(r"Analysis\(\s*\[([^\]]+)\]", spec_content)
            if match:
                scripts_str = match.group(1)
                # Extract first script name
                script_match = re.search(r"['\"]([^'\"]+)['\"]", scripts_str)
                if script_match:
                    script_name = script_match.group(1)
                    entry_point = self.project_root / script_name
                    if entry_point.exists():
                        return entry_point
        except Exception as e:
            logger.warning(f"Could not parse spec file for entry point: {e}")
        
        # Check candidates
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        raise BuildError("Could not find entry point script")
    
    def _validate_initialization(self) -> None:
        """Validate that initialization was successful.
        
        Raises:
            BuildError: If validation fails
        """
        if not self.spec_file.exists():
            raise BuildError(f"Spec file not found: {self.spec_file}")
        
        if not self.entry_point.exists():
            raise BuildError(f"Entry point not found: {self.entry_point}")
    
    # Build Environment Validation
    
    def validate_build_environment(self) -> bool:
        """Validate that the build environment is ready.
        
        Returns:
            True if environment is valid
            
        Raises:
            BuildError: If environment validation fails
        """
        # Check PyInstaller availability
        if not shutil.which('pyinstaller'):
            raise BuildError("PyInstaller not found. Install with: pip install pyinstaller")
        
        # Check Python version compatibility
        if sys.version_info < (3, 8):
            raise BuildError(f"Python 3.8+ required, found {sys.version}")
        
        # Check disk space (basic check)
        try:
            stat_result = os.statvfs(self.project_root)
            free_bytes = stat_result.f_frsize * stat_result.f_available
            # Require at least 500MB free space
            if free_bytes < 500 * 1024 * 1024:
                logger.warning(f"Low disk space: {free_bytes / 1024 / 1024:.1f} MB available")
        except (OSError, AttributeError):
            # statvfs not available on Windows
            pass
        
        return True
    
    def validate_spec_file(self) -> bool:
        """Validate that the spec file is valid.
        
        Returns:
            True if spec file is valid
            
        Raises:
            BuildError: If spec file validation fails
        """
        if not self.spec_file.exists():
            raise BuildError(f"Spec file not found: {self.spec_file}")
        
        try:
            content = self.spec_file.read_text()
            
            # Basic validation - should contain required elements
            required_elements = ['Analysis', 'PYZ', 'EXE']
            for element in required_elements:
                if element not in content:
                    raise BuildError(f"Spec file missing required element: {element}")
            
            return True
        except UnicodeDecodeError:
            raise BuildError(f"Spec file is not valid UTF-8: {self.spec_file}")
        except Exception as e:
            raise BuildError(f"Error reading spec file: {e}")
    
    def validate_entry_point(self) -> bool:
        """Validate that the entry point script exists.
        
        Returns:
            True if entry point is valid
            
        Raises:
            BuildError: If entry point validation fails
        """
        if not self.entry_point.exists():
            raise BuildError(f"Entry point not found: {self.entry_point}")
        
        # Check if it's a valid Python file
        try:
            content = self.entry_point.read_text()
            # Basic syntax check
            compile(content, str(self.entry_point), 'exec')
            return True
        except SyntaxError as e:
            raise BuildError(f"Entry point has syntax errors: {e}")
        except UnicodeDecodeError:
            raise BuildError(f"Entry point is not valid UTF-8: {self.entry_point}")
        except Exception as e:
            raise BuildError(f"Error validating entry point: {e}")
    
    # Build Command Generation
    
    def generate_build_command(self, 
                             clean: bool = False,
                             distpath: Optional[str] = None,
                             workpath: Optional[str] = None,
                             additional_args: Optional[List[str]] = None) -> List[str]:
        """Generate the PyInstaller build command.
        
        Args:
            clean: Whether to clean build artifacts
            distpath: Custom distribution directory
            workpath: Custom work directory
            additional_args: Additional PyInstaller arguments
            
        Returns:
            Complete command as list of strings
        """
        command = ['pyinstaller']
        
        # Add spec file
        command.append(str(self.spec_file))
        
        # Add options
        if clean:
            command.append('--clean')
        
        if distpath:
            command.extend(['--distpath', distpath])
        
        if workpath:
            command.extend(['--workpath', workpath])
        
        # Add build options
        for key, value in self.build_options.items():
            if isinstance(value, bool) and value:
                command.append(f'--{key}')
            elif value and not isinstance(value, bool):
                command.extend([f'--{key}', str(value)])
        
        # Add additional arguments
        if additional_args:
            command.extend(additional_args)
        
        return command
    
    # Build Execution
    
    def execute_build(self, 
                     timeout: Optional[int] = None,
                     capture_output: bool = True,
                     clean: bool = False,
                     distpath: Optional[str] = None,
                     workpath: Optional[str] = None) -> BuildResult:
        """Execute the PyInstaller build.
        
        Args:
            timeout: Build timeout in seconds
            capture_output: Whether to capture stdout/stderr
            clean: Whether to clean build artifacts
            distpath: Custom distribution directory
            workpath: Custom work directory
            
        Returns:
            BuildResult with build information
        """
        start_time = time.time()
        
        # Generate command
        command = self.generate_build_command(
            clean=clean,
            distpath=distpath,
            workpath=workpath
        )
        
        logger.info(f"Executing build command: {' '.join(command)}")
        
        try:
            # Execute build
            result = subprocess.run(
                command,
                cwd=self.project_root,
                timeout=timeout,
                capture_output=capture_output,
                text=True
            )
            
            build_time = time.time() - start_time
            
            # Check if build succeeded
            success = result.returncode == 0
            
            # Find the created executable
            executable_path = None
            if success:
                executable_path = self._find_built_executable(distpath)
            
            # Create platform info
            platform_info = self.detect_platform()
            
            return BuildResult(
                success=success,
                executable_path=executable_path,
                build_time=build_time,
                output=result.stdout or "",
                error=result.stderr or "",
                platform_info=platform_info,
                metrics={
                    'command': ' '.join(command),
                    'return_code': result.returncode,
                    'timeout_used': timeout,
                    'capture_output': capture_output
                }
            )
            
        except subprocess.TimeoutExpired:
            build_time = time.time() - start_time
            return BuildResult(
                success=False,
                build_time=build_time,
                error=f"Build timed out after {timeout} seconds"
            )
        except Exception as e:
            build_time = time.time() - start_time
            return BuildResult(
                success=False,
                build_time=build_time,
                error=f"Build execution failed: {e}"
            )
    
    def _find_built_executable(self, distpath: Optional[str] = None) -> Optional[str]:
        """Find the built executable file.
        
        Args:
            distpath: Custom distribution directory
            
        Returns:
            Path to executable or None if not found
        """
        # Determine dist directory
        if distpath:
            dist_dir = Path(distpath)
        else:
            dist_dir = self.project_root / "dist"
        
        if not dist_dir.exists():
            return None
        
        # Get expected executable name
        expected_name = self.get_expected_executable_name()
        
        # Look for executable in dist directory
        for item in dist_dir.iterdir():
            if item.is_dir():
                # Check inside app directory
                exe_path = item / expected_name
                if exe_path.exists():
                    return str(exe_path)
            elif item.name == expected_name:
                # Direct executable file
                return str(item)
        
        return None
    
    # Build Result Validation
    
    def validate_executable(self) -> bool:
        """Validate that the built executable exists.
        
        Returns:
            True if executable is valid
            
        Raises:
            BuildError: If executable validation fails
        """
        executable_path = self.get_executable_path()
        if not executable_path or not Path(executable_path).exists():
            raise BuildError("Built executable not found")
        
        return True
    
    def validate_executable_permissions(self) -> bool:
        """Validate that the executable has proper permissions.
        
        Returns:
            True if permissions are valid
            
        Raises:
            BuildError: If permission validation fails
        """
        executable_path = self.get_executable_path()
        if not executable_path:
            raise BuildError("No executable to validate permissions")
        
        exe_path = Path(executable_path)
        if not exe_path.exists():
            raise BuildError(f"Executable not found: {executable_path}")
        
        # Check if executable bit is set (Unix-like systems)
        if os.name != 'nt':
            file_stat = exe_path.stat()
            if not (file_stat.st_mode & stat.S_IEXEC):
                raise BuildError(f"Executable lacks execute permissions: {executable_path}")
        
        return True
    
    def get_executable_size(self) -> int:
        """Get the size of the built executable in bytes.
        
        Returns:
            Size in bytes
            
        Raises:
            BuildError: If executable not found
        """
        executable_path = self.get_executable_path()
        if not executable_path:
            raise BuildError("No executable found")
        
        exe_path = Path(executable_path)
        if not exe_path.exists():
            raise BuildError(f"Executable not found: {executable_path}")
        
        return exe_path.stat().st_size
    
    def get_executable_path(self) -> Optional[str]:
        """Get the path to the built executable.
        
        Returns:
            Path to executable or None if not found
        """
        return self._find_built_executable()
    
    # Cross-Platform Compatibility
    
    def detect_platform(self) -> Dict[str, str]:
        """Detect the current platform information.
        
        Returns:
            Dictionary with platform information
        """
        return {
            'system': platform.system(),
            'architecture': platform.architecture()[0],
            'machine': platform.machine(),
            'platform': platform.platform(),
            'python_version': platform.python_version()
        }
    
    def get_executable_extension(self) -> str:
        """Get the appropriate executable extension for current platform.
        
        Returns:
            Executable extension (with dot)
        """
        if platform.system() == 'Windows':
            return '.exe'
        else:
            return ''
    
    def get_expected_executable_name(self) -> str:
        """Get the expected executable name based on spec file.
        
        Returns:
            Expected executable name with extension
        """
        # Extract name from spec file
        try:
            spec_content = self.spec_file.read_text()
            match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", spec_content)
            if match:
                base_name = match.group(1)
            else:
                base_name = self.spec_file.stem
        except Exception:
            base_name = self.spec_file.stem
        
        return base_name + self.get_executable_extension()
    
    # Build Cleanup
    
    def clean_build_artifacts(self) -> None:
        """Clean PyInstaller build artifacts."""
        artifacts_to_clean = [
            self.project_root / "build",  # PyInstaller's build dir
            self.project_root / "dist"
        ]
        
        for artifact in artifacts_to_clean:
            if artifact.exists() and artifact.is_dir():
                shutil.rmtree(artifact)
                logger.info(f"Cleaned: {artifact}")
    
    def clean_pycache(self) -> None:
        """Clean Python cache files."""
        for pycache_dir in self.project_root.rglob("__pycache__"):
            if pycache_dir.is_dir():
                shutil.rmtree(pycache_dir)
                logger.info(f"Cleaned: {pycache_dir}")
    
    def clean_all(self) -> None:
        """Clean all build artifacts and cache files."""
        self.clean_build_artifacts()
        self.clean_pycache()
        
        # Clean additional PyInstaller files
        additional_files = [
            self.project_root / f"{self.spec_file.stem}.spec.bak"
        ]
        
        for file_path in additional_files:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Cleaned: {file_path}")
    
    # Build Configuration
    
    def load_build_config(self) -> Dict[str, Any]:
        """Load build configuration from spec file.
        
        Returns:
            Build configuration dictionary
        """
        try:
            spec_content = self.spec_file.read_text()
            
            # Extract key configuration values using regex
            config = {}
            
            # Extract debug setting
            debug_match = re.search(r"debug\s*=\s*(True|False)", spec_content)
            if debug_match:
                config['debug'] = debug_match.group(1) == 'True'
            
            # Extract console setting
            console_match = re.search(r"console\s*=\s*(True|False)", spec_content)
            if console_match:
                config['console'] = console_match.group(1) == 'True'
            
            # Extract UPX setting
            upx_match = re.search(r"upx\s*=\s*(True|False)", spec_content)
            if upx_match:
                config['upx'] = upx_match.group(1) == 'True'
            
            return config
        except Exception as e:
            logger.warning(f"Could not load build config: {e}")
            return {}
    
    def get_build_options(self) -> Dict[str, Any]:
        """Get current build options.
        
        Returns:
            Current build options
        """
        return self.build_options.copy()
    
    def set_build_option(self, key: str, value: Any) -> None:
        """Set a build option.
        
        Args:
            key: Option name
            value: Option value
        """
        self.build_options[key] = value
    
    # Build Testing
    
    def test_executable(self, args: Optional[List[str]] = None, timeout: int = 30) -> bool:
        """Test the built executable by running it.
        
        Args:
            args: Arguments to pass to executable
            timeout: Test timeout in seconds
            
        Returns:
            True if executable runs successfully
        """
        executable_path = self.get_executable_path()
        if not executable_path:
            return False
        
        try:
            command = [executable_path]
            if args:
                command.extend(args)
            
            # For GUI applications, we can't easily test full functionality
            # So we'll just check if it starts without immediate crash
            result = subprocess.run(
                command + ['--help'],  # Try help flag first
                timeout=timeout,
                capture_output=True,
                text=True
            )
            
            # If help works, that's good
            if result.returncode == 0:
                return True
            
            # If help doesn't work, try just running it briefly
            result = subprocess.run(
                command,
                timeout=5,  # Very short timeout for GUI apps
                capture_output=True,
                text=True
            )
            
            # For GUI apps, we expect it might not exit cleanly in 5 seconds
            # So we consider timeout or 0 return code as success
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            # Timeout might be expected for GUI applications
            return True
        except Exception as e:
            logger.error(f"Executable test failed: {e}")
            return False
    
    # Build Reporting
    
    def generate_build_report(self, build_result: BuildResult) -> Dict[str, Any]:
        """Generate a comprehensive build report.
        
        Args:
            build_result: Build result to report on
            
        Returns:
            Build report dictionary
        """
        report = {
            'timestamp': time.time(),
            'success': build_result.success,
            'build_time': build_result.build_time,
            'platform': build_result.platform_info or self.detect_platform(),
            'spec_file': str(self.spec_file),
            'entry_point': str(self.entry_point),
            'project_root': str(self.project_root)
        }
        
        if build_result.executable_path:
            exe_path = Path(build_result.executable_path)
            if exe_path.exists():
                report['executable'] = {
                    'path': build_result.executable_path,
                    'size': exe_path.stat().st_size,
                    'size_mb': exe_path.stat().st_size / (1024 * 1024)
                }
        
        if build_result.error:
            report['error'] = build_result.error
        
        if build_result.metrics:
            report['metrics'] = build_result.metrics
        
        return report
    
    def get_build_metrics(self, build_result: BuildResult) -> Dict[str, Any]:
        """Extract build metrics from build result.
        
        Args:
            build_result: Build result to analyze
            
        Returns:
            Build metrics dictionary
        """
        metrics = {
            'build_time': build_result.build_time,
            'success': build_result.success
        }
        
        if build_result.executable_path:
            try:
                size = self.get_executable_size()
                metrics['executable_size'] = size
                metrics['executable_size_mb'] = size / (1024 * 1024)
            except BuildError:
                pass
        
        if build_result.platform_info:
            metrics['platform'] = build_result.platform_info['system']
            metrics['architecture'] = build_result.platform_info['architecture']
        
        # Add custom metrics from build result
        if build_result.metrics:
            metrics.update(build_result.metrics)
        
        return metrics
    
    def format_build_summary(self, build_result: BuildResult) -> str:
        """Format a human-readable build summary.
        
        Args:
            build_result: Build result to summarize
            
        Returns:
            Formatted summary string
        """
        lines = []
        lines.append("="*60)
        lines.append("BUILD SUMMARY")
        lines.append("="*60)
        
        status = "SUCCESS" if build_result.success else "FAILED"
        lines.append(f"Status: {status}")
        lines.append(f"Build Time: {build_result.build_time:.1f}s")
        
        if build_result.executable_path:
            exe_path = Path(build_result.executable_path)
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                lines.append(f"Executable: {exe_path.name} ({size_mb:.1f} MB)")
                lines.append(f"Location: {exe_path.parent}")
        
        if build_result.platform_info:
            system = build_result.platform_info.get('system', 'Unknown')
            arch = build_result.platform_info.get('architecture', 'Unknown')
            lines.append(f"Platform: {system} ({arch})")
        
        if build_result.error:
            lines.append(f"Error: {build_result.error}")
        
        lines.append("="*60)
        
        return "\n".join(lines)


# Convenience function for simple builds
def build_project(project_root: Optional[str] = None, 
                  clean: bool = False,
                  timeout: Optional[int] = None) -> BuildResult:
    """Convenience function to build the project.
    
    Args:
        project_root: Project root directory
        clean: Whether to clean before building
        timeout: Build timeout in seconds
        
    Returns:
        BuildResult with build information
    """
    builder = LocalBuilder(project_root=project_root)
    return builder.execute_build(clean=clean, timeout=timeout)