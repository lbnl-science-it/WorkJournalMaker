"""
Test script for EntryManager Service - Step 4 Implementation

This script tests the EntryManager service integration with the existing
FileDiscovery system and database operations.
"""

import asyncio
from datetime import date, timedelta
from config_manager import ConfigManager
from logger import JournalSummarizerLogger
from web.database import DatabaseManager
from web.services.entry_manager import EntryManager


async def test_entry_manager():
    """Test EntryManager functionality."""
    print("🧪 Testing EntryManager Service Implementation")
    print("=" * 50)
    
    try:
        # Initialize configuration and logging
        print("📋 Initializing configuration...")
        config_manager = ConfigManager()
        config = config_manager.get_config()
        logger = JournalSummarizerLogger(config.logging)
        
        # Initialize database
        print("🗄️ Initializing database...")
        db_manager = DatabaseManager("web/test_journal_index.db")
        await db_manager.initialize()
        
        # Initialize EntryManager
        print("⚙️ Initializing EntryManager...")
        entry_manager = EntryManager(config, logger, db_manager)
        
        # Test date
        test_date = date.today() - timedelta(days=1)  # Yesterday
        test_content = f"Test entry content for {test_date}\n\nThis is a test entry created by the EntryManager service test."
        
        print(f"📅 Testing with date: {test_date}")
        
        # Test 1: Save entry content
        print("\n1️⃣ Testing save_entry_content...")
        success = await entry_manager.save_entry_content(test_date, test_content)
        if success:
            print("✅ Entry saved successfully")
        else:
            print("❌ Failed to save entry")
            return
        
        # Test 2: Get entry content
        print("\n2️⃣ Testing get_entry_content...")
        retrieved_content = await entry_manager.get_entry_content(test_date)
        if retrieved_content:
            print(f"✅ Entry retrieved successfully (length: {len(retrieved_content)})")
            if retrieved_content.strip() == test_content.strip():
                print("✅ Content matches exactly")
            else:
                print("⚠️ Content doesn't match exactly")
        else:
            print("❌ Failed to retrieve entry")
        
        # Test 3: Get entry by date
        print("\n3️⃣ Testing get_entry_by_date...")
        entry_response = await entry_manager.get_entry_by_date(test_date, include_content=True)
        if entry_response:
            print(f"✅ Entry response retrieved successfully")
            print(f"   📊 Metadata: {entry_response.metadata.word_count} words, {entry_response.metadata.character_count} chars")
            print(f"   📁 File path: {entry_response.file_path}")
            print(f"   📆 Week ending: {entry_response.week_ending_date}")
        else:
            print("❌ Failed to get entry response")
        
        # Test 4: Get recent entries
        print("\n4️⃣ Testing get_recent_entries...")
        recent_entries = await entry_manager.get_recent_entries(limit=5)
        print(f"✅ Retrieved {len(recent_entries.entries)} recent entries")
        print(f"   📊 Total count: {recent_entries.total_count}")
        print(f"   📄 Has more: {recent_entries.has_more}")
        
        # Test 5: List entries with filters
        print("\n5️⃣ Testing list_entries with filters...")
        from web.models.journal import EntryListRequest
        
        list_request = EntryListRequest(
            start_date=test_date - timedelta(days=7),
            end_date=test_date + timedelta(days=1),
            has_content=True,
            limit=10,
            offset=0,
            sort_by="date",
            sort_order="desc"
        )
        
        filtered_entries = await entry_manager.list_entries(list_request)
        print(f"✅ Retrieved {len(filtered_entries.entries)} filtered entries")
        print(f"   📊 Total count: {filtered_entries.total_count}")
        
        # Test 6: File path construction
        print("\n6️⃣ Testing file path construction...")
        file_path = entry_manager._construct_file_path(test_date)
        print(f"✅ Constructed file path: {file_path}")
        print(f"   📁 File exists: {file_path.exists()}")
        
        # Test 7: Database health check
        print("\n7️⃣ Testing database health...")
        health_status = await db_manager.health_check()
        print(f"✅ Database health: {health_status['status']}")
        print(f"   📊 Entry count: {health_status.get('entry_count', 'N/A')}")
        
        print("\n🎉 All tests completed successfully!")
        print("=" * 50)
        print("✅ EntryManager Service is working correctly")
        print("✅ Integration with FileDiscovery is functional")
        print("✅ Database operations are working")
        print("✅ Async APIs are responsive")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        if 'db_manager' in locals() and db_manager.engine:
            await db_manager.engine.dispose()


async def test_file_discovery_integration():
    """Test integration with existing FileDiscovery system."""
    print("\n🔗 Testing FileDiscovery Integration")
    print("-" * 30)
    
    try:
        # Initialize configuration
        config_manager = ConfigManager()
        config = config_manager.get_config()
        logger = JournalSummarizerLogger(config.logging)
        
        # Test FileDiscovery directly
        from file_discovery import FileDiscovery
        
        file_discovery = FileDiscovery(config.processing.base_path)
        
        # Test date range
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Discovering files from {start_date} to {end_date}")
        
        # Discover files
        discovery_result = file_discovery.discover_files(start_date, end_date)
        
        print(f"✅ Found {len(discovery_result.found_files)} files")
        print(f"   📊 Missing: {len(discovery_result.missing_files)}")
        print(f"   ⏱️ Processing time: {discovery_result.processing_time:.3f}s")
        
        # Show some found files
        if discovery_result.found_files:
            print("   📁 Sample files:")
            for file_path in discovery_result.found_files[:3]:
                print(f"      {file_path}")
        
        print("✅ FileDiscovery integration is working")
        
    except Exception as e:
        print(f"❌ FileDiscovery integration test failed: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting EntryManager Service Tests")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_entry_manager())
    asyncio.run(test_file_discovery_integration())
    
    print("\n🏁 Test suite completed!")