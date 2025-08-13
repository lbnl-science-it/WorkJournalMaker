# ABOUTME: Comprehensive tests for local PyInstaller build execution and validation
# ABOUTME: Tests build process, executable creation, and cross-platform compatibility

import os
import sys
import subprocess
import tempfile
import shutil
import platform
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from typing import Dict, List, Optional, Tuple

# Import the module we'll be testing (to be implemented)
try:
    from build.local_builder import LocalBuilder, BuildResult, BuildError
except ImportError:
    # Mock classes for testing
    class BuildError(Exception):
        pass
    
    class BuildResult:
        def __init__(self, success: bool, executable_path: Optional[str] = None, 
                     build_time: float = 0.0, output: str = "", error: str = ""):
            self.success = success
            self.executable_path = executable_path
            self.build_time = build_time
            self.output = output
            self.error = error
    
    class LocalBuilder:
        def __init__(self, project_root: Optional[str] = None):
            pass


class TestLocalBuilderInitialization:
    """Test LocalBuilder initialization and configuration."""
    
    def test_init_with_project_root(self):
        """Test LocalBuilder initialization with explicit project root."""
        test_root = "/test/project"
        builder = LocalBuilder(project_root=test_root)
        assert hasattr(builder, 'project_root')
    
    def test_init_auto_detect_project_root(self):
        """Test LocalBuilder initialization with auto-detected project root."""
        builder = LocalBuilder()
        assert hasattr(builder, 'project_root')
    
    def test_init_invalid_project_root(self):
        """Test LocalBuilder initialization with invalid project root."""
        with pytest.raises(ValueError):
            LocalBuilder(project_root="/nonexistent/path")
    
    def test_init_missing_spec_file(self):
        """Test LocalBuilder initialization when .spec file is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(BuildError):
                LocalBuilder(project_root=temp_dir)


class TestBuildValidation:
    """Test build environment validation."""
    
    @pytest.fixture
    def mock_builder(self):
        """Create a mock LocalBuilder for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create minimal project structure
            spec_content = """
a = Analysis(['server_runner.py'], pathex=['.'], binaries=[], datas=[], hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], win_no_prefer_redirects=False, win_private_assemblies=False, cipher=None, noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [], name='TestApp', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, upx_exclude=[], runtime_tmpdir=None, console=False, disable_windowed_traceback=False, argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None)
"""
            spec_path = Path(temp_dir) / "TestApp.spec"
            spec_path.write_text(spec_content)
            
            # Create entry point
            entry_path = Path(temp_dir) / "server_runner.py"
            entry_path.write_text("print('Hello World')")
            
            yield LocalBuilder(project_root=temp_dir)
    
    def test_validate_pyinstaller_available(self, mock_builder):
        """Test validation that PyInstaller is available."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/pyinstaller'
            result = mock_builder.validate_build_environment()
            assert result is True
    
    def test_validate_pyinstaller_missing(self, mock_builder):
        """Test validation failure when PyInstaller is missing."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None
            with pytest.raises(BuildError, match="PyInstaller not found"):
                mock_builder.validate_build_environment()
    
    def test_validate_spec_file_exists(self, mock_builder):
        """Test validation that .spec file exists."""
        result = mock_builder.validate_spec_file()
        assert result is True
    
    def test_validate_spec_file_missing(self):
        """Test validation failure when .spec file is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            builder = LocalBuilder.__new__(LocalBuilder)
            builder.project_root = Path(temp_dir)
            builder.spec_file = Path(temp_dir) / "missing.spec"
            
            with pytest.raises(BuildError, match="Spec file not found"):
                builder.validate_spec_file()
    
    def test_validate_entry_point_exists(self, mock_builder):
        """Test validation that entry point script exists."""
        result = mock_builder.validate_entry_point()
        assert result is True
    
    def test_validate_entry_point_missing(self, mock_builder):
        """Test validation failure when entry point is missing."""
        # Remove the entry point file
        entry_path = mock_builder.project_root / "server_runner.py"
        entry_path.unlink()
        
        with pytest.raises(BuildError, match="Entry point not found"):
            mock_builder.validate_entry_point()


class TestBuildExecution:
    """Test PyInstaller build execution."""
    
    @pytest.fixture
    def mock_builder(self):
        """Create a mock LocalBuilder for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            spec_content = """
a = Analysis(['server_runner.py'], pathex=['.'], binaries=[], datas=[], hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], win_no_prefer_redirects=False, win_private_assemblies=False, cipher=None, noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [], name='TestApp', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, upx_exclude=[], runtime_tmpdir=None, console=False, disable_windowed_traceback=False, argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None)
"""
            spec_path = Path(temp_dir) / "TestApp.spec"
            spec_path.write_text(spec_content)
            
            entry_path = Path(temp_dir) / "server_runner.py"
            entry_path.write_text("print('Hello World')")
            
            yield LocalBuilder(project_root=temp_dir)
    
    def test_build_command_generation(self, mock_builder):
        """Test generation of PyInstaller command."""
        command = mock_builder.generate_build_command()
        assert isinstance(command, list)
        assert 'pyinstaller' in command[0]
        assert any('.spec' in arg for arg in command)
    
    def test_build_command_with_clean(self, mock_builder):
        """Test build command generation with clean option."""
        command = mock_builder.generate_build_command(clean=True)
        assert '--clean' in command
    
    def test_build_command_with_distpath(self, mock_builder):
        """Test build command generation with custom dist path."""
        custom_path = "/custom/dist"
        command = mock_builder.generate_build_command(distpath=custom_path)
        assert '--distpath' in command
        assert custom_path in command
    
    def test_build_command_with_workpath(self, mock_builder):
        """Test build command generation with custom work path."""
        custom_path = "/custom/work"
        command = mock_builder.generate_build_command(workpath=custom_path)
        assert '--workpath' in command
        assert custom_path in command
    
    @patch('subprocess.run')
    def test_execute_build_success(self, mock_run, mock_builder):
        """Test successful build execution."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Build completed successfully"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Mock executable file creation
        with patch.object(Path, 'exists', return_value=True):
            result = mock_builder.execute_build()
            assert isinstance(result, BuildResult)
            assert result.success is True
            assert result.output == "Build completed successfully"
    
    @patch('subprocess.run')
    def test_execute_build_failure(self, mock_run, mock_builder):
        """Test failed build execution."""
        # Mock failed subprocess run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Build failed with errors"
        mock_run.return_value = mock_result
        
        result = mock_builder.execute_build()
        assert isinstance(result, BuildResult)
        assert result.success is False
        assert result.error == "Build failed with errors"
    
    @patch('subprocess.run')
    def test_execute_build_timeout(self, mock_run, mock_builder):
        """Test build execution timeout."""
        # Mock timeout exception
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=['pyinstaller'], timeout=300)
        
        result = mock_builder.execute_build(timeout=300)
        assert isinstance(result, BuildResult)
        assert result.success is False
        assert "timeout" in result.error.lower()
    
    @patch('subprocess.run')
    def test_execute_build_with_capture_output(self, mock_run, mock_builder):
        """Test build execution with output capture."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Build output"
        mock_result.stderr = "Build warnings"
        mock_run.return_value = mock_result
        
        with patch.object(Path, 'exists', return_value=True):
            result = mock_builder.execute_build(capture_output=True)
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[1]['capture_output'] is True
            assert call_args[1]['text'] is True


