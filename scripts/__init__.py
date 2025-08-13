# ABOUTME: Build system package initialization for WorkJournalMaker
# ABOUTME: Exports core build classes and functions for PyInstaller integration

"""
Build system package for WorkJournalMaker desktop application.

This package provides comprehensive PyInstaller-based build tools for creating
standalone executables of the WorkJournalMaker web application.
"""

from .local_builder import LocalBuilder, BuildResult, BuildError, build_project
from .build_config import BuildConfig, PyInstallerSpecGenerator, create_build_config, generate_spec_file

__all__ = [
    'LocalBuilder',
    'BuildResult',
    'BuildError',
    'build_project',
    'BuildConfig',
    'PyInstallerSpecGenerator',
    'create_build_config',
    'generate_spec_file'
]

