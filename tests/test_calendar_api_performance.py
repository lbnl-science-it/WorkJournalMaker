"""
Performance and Load Tests for Calendar API

This module contains performance tests for the Calendar API endpoints,
testing response times, concurrent access, and resource usage.
"""

import pytest
import asyncio
import time
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import concurrent.futures
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from web.app import app
from web.services.calendar_service import CalendarService
from web.models.journal import CalendarMonth, CalendarEntry, EntryStatus


class TestCalendarAPIPerformance:
    """Performance tests for Calendar API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_calendar_service(self):
        """Create mock calendar service with realistic response times."""
        service = AsyncMock(spec=CalendarService)
        
        # Add realistic delays to simulate database operations
        async def mock_get_calendar_month(year, month):
            await asyncio.sleep(0.01)  # 10ms delay
            return CalendarMonth(
                year=year,
                month=month,
                month_name=date(year, month, 1).strftime("%B"),
                entries=[],
                today=date.today()
            )
        
        async def mock_get_today_info():
            await asyncio.sleep(0.005)  # 5ms delay
            return {
                "today": date.today(),
                "day_name": date.today().strftime("%A"),
                "formatted_date": date.today().strftime("%B %d, %Y"),
                "has_entry": False,
                "entry_metadata": None,
                "week_ending_date": date.today(),
                "current_month": date.today().month,
                "current_year": date.today().year
            }
        
        async def mock_has_entry_for_date(entry_date):
            await asyncio.sleep(0.002)  # 2ms delay
            return False
        
        async def mock_get_entries_for_date_range(start_date, end_date):
            await asyncio.sleep(0.02)  # 20ms delay for range queries
            return []
        
        service.get_calendar_month.side_effect = mock_get_calendar_month
        service.get_today_info.side_effect = mock_get_today_info
        service.has_entry_for_date.side_effect = mock_has_entry_for_date
        service.get_entries_for_date_range.side_effect = mock_get_entries_for_date_range
        service.get_adjacent_months.return_value = ((2023, 12), (2024, 2))
        service.get_week_ending_date.return_value = date.today()
        
        return service
    
    def test_calendar_month_response_time(self, client, mock_calendar_service):
        """Test calendar month endpoint response time."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            start_time = time.time()
            response = client.get("/api/calendar/2024/1")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 0.5  # Should respond within 500ms
    
    def test_today_info_response_time(self, client, mock_calendar_service):
        """Test today info endpoint response time."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            start_time = time.time()
            response = client.get("/api/calendar/today")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 0.2  # Should respond within 200ms
    
    def test_entry_exists_response_time(self, client, mock_calendar_service):
        """Test entry exists endpoint response time."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            start_time = time.time()
            response = client.get("/api/calendar/date/2024-01-01/exists")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 0.1  # Should respond within 100ms
    
    def test_date_range_response_time(self, client, mock_calendar_service):
        """Test date range endpoint response time."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            start_time = time.time()
            response = client.get("/api/calendar/range/2024-01-01/2024-01-31")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0  # Should respond within 1 second
    
    def test_concurrent_calendar_requests(self, client, mock_calendar_service):
        """Test concurrent requests to calendar endpoints."""
        def make_request(endpoint):
            with patch.object(app.state, 'calendar_service', mock_calendar_service):
                return client.get(endpoint)
        
        endpoints = [
            "/api/calendar/2024/1",
            "/api/calendar/2024/2",
            "/api/calendar/2024/3",
            "/api/calendar/today",
            "/api/calendar/current"
        ]
        
        start_time = time.time()
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, endpoint) for endpoint in endpoints]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        assert all(response.status_code == 200 for response in responses)
        
        # Concurrent requests should be faster than sequential
        assert total_time < 2.0  # Should complete within 2 seconds
    
    def test_multiple_month_requests_performance(self, client, mock_calendar_service):
        """Test performance when requesting multiple months."""
        months = [(2024, month) for month in range(1, 13)]  # Full year
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            start_time = time.time()
            
            responses = []
            for year, month in months:
                response = client.get(f"/api/calendar/{year}/{month}")
                responses.append(response)
            
            end_time = time.time()
            total_time = end_time - start_time
        
        # All requests should succeed
        assert all(response.status_code == 200 for response in responses)
        
        # Should complete within reasonable time (12 months)
        assert total_time < 5.0  # Should complete within 5 seconds
    
    def test_navigation_requests_performance(self, client, mock_calendar_service):
        """Test performance of navigation requests."""
        navigation_endpoints = [
            "/api/calendar/2024/1/navigation",
            "/api/calendar/2024/6/navigation",
            "/api/calendar/2024/12/navigation"
        ]
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            start_time = time.time()
            
            responses = []
            for endpoint in navigation_endpoints:
                response = client.get(endpoint)
                responses.append(response)
            
            end_time = time.time()
            total_time = end_time - start_time
        
        # All requests should succeed
        assert all(response.status_code == 200 for response in responses)
        
        # Navigation should be very fast
        assert total_time < 0.5  # Should complete within 500ms
    
    def test_stats_endpoint_performance(self, client, mock_calendar_service):
        """Test performance of statistics endpoint."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            start_time = time.time()
            response = client.get("/api/calendar/stats?year=2024")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0  # Should respond within 1 second
    
    def test_year_overview_performance(self, client, mock_calendar_service):
        """Test performance of year overview endpoint."""
        with patch.object(app.state, 'calendar_service', mock_calendar_service):
            start_time = time.time()
            response = client.get("/api/calendar/months/2024")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0  # Should respond within 2 seconds


