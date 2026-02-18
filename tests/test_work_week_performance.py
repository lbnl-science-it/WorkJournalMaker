"""
Performance tests for work week functionality.

This module contains comprehensive performance tests to ensure the work week functionality
meets all performance requirements, particularly the <10ms calculation requirement.
"""

import asyncio
import time
import statistics
import psutil
import pytest
import pytest_asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple
import os

from web.services.work_week_service import WorkWeekService, WorkWeekConfig, WorkWeekPreset
from web.services.entry_manager import EntryManager
from web.services.settings_service import SettingsService
from web.database import DatabaseManager
from web.utils.timezone_utils import get_timezone_manager
from file_discovery import FileDiscovery
from config_manager import AppConfig
from logger import JournalSummarizerLogger


class TestWorkWeekPerformance:
    """Test class for work week performance validation."""
    
    @pytest_asyncio.fixture
    async def work_week_service(self):
        """Create WorkWeekService instance for testing."""
        config = AppConfig()
        logger = JournalSummarizerLogger(config)
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        service = WorkWeekService(config, logger, db_manager)
        return service
    
    @pytest.fixture
    def test_configurations(self):
        """Generate test work week configurations."""
        return [
            WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.SUNDAY_THURSDAY, start_day=7, end_day=4, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=2, end_day=6, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=3, end_day=7, timezone="UTC"),
        ]
    
    @pytest.fixture
    def test_dates(self):
        """Generate comprehensive test date scenarios."""
        base_date = date(2024, 1, 1)
        dates = []
        
        # Generate 365 days of test dates
        for i in range(365):
            dates.append(base_date + timedelta(days=i))
        
        # Add specific edge cases
        edge_cases = [
            date(2024, 2, 29),  # Leap year
            date(2024, 12, 31), # Year end
            date(2025, 1, 1),   # Year start
            date(2024, 3, 10),  # DST transition
            date(2024, 11, 3),  # DST transition
        ]
        
        dates.extend(edge_cases)
        return dates

    @pytest.mark.asyncio
    async def test_work_week_calculation_performance(self, work_week_service, test_configurations, test_dates):
        """
        Test that work week calculations meet the <10ms requirement.
        
        This is the critical performance test that validates the core requirement.
        """
        user_id = "test_user"
        performance_results = []
        
        for config in test_configurations:
            # Set up configuration
            await work_week_service.update_work_week_config(config, user_id)
            config_times = []
            
            for test_date in test_dates:
                # Measure calculation time
                start_time = time.perf_counter_ns()
                
                week_ending = await work_week_service.calculate_week_ending_date(
                    test_date, user_id
                )
                
                end_time = time.perf_counter_ns()
                calculation_time_ms = (end_time - start_time) / 1_000_000  # Convert to milliseconds
                
                config_times.append(calculation_time_ms)
                
                # Assert individual calculation is under 10ms
                assert calculation_time_ms < 10.0, f"Calculation took {calculation_time_ms:.3f}ms, exceeds 10ms limit"
            
            # Calculate statistics for this configuration
            avg_time = statistics.mean(config_times)
            max_time = max(config_times)
            min_time = min(config_times)
            p95_time = statistics.quantiles(config_times, n=20)[18]  # 95th percentile
            
            performance_results.append({
                'config': config.preset.value,
                'avg_time_ms': avg_time,
                'max_time_ms': max_time,
                'min_time_ms': min_time,
                'p95_time_ms': p95_time,
                'total_calculations': len(config_times)
            })
            
            # Assert performance requirements
            assert avg_time < 5.0, f"Average calculation time {avg_time:.3f}ms exceeds 5ms target"
            assert max_time < 10.0, f"Maximum calculation time {max_time:.3f}ms exceeds 10ms limit"
            assert p95_time < 8.0, f"95th percentile {p95_time:.3f}ms exceeds 8ms target"
        
        # Print performance summary
        print("\n=== Work Week Calculation Performance Results ===")
        for result in performance_results:
            print(f"Config: {result['config']}")
            print(f"  Average: {result['avg_time_ms']:.3f}ms")
            print(f"  Maximum: {result['max_time_ms']:.3f}ms")
            print(f"  95th percentile: {result['p95_time_ms']:.3f}ms")
            print(f"  Total calculations: {result['total_calculations']}")
            print()

    @pytest.mark.asyncio
    async def test_database_sync_performance(self, work_week_service):
        """Test database synchronization performance with large datasets."""
        user_id = "test_user"
        config = WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone="UTC")
        await work_week_service.update_work_week_config(config, user_id)
        
        # Test with increasing dataset sizes
        dataset_sizes = [100, 500, 1000, 5000]
        results = []
        
        for size in dataset_sizes:
            # Generate test entries
            entries = []
            base_date = date(2024, 1, 1)
            
            for i in range(size):
                test_date = base_date + timedelta(days=i % 365)
                entries.append({
                    'date': test_date,
                    'content': f'Test entry {i}',
                    'user_id': user_id
                })
            
            # Measure sync performance
            start_time = time.perf_counter()
            
            # Simulate database sync operations
            for entry in entries:
                week_ending = await work_week_service.calculate_week_ending_date(
                    entry['date'], user_id
                )
                # Simulate database write time
                await asyncio.sleep(0.001)  # 1ms per database write
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            time_per_entry = (total_time / size) * 1000  # Convert to ms
            
            results.append({
                'dataset_size': size,
                'total_time_s': total_time,
                'time_per_entry_ms': time_per_entry
            })
            
            # Assert performance requirements
            assert time_per_entry < 15.0, f"Database sync time {time_per_entry:.3f}ms per entry exceeds 15ms limit"
        
        # Print results
        print("\n=== Database Sync Performance Results ===")
        for result in results:
            print(f"Dataset size: {result['dataset_size']}")
            print(f"  Total time: {result['total_time_s']:.2f}s")
            print(f"  Time per entry: {result['time_per_entry_ms']:.3f}ms")
            print()

    @pytest.mark.asyncio
    async def test_file_discovery_performance(self):
        """Test file discovery performance with mixed directory structures."""
        # Create temporary directory structure for testing
        import tempfile
        import shutil
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mixed directory structure
            self._create_mixed_directory_structure(temp_dir)
            
            # Test file discovery performance
            discovery = FileDiscovery(temp_dir)
            
            start_time = time.perf_counter()
            discovered_files = discovery.discover_files()
            end_time = time.perf_counter()
            
            discovery_time = end_time - start_time
            files_per_second = len(discovered_files) / discovery_time if discovery_time > 0 else 0
            
            print(f"\n=== File Discovery Performance ===")
            print(f"Files discovered: {len(discovered_files)}")
            print(f"Discovery time: {discovery_time:.3f}s")
            print(f"Files per second: {files_per_second:.1f}")
            
            # Assert performance requirements
            assert discovery_time < 5.0, f"File discovery took {discovery_time:.3f}s, exceeds 5s limit"
            assert files_per_second > 100, f"Discovery rate {files_per_second:.1f} files/s below 100 files/s target"

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self, work_week_service):
        """Test performance under concurrent operations."""
        user_id = "concurrent_test_user"
        config = WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone="UTC")
        await work_week_service.update_work_week_config(config, user_id)
        
        # Create concurrent calculation tasks
        num_concurrent = 50
        test_dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(num_concurrent)]
        
        async def calculate_week_ending(test_date):
            start_time = time.perf_counter_ns()
            result = await work_week_service.calculate_week_ending_date(test_date, user_id)
            end_time = time.perf_counter_ns()
            return (end_time - start_time) / 1_000_000, result
        
        # Execute concurrent operations
        start_time = time.perf_counter()
        tasks = [calculate_week_ending(date) for date in test_dates]
        results = await asyncio.gather(*tasks)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        calculation_times = [result[0] for result in results]
        
        avg_concurrent_time = statistics.mean(calculation_times)
        max_concurrent_time = max(calculation_times)
        
        print(f"\n=== Concurrent Operations Performance ===")
        print(f"Concurrent operations: {num_concurrent}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average calculation time: {avg_concurrent_time:.3f}ms")
        print(f"Maximum calculation time: {max_concurrent_time:.3f}ms")
        
        # Assert performance requirements
        assert avg_concurrent_time < 15.0, f"Average concurrent time {avg_concurrent_time:.3f}ms exceeds 15ms limit"
        assert max_concurrent_time < 25.0, f"Maximum concurrent time {max_concurrent_time:.3f}ms exceeds 25ms limit"

    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self, work_week_service):
        """Monitor memory consumption during operations."""
        user_id = "memory_test_user"
        config = WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone="UTC")
        await work_week_service.update_work_week_config(config, user_id)
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform extensive calculations
        test_dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(1000)]
        
        for i, test_date in enumerate(test_dates):
            await work_week_service.calculate_week_ending_date(test_date, user_id)
            
            # Monitor memory every 100 operations
            if i % 100 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Assert memory usage stays reasonable
                assert memory_increase < 50, f"Memory usage increased by {memory_increase:.1f}MB, exceeds 50MB limit"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory
        
        print(f"\n=== Memory Usage Monitoring ===")
        print(f"Initial memory: {initial_memory:.1f}MB")
        print(f"Final memory: {final_memory:.1f}MB")
        print(f"Memory increase: {total_memory_increase:.1f}MB")
        
        # Assert final memory usage
        assert total_memory_increase < 100, f"Total memory increase {total_memory_increase:.1f}MB exceeds 100MB limit"

    def _create_mixed_directory_structure(self, base_dir: str):
        """Create a mixed directory structure for testing."""
        import os
        
        # Create old-style daily directories
        for i in range(50):
            date_obj = date(2024, 1, 1) + timedelta(days=i)
            daily_dir = os.path.join(base_dir, f"week_ending_{date_obj.strftime('%Y-%m-%d')}")
            os.makedirs(daily_dir, exist_ok=True)
            
            # Create test files
            for j in range(3):
                file_path = os.path.join(daily_dir, f"entry_{j}.md")
                with open(file_path, 'w') as f:
                    f.write(f"Test entry content {i}-{j}")
        
        # Create new-style weekly directories
        for i in range(10):
            # Calculate proper week ending dates
            start_date = date(2024, 3, 1) + timedelta(weeks=i)
            # Assume Monday-Friday work week, so week ends on Friday
            days_until_friday = (4 - start_date.weekday()) % 7
            week_ending = start_date + timedelta(days=days_until_friday)
            
            weekly_dir = os.path.join(base_dir, f"week_ending_{week_ending.strftime('%Y-%m-%d')}")
            os.makedirs(weekly_dir, exist_ok=True)
            
            # Create test files for the week
            for j in range(5):  # 5 days in work week
                file_path = os.path.join(weekly_dir, f"entry_{j}.md")
                with open(file_path, 'w') as f:
                    f.write(f"Weekly entry content {i}-{j}")


