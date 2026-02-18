"""
Comprehensive Tests for Calendar API Endpoints

This module contains tests for all calendar API endpoints including:
- Calendar month data retrieval
- Navigation functionality
- Date range queries
- Entry existence checking
- Today's information
- Calendar statistics
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from web.app import app
from web.services.calendar_service import CalendarService
from web.models.journal import CalendarMonth, CalendarEntry, TodayResponse, EntryStatus


class TestCalendarAPIEndpoints:
    """Test suite for Calendar API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_calendar_service(self):
        """Create mock calendar service."""
        service = AsyncMock(spec=CalendarService)
        return service
    
    @pytest.fixture
    def sample_calendar_month(self):
        """Sample calendar month data."""
        entries = [
            CalendarEntry(
                date=date(2024, 1, 1),
                has_content=True,
                word_count=150,
                status=EntryStatus.COMPLETE
            ),
            CalendarEntry(
                date=date(2024, 1, 2),
                has_content=False,
                word_count=0,
                status=EntryStatus.EMPTY
            ),
            CalendarEntry(
                date=date(2024, 1, 3),
                has_content=True,
                word_count=200,
                status=EntryStatus.COMPLETE
            )
        ]
        
        return CalendarMonth(
            year=2024,
            month=1,
            month_name="January",
            entries=entries,
            today=date.today()
        )
    
    @pytest.fixture
    def sample_today_response(self):
        """Sample today response data."""
        return TodayResponse(
            today=date.today(),
            day_name=date.today().strftime("%A"),
            formatted_date=date.today().strftime("%B %d, %Y"),
            has_entry=True,
            entry_metadata={"word_count": 150, "has_content": True},
            week_ending_date=date.today() + timedelta(days=4),
            current_month=date.today().month,
            current_year=date.today().year
        )
    
    def test_get_today_info_success(self, client, mock_calendar_service, sample_today_response):
        """Test successful retrieval of today's information."""
        # Mock the service method
        mock_calendar_service.get_today_info.return_value = {
            "today": sample_today_response.today,
            "day_name": sample_today_response.day_name,
            "formatted_date": sample_today_response.formatted_date,
            "has_entry": sample_today_response.has_entry,
            "entry_metadata": sample_today_response.entry_metadata,
            "week_ending_date": sample_today_response.week_ending_date,
            "current_month": sample_today_response.current_month,
            "current_year": sample_today_response.current_year
        }
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/today")
        
        assert response.status_code == 200
        data = response.json()
        assert data["today"] == str(sample_today_response.today)
        assert data["has_entry"] == sample_today_response.has_entry
        assert data["entry_metadata"] == sample_today_response.entry_metadata
    
    def test_get_today_info_service_error(self, client, mock_calendar_service):
        """Test today info endpoint when service raises an error."""
        mock_calendar_service.get_today_info.side_effect = Exception("Service error")
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/today")
        
        assert response.status_code == 500
        assert "Failed to retrieve today's information" in response.json()["detail"]
    
    def test_get_calendar_month_success(self, client, mock_calendar_service, sample_calendar_month):
        """Test successful retrieval of calendar month data."""
        mock_calendar_service.get_calendar_month.return_value = sample_calendar_month
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/2024/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2024
        assert data["month"] == 1
        assert data["month_name"] == "January"
        assert len(data["entries"]) == 3
        
        # Verify service was called with correct parameters
        mock_calendar_service.get_calendar_month.assert_called_once_with(2024, 1)
    
    def test_get_calendar_month_invalid_year(self, client, mock_calendar_service):
        """Test calendar month endpoint with invalid year."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/1800/1")
        
        assert response.status_code == 400
        assert "Invalid year" in response.json()["detail"]
    
    def test_get_calendar_month_invalid_month(self, client, mock_calendar_service):
        """Test calendar month endpoint with invalid month."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/2024/13")
        
        assert response.status_code == 400
        assert "Invalid month" in response.json()["detail"]
    
    def test_get_calendar_month_service_error(self, client, mock_calendar_service):
        """Test calendar month endpoint when service raises an error."""
        mock_calendar_service.get_calendar_month.side_effect = Exception("Service error")
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/2024/1")
        
        assert response.status_code == 500
        assert "Failed to retrieve calendar data" in response.json()["detail"]
    
    def test_get_calendar_navigation_success(self, client, mock_calendar_service):
        """Test successful retrieval of calendar navigation data."""
        mock_calendar_service.get_adjacent_months.return_value = ((2023, 12), (2024, 2))
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/2024/1/navigation")
        
        assert response.status_code == 200
        data = response.json()
        assert data["current"]["year"] == 2024
        assert data["current"]["month"] == 1
        assert data["previous"]["year"] == 2023
        assert data["previous"]["month"] == 12
        assert data["next"]["year"] == 2024
        assert data["next"]["month"] == 2
        assert "today" in data
    
    def test_get_calendar_navigation_invalid_params(self, client, mock_calendar_service):
        """Test calendar navigation with invalid parameters."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/1800/1/navigation")
        
        assert response.status_code == 400
        assert "Invalid year" in response.json()["detail"]
    
    def test_check_entry_exists_success(self, client, mock_calendar_service):
        """Test successful entry existence check."""
        test_date = date(2024, 1, 15)
        mock_calendar_service.has_entry_for_date.return_value = True
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get(f"/api/calendar/date/{test_date}/exists")
        
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == str(test_date)
        assert data["has_entry"] is True
        assert data["formatted_date"] == test_date.strftime("%B %d, %Y")
        assert data["day_name"] == test_date.strftime("%A")
    
    def test_check_entry_exists_service_error(self, client, mock_calendar_service):
        """Test entry existence check when service raises an error."""
        test_date = date(2024, 1, 15)
        mock_calendar_service.has_entry_for_date.side_effect = Exception("Service error")
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get(f"/api/calendar/date/{test_date}/exists")
        
        assert response.status_code == 500
        assert "Failed to check entry existence" in response.json()["detail"]
    
    def test_get_entries_in_range_success(self, client, mock_calendar_service):
        """Test successful retrieval of entries in date range."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        sample_entries = [
            CalendarEntry(
                date=date(2024, 1, 1),
                has_content=True,
                word_count=150,
                status=EntryStatus.COMPLETE
            ),
            CalendarEntry(
                date=date(2024, 1, 15),
                has_content=True,
                word_count=200,
                status=EntryStatus.COMPLETE
            )
        ]
        
        mock_calendar_service.get_entries_for_date_range.return_value = sample_entries
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get(f"/api/calendar/range/{start_date}/{end_date}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["date"] == str(date(2024, 1, 1))
        assert data[0]["has_content"] is True
        assert data[0]["word_count"] == 150
    
    def test_get_entries_in_range_invalid_range(self, client, mock_calendar_service):
        """Test entries in range with invalid date range."""
        start_date = date(2024, 1, 31)
        end_date = date(2024, 1, 1)  # End before start
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get(f"/api/calendar/range/{start_date}/{end_date}")
        
        assert response.status_code == 400
        assert "Start date must be before or equal to end date" in response.json()["detail"]
    
    def test_get_entries_in_range_too_large(self, client, mock_calendar_service):
        """Test entries in range with too large date range."""
        start_date = date(2024, 1, 1)
        end_date = date(2025, 1, 2)  # More than 365 days
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get(f"/api/calendar/range/{start_date}/{end_date}")
        
        assert response.status_code == 400
        assert "Date range cannot exceed 365 days" in response.json()["detail"]
    
    def test_get_current_month_success(self, client, mock_calendar_service, sample_calendar_month):
        """Test successful retrieval of current month data."""
        today = date.today()
        current_month_data = CalendarMonth(
            year=today.year,
            month=today.month,
            month_name=today.strftime("%B"),
            entries=[],
            today=today
        )
        
        mock_calendar_service.get_calendar_month.return_value = current_month_data
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/current")
        
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == today.year
        assert data["month"] == today.month
    
    def test_get_week_info_success(self, client, mock_calendar_service):
        """Test successful retrieval of week information."""
        test_date = date(2024, 1, 15)
        week_ending = date(2024, 1, 19)  # Friday
        week_start = date(2024, 1, 15)   # Monday
        
        sample_entries = [
            CalendarEntry(
                date=date(2024, 1, 15),
                has_content=True,
                word_count=150,
                status=EntryStatus.COMPLETE
            ),
            CalendarEntry(
                date=date(2024, 1, 16),
                has_content=False,
                word_count=0,
                status=EntryStatus.EMPTY
            )
        ]
        
        mock_calendar_service.get_week_ending_date.return_value = week_ending
        mock_calendar_service.get_entries_for_date_range.return_value = sample_entries
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get(f"/api/calendar/week/{test_date}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["entry_date"] == str(test_date)
        assert data["week_ending"] == str(week_ending)
        assert data["total_entries"] == 1  # Only entries with content
        assert len(data["entries"]) == 2
    
    def test_get_calendar_stats_success(self, client, mock_calendar_service):
        """Test successful retrieval of calendar statistics."""
        sample_entries = [
            CalendarEntry(
                date=date(2024, 1, 1),
                has_content=True,
                word_count=150,
                status=EntryStatus.COMPLETE
            ),
            CalendarEntry(
                date=date(2024, 1, 2),
                has_content=True,
                word_count=200,
                status=EntryStatus.COMPLETE
            ),
            CalendarEntry(
                date=date(2024, 1, 3),
                has_content=False,
                word_count=0,
                status=EntryStatus.EMPTY
            )
        ]
        
        mock_calendar_service.get_entries_for_date_range.return_value = sample_entries
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/stats?year=2024&month=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["period"]["year"] == 2024
        assert data["period"]["month"] == 1
        assert data["entries"]["total_entries"] == 3
        assert data["entries"]["entries_with_content"] == 2
        assert data["entries"]["empty_entries"] == 1
        assert data["content"]["total_words"] == 350
        assert data["content"]["average_words_per_entry"] == 175.0
    
    def test_get_calendar_stats_invalid_year(self, client, mock_calendar_service):
        """Test calendar stats with invalid year."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/stats?year=1800")
        
        assert response.status_code == 400
        assert "Invalid year" in response.json()["detail"]
    
    def test_get_calendar_stats_invalid_month(self, client, mock_calendar_service):
        """Test calendar stats with invalid month."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/stats?year=2024&month=13")
        
        assert response.status_code == 400
        assert "Invalid month" in response.json()["detail"]
    
    def test_get_year_overview_success(self, client, mock_calendar_service):
        """Test successful retrieval of year overview."""
        # Mock entries for different months
        mock_calendar_service.get_entries_for_date_range.side_effect = [
            # January - 2 entries with content out of 31 days
            [CalendarEntry(date=date(2024, 1, 1), has_content=True, word_count=150, status=EntryStatus.COMPLETE),
             CalendarEntry(date=date(2024, 1, 2), has_content=True, word_count=200, status=EntryStatus.COMPLETE)],
            # February - 1 entry with content out of 29 days (leap year)
            [CalendarEntry(date=date(2024, 2, 1), has_content=True, word_count=100, status=EntryStatus.COMPLETE)],
            # March through December - empty lists for simplicity
            [], [], [], [], [], [], [], [], [], []
        ]
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/months/2024")
        
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2024
        assert len(data["months"]) == 12
        
        # Check January data
        january = data["months"][0]
        assert january["month"] == 1
        assert january["month_name"] == "January"
        assert january["total_days"] == 31
        assert january["entries_with_content"] == 2
        assert january["completion_rate"] == round((2/31) * 100, 2)
        
        # Check February data
        february = data["months"][1]
        assert february["month"] == 2
        assert february["month_name"] == "February"
        assert february["total_days"] == 29  # Leap year
        assert february["entries_with_content"] == 1
    
    def test_get_year_overview_invalid_year(self, client, mock_calendar_service):
        """Test year overview with invalid year."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/months/1800")
        
        assert response.status_code == 400
        assert "Invalid year" in response.json()["detail"]
    
    def test_get_year_overview_service_error(self, client, mock_calendar_service):
        """Test year overview when service raises an error."""
        mock_calendar_service.get_entries_for_date_range.side_effect = Exception("Service error")
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            response = client.get("/api/calendar/months/2024")
        
        assert response.status_code == 500
        assert "Failed to retrieve year overview" in response.json()["detail"]


class TestCalendarAPIIntegration:
    """Integration tests for Calendar API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_api_endpoint_accessibility(self, client):
        """Test that all calendar API endpoints are accessible."""
        # Note: These tests will fail without proper app state setup
        # but they verify the endpoints are properly registered
        
        endpoints_to_test = [
            "/api/calendar/today",
            "/api/calendar/2024/1",
            "/api/calendar/2024/1/navigation",
            "/api/calendar/date/2024-01-01/exists",
            "/api/calendar/range/2024-01-01/2024-01-31",
            "/api/calendar/current",
            "/api/calendar/week/2024-01-15",
            "/api/calendar/stats",
            "/api/calendar/months/2024"
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            # Should not return 404 (endpoint not found)
            assert response.status_code != 404, f"Endpoint {endpoint} not found"
    
    def test_calendar_api_error_handling(self, client):
        """Test error handling across calendar API endpoints."""
        # Test invalid date formats
        response = client.get("/api/calendar/date/invalid-date/exists")
        assert response.status_code == 422  # Validation error
        
        # Test invalid date range
        response = client.get("/api/calendar/range/invalid-start/invalid-end")
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])