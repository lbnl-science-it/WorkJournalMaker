# ABOUTME: PyInstaller build configuration for cross-platform desktop packaging
# ABOUTME: Handles asset discovery, dependency analysis, and .spec file generation

import os
import sys
import platform
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set
import logging


class BuildConfig:
    """Main build configuration class for PyInstaller packaging.
    
    Handles project structure analysis, asset discovery, dependency detection,
    and cross-platform configuration management.
    """
    
    def __init__(
        self,
        project_root: Optional[str] = None,
        app_name: str = "WorkJournalMaker",
        entry_point: str = "server_runner.py",
        console: bool = False,
        one_file: bool = True,
        debug: bool = False,
        icon_file: Optional[str] = None
    ) -> None:
        """Initialize BuildConfig.
        
        Args:
            project_root: Root directory of the project (auto-detected if None)
            app_name: Name of the application executable
            entry_point: Main entry point script
            console: Whether to show console window
            one_file: Whether to create a single executable file
            debug: Whether to enable debug mode
            icon_file: Path to application icon file
            
        Raises:
            ValueError: If project structure is invalid
        """
        self.project_root = Path(project_root) if project_root else self._detect_project_root()
        self.app_name = app_name
        self.entry_point = entry_point
        self.console = console
        self.one_file = one_file
        self.debug = debug
        self.icon_file = icon_file
        
        # Platform detection
        self.platform = platform.system().lower()
        self.is_windows = self.platform == "windows"
        self.is_macos = self.platform == "darwin"
        self.is_linux = self.platform == "linux"
        
        # Validate project structure
        self._validate_project_structure()
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
    
    def _detect_project_root(self) -> Path:
        """Auto-detect the project root directory.
        
        Returns:
            Path to project root
            
        Raises:
            ValueError: If project root cannot be detected
        """
        # Start from current directory and look for key project files
        current = Path.cwd()
        
        while current != current.parent:
            # Look for key project indicators
            if any((current / indicator).exists() for indicator in [
                "server_runner.py",
                "work_journal_summarizer.py",
                "web/app.py",
                "desktop/desktop_app.py"
            ]):
                return current
            current = current.parent
        
        raise ValueError("Could not detect project root directory")
    
    def _validate_project_structure(self) -> None:
        """Validate that the project has the expected structure.
        
        Raises:
            ValueError: If required components are missing
        """
        required_files = [
            self.entry_point,
            "web/app.py",
            "desktop/desktop_app.py"
        ]
        
        required_dirs = [
            "web",
            "desktop",
            "web/static",
            "web/templates"
        ]
        
        missing_files = []
        missing_dirs = []
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.is_dir():
                missing_dirs.append(dir_path)
        
        if missing_files or missing_dirs:
            error_msg = "Invalid project structure:"
            if missing_files:
                error_msg += f" Missing files: {missing_files}"
            if missing_dirs:
                error_msg += f" Missing directories: {missing_dirs}"
            raise ValueError(error_msg)
    
    def get_static_assets(self) -> List[Tuple[str, str]]:
        """Get list of static assets to include in the build.
        
        Returns:
            List of (source_path, dest_path) tuples for PyInstaller
        """
        assets = []
        
        # Web static assets
        static_dir = self.project_root / "web" / "static"
        if static_dir.exists():
            assets.append((str(static_dir), "web/static"))
        
        # Web templates
        templates_dir = self.project_root / "web" / "templates"
        if templates_dir.exists():
            assets.append((str(templates_dir), "web/templates"))
        
        return assets
    
    def get_template_files(self) -> List[str]:
        """Get list of template files.
        
        Returns:
            List of template file paths
        """
        templates = []
        templates_dir = self.project_root / "web" / "templates"
        
        if templates_dir.exists():
            for template_file in templates_dir.rglob("*.html"):
                templates.append(str(template_file.relative_to(self.project_root)))
        
        return templates
    
    def get_hidden_imports(self) -> List[str]:
        """Get list of hidden imports required for the application.
        
        Returns:
            List of module names to include as hidden imports
        """
        hidden_imports = []
        
        # Uvicorn hidden imports
        hidden_imports.extend([
            "uvicorn.lifespan.on",
            "uvicorn.lifespan.off",
            "uvicorn.protocols.websockets.auto",
            "uvicorn.protocols.websockets.websockets_impl",
            "uvicorn.protocols.http.auto",
            "uvicorn.protocols.http.h11_impl",
            "uvicorn.loops.auto",
            "uvicorn.loops.asyncio"
        ])
        
        # FastAPI hidden imports
        hidden_imports.extend([
            "fastapi.routing",
            "fastapi.responses",
            "fastapi.encoders",
            "fastapi.exceptions",
            "starlette.routing",
            "starlette.responses",
            "starlette.middleware",
            "starlette.staticfiles"
        ])
        
        # SQLAlchemy hidden imports
        hidden_imports.extend([
            "sqlalchemy.ext.declarative",
            "sqlalchemy.sql.default_comparator",
            "aiosqlite"
        ])
        
        # Jinja2 hidden imports
        hidden_imports.extend([
            "jinja2.ext"
        ])
        
        # Google GenAI (if available)
        try:
            import google.genai
            hidden_imports.extend([
                "google.genai",
                "google.genai.models",
                "google.genai.client",
                "google.auth",
                "google.oauth2"
            ])
        except ImportError:
            pass
        
        # AWS Boto3 (if available)
        try:
            import boto3
            hidden_imports.extend([
                "boto3",
                "botocore",
                "botocore.client",
                "botocore.session"
            ])
        except ImportError:
            pass
        
        return hidden_imports
    
    def get_excluded_modules(self) -> List[str]:
        """Get list of modules to exclude from the build.
        
        Returns:
            List of module names to exclude
        """
        excluded = []
        
        # GUI frameworks not needed for server app
        excluded.extend([
            "tkinter",
            "_tkinter",
            "matplotlib",
            "matplotlib.pyplot",
            "PyQt5",
            "PyQt6",
            "PySide2",
            "PySide6"
        ])
        
        # Development and testing tools
        excluded.extend([
            "pytest",
            "pytest_cov",
            "pytest_mock",
            "coverage",
            "black",
            "flake8",
            "mypy"
        ])
        
        # Documentation tools
        excluded.extend([
            "sphinx",
            "jupyter",
            "notebook",
            "ipython"
        ])
        
        return excluded
    
    def get_platform_specific_config(self) -> Dict[str, Any]:
        """Get platform-specific configuration options.
        
        Returns:
            Dictionary of platform-specific PyInstaller options
        """
        config = {}
        
        if self.is_windows:
            config.update({
                "console": self.console,
                "windowed": not self.console,
                "version_file": None,  # Could add version resource file
                "manifest": None       # Could add manifest file
            })
        
        elif self.is_macos:
            config.update({
                "console": self.console,
                "windowed": not self.console,
                "info_plist": None,    # Could add Info.plist customization
                "bundle_identifier": f"com.workjournal.{self.app_name.lower()}"
            })
        
        else:  # Linux and other Unix-like systems
            config.update({
                "console": True  # Linux typically uses console
            })
        
        return config


