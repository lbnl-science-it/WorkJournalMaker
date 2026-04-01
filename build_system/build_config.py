# ABOUTME: PyInstaller build configuration for WorkJournalMaker
# ABOUTME: Provides asset discovery, hidden import lists, and build configuration

"""
PyInstaller build configuration.

This module provides build configuration management for PyInstaller-based
builds of the WorkJournalMaker desktop application. It handles asset discovery,
dependency analysis, and build configuration.

Key Features:
- Automatic asset discovery (static files, templates)
- Hidden import detection for complex dependencies
- Cross-platform build configuration
- Build validation and verification

Usage:
    config = BuildConfig(project_root="/path/to/project")
    assets = config.get_static_assets()
    hidden_imports = config.get_hidden_imports()
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import logging

# Setup module logger
logger = logging.getLogger(__name__)


class BuildConfigError(Exception):
    """Exception raised for build configuration errors."""
    pass


class BuildConfig:
    """Configuration management for PyInstaller builds."""
    
    def __init__(self,
                 project_root: str,
                 app_name: str = "WorkJournalMaker",
                 entry_point: str = "server_runner.py",
                 console: bool = False,
                 one_file: bool = True,
                 debug: bool = False,
                 icon_file: Optional[str] = None):
        """Initialize build configuration.
        
        Args:
            project_root: Path to project root directory
            app_name: Application name for the executable
            entry_point: Entry point script name
            console: Whether to show console window
            one_file: Whether to create a single executable
            debug: Whether to enable debug mode
            icon_file: Path to icon file (optional)
            
        Raises:
            BuildConfigError: If configuration is invalid
        """
        self.project_root = Path(project_root)
        self.app_name = app_name
        self.entry_point = entry_point
        self.console = console
        self.one_file = one_file
        self.debug = debug
        self.icon_file = icon_file
        
        # Validate configuration
        self._validate_configuration()
    
    def _validate_configuration(self) -> None:
        """Validate the build configuration.
        
        Raises:
            BuildConfigError: If configuration is invalid
        """
        if not self.project_root.exists():
            raise BuildConfigError(f"Project root does not exist: {self.project_root}")
        
        if not self.project_root.is_dir():
            raise BuildConfigError(f"Project root is not a directory: {self.project_root}")
        
        # Check entry point exists
        entry_path = self.project_root / self.entry_point
        if not entry_path.exists():
            raise BuildConfigError(f"Entry point does not exist: {entry_path}")
        
        # Check icon file if specified
        if self.icon_file:
            icon_path = self.project_root / self.icon_file
            if not icon_path.exists():
                logger.warning(f"Icon file does not exist: {icon_path}")
    
    def get_static_assets(self) -> List[Tuple[str, str]]:
        """Get list of static assets to include in build.
        
        Returns:
            List of (source_path, destination_path) tuples
        """
        assets = []
        
        # Web static files
        web_static = self.project_root / "web" / "static"
        if web_static.exists() and web_static.is_dir():
            assets.append((str(web_static), "web/static"))
        
        # Web templates
        web_templates = self.project_root / "web" / "templates"
        if web_templates.exists() and web_templates.is_dir():
            assets.append((str(web_templates), "web/templates"))
        
        # Configuration files
        config_candidates = [
            "config.yaml",
            "config.json",
            "settings.yaml",
            "settings.json"
        ]
        for config_file in config_candidates:
            config_path = self.project_root / config_file
            if config_path.exists():
                assets.append((str(config_path), config_file))
        
        return assets
    
    def get_template_files(self) -> List[str]:
        """Get list of template files for inclusion.
        
        Returns:
            List of template file paths relative to project root
        """
        templates = []
        
        templates_dir = self.project_root / "web" / "templates"
        if templates_dir.exists() and templates_dir.is_dir():
            for template_file in templates_dir.rglob("*.html"):
                rel_path = template_file.relative_to(self.project_root)
                templates.append(str(rel_path))
        
        return templates
    
    def get_hidden_imports(self) -> List[str]:
        """Get list of hidden imports required by the application.
        
        Returns:
            List of module names to import
        """
        return [
            # Uvicorn server components
            'uvicorn.lifespan.on',
            'uvicorn.lifespan.off',
            'uvicorn.protocols.websockets.auto',
            'uvicorn.protocols.websockets.websockets_impl',
            'uvicorn.protocols.http.auto',
            'uvicorn.protocols.http.h11_impl',
            'uvicorn.loops.auto',
            'uvicorn.loops.asyncio',
            
            # FastAPI components
            'fastapi.routing',
            'fastapi.responses',
            'fastapi.encoders',
            'fastapi.exceptions',
            
            # Starlette components
            'starlette.routing',
            'starlette.responses',
            'starlette.middleware',
            'starlette.staticfiles',
            
            # SQLAlchemy components
            'sqlalchemy.ext.declarative',
            'sqlalchemy.sql.default_comparator',
            'aiosqlite',
            
            # Template engine
            'jinja2.ext',
            
            # Google GenAI (if used)
            'google.genai',
            'google.genai.models',
            'google.genai.client',
            'google.auth',
            'google.oauth2',
            
            # AWS Bedrock (if used)
            'boto3',
            'botocore',
            'botocore.client',
            'botocore.session',
            
            # Additional common imports
            'asyncio',
            'concurrent.futures',
            'multiprocessing',
            'queue'
        ]
    
    def get_excluded_modules(self) -> List[str]:
        """Get list of modules to exclude from the build.
        
        Returns:
            List of module names to exclude
        """
        return [
            # GUI toolkits (not needed for web app)
            'tkinter',
            '_tkinter',
            
            # Plotting libraries (heavy and not needed)
            'matplotlib',
            'matplotlib.pyplot',
            
            # Qt libraries (not needed)
            'PyQt5',
            'PyQt6',
            'PySide2',
            'PySide6',
            
            # Development and testing tools
            'pytest',
            'pytest_cov',
            'pytest_mock',
            'coverage',
            'black',
            'flake8',
            'mypy',
            
            # Documentation tools
            'sphinx',
            'docutils',
            
            # Jupyter/IPython (development tools)
            'jupyter',
            'notebook',
            'ipython',
            'IPython',
            
            # Large optional libraries
            'pandas',
            'numpy',
            'scipy',
            'sklearn',
            'tensorflow',
            'torch',
            'cv2',
            
            # Development servers (not needed in production)
            'werkzeug.debug',
            'flask.debug'
        ]


def create_build_config(project_root: str, **kwargs) -> BuildConfig:
    """Convenience function to create a build configuration.

    Args:
        project_root: Path to project root directory
        **kwargs: Additional configuration options

    Returns:
        Configured BuildConfig instance
    """
    return BuildConfig(project_root=project_root, **kwargs)