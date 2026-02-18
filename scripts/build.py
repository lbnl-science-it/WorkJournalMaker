#!/usr/bin/env python3
# ABOUTME: Main build script for local development testing
# ABOUTME: Provides convenient command-line interface for PyInstaller builds

"""
Main build script for WorkJournalMaker desktop application.

This script provides a convenient interface for building the application
locally during development. It handles build configuration, execution,
and validation with comprehensive error reporting.

Usage:
    python scripts/build.py [options]
    
Examples:
    # Basic build
    python scripts/build.py
    
    # Clean build with testing
    python scripts/build.py --clean --test
    
    # Debug build with verbose output
    python scripts/build.py --debug --verbose
    
    # Quick build without testing
    python scripts/build.py --no-test --no-validate
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

script_dir = Path(__file__).parent
project_root = script_dir.parent

try:
    from build_system.local_builder import LocalBuilder, BuildResult, BuildError, build_project
    from build_system.build_config import BuildConfig, create_build_config
except ImportError as e:
    print(f"Error importing build modules: {e}")
    print("Make sure you're running this script from the project root")
    sys.exit(1)


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """Set up logging configuration.
    
    Args:
        verbose: Enable verbose output
        debug: Enable debug output
    """
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def validate_environment() -> bool:
    """Validate the build environment.
    
    Returns:
        True if environment is valid
    """
    try:
        builder = LocalBuilder(project_root=str(project_root))
        builder.validate_build_environment()
        builder.validate_spec_file()
        builder.validate_entry_point()
        print("✓ Build environment validation passed")
        return True
    except BuildError as e:
        print(f"✗ Build environment validation failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during validation: {e}")
        return False


def perform_build(
    clean: bool = False,
    debug: bool = False,
    test_executable: bool = True,
    validate_result: bool = True,
    timeout: Optional[int] = None
) -> BuildResult:
    """Perform the actual build.
    
    Args:
        clean: Whether to clean before building
        debug: Whether to enable debug mode
        test_executable: Whether to test the built executable
        validate_result: Whether to validate the build result
        timeout: Build timeout in seconds
        
    Returns:
        BuildResult with build information
    """
    print(f"Building WorkJournalMaker...")
    if clean:
        print("  - Cleaning build artifacts")
    if debug:
        print("  - Debug mode enabled")
    if test_executable:
        print("  - Executable testing enabled")
    
    try:
        # Create builder
        builder = LocalBuilder(project_root=str(project_root))
        
        # Clean if requested
        if clean:
            builder.clean_all()
            print("✓ Cleaned build artifacts")
        
        # Set debug option in spec if needed
        if debug:
            builder.set_build_option('debug', True)
        
        # Execute build
        print("Executing PyInstaller...")
        result = builder.execute_build(timeout=timeout)
        
        if result.success:
            print(f"✓ Build completed in {result.build_time:.1f}s")
            
            # Validate result if requested
            if validate_result:
                try:
                    builder.validate_executable()
                    builder.validate_executable_permissions()
                    print("✓ Executable validation passed")
                except BuildError as e:
                    print(f"✗ Executable validation failed: {e}")
                    result.success = False
                    result.error = f"Validation failed: {e}"
            
            # Test executable if requested
            if test_executable and result.success:
                print("Testing executable...")
                test_passed = builder.test_executable(timeout=30)
                if test_passed:
                    print("✓ Executable test passed")
                else:
                    print("✗ Executable test failed")
                    result.metrics['executable_test_passed'] = False
            
        else:
            print(f"✗ Build failed after {result.build_time:.1f}s")
            if result.error:
                print(f"Error: {result.error}")
        
        return result
        
    except Exception as e:
        print(f"✗ Build failed with exception: {e}")
        return BuildResult(
            success=False,
            build_time=0.0,
            error=str(e)
        )


def print_build_summary(result: BuildResult) -> None:
    """Print a comprehensive build summary.
    
    Args:
        result: Build result to summarize
    """
    print("\n" + "="*60)
    print("BUILD SUMMARY")
    print("="*60)
    
    status = "SUCCESS" if result.success else "FAILED"
    print(f"Status: {status}")
    print(f"Build Time: {result.build_time:.1f}s")
    
    if result.executable_path:
        exe_path = Path(result.executable_path)
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable: {exe_path.name} ({size_mb:.1f} MB)")
            print(f"Location: {exe_path.parent}")
        else:
            print(f"Executable: {result.executable_path} (NOT FOUND)")
    
    if result.platform_info:
        system = result.platform_info.get('system', 'Unknown')
        arch = result.platform_info.get('architecture', 'Unknown')
        print(f"Platform: {system} ({arch})")
    
    if result.error:
        print(f"Error: {result.error}")
    
    if result.metrics:
        print("Metrics:")
        for key, value in result.metrics.items():
            print(f"  {key}: {value}")
    
    print("="*60)


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Build WorkJournalMaker desktop application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Basic build
  %(prog)s --clean --test           # Clean build with testing
  %(prog)s --debug --verbose        # Debug build with verbose output
  %(prog)s --no-test --no-validate  # Quick build without validation
        """
    )
    
    # Build options
    parser.add_argument(
        '--clean', '-c',
        action='store_true',
        help='Clean build artifacts before building'
    )
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--no-test',
        action='store_true',
        help='Skip executable testing'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip build result validation'
    )
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=300,
        help='Build timeout in seconds (default: 300)'
    )
    
    # Output options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-essential output'
    )
    
    # Environment options
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate environment, don\'t build'
    )
    
    args = parser.parse_args()
    
    # Handle conflicting options
    if args.verbose and args.quiet:
        print("Error: --verbose and --quiet cannot be used together")
        return 1
    
    # Setup logging
    if not args.quiet:
        setup_logging(verbose=args.verbose, debug=args.debug)
    
    # Print header
    if not args.quiet:
        print("WorkJournalMaker Build Script")
        print("="*40)
    
    # Validate environment
    if not validate_environment():
        return 1
    
    # If only validating, exit here
    if args.validate_only:
        print("Environment validation completed successfully")
        return 0
    
    # Perform build
    result = perform_build(
        clean=args.clean,
        debug=args.debug,
        test_executable=not args.no_test,
        validate_result=not args.no_validate,
        timeout=args.timeout
    )
    
    # Print summary
    if not args.quiet:
        print_build_summary(result)
    
    # Return appropriate exit code
    return 0 if result.success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nBuild interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)