class TestCalendarAPILoadTesting:
    """Load testing for Calendar API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_calendar_service_fast(self):
        """Create fast mock calendar service for load testing."""
        service = AsyncMock(spec=CalendarService)
        
        # Minimal delays for load testing
        service.get_calendar_month.return_value = CalendarMonth(
            year=2024,
            month=1,
            month_name="January",
            entries=[],
            today=date.today()
        )
        
        service.get_today_info.return_value = {
            "today": date.today(),
            "day_name": "Monday",
            "formatted_date": "January 1, 2024",
            "has_entry": False,
            "entry_metadata": None,
            "week_ending_date": date.today(),
            "current_month": 1,
            "current_year": 2024
        }
        
        service.has_entry_for_date.return_value = False
        service.get_entries_for_date_range.return_value = []
        service.get_adjacent_months.return_value = ((2023, 12), (2024, 2))
        service.get_week_ending_date.return_value = date.today()
        
        return service
    
    @pytest.mark.slow
    def test_high_volume_calendar_requests(self, client, mock_calendar_service_fast):
        """Test high volume of calendar requests."""
        num_requests = 100
        
        def make_calendar_request(month):
            with patch.object(app.state, 'calendar_service', mock_calendar_service_fast):
                return client.get(f"/api/calendar/2024/{(month % 12) + 1}")
        
        start_time = time.time()
        
        # Make many concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(make_calendar_request, i) 
                for i in range(num_requests)
            ]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        successful_requests = sum(1 for response in responses if response.status_code == 200)
        success_rate = successful_requests / num_requests
        
        assert success_rate >= 0.95  # At least 95% success rate
        assert total_time < 10.0  # Should complete within 10 seconds
        
        # Calculate requests per second
        rps = num_requests / total_time
        assert rps > 10  # Should handle at least 10 requests per second
    
    @pytest.mark.slow
    def test_mixed_endpoint_load(self, client, mock_calendar_service_fast):
        """Test load with mixed endpoint requests."""
        endpoints = [
            "/api/calendar/today",
            "/api/calendar/2024/1",
            "/api/calendar/2024/1/navigation",
            "/api/calendar/date/2024-01-01/exists",
            "/api/calendar/current"
        ]
        
        num_requests_per_endpoint = 20
        total_requests = len(endpoints) * num_requests_per_endpoint
        
        def make_mixed_request(endpoint_index):
            endpoint = endpoints[endpoint_index % len(endpoints)]
            with patch.object(app.state, 'calendar_service', mock_calendar_service_fast):
                return client.get(endpoint)
        
        start_time = time.time()
        
        # Make mixed concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(make_mixed_request, i) 
                for i in range(total_requests)
            ]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate success metrics
        successful_requests = sum(1 for response in responses if response.status_code == 200)
        success_rate = successful_requests / total_requests
        
        assert success_rate >= 0.95  # At least 95% success rate
        assert total_time < 15.0  # Should complete within 15 seconds
    
    def test_memory_usage_stability(self, client, mock_calendar_service_fast):
        """Test that memory usage remains stable under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make many requests to test memory stability
        with patch.object(app.state, 'calendar_service', mock_calendar_service_fast):
            for i in range(50):
                response = client.get(f"/api/calendar/2024/{(i % 12) + 1}")
                assert response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024  # 10MB


