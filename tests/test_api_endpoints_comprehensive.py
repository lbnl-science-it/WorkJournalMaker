"""
Comprehensive API Endpoint Testing Suite (Step 17)

This module provides comprehensive testing for all API endpoints including
validation, error handling, performance, and security aspects.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import sys
from web.app import app


class TestAPIEndpoints:
    """Comprehensive API endpoint testing."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        with TestClient(app) as client:
            yield client
    
    def test_health_endpoint_comprehensive(self, client):
        """Comprehensive test of health endpoint."""
        response = client.get("/api/health/")
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields
        required_fields = ["status", "service", "version", "timestamp"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Status should be healthy
        assert data["status"] == "healthy"
        
        # Service should be identified
        assert isinstance(data["service"], str)
        assert len(data["service"]) > 0
        
        # Version should be present
        assert isinstance(data["version"], str)
        
        # Timestamp should be recent
        assert isinstance(data["timestamp"], str)
    
    def test_entry_crud_operations_comprehensive(self, client):
        """Comprehensive test of entry CRUD operations."""
        today = date.today().isoformat()
        
        # CREATE - Test entry creation
        entry_data = {
            "date": today,
            "content": "Test entry content for comprehensive CRUD testing\n\nThis includes multiple lines and formatting."
        }
        
        create_response = client.post(f"/api/entries/{today}", json=entry_data)
        assert create_response.status_code == 200
        
        created_entry = create_response.json()
        assert created_entry["date"] == today
        assert "Test entry content" in created_entry.get("content", "")
        
        # READ - Test entry retrieval
        read_response = client.get(f"/api/entries/{today}?include_content=true")
        assert read_response.status_code == 200
        
        retrieved_entry = read_response.json()
        assert retrieved_entry["date"] == today
        assert "metadata" in retrieved_entry
        assert retrieved_entry["metadata"]["word_count"] > 0
        
        # READ without content
        read_no_content = client.get(f"/api/entries/{today}")
        assert read_no_content.status_code == 200
        
        entry_no_content = read_no_content.json()
        assert "content" not in entry_no_content or entry_no_content["content"] is None
        
        # UPDATE - Test entry update
        updated_data = {
            "content": "Updated test entry content\n\nThis has been modified for testing purposes."
        }
        
        update_response = client.put(f"/api/entries/{today}", json=updated_data)
        assert update_response.status_code == 200
        
        updated_entry = update_response.json()
        assert "Updated test entry content" in updated_entry.get("content", "")
        
        # Verify update persisted
        verify_response = client.get(f"/api/entries/{today}?include_content=true")
        assert verify_response.status_code == 200
        verify_entry = verify_response.json()
        assert "Updated test entry content" in verify_entry.get("content", "")
    
    def test_entry_validation_comprehensive(self, client):
        """Comprehensive test of entry data validation."""
        
        # Test invalid date formats
        invalid_dates = [
            "invalid-date",
            "2024-13-01",  # Invalid month
            "2024-01-32",  # Invalid day
            "24-01-01",    # Wrong year format
        ]

        for invalid_date in invalid_dates:
            response = client.post(f"/api/entries/{invalid_date}", json={
                "date": invalid_date,
                "content": "Test content"
            })
            assert response.status_code in [400, 422], f"Should reject invalid date: {invalid_date}"
        
        # Test date format that gets parsed but returns 404 (not found)
        response = client.post("/api/entries/2024/01/01", json={
            "date": "2024/01/01",
            "content": "Test content"
        })
        assert response.status_code == 404, "Should return 404 for date format that creates invalid URL path"
        
        # Test future date
        future_date = (date.today() + timedelta(days=1)).isoformat()
        response = client.post(f"/api/entries/{future_date}", json={
            "date": future_date,
            "content": "Test content"
        })
        assert response.status_code == 422  # API returns 422 for validation errors
        
        # Test empty content
        today = date.today().isoformat()
        response = client.post(f"/api/entries/{today}", json={
            "date": today,
            "content": ""
        })
        # Should accept empty content
        assert response.status_code == 200
        
        # Test very long content
        long_content = "A" * 100000  # 100KB of content
        response = client.post(f"/api/entries/{today}", json={
            "date": today,
            "content": long_content
        })
        # Should handle large content appropriately
        assert response.status_code in [200, 413]  # 413 = Payload Too Large
        
        # Test special characters
        special_content = "Content with special chars: àáâãäåæçèéêë 中文 🚀 ñ"
        response = client.post(f"/api/entries/{today}", json={
            "date": today,
            "content": special_content
        })
        assert response.status_code == 200
    
    def test_calendar_endpoints_comprehensive(self, client):
        """Comprehensive test of calendar endpoints."""
        
        # Test today info
        response = client.get("/api/calendar/today")
        assert response.status_code == 200
        
        today_data = response.json()
        required_fields = [
            "today", "day_name", "formatted_date", "has_entry",
            "week_ending_date", "current_month", "current_year"
        ]
        for field in required_fields:
            assert field in today_data, f"Missing field {field} in today response"
        
        # Test calendar month data
        today = date.today()
        response = client.get(f"/api/calendar/{today.year}/{today.month}")
        assert response.status_code == 200
        
        calendar_data = response.json()
        required_fields = ["year", "month", "month_name", "entries", "today"]
        for field in required_fields:
            assert field in calendar_data, f"Missing field {field} in calendar month response"
        
        assert calendar_data["year"] == today.year
        assert calendar_data["month"] == today.month
        assert isinstance(calendar_data["entries"], list)
        
        # Test date range endpoint
        start_date = (today - timedelta(days=7)).isoformat()
        end_date = today.isoformat()
        response = client.get(f"/api/calendar/range/{start_date}/{end_date}")
        assert response.status_code == 200
        
        range_data = response.json()
        # The range endpoint returns a list directly, not wrapped in "entries"
        assert isinstance(range_data, list)
        # No need to check for "entries" key since it's a direct list
    
    def test_pagination_comprehensive(self, client):
        """Comprehensive test of API pagination functionality."""
        
        # Test entries pagination
        response = client.get("/api/entries/?limit=5&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["entries", "total_count", "has_more", "pagination"]
        for field in required_fields:
            assert field in data, f"Missing pagination field: {field}"
        
        # Test pagination parameters
        assert len(data["entries"]) <= 5
        assert isinstance(data["total_count"], int)
        assert isinstance(data["has_more"], bool)
        
        # Test pagination metadata
        pagination = data["pagination"]
        assert "limit" in pagination
        assert "offset" in pagination
        # The API uses offset-based pagination with has_next/has_prev
        assert "has_next" in pagination
        assert "has_prev" in pagination
        
        # Test different page sizes
        for limit in [1, 10, 25, 50]:
            response = client.get(f"/api/entries/?limit={limit}&offset=0")
            assert response.status_code == 200
            data = response.json()
            assert len(data["entries"]) <= limit
        
        # Test offset functionality
        response = client.get("/api/entries/?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["offset"] == 5
    
    def test_error_handling_comprehensive(self, client):
        """Comprehensive test of API error handling."""
        
        # Test non-existent entry
        response = client.get("/api/entries/1900-01-01")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "detail" in error_data
        
        # Test invalid parameters
        invalid_params = [
            "/api/entries/?limit=invalid",
            "/api/entries/?offset=invalid",
            "/api/entries/?limit=-1",
            "/api/entries/?offset=-1",
            "/api/entries/?limit=1000",  # Too large
        ]
        
        for invalid_param in invalid_params:
            response = client.get(invalid_param)
            assert response.status_code in [400, 422], f"Should reject invalid param: {invalid_param}"
        
        # Test invalid calendar dates
        invalid_calendar_requests = [
            "/api/calendar/1800/1",    # Year too old
            "/api/calendar/3001/1",    # Year too new (API allows up to 3000)
            "/api/calendar/2024/13",   # Invalid month
            "/api/calendar/2024/0",    # Invalid month
        ]
        
        for invalid_request in invalid_calendar_requests:
            response = client.get(invalid_request)
            assert response.status_code == 400, f"Should reject invalid calendar request: {invalid_request}"
        
        # Test malformed JSON
        response = client.post("/api/entries/2024-01-01", 
                             data="invalid json", 
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422
    
    def test_response_format_consistency(self, client):
        """Test that all API responses follow consistent format."""
        
        endpoints_to_test = [
            "/api/health/",
            "/api/calendar/today",
            "/api/entries/recent?limit=5",
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            
            # Should return JSON
            assert response.headers.get("content-type", "").startswith("application/json")
            
            # Should be valid JSON
            try:
                data = response.json()
                assert isinstance(data, (dict, list))
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON response from {endpoint}")
    
    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        response = client.options("/api/health/")
        
        # Should have CORS headers (if CORS is enabled)
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        # Note: CORS headers might not be present in test environment
        # This test documents the expected behavior
        for header in cors_headers:
            # Just check that if present, they're not empty
            if header in response.headers:
                assert len(response.headers[header]) > 0
    
    def test_rate_limiting_behavior(self, client):
        """Test API rate limiting behavior (if implemented)."""
        
        # Make multiple rapid requests
        responses = []
        start_time = time.time()
        
        for _ in range(50):
            response = client.get("/api/health/")
            responses.append(response.status_code)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should not have too many failures
        success_rate = sum(1 for code in responses if code == 200) / len(responses)
        assert success_rate > 0.8, f"Success rate too low: {success_rate}"
        
        # Should complete in reasonable time
        assert duration < 10, f"Requests took too long: {duration}s"
    
    def test_concurrent_request_handling(self, client):
        """Test handling of concurrent requests."""
        
        def make_request():
            response = client.get("/api/health/")
            return response.status_code
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        success_count = sum(1 for status in results if status == 200)
        assert success_count >= 18, f"Too many concurrent request failures: {success_count}/20"
    
    def test_request_size_limits(self, client):
        """Test request size limits."""
        
        # Test large request body
        large_content = "A" * 1000000  # 1MB of content
        
        response = client.post("/api/entries/2024-01-01", json={
            "date": "2024-01-01",
            "content": large_content
        })
        
        # Should either accept or reject with appropriate status
        assert response.status_code in [200, 413, 422]
        
        if response.status_code == 413:
            # Payload too large - expected behavior
            assert "too large" in response.json().get("detail", "").lower()
    
    def test_authentication_headers(self, client):
        """Test authentication header handling (if implemented)."""
        
        # Test without authentication
        response = client.get("/api/entries/")
        # Should work without auth for now (or return 401 if auth is required)
        assert response.status_code in [200, 401]
        
        # Test with invalid authentication
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/entries/", headers=headers)
        # Should work or return 401
        assert response.status_code in [200, 401]
    
    def test_content_type_handling(self, client):
        """Test content type handling."""
        
        # Test JSON content type
        response = client.post("/api/entries/2024-01-01", 
                             json={"date": "2024-01-01", "content": "test"},
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        
        # Test unsupported content type
        response = client.post("/api/entries/2024-01-01",
                             data="test data",
                             headers={"Content-Type": "text/plain"})
        assert response.status_code in [415, 422]  # Unsupported Media Type


class TestAPIPerformance:
    """Performance testing for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        with TestClient(app) as client:
            yield client
    
    def test_response_times(self, client):
        """Test API response times."""
        endpoints = [
            "/api/health/",
            "/api/calendar/today",
            "/api/entries/recent?limit=10"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Response should be under 2 seconds
            assert response_time < 2.0, f"Slow response for {endpoint}: {response_time}s"
            assert response.status_code == 200
    
    def test_throughput_capacity(self, client):
        """Test API throughput capacity."""
        
        def make_health_request():
            start = time.time()
            response = client.get("/api/health/")
            end = time.time()
            return response.status_code, end - start
        
        # Make many requests and measure throughput
        num_requests = 100
        start_time = time.time()
        
        results = []
        for _ in range(num_requests):
            status, duration = make_health_request()
            results.append((status, duration))
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate metrics
        successful_requests = sum(1 for status, _ in results if status == 200)
        average_response_time = sum(duration for _, duration in results) / len(results)
        requests_per_second = successful_requests / total_time
        
        # Performance assertions
        assert successful_requests >= num_requests * 0.95  # 95% success rate
        assert average_response_time < 0.5  # Average under 500ms
        assert requests_per_second > 10  # At least 10 RPS
        
        print(f"Performance metrics:")
        print(f"  Successful requests: {successful_requests}/{num_requests}")
        print(f"  Average response time: {average_response_time:.3f}s")
        print(f"  Requests per second: {requests_per_second:.1f}")


def run_comprehensive_api_tests():
    """Run all comprehensive API tests."""
    print("🧪 Running Comprehensive API Endpoint Tests")
    print("=" * 50)
    
    # Test classes to run
    test_classes = [
        "tests/test_api_endpoints_comprehensive.py::TestAPIEndpoints",
        "tests/test_api_endpoints_comprehensive.py::TestAPIPerformance"
    ]
    
    results = {}
    
    for test_class in test_classes:
        print(f"\n🔍 Running {test_class}...")
        start_time = time.time()
        
        exit_code = pytest.main([test_class, "-v", "--tb=short"])
        end_time = time.time()
        
        results[test_class] = {
            "status": "PASSED" if exit_code == 0 else "FAILED",
            "duration": end_time - start_time
        }
    
    # Print summary
    print("\n" + "="*60)
    print("COMPREHENSIVE API TESTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result["status"] == "PASSED")
    failed = len(results) - passed
    total_time = sum(result["duration"] for result in results.values())
    
    for test_class, result in results.items():
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        print(f"{status_icon} {test_class}: {result['status']} ({result['duration']:.2f}s)")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    print(f"Total duration: {total_time:.2f}s")
    
    if failed == 0:
        print("\n🎉 All API tests passed!")
    else:
        print(f"\n⚠️  {failed} test class(es) failed. Please review and fix issues.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_comprehensive_api_tests()
    sys.exit(0 if success else 1)