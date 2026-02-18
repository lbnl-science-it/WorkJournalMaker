"""
Test Suite for Step 2: Database Schema & Models

This test suite validates the enhanced database schema, Pydantic models,
and database operations implemented in Step 2 of the web application.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import date, datetime, timedelta
from web.database import DatabaseManager, JournalEntryIndex, WebSettings, SyncStatus
from web.models.journal import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryResponse,
    EntryListRequest, EntrySearchRequest, EntryExportRequest,
    JournalEntryMetadata, EntryStatus, CalendarEntry, CalendarMonth,
    DatabaseStats, EntryValidationResult
)
from web.models.settings import (
    WebSettingCreate, WebSettingUpdate, WebSettingResponse,
    SettingsCollection, UserPreferences, SettingsValidationResult,
    SettingValueType
)
from web.models.responses import (
    APIResponse, ErrorResponse, HealthResponse, PaginationResponse,
    OperationResponse, BulkOperationResponse, SyncStatusResponse,
    SystemStatusResponse, ExportResponse, MetricsResponse
)


class TestDatabaseSchema:
    """Test database schema and table creation."""
    
    @pytest.fixture
    async def temp_db_manager(self):
        """Create a temporary database manager for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            db_manager = DatabaseManager(db_path)
            await db_manager.initialize()
            yield db_manager
        finally:
            if db_manager.engine:
                await db_manager.engine.dispose()
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_database_initialization(self, temp_db_manager):
        """Test database initialization and table creation."""
        db_manager = temp_db_manager
        
        # Test database health check
        health = await db_manager.health_check()
        assert health["status"] == "healthy"
        assert health["entry_count"] == 0
        assert "database_path" in health
    
    async def test_journal_entry_index_table(self, temp_db_manager):
        """Test JournalEntryIndex table operations."""
        db_manager = temp_db_manager
        
        async with db_manager.get_session() as session:
            # Create test entry
            test_entry = JournalEntryIndex(
                date=date.today(),
                file_path="/test/path/worklog_2024-01-01.txt",
                week_ending_date=date.today() + timedelta(days=6),
                word_count=100,
                character_count=500,
                line_count=10,
                has_content=True,
                file_size_bytes=1024
            )
            session.add(test_entry)
            await session.commit()
            
            # Verify entry was created
            from sqlalchemy import select
            stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == date.today())
            result = await session.execute(stmt)
            retrieved_entry = result.scalar_one_or_none()
            
            assert retrieved_entry is not None
            assert retrieved_entry.word_count == 100
            assert retrieved_entry.has_content is True
    
    async def test_web_settings_table(self, temp_db_manager):
        """Test WebSettings table operations."""
        db_manager = temp_db_manager
        
        # Test setting creation and retrieval
        success = await db_manager.set_setting("test_key", "test_value", "string", "Test setting")
        assert success is True
        
        setting = await db_manager.get_setting("test_key")
        assert setting is not None
        assert setting["key"] == "test_key"
        assert setting["value"] == "test_value"
        assert setting["parsed_value"] == "test_value"
        assert setting["value_type"] == "string"
    
    async def test_sync_status_table(self, temp_db_manager):
        """Test SyncStatus table operations."""
        db_manager = temp_db_manager
        
        async with db_manager.get_session() as session:
            # Create sync status record
            sync_record = SyncStatus(
                sync_type="full",
                started_at=datetime.utcnow(),
                status="running",
                entries_processed=0
            )
            session.add(sync_record)
            await session.commit()
            
            # Verify record was created
            from sqlalchemy import select
            stmt = select(SyncStatus).where(SyncStatus.sync_type == "full")
            result = await session.execute(stmt)
            retrieved_record = result.scalar_one_or_none()
            
            assert retrieved_record is not None
            assert retrieved_record.status == "running"