class TestCalendarAPIStressTests:
    """Stress tests for Calendar API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_calendar_service_with_delays(self):
        """Create mock calendar service with variable delays."""
        service = AsyncMock(spec=CalendarService)
        
        # Add variable delays to simulate real-world conditions
        async def mock_get_calendar_month_with_delay(year, month):
            # Simulate variable database response times
            delay = 0.01 + (hash(f"{year}-{month}") % 100) / 10000  # 10-20ms
            await asyncio.sleep(delay)
            return CalendarMonth(
                year=year,
                month=month,
                month_name=date(year, month, 1).strftime("%B"),
                entries=[],
                today=date.today()
            )
        
        service.get_calendar_month.side_effect = mock_get_calendar_month_with_delay
        service.get_today_info.return_value = {
            "today": date.today(),
            "day_name": "Monday",
            "formatted_date": "January 1, 2024",
            "has_entry": False,
            "entry_metadata": None,
            "week_ending_date": date.today(),
            "current_month": 1,
            "current_year": 2024
        }
        
        return service
    
    @pytest.mark.slow
    def test_sustained_load(self, client, mock_calendar_service_with_delays):
        """Test sustained load over time."""
        duration_seconds = 30
        request_interval = 0.1  # 10 requests per second
        
        start_time = time.time()
        successful_requests = 0
        failed_requests = 0
        
        with patch.object(app.state, 'calendar_service', mock_calendar_service_with_delays):
            while time.time() - start_time < duration_seconds:
                try:
                    response = client.get("/api/calendar/2024/1")
                    if response.status_code == 200:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                except Exception:
                    failed_requests += 1
                
                time.sleep(request_interval)
        
        total_requests = successful_requests + failed_requests
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        # Should maintain high success rate under sustained load
        assert success_rate >= 0.90  # At least 90% success rate
        assert total_requests > 200  # Should have made substantial number of requests
    
    def test_error_recovery(self, client):
        """Test API recovery after service errors."""
        # Create a service that fails initially then recovers
        service = AsyncMock(spec=CalendarService)
        
        call_count = 0
        
        async def failing_then_working_service(year, month):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 3:  # First 3 calls fail
                raise Exception("Simulated service failure")
            else:  # Subsequent calls succeed
                return CalendarMonth(
                    year=year,
                    month=month,
                    month_name="January",
                    entries=[],
                    today=date.today()
                )
        
        service.get_calendar_month.side_effect = failing_then_working_service
        
        with patch.object(app.state, 'calendar_service', service):
            # First few requests should fail
            for i in range(3):
                response = client.get("/api/calendar/2024/1")
                assert response.status_code == 500
            
            # Subsequent requests should succeed
            for i in range(3):
                response = client.get("/api/calendar/2024/1")
                assert response.status_code == 200


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-m", "not slow"])
    
    # Run slow tests separately
    print("\nRunning slow/load tests...")
    pytest.main([__file__, "-v", "-m", "slow"])