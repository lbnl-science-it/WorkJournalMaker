#!/usr/bin/env python3
"""
Debug script to test file discovery logic and validate the fix.
"""

from datetime import date, timedelta
from pathlib import Path
from file_discovery import FileDiscovery

def debug_week_ending_calculation():
    """Test the current week ending calculation logic."""
    print("🔍 Testing current file discovery logic...")
    print("=" * 50)
    
    # Test with your actual date range
    start_date = date(2024, 7, 1)
    end_date = date(2025, 6, 6)
    
    discovery = FileDiscovery()
    
    # Test current logic
    week_ending = discovery._calculate_week_ending(start_date, end_date)
    print(f"Date range: {start_date} to {end_date}")
    print(f"Current week_ending calculation: {week_ending}")
    print()
    
    # Show what paths it's trying to find
    print("🔍 Sample file paths being generated:")
    print("-" * 40)
    
    test_dates = [
        date(2024, 7, 1),   # First day
        date(2024, 7, 15),  # Mid July
        date(2024, 12, 20), # Your actual file example
        date(2025, 1, 15),  # January 2025
        date(2025, 6, 6)    # Last day
    ]
    
    for test_date in test_dates:
        file_path = discovery._construct_file_path(test_date, week_ending)
        print(f"Date {test_date} -> {file_path}")
    
    print()
    print("🎯 Expected path for your actual file:")
    print("/Users/TYFong/Desktop/worklogs/worklogs_2024/worklogs_2024-12/week_ending_2024-12-20/worklog_2024-12-20.txt")
    print()

def calculate_proper_week_ending(target_date: date) -> date:
    """
    Calculate proper week ending date for a single file.
    Assumes week ends on Friday (adjust as needed for your structure).
    """
    # Find the Friday of the week containing target_date
    days_since_monday = target_date.weekday()  # Monday = 0, Sunday = 6
    days_to_friday = 4 - days_since_monday  # Friday = 4
    
    if days_to_friday < 0:
        days_to_friday += 7  # Next Friday
    
    return target_date + timedelta(days=days_to_friday)

def test_proper_week_ending():
    """Test the corrected week ending calculation."""
    print("✅ Testing corrected file discovery logic...")
    print("=" * 50)
    
    discovery = FileDiscovery()
    
    test_dates = [
        date(2024, 7, 1),   # First day
        date(2024, 7, 15),  # Mid July  
        date(2024, 12, 20), # Your actual file example
        date(2025, 1, 15),  # January 2025
        date(2025, 6, 6)    # Last day
    ]
    
    print("🔍 Corrected file paths:")
    print("-" * 40)
    
    for test_date in test_dates:
        proper_week_ending = calculate_proper_week_ending(test_date)
        file_path = discovery._construct_file_path(test_date, proper_week_ending)
        print(f"Date {test_date} -> week_ending_{proper_week_ending} -> {file_path.name}")
        print(f"  Full path: {file_path}")
        print()

def test_fixed_file_discovery():
    """Test the fixed file discovery logic."""
    print("🔧 Testing FIXED file discovery logic...")
    print("=" * 50)
    
    # Test with your actual date range
    start_date = date(2024, 7, 1)
    end_date = date(2025, 6, 6)
    
    discovery = FileDiscovery()
    
    test_dates = [
        date(2024, 7, 1),   # First day
        date(2024, 7, 15),  # Mid July
        date(2024, 12, 20), # Your actual file example
        date(2025, 1, 15),  # January 2025
        date(2025, 6, 6)    # Last day
    ]
    
    print("🔍 Fixed file paths using new logic:")
    print("-" * 40)
    
    for test_date in test_dates:
        week_ending = discovery._calculate_week_ending_for_date(test_date)
        file_path = discovery._construct_file_path(test_date, week_ending)
        print(f"Date {test_date} -> week_ending_{week_ending} -> {file_path.name}")
        print(f"  Full path: {file_path}")
        
        # Check if this matches your actual file structure
        if test_date == date(2024, 12, 20):
            expected = "/Users/TYFong/Desktop/worklogs/worklogs_2024/worklogs_2024-12/week_ending_2024-12-20/worklog_2024-12-20.txt"
            if str(file_path) == expected:
                print(f"  ✅ MATCHES your actual file structure!")
            else:
                print(f"  ❌ Does not match expected: {expected}")
        print()

if __name__ == "__main__":
    debug_week_ending_calculation()
    print()
    test_proper_week_ending()
    print()
    test_fixed_file_discovery()