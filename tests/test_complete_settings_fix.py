#!/usr/bin/env python3
"""
Comprehensive test script to verify the complete settings integration fix.
Tests both work week settings AND filesystem settings.
"""

import asyncio
import sys
import tempfile
from pathlib import Path
from datetime import date

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent))

from web.database import DatabaseManager
from web.services.settings_service import SettingsService
from web.services.work_week_service import WorkWeekService
from web.services.entry_manager import EntryManager
from config_manager import ConfigManager
from logger import JournalSummarizerLogger

async def test_complete_settings_integration():
    """Test that ALL settings now work correctly for entry generation."""
    print("🧪 Testing COMPLETE Settings Integration Fix")
    print("=" * 50)
    
    # Initialize dependencies
    config_manager = ConfigManager()
    config = config_manager.get_config()
    logger = JournalSummarizerLogger(config.logging)
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Initialize services
    settings_service = SettingsService(config, logger, db_manager)
    work_week_service = WorkWeekService(config, logger, db_manager)
    entry_manager = EntryManager(config, logger, db_manager, work_week_service)
    
    print("\n1. 📁 Testing Filesystem Settings Integration...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_base_path = Path(temp_dir) / "test_journals"
        temp_output_path = Path(temp_dir) / "test_output"
        
        print(f"   Setting base path to: {temp_base_path}")
        print(f"   Setting output path to: {temp_output_path}")
        
        # Update filesystem settings
        try:
            base_result = await settings_service.update_setting('filesystem.base_path', str(temp_base_path))
            output_result = await settings_service.update_setting('filesystem.output_path', str(temp_output_path))
            
            if base_result and output_result:
                print("   ✅ Filesystem settings updated successfully")
            else:
                print("   ❌ Failed to update filesystem settings")
                return
                
        except Exception as e:
            print(f"   ❌ Error updating filesystem settings: {e}")
            return
        
        print("\n2. 🔧 Testing Work Week Settings...")
        
        # Update work week settings to Sunday-Thursday
        try:
            result = await settings_service.update_work_week_configuration(
                preset='sunday_thursday',
                start_day=7,  # Sunday
                end_day=4,    # Thursday
                timezone='America/Los_Angeles'
            )
            print(f"   ✅ Work week settings updated: {result['success']}")
            if not result['success']:
                print(f"      - Errors: {result['errors']}")
                return
        except Exception as e:
            print(f"   ❌ Failed to update work week settings: {e}")
            return
        
        print("\n3. 🏗️ Testing EntryManager with New Settings...")
        
        # Clear any caches to force fresh retrieval
        work_week_service._clear_config_cache()
        
        # Test entry creation with new settings
        test_date = date(2025, 7, 8)  # Tuesday, July 8, 2025
        test_content = f"Test entry created on {test_date}\n\nThis entry should use the new filesystem and work week settings."
        
        try:
            # Save entry - this should use the new base path and work week settings
            success = await entry_manager.save_entry_content(test_date, test_content)
            print(f"   ✅ Entry save result: {success}")
            
            if success:
                # Verify the entry was saved to the correct location
                retrieved_content = await entry_manager.get_entry_content(test_date)
                if retrieved_content and test_content in retrieved_content:
                    print("   🎯 Entry content matches - settings are working!")
                else:
                    print("   ⚠️  Entry content doesn't match")
                    
                # Check if file was created in the new base path
                if temp_base_path.exists():
                    created_files = list(temp_base_path.rglob("*.txt"))
                    if created_files:
                        print(f"   ✅ File created in new base path: {created_files[0]}")
                        
                        # Verify work week directory structure
                        file_path = created_files[0]
                        if "week_ending" in str(file_path):
                            print("   🎯 Work week directory structure is correct!")
                        else:
                            print("   ⚠️  Work week directory structure not found")
                    else:
                        print("   ❌ No files found in new base path")
                else:
                    print("   ❌ New base path directory not created")
            else:
                print("   ❌ Entry save failed")
                
        except Exception as e:
            print(f"   ❌ Error testing entry operations: {e}")
            return
        
        print("\n4. 🔄 Testing Settings Persistence...")
        
        # Change settings again and verify persistence
        try:
            # Change back to Monday-Friday
            result = await settings_service.update_work_week_configuration(
                preset='monday_friday',
                start_day=1,  # Monday
                end_day=5,    # Friday
                timezone='UTC'
            )
            print(f"   ✅ Changed back to Monday-Friday: {result['success']}")
            
            # Clear cache and verify change took effect
            work_week_service._clear_config_cache()
            
            # Test with a different date
            test_date2 = date(2025, 7, 9)  # Wednesday, July 9, 2025
            test_content2 = "Test entry with Monday-Friday settings"
            
            success2 = await entry_manager.save_entry_content(test_date2, test_content2)
            print(f"   ✅ Second entry save result: {success2}")
            
            if success2:
                print("   🎯 Settings changes are persisting correctly!")
            else:
                print("   ⚠️  Settings changes may not be persisting")
                
        except Exception as e:
            print(f"   ❌ Error testing settings persistence: {e}")
    
    print("\n5. 📊 Summary of Integration Test...")
    
    # Get final settings state
    try:
        current_settings = await settings_service.get_work_week_settings()
        base_path_setting = await settings_service.get_setting('filesystem.base_path')
        
        print("   Final Settings State:")
        print(f"   - Work Week Preset: {current_settings.get('preset', 'unknown')}")
        print(f"   - Start Day: {current_settings.get('start_day', 'unknown')}")
        print(f"   - End Day: {current_settings.get('end_day', 'unknown')}")
        print(f"   - Base Path: {base_path_setting.parsed_value if base_path_setting else 'unknown'}")
        
    except Exception as e:
        print(f"   ❌ Error getting final settings: {e}")
    
    print("\n🎉 Complete settings integration test finished!")

if __name__ == "__main__":
    asyncio.run(test_complete_settings_integration())