# ABOUTME: Build system package initialization for WorkJournalMaker
# ABOUTME: Exports core build classes and functions for PyInstaller integration

"""
Build system package for WorkJournalMaker desktop application.

This package provides comprehensive PyInstaller-based build tools for creating
standalone executables of the WorkJournalMaker web application.
"""

from .workflow_generator import WorkflowGenerator, WorkflowConfig, BuildMatrix, create_default_config, create_default_matrix, generate_workflow_file

__all__ = [
    'WorkflowGenerator',
    'WorkflowConfig',
    'BuildMatrix',
    'create_default_config',
    'create_default_matrix',
    'generate_workflow_file'
]

