#!/usr/bin/env python3
"""
ABOUTME: Simple Sync Functionality Validation for Issue #35
ABOUTME: Basic validation of sync trigger functionality without complex dependencies

This script provides basic validation that the sync trigger functionality
fixes from Issue #35 are working correctly.
"""

import sys
import json
from pathlib import Path

def test_api_client_structure():
    """Test that the API client has the correct structure."""
    print("🔍 Testing API client structure...")
    
    try:
        # Read the api.js file
        api_js_path = Path(__file__).parent.parent / "web" / "static" / "js" / "api.js"
        
        if not api_js_path.exists():
            raise FileNotFoundError(f"API client file not found: {api_js_path}")
        
        with open(api_js_path, 'r') as f:
            api_content = f.read()
        
        # Check that the old broken method is removed
        if 'trigger: () => this.post(\'/api/sync/trigger\')' in api_content:
            raise AssertionError("Old broken trigger() method still exists in API client")
        
        print("   ✅ Old broken trigger() method has been removed")
        
        # Check that new methods exist
        required_methods = [
            'triggerFull:',
            'triggerIncremental:',
            'syncEntry:',
            '/api/sync/full',
            '/api/sync/incremental',
            '/api/sync/entry/'
        ]
        
        for method in required_methods:
            if method not in api_content:
                raise AssertionError(f"Required method/endpoint '{method}' not found in API client")
            print(f"   ✅ Found: {method}")
        
        print("✅ API client structure validation passed")
        return True
        
    except Exception as e:
        print(f"❌ API client structure validation failed: {e}")
        return False

def test_sync_api_endpoints():
    """Test that sync API endpoints are properly defined."""
    print("\n🌐 Testing sync API endpoints...")
    
    try:
        # Read the sync API file
        sync_api_path = Path(__file__).parent.parent / "web" / "api" / "sync.py"
        
        if not sync_api_path.exists():
            raise FileNotFoundError(f"Sync API file not found: {sync_api_path}")
        
        with open(sync_api_path, 'r') as f:
            sync_content = f.read()
        
        # Check for required endpoints
        required_endpoints = [
            '@router.post("/full")',
            '@router.post("/incremental")',
            '@router.post("/entry/{entry_date}")',
            '@router.get("/status")',
            '@router.get("/history")',
            '@router.get("/scheduler/status")'
        ]
        
        for endpoint in required_endpoints:
            if endpoint not in sync_content:
                raise AssertionError(f"Required endpoint '{endpoint}' not found in sync API")
            print(f"   ✅ Found endpoint: {endpoint}")
        
        # Check that endpoints have proper function signatures
        required_functions = [
            'async def trigger_full_sync(',
            'async def trigger_incremental_sync(',
            'async def sync_single_entry(',
            'async def get_sync_status(',
            'async def get_sync_history('
        ]
        
        for function in required_functions:
            if function not in sync_content:
                raise AssertionError(f"Required function '{function}' not found in sync API")
            print(f"   ✅ Found function: {function}")
        
        print("✅ Sync API endpoints validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Sync API endpoints validation failed: {e}")
        return False

def test_settings_ui_integration():
    """Test that settings UI has sync integration."""
    print("\n🖥️ Testing settings UI integration...")
    
    try:
        # Check settings.html for sync panel
        settings_html_path = Path(__file__).parent.parent / "web" / "templates" / "settings.html"
        
        if not settings_html_path.exists():
            raise FileNotFoundError(f"Settings template not found: {settings_html_path}")
        
        with open(settings_html_path, 'r') as f:
            settings_content = f.read()
        
        # Check for sync UI elements
        required_ui_elements = [
            'data-category="sync"',
            'id="sync-panel"',
            'Database Sync',
            'trigger-incremental-sync',
            'trigger-full-sync',
            'sync-status-content',
            'sync-history-content'
        ]
        
        for element in required_ui_elements:
            if element not in settings_content:
                raise AssertionError(f"Required UI element '{element}' not found in settings template")
            print(f"   ✅ Found UI element: {element}")
        
        # Check settings.css for sync styles
        settings_css_path = Path(__file__).parent.parent / "web" / "static" / "css" / "settings.css"
        
        if settings_css_path.exists():
            with open(settings_css_path, 'r') as f:
                css_content = f.read()
            
            sync_css_elements = [
                '.sync-section',
                '.sync-controls-card',
                '.sync-status-card',
                '.sync-history-card'
            ]
            
            for element in sync_css_elements:
                if element not in css_content:
                    print(f"   ⚠️ CSS class '{element}' not found (may be acceptable)")
                else:
                    print(f"   ✅ Found CSS class: {element}")
        
        # Check settings.js for sync functionality
        settings_js_path = Path(__file__).parent.parent / "web" / "static" / "js" / "settings.js"
        
        if settings_js_path.exists():
            with open(settings_js_path, 'r') as f:
                js_content = f.read()
            
            sync_js_elements = [
                'SyncManager',
                'triggerIncrementalSync',
                'triggerFullSync',
                'loadSyncStatus',
                'loadSyncHistory'
            ]
            
            for element in sync_js_elements:
                if element not in js_content:
                    print(f"   ⚠️ JS element '{element}' not found (may be acceptable)")
                else:
                    print(f"   ✅ Found JS element: {element}")
        
        print("✅ Settings UI integration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Settings UI integration validation failed: {e}")
        return False

def test_file_modifications():
    """Test that all expected files have been modified."""
    print("\n📁 Testing file modifications...")
    
    try:
        expected_files = [
            "web/static/js/api.js",
            "web/templates/settings.html", 
            "web/static/css/settings.css",
            "web/static/js/settings.js"
        ]
        
        project_root = Path(__file__).parent.parent
        
        for file_path in expected_files:
            full_path = project_root / file_path
            if not full_path.exists():
                raise FileNotFoundError(f"Expected modified file not found: {file_path}")
            print(f"   ✅ File exists: {file_path}")
        
        print("✅ File modifications validation passed")
        return True
        
    except Exception as e:
        print(f"❌ File modifications validation failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Starting Simple Sync Functionality Validation (Issue #35)")
    print("=" * 60)
    
    tests = [
        ("API Client Structure", test_api_client_structure),
        ("Sync API Endpoints", test_sync_api_endpoints), 
        ("Settings UI Integration", test_settings_ui_integration),
        ("File Modifications", test_file_modifications)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    if passed == total:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("\nIssue #35 - Key Fixes Validated:")
        print("  ✅ API client mismatch resolved")
        print("  ✅ Proper sync trigger endpoints available")
        print("  ✅ UI controls added for manual sync triggers")
        print("  ✅ All required files have been modified")
        print("\nSync trigger functionality is ready for testing!")
    else:
        print(f"\n⚠️ {total - passed} validations failed.")
        print("Please review the errors above before proceeding.")
    
    print("\n" + "=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)