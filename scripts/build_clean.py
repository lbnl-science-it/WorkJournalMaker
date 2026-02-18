#!/usr/bin/env python3
# ABOUTME: Clean build script with comprehensive validation
# ABOUTME: Full build process with testing, validation, and reporting

"""
Clean build script with comprehensive validation.

This script performs a complete clean build with full validation,
testing, and comprehensive reporting. Use this for release builds
and thorough validation.

Usage:
    python scripts/build_clean.py
"""

import sys
import time
from pathlib import Path

script_dir = Path(__file__).parent
project_root = script_dir.parent

try:
    from build_system.local_builder import LocalBuilder, BuildError
    from build_system.build_config import BuildConfig
except ImportError as e:
    print(f"Error importing build modules: {e}")
    sys.exit(1)


def comprehensive_build() -> bool:
    """Perform a comprehensive clean build with full validation.
    
    Returns:
        True if build succeeded
    """
    print("Comprehensive Clean Build - WorkJournalMaker")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # Create builder
        builder = LocalBuilder(project_root=str(project_root))
        
        print("Phase 1: Environment Validation")
        print("-" * 30)
        
        # Comprehensive environment validation
        builder.validate_build_environment()
        print("✓ PyInstaller available")
        
        builder.validate_spec_file()
        print("✓ .spec file valid")
        
        builder.validate_entry_point()
        print("✓ Entry point valid")
        
        # Check dependencies
        config = BuildConfig(project_root=str(project_root))
        static_assets = config.get_static_assets()
        for source_path, _ in static_assets:
            if not Path(source_path).exists():
                print(f"✗ Asset path missing: {source_path}")
                return False
        print(f"✓ {len(static_assets)} asset paths validated")
        
        print("\nPhase 2: Clean Build")
        print("-" * 30)
        
        # Clean all artifacts
        builder.clean_all()
        print("✓ Cleaned build artifacts")
        print("✓ Cleaned Python cache")
        
        # Execute build
        print("Executing PyInstaller build...")
        result = builder.execute_build(
            clean=True,
            capture_output=True,
            timeout=600  # Longer timeout for comprehensive build
        )
        
        build_time = time.time() - start_time
        
        if not result.success:
            print(f"✗ Build failed after {build_time:.1f}s")
            if result.error:
                print(f"Error: {result.error}")
            return False
        
        print(f"✓ Build completed in {build_time:.1f}s")
        
        print("\nPhase 3: Result Validation")
        print("-" * 30)
        
        # Comprehensive validation
        builder.validate_executable()
        print("✓ Executable exists and is valid")
        
        builder.validate_executable_permissions()
        print("✓ Executable permissions correct")
        
        # Get executable info
        executable_path_str = builder.get_executable_path()
        if executable_path_str:
            executable_path = Path(executable_path_str)
            size_mb = executable_path.stat().st_size / (1024 * 1024)
            print(f"✓ Executable: {executable_path.name} ({size_mb:.1f} MB)")
        
        print("\nPhase 4: Executable Testing")
        print("-" * 30)
        
        # Test executable
        test_passed = builder.test_executable(timeout=60)
        if test_passed:
            print("✓ Executable test passed")
        else:
            print("✗ Executable test failed")
            return False
        
        print("\nPhase 5: Build Report")
        print("-" * 30)
        
        # Generate report
        report = builder.generate_build_report(result)
        metrics = builder.get_build_metrics(result)
        
        print(f"Build Time: {report['build_time']:.1f}s")
        print(f"Platform: {report['platform_info']['system']} ({report['platform_info']['architecture']})")
        print(f"Project Root: {report['project_root']}")
        print(f"Spec File: {report['spec_file']}")
        
        if 'executable_size' in report:
            size_mb = report['executable_size'] / (1024 * 1024)
            print(f"Executable Size: {size_mb:.1f} MB")
        
        print("\n" + "=" * 50)
        print("BUILD SUCCESSFUL")
        print("=" * 50)
        
        return True
        
    except BuildError as e:
        build_time = time.time() - start_time
        print(f"✗ Build validation failed after {build_time:.1f}s: {e}")
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
    success = comprehensive_build()
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nBuild interrupted")
        sys.exit(1)