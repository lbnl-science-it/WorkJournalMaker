"""
Simple performance and compatibility tests for work week functionality.
This is a simplified version to test core functionality and evaluate performance.
"""

import asyncio
import time
import statistics
import pytest
import pytest_asyncio
from datetime import datetime, date, timedelta
import os

from web.services.work_week_service import WorkWeekService, WorkWeekConfig, WorkWeekPreset
from web.database import DatabaseManager
from config_manager import AppConfig
from logger import JournalSummarizerLogger


class TestWorkWeekSimple:
    """Simple test class for work week functionality evaluation."""
    
    @pytest_asyncio.fixture
    async def work_week_service(self):
        """Create WorkWeekService instance for testing."""
        from logger import LogConfig, LogLevel
        
        # Create proper configs for testing
        app_config = AppConfig()
        
        # Create log config with test directory
        log_config = LogConfig(log_dir="/tmp/test_logs/")
        os.makedirs(log_config.log_dir, exist_ok=True)
        
        logger = JournalSummarizerLogger(log_config)
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        service = WorkWeekService(app_config, logger, db_manager)
        return service

    @pytest.mark.asyncio
    async def test_basic_functionality(self, work_week_service):
        """Test basic work week functionality works."""
        print("\n=== Basic Functionality Test ===")
        
        user_id = "test_user"
        
        # Test 1: Get default configuration
        default_config = work_week_service.get_default_work_week_config()
        assert default_config is not None
        assert default_config.preset == WorkWeekPreset.MONDAY_FRIDAY
        print(f"✓ Default config: {default_config.preset.value}")
        
        # Test 2: Update configuration
        custom_config = WorkWeekConfig(
            preset=WorkWeekPreset.CUSTOM,
            start_day=2,  # Tuesday
            end_day=6,    # Saturday
            timezone="UTC"
        )
        
        updated_config = await work_week_service.update_work_week_config(custom_config, user_id)
        assert updated_config is not None
        assert updated_config.start_day == 2
        assert updated_config.end_day == 6
        print(f"✓ Custom config updated: {updated_config.start_day}-{updated_config.end_day}")
        
        # Test 3: Retrieve user configuration
        user_config = await work_week_service.get_user_work_week_config(user_id)
        assert user_config is not None
        assert user_config.start_day == 2
        assert user_config.end_day == 6
        print(f"✓ User config retrieved: {user_config.preset.value}")

    @pytest.mark.asyncio
    async def test_performance_basic(self, work_week_service):
        """Test basic performance requirements."""
        print("\n=== Basic Performance Test ===")
        
        user_id = "perf_user"
        
        # Set up configuration
        config = WorkWeekConfig(
            preset=WorkWeekPreset.MONDAY_FRIDAY,
            start_day=1, end_day=5, timezone="UTC"
        )
        await work_week_service.update_work_week_config(config, user_id)
        
        # Test calculation performance
        test_dates = [
            date(2024, 1, 15),  # Monday
            date(2024, 1, 16),  # Tuesday
            date(2024, 1, 17),  # Wednesday
            date(2024, 1, 18),  # Thursday
            date(2024, 1, 19),  # Friday
            date(2024, 1, 20),  # Saturday
            date(2024, 1, 21),  # Sunday
        ]
        
        calculation_times = []
        results = []
        
        for test_date in test_dates:
            start_time = time.perf_counter_ns()
            
            week_ending = await work_week_service.calculate_week_ending_date(test_date, user_id)
            
            end_time = time.perf_counter_ns()
            calculation_time_ms = (end_time - start_time) / 1_000_000
            
            calculation_times.append(calculation_time_ms)
            results.append((test_date, week_ending, calculation_time_ms))
            
            # Assert performance requirement
            assert calculation_time_ms < 10.0, f"Calculation too slow: {calculation_time_ms:.3f}ms"
        
        # Calculate statistics
        avg_time = statistics.mean(calculation_times)
        max_time = max(calculation_times)
        min_time = min(calculation_times)
        
        print(f"Performance Results:")
        print(f"  Average time: {avg_time:.3f}ms")
        print(f"  Maximum time: {max_time:.3f}ms")
        print(f"  Minimum time: {min_time:.3f}ms")
        print(f"  All calculations < 10ms: {'✓' if max_time < 10.0 else '✗'}")
        
        # Print detailed results
        print(f"\nDetailed Results:")
        for test_date, week_ending, calc_time in results:
            day_name = test_date.strftime('%A')
            print(f"  {test_date} ({day_name}) -> {week_ending} ({calc_time:.3f}ms)")
        
        # Assert overall performance
        assert avg_time < 5.0, f"Average time too slow: {avg_time:.3f}ms"
        assert max_time < 10.0, f"Maximum time too slow: {max_time:.3f}ms"

    @pytest.mark.asyncio
    async def test_weekend_assignment(self, work_week_service):
        """Test weekend assignment logic."""
        print("\n=== Weekend Assignment Test ===")
        
        user_id = "weekend_user"
        
        # Monday-Friday work week
        config = WorkWeekConfig(
            preset=WorkWeekPreset.MONDAY_FRIDAY,
            start_day=1, end_day=5, timezone="UTC"
        )
        await work_week_service.update_work_week_config(config, user_id)
        
        # Test weekend assignment
        saturday = date(2024, 1, 20)  # Saturday
        sunday = date(2024, 1, 21)    # Sunday
        
        saturday_week_ending = await work_week_service.calculate_week_ending_date(saturday, user_id)
        sunday_week_ending = await work_week_service.calculate_week_ending_date(sunday, user_id)
        
        # Expected: Saturday -> previous Friday, Sunday -> next Friday
        expected_saturday_week = date(2024, 1, 19)  # Previous Friday
        expected_sunday_week = date(2024, 1, 26)    # Next Friday
        
        print(f"Saturday {saturday} -> {saturday_week_ending} (expected: {expected_saturday_week})")
        print(f"Sunday {sunday} -> {sunday_week_ending} (expected: {expected_sunday_week})")
        
        # Verify weekend assignment logic
        assert saturday_week_ending == expected_saturday_week, \
            f"Saturday assignment incorrect: {saturday_week_ending} != {expected_saturday_week}"
        assert sunday_week_ending == expected_sunday_week, \
            f"Sunday assignment incorrect: {sunday_week_ending} != {expected_sunday_week}"
        
        print("✓ Weekend assignment logic working correctly")

    @pytest.mark.asyncio
    async def test_multiple_configurations(self, work_week_service):
        """Test different work week configurations."""
        print("\n=== Multiple Configuration Test ===")
        
        configurations = [
            ("Monday-Friday", WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone="UTC")),
            ("Sunday-Thursday", WorkWeekConfig(preset=WorkWeekPreset.SUNDAY_THURSDAY, start_day=7, end_day=4, timezone="UTC")),
            ("Custom Tue-Sat", WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=2, end_day=6, timezone="UTC")),
        ]
        
        test_date = date(2024, 1, 15)  # Monday
        
        for config_name, config in configurations:
            user_id = f"user_{config_name.lower().replace('-', '_').replace(' ', '_')}"
            
            # Update configuration
            await work_week_service.update_work_week_config(config, user_id)
            
            # Calculate week ending
            start_time = time.perf_counter_ns()
            week_ending = await work_week_service.calculate_week_ending_date(test_date, user_id)
            end_time = time.perf_counter_ns()
            
            calculation_time_ms = (end_time - start_time) / 1_000_000
            
            print(f"  {config_name}: {test_date} -> {week_ending} ({calculation_time_ms:.3f}ms)")
            
            # Assert performance
            assert calculation_time_ms < 10.0, f"Configuration {config_name} too slow: {calculation_time_ms:.3f}ms"
            assert week_ending is not None, f"Configuration {config_name} returned None"

    @pytest.mark.asyncio
    async def test_configuration_validation(self, work_week_service):
        """Test configuration validation."""
        print("\n=== Configuration Validation Test ===")
        
        # Test valid configurations
        valid_configs = [
            WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.SUNDAY_THURSDAY, start_day=7, end_day=4, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=3, end_day=7, timezone="UTC"),
        ]
        
        for i, config in enumerate(valid_configs):
            try:
                validated = work_week_service.validate_work_week_config(config)
                assert validated is not None, f"Valid config {i} failed validation"
                print(f"✓ Valid config {i}: {config.preset.value}")
            except Exception as e:
                pytest.fail(f"Valid config {i} caused exception: {e}")
        
        # Test invalid configurations that should be auto-corrected
        invalid_configs = [
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=3, end_day=3, timezone="UTC"),  # Same day
        ]
        
        for i, config in enumerate(invalid_configs):
            try:
                corrected = work_week_service.validate_work_week_config(config)
                assert corrected is not None, f"Invalid config {i} not corrected"
                assert corrected.start_day != corrected.end_day, f"Invalid config {i} not properly corrected"
                print(f"✓ Invalid config {i} auto-corrected: {config.start_day}-{config.end_day} -> {corrected.start_day}-{corrected.end_day}")
            except Exception as e:
                pytest.fail(f"Invalid config {i} caused exception: {e}")

    @pytest.mark.asyncio
    async def test_load_simulation(self, work_week_service):
        """Test with moderate load to simulate real usage."""
        print("\n=== Load Simulation Test ===")
        
        num_users = 10
        entries_per_user = 50
        
        # Set up users with different configurations
        users = []
        configs = [
            WorkWeekConfig(preset=WorkWeekPreset.MONDAY_FRIDAY, start_day=1, end_day=5, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.SUNDAY_THURSDAY, start_day=7, end_day=4, timezone="UTC"),
            WorkWeekConfig(preset=WorkWeekPreset.CUSTOM, start_day=2, end_day=6, timezone="UTC"),
        ]
        
        for i in range(num_users):
            user_id = f"load_user_{i}"
            config = configs[i % len(configs)]
            await work_week_service.update_work_week_config(config, user_id)
            users.append(user_id)
        
        # Generate test dates
        base_date = date(2024, 1, 1)
        test_dates = [base_date + timedelta(days=i) for i in range(entries_per_user)]
        
        # Measure total performance
        total_start_time = time.perf_counter()
        all_calculation_times = []
        
        for user_id in users:
            for test_date in test_dates:
                start_time = time.perf_counter_ns()
                
                week_ending = await work_week_service.calculate_week_ending_date(test_date, user_id)
                
                end_time = time.perf_counter_ns()
                calculation_time_ms = (end_time - start_time) / 1_000_000
                
                all_calculation_times.append(calculation_time_ms)
                
                # Assert individual performance
                assert calculation_time_ms < 10.0, f"Individual calculation too slow: {calculation_time_ms:.3f}ms"
                assert week_ending is not None, f"Calculation returned None for {user_id} on {test_date}"
        
        total_end_time = time.perf_counter()
        total_time = total_end_time - total_start_time
        
        # Calculate statistics
        total_calculations = len(all_calculation_times)
        avg_time = statistics.mean(all_calculation_times)
        max_time = max(all_calculation_times)
        throughput = total_calculations / total_time
        
        print(f"Load Test Results:")
        print(f"  Users: {num_users}")
        print(f"  Entries per user: {entries_per_user}")
        print(f"  Total calculations: {total_calculations}")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Average calculation time: {avg_time:.3f}ms")
        print(f"  Maximum calculation time: {max_time:.3f}ms")
        print(f"  Throughput: {throughput:.1f} calculations/second")
        
        # Assert performance requirements
        assert avg_time < 5.0, f"Average load time too high: {avg_time:.3f}ms"
        assert max_time < 15.0, f"Maximum load time too high: {max_time:.3f}ms"
        assert throughput > 100, f"Throughput too low: {throughput:.1f} calc/s"
        
        print("✓ Load simulation passed all performance requirements")


if __name__ == "__main__":
    # Run simple tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])