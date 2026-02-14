#!/usr/bin/env python3
# ABOUTME: Build testing and validation script
# ABOUTME: Tests existing builds and validates executable functionality

"""
Build testing and validation script.

This script tests existing builds and validates executable functionality
without rebuilding. Use this to verify that a previous build is working
correctly.

Usage:
    python scripts/build_test.py [options]
"""

import sys
import subprocess
import platform
from pathlib import Path

# Add project root to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

try:
    from build_system.local_builder import LocalBuilder, BuildError
except ImportError as e:
    print(f"Error importing build modules: {e}")
    sys.exit(1)


def find_executable() -> Path:
    """Find the built executable.
    
    Returns:
        Path to executable
        
    Raises:
        FileNotFoundError: If executable not found
    """
    dist_dir = project_root / "dist"
    
    if not dist_dir.exists():
        raise FileNotFoundError("dist directory not found - no build exists")
    
    # Look for executable
    if platform.system() == "Windows":
        exe_files = list(dist_dir.glob("*.exe"))
    else:
        # On Unix systems, look for files without extensions that are executable
        exe_files = []
        for item in dist_dir.iterdir():
            if item.is_file() and not item.suffix and item.stat().st_mode & 0o111:
                exe_files.append(item)
    
    if not exe_files:
        raise FileNotFoundError("No executable found in dist directory")
    
    # Return the first executable found
    return exe_files[0]


def test_executable_basic(executable_path: Path) -> bool:
    """Test basic executable functionality.
    
    Args:
        executable_path: Path to executable
        
    Returns:
        True if basic test passes
    """
    print(f"Testing executable: {executable_path.name}")
    
    try:
        # Test with --help flag
        result = subprocess.run(
            [str(executable_path), "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ --help command successful")
            return True
        else:
            print(f"✗ --help command failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ --help command timed out")
        return False
    except Exception as e:
        print(f"✗ --help command failed: {e}")
        return False


def test_executable_version(executable_path: Path) -> bool:
    """Test executable version command.
    
    Args:
        executable_path: Path to executable
        
    Returns:
        True if version test passes
    """
    try:
        # Test with --version flag
        result = subprocess.run(
            [str(executable_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Version command might not exist, so don't fail if it returns non-zero
        if result.returncode == 0 and result.stdout.strip():
            print(f"✓ Version: {result.stdout.strip()}")
            return True
        else:
            print("~ Version command not available (this is normal)")
            return True  # Don't fail for missing version command
            
    except subprocess.TimeoutExpired:
        print("~ Version command timed out")
        return True  # Don't fail for timeout
    except Exception as e:
        print(f"~ Version command error: {e}")
        return True  # Don't fail for version errors


def test_executable_startup(executable_path: Path) -> bool:
    """Test executable startup (short-lived test).
    
    Args:
        executable_path: Path to executable
        
    Returns:
        True if startup test passes
    """
    try:
        # Start the executable and immediately terminate it
        process = subprocess.Popen(
            [str(executable_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Let it run briefly
        try:
            stdout, stderr = process.communicate(timeout=5)
            
            if process.returncode == 0:
                print("✓ Executable started and exited successfully")
                return True
            else:
                print(f"✗ Executable exited with code: {process.returncode}")
                if stderr:
                    print(f"Error: {stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            # If it's still running after timeout, that's actually good
            # (means it started successfully), so terminate it
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            print("✓ Executable started successfully (terminated after timeout)")
            return True
            
    except Exception as e:
        print(f"✗ Startup test failed: {e}")
        return False


def validate_executable_properties(executable_path: Path) -> bool:
    """Validate executable file properties.
    
    Args:
        executable_path: Path to executable
        
    Returns:
        True if properties are valid
    """
    print(f"Validating executable properties...")
    
    # Check file exists
    if not executable_path.exists():
        print("✗ Executable file does not exist")
        return False
    
    print("✓ Executable file exists")
    
    # Check file size
    size_bytes = executable_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    
    if size_bytes == 0:
        print("✗ Executable file is empty")
        return False
    
    print(f"✓ Executable size: {size_mb:.1f} MB")
    
    # Check if file is too small (likely indicates a problem)
    if size_mb < 10:  # Adjust threshold as needed
        print(f"⚠ Executable seems small ({size_mb:.1f} MB) - may indicate an issue")
    
    # Check permissions (Unix systems)
    if platform.system() != "Windows":
        import stat
        mode = executable_path.stat().st_mode
        if not (mode & stat.S_IXUSR):
            print("✗ Executable is not executable")
            return False
        print("✓ Executable permissions correct")
    
    return True


def comprehensive_test() -> bool:
    """Run comprehensive executable tests.
    
    Returns:
        True if all tests pass
    """
    print("Comprehensive Executable Testing")
    print("=" * 40)
    
    try:
        # Find executable
        executable_path = find_executable()
        print(f"Found executable: {executable_path}")
        
        # Validate properties
        if not validate_executable_properties(executable_path):
            return False
        
        print("\nRunning functional tests...")
        print("-" * 30)
        
        # Run tests
        tests_passed = 0
        total_tests = 3
        
        if test_executable_basic(executable_path):
            tests_passed += 1
        
        if test_executable_version(executable_path):
            tests_passed += 1
        
        if test_executable_startup(executable_path):
            tests_passed += 1
        
        print("\nTest Results:")
        print("-" * 30)
        print(f"Tests passed: {tests_passed}/{total_tests}")
        
        if tests_passed == total_tests:
            print("✓ All tests passed")
            return True
        else:
            print(f"✗ {total_tests - tests_passed} tests failed")
            return False
        
    except FileNotFoundError as e:
        print(f"✗ {e}")
        print("Run a build first: python scripts/build.py")
        return False
    except Exception as e:
        print(f"✗ Testing failed: {e}")
        return False


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test built executable")
    parser.add_argument(
        '--basic-only',
        action='store_true',
        help='Run only basic tests'
    )
    
    args = parser.parse_args()
    
    if args.basic_only:
        try:
            executable_path = find_executable()
            success = (
                validate_executable_properties(executable_path) and
                test_executable_basic(executable_path)
            )
        except Exception as e:
            print(f"Basic test failed: {e}")
            success = False
    else:
        success = comprehensive_test()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTesting interrupted")
        sys.exit(1)