class TestJournalModels:
    """Test journal entry Pydantic models."""
    
    def test_journal_entry_create_validation(self):
        """Test JournalEntryCreate model validation."""
        # Valid entry
        entry = JournalEntryCreate(
            date=date.today(),
            content="Test content"
        )
        assert entry.date == date.today()
        assert entry.content == "Test content"
        
        # Test future date validation
        with pytest.raises(ValueError, match="Entry date cannot be in the future"):
            JournalEntryCreate(
                date=date.today() + timedelta(days=1),
                content="Future content"
            )
    
    def test_entry_list_request_validation(self):
        """Test EntryListRequest model validation."""
        # Valid request
        request = EntryListRequest(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            limit=20,
            sort_by="date",
            sort_order="desc"
        )
        assert request.start_date == date(2024, 1, 1)
        assert request.limit == 20
        
        # Test invalid date range
        with pytest.raises(ValueError, match="start_date must be before or equal to end_date"):
            EntryListRequest(
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1)
            )
        
        # Test invalid sort field
        with pytest.raises(ValueError, match="sort_by must be one of"):
            EntryListRequest(sort_by="invalid_field")
    
    def test_entry_search_request_validation(self):
        """Test EntrySearchRequest model validation."""
        # Valid search request
        request = EntrySearchRequest(
            query="test search",
            search_content=True,
            limit=10
        )
        assert request.query == "test search"
        assert request.search_content is True
        
        # Test empty query validation
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            EntrySearchRequest(query="   ")
    
    def test_journal_entry_metadata(self):
        """Test JournalEntryMetadata model."""
        metadata = JournalEntryMetadata(
            word_count=100,
            character_count=500,
            line_count=10,
            file_size_bytes=1024,
            has_content=True,
            status=EntryStatus.COMPLETE
        )
        assert metadata.word_count == 100
        assert metadata.status == EntryStatus.COMPLETE
    
    def test_calendar_models(self):
        """Test calendar-related models."""
        # Test CalendarEntry
        cal_entry = CalendarEntry(
            date=date.today(),
            has_content=True,
            word_count=50,
            status=EntryStatus.COMPLETE
        )
        assert cal_entry.date == date.today()
        assert cal_entry.has_content is True
        
        # Test CalendarMonth
        cal_month = CalendarMonth(
            year=2024,
            month=1,
            month_name="January",
            entries=[cal_entry],
            today=date.today()
        )
        assert cal_month.year == 2024
        assert len(cal_month.entries) == 1


class TestSettingsModels:
    """Test settings-related Pydantic models."""
    
    def test_web_setting_create_validation(self):
        """Test WebSettingCreate model validation."""
        # Valid setting
        setting = WebSettingCreate(
            key="test_setting",
            value="test_value",
            value_type=SettingValueType.STRING,
            description="Test description"
        )
        assert setting.key == "test_setting"
        assert setting.value_type == SettingValueType.STRING
        
        # Test key format validation
        with pytest.raises(ValueError, match="Setting key must contain only alphanumeric"):
            WebSettingCreate(
                key="invalid@key",
                value="value",
                value_type=SettingValueType.STRING
            )
    
    def test_settings_collection_validation(self):
        """Test SettingsCollection model validation."""
        # Valid settings collection
        settings = SettingsCollection(
            settings={
                "theme": "dark",
                "auto_save_interval": 30,
                "show_word_count": True
            }
        )
        assert settings.settings["theme"] == "dark"
        assert settings.settings["auto_save_interval"] == 30
        
        # Test invalid key validation
        with pytest.raises(ValueError, match="Invalid setting keys"):
            SettingsCollection(
                settings={"invalid_key": "value"}
            )
    
    def test_user_preferences(self):
        """Test UserPreferences model."""
        prefs = UserPreferences(
            theme="dark",
            editor_font_size=16,
            auto_save_interval=60,
            show_word_count=True,
            calendar_start_day=1
        )
        assert prefs.theme == "dark"
        assert prefs.editor_font_size == 16
        assert prefs.calendar_start_day == 1


