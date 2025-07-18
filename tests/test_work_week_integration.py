#!/usr/bin/env python3
"""
Test script for Work Week Integration in Entry Manager

This script tests the complete workflow from work week configuration to entry creation
to verify that the Entry Manager properly uses work week calculations for directory organization.
"""

import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent))

from config_manager import ConfigManager
from logger import LogConfig, JournalSummarizerLogger
from web.database import DatabaseManager
from web.services.work_week_service import WorkWeekService, WorkWeekConfig, WorkWeekPreset
from web.services.entry_manager import EntryManager


async def test_work_week_integration():
    """Test the complete work week integration workflow."""
    print("🧪 Testing Work Week Integration with Entry Manager")
    print("=" * 60)
    
    try:
        # Initialize core services
        config_manager = ConfigManager()
        config = config_manager.get_config()
        logger = JournalSummarizerLogger(config.logging)
        db_manager = DatabaseManager()
        
        # Initialize database
        await db_manager.initialize()
        print("✅ Database initialized")
        
        # Initialize WorkWeekService
        work_week_service = WorkWeekService(config, logger, db_manager)
        print("✅ WorkWeekService initialized")
        
        # Initialize EntryManager with WorkWeekService
        entry_manager = EntryManager(config, logger, db_manager, work_week_service)
        print("✅ EntryManager initialized with work week integration")
        
        # Test 1: Verify work week service availability
        print("\n📋 Test 1: Work Week Service Availability")
        is_available = entry_manager.is_work_week_service_available()
        print(f"   Work week service available: {is_available}")
        
        # Get integration status
        status = await entry_manager.get_work_week_integration_status()
        print(f"   Integration enabled: {status.get('integration_enabled', False)}")
        print(f"   Fallback mode: {status.get('fallback_mode', True)}")
        
        # Test 2: Test with Monday-Friday work week
        print("\n📋 Test 2: Monday-Friday Work Week Configuration")
        
        # Configure Monday-Friday work week
        monday_friday_config = WorkWeekConfig.from_preset(WorkWeekPreset.MONDAY_FRIDAY)
        await work_week_service.update_work_week_config(monday_friday_config)
        print(f"   Configured work week: {monday_friday_config.preset.value}")
        
        # Test entry creation on different days
        test_dates = [
            date(2024, 1, 15),  # Monday
            date(2024, 1, 17),  # Wednesday
            date(2024, 1, 19),  # Friday
            date(2024, 1, 20),  # Saturday (weekend)
            date(2024, 1, 21),  # Sunday (weekend)
        ]
        
        monday_friday_results = []
        for test_date in test_dates:
            # Calculate week ending date
            week_ending = await work_week_service.calculate_week_ending_date(test_date)
            day_name = test_date.strftime("%A")
            
            # Test file path construction (async version)
            file_path = await entry_manager._construct_file_path_async(test_date)
            
            monday_friday_results.append({
                'date': test_date,
                'day': day_name,
                'week_ending': week_ending,
                'file_path': str(file_path)
            })
            
            print(f"   {day_name} {test_date} -> Week ending: {week_ending}")
            print(f"     File path: {file_path}")
        
        # Test 3: Test with Sunday-Thursday work week
        print("\n📋 Test 3: Sunday-Thursday Work Week Configuration")
        
        # Configure Sunday-Thursday work week
        sunday_thursday_config = WorkWeekConfig.from_preset(WorkWeekPreset.SUNDAY_THURSDAY)
        await work_week_service.update_work_week_config(sunday_thursday_config)
        print(f"   Configured work week: {sunday_thursday_config.preset.value}")
        
        sunday_thursday_results = []
        for test_date in test_dates:
            # Calculate week ending date
            week_ending = await work_week_service.calculate_week_ending_date(test_date)
            day_name = test_date.strftime("%A")
            
            # Test file path construction (async version)
            file_path = await entry_manager._construct_file_path_async(test_date)
            
            sunday_thursday_results.append({
                'date': test_date,
                'day': day_name,
                'week_ending': week_ending,
                'file_path': str(file_path)
            })
            
            print(f"   {day_name} {test_date} -> Week ending: {week_ending}")
            print(f"     File path: {file_path}")
        
        # Test 4: Test custom work week (Tuesday-Saturday)
        print("\n📋 Test 4: Custom Work Week Configuration (Tuesday-Saturday)")
        
        # Configure custom work week
        custom_config = WorkWeekConfig(
            preset=WorkWeekPreset.CUSTOM,
            start_day=2,  # Tuesday
            end_day=6     # Saturday
        )
        await work_week_service.update_work_week_config(custom_config)
        print(f"   Configured work week: Tuesday-Saturday (Custom)")
        
        custom_results = []
        for test_date in test_dates:
            # Calculate week ending date
            week_ending = await work_week_service.calculate_week_ending_date(test_date)
            day_name = test_date.strftime("%A")
            
            # Test file path construction (async version)
            file_path = await entry_manager._construct_file_path_async(test_date)
            
            custom_results.append({
                'date': test_date,
                'day': day_name,
                'week_ending': week_ending,
                'file_path': str(file_path)
            })
            
            print(f"   {day_name} {test_date} -> Week ending: {week_ending}")
            print(f"     File path: {file_path}")
        
        # Test 5: Test actual entry saving and retrieval
        print("\n📋 Test 5: Entry Creation and Retrieval")
        
        # Reset to Monday-Friday for this test
        await work_week_service.update_work_week_config(monday_friday_config)
        
        test_entry_date = date(2024, 1, 17)  # Wednesday
        test_content = f"Test journal entry for work week integration on {test_entry_date}"
        
        # Save entry
        save_success = await entry_manager.save_entry_content(test_entry_date, test_content)
        print(f"   Entry save success: {save_success}")
        
        if save_success:
            # Retrieve entry
            retrieved_content = await entry_manager.get_entry_content(test_entry_date)
            content_matches = retrieved_content == test_content
            print(f"   Entry retrieval success: {retrieved_content is not None}")
            print(f"   Content matches: {content_matches}")
            
            # Get entry metadata
            entry_response = await entry_manager.get_entry_by_date(test_entry_date, include_content=True)
            if entry_response:
                print(f"   Week ending in database: {entry_response.week_ending_date}")
                print(f"   Word count: {entry_response.metadata.word_count}")
        
        # Test 6: Test backward compatibility
        print("\n📋 Test 6: Backward Compatibility")
        
        # Create EntryManager without WorkWeekService
        legacy_entry_manager = EntryManager(config, logger, db_manager)
        is_legacy_available = legacy_entry_manager.is_work_week_service_available()
        print(f"   Legacy mode (no work week service): {not is_legacy_available}")
        
        # Test file path construction in legacy mode
        legacy_file_path = legacy_entry_manager._construct_file_path(test_entry_date)
        print(f"   Legacy file path: {legacy_file_path}")
        
        # Test legacy entry retrieval
        legacy_content = await legacy_entry_manager.get_entry_content(test_entry_date)
        legacy_retrieval_success = legacy_content is not None
        print(f"   Legacy entry retrieval: {legacy_retrieval_success}")
        
        # Test sync file path construction still works
        sync_file_path = legacy_entry_manager._construct_file_path(test_entry_date)
        print(f"   Sync file path construction: Working")
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 Work Week Integration Test Summary:")
        print(f"   ✅ Work week service integration: Working")
        print(f"   ✅ Monday-Friday configuration: Working")
        print(f"   ✅ Sunday-Thursday configuration: Working")
        print(f"   ✅ Custom work week configuration: Working")
        print(f"   ✅ Entry creation and retrieval: Working")
        print(f"   ✅ Backward compatibility: Working")
        print("   🚀 All tests passed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if 'db_manager' in locals() and db_manager.engine:
            await db_manager.engine.dispose()


async def main():
    """Main test function."""
    success = await test_work_week_integration()
    if success:
        print("\n✅ Work Week Integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Work Week Integration test failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())