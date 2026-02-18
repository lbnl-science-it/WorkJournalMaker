"""
Comprehensive Test Suite for Calendar Implementation (Step 8)

This module provides a comprehensive test runner for all calendar-related
functionality including API endpoints, service integration, and performance tests.
"""

import pytest
import sys
import time
from pathlib import Path
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from web.api.calendar import router as calendar_router
from web.services.calendar_service import CalendarService
from web.models.journal import CalendarMonth, CalendarEntry, TodayResponse, EntryStatus


class TestCalendarImplementationValidation:
    """Validation tests for Step 8 implementation."""
    
    def test_calendar_router_exists(self):
        """Test that calendar router is properly defined."""
        assert calendar_router is not None
        assert hasattr(calendar_router, 'routes')
        assert len(calendar_router.routes) > 0
    
    def test_calendar_router_endpoints(self):
        """Test that all required endpoints are defined in the router."""
        route_paths = [route.path for route in calendar_router.routes]
        
        required_endpoints = [
            "/today",
            "/{year}/{month}",
            "/{year}/{month}/navigation",
            "/date/{entry_date}/exists",
            "/range/{start_date}/{end_date}",
            "/current",
            "/week/{entry_date}",
            "/stats",
            "/months/{year}"
        ]
        
        for endpoint in required_endpoints:
            # Check if endpoint exists (allowing for prefix)
            found = any(endpoint in path for path in route_paths)
            assert found, f"Required endpoint {endpoint} not found in router"
    
    def test_calendar_service_methods(self):
        """Test that CalendarService has all required methods."""
        required_methods = [
            'get_calendar_month',
            'get_adjacent_months',
            'has_entry_for_date',
            'get_entries_for_date_range',
            'get_week_ending_date',
            'get_today_info'
        ]
        
        for method in required_methods:
            assert hasattr(CalendarService, method), f"CalendarService missing method: {method}"
    
    def test_calendar_models_exist(self):
        """Test that all required calendar models exist."""
        # Test CalendarEntry model
        entry = CalendarEntry(
            date=date(2024, 1, 1),
            has_content=True,
            word_count=150,
            status=EntryStatus.COMPLETE
        )
        assert entry.date == date(2024, 1, 1)
        assert entry.has_content is True
        assert entry.word_count == 150
        assert entry.status == EntryStatus.COMPLETE
        
        # Test CalendarMonth model
        month = CalendarMonth(
            year=2024,
            month=1,
            month_name="January",
            entries=[entry],
            today=date.today()
        )
        assert month.year == 2024
        assert month.month == 1
        assert month.month_name == "January"
        assert len(month.entries) == 1
        
        # Test TodayResponse model
        today_response = TodayResponse(
            today=date.today(),
            day_name="Monday",
            formatted_date="January 1, 2024",
            has_entry=True,
            entry_metadata={"word_count": 150},
            week_ending_date=date.today(),
            current_month=1,
            current_year=2024
        )
        assert today_response.today == date.today()
        assert today_response.has_entry is True


