"""
Timezone boundary and load testing for work week functionality.

This module contains comprehensive tests for timezone handling and high-load scenarios
to ensure the work week functionality performs correctly under stress.
"""

import asyncio
import pytest
import time
import statistics
import concurrent.futures
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import sys
import os
import random
from zoneinfo import ZoneInfo

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.services.work_week_service import WorkWeekService, WorkWeekConfig, WorkWeekPreset
from web.services.entry_manager import EntryManager
from web.services.settings_service import SettingsService
from web.database import DatabaseManager
from web.utils.timezone_utils import get_user_timezone


class TestWorkWeekTimezoneHandling:
    """Test class for comprehensive timezone boundary testing."""
    
    @pytest.fixture
    async def multi_timezone_setup(self):
        """Set up multiple timezone configurations for testing."""
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        settings_service = SettingsService(db_manager)
        work_week_service = WorkWeekService(db_manager, settings_service)
        
        # Define test timezones with various UTC offsets
        timezones = [
            "UTC",                    # UTC+0
            "America/New_York",       # UTC-5/-4 (EST/EDT)
            "Europe/London",          # UTC+0/+1 (GMT/BST)
            "Asia/Tokyo",             # UTC+9
            "Australia/Sydney",       # UTC+10/+11
            "America/Los_Angeles",    # UTC-8/-7 (PST/PDT)
            "Europe/Berlin",          # UTC+1/+2 (CET/CEST)
            "Asia/Kolkata",           # UTC+5:30
            "America/St_Johns",       # UTC-3:30/-2:30 (NST/NDT)
            "Pacific/Kiritimati",     # UTC+14 (extreme positive)
            "Pacific/Niue",           # UTC-11 (extreme negative)
        ]
        
        yield {
            'db_manager': db_manager,
            'settings_service': settings_service,
            'work_week_service': work_week_service,
            'timezones': timezones
        }

    @pytest.mark.asyncio
    async def test_timezone_boundary_calculations(self, multi_timezone_setup):
        """Test work week calculations across timezone boundaries."""
        work_week_service = multi_timezone_setup['work_week_service']
        timezones = multi_timezone_setup['timezones']
        
        user_id = "timezone_boundary_user"
        config = WorkWeekConfig(
            preset=WorkWeekPreset.MONDAY_FRIDAY,
            start_day=1, end_day=5, timezone="UTC"
        )
        await work_week_service.update_work_week_config(user_id, config)
        
        # Test dates that are likely to cause timezone boundary issues
        boundary_dates = [
            date(2024, 3, 10),  # DST transition in many regions
            date(2024, 11, 3),  # DST transition back
            date(2024, 12, 31), # Year boundary
            date(2024, 1, 1),   # New Year
            date(2024, 2, 29),  # Leap day
        ]
        
        results = {}
        
        for timezone in timezones:
            config.timezone = timezone
            timezone_results = []
            
            for test_date in boundary_dates:
                try:
                    start_time = time.perf_counter_ns()
                    
                    week_ending = await work_week_service.calculate_week_ending_date(
                        test_date, config, timezone
                    )
                    
                    end_time = time.perf_counter_ns()
                    calculation_time = (end_time - start_time) / 1_000_000  # Convert to ms
                    
                    # Validate result
                    assert week_ending is not None, f"Null result for {test_date} in {timezone}"
                    assert isinstance(week_ending, date), f"Invalid type for {test_date} in {timezone}"
                    
                    # Ensure week ending is within reasonable range of test date
                    date_diff = abs((week_ending - test_date).days)
                    assert date_diff <= 7, f"Week ending too far from test date: {date_diff} days"
                    
                    timezone_results.append({
                        'date': test_date,
                        'week_ending': week_ending,
                        'calculation_time_ms': calculation_time,
                        'success': True
                    })
                    
                    # Assert performance requirement
                    assert calculation_time < 10.0, \
                        f"Timezone calculation too slow: {calculation_time:.3f}ms for {timezone}"
                
                except Exception as e:
                    timezone_results.append({
                        'date': test_date,
                        'week_ending': None,
                        'calculation_time_ms': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            results[timezone] = timezone_results
        
        # Analyze results
        failed_timezones = []
        for timezone, timezone_results in results.items():
            failed_calculations = [r for r in timezone_results if not r['success']]
            if failed_calculations:
                failed_timezones.append((timezone, failed_calculations))
        
        assert not failed_timezones, f"Timezone calculations failed: {failed_timezones}"
        
        # Print performance summary
        print("\n=== Timezone Boundary Test Results ===")
        for timezone, timezone_results in results.items():
            successful_times = [r['calculation_time_ms'] for r in timezone_results if r['success']]
            if successful_times:
                avg_time = statistics.mean(successful_times)
                max_time = max(successful_times)
                print(f"{timezone}: avg={avg_time:.3f}ms, max={max_time:.3f}ms")

    @pytest.mark.asyncio
    async def test_daylight_saving_transitions(self, multi_timezone_setup):
        """Test calculations during DST transitions."""
        work_week_service = multi_timezone_setup['work_week_service']
        
        user_id = "dst_test_user"
        
        # DST transition dates for different timezones
        dst_transitions = {
            "America/New_York": [
                (date(2024, 3, 10), "Spring forward"),  # 2 AM -> 3 AM
                (date(2024, 11, 3), "Fall back"),       # 2 AM -> 1 AM
            ],
            "Europe/London": [
                (date(2024, 3, 31), "Spring forward"),  # 1 AM -> 2 AM
                (date(2024, 10, 27), "Fall back"),      # 2 AM -> 1 AM
            ],
            "Australia/Sydney": [
                (date(2024, 4, 7), "Fall back"),        # 3 AM -> 2 AM
                (date(2024, 10, 6), "Spring forward"),  # 2 AM -> 3 AM
            ],
        }
        
        for timezone, transitions in dst_transitions.items():
            print(f"\nTesting DST transitions for {timezone}")
            
            config = WorkWeekConfig(
                preset=WorkWeekPreset.MONDAY_FRIDAY,
                start_day=1, end_day=5, timezone=timezone
            )
            await work_week_service.update_work_week_config(user_id, config)
            
            for transition_date, description in transitions:
                # Test the transition day and surrounding days
                test_dates = [
                    transition_date - timedelta(days=1),  # Day before
                    transition_date,                      # Transition day
                    transition_date + timedelta(days=1),  # Day after
                ]
                
                for test_date in test_dates:
                    start_time = time.perf_counter_ns()
                    
                    week_ending = await work_week_service.calculate_week_ending_date(
                        test_date, config, timezone
                    )
                    
                    end_time = time.perf_counter_ns()
                    calculation_time = (end_time - start_time) / 1_000_000
                    
                    # Validate result
                    assert week_ending is not None, \
                        f"DST calculation failed for {test_date} ({description}) in {timezone}"
                    assert isinstance(week_ending, date), \
                        f"Invalid result type for DST transition in {timezone}"
                    
                    # Performance check
                    assert calculation_time < 10.0, \
                        f"DST calculation too slow: {calculation_time:.3f}ms"
                    
                    print(f"  {test_date} -> {week_ending} ({calculation_time:.3f}ms)")

    @pytest.mark.asyncio
    async def test_multiple_timezone_scenarios(self, multi_timezone_setup):
        """Test with different user timezones simultaneously."""
        work_week_service = multi_timezone_setup['work_week_service']
        timezones = multi_timezone_setup['timezones']
        
        # Create multiple users with different timezones
        users_and_timezones = [
            (f"user_{i}", timezone) for i, timezone in enumerate(timezones)
        ]
        
        # Set up different work week configurations for each user
        configs = [
            WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone=tz),
            WorkWeekConfig(preset=WorkWeekPreset.SUNDAY_THURSDAY, start_day=7, end_day=4, timezone=tz),
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=2, end_day=6, timezone=tz),
        ]
        
        # Test simultaneous operations across timezones
        test_date = date(2024, 6, 15)  # Mid-year to avoid most DST issues
        tasks = []
        
        for (user_id, timezone), config in zip(users_and_timezones, configs * (len(users_and_timezones) // len(configs) + 1)):
            config.timezone = timezone
            await work_week_service.update_work_week_config(user_id, config)
            
            # Create async task for calculation
            task = work_week_service.calculate_week_ending_date(test_date, config, timezone)
            tasks.append((user_id, timezone, task))
        
        # Execute all calculations concurrently
        start_time = time.perf_counter()
        results = []
        
        for user_id, timezone, task in tasks:
            try:
                week_ending = await task
                results.append({
                    'user_id': user_id,
                    'timezone': timezone,
                    'week_ending': week_ending,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'user_id': user_id,
                    'timezone': timezone,
                    'week_ending': None,
                    'success': False,
                    'error': str(e)
                })
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Validate results
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        assert len(failed_results) == 0, f"Failed timezone calculations: {failed_results}"
        assert len(successful_results) == len(users_and_timezones), \
            f"Expected {len(users_and_timezones)} results, got {len(successful_results)}"
        
        print(f"\n=== Multiple Timezone Test Results ===")
        print(f"Total calculations: {len(results)}")
        print(f"Successful: {len(successful_results)}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average time per calculation: {(total_time / len(results) * 1000):.3f}ms")

    @pytest.mark.asyncio
    async def test_timezone_edge_cases(self, multi_timezone_setup):
        """Test edge cases and boundary conditions for timezones."""
        work_week_service = multi_timezone_setup['work_week_service']
        
        user_id = "edge_case_user"
        
        # Test extreme timezone offsets
        extreme_timezones = [
            "Pacific/Kiritimati",  # UTC+14 (furthest ahead)
            "Pacific/Niue",        # UTC-11 (furthest behind, excluding uninhabited areas)
            "Pacific/Chatham",     # UTC+12:45 (unusual offset)
            "Asia/Kathmandu",      # UTC+5:45 (another unusual offset)
        ]
        
        edge_case_dates = [
            date(1970, 1, 1),   # Unix epoch
            date(2038, 1, 19),  # Near 32-bit timestamp limit
            date(2000, 2, 29),  # Y2K leap year
            date(1900, 2, 28),  # Non-leap century year
            date(2100, 2, 28),  # Future non-leap century year
        ]
        
        for timezone in extreme_timezones:
            config = WorkWeekConfig(
                preset=WorkWeekPreset.MONDAY_FRIDAY,
                start_day=1, end_day=5, timezone=timezone
            )
            await work_week_service.update_work_week_config(user_id, config)
            
            print(f"\nTesting edge cases for {timezone}")
            
            for test_date in edge_case_dates:
                try:
                    start_time = time.perf_counter_ns()
                    
                    week_ending = await work_week_service.calculate_week_ending_date(
                        test_date, config, timezone
                    )
                    
                    end_time = time.perf_counter_ns()
                    calculation_time = (end_time - start_time) / 1_000_000
                    
                    # Validate result
                    assert week_ending is not None, f"Null result for {test_date} in {timezone}"
                    assert isinstance(week_ending, date), f"Invalid type for {test_date} in {timezone}"
                    
                    # Ensure reasonable week ending
                    date_diff = abs((week_ending - test_date).days)
                    assert date_diff <= 7, \
                        f"Week ending too far: {date_diff} days for {test_date} in {timezone}"
                    
                    # Performance check
                    assert calculation_time < 15.0, \
                        f"Edge case calculation too slow: {calculation_time:.3f}ms"
                    
                    print(f"  {test_date} -> {week_ending} ({calculation_time:.3f}ms)")
                
                except Exception as e:
                    pytest.fail(f"Edge case failed for {test_date} in {timezone}: {e}")


class TestWorkWeekLoadTesting:
    """Test class for high-load scenarios."""
    
    @pytest.fixture
    async def load_test_setup(self):
        """Set up environment for load testing."""
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        settings_service = SettingsService(db_manager)
        work_week_service = WorkWeekService(db_manager, settings_service)
        
        yield {
            'db_manager': db_manager,
            'settings_service': settings_service,
            'work_week_service': work_week_service
        }

    @pytest.mark.asyncio
    async def test_high_volume_entry_creation(self, load_test_setup):
        """Test with many concurrent entry creations."""
        work_week_service = load_test_setup['work_week_service']
        
        # Simulate high volume of concurrent users
        num_users = 50
        entries_per_user = 20
        
        users = [f"load_user_{i}" for i in range(num_users)]
        
        # Set up different configurations for users
        configs = [
            WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.SUNDAY_THURSDAY, start_day=7, end_day=4, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=2, end_day=6, timezone="UTC"),
        ]
        
        # Configure users
        for i, user_id in enumerate(users):
            config = configs[i % len(configs)]
            await work_week_service.update_work_week_config(user_id, config)
        
        # Generate test dates
        base_date = date(2024, 1, 1)
        test_dates = [base_date + timedelta(days=i) for i in range(entries_per_user)]
        
        # Create concurrent tasks
        async def create_entries_for_user(user_id):
            user_config = await work_week_service.get_user_work_week_config(user_id)
            entry_times = []
            
            for test_date in test_dates:
                start_time = time.perf_counter_ns()
                
                week_ending = await work_week_service.calculate_week_ending_date(
                    test_date, user_config, user_config.timezone
                )
                
                end_time = time.perf_counter_ns()
                calculation_time = (end_time - start_time) / 1_000_000
                
                entry_times.append(calculation_time)
                
                # Validate performance per calculation
                assert calculation_time < 10.0, \
                    f"Individual calculation too slow: {calculation_time:.3f}ms"
            
            return {
                'user_id': user_id,
                'total_entries': len(test_dates),
                'avg_time': statistics.mean(entry_times),
                'max_time': max(entry_times),
                'total_time': sum(entry_times)
            }
        
        # Execute load test
        start_time = time.perf_counter()
        
        tasks = [create_entries_for_user(user_id) for user_id in users]
        results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        total_test_time = end_time - start_time
        
        # Analyze results
        total_calculations = sum(r['total_entries'] for r in results)
        avg_calculation_time = statistics.mean([r['avg_time'] for r in results])
        max_calculation_time = max([r['max_time'] for r in results])
        calculations_per_second = total_calculations / total_test_time
        
        print(f"\n=== High Volume Load Test Results ===")
        print(f"Users: {num_users}")
        print(f"Entries per user: {entries_per_user}")
        print(f"Total calculations: {total_calculations}")
        print(f"Total test time: {total_test_time:.3f}s")
        print(f"Calculations per second: {calculations_per_second:.1f}")
        print(f"Average calculation time: {avg_calculation_time:.3f}ms")
        print(f"Maximum calculation time: {max_calculation_time:.3f}ms")
        
        # Assert performance requirements
        assert avg_calculation_time < 5.0, \
            f"Average load test time too high: {avg_calculation_time:.3f}ms"
        assert max_calculation_time < 15.0, \
            f"Maximum load test time too high: {max_calculation_time:.3f}ms"
        assert calculations_per_second > 100, \
            f"Throughput too low: {calculations_per_second:.1f} calc/s"

    @pytest.mark.asyncio
    async def test_large_dataset_operations(self, load_test_setup):
        """Test with large numbers of existing entries."""
        work_week_service = load_test_setup['work_week_service']
        db_manager = load_test_setup['db_manager']
        
        user_id = "large_dataset_user"
        config = WorkWeekConfig(
            preset=WorkWeekPreset.MONDAY_FRIDAY,
            start_day=1, end_day=5, timezone="UTC"
        )
        await work_week_service.update_work_week_config(user_id, config)
        
        # Simulate large dataset sizes
        dataset_sizes = [1000, 5000, 10000]
        
        for dataset_size in dataset_sizes:
            print(f"\nTesting with {dataset_size} entries")
            
            # Generate large date range
            base_date = date(2020, 1, 1)
            test_dates = [base_date + timedelta(days=i) for i in range(dataset_size)]
            
            # Measure batch processing performance
            start_time = time.perf_counter()
            calculation_times = []
            
            for i, test_date in enumerate(test_dates):
                calc_start = time.perf_counter_ns()
                
                week_ending = await work_week_service.calculate_week_ending_date(
                    test_date, config, "UTC"
                )
                
                calc_end = time.perf_counter_ns()
                calculation_time = (calc_end - calc_start) / 1_000_000
                calculation_times.append(calculation_time)
                
                # Progress indicator for large datasets
                if (i + 1) % 1000 == 0:
                    print(f"  Processed {i + 1}/{dataset_size} entries")
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            # Calculate statistics
            avg_time = statistics.mean(calculation_times)
            max_time = max(calculation_times)
            p95_time = statistics.quantiles(calculation_times, n=20)[18]  # 95th percentile
            throughput = dataset_size / total_time
            
            print(f"  Results for {dataset_size} entries:")
            print(f"    Total time: {total_time:.3f}s")
            print(f"    Average calculation: {avg_time:.3f}ms")
            print(f"    Maximum calculation: {max_time:.3f}ms")
            print(f"    95th percentile: {p95_time:.3f}ms")
            print(f"    Throughput: {throughput:.1f} calc/s")
            
            # Assert performance requirements scale properly
            assert avg_time < 8.0, \
                f"Average time degraded with large dataset: {avg_time:.3f}ms"
            assert max_time < 20.0, \
                f"Maximum time too high with large dataset: {max_time:.3f}ms"
            assert throughput > 50, \
                f"Throughput too low with large dataset: {throughput:.1f} calc/s"

    @pytest.mark.asyncio
    async def test_database_performance_under_load(self, load_test_setup):
        """Test database operations performance under load."""
        work_week_service = load_test_setup['work_week_service']
        settings_service = load_test_setup['settings_service']
        
        # Test concurrent database operations
        num_concurrent_users = 25
        operations_per_user = 50
        
        async def user_operations(user_id):
            operation_times = []
            
            for i in range(operations_per_user):
                # Mix of operations: config updates and retrievals
                if i % 3 == 0:
                    # Update configuration
                    start_time = time.perf_counter_ns()
                    
                    new_config = WorkWeekConfig(
                        preset=random.choice(list(WorkWeekPreset)),
                        start_day=random.randint(1, 7),
                        end_day=random.randint(1, 7),
                        timezone="UTC"
                    )
                    await work_week_service.update_work_week_config(user_id, new_config)
                    
                    end_time = time.perf_counter_ns()
                else:
                    # Retrieve configuration
                    start_time = time.perf_counter_ns()
                    
                    config = await work_week_service.get_user_work_week_config(user_id)
                    
                    end_time = time.perf_counter_ns()
                
                operation_time = (end_time - start_time) / 1_000_000
                operation_times.append(operation_time)
            
            return {
                'user_id': user_id,
                'operations': operations_per_user,
                'avg_time': statistics.mean(operation_times),
                'max_time': max(operation_times)
            }
        
        # Execute concurrent database operations
        start_time = time.perf_counter()
        
        users = [f"db_load_user_{i}" for i in range(num_concurrent_users)]
        tasks = [user_operations(user_id) for user_id in users]
        results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Analyze database performance
        total_operations = sum(r['operations'] for r in results)
        avg_operation_time = statistics.mean([r['avg_time'] for r in results])
        max_operation_time = max([r['max_time'] for r in results])
        operations_per_second = total_operations / total_time
        
        print(f"\n=== Database Load Test Results ===")
        print(f"Concurrent users: {num_concurrent_users}")
        print(f"Operations per user: {operations_per_user}")
        print(f"Total operations: {total_operations}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Operations per second: {operations_per_second:.1f}")
        print(f"Average operation time: {avg_operation_time:.3f}ms")
        print(f"Maximum operation time: {max_operation_time:.3f}ms")
        
        # Assert database performance requirements
        assert avg_operation_time < 25.0, \
            f"Database operations too slow under load: {avg_operation_time:.3f}ms"
        assert max_operation_time < 100.0, \
            f"Maximum database operation too slow: {max_operation_time:.3f}ms"
        assert operations_per_second > 20, \
            f"Database throughput too low: {operations_per_second:.1f} ops/s"


if __name__ == "__main__":
    # Run timezone and load tests
    pytest.main([__file__, "-v", "--tb=short"])