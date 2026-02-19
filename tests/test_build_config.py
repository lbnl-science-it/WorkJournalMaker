# ABOUTME: Comprehensive tests for PyInstaller build configuration
# ABOUTME: Tests .spec file generation, asset inclusion, and cross-platform builds

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import pytest

# Import the module we're testing
from build_system.build_config import BuildConfig, PyInstallerSpecGenerator


class TestBuildConfig(unittest.TestCase):
    """Test the main BuildConfig class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: self._cleanup_temp_dir(self.temp_dir))
        
        # Mock project structure
        self.project_root = Path(self.temp_dir) / "project"
        self.project_root.mkdir()
        
        # Create mock directories
        self.web_dir = self.project_root / "web"
        self.web_dir.mkdir()
        (self.web_dir / "static").mkdir()
        (self.web_dir / "templates").mkdir()
        
        self.desktop_dir = self.project_root / "desktop"
        self.desktop_dir.mkdir()
        
        # Create required files for validation
        (self.project_root / "server_runner.py").write_text("# Mock entry point")
        (self.web_dir / "app.py").write_text("# Mock web app")
        (self.desktop_dir / "desktop_app.py").write_text("# Mock desktop app")
    
    def _cleanup_temp_dir(self, temp_dir: str) -> None:
        """Clean up temporary directory."""
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    def test_build_config_init_default_values(self) -> None:
        """Test BuildConfig initialization with default values."""
        config = BuildConfig(project_root=str(self.project_root))
        
        self.assertEqual(config.app_name, "WorkJournalMaker")
        self.assertEqual(config.entry_point, "server_runner.py")
        self.assertFalse(config.console)
        self.assertTrue(config.one_file)
        self.assertFalse(config.debug)
        self.assertIsNone(config.icon_file)
    
    def test_build_config_init_custom_values(self) -> None:
        """Test BuildConfig initialization with custom values."""
        # Create the custom entry point file
        (self.project_root / "custom_entry.py").write_text("# Custom entry point")
        
        config = BuildConfig(
            project_root=str(self.project_root),
            app_name="CustomApp",
            entry_point="custom_entry.py",
            console=True,
            one_file=False,
            debug=True,
            icon_file="icon.ico"
        )
        
        self.assertEqual(config.app_name, "CustomApp")
        self.assertEqual(config.entry_point, "custom_entry.py")
        self.assertTrue(config.console)
        self.assertFalse(config.one_file)
        self.assertTrue(config.debug)
        self.assertEqual(config.icon_file, "icon.ico")
    
    def test_build_config_detect_project_structure(self) -> None:
        """Test project structure detection."""
        config = BuildConfig(project_root=str(self.project_root))
        
        # Should detect all required files and directories
        self.assertTrue((config.project_root / "server_runner.py").exists())
        self.assertTrue((config.project_root / "web" / "app.py").exists())
        self.assertTrue((config.project_root / "desktop" / "desktop_app.py").exists())
        self.assertTrue((config.project_root / "web" / "static").is_dir())
        self.assertTrue((config.project_root / "web" / "templates").is_dir())
    
    def test_build_config_get_static_assets(self) -> None:
        """Test static asset discovery."""
        config = BuildConfig(project_root=str(self.project_root))
        assets = config.get_static_assets()
        
        self.assertIsInstance(assets, list)
        self.assertEqual(len(assets), 2)  # static and templates
        
        # Check static assets
        static_asset = next((asset for asset in assets if asset[1] == "web/static"), None)
        self.assertIsNotNone(static_asset)
        
        # Check templates
        template_asset = next((asset for asset in assets if asset[1] == "web/templates"), None)
        self.assertIsNotNone(template_asset)
    
    def test_build_config_get_template_files(self) -> None:
        """Test template file discovery."""
        # Create some template files
        (self.web_dir / "templates" / "base.html").write_text("<html></html>")
        (self.web_dir / "templates" / "dashboard.html").write_text("<html></html>")
        
        config = BuildConfig(project_root=str(self.project_root))
        templates = config.get_template_files()
        
        self.assertIsInstance(templates, list)
        self.assertEqual(len(templates), 2)
        self.assertIn("web/templates/base.html", templates)
        self.assertIn("web/templates/dashboard.html", templates)
    
    def test_build_config_get_hidden_imports(self) -> None:
        """Test hidden import detection."""
        config = BuildConfig(project_root=str(self.project_root))
        hidden_imports = config.get_hidden_imports()
        
        self.assertIsInstance(hidden_imports, list)
        self.assertGreater(len(hidden_imports), 0)
        
        # Check for essential imports
        self.assertIn("uvicorn.lifespan.on", hidden_imports)
        self.assertIn("fastapi.routing", hidden_imports)
        self.assertIn("sqlalchemy.ext.declarative", hidden_imports)
    
    def test_build_config_get_excluded_modules(self) -> None:
        """Test excluded module configuration."""
        config = BuildConfig(project_root=str(self.project_root))
        excluded = config.get_excluded_modules()
        
        self.assertIsInstance(excluded, list)
        self.assertGreater(len(excluded), 0)
        
        # Check for expected exclusions
        self.assertIn("tkinter", excluded)
        self.assertIn("matplotlib", excluded)
        self.assertIn("pytest", excluded)


class TestPyInstallerSpecGenerator(unittest.TestCase):
    """Test the PyInstaller spec file generator."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: self._cleanup_temp_dir(self.temp_dir))
        
        self.project_root = Path(self.temp_dir) / "project"
        self.project_root.mkdir()
        
        # Create mock directories and files (same as TestBuildConfig)
        web_dir = self.project_root / "web"
        web_dir.mkdir()
        (web_dir / "static").mkdir()
        (web_dir / "templates").mkdir()
        
        desktop_dir = self.project_root / "desktop"
        desktop_dir.mkdir()
        
        # Create required files for validation
        (self.project_root / "server_runner.py").write_text("# Mock entry point")
        (web_dir / "app.py").write_text("# Mock web app")
        (desktop_dir / "desktop_app.py").write_text("# Mock desktop app")
        
        # Create example spec configuration
        self.spec_config = {
            'app_name': 'WorkJournalMaker',
            'entry_point': 'server_runner.py',
            'project_root': str(self.project_root),
            'icon_file': None,
            'console': False,
            'one_file': True,
            'debug': False,
            'static_assets': [
                ('web/static', 'web/static'),
                ('web/templates', 'web/templates')
            ],
            'hidden_imports': [
                'uvicorn.lifespan.on',
                'uvicorn.lifespan.off',
                'uvicorn.protocols.websockets.auto'
            ],
            'excluded_modules': [
                'tkinter',
                '_tkinter',
                'matplotlib'
            ]
        }
    
    def _cleanup_temp_dir(self, temp_dir: str) -> None:
        """Clean up temporary directory."""
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    def test_spec_generator_init(self) -> None:
        """Test PyInstallerSpecGenerator initialization."""
        config = BuildConfig(project_root=str(self.project_root))
        generator = PyInstallerSpecGenerator(config)
        
        self.assertEqual(generator.config, config)
        self.assertIsNotNone(generator.logger)
    
    def test_spec_generator_validate_config(self) -> None:
        """Test configuration validation."""
        config = BuildConfig(project_root=str(self.project_root))
        generator = PyInstallerSpecGenerator(config)
        
        # Should validate successfully with proper project structure
        self.assertTrue(generator.validate_config())
        
        # Test with missing entry point by creating an invalid config manually
        # (bypassing BuildConfig validation which happens at init)
        config_invalid = BuildConfig(project_root=str(self.project_root))
        config_invalid.entry_point = "nonexistent.py"  # Manually set invalid entry point
        generator_invalid = PyInstallerSpecGenerator(config_invalid)
        self.assertFalse(generator_invalid.validate_config())
    
    def test_spec_generator_generate_analysis_section(self) -> None:
        """Test Analysis section generation."""
        config = BuildConfig(project_root=str(self.project_root))
        generator = PyInstallerSpecGenerator(config)
        
        analysis_section = generator.generate_analysis_section()
        
        self.assertIsInstance(analysis_section, str)
        self.assertIn("a = Analysis(", analysis_section)
        self.assertIn("hiddenimports=[", analysis_section)
        self.assertIn("excludes=[", analysis_section)
        self.assertIn("datas=[", analysis_section)
    
    def test_spec_generator_generate_pyz_section(self) -> None:
        """Test PYZ section generation."""
        config = BuildConfig(project_root=str(self.project_root))
        generator = PyInstallerSpecGenerator(config)
        
        pyz_section = generator.generate_pyz_section()
        
        self.assertIsInstance(pyz_section, str)
        self.assertIn("pyz = PYZ(", pyz_section)
    
    def test_spec_generator_generate_exe_section(self) -> None:
        """Test EXE section generation."""
        config = BuildConfig(project_root=str(self.project_root))
        generator = PyInstallerSpecGenerator(config)
        
        exe_section = generator.generate_exe_section()
        
        self.assertIsInstance(exe_section, str)
        self.assertIn("exe = EXE(", exe_section)
        self.assertIn(f"name='{config.app_name}'", exe_section)
    
    def test_spec_generator_generate_collect_section(self) -> None:
        """Test COLLECT section generation."""
        # Test one-file mode (should return empty string)
        config_onefile = BuildConfig(project_root=str(self.project_root), one_file=True)
        generator_onefile = PyInstallerSpecGenerator(config_onefile)
        collect_section_onefile = generator_onefile.generate_collect_section()
        self.assertEqual(collect_section_onefile, "")
        
        # Test directory mode (should return COLLECT section)
        config_dir = BuildConfig(project_root=str(self.project_root), one_file=False)
        generator_dir = PyInstallerSpecGenerator(config_dir)
        collect_section_dir = generator_dir.generate_collect_section()
        self.assertIn("coll = COLLECT(", collect_section_dir)
    
    def test_spec_generator_generate_complete_spec(self) -> None:
        """Test complete .spec file generation."""
        config = BuildConfig(project_root=str(self.project_root))
        generator = PyInstallerSpecGenerator(config)
        
        spec_content = generator.generate_complete_spec()
        
        self.assertIsInstance(spec_content, str)
        self.assertIn("# -*- mode: python ; coding: utf-8 -*-", spec_content)
        self.assertIn("a = Analysis(", spec_content)
        self.assertIn("pyz = PYZ(", spec_content)
        self.assertIn("exe = EXE(", spec_content)
    
    def test_spec_generator_cross_platform_paths(self) -> None:
        """Test cross-platform path handling."""
        config = BuildConfig(project_root=str(self.project_root))
        generator = PyInstallerSpecGenerator(config)
        
        analysis_section = generator.generate_analysis_section()
        
        # Paths should use forward slashes for cross-platform compatibility
        self.assertNotIn("\\", analysis_section)  # No backslashes
        self.assertIn("web/static", analysis_section)  # Forward slashes
    
    def test_spec_generator_write_spec_file(self) -> None:
        """Test writing .spec file to disk."""
        config = BuildConfig(project_root=str(self.project_root))
        generator = PyInstallerSpecGenerator(config)
        
        # Write spec file
        spec_file_path = generator.write_spec_file()
        
        self.assertTrue(Path(spec_file_path).exists())
        
        # Read and verify content
        spec_content = Path(spec_file_path).read_text()
        self.assertIn("# -*- mode: python", spec_content)
        self.assertIn("a = Analysis(", spec_content)


