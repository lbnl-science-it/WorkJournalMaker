"""
Performance Testing Suite (Step 17)

This module provides comprehensive performance testing including load testing,
memory usage monitoring, and concurrent access validation.
"""

import pytest
import asyncio
import time
import psutil
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
import sys
from datetime import date, timedelta
import threading
import statistics

from web.app import app


class TestPerformance:
    """Performance and load testing."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        with TestClient(app) as client:
            yield client
    
    def test_response_times_comprehensive(self, client):
        """Test API response times comprehensively."""
        endpoints = [
            ("/api/health/", 0.5),           # Health check should be very fast
            ("/api/calendar/today", 1.0),    # Today info should be fast
            ("/api/entries/recent?limit=10", 2.0),  # Recent entries may be slower
            ("/api/calendar/2024/1", 2.0),   # Calendar data may be slower
        ]
        
        results = {}
        
        for endpoint, max_time in endpoints:
            times = []
            
            # Test each endpoint multiple times
            for _ in range(10):
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                response_time = end_time - start_time
                times.append(response_time)
                
                # Each request should succeed
                assert response.status_code == 200, f"Failed request to {endpoint}"
            
            # Calculate statistics
            avg_time = statistics.mean(times)
            max_response_time = max(times)
            min_response_time = min(times)
            
            results[endpoint] = {
                'avg': avg_time,
                'max': max_response_time,
                'min': min_response_time,
                'times': times
            }
            
            # Performance assertions
            assert avg_time < max_time, f"Average response time too slow for {endpoint}: {avg_time:.3f}s"
            assert max_response_time < max_time * 2, f"Max response time too slow for {endpoint}: {max_response_time:.3f}s"
        
        # Print performance summary
        print("\nPerformance Results:")
        for endpoint, stats in results.items():
            print(f"  {endpoint}:")
            print(f"    Average: {stats['avg']:.3f}s")
            print(f"    Min: {stats['min']:.3f}s")
            print(f"    Max: {stats['max']:.3f}s")
    
    def test_concurrent_requests_load(self, client):
        """Test handling of concurrent requests under load."""
        
        def make_request(endpoint):
            """Make a single request and return timing info."""
            start_time = time.time()
            try:
                response = client.get(endpoint)
                end_time = time.time()
                return {
                    'status': response.status_code,
                    'duration': end_time - start_time,
                    'success': response.status_code == 200
                }
            except Exception as e:
                end_time = time.time()
                return {
                    'status': 500,
                    'duration': end_time - start_time,
                    'success': False,
                    'error': str(e)
                }
        
        # Test different concurrency levels
        concurrency_levels = [5, 10, 20]
        endpoints = ["/api/health/", "/api/calendar/today"]
        
        for concurrency in concurrency_levels:
            for endpoint in endpoints:
                print(f"\nTesting {concurrency} concurrent requests to {endpoint}")
                
                # Make concurrent requests
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [executor.submit(make_request, endpoint) for _ in range(concurrency)]
                    results = [future.result() for future in as_completed(futures)]
                
                # Analyze results
                successful_requests = sum(1 for r in results if r['success'])
                failed_requests = len(results) - successful_requests
                avg_duration = statistics.mean([r['duration'] for r in results])
                max_duration = max([r['duration'] for r in results])
                
                # Performance assertions
                success_rate = successful_requests / len(results)
                assert success_rate >= 0.95, f"Success rate too low: {success_rate:.2%}"
                assert avg_duration < 2.0, f"Average duration too high: {avg_duration:.3f}s"
                assert max_duration < 5.0, f"Max duration too high: {max_duration:.3f}s"
                
                print(f"  Success rate: {success_rate:.2%}")
                print(f"  Average duration: {avg_duration:.3f}s")
                print(f"  Max duration: {max_duration:.3f}s")
    
    def test_memory_usage_under_load(self, client):
        """Test memory usage under sustained load."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"Initial memory usage: {initial_memory:.2f} MB")
        
        # Make sustained requests
        num_requests = 200
        memory_samples = []
        
        for i in range(num_requests):
            # Make request
            response = client.get("/api/health/")
            assert response.status_code == 200
            
            # Sample memory every 10 requests
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        max_memory = max(memory_samples)
        
        print(f"Final memory usage: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        print(f"Peak memory usage: {max_memory:.2f} MB")
        
        # Memory usage should be reasonable
        assert memory_increase < 100, f"Memory increase too high: {memory_increase:.2f} MB"
        assert max_memory < initial_memory + 150, f"Peak memory too high: {max_memory:.2f} MB"
    
    def test_database_performance(self, client):
        """Test database operation performance."""
        # Test entry creation performance
        creation_times = []
        
        for i in range(10):
            test_date = (date.today() - timedelta(days=i)).isoformat()
            entry_data = {
                "date": test_date,
                "content": f"Performance test entry {i}\n\nThis is test content for performance testing."
            }
            
            start_time = time.time()
            response = client.post(f"/api/entries/{test_date}", json=entry_data)
            end_time = time.time()
            
            if response.status_code == 200:
                creation_times.append(end_time - start_time)
        
        if creation_times:
            avg_creation_time = statistics.mean(creation_times)
            max_creation_time = max(creation_times)
            
            print(f"Average entry creation time: {avg_creation_time:.3f}s")
            print(f"Max entry creation time: {max_creation_time:.3f}s")
            
            # Database operations should be fast
            assert avg_creation_time < 1.0, f"Average creation time too slow: {avg_creation_time:.3f}s"
            assert max_creation_time < 2.0, f"Max creation time too slow: {max_creation_time:.3f}s"
        
        # Test entry retrieval performance
        retrieval_times = []
        
        for i in range(10):
            test_date = (date.today() - timedelta(days=i)).isoformat()
            
            start_time = time.time()
            response = client.get(f"/api/entries/{test_date}")
            end_time = time.time()
            
            if response.status_code == 200:
                retrieval_times.append(end_time - start_time)
        
        if retrieval_times:
            avg_retrieval_time = statistics.mean(retrieval_times)
            max_retrieval_time = max(retrieval_times)
            
            print(f"Average entry retrieval time: {avg_retrieval_time:.3f}s")
            print(f"Max entry retrieval time: {max_retrieval_time:.3f}s")
            
            # Retrieval should be very fast
            assert avg_retrieval_time < 0.5, f"Average retrieval time too slow: {avg_retrieval_time:.3f}s"
            assert max_retrieval_time < 1.0, f"Max retrieval time too slow: {max_retrieval_time:.3f}s"
    
    def test_throughput_capacity(self, client):
        """Test API throughput capacity."""
        
        def make_health_request():
            """Make a health check request."""
            start = time.time()
            response = client.get("/api/health/")
            end = time.time()
            return response.status_code, end - start
        
        # Test different request volumes
        request_volumes = [50, 100, 200]
        
        for volume in request_volumes:
            print(f"\nTesting throughput with {volume} requests")
            
            start_time = time.time()
            results = []
            
            # Sequential requests to measure pure throughput
            for _ in range(volume):
                status, duration = make_health_request()
                results.append((status, duration))
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Calculate metrics
            successful_requests = sum(1 for status, _ in results if status == 200)
            average_response_time = statistics.mean([duration for _, duration in results])
            requests_per_second = successful_requests / total_time
            
            print(f"  Successful requests: {successful_requests}/{volume}")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Average response time: {average_response_time:.3f}s")
            print(f"  Requests per second: {requests_per_second:.1f}")
            
            # Performance assertions
            assert successful_requests >= volume * 0.95  # 95% success rate
            assert average_response_time < 0.5  # Average under 500ms
            assert requests_per_second > 20  # At least 20 RPS
    
    def test_file_system_performance(self, client):
        """Test file system operation performance."""
        # Test creating multiple entries (which involves file operations)
        file_operation_times = []
        
        for i in range(20):
            test_date = (date.today() - timedelta(days=i)).isoformat()
            content = f"File system performance test entry {i}\n" + "Content line\n" * 50
            
            entry_data = {
                "date": test_date,
                "content": content
            }
            
            start_time = time.time()
            response = client.post(f"/api/entries/{test_date}", json=entry_data)
            end_time = time.time()
            
            if response.status_code == 200:
                file_operation_times.append(end_time - start_time)
        
        if file_operation_times:
            avg_file_time = statistics.mean(file_operation_times)
            max_file_time = max(file_operation_times)
            
            print(f"Average file operation time: {avg_file_time:.3f}s")
            print(f"Max file operation time: {max_file_time:.3f}s")
            
            # File operations should be reasonably fast
            assert avg_file_time < 2.0, f"Average file operation too slow: {avg_file_time:.3f}s"
            assert max_file_time < 5.0, f"Max file operation too slow: {max_file_time:.3f}s"


class TestConcurrentAccess:
    """Test concurrent access scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        with TestClient(app) as client:
            yield client
    
    def test_concurrent_read_access(self, client):
        """Test concurrent read access to the same resource."""
        test_date = date.today().isoformat()
        
        # Create an entry first
        entry_data = {
            "date": test_date,
            "content": "Concurrent access test entry"
        }
        response = client.post(f"/api/entries/{test_date}", json=entry_data)
        assert response.status_code == 200
        
        def read_entry():
            """Read the entry and return result."""
            response = client.get(f"/api/entries/{test_date}?include_content=true")
            return response.status_code, response.json() if response.status_code == 200 else None
        
        # Make concurrent read requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_entry) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        # All reads should succeed
        successful_reads = sum(1 for status, _ in results if status == 200)
        assert successful_reads == 20, f"Not all concurrent reads succeeded: {successful_reads}/20"
        
        # All reads should return the same content
        contents = [data.get('content') for status, data in results if status == 200 and data]
        unique_contents = set(contents)
        assert len(unique_contents) <= 1, "Concurrent reads returned different content"
    
    def test_concurrent_write_safety(self, client):
        """Test that concurrent writes are handled safely."""
        test_date = date.today().isoformat()
        
        def write_entry(content_suffix):
            """Write an entry with unique content."""
            entry_data = {
                "date": test_date,
                "content": f"Concurrent write test {content_suffix}"
            }
            response = client.post(f"/api/entries/{test_date}", json=entry_data)
            return response.status_code, content_suffix
        
        # Make concurrent write requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_entry, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # At least some writes should succeed
        successful_writes = sum(1 for status, _ in results if status == 200)
        assert successful_writes > 0, "No concurrent writes succeeded"
        
        # Verify final state is consistent
        response = client.get(f"/api/entries/{test_date}?include_content=true")
        assert response.status_code == 200
        
        final_content = response.json().get('content', '')
        assert "Concurrent write test" in final_content
    
    def test_mixed_concurrent_operations(self, client):
        """Test mixed concurrent read/write operations."""
        test_date = date.today().isoformat()
        
        # Create initial entry
        entry_data = {
            "date": test_date,
            "content": "Initial content for mixed operations test"
        }
        response = client.post(f"/api/entries/{test_date}", json=entry_data)
        assert response.status_code == 200
        
        results = []
        
        def read_operation():
            response = client.get(f"/api/entries/{test_date}")
            results.append(('read', response.status_code))
            return response.status_code
        
        def write_operation(suffix):
            entry_data = {
                "content": f"Updated content {suffix}"
            }
            response = client.put(f"/api/entries/{test_date}", json=entry_data)
            results.append(('write', response.status_code))
            return response.status_code
        
        # Mix of read and write operations
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            
            # Submit read operations
            for _ in range(15):
                futures.append(executor.submit(read_operation))
            
            # Submit write operations
            for i in range(5):
                futures.append(executor.submit(write_operation, i))
            
            # Wait for all operations to complete
            for future in as_completed(futures):
                future.result()
        
        # Analyze results
        read_results = [status for op, status in results if op == 'read']
        write_results = [status for op, status in results if op == 'write']
        
        # Most operations should succeed
        successful_reads = sum(1 for status in read_results if status == 200)
        successful_writes = sum(1 for status in write_results if status == 200)
        
        read_success_rate = successful_reads / len(read_results) if read_results else 0
        write_success_rate = successful_writes / len(write_results) if write_results else 0
        
        assert read_success_rate >= 0.9, f"Read success rate too low: {read_success_rate:.2%}"
        assert write_success_rate >= 0.5, f"Write success rate too low: {write_success_rate:.2%}"
        
        print(f"Mixed operations results:")
        print(f"  Read success rate: {read_success_rate:.2%}")
        print(f"  Write success rate: {write_success_rate:.2%}")


def run_performance_tests():
    """Run all performance tests."""
    print("🧪 Running Performance Tests")
    print("=" * 50)
    
    # Test classes to run
    test_classes = [
        "tests/test_performance_comprehensive.py::TestPerformance",
        "tests/test_performance_comprehensive.py::TestConcurrentAccess"
    ]
    
    results = {}
    
    for test_class in test_classes:
        print(f"\n🔍 Running {test_class}...")
        start_time = time.time()
        
        exit_code = pytest.main([test_class, "-v", "--tb=short", "-s"])
        end_time = time.time()
        
        results[test_class] = {
            "status": "PASSED" if exit_code == 0 else "FAILED",
            "duration": end_time - start_time
        }
    
    # Print summary
    print("\n" + "="*60)
    print("PERFORMANCE TESTS SUMMARY")
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
        print("\n🎉 All performance tests passed!")
    else:
        print(f"\n⚠️  {failed} test class(es) failed. Please review and fix issues.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)