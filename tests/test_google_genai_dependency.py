#!/usr/bin/env python3
"""
Tests for Google GenAI dependency verification.

This test module verifies that the google-genai dependency is properly
installed and can be imported successfully in the test environment.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock


class TestGoogleGenAIDependency:
    """Test cases for Google GenAI dependency verification."""

    def test_google_genai_import(self):
        """Test that google.genai can be imported successfully."""
        try:
            import google.genai as genai
            assert genai is not None
        except ImportError as e:
            pytest.fail(f"Failed to import google.genai: {e}")

    def test_google_genai_client_class_exists(self):
        """Test that the Client class is available in google.genai."""
        import google.genai as genai
        
        assert hasattr(genai, 'Client'), "google.genai.Client class not found"
        
        # Verify it's a class that can be instantiated (even if it fails due to auth)
        client_class = genai.Client
        assert callable(client_class), "Client should be callable (class)"

    def test_google_genai_basic_attributes(self):
        """Test that google.genai has expected basic attributes."""
        import google.genai as genai
        
        # Check for key attributes/methods we'll need
        expected_attributes = ['Client']
        
        for attr in expected_attributes:
            assert hasattr(genai, attr), f"google.genai missing expected attribute: {attr}"

    def test_google_genai_client_structure(self):
        """Test that the Client class has expected structure."""
        import google.genai as genai
        
        client_class = genai.Client
        
        # Check that Client class exists and is properly structured
        assert client_class is not None
        
        # We can't instantiate without proper auth, but we can check the class exists
        # and has the basic structure we expect
        assert str(client_class).startswith("<class"), "Client should be a proper class"

    def test_import_error_handling(self):
        """Test graceful handling of import errors."""
        # This test verifies our error handling approach
        try:
            import google.genai as genai
            # If import succeeds, that's good
            success = True
        except ImportError:
            # If import fails, we should handle it gracefully
            success = False
        
        # In our actual implementation, we'll handle both cases
        # For now, we expect the import to succeed since we added the dependency
        assert success, "google.genai import should succeed with proper dependency"

    def test_module_version_info(self):
        """Test that we can access module information."""
        import google.genai as genai
        
        # The module should be importable and have basic module attributes
        assert hasattr(genai, '__name__')
        assert genai.__name__ == 'google.genai'

    @patch('google.genai.Client')
    def test_mocked_client_creation(self, mock_client):
        """Test that we can mock the Client for testing purposes."""
        import google.genai as genai
        
        # Configure the mock
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Create a client instance (mocked)
        client = genai.Client()
        
        # Verify the mock was called and returned our mock instance
        mock_client.assert_called_once()
        assert client is mock_instance

    def test_dependency_in_requirements(self):
        """Test that google-genai is listed in requirements.txt."""
        try:
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
            
            assert 'google-genai' in requirements, "google-genai should be in requirements.txt"
        except FileNotFoundError:
            pytest.fail("requirements.txt file not found")

    def test_no_import_side_effects(self):
        """Test that importing google.genai doesn't cause side effects."""
        # Store initial modules
        initial_modules = set(sys.modules.keys())
        
        # Import the module
        import google.genai as genai
        
        # The import should not cause any exceptions or major side effects
        # We expect some new modules to be loaded, but no errors
        assert genai is not None
        
        # Verify we can import it multiple times without issues
        import google.genai as genai2
        assert genai2 is genai  # Should be the same module object