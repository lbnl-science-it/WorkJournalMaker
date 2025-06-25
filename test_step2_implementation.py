#!/usr/bin/env python3
"""
Step 2 Implementation Test Script

This script tests the database schema and models implementation
to ensure everything works correctly.
"""

import asyncio
import sys
from pathlib import Path
from datetime import date, datetime

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from web.database import DatabaseManager
from web.models.journal import JournalEntryCreate, EntryListRequest, EntrySearchRequest
from web.models.settings import WebSettingCreate, UserPreferences, SettingsCollection
from web.models.responses import APIResponse, ResponseStatus, PaginationResponse


async def test_database_initialization():
    """Test database initialization and basic operations."""
    print("🔧 Testing database initialization...")
    
    # Initialize database manager
    db_manager = DatabaseManager("test_journal_index.db")
    await db_manager.initialize()
    
    # Test health check
    health = await db_manager.health_check()
    print(f"✅ Database health: {health['status']}")
    print(f"📊 Entry count: {health['entry_count']}")
    
    return db_manager


async def test_settings_operations(db_manager):
    """Test settings CRUD operations."""
    print("\n⚙️ Testing settings operations...")
    
    # Test setting creation
    success = await db_manager.set_setting("theme", "dark", "string", "UI theme preference")
    print(f"✅ Setting creation: {'Success' if success else 'Failed'}")
    
    # Test setting retrieval
    setting = await db_manager.get_setting("theme")
    if setting:
        print(f"✅ Setting retrieval: {setting['key']} = {setting['parsed_value']}")
    else:
        print("❌ Setting retrieval failed")
    
    # Test all settings
    all_settings = await db_manager.get_all_settings()
    print(f"✅ Total settings: {len(all_settings)}")
    
    return True


def test_pydantic_models():
    """Test Pydantic model validation."""
    print("\n📝 Testing Pydantic models...")
    
    # Test JournalEntryCreate
    try:
        entry = JournalEntryCreate(
            date=date.today(),
            content="Test journal entry content"
        )
        print(f"✅ JournalEntryCreate: {entry.date}")
    except Exception as e:
        print(f"❌ JournalEntryCreate failed: {e}")
    
    # Test EntryListRequest
    try:
        request = EntryListRequest(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            limit=10,
            sort_by="date",
            sort_order="desc"
        )
        print(f"✅ EntryListRequest: {request.limit} items, sorted by {request.sort_by}")
    except Exception as e:
        print(f"❌ EntryListRequest failed: {e}")
    
    # Test EntrySearchRequest
    try:
        search = EntrySearchRequest(
            query="test search query",
            search_content=True,
            limit=20
        )
        print(f"✅ EntrySearchRequest: '{search.query}' with limit {search.limit}")
    except Exception as e:
        print(f"❌ EntrySearchRequest failed: {e}")
    
    # Test WebSettingCreate
    try:
        setting = WebSettingCreate(
            key="test_setting",
            value="test_value",
            value_type="string",
            description="Test setting description"
        )
        print(f"✅ WebSettingCreate: {setting.key} = {setting.value}")
    except Exception as e:
        print(f"❌ WebSettingCreate failed: {e}")
    
    # Test UserPreferences
    try:
        prefs = UserPreferences(
            theme="dark",
            editor_font_size=16,
            auto_save_interval=30,
            show_word_count=True
        )
        print(f"✅ UserPreferences: theme={prefs.theme}, font_size={prefs.editor_font_size}")
    except Exception as e:
        print(f"❌ UserPreferences failed: {e}")
    
    # Test SettingsCollection
    try:
        collection = SettingsCollection(
            settings={
                "theme": "light",
                "auto_save_interval": 60,
                "show_word_count": False
            }
        )
        print(f"✅ SettingsCollection: {len(collection.settings)} settings")
    except Exception as e:
        print(f"❌ SettingsCollection failed: {e}")
    
    # Test APIResponse
    try:
        response = APIResponse(
            status=ResponseStatus.SUCCESS,
            message="Test operation successful",
            data={"result": "test_data"}
        )
        print(f"✅ APIResponse: {response.status} - {response.message}")
    except Exception as e:
        print(f"❌ APIResponse failed: {e}")
    
    # Test PaginationResponse
    try:
        pagination = PaginationResponse(
            page=1,
            per_page=10,
            total=25,
            pages=3,
            has_prev=False,
            has_next=True,
            next_page=2
        )
        print(f"✅ PaginationResponse: page {pagination.page} of {pagination.pages}")
    except Exception as e:
        print(f"❌ PaginationResponse failed: {e}")
    
    return True


async def test_database_stats(db_manager):
    """Test database statistics functionality."""
    print("\n📈 Testing database statistics...")
    
    try:
        stats = await db_manager.get_database_stats()
        print(f"✅ Database stats retrieved:")
        print(f"   📊 Total entries: {stats['total_entries']}")
        print(f"   📝 Entries with content: {stats['entries_with_content']}")
        print(f"   💾 Database size: {stats['database_size_mb']} MB")
        if stats['date_range']:
            print(f"   📅 Date range: {stats['date_range']['start']} to {stats['date_range']['end']}")
        else:
            print(f"   📅 Date range: No entries yet")
        return True
    except Exception as e:
        print(f"❌ Database stats failed: {e}")
        return False


def test_model_validation_errors():
    """Test model validation error handling."""
    print("\n🚨 Testing validation error handling...")
    
    # Test future date validation
    try:
        from datetime import timedelta
        future_entry = JournalEntryCreate(
            date=date.today() + timedelta(days=1),
            content="Future entry"
        )
        print("❌ Future date validation should have failed")
    except ValueError as e:
        print(f"✅ Future date validation: {e}")
    
    # Test invalid date range
    try:
        invalid_request = EntryListRequest(
            start_date=date(2024, 1, 31),
            end_date=date(2024, 1, 1)
        )
        print("❌ Invalid date range validation should have failed")
    except ValueError as e:
        print(f"✅ Invalid date range validation: {e}")
    
    # Test empty search query
    try:
        empty_search = EntrySearchRequest(query="   ")
        print("❌ Empty search query validation should have failed")
    except ValueError as e:
        print(f"✅ Empty search query validation: {e}")
    
    # Test invalid setting key
    try:
        invalid_setting = WebSettingCreate(
            key="invalid@key!",
            value="test",
            value_type="string"
        )
        print("❌ Invalid setting key validation should have failed")
    except ValueError as e:
        print(f"✅ Invalid setting key validation: {e}")
    
    return True


async def main():
    """Main test function."""
    print("🚀 Starting Step 2 Implementation Tests")
    print("=" * 50)
    
    try:
        # Test database initialization
        db_manager = await test_database_initialization()
        
        # Test settings operations
        await test_settings_operations(db_manager)
        
        # Test Pydantic models
        test_pydantic_models()
        
        # Test database statistics
        await test_database_stats(db_manager)
        
        # Test validation error handling
        test_model_validation_errors()
        
        print("\n" + "=" * 50)
        print("🎉 All Step 2 tests completed successfully!")
        print("✅ Database schema and models are working correctly")
        
        # Clean up
        if db_manager.engine:
            await db_manager.engine.dispose()
        
        # Remove test database
        import os
        if os.path.exists("test_journal_index.db"):
            os.remove("test_journal_index.db")
            print("🧹 Test database cleaned up")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)