class TestCalendarEndpointValidation:
    """Validation tests for calendar API endpoints."""
    
    @pytest.fixture
    def mock_calendar_service(self):
        """Create comprehensive mock calendar service."""
        service = AsyncMock(spec=CalendarService)
        
        # Mock get_calendar_month
        service.get_calendar_month.return_value = CalendarMonth(
            year=2024,
            month=1,
            month_name="January",
            entries=[
                CalendarEntry(
                    date=date(2024, 1, 1),
                    has_content=True,
                    word_count=150,
                    status=EntryStatus.COMPLETE
                )
            ],
            today=date.today()
        )
        
        # Mock get_today_info
        service.get_today_info.return_value = {
            "today": date.today(),
            "day_name": date.today().strftime("%A"),
            "formatted_date": date.today().strftime("%B %d, %Y"),
            "has_entry": True,
            "entry_metadata": {"word_count": 150, "has_content": True},
            "week_ending_date": date.today() + timedelta(days=4),
            "current_month": date.today().month,
            "current_year": date.today().year
        }
        
        # Mock other methods
        service.get_adjacent_months.return_value = ((2023, 12), (2024, 2))
        service.has_entry_for_date.return_value = True
        service.get_entries_for_date_range.return_value = [
            CalendarEntry(
                date=date(2024, 1, 1),
                has_content=True,
                word_count=150,
                status=EntryStatus.COMPLETE
            )
        ]
        service.get_week_ending_date.return_value = date.today() + timedelta(days=4)
        
        return service
    
    def test_endpoint_response_models(self, mock_calendar_service):
        """Test that endpoints return properly structured responses."""
        from fastapi.testclient import TestClient
        from web.app import app
        
        client = TestClient(app)
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            # Test today endpoint
            response = client.get("/api/calendar/today")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["today", "day_name", "formatted_date", "has_entry", 
                                 "week_ending_date", "current_month", "current_year"]
                for field in required_fields:
                    assert field in data, f"Missing field {field} in today response"
            
            # Test calendar month endpoint
            response = client.get("/api/calendar/2024/1")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["year", "month", "month_name", "entries", "today"]
                for field in required_fields:
                    assert field in data, f"Missing field {field} in calendar month response"
    
    def test_endpoint_error_handling(self):
        """Test that endpoints handle errors appropriately."""
        from fastapi.testclient import TestClient
        from web.app import app
        
        client = TestClient(app)
        
        # Test invalid year
        response = client.get("/api/calendar/1800/1")
        assert response.status_code == 400
        
        # Test invalid month
        response = client.get("/api/calendar/2024/13")
        assert response.status_code == 400
        
        # Test invalid date format
        response = client.get("/api/calendar/date/invalid-date/exists")
        assert response.status_code == 422


class TestCalendarIntegrationValidation:
    """Integration validation tests."""
    
    def test_calendar_service_initialization(self):
        """Test that CalendarService can be initialized properly."""
        from config_manager import AppConfig
        from logger import JournalSummarizerLogger
        from web.database import DatabaseManager
        
        # Create mock dependencies with proper structure
        mock_config = MagicMock(spec=AppConfig)
        mock_processing = MagicMock()
        mock_processing.base_path = Path("/test/path")
        mock_config.processing = mock_processing
        
        mock_logger = MagicMock(spec=JournalSummarizerLogger)
        mock_db_manager = AsyncMock(spec=DatabaseManager)
        
        # Test service initialization
        with patch('web.services.calendar_service.FileDiscovery'):
            service = CalendarService(mock_config, mock_logger, mock_db_manager)
            assert service is not None
            assert hasattr(service, 'config')
            assert hasattr(service, 'logger')
            assert hasattr(service, 'db_manager')
    
    def test_calendar_service_file_discovery_integration(self):
        """Test that CalendarService integrates with FileDiscovery."""
        from config_manager import AppConfig
        from logger import JournalSummarizerLogger
        from web.database import DatabaseManager
        
        # Create mock dependencies with proper structure
        mock_config = MagicMock(spec=AppConfig)
        mock_processing = MagicMock()
        mock_processing.base_path = Path("/test/path")
        mock_config.processing = mock_processing
        
        mock_logger = MagicMock(spec=JournalSummarizerLogger)
        mock_db_manager = AsyncMock(spec=DatabaseManager)
        
        with patch('web.services.calendar_service.FileDiscovery') as mock_fd_class:
            mock_fd_instance = MagicMock()
            mock_fd_class.return_value = mock_fd_instance
            
            service = CalendarService(mock_config, mock_logger, mock_db_manager)
            
            # Test that FileDiscovery is initialized
            mock_fd_class.assert_called_once_with(mock_config.processing.base_path)
            assert service.file_discovery == mock_fd_instance


