#!/usr/bin/env python3
"""
Debug script to diagnose settings integration issues.
This script will check if settings are being saved and retrieved correctly.
"""

import asyncio
from datetime import date, datetime

from web.database import DatabaseManager, WebSettings
from web.services.settings_service import SettingsService
from web.services.work_week_service import WorkWeekService
from config_manager import ConfigManager
from logger import JournalSummarizerLogger
from sqlalchemy import select

async def debug_settings_integration():
    """Debug the settings integration issue."""
    print("🔍 Debugging Settings Integration Issue")
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
    
    print("\n1. 📋 Checking all settings in database:")
    async with db_manager.get_session() as session:
        stmt = select(WebSettings)
        result = await session.execute(stmt)
        all_settings = result.scalars().all()
        
        print(f"   Total settings found: {len(all_settings)}")
        for setting in all_settings:
            print(f"   - Key: '{setting.key}' = '{setting.value}'")
    
    print("\n2. 🔧 Checking work week specific settings:")
    work_week_keys = [
        "work_week.preset",
        "work_week.start_day", 
        "work_week.end_day",
        "work_week.timezone"
    ]
    
    async with db_manager.get_session() as session:
        for key in work_week_keys:
            stmt = select(WebSettings).where(WebSettings.key == key)
            result = await session.execute(stmt)
            setting = result.scalar_one_or_none()
            if setting:
                print(f"   ✅ {key}: '{setting.value}'")
            else:
                print(f"   ❌ {key}: NOT FOUND")
    
    print("\n3. 🏗️ Testing WorkWeekService configuration retrieval:")
    try:
        work_week_config = await work_week_service.get_user_work_week_config()
        print(f"   ✅ Retrieved config:")
        print(f"      - Preset: {work_week_config.preset.value}")
        print(f"      - Start Day: {work_week_config.start_day}")
        print(f"      - End Day: {work_week_config.end_day}")
        print(f"      - Timezone: {work_week_config.timezone}")
    except Exception as e:
        print(f"   ❌ Failed to retrieve work week config: {e}")
    
    print("\n4. 📅 Testing week ending calculation:")
    test_date = date.today()
    try:
        week_ending = await work_week_service.calculate_week_ending_date(test_date)
        print(f"   ✅ Week ending for {test_date}: {week_ending}")
    except Exception as e:
        print(f"   ❌ Failed to calculate week ending: {e}")
    
    print("\n5. 🔄 Testing SettingsService work week methods:")
    try:
        settings_work_week = await settings_service.get_work_week_settings()
        print(f"   ✅ SettingsService work week settings:")
        for key, value in settings_work_week.items():
            print(f"      - {key}: {value}")
    except Exception as e:
        print(f"   ❌ Failed to get work week settings from SettingsService: {e}")
    
    print("\n6. 🎯 Diagnosis Summary:")
    print("   Checking for key mismatches...")
    
    # Check if settings service uses different keys
    try:
        all_settings_from_service = await settings_service.get_all_settings()
        work_week_related = {k: v for k, v in all_settings_from_service.items() 
                           if 'work' in k.lower() or 'week' in k.lower()}
        
        if work_week_related:
            print("   📋 Work week related settings from SettingsService:")
            for key, setting in work_week_related.items():
                print(f"      - {key}: {setting.value if hasattr(setting, 'value') else setting}")
        else:
            print("   ⚠️  No work week related settings found in SettingsService")
            
    except Exception as e:
        print(f"   ❌ Error checking SettingsService: {e}")
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(debug_settings_integration())