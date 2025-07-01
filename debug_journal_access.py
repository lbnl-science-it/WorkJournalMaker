#!/usr/bin/env python3
"""
Debug script to diagnose journal entry access issues.
This script will help identify the root cause of the file discovery problem.
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import asyncio

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent))

from file_discovery import FileDiscovery
from config_manager import AppConfig
from logger import JournalSummarizerLogger
from web.database import DatabaseManager
from web.services.entry_manager import EntryManager

async def diagnose_journal_access():
    """Diagnose journal entry access issues."""
    print("=== Journal Access Diagnostic Tool ===\n")
    
    try:
        # 1. Test Configuration Loading
        print("1. Testing Configuration Loading...")
        config = AppConfig()
        print(f"   ✓ Config loaded successfully")
        print(f"   ✓ Base path: {config.processing.base_path}")
        
        # 2. Test Logger Initialization
        print("\n2. Testing Logger Initialization...")
        try:
            logger = JournalSummarizerLogger()
            print(f"   ✓ Logger initialized successfully")
            
            # Test debug method specifically
            if hasattr(logger, 'debug'):
                logger.debug("Test debug message")
                print("   ✓ Logger.debug() method available")
            else:
                print("   ✗ Logger.debug() method NOT available - THIS IS THE PROBLEM!")
                print("   Available methods:", [method for method in dir(logger) if not method.startswith('_')])
        except Exception as e:
            print(f"   ✗ Logger initialization failed: {e}")
        
        # 3. Test File Discovery
        print("\n3. Testing File Discovery...")
        file_discovery = FileDiscovery(config.processing.base_path)
        
        # Test recent date range
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        print(f"   Testing date range: {start_date} to {end_date}")
        result = file_discovery.discover_files(start_date, end_date)
        
        print(f"   ✓ Files found: {len(result.found_files)}")
        print(f"   ✓ Files missing: {len(result.missing_files)}")
        print(f"   ✓ Success rate: {len(result.found_files)/result.total_expected*100:.1f}%")
        
        if result.found_files:
            print("   ✓ Sample found files:")
            for i, file_path in enumerate(result.found_files[:3]):
                print(f"     - {file_path}")
                if i >= 2:
                    break
        
        # 4. Test Database Connection
        print("\n4. Testing Database Connection...")
        try:
            db_manager = DatabaseManager()
            await db_manager.initialize()
            print("   ✓ Database connection successful")
            
            # Test entry count
            async with db_manager.get_session() as session:
                from web.database import JournalEntryIndex
                from sqlalchemy import select, func
                
                count_stmt = select(func.count(JournalEntryIndex.id))
                result = await session.execute(count_stmt)
                entry_count = result.scalar()
                print(f"   ✓ Database entries: {entry_count}")
                
        except Exception as e:
            print(f"   ✗ Database connection failed: {e}")
        
        # 5. Test EntryManager
        print("\n5. Testing EntryManager...")
        try:
            entry_manager = EntryManager(config, logger, db_manager)
            print("   ✓ EntryManager initialized")
            
            # Test getting today's entry
            today = date.today()
            entry = await entry_manager.get_entry_by_date(today, include_content=False)
            if entry:
                print(f"   ✓ Today's entry found: {entry.date}")
            else:
                print(f"   - Today's entry not found (this may be normal)")
                
        except Exception as e:
            print(f"   ✗ EntryManager test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # 6. Test File Path Construction
        print("\n6. Testing File Path Construction...")
        test_date = date.today()
        file_path = file_discovery._construct_file_path(
            test_date, 
            file_discovery._calculate_week_ending_for_date(test_date)
        )
        print(f"   Expected path for {test_date}: {file_path}")
        print(f"   File exists: {file_path.exists()}")
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"   File size: {len(content)} characters")
                print(f"   Content preview: {content[:100]}...")
            except Exception as e:
                print(f"   Error reading file: {e}")
        
    except Exception as e:
        print(f"Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose_journal_access())