class PyInstallerSpecGenerator:
    """Generates PyInstaller .spec files from build configuration."""
    
    def __init__(self, build_config: BuildConfig) -> None:
        """Initialize the spec generator.
        
        Args:
            build_config: BuildConfig instance with project configuration
        """
        self.config = build_config
        self.logger = logging.getLogger(__name__)
    
    def validate_config(self) -> bool:
        """Validate the build configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check entry point exists
            entry_point_path = self.config.project_root / self.config.entry_point
            if not entry_point_path.exists():
                self.logger.error(f"Entry point not found: {self.config.entry_point}")
                return False
            
            # Check static assets exist
            assets = self.config.get_static_assets()
            for source_path, _ in assets:
                if not Path(source_path).exists():
                    self.logger.error(f"Asset path not found: {source_path}")
                    return False
            
            # Check icon file if specified
            if self.config.icon_file:
                icon_path = self.config.project_root / self.config.icon_file
                if not icon_path.exists():
                    self.logger.error(f"Icon file not found: {self.config.icon_file}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            return False
    
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
        excluded_modules_str = ",\n    ".join(f"'{mod}'" for mod in excluded_modules)
        
        # Format data files (static assets)
        data_files = []
        for source, dest in static_assets:
            # Use forward slashes for cross-platform compatibility
            source_norm = source.replace(os.sep, '/')
            dest_norm = dest.replace(os.sep, '/')
            data_files.append(f"('{source_norm}', '{dest_norm}')")
        
        data_files_str = ",\n    ".join(data_files)
        
        analysis_section = f"""a = Analysis(
    ['{self.config.entry_point}'],
    pathex=['{str(self.config.project_root).replace(os.sep, "/")}'],
    binaries=[],
    datas=[
        {data_files_str}
    ],
    hiddenimports=[
        {hidden_imports_str}
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        {excluded_modules_str}
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)"""
        
        return analysis_section
    
    def generate_pyz_section(self) -> str:
        """Generate the PYZ section of the .spec file.
        
        Returns:
            PYZ section as string
        """
        return """pyz = PYZ(a.pure, a.zipped_data, cipher=None)"""
    
    def generate_exe_section(self) -> str:
        """Generate the EXE section of the .spec file.
        
        Returns:
            EXE section as string
        """
        platform_config = self.config.get_platform_specific_config()
        
        # Icon configuration
        icon_line = ""
        if self.config.icon_file:
            icon_path = str(self.config.project_root / self.config.icon_file)
            icon_line = f"    icon='{icon_path.replace(os.sep, '/')}',\n"
        
        # Console/windowed configuration
        console_setting = "true" if platform_config.get("console", self.config.console) else "false"
        
        if self.config.one_file:
            exe_section = f"""exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{self.config.app_name}',
{icon_line}    debug={str(self.config.debug).lower()},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={console_setting},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)"""
        else:
            # Directory mode
            exe_section = f"""exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{self.config.app_name}',
{icon_line}    debug={str(self.config.debug).lower()},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={console_setting},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)"""
        
        return exe_section
    
    def generate_collect_section(self) -> str:
        """Generate the COLLECT section of the .spec file (for directory mode).
        
        Returns:
            COLLECT section as string, or empty string for one-file mode
        """
        if self.config.one_file:
            return ""
        
        return f"""coll = COLLECT(
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
            Complete .spec file content as string
        """
        header = f"""# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for {self.config.app_name}
# Generated automatically by build_config.py

"""
        
        sections = [
            header,
            self.generate_analysis_section(),
            "",
            self.generate_pyz_section(),
            "",
            self.generate_exe_section()
        ]
        
        # Add COLLECT section for directory mode
        collect_section = self.generate_collect_section()
        if collect_section:
            sections.extend(["", collect_section])
        
        return "\n".join(sections)
    
    def write_spec_file(self, output_path: Optional[str] = None) -> str:
        """Write the .spec file to disk.
        
        Args:
            output_path: Path to write the .spec file (uses default if None)
            
        Returns:
            Path to the written .spec file
            
        Raises:
            ValueError: If configuration is invalid
            IOError: If file cannot be written
        """
        if not self.validate_config():
            raise ValueError("Invalid build configuration")
        
        if output_path is None:
            output_path = self.config.project_root / f"{self.config.app_name}.spec"
        else:
            output_path = Path(output_path)
        
        try:
            spec_content = self.generate_complete_spec()
            output_path.write_text(spec_content, encoding='utf-8')
            
            self.logger.info(f"Generated .spec file: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to write .spec file: {e}")
            raise IOError(f"Could not write .spec file to {output_path}: {e}")


def create_build_config(
    project_root: Optional[str] = None,
    **kwargs
) -> BuildConfig:
    """Factory function to create a BuildConfig instance.
    
    Args:
        project_root: Root directory of the project
        **kwargs: Additional configuration options
        
    Returns:
        Configured BuildConfig instance
    """
    return BuildConfig(project_root=project_root, **kwargs)


def generate_spec_file(
    project_root: Optional[str] = None,
    output_path: Optional[str] = None,
    **config_kwargs
) -> str:
    """Generate a PyInstaller .spec file for the project.
    
    Args:
        project_root: Root directory of the project
        output_path: Path to write the .spec file
        **config_kwargs: Additional configuration options
        
    Returns:
        Path to the generated .spec file
        
    Raises:
        ValueError: If project structure is invalid
        IOError: If .spec file cannot be written
    """
    # Create build configuration
    build_config = create_build_config(project_root=project_root, **config_kwargs)
    
    # Generate .spec file
    spec_generator = PyInstallerSpecGenerator(build_config)
    return spec_generator.write_spec_file(output_path)


if __name__ == "__main__":
    # Command-line usage example
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate PyInstaller .spec file")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--output", help="Output .spec file path")
    parser.add_argument("--app-name", default="WorkJournalMaker", help="Application name")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--console", action="store_true", help="Show console window")
    parser.add_argument("--directory", action="store_true", help="Create directory instead of single file")
    
    args = parser.parse_args()
    
    try:
        spec_file = generate_spec_file(
            project_root=args.project_root,
            output_path=args.output,
            app_name=args.app_name,
            debug=args.debug,
            console=args.console,
            one_file=not args.directory
        )
        print(f"Generated .spec file: {spec_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)