class TestResponseModels:
    """Test response Pydantic models."""
    
    def test_api_response(self):
        """Test APIResponse model."""
        from web.models.responses import ResponseStatus
        
        response = APIResponse(
            status=ResponseStatus.SUCCESS,
            message="Operation successful",
            data={"result": "test"}
        )
        assert response.status == ResponseStatus.SUCCESS
        assert response.message == "Operation successful"
        assert response.data["result"] == "test"
    
    def test_pagination_response(self):
        """Test PaginationResponse model."""
        pagination = PaginationResponse(
            page=2,
            per_page=10,
            total=25,
            pages=3,
            has_prev=True,
            has_next=True,
            prev_page=1,
            next_page=3
        )
        assert pagination.page == 2
        assert pagination.has_prev is True
        assert pagination.has_next is True
    
    def test_operation_response(self):
        """Test OperationResponse model."""
        response = OperationResponse(
            success=True,
            message="Operation completed",
            operation_id="op_123",
            data={"processed": 10}
        )
        assert response.success is True
        assert response.operation_id == "op_123"
        assert response.data["processed"] == 10
    
    def test_export_response(self):
        """Test ExportResponse model."""
        export_resp = ExportResponse(
            export_id="export_123",
            format="json",
            file_size_bytes=1024,
            entry_count=50,
            created_at=datetime.utcnow()
        )
        assert export_resp.export_id == "export_123"
        assert export_resp.format == "json"
        assert export_resp.entry_count == 50


class TestDatabaseManagerMethods:
    """Test DatabaseManager enhanced methods."""
    
    @pytest.fixture
    async def temp_db_manager(self):
        """Create a temporary database manager for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            db_manager = DatabaseManager(db_path)
            await db_manager.initialize()
            yield db_manager
        finally:
            if db_manager.engine:
                await db_manager.engine.dispose()
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_setting_operations(self, temp_db_manager):
        """Test setting CRUD operations."""
        db_manager = temp_db_manager
        
        # Test setting creation
        success = await db_manager.set_setting("test_key", "test_value", "string", "Test setting")
        assert success is True
        
        # Test setting retrieval
        setting = await db_manager.get_setting("test_key")
        assert setting is not None
        assert setting["parsed_value"] == "test_value"
        
        # Test setting update
        success = await db_manager.set_setting("test_key", "updated_value", "string", "Updated setting")
        assert success is True
        
        updated_setting = await db_manager.get_setting("test_key")
        assert updated_setting["parsed_value"] == "updated_value"
        
        # Test get all settings
        all_settings = await db_manager.get_all_settings()
        assert "test_key" in all_settings
        assert all_settings["test_key"] == "updated_value"
    
    async def test_value_parsing(self, temp_db_manager):
        """Test setting value parsing."""
        db_manager = temp_db_manager
        
        # Test integer parsing
        await db_manager.set_setting("int_setting", "42", "integer")
        setting = await db_manager.get_setting("int_setting")
        assert setting["parsed_value"] == 42
        assert isinstance(setting["parsed_value"], int)
        
        # Test boolean parsing
        await db_manager.set_setting("bool_setting", "true", "boolean")
        setting = await db_manager.get_setting("bool_setting")
        assert setting["parsed_value"] is True
        
        # Test float parsing
        await db_manager.set_setting("float_setting", "3.14", "float")
        setting = await db_manager.get_setting("float_setting")
        assert setting["parsed_value"] == 3.14
        assert isinstance(setting["parsed_value"], float)
    
    async def test_database_stats(self, temp_db_manager):
        """Test database statistics."""
        db_manager = temp_db_manager
        
        # Add some test data
        async with db_manager.get_session() as session:
            test_entry = JournalEntryIndex(
                date=date.today(),
                file_path="/test/path.txt",
                week_ending_date=date.today(),
                word_count=100,
                has_content=True
            )
            session.add(test_entry)
            await session.commit()
        
        # Get stats
        stats = await db_manager.get_database_stats()
        assert stats["total_entries"] == 1
        assert stats["entries_with_content"] == 1
        assert "database_size_mb" in stats


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])