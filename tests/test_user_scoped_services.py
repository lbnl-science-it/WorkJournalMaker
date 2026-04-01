# ABOUTME: Tests that service methods accept user_id parameter for multi-user scoping.
# ABOUTME: Validates method signatures have user_id with default "local".
"""Tests for user-scoped service methods."""
import pytest
import inspect


class TestEntryManagerUserScope:
    def test_get_entry_by_date_accepts_user_id(self):
        """EntryManager.get_entry_by_date accepts user_id parameter."""
        from web.services.entry_manager import EntryManager
        sig = inspect.signature(EntryManager.get_entry_by_date)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"

    def test_get_entry_content_accepts_user_id(self):
        from web.services.entry_manager import EntryManager
        sig = inspect.signature(EntryManager.get_entry_content)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"

    def test_save_entry_content_accepts_user_id(self):
        from web.services.entry_manager import EntryManager
        sig = inspect.signature(EntryManager.save_entry_content)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"

    def test_get_recent_entries_accepts_user_id(self):
        from web.services.entry_manager import EntryManager
        sig = inspect.signature(EntryManager.get_recent_entries)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"

    def test_list_entries_accepts_user_id(self):
        from web.services.entry_manager import EntryManager
        sig = inspect.signature(EntryManager.list_entries)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"

    def test_delete_entry_accepts_user_id(self):
        from web.services.entry_manager import EntryManager
        sig = inspect.signature(EntryManager.delete_entry)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"


class TestCalendarServiceUserScope:
    def test_get_calendar_month_accepts_user_id(self):
        from web.services.calendar_service import CalendarService
        sig = inspect.signature(CalendarService.get_calendar_month)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"

    def test_get_entries_for_date_range_accepts_user_id(self):
        from web.services.calendar_service import CalendarService
        sig = inspect.signature(CalendarService.get_entries_for_date_range)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"

    def test_has_entry_for_date_accepts_user_id(self):
        from web.services.calendar_service import CalendarService
        sig = inspect.signature(CalendarService.has_entry_for_date)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"


class TestSettingsServiceUserScope:
    def test_get_all_settings_accepts_user_id(self):
        from web.services.settings_service import SettingsService
        sig = inspect.signature(SettingsService.get_all_settings)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"

    def test_get_setting_accepts_user_id(self):
        from web.services.settings_service import SettingsService
        sig = inspect.signature(SettingsService.get_setting)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"

    def test_update_setting_accepts_user_id(self):
        from web.services.settings_service import SettingsService
        sig = inspect.signature(SettingsService.update_setting)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"


class TestWebSummarizerUserScope:
    def test_start_summarization_accepts_user_id(self):
        from web.services.web_summarizer import WebSummarizationService
        sig = inspect.signature(WebSummarizationService.start_summarization)
        assert 'user_id' in sig.parameters
        assert sig.parameters['user_id'].default == "local"