class TestBuildResultValidation:
    """Test validation of build results."""
    
    @pytest.fixture
    def mock_builder(self):
        """Create a mock LocalBuilder for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            spec_content = """
a = Analysis(['server_runner.py'], pathex=['.'], binaries=[], datas=[], hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], win_no_prefer_redirects=False, win_private_assemblies=False, cipher=None, noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [], name='TestApp', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, upx_exclude=[], runtime_tmpdir=None, console=False, disable_windowed_traceback=False, argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None)
"""
            spec_path = Path(temp_dir) / "TestApp.spec"
            spec_path.write_text(spec_content)
            
            # Create dist directory and executable
            dist_dir = Path(temp_dir) / "dist"
            dist_dir.mkdir()
            
            # Create platform-specific executable
            if platform.system() == "Windows":
                exe_path = dist_dir / "TestApp.exe"
            else:
                exe_path = dist_dir / "TestApp"
            
            exe_path.write_text("fake executable")
            exe_path.chmod(0o755)
            
            yield LocalBuilder(project_root=temp_dir)
    
    def test_validate_executable_exists(self, mock_builder):
        """Test validation that executable file exists."""
        result = mock_builder.validate_executable()
        assert result is True
    
    def test_validate_executable_missing(self, mock_builder):
        """Test validation failure when executable is missing."""
        # Remove the executable
        dist_dir = mock_builder.project_root / "dist"
        for exe_file in dist_dir.glob("*"):
            exe_file.unlink()
        
        with pytest.raises(BuildError, match="Executable not found"):
            mock_builder.validate_executable()
    
    def test_validate_executable_permissions(self, mock_builder):
        """Test validation of executable permissions."""
        if platform.system() != "Windows":
            result = mock_builder.validate_executable_permissions()
            assert result is True
    
    def test_get_executable_size(self, mock_builder):
        """Test getting executable file size."""
        size = mock_builder.get_executable_size()
        assert isinstance(size, int)
        assert size > 0
    
    def test_get_executable_path(self, mock_builder):
        """Test getting executable file path."""
        path = mock_builder.get_executable_path()
        assert isinstance(path, Path)
        assert path.exists()


class TestCrossPlatformCompatibility:
    """Test cross-platform build compatibility."""
    
    def test_detect_platform(self):
        """Test platform detection."""
        builder = LocalBuilder.__new__(LocalBuilder)
        platform_info = builder.detect_platform()
        assert isinstance(platform_info, dict)
        assert 'system' in platform_info
        assert 'architecture' in platform_info
    
    def test_get_executable_extension_windows(self):
        """Test executable extension detection on Windows."""
        builder = LocalBuilder.__new__(LocalBuilder)
        with patch('platform.system', return_value='Windows'):
            ext = builder.get_executable_extension()
            assert ext == '.exe'
    
    def test_get_executable_extension_unix(self):
        """Test executable extension detection on Unix systems."""
        builder = LocalBuilder.__new__(LocalBuilder)
        with patch('platform.system', return_value='Darwin'):
            ext = builder.get_executable_extension()
            assert ext == ''
        
        with patch('platform.system', return_value='Linux'):
            ext = builder.get_executable_extension()
            assert ext == ''
    
    def test_get_expected_executable_name(self):
        """Test expected executable name generation."""
        builder = LocalBuilder.__new__(LocalBuilder)
        builder.app_name = "TestApp"
        
        with patch('platform.system', return_value='Windows'):
            name = builder.get_expected_executable_name()
            assert name == "TestApp.exe"
        
        with patch('platform.system', return_value='Darwin'):
            name = builder.get_expected_executable_name()
            assert name == "TestApp"


class TestBuildCleanup:
    """Test build cleanup operations."""
    
    @pytest.fixture
    def mock_builder_with_artifacts(self):
        """Create a mock LocalBuilder with build artifacts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create build artifacts
            build_dir = project_root / "build"
            build_dir.mkdir()
            (build_dir / "TestApp").mkdir()
            (build_dir / "TestApp" / "TestApp.spec").write_text("spec content")
            
            dist_dir = project_root / "dist"
            dist_dir.mkdir()
            (dist_dir / "TestApp").write_text("executable")
            
            pycache_dir = project_root / "__pycache__"
            pycache_dir.mkdir()
            (pycache_dir / "test.pyc").write_text("bytecode")
            
            builder = LocalBuilder.__new__(LocalBuilder)
            builder.project_root = project_root
            builder.build_dir = build_dir
            builder.dist_dir = dist_dir
            
            yield builder
    
    def test_clean_build_artifacts(self, mock_builder_with_artifacts):
        """Test cleaning of build artifacts."""
        builder = mock_builder_with_artifacts
        builder.clean_build_artifacts()
        
        assert not builder.build_dir.exists()
        assert not builder.dist_dir.exists()
    
    def test_clean_pycache(self, mock_builder_with_artifacts):
        """Test cleaning of Python cache files."""
        builder = mock_builder_with_artifacts
        builder.clean_pycache()
        
        pycache_dir = builder.project_root / "__pycache__"
        assert not pycache_dir.exists()
    
    def test_clean_all(self, mock_builder_with_artifacts):
        """Test comprehensive cleanup."""
        builder = mock_builder_with_artifacts
        builder.clean_all()
        
        assert not builder.build_dir.exists()
        assert not builder.dist_dir.exists()
        
        pycache_dir = builder.project_root / "__pycache__"
        assert not pycache_dir.exists()