class TestWorkWeekBenchmarks:
    """Benchmark tests for work week functionality."""
    
    @pytest.mark.asyncio
    async def test_calculation_benchmarks(self):
        """Comprehensive benchmarks for work week calculations."""
        config = AppConfig()
        logger = JournalSummarizerLogger(config)
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        service = WorkWeekService(config, logger, db_manager)
        
        user_id = "benchmark_user"
        
        # Test different configuration types
        configs = [
            ("Monday-Friday", WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone="UTC")),
            ("Sunday-Thursday", WorkWeekConfig(preset=WorkWeekPreset.SUNDAY_THURSDAY, start_day=7, end_day=4, timezone="UTC")),
            ("Custom Tuesday-Saturday", WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=2, end_day=6, timezone="UTC")),
        ]
        
        # Benchmark each configuration
        for config_name, config in configs:
            await service.update_work_week_config(config, user_id)
            
            # Generate test scenarios
            scenarios = self._generate_benchmark_scenarios()
            
            benchmark_results = []
            
            for scenario_name, dates in scenarios.items():
                times = []
                
                for test_date in dates:
                    start_time = time.perf_counter_ns()
                    await service.calculate_week_ending_date(test_date, user_id)
                    end_time = time.perf_counter_ns()
                    
                    calculation_time_ms = (end_time - start_time) / 1_000_000
                    times.append(calculation_time_ms)
                
                benchmark_results.append({
                    'scenario': scenario_name,
                    'min_time': min(times),
                    'max_time': max(times),
                    'avg_time': statistics.mean(times),
                    'median_time': statistics.median(times),
                    'samples': len(times)
                })
            
            # Print benchmark results
            print(f"\n=== Benchmark Results for {config_name} ===")
            for result in benchmark_results:
                print(f"Scenario: {result['scenario']}")
                print(f"  Min: {result['min_time']:.3f}ms")
                print(f"  Max: {result['max_time']:.3f}ms")
                print(f"  Avg: {result['avg_time']:.3f}ms")
                print(f"  Median: {result['median_time']:.3f}ms")
                print(f"  Samples: {result['samples']}")
                print()
    
    def _generate_benchmark_scenarios(self) -> Dict[str, List[date]]:
        """Generate comprehensive benchmark scenarios."""
        scenarios = {}
        
        # Regular work days
        scenarios["Regular Weekdays"] = [
            date(2024, 1, 1),   # Monday
            date(2024, 1, 2),   # Tuesday
            date(2024, 1, 3),   # Wednesday
            date(2024, 1, 4),   # Thursday
            date(2024, 1, 5),   # Friday
        ]
        
        # Weekend days
        scenarios["Weekend Days"] = [
            date(2024, 1, 6),   # Saturday
            date(2024, 1, 7),   # Sunday
        ]
        
        # Month boundaries
        scenarios["Month Boundaries"] = [
            date(2024, 1, 31),  # End of January
            date(2024, 2, 1),   # Start of February
            date(2024, 2, 29),  # Leap day
            date(2024, 3, 1),   # Start of March
        ]
        
        # Year boundaries
        scenarios["Year Boundaries"] = [
            date(2023, 12, 31), # End of 2023
            date(2024, 1, 1),   # Start of 2024
            date(2024, 12, 31), # End of 2024
            date(2025, 1, 1),   # Start of 2025
        ]
        
        # Random dates throughout the year
        import random
        base_date = date(2024, 1, 1)
        scenarios["Random Dates"] = [
            base_date + timedelta(days=random.randint(0, 365))
            for _ in range(20)
        ]
        
        return scenarios


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short"])