#!/usr/bin/env python3
"""
Test script to verify the logger fix works correctly.
"""

import sys
from datetime import date
import asyncio

from config_manager import AppConfig
from logger import JournalSummarizerLogger, LogConfig
from web.database import DatabaseManager
from web.services.entry_manager import EntryManager

async def test_logger_fix():
    """Test that the logger fix resolves the debug method issue."""
    print("=== Testing Logger Fix ===\n")
    
    try:
        # 1. Create proper config and logger
        print("1. Creating configuration and logger...")
        config = AppConfig()
        
        # Create LogConfig from AppConfig
        log_config = LogConfig(
            level=config.logging.level,
            console_output=config.logging.console_output,
            file_output=config.logging.file_output,
            log_dir=config.logging.log_dir,
            include_timestamps=config.logging.include_timestamps,
            include_module_names=config.logging.include_module_names,
            max_file_size_mb=config.logging.max_file_size_mb,
            backup_count=config.logging.backup_count
        )
        
        logger = JournalSummarizerLogger(log_config)
        print("   ✓ Logger created successfully")
        
        # 2. Test database connection
        print("\n2. Testing database connection...")
        db_manager = DatabaseManager()
        await db_manager.initialize()
        print("   ✓ Database initialized")
        
        # 3. Test EntryManager creation
        print("\n3. Testing EntryManager creation...")
        entry_manager = EntryManager(config, logger, db_manager)
        print("   ✓ EntryManager created successfully")
        
        # 4. Test getting an entry (this should not crash with debug error)
        print("\n4. Testing entry retrieval...")
        today = date.today()
        try:
            entry = await entry_manager.get_entry_by_date(today, include_content=False)
            if entry:
                print(f"   ✓ Entry found for {today}: {entry.date}")
            else:
                print(f"   ✓ No entry found for {today} (this is normal)")
            print("   ✓ No logger.debug() errors occurred!")
        except Exception as e:
            print(f"   ✗ Entry retrieval failed: {e}")
            return False
        
        # 5. Test getting entry content (this was failing before)
        print("\n5. Testing entry content retrieval...")
        try:
            content = await entry_manager.get_entry_content(today)
            if content:
                print(f"   ✓ Entry content retrieved: {len(content)} characters")
            else:
                print("   ✓ No content found (this is normal if no entry exists)")
            print("   ✓ No logger.debug() errors occurred!")
        except Exception as e:
            print(f"   ✗ Entry content retrieval failed: {e}")
            return False
        
        print("\n=== Logger Fix Test PASSED ===")
        return True
        
    except Exception as e:
        print(f"\n=== Logger Fix Test FAILED ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_logger_fix())
    sys.exit(0 if success else 1)