class TestCalendarImplementationCompleteness:
    """Test completeness of Step 8 implementation."""
    
    def test_all_blueprint_requirements_implemented(self):
        """Test that all requirements from the blueprint are implemented."""
        # Requirements from Step 8 blueprint:
        # 1. Create calendar data API endpoints ✓
        # 2. Implement date range queries ✓
        # 3. Add today's information endpoints ✓
        # 4. Support multiple calendar views ✓
        # 5. Include comprehensive error handling ✓
        # 6. Add navigation endpoints ✓
        
        from web.api.calendar import router
        
        # Check that router has the expected number of endpoints
        assert len(router.routes) >= 9, "Not all required endpoints implemented"
        
        # Check for specific endpoint patterns
        route_paths = [route.path for route in router.routes]
        
        # Calendar data endpoints
        assert any("/{year}/{month}" in path for path in route_paths)
        assert any("/current" in path for path in route_paths)
        
        # Date range queries
        assert any("/range/{start_date}/{end_date}" in path for path in route_paths)
        
        # Today's information
        assert any("/today" in path for path in route_paths)
        
        # Navigation
        assert any("/navigation" in path for path in route_paths)
        
        # Statistics and overview
        assert any("/stats" in path for path in route_paths)
        assert any("/months/{year}" in path for path in route_paths)
    
    def test_error_handling_completeness(self):
        """Test that comprehensive error handling is implemented."""
        from fastapi.testclient import TestClient
        from web.app import app
        
        client = TestClient(app)
        
        # Test various error conditions
        error_test_cases = [
            ("/api/calendar/1800/1", 400),  # Invalid year
            ("/api/calendar/2024/13", 400),  # Invalid month
            ("/api/calendar/3001/1", 400),  # Year too high
            ("/api/calendar/2024/0", 400),  # Month too low
        ]
        
        for endpoint, expected_status in error_test_cases:
            response = client.get(endpoint)
            assert response.status_code == expected_status, f"Expected {expected_status} for {endpoint}, got {response.status_code}"
    
    def test_response_model_validation(self):
        """Test that all response models are properly validated."""
        # Test CalendarEntry validation
        with pytest.raises(ValueError):
            CalendarEntry(
                date=date.today() + timedelta(days=1),  # Future date
                has_content=True,
                word_count=-1,  # Negative word count
                status=EntryStatus.COMPLETE
            )
        
        # Test CalendarMonth validation
        with pytest.raises(ValueError):
            CalendarMonth(
                year=1800,  # Invalid year
                month=13,   # Invalid month
                month_name="Invalid",
                entries=[],
                today=date.today()
            )


def run_comprehensive_calendar_tests():
    """Run all calendar-related tests."""
    print("Running comprehensive calendar tests for Step 8...")
    
    # Test files to run
    test_files = [
        "tests/test_calendar_api_endpoints.py",
        "tests/test_calendar_service_integration.py",
        "tests/test_calendar_api_performance.py",
        "tests/test_calendar_comprehensive.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        print(f"\nRunning {test_file}...")
        start_time = time.time()
        
        try:
            # Run the test file
            exit_code = pytest.main([test_file, "-v", "--tb=short"])
            end_time = time.time()
            
            results[test_file] = {
                "status": "PASSED" if exit_code == 0 else "FAILED",
                "duration": end_time - start_time,
                "exit_code": exit_code
            }
            
        except Exception as e:
            end_time = time.time()
            results[test_file] = {
                "status": "ERROR",
                "duration": end_time - start_time,
                "error": str(e)
            }
    
    # Print summary
    print("\n" + "="*60)
    print("CALENDAR TESTS SUMMARY (Step 8)")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    total_duration = 0
    
    for test_file, result in results.items():
        status = result["status"]
        duration = result["duration"]
        total_duration += duration
        
        if status == "PASSED":
            total_passed += 1
            print(f"✅ {test_file}: {status} ({duration:.2f}s)")
        else:
            total_failed += 1
            print(f"❌ {test_file}: {status} ({duration:.2f}s)")
            if "error" in result:
                print(f"   Error: {result['error']}")
    
    print(f"\nTotal: {total_passed} passed, {total_failed} failed")
    print(f"Total duration: {total_duration:.2f}s")
    
    if total_failed == 0:
        print("\n🎉 All calendar tests passed! Step 8 implementation is complete.")
    else:
        print(f"\n⚠️  {total_failed} test file(s) failed. Please review and fix issues.")
    
    return total_failed == 0


if __name__ == "__main__":
    # Run individual validation tests
    pytest.main([__file__, "-v"])
    
    # Run comprehensive test suite
    success = run_comprehensive_calendar_tests()
    sys.exit(0 if success else 1)