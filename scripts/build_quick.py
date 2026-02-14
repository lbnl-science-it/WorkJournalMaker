#!/usr/bin/env python3
# ABOUTME: Quick build script for rapid development iteration
# ABOUTME: Minimal build with fast execution and basic validation

"""
Quick build script for fast development iteration.

This script provides a minimal, fast build process for development,
skipping comprehensive validation and testing to speed up the build cycle.
Use this for rapid prototyping and development iteration.

Usage:
    python scripts/build_quick.py [options]
"""

import sys
import time
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


def quick_build() -> bool:
    """Perform a quick build with minimal validation.
    
    Returns:
        True if build succeeded
    """
    print("Quick Build - WorkJournalMaker")
    print("-" * 30)
    
    start_time = time.time()
    
    try:
        # Create builder
        builder = LocalBuilder(project_root=str(project_root))
        
        # Basic validation only
        if not builder.spec_file.exists():
            print("✗ .spec file not found")
            return False
        
        print("✓ .spec file found")
        
        # Execute build with minimal options
        result = builder.execute_build(
            clean=False,
            capture_output=False,  # Don't capture for faster execution
            timeout=120  # Shorter timeout
        )
        
        build_time = time.time() - start_time
        
        if result.success:
            print(f"✓ Build completed in {build_time:.1f}s")
            
            # Quick executable check
            executable_path = builder.get_executable_path()
            if executable_path and executable_path.exists():
                size_mb = executable_path.stat().st_size / (1024 * 1024)
                print(f"✓ Executable: {executable_path.name} ({size_mb:.1f} MB)")
            else:
                print("⚠ Executable not found")
                return False
            
            return True
        else:
            print(f"✗ Build failed after {build_time:.1f}s")
            if result.error:
                print(f"Error: {result.error[:200]}...")  # Truncate long errors
            return False
            
    except Exception as e:
        build_time = time.time() - start_time
        print(f"✗ Build failed after {build_time:.1f}s: {e}")
        return False


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick build for development")
    parser.add_argument('--clean', action='store_true', help='Clean before building')
    
    args = parser.parse_args()
    
    # Clean if requested
    if args.clean:
        try:
            builder = LocalBuilder(project_root=str(project_root))
            builder.clean_all()
            print("✓ Cleaned build artifacts")
        except Exception as e:
            print(f"⚠ Clean failed: {e}")
    
    # Perform quick build
    success = quick_build()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nBuild interrupted")
        sys.exit(1)