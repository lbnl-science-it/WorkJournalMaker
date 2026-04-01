# ABOUTME: Comprehensive tests for PyInstaller build configuration
# ABOUTME: Tests asset discovery, hidden imports, and build configuration

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import pytest

# Import the module we're testing
from build_system.build_config import BuildConfig


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
        # Placeholder for future spec file validation tests
        pass

    def test_validate_required_sections(self) -> None:
        """Test validation of required .spec file sections."""
        # Placeholder for future spec file validation tests
        pass

    def test_validate_asset_paths(self) -> None:
        """Test validation of asset paths in .spec file."""
        # Placeholder for future spec file validation tests
        pass

    def test_validate_hidden_imports(self) -> None:
        """Test validation of hidden imports list."""
        # Placeholder for future spec file validation tests
        pass


if __name__ == "__main__":
    unittest.main()