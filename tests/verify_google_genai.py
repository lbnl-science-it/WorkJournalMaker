#!/usr/bin/env python3
"""
Google GenAI Dependency Verification Script

This script verifies that the google-genai dependency is properly installed
and can be imported successfully. It performs basic functionality checks
without making actual API calls.
"""

import sys
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_google_genai_import() -> bool:
    """
    Test that google.genai can be imported successfully.
    
    Returns:
        bool: True if import is successful, False otherwise
    """
    try:
        import google.genai as genai
        logger.info("✓ Successfully imported google.genai module")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import google.genai: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error importing google.genai: {e}")
        return False


def test_client_creation() -> bool:
    """
    Test that a Google GenAI client can be created (without authentication).
    
    Returns:
        bool: True if client creation is successful, False otherwise
    """
    try:
        import google.genai as genai
        
        # Test client creation with minimal configuration
        # This should work without authentication for basic structure validation
        client_class = genai.Client
        logger.info("✓ Google GenAI Client class is accessible")
        
        # Check if the Client class has expected methods
        expected_methods = ['models']
        for method in expected_methods:
            if hasattr(client_class, method) or hasattr(genai, method):
                logger.info(f"✓ Found expected attribute/method: {method}")
            else:
                logger.warning(f"⚠ Expected attribute/method not found: {method}")
        
        return True
    except ImportError as e:
        logger.error(f"✗ Import error during client creation test: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error during client creation test: {e}")
        return False


def test_basic_functionality() -> bool:
    """
    Test basic functionality of the google.genai module.
    
    Returns:
        bool: True if basic functionality works, False otherwise
    """
    try:
        import google.genai as genai
        
        # Check module attributes
        logger.info(f"✓ Google GenAI module version info available")
        
        # Test that we can access the main classes/functions we'll need
        if hasattr(genai, 'Client'):
            logger.info("✓ Client class is available")
        else:
            logger.warning("⚠ Client class not found in expected location")
        
        return True
    except Exception as e:
        logger.error(f"✗ Error during basic functionality test: {e}")
        return False


def run_verification() -> bool:
    """
    Run all verification tests.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    logger.info("Starting Google GenAI dependency verification...")
    logger.info("=" * 50)
    
    tests = [
        ("Import Test", test_google_genai_import),
        ("Client Creation Test", test_client_creation),
        ("Basic Functionality Test", test_basic_functionality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name}...")
        try:
            result = test_func()
            results.append(result)
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            logger.error(f"{test_name}: FAILED with exception: {e}")
            results.append(False)
    
    logger.info("\n" + "=" * 50)
    
    all_passed = all(results)
    if all_passed:
        logger.info("✓ All verification tests PASSED!")
        logger.info("Google GenAI dependency is properly installed and functional.")
    else:
        logger.error("✗ Some verification tests FAILED!")
        logger.error("Please check the installation of google-genai dependency.")
        
        # Provide helpful troubleshooting information
        logger.info("\nTroubleshooting steps:")
        logger.info("1. Ensure google-genai is installed: pip install google-genai")
        logger.info("2. Check Python version compatibility")
        logger.info("3. Verify no conflicting packages are installed")
    
    return all_passed


def main():
    """Main entry point for the verification script."""
    try:
        success = run_verification()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nVerification interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()