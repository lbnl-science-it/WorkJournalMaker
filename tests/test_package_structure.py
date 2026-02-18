# ABOUTME: Tests that the project is properly installable as a Python package.
# ABOUTME: Validates root modules and sub-packages are importable without sys.path hacks.

"""Verify the project root is importable as a proper Python package.

These tests confirm that `pyproject.toml` with a flat layout makes root-level
modules and sub-packages discoverable via standard import machinery, without
any sys.path manipulation.
"""

import importlib
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestRootModulesImportable:
    """Root-level .py modules should be importable without sys.path hacks."""

    @pytest.mark.parametrize("module_name", [
        "config_manager",
        "logger",
        "file_discovery",
        "content_processor",
        "unified_llm_client",
        "llm_data_structures",
        "output_manager",
        "bedrock_client",
        "google_genai_client",
        "summary_generator",
    ])
    def test_root_module_importable(self, module_name):
        """Each root-level module should be importable by name."""
        mod = importlib.import_module(module_name)
        assert mod is not None


class TestSubPackagesImportable:
    """Sub-packages with __init__.py should be importable."""

    @pytest.mark.parametrize("package_name", [
        "web",
        "desktop",
        "scripts",
        "build_system",
    ])
    def test_subpackage_importable(self, package_name):
        """Each sub-package should be importable."""
        mod = importlib.import_module(package_name)
        assert mod is not None


class TestPyprojectExists:
    """pyproject.toml should exist and have correct structure."""

    def test_pyproject_toml_exists(self):
        """pyproject.toml must exist at project root."""
        assert (PROJECT_ROOT / "pyproject.toml").is_file()

    def test_conftest_exists(self):
        """conftest.py must exist at project root for pytest discovery."""
        assert (PROJECT_ROOT / "conftest.py").is_file()


class TestEditableInstall:
    """The package should be installed in editable mode."""

    def test_package_is_installed(self):
        """workjournalmaker should appear in pip list."""
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "workjournalmaker"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, (
            "workjournalmaker is not installed. Run: pip install -e ."
        )

    def test_editable_install_resolves_to_project_root(self):
        """Modules should resolve to files under the project root."""
        import config_manager
        module_path = Path(config_manager.__file__).resolve()
        assert module_path.is_relative_to(PROJECT_ROOT), (
            f"config_manager resolved to {module_path}, "
            f"expected under {PROJECT_ROOT}"
        )