class TestBuildConfiguration:
    """Test build configuration handling."""
    
    def test_load_build_config_from_spec(self):
        """Test loading build configuration from .spec file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            spec_content = """
a = Analysis(['server_runner.py'], pathex=['.'], binaries=[], datas=[], hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], win_no_prefer_redirects=False, win_private_assemblies=False, cipher=None, noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(pyz, a.scripts, [], [], [], [], name='TestApp', debug=False, console=True)
"""
            spec_path = Path(temp_dir) / "TestApp.spec"
            spec_path.write_text(spec_content)
            
            builder = LocalBuilder.__new__(LocalBuilder)
            builder.spec_file = spec_path
            
            config = builder.load_build_config()
            assert isinstance(config, dict)
            assert 'app_name' in config
            assert config['app_name'] == 'TestApp'
    
    def test_get_build_options(self):
        """Test getting build options."""
        builder = LocalBuilder.__new__(LocalBuilder)
        options = builder.get_build_options()
        assert isinstance(options, dict)
        assert 'clean' in options
        assert 'distpath' in options
        assert 'workpath' in options
    
    def test_set_build_option(self):
        """Test setting build options."""
        builder = LocalBuilder.__new__(LocalBuilder)
        builder.set_build_option('clean', True)
        builder.set_build_option('distpath', '/custom/dist')
        
        options = builder.get_build_options()
        assert options['clean'] is True
        assert options['distpath'] == '/custom/dist'


class TestBuildTesting:
    """Test build result testing."""
    
    @pytest.fixture
    def mock_executable(self):
        """Create a mock executable for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_path = Path(temp_dir) / "TestApp"
            exe_script = """#!/usr/bin/env python3
import sys
print("Hello from TestApp")
sys.exit(0)
"""
            exe_path.write_text(exe_script)
            exe_path.chmod(0o755)
            yield exe_path
    
    def test_test_executable_basic(self, mock_executable):
        """Test basic executable testing."""
        builder = LocalBuilder.__new__(LocalBuilder)
        builder.executable_path = mock_executable
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Hello from TestApp"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = builder.test_executable()
            assert result is True
    
    def test_test_executable_failure(self, mock_executable):
        """Test executable testing with failure."""
        builder = LocalBuilder.__new__(LocalBuilder)
        builder.executable_path = mock_executable
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Application error"
            mock_run.return_value = mock_result
            
            result = builder.test_executable()
            assert result is False
    
    def test_test_executable_with_args(self, mock_executable):
        """Test executable testing with command line arguments."""
        builder = LocalBuilder.__new__(LocalBuilder)
        builder.executable_path = mock_executable
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Test with args"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = builder.test_executable(args=['--test', 'arg'])
            assert result is True
            
            # Verify args were passed
            call_args = mock_run.call_args[0][0]
            assert '--test' in call_args
            assert 'arg' in call_args


