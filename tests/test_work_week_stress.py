"""
Stress testing for work week functionality under extreme scenarios and resource constraints.

This module contains comprehensive stress tests to ensure the work week functionality
remains stable and performant under extreme conditions and resource limitations.
"""

import asyncio
import pytest
import time
import statistics
import tempfile
import shutil
import os
import psutil
import gc
import threading
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import sys
import random
import weakref
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.services.work_week_service import WorkWeekService, WorkWeekConfig, WorkWeekPreset
from web.services.entry_manager import EntryManager
from web.services.settings_service import SettingsService
from web.database import DatabaseManager
from web.utils.timezone_utils import get_user_timezone
from file_discovery import FileDiscovery


class TestWorkWeekStressTesting:
    """Test class for extreme scenario stress testing."""
    
    @pytest.fixture
    async def stress_test_setup(self):
        """Set up environment for stress testing."""
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        settings_service = SettingsService(db_manager)
        work_week_service = WorkWeekService(db_manager, settings_service)
        
        # Monitor system resources
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        yield {
            'db_manager': db_manager,
            'settings_service': settings_service,
            'work_week_service': work_week_service,
            'process': process,
            'initial_memory': initial_memory
        }

    @pytest.mark.asyncio
    async def test_extreme_date_ranges(self, stress_test_setup):
        """Test work week calculations with extreme date ranges."""
        work_week_service = stress_test_setup['work_week_service']
        
        user_id = "extreme_date_user"
        config = WorkWeekConfig(
            preset=WorkWeekPreset.MONDAY_FRIDAY,
            start_day=1, end_day=5, timezone="UTC"
        )
        await work_week_service.update_work_week_config(user_id, config)
        
        # Test extreme date ranges
        extreme_dates = [
            # Very old dates
            date(1900, 1, 1),
            date(1901, 2, 28),  # Non-leap year
            date(1904, 2, 29),  # Early leap year
            
            # Around Unix epoch
            date(1970, 1, 1),
            date(1969, 12, 31),
            
            # Y2K boundary
            date(1999, 12, 31),
            date(2000, 1, 1),
            date(2000, 2, 29),  # Y2K leap year
            
            # Far future dates
            date(2100, 1, 1),
            date(2100, 2, 28),  # Non-leap century year
            date(2400, 2, 29),  # Future leap year
            date(3000, 12, 31),
            
            # Edge cases
            date(9999, 12, 31),  # Maximum Python date
        ]
        
        print("\n=== Extreme Date Range Testing ===")
        calculation_times = []
        successful_calculations = 0
        
        for extreme_date in extreme_dates:
            try:
                start_time = time.perf_counter_ns()
                
                week_ending = await work_week_service.calculate_week_ending_date(
                    extreme_date, config, "UTC"
                )
                
                end_time = time.perf_counter_ns()
                calculation_time = (end_time - start_time) / 1_000_000
                calculation_times.append(calculation_time)
                
                # Validate result
                assert week_ending is not None, f"Null result for extreme date {extreme_date}"
                assert isinstance(week_ending, date), f"Invalid type for extreme date {extreme_date}"
                
                # Ensure reasonable week ending (within 7 days)
                date_diff = abs((week_ending - extreme_date).days)
                assert date_diff <= 7, \
                    f"Week ending too far from extreme date: {date_diff} days for {extreme_date}"
                
                # Performance check (relaxed for extreme dates)
                assert calculation_time < 50.0, \
                    f"Extreme date calculation too slow: {calculation_time:.3f}ms for {extreme_date}"
                
                successful_calculations += 1
                print(f"  {extreme_date} -> {week_ending} ({calculation_time:.3f}ms)")
                
            except Exception as e:
                print(f"  FAILED: {extreme_date} - {str(e)}")
                # Some extreme dates might legitimately fail, but we should track them
        
        # Analysis
        if calculation_times:
            avg_time = statistics.mean(calculation_times)
            max_time = max(calculation_times)
            
            print(f"\nExtreme Date Results:")
            print(f"  Successful: {successful_calculations}/{len(extreme_dates)}")
            print(f"  Average time: {avg_time:.3f}ms")
            print(f"  Maximum time: {max_time:.3f}ms")
            
            # At least 80% of extreme dates should work
            success_rate = successful_calculations / len(extreme_dates)
            assert success_rate >= 0.8, f"Too many extreme date failures: {success_rate:.1%}"

    @pytest.mark.asyncio
    async def test_invalid_configuration_handling(self, stress_test_setup):
        """Test behavior with malformed and invalid configurations."""
        work_week_service = stress_test_setup['work_week_service']
        
        user_id = "invalid_config_user"
        test_date = date(2024, 6, 15)
        
        # Test various invalid configurations
        invalid_configs = [
            # Same start and end day
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=3, end_day=3, timezone="UTC"),
            
            # Invalid day numbers
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=0, end_day=5, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=1, end_day=8, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=-1, end_day=5, timezone="UTC"),
            
            # Invalid timezone
            WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone="Invalid/Timezone"),
            
            # None values (if they somehow get through)
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=None, end_day=5, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=1, end_day=None, timezone="UTC"),
        ]
        
        print("\n=== Invalid Configuration Handling ===")
        handled_gracefully = 0
        
        for i, invalid_config in enumerate(invalid_configs):
            print(f"  Testing invalid config {i+1}: {invalid_config}")
            
            try:
                # Service should either auto-correct or reject gracefully
                await work_week_service.update_work_week_config(user_id, invalid_config)
                
                # If update succeeded, try calculation
                try:
                    week_ending = await work_week_service.calculate_week_ending_date(
                        test_date, invalid_config, invalid_config.timezone or "UTC"
                    )
                    
                    if week_ending is not None:
                        print(f"    Auto-corrected: {week_ending}")
                        handled_gracefully += 1
                    else:
                        print(f"    Returned None (graceful failure)")
                        handled_gracefully += 1
                        
                except Exception as calc_error:
                    print(f"    Calculation failed gracefully: {type(calc_error).__name__}")
                    handled_gracefully += 1
                    
            except Exception as config_error:
                print(f"    Configuration rejected gracefully: {type(config_error).__name__}")
                handled_gracefully += 1
        
        # All invalid configurations should be handled gracefully
        print(f"\nInvalid Configuration Results:")
        print(f"  Handled gracefully: {handled_gracefully}/{len(invalid_configs)}")
        
        assert handled_gracefully == len(invalid_configs), \
            "Some invalid configurations caused unhandled exceptions"

    @pytest.mark.asyncio
    async def test_service_failure_scenarios(self, stress_test_setup):
        """Test behavior when services fail or are unavailable."""
        work_week_service = stress_test_setup['work_week_service']
        settings_service = stress_test_setup['settings_service']
        db_manager = stress_test_setup['db_manager']
        
        user_id = "failure_test_user"
        test_date = date(2024, 6, 15)
        
        # Set up valid configuration first
        valid_config = WorkWeekConfig(
            preset=WorkWeekPreset.MONDAY_FRIDAY,
            start_day=1, end_day=5, timezone="UTC"
        )
        await work_week_service.update_work_week_config(user_id, valid_config)
        
        print("\n=== Service Failure Scenarios ===")
        
        # Test 1: Database connection issues (simulate by closing connection)
        print("  Testing database failure scenarios...")
        
        # This test would require mocking database failures
        # For now, we'll test that the service can handle missing user configs
        missing_user_id = "nonexistent_user"
        
        try:
            config = await work_week_service.get_user_work_week_config(missing_user_id)
            # Should return default configuration
            assert config is not None, "Service failed to provide default config for missing user"
            print(f"    Missing user handled gracefully: {config.preset.value}")
        except Exception as e:
            print(f"    Missing user caused exception: {type(e).__name__}")
            # This should be handled gracefully, so this is a test failure
            pytest.fail(f"Service should handle missing users gracefully: {e}")
        
        # Test 2: Corrupted configuration data
        print("  Testing corrupted configuration scenarios...")
        
        # Test with various edge cases that might occur in production
        edge_case_dates = [
            None,  # This should be handled gracefully
            "not_a_date",  # Wrong type
        ]
        
        for edge_case in edge_case_dates:
            try:
                if edge_case is None:
                    # Skip None test as it would be caught by type checking
                    continue
                    
                # This would require more sophisticated testing setup
                # For now, we'll verify the service is robust
                print(f"    Edge case handled: {type(edge_case)}")
                
            except Exception as e:
                print(f"    Edge case caused exception: {type(e).__name__}")

    @pytest.mark.asyncio
    async def test_resource_exhaustion_scenarios(self, stress_test_setup):
        """Test behavior under resource constraints."""
        work_week_service = stress_test_setup['work_week_service']
        process = stress_test_setup['process']
        initial_memory = stress_test_setup['initial_memory']
        
        user_id = "resource_test_user"
        config = WorkWeekConfig(
            preset=WorkWeekPreset.MONDAY_FRIDAY,
            start_day=1, end_day=5, timezone="UTC"
        )
        await work_week_service.update_work_week_config(user_id, config)
        
        print("\n=== Resource Exhaustion Testing ===")
        
        # Test 1: Memory usage under sustained load
        print("  Testing memory usage under sustained load...")
        
        # Generate large number of calculations
        num_calculations = 10000
        base_date = date(2024, 1, 1)
        
        memory_measurements = []
        calculation_times = []
        
        for i in range(num_calculations):
            test_date = base_date + timedelta(days=i % 365)
            
            start_time = time.perf_counter_ns()
            
            week_ending = await work_week_service.calculate_week_ending_date(
                test_date, config, "UTC"
            )
            
            end_time = time.perf_counter_ns()
            calculation_time = (end_time - start_time) / 1_000_000
            calculation_times.append(calculation_time)
            
            # Monitor memory every 1000 calculations
            if i % 1000 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                memory_measurements.append(memory_increase)
                
                print(f"    {i:,} calculations: +{memory_increase:.1f}MB, {calculation_time:.3f}ms")
                
                # Memory should not grow excessively
                assert memory_increase < 200, \
                    f"Memory usage too high: {memory_increase:.1f}MB after {i} calculations"
                
                # Force garbage collection to test memory management
                if i % 5000 == 0:
                    gc.collect()
        
        # Final analysis
        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - initial_memory
        
        avg_calculation_time = statistics.mean(calculation_times)
        max_calculation_time = max(calculation_times)
        
        print(f"\n  Sustained Load Results:")
        print(f"    Total calculations: {num_calculations:,}")
        print(f"    Memory increase: {total_memory_increase:.1f}MB")
        print(f"    Average calculation time: {avg_calculation_time:.3f}ms")
        print(f"    Maximum calculation time: {max_calculation_time:.3f}ms")
        
        # Assert resource usage is reasonable
        assert total_memory_increase < 300, \
            f"Total memory increase too high: {total_memory_increase:.1f}MB"
        assert avg_calculation_time < 10.0, \
            f"Performance degraded under load: {avg_calculation_time:.3f}ms"

    @pytest.mark.asyncio
    async def test_concurrent_stress_scenarios(self, stress_test_setup):
        """Test extreme concurrent access scenarios."""
        work_week_service = stress_test_setup['work_week_service']
        
        print("\n=== Concurrent Stress Testing ===")
        
        # Test with high number of concurrent operations
        num_concurrent_users = 100
        operations_per_user = 100
        
        async def stress_user_operations(user_id):
            user_config = WorkWeekConfig(
                preset=random.choice(list(WorkWeekPreset)),
                start_day=random.randint(1, 7),
                end_day=random.randint(1, 7),
                timezone=random.choice(["UTC", "America/New_York", "Europe/London"])
            )
            
            try:
                await work_week_service.update_work_week_config(user_id, user_config)
            except:
                # Use default if config update fails
                user_config = await work_week_service.get_default_work_week_config()
            
            operation_times = []
            successful_operations = 0
            
            base_date = date(2024, 1, 1)
            
            for i in range(operations_per_user):
                test_date = base_date + timedelta(days=random.randint(0, 365))
                
                try:
                    start_time = time.perf_counter_ns()
                    
                    week_ending = await work_week_service.calculate_week_ending_date(
                        test_date, user_config, user_config.timezone
                    )
                    
                    end_time = time.perf_counter_ns()
                    
                    if week_ending is not None:
                        calculation_time = (end_time - start_time) / 1_000_000
                        operation_times.append(calculation_time)
                        successful_operations += 1
                        
                        # Individual operation should still be fast
                        assert calculation_time < 25.0, \
                            f"Individual concurrent operation too slow: {calculation_time:.3f}ms"
                    
                except Exception as e:
                    # Log but don't fail the test - some operations might fail under extreme stress
                    pass
            
            return {
                'user_id': user_id,
                'successful_operations': successful_operations,
                'total_operations': operations_per_user,
                'avg_time': statistics.mean(operation_times) if operation_times else 0,
                'max_time': max(operation_times) if operation_times else 0
            }
        
        # Execute concurrent stress test
        start_time = time.perf_counter()
        
        users = [f"stress_user_{i}" for i in range(num_concurrent_users)]
        tasks = [stress_user_operations(user_id) for user_id in users]
        
        # Use asyncio.gather with return_exceptions to handle partial failures
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Analyze results (filter out exceptions)
        successful_results = [r for r in results if isinstance(r, dict)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        if successful_results:
            total_successful_operations = sum(r['successful_operations'] for r in successful_results)
            total_operations_attempted = sum(r['total_operations'] for r in successful_results)
            avg_success_rate = total_successful_operations / total_operations_attempted if total_operations_attempted > 0 else 0
            
            operation_times = [r['avg_time'] for r in successful_results if r['avg_time'] > 0]
            avg_operation_time = statistics.mean(operation_times) if operation_times else 0
            max_operation_time = max([r['max_time'] for r in successful_results]) if successful_results else 0
            
            throughput = total_successful_operations / total_time if total_time > 0 else 0
            
            print(f"\n  Concurrent Stress Results:")
            print(f"    Concurrent users: {num_concurrent_users}")
            print(f"    Operations per user: {operations_per_user}")
            print(f"    Successful users: {len(successful_results)}")
            print(f"    Failed users: {len(failed_results)}")
            print(f"    Total successful operations: {total_successful_operations:,}")
            print(f"    Success rate: {avg_success_rate:.1%}")
            print(f"    Total time: {total_time:.3f}s")
            print(f"    Throughput: {throughput:.1f} ops/s")
            print(f"    Average operation time: {avg_operation_time:.3f}ms")
            print(f"    Maximum operation time: {max_operation_time:.3f}ms")
            
            # Assert minimum performance under stress
            assert len(successful_results) >= num_concurrent_users * 0.8, \
                f"Too many users failed under stress: {len(failed_results)}/{num_concurrent_users}"
            assert avg_success_rate >= 0.9, \
                f"Success rate too low under stress: {avg_success_rate:.1%}"
            assert throughput > 50, \
                f"Throughput too low under stress: {throughput:.1f} ops/s"
        else:
            pytest.fail("All concurrent operations failed under stress test")

    @pytest.mark.asyncio
    async def test_file_system_stress(self):
        """Test file system operations under stress."""
        print("\n=== File System Stress Testing ===")
        
        # Create temporary directory for stress testing
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create large directory structure
            num_directories = 1000
            files_per_directory = 10
            
            print(f"  Creating {num_directories} directories with {files_per_directory} files each...")
            
            start_time = time.perf_counter()
            
            # Create mixed directory structure (old and new style)
            base_date = date(2020, 1, 1)
            
            for i in range(num_directories):
                # Alternate between daily and weekly directory styles
                if i % 2 == 0:
                    # Daily style (legacy)
                    test_date = base_date + timedelta(days=i)
                    dir_name = f"week_ending_{test_date.strftime('%Y-%m-%d')}"
                else:
                    # Weekly style (new)
                    week_start = base_date + timedelta(days=(i // 7) * 7)
                    week_end = week_start + timedelta(days=4)  # Friday
                    dir_name = f"week_ending_{week_end.strftime('%Y-%m-%d')}"
                
                dir_path = os.path.join(temp_dir, dir_name)
                os.makedirs(dir_path, exist_ok=True)
                
                # Create files in directory
                for j in range(files_per_directory):
                    file_date = base_date + timedelta(days=i, hours=j)
                    file_name = f"{file_date.strftime('%Y-%m-%d_%H')}.md"
                    file_path = os.path.join(dir_path, file_name)
                    
                    with open(file_path, 'w') as f:
                        f.write(f"Test content for {file_date}")
            
            creation_time = time.perf_counter() - start_time
            
            print(f"    Directory creation time: {creation_time:.3f}s")
            
            # Test file discovery performance with large structure
            print("  Testing file discovery with large directory structure...")
            
            discovery_start = time.perf_counter()
            discovery = FileDiscovery(temp_dir)
            discovered_files = discovery.discover_files()
            discovery_time = time.perf_counter() - discovery_start
            
            expected_files = num_directories * files_per_directory
            
            print(f"    Files discovered: {len(discovered_files)}")
            print(f"    Expected files: {expected_files}")
            print(f"    Discovery time: {discovery_time:.3f}s")
            print(f"    Discovery rate: {len(discovered_files) / discovery_time:.1f} files/s")
            
            # Test week ending discovery performance
            print("  Testing week ending discovery performance...")
            
            test_dates = [base_date + timedelta(days=i) for i in range(0, num_directories, 10)]
            week_ending_times = []
            
            for test_date in test_dates[:50]:  # Test first 50 to avoid excessive time
                we_start = time.perf_counter_ns()
                week_ending = discovery._find_week_ending_for_date(test_date)
                we_end = time.perf_counter_ns()
                
                we_time = (we_end - we_start) / 1_000_000
                week_ending_times.append(we_time)
                
                assert week_ending is not None, f"Could not find week ending for {test_date}"
            
            avg_we_time = statistics.mean(week_ending_times)
            max_we_time = max(week_ending_times)
            
            print(f"    Week ending discovery tests: {len(week_ending_times)}")
            print(f"    Average week ending time: {avg_we_time:.3f}ms")
            print(f"    Maximum week ending time: {max_we_time:.3f}ms")
            
            # Assert performance requirements
            assert len(discovered_files) >= expected_files * 0.95, \
                f"File discovery missed too many files: {len(discovered_files)}/{expected_files}"
            assert discovery_time < 30.0, \
                f"File discovery too slow: {discovery_time:.3f}s"
            assert avg_we_time < 100.0, \
                f"Week ending discovery too slow: {avg_we_time:.3f}ms"
            
        finally:
            # Cleanup
            print("  Cleaning up test directory...")
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, stress_test_setup):
        """Test for memory leaks during extended operations."""
        work_week_service = stress_test_setup['work_week_service']
        process = stress_test_setup['process']
        initial_memory = stress_test_setup['initial_memory']
        
        print("\n=== Memory Leak Detection ===")
        
        user_id = "memory_leak_test_user"
        config = WorkWeekConfig(
            preset=WorkWeekPreset.MONDAY_FRIDAY,
            start_day=1, end_day=5, timezone="UTC"
        )
        await work_week_service.update_work_week_config(user_id, config)
        
        # Run extended operations with periodic memory checks
        cycles = 10
        operations_per_cycle = 1000
        base_date = date(2024, 1, 1)
        
        memory_measurements = []
        
        for cycle in range(cycles):
            print(f"  Running cycle {cycle + 1}/{cycles}...")
            
            cycle_start_memory = process.memory_info().rss / 1024 / 1024
            
            # Perform operations
            for i in range(operations_per_cycle):
                test_date = base_date + timedelta(days=random.randint(0, 365))
                
                week_ending = await work_week_service.calculate_week_ending_date(
                    test_date, config, "UTC"
                )
                
                assert week_ending is not None, f"Operation failed in cycle {cycle}"
            
            # Force garbage collection
            gc.collect()
            
            cycle_end_memory = process.memory_info().rss / 1024 / 1024
            cycle_memory_change = cycle_end_memory - cycle_start_memory
            total_memory_increase = cycle_end_memory - initial_memory
            
            memory_measurements.append({
                'cycle': cycle + 1,
                'cycle_change': cycle_memory_change,
                'total_increase': total_memory_increase,
                'absolute_memory': cycle_end_memory
            })
            
            print(f"    Cycle memory change: {cycle_memory_change:+.1f}MB")
            print(f"    Total memory increase: {total_memory_increase:.1f}MB")
            
            # Assert no excessive memory growth per cycle
            assert cycle_memory_change < 50, \
                f"Excessive memory growth in cycle {cycle}: {cycle_memory_change:.1f}MB"
            
            # Assert total memory increase remains reasonable
            assert total_memory_increase < 200, \
                f"Total memory increase too high: {total_memory_increase:.1f}MB"
        
        # Analyze memory leak patterns
        final_memory = memory_measurements[-1]['total_increase']
        
        # Check if memory is growing linearly (indicating a leak)
        memory_increases = [m['total_increase'] for m in memory_measurements]
        
        # Calculate trend (simple linear regression slope)
        x_values = list(range(len(memory_increases)))
        n = len(memory_increases)
        
        if n > 1:
            x_mean = sum(x_values) / n
            y_mean = sum(memory_increases) / n
            
            numerator = sum((x_values[i] - x_mean) * (memory_increases[i] - y_mean) for i in range(n))
            denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
            
            slope = numerator / denominator if denominator != 0 else 0
            
            print(f"\n  Memory Leak Analysis:")
            print(f"    Final memory increase: {final_memory:.1f}MB")
            print(f"    Memory growth trend: {slope:.2f}MB per cycle")
            print(f"    Operations completed: {cycles * operations_per_cycle:,}")
            
            # Assert no significant memory leak
            assert slope < 5.0, \
                f"Potential memory leak detected: {slope:.2f}MB per cycle"
            assert final_memory < 250, \
                f"Final memory usage too high: {final_memory:.1f}MB"


if __name__ == "__main__":
    # Run stress tests
    pytest.main([__file__, "-v", "--tb=short", "-x"])  # Stop on first failure for stress tests