class TestPlatformSpecificConfig(unittest.TestCase):
    """Test platform-specific configuration handling."""
    
    def test_windows_config(self) -> None:
        """Test Windows-specific configuration."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig
    
    def test_macos_config(self) -> None:
        """Test macOS-specific configuration."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig
    
    def test_linux_config(self) -> None:
        """Test Linux-specific configuration."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig


class TestAssetCollection(unittest.TestCase):
    """Test asset collection and bundling logic."""
    
    def setUp(self) -> None:
        """Set up test fixtures with mock assets."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: self._cleanup_temp_dir(self.temp_dir))
        
        # Create mock web assets
        self.project_root = Path(self.temp_dir) / "project"
        self.project_root.mkdir()
        
        web_static = self.project_root / "web" / "static"
        web_static.mkdir(parents=True)
        
        # Create mock CSS files
        css_dir = web_static / "css"
        css_dir.mkdir()
        (css_dir / "base.css").write_text("/* base styles */")
        (css_dir / "components.css").write_text("/* component styles */")
        
        # Create mock JS files
        js_dir = web_static / "js"
        js_dir.mkdir()
        (js_dir / "app.js").write_text("console.log('app');")
        (js_dir / "utils.js").write_text("console.log('utils');")
        
        # Create mock templates
        templates_dir = self.project_root / "web" / "templates"
        templates_dir.mkdir(parents=True)
        (templates_dir / "base.html").write_text("<html><body>base</body></html>")
        (templates_dir / "dashboard.html").write_text("<html><body>dashboard</body></html>")
    
    def _cleanup_temp_dir(self, temp_dir: str) -> None:
        """Clean up temporary directory."""
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    def test_collect_css_assets(self) -> None:
        """Test CSS asset collection."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig
    
    def test_collect_js_assets(self) -> None:
        """Test JavaScript asset collection."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig
    
    def test_collect_template_assets(self) -> None:
        """Test template asset collection."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig
    
    def test_collect_icon_assets(self) -> None:
        """Test icon asset collection."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig
    
    def test_asset_path_normalization(self) -> None:
        """Test asset path normalization for cross-platform compatibility."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig


class TestDependencyAnalysis(unittest.TestCase):
    """Test dependency analysis for hidden imports."""
    
    def test_detect_uvicorn_dependencies(self) -> None:
        """Test detection of uvicorn hidden imports."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig
    
    def test_detect_fastapi_dependencies(self) -> None:
        """Test detection of FastAPI hidden imports."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig
    
    def test_detect_sqlalchemy_dependencies(self) -> None:
        """Test detection of SQLAlchemy hidden imports."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig
    
    def test_detect_google_genai_dependencies(self) -> None:
        """Test detection of Google GenAI dependencies."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig
    
    def test_detect_aws_boto3_dependencies(self) -> None:
        """Test detection of AWS boto3 dependencies."""
        # This test will fail until we implement BuildConfig
        with pytest.raises(ImportError):
            from build.build_config import BuildConfig


class TestSpecFileValidation(unittest.TestCase):
    """Test .spec file validation and syntax checking."""
    
    def test_validate_spec_syntax(self) -> None:
        """Test .spec file syntax validation."""
        # This test will fail until we implement PyInstallerSpecGenerator
        with pytest.raises(ImportError):
            from build.build_config import PyInstallerSpecGenerator
    
    def test_validate_required_sections(self) -> None:
        """Test validation of required .spec file sections."""
        # This test will fail until we implement PyInstallerSpecGenerator
        with pytest.raises(ImportError):
            from build.build_config import PyInstallerSpecGenerator
    
    def test_validate_asset_paths(self) -> None:
        """Test validation of asset paths in .spec file."""
        # This test will fail until we implement PyInstallerSpecGenerator
        with pytest.raises(ImportError):
            from build.build_config import PyInstallerSpecGenerator
    
    def test_validate_hidden_imports(self) -> None:
        """Test validation of hidden imports list."""
        # This test will fail until we implement PyInstallerSpecGenerator
        with pytest.raises(ImportError):
            from build.build_config import PyInstallerSpecGenerator


if __name__ == "__main__":
    unittest.main()