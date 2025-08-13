# ABOUTME: PyInstaller build configuration and .spec file generation for WorkJournalMaker
# ABOUTME: Provides cross-platform build configuration with asset discovery and spec generation

"""
PyInstaller build configuration and .spec file generation.

This module provides comprehensive build configuration management for PyInstaller-based
builds of the WorkJournalMaker desktop application. It handles asset discovery,
dependency analysis, and .spec file generation for cross-platform builds.

Key Features:
- Automatic asset discovery (static files, templates)
- Hidden import detection for complex dependencies
- Cross-platform build configuration
- Dynamic .spec file generation
- Build validation and verification

Usage:
    config = BuildConfig(project_root="/path/to/project")
    assets = config.get_static_assets()
    
    generator = PyInstallerSpecGenerator(config)
    spec_content = generator.generate_complete_spec()
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


class PyInstallerSpecGenerator:
    """Generator for PyInstaller .spec files."""
    
    def __init__(self, config: BuildConfig):
        """Initialize the spec generator.
        
        Args:
            config: Build configuration
        """
        self.config = config
    
    def validate_config(self) -> bool:
        """Validate that the configuration is suitable for spec generation.
        
        Returns:
            True if configuration is valid
            
        Raises:
            BuildConfigError: If configuration is invalid
        """
        # Check that entry point exists
        entry_path = self.config.project_root / self.config.entry_point
        if not entry_path.exists():
            raise BuildConfigError(f"Entry point not found: {entry_path}")
        
        # Check that we have required assets
        assets = self.config.get_static_assets()
        for source_path, _ in assets:
            if not Path(source_path).exists():
                logger.warning(f"Asset path not found: {source_path}")
        
        return True
    
    def generate_analysis_section(self) -> str:
        """Generate the Analysis section of the .spec file.
        
        Returns:
            Analysis section as string
        """
        hidden_imports = self.config.get_hidden_imports()
        excluded_modules = self.config.get_excluded_modules()
        static_assets = self.config.get_static_assets()
        
        # Format hidden imports
        hidden_imports_str = ",\n    ".join(f"'{imp}'" for imp in hidden_imports)
        
        # Format excluded modules
        excluded_str = ",\n    ".join(f"'{mod}'" for mod in excluded_modules)
        
        # Format data files
        datas = []
        for source_path, dest_path in static_assets:
            datas.append(f"('{source_path}', '{dest_path}')")
        datas_str = ",\n    ".join(datas)
        
        return f"""a = Analysis(
    ['{self.config.entry_point}'],
    pathex=['{self.config.project_root}'],
    binaries=[],
    datas=[
        {datas_str}
    ],
    hiddenimports=[
        {hidden_imports_str}
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        {excluded_str}
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)"""
    
    def generate_pyz_section(self) -> str:
        """Generate the PYZ section of the .spec file.
        
        Returns:
            PYZ section as string
        """
        return "pyz = PYZ(a.pure, a.zipped_data, cipher=None)"
    
    def generate_exe_section(self) -> str:
        """Generate the EXE section of the .spec file.
        
        Returns:
            EXE section as string
        """
        icon_line = ""
        if self.config.icon_file:
            icon_line = f"    icon='{self.config.icon_file}',"
        
        if self.config.one_file:
            # One-file mode
            return f"""exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{self.config.app_name}',
    debug={str(self.config.debug)},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={str(self.config.console)},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,{icon_line}
)"""
        else:
            # One-directory mode
            return f"""exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{self.config.app_name}',
    debug={str(self.config.debug)},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={str(self.config.console)},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,{icon_line}
)"""
    
    def generate_collect_section(self) -> str:
        """Generate the COLLECT section of the .spec file.
        
        Returns:
            COLLECT section as string (empty for one-file mode)
        """
        if self.config.one_file:
            return ""
        
        return f"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{self.config.app_name}',
)"""
    
    def generate_complete_spec(self) -> str:
        """Generate the complete .spec file content.
        
        Returns:
            Complete .spec file content
        """
        analysis_section = self.generate_analysis_section()
        pyz_section = self.generate_pyz_section()
        exe_section = self.generate_exe_section()
        collect_section = self.generate_collect_section()
        
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for {self.config.app_name}
# Generated automatically by build_config.py


{analysis_section}

{pyz_section}

{exe_section}"""
        
        if collect_section:
            spec_content += collect_section
        
        return spec_content
    
    def write_spec_file(self, output_path: Optional[str] = None) -> str:
        """Write the .spec file to disk.
        
        Args:
            output_path: Output file path. If None, uses default location.
            
        Returns:
            Path to written .spec file
        """
        if output_path is None:
            output_path = self.config.project_root / f"{self.config.app_name}.spec"
        else:
            output_path = Path(output_path)
        
        spec_content = self.generate_complete_spec()
        
        try:
            output_path.write_text(spec_content, encoding='utf-8')
            logger.info(f"Spec file written to: {output_path}")
            return str(output_path)
        except Exception as e:
            raise BuildConfigError(f"Failed to write spec file: {e}")


def create_build_config(project_root: str, **kwargs) -> BuildConfig:
    """Convenience function to create a build configuration.
    
    Args:
        project_root: Path to project root directory
        **kwargs: Additional configuration options
        
    Returns:
        Configured BuildConfig instance
    """
    return BuildConfig(project_root=project_root, **kwargs)


def generate_spec_file(project_root: str, 
                      output_path: Optional[str] = None,
                      **config_kwargs) -> str:
    """Convenience function to generate a .spec file.
    
    Args:
        project_root: Path to project root directory
        output_path: Output file path for .spec file
        **config_kwargs: Additional configuration options
        
    Returns:
        Path to generated .spec file
    """
    config = create_build_config(project_root, **config_kwargs)
    generator = PyInstallerSpecGenerator(config)
    generator.validate_config()
    return generator.write_spec_file(output_path)