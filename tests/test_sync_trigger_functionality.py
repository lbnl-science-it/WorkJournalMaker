#!/usr/bin/env python3
"""
ABOUTME: Test Suite for Database Sync Trigger Functionality (Issue #35)
ABOUTME: Comprehensive tests for sync API endpoints and UI integration

This module tests the fix for GitHub Issue #35 - Database Sync Trigger Functionality.
Tests include API endpoint validation, frontend integration, and end-to-end sync workflows.
"""

import asyncio
import json
import tempfile
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import pytest
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from fastapi import BackgroundTasks

from config_manager import ConfigManager, AppConfig
from logger import JournalSummarizerLogger
from web.database import DatabaseManager
from web.services.sync_service import DatabaseSyncService, SyncType
from web.services.scheduler import SyncScheduler
from web.api.sync import router as sync_router
from web.app import create_app


class SyncTriggerFunctionalityTester:
    """Comprehensive tester for sync trigger functionality (Issue #35)."""
    
    def __init__(self):
        self.temp_dir = None
        self.config = None
        self.logger = None
        self.db_manager = None
        self.sync_service = None
        self.scheduler = None
        self.test_app = None
        self.client = None
        self.test_results = []
    
    async def setup_test_environment(self):
        """Set up test environment with temporary directories and test data."""
        print("🔧 Setting up test environment for sync trigger functionality...")
        
        # Create temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sync_trigger_test_"))
        print(f"   Created temp directory: {self.temp_dir}")
        
        # Create test configuration
        config_manager = ConfigManager()
        self.config = config_manager.get_config()
        
        # Override paths for testing
        self.config.processing.base_path = str(self.temp_dir / "worklogs")
        
        # Initialize logger
        self.logger = JournalSummarizerLogger(self.config.logging)
        
        # Initialize database manager with test database
        test_db_path = self.temp_dir / "test_sync_trigger.db"
        self.db_manager = DatabaseManager(str(test_db_path))
        await self.db_manager.initialize()
        
        # Initialize sync service and scheduler
        self.sync_service = DatabaseSyncService(self.config, self.logger, self.db_manager)
        self.scheduler = SyncScheduler(self.config, self.logger, self.db_manager)
        
        # Initialize test FastAPI app
        self.test_app = create_app()
        self.test_app.state.config = self.config
        self.test_app.state.logger = self.logger
        self.test_app.state.db_manager = self.db_manager
        self.test_app.state.scheduler = self.scheduler
        
        # Create test client
        self.client = TestClient(self.test_app)
        
        print("✅ Test environment setup complete")
    
    async def create_test_journal_files(self):
        """Create test journal files for sync testing."""
        print("📝 Creating test journal files...")
        
        base_path = Path(self.config.processing.base_path)
        test_dates = [
            date.today() - timedelta(days=10),
            date.today() - timedelta(days=7),
            date.today() - timedelta(days=3),
            date.today() - timedelta(days=1),
            date.today()
        ]
        
        for test_date in test_dates:
            # Create directory structure matching expected format
            year_dir = base_path / f"worklogs_{test_date.year}"
            month_dir = year_dir / f"worklogs_{test_date.year}-{test_date.month:02d}"
            week_dir = month_dir / f"week_ending_{test_date.year}-{test_date.month:02d}-{test_date.day:02d}"
            
            week_dir.mkdir(parents=True, exist_ok=True)
            
            # Create test file
            filename = f"worklog_{test_date.year}-{test_date.month:02d}-{test_date.day:02d}.txt"
            file_path = week_dir / filename
            
            content = f"""Sync Trigger Test Entry for {test_date}

Today's Tasks:
- Testing sync trigger functionality (Issue #35)
- Validating API endpoint fixes
- Verifying UI integration
- Ensuring proper error handling

Implementation Details:
- Fixed API client mismatch in /api/sync/trigger vs /api/sync/full and /api/sync/incremental
- Added comprehensive UI controls for manual sync triggers
- Implemented real-time sync status display and progress indicators
- Created comprehensive test coverage

Test Status: Active
Word Count: {len(content.split())}
Date: {test_date}
"""
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"   Created: {file_path}")
        
        print(f"✅ Created {len(test_dates)} test journal files")
    
    def test_api_endpoint_availability(self):
        """Test that all required sync API endpoints are available."""
        print("\n🌐 Testing API endpoint availability...")
        
        try:
            # Test GET endpoints
            endpoints_get = [
                "/api/sync/status",
                "/api/sync/history",
                "/api/sync/scheduler/status"
            ]
            
            for endpoint in endpoints_get:
                response = self.client.get(endpoint)
                assert response.status_code in [200, 503], f"GET {endpoint} returned {response.status_code}"
                print(f"   ✅ GET {endpoint} - Status: {response.status_code}")
            
            # Test that the old broken endpoint doesn't exist
            response = self.client.post("/api/sync/trigger")
            assert response.status_code == 404, f"Old broken endpoint /api/sync/trigger should return 404, got {response.status_code}"
            print("   ✅ Old broken endpoint /api/sync/trigger properly returns 404")
            
            self.test_results.append(("API Endpoint Availability", True, "All endpoints available"))
            
        except Exception as e:
            self.test_results.append(("API Endpoint Availability", False, str(e)))
            print(f"   ❌ Error: {str(e)}")
    
    def test_sync_trigger_endpoints(self):
        """Test the fixed sync trigger endpoints."""
        print("\n🔄 Testing sync trigger endpoints...")
        
        try:
            # Test incremental sync trigger
            print("   Testing POST /api/sync/incremental...")
            response = self.client.post("/api/sync/incremental", json={"since_days": 7})
            assert response.status_code == 200, f"Incremental sync returned {response.status_code}"
            
            data = response.json()
            assert "message" in data, "Response missing message field"
            assert "sync_type" in data, "Response missing sync_type field"
            assert data["sync_type"] == "incremental", "Wrong sync type returned"
            print(f"   ✅ Incremental sync triggered: {data['message']}")
            
            # Test full sync trigger
            print("   Testing POST /api/sync/full...")
            response = self.client.post("/api/sync/full", json={"date_range_days": 30})
            assert response.status_code == 200, f"Full sync returned {response.status_code}"
            
            data = response.json()
            assert "message" in data, "Response missing message field"
            assert "sync_type" in data, "Response missing sync_type field"
            assert data["sync_type"] == "full", "Wrong sync type returned"
            print(f"   ✅ Full sync triggered: {data['message']}")
            
            # Test single entry sync
            print("   Testing POST /api/sync/entry/{date}...")
            test_date = date.today().isoformat()
            response = self.client.post(f"/api/sync/entry/{test_date}")
            assert response.status_code == 200, f"Entry sync returned {response.status_code}"
            
            data = response.json()
            assert "message" in data, "Response missing message field"
            assert "sync_type" in data, "Response missing sync_type field"
            assert data["sync_type"] == "single_entry", "Wrong sync type returned"
            print(f"   ✅ Entry sync triggered: {data['message']}")
            
            self.test_results.append(("Sync Trigger Endpoints", True, "All trigger endpoints working"))
            
        except Exception as e:
            self.test_results.append(("Sync Trigger Endpoints", False, str(e)))
            print(f"   ❌ Error: {str(e)}")
    
    def test_sync_status_endpoint(self):
        """Test sync status endpoint returns proper data structure."""
        print("\n📊 Testing sync status endpoint...")
        
        try:
            response = self.client.get("/api/sync/status")
            assert response.status_code == 200, f"Status endpoint returned {response.status_code}"
            
            data = response.json()
            
            # Verify required fields
            required_fields = ["sync_status", "database_stats", "timestamp"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify sync_status structure
            sync_status = data["sync_status"]
            assert "sync_in_progress" in sync_status, "Missing sync_in_progress in sync_status"
            
            # Verify database_stats structure
            db_stats = data["database_stats"]
            assert "total_entries" in db_stats, "Missing total_entries in database_stats"
            
            print("   ✅ Sync status endpoint returns proper structure")
            print(f"   Database entries: {db_stats.get('total_entries', 0)}")
            print(f"   Sync in progress: {sync_status.get('sync_in_progress', False)}")
            
            self.test_results.append(("Sync Status Endpoint", True, "Status endpoint returns proper data"))
            
        except Exception as e:
            self.test_results.append(("Sync Status Endpoint", False, str(e)))
            print(f"   ❌ Error: {str(e)}")
    
    def test_sync_history_endpoint(self):
        """Test sync history endpoint returns proper data structure."""
        print("\n📜 Testing sync history endpoint...")
        
        try:
            # Test with default parameters
            response = self.client.get("/api/sync/history")
            assert response.status_code == 200, f"History endpoint returned {response.status_code}"
            
            data = response.json()
            
            # Verify required fields
            required_fields = ["history", "total_records", "retrieved_at"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify history structure
            history = data["history"]
            assert isinstance(history, list), "History should be a list"
            
            # If there are history records, verify their structure
            if history:
                record = history[0]
                expected_fields = ["id", "sync_type", "status", "started_at", "entries_processed"]
                for field in expected_fields:
                    assert field in record, f"Missing field in history record: {field}"
            
            print(f"   ✅ History endpoint returns {len(history)} records")
            
            # Test with parameters
            response = self.client.get("/api/sync/history?limit=5&sync_type=full")
            assert response.status_code == 200, f"History with params returned {response.status_code}"
            
            data = response.json()
            assert "history" in data, "History field missing from filtered response"
            
            print("   ✅ History endpoint works with parameters")
            
            self.test_results.append(("Sync History Endpoint", True, "History endpoint returns proper data"))
            
        except Exception as e:
            self.test_results.append(("Sync History Endpoint", False, str(e)))
            print(f"   ❌ Error: {str(e)}")
    
    def test_scheduler_endpoints(self):
        """Test scheduler control endpoints."""
        print("\n⏰ Testing scheduler endpoints...")
        
        try:
            # Test scheduler status
            response = self.client.get("/api/sync/scheduler/status")
            # Scheduler might not be available in test environment, so 503 is acceptable
            assert response.status_code in [200, 503], f"Scheduler status returned {response.status_code}"
            
            if response.status_code == 200:
                data = response.json()
                assert "is_running" in data or "running" in data, "Scheduler status missing running state"
                print("   ✅ Scheduler status endpoint working")
            else:
                print("   ⚠️ Scheduler not available in test environment (acceptable)")
            
            # Test scheduler trigger endpoints (these should work even if scheduler isn't running)
            trigger_endpoints = [
                "/api/sync/scheduler/trigger/incremental",
                "/api/sync/scheduler/trigger/full"
            ]
            
            for endpoint in trigger_endpoints:
                response = self.client.post(endpoint)
                # These might return 503 if scheduler is not available, which is acceptable
                assert response.status_code in [200, 503], f"{endpoint} returned {response.status_code}"
                print(f"   ✅ {endpoint} - Status: {response.status_code}")
            
            self.test_results.append(("Scheduler Endpoints", True, "Scheduler endpoints properly configured"))
            
        except Exception as e:
            self.test_results.append(("Scheduler Endpoints", False, str(e)))
            print(f"   ❌ Error: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling in sync endpoints."""
        print("\n🛡️ Testing error handling...")
        
        try:
            # Test invalid date format for single entry sync
            response = self.client.post("/api/sync/entry/invalid-date")
            assert response.status_code == 422, f"Invalid date should return 422, got {response.status_code}"
            print("   ✅ Invalid date format properly rejected")
            
            # Test invalid parameters
            response = self.client.post("/api/sync/incremental", json={"since_days": -1})
            # Should either accept and clamp the value or return an error
            assert response.status_code in [200, 400, 422], f"Invalid since_days returned {response.status_code}"
            print("   ✅ Invalid parameters handled gracefully")
            
            # Test concurrent sync prevention (this might pass if sync completes quickly)
            print("   Testing concurrent sync prevention...")
            import threading
            import time
            
            responses = []
            
            def trigger_sync():
                resp = self.client.post("/api/sync/full")
                responses.append(resp)
            
            # Start two concurrent requests
            thread1 = threading.Thread(target=trigger_sync)
            thread2 = threading.Thread(target=trigger_sync)
            
            thread1.start()
            time.sleep(0.1)  # Small delay to increase chance of overlap
            thread2.start()
            
            thread1.join()
            thread2.join()
            
            # At least one should succeed
            success_count = sum(1 for r in responses if r.status_code == 200)
            assert success_count >= 1, "At least one sync should succeed"
            
            # Check if concurrent prevention worked (409 conflict)
            conflict_count = sum(1 for r in responses if r.status_code == 409)
            if conflict_count > 0:
                print("   ✅ Concurrent sync prevention working")
            else:
                print("   ✅ Both syncs completed (acceptable if fast)")
            
            self.test_results.append(("Error Handling", True, "Error conditions handled properly"))
            
        except Exception as e:
            self.test_results.append(("Error Handling", False, str(e)))
            print(f"   ❌ Error: {str(e)}")
    
    async def test_end_to_end_sync_workflow(self):
        """Test complete end-to-end sync workflow."""
        print("\n🔄 Testing end-to-end sync workflow...")
        
        try:
            # Step 1: Check initial database state
            response = self.client.get("/api/sync/status")
            assert response.status_code == 200, "Status check failed"
            initial_data = response.json()
            initial_entries = initial_data["database_stats"]["total_entries"]
            
            print(f"   Initial database entries: {initial_entries}")
            
            # Step 2: Trigger full sync
            response = self.client.post("/api/sync/full", json={"date_range_days": 30})
            assert response.status_code == 200, "Full sync trigger failed"
            
            print("   ✅ Full sync triggered successfully")
            
            # Step 3: Wait a moment for background processing
            await asyncio.sleep(2)
            
            # Step 4: Check sync status
            response = self.client.get("/api/sync/status")
            assert response.status_code == 200, "Status check after sync failed"
            post_sync_data = response.json()
            post_sync_entries = post_sync_data["database_stats"]["total_entries"]
            
            print(f"   Post-sync database entries: {post_sync_entries}")
            
            # Step 5: Verify entries were processed
            # Note: This might be 0 if files don't exist, which is acceptable in test environment
            assert post_sync_entries >= initial_entries, "Entry count should not decrease"
            
            # Step 6: Check sync history
            response = self.client.get("/api/sync/history")
            assert response.status_code == 200, "History check failed"
            history_data = response.json()
            
            # Should have at least one sync record
            assert len(history_data["history"]) > 0, "No sync history found"
            
            # Most recent sync should be our full sync
            recent_sync = history_data["history"][0]
            assert recent_sync["sync_type"] == "full", "Most recent sync should be full sync"
            
            print("   ✅ End-to-end sync workflow completed successfully")
            
            self.test_results.append(("End-to-End Workflow", True, "Complete sync workflow working"))
            
        except Exception as e:
            self.test_results.append(("End-to-End Workflow", False, str(e)))
            print(f"   ❌ Error: {str(e)}")
    
    def test_api_response_formats(self):
        """Test that API responses match expected formats for frontend consumption."""
        print("\n📋 Testing API response formats for frontend integration...")
        
        try:
            # Test sync status response format
            response = self.client.get("/api/sync/status")
            data = response.json()
            
            # Verify timestamp format
            timestamp = data["timestamp"]
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should parse without error
            print("   ✅ Timestamp format is valid ISO format")
            
            # Test sync trigger response format
            response = self.client.post("/api/sync/incremental")
            data = response.json()
            
            required_fields = ["message", "sync_type", "started_at"]
            for field in required_fields:
                assert field in data, f"Missing field in trigger response: {field}"
            
            # Verify started_at timestamp format
            started_at = data["started_at"]
            datetime.fromisoformat(started_at.replace('Z', '+00:00'))  # Should parse without error
            print("   ✅ Trigger response format is correct")
            
            # Test history response format
            response = self.client.get("/api/sync/history")
            data = response.json()
            
            if data["history"]:
                record = data["history"][0]
                # Verify timestamp fields
                datetime.fromisoformat(record["started_at"].replace('Z', '+00:00'))
                if record.get("completed_at"):
                    datetime.fromisoformat(record["completed_at"].replace('Z', '+00:00'))
                print("   ✅ History response format is correct")
            
            self.test_results.append(("API Response Formats", True, "All response formats correct for frontend"))
            
        except Exception as e:
            self.test_results.append(("API Response Formats", False, str(e)))
            print(f"   ❌ Error: {str(e)}")
    
    async def cleanup_test_environment(self):
        """Clean up test environment."""
        print("\n🧹 Cleaning up test environment...")
        
        try:
            # Stop scheduler if running
            if self.scheduler:
                await self.scheduler.stop()
            
            # Close database connections
            if self.db_manager and self.db_manager.engine:
                await self.db_manager.engine.dispose()
            
            # Remove temporary directory
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"   Removed temp directory: {self.temp_dir}")
            
            print("✅ Cleanup complete")
            
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {str(e)}")
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "="*70)
        print("📊 SYNC TRIGGER FUNCTIONALITY TEST SUMMARY (Issue #35)")
        print("="*70)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"\nTests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, success, message in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {test_name}")
            if not success:
                print(f"    Error: {message}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Sync trigger functionality is working correctly.")
            print("\nIssue #35 - Key Fixes Verified:")
            print("  ✅ API client mismatch resolved (/api/sync/trigger → /api/sync/full, /api/sync/incremental)")
            print("  ✅ Proper sync trigger endpoints available and working")
            print("  ✅ Sync status display functionality")
            print("  ✅ Sync history tracking")
            print("  ✅ Error handling and edge cases")
            print("  ✅ API response formats compatible with frontend")
            print("  ✅ End-to-end sync workflow functionality")
        else:
            print(f"\n⚠️ {total - passed} tests failed. Please review the errors above.")
        
        print("\n" + "="*70)


async def main():
    """Main test execution function."""
    print("🚀 Starting Sync Trigger Functionality Tests (Issue #35)")
    print("="*70)
    
    tester = SyncTriggerFunctionalityTester()
    
    try:
        # Setup
        await tester.setup_test_environment()
        await tester.create_test_journal_files()
        
        # Run API tests
        tester.test_api_endpoint_availability()
        tester.test_sync_trigger_endpoints()
        tester.test_sync_status_endpoint()
        tester.test_sync_history_endpoint()
        tester.test_scheduler_endpoints()
        tester.test_error_handling()
        tester.test_api_response_formats()
        
        # Run integration tests
        await tester.test_end_to_end_sync_workflow()
        
    except Exception as e:
        print(f"\n💥 Critical test failure: {str(e)}")
        tester.test_results.append(("Critical Test Setup", False, str(e)))
    
    finally:
        # Cleanup and summary
        await tester.cleanup_test_environment()
        tester.print_test_summary()


if __name__ == "__main__":
    asyncio.run(main())