class TestBuildReporting:
    """Test build reporting and metrics."""
    
    def test_generate_build_report(self):
        """Test generation of build report."""
        builder = LocalBuilder.__new__(LocalBuilder)
        
        # Mock build result
        build_result = BuildResult(
            success=True,
            executable_path="/dist/TestApp",
            build_time=45.2,
            output="Build completed successfully",
            error=""
        )
        
        report = builder.generate_build_report(build_result)
        assert isinstance(report, dict)
        assert 'success' in report
        assert 'build_time' in report
        assert 'executable_path' in report
        assert 'platform_info' in report
    
    def test_get_build_metrics(self):
        """Test getting build metrics."""
        builder = LocalBuilder.__new__(LocalBuilder)
        
        build_result = BuildResult(
            success=True,
            executable_path="/dist/TestApp",
            build_time=45.2,
            output="Build completed",
            error=""
        )
        
        with patch.object(builder, 'get_executable_size', return_value=1024000):
            metrics = builder.get_build_metrics(build_result)
            assert isinstance(metrics, dict)
            assert 'build_time' in metrics
            assert 'executable_size' in metrics
            assert metrics['executable_size'] == 1024000
    
    def test_format_build_summary(self):
        """Test formatting of build summary."""
        builder = LocalBuilder.__new__(LocalBuilder)
        
        build_result = BuildResult(
            success=True,
            executable_path="/dist/TestApp",
            build_time=45.2,
            output="Build completed",
            error=""
        )
        
        summary = builder.format_build_summary(build_result)
        assert isinstance(summary, str)
        assert "SUCCESS" in summary or "success" in summary
        assert "45.2" in summary


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])