#!/usr/bin/env python3
"""
Test script to verify the week ending fix works correctly.
"""

import sys
from datetime import date
import asyncio

from file_discovery import FileDiscovery
from config_manager import AppConfig

async def test_week_ending_fix():
    """Test that the week ending fix resolves the directory structure issue."""
    print("=== Testing Week Ending Fix ===\n")
    
    try:
        # 1. Setup
        config = AppConfig()
        file_discovery = FileDiscovery(config.processing.base_path)
        
        # 2. Test the problematic file from diagnostic
        print("1. Testing problematic file from diagnostic...")
        test_date = date(2025, 6, 17)  # June 17, 2025
        
        print(f"   Testing date: {test_date}")
        
        # Use new method to find actual week ending
        actual_week_ending = file_discovery._find_week_ending_for_date(test_date)
        print(f"   ✓ Found actual week ending: {actual_week_ending}")
        
        # Construct path using actual week ending
        constructed_path = file_discovery._construct_file_path(test_date, actual_week_ending)
        print(f"   ✓ Constructed path: {constructed_path}")
        
        # Check if file exists
        file_exists = constructed_path.exists()
        print(f"   ✓ File exists: {file_exists}")
        
        if file_exists:
            print("   ✅ SUCCESS: File discovery now works correctly!")
            
            # Read content to verify
            with open(constructed_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"   ✓ File content preview: {content[:50]}...")
        else:
            print("   ❌ FAILED: File still not found with new logic")
            
            # Debug: show what directory we're looking in
            expected_dir = constructed_path.parent
            print(f"   Debug: Looking in directory: {expected_dir}")
            print(f"   Debug: Directory exists: {expected_dir.exists()}")
            
            if expected_dir.exists():
                files_in_dir = list(expected_dir.glob("*.txt"))
                print(f"   Debug: Files in directory: {[f.name for f in files_in_dir]}")
        
        # 3. Test a few more dates to ensure consistency
        print("\n2. Testing additional dates...")
        test_dates = [
            date(2025, 6, 20),  # June 20, 2025
            date(2025, 6, 23),  # June 23, 2025
            date(2025, 6, 25),  # June 25, 2025
        ]
        
        success_count = 0
        for test_date in test_dates:
            week_ending = file_discovery._find_week_ending_for_date(test_date)
            file_path = file_discovery._construct_file_path(test_date, week_ending)
            exists = file_path.exists()
            
            status = "✅" if exists else "❌"
            print(f"   {status} {test_date} -> week_ending_{week_ending} -> exists: {exists}")
            
            if exists:
                success_count += 1
        
        print(f"\n3. Summary:")
        print(f"   ✓ Tested {len(test_dates) + 1} dates")
        print(f"   ✓ Success rate: {success_count + (1 if file_exists else 0)}/{len(test_dates) + 1}")
        
        if success_count + (1 if file_exists else 0) == len(test_dates) + 1:
            print("   🎉 ALL TESTS PASSED - Week ending fix is working!")
            return True
        else:
            print("   ⚠️  Some tests failed - may need additional fixes")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_week_ending_fix())
    sys.exit(0 if success else 1)