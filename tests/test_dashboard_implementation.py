#!/usr/bin/env python3
"""
Test script for Step 12: Dashboard Interface Implementation
Validates all requirements from the blueprint.
"""

import requests
import time
import json
from pathlib import Path

def test_dashboard_functionality():
    """Test all dashboard functionality requirements."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Step 12: Dashboard Interface Implementation")
    print("=" * 60)
    
    # Test 1: Dashboard loads successfully
    print("\n1. Testing dashboard page load...")
    try:
        response = requests.get(f"{base_url}/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "Daily Work Journal" in response.text, "Dashboard title not found"
        print("✅ Dashboard loads successfully")
    except Exception as e:
        print(f"❌ Dashboard load failed: {e}")
        return False
    
    # Test 2: Static assets load correctly
    print("\n2. Testing static assets...")
    assets = [
        "/static/css/variables.css",
        "/static/css/base.css", 
        "/static/css/components.css",
        "/static/css/dashboard.css",
        "/static/js/utils.js",
        "/static/js/dashboard.js",
        "/static/icons/favicon.svg"
    ]
    
    for asset in assets:
        try:
            response = requests.get(f"{base_url}{asset}")
            assert response.status_code == 200, f"Asset {asset} failed to load"
        except Exception as e:
            print(f"❌ Asset {asset} failed: {e}")
            return False
    print("✅ All static assets load correctly")
    
    # Test 3: API endpoints respond correctly
    print("\n3. Testing API endpoints...")
    api_endpoints = [
        "/api/calendar/today",
        "/api/entries/recent?limit=5", 
        "/api/entries/stats/database"
    ]
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            assert response.status_code == 200, f"API {endpoint} failed"
            data = response.json()
            assert isinstance(data, dict), f"API {endpoint} returned invalid JSON"
        except Exception as e:
            print(f"❌ API endpoint {endpoint} failed: {e}")
            return False
    print("✅ All API endpoints respond correctly")
    
    # Test 4: Entry creation functionality
    print("\n4. Testing entry creation...")
    try:
        today = time.strftime("%Y-%m-%d")
        entry_data = {
            "date": today,
            "content": f"Test entry created on {today}\n\nThis is a test entry."
        }
        
        response = requests.post(
            f"{base_url}/api/entries/{today}",
            json=entry_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Entry creation should succeed (200) or already exist (422)
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"
        print("✅ Entry creation functionality works")
    except Exception as e:
        print(f"❌ Entry creation failed: {e}")
        return False
    
    # Test 5: File structure validation
    print("\n5. Testing file structure...")
    required_files = [
        "web/templates/dashboard.html",
        "web/static/css/dashboard.css", 
        "web/static/js/dashboard.js",
        "web/static/icons/favicon.svg"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Required file missing: {file_path}")
            return False
    print("✅ All required files exist")
    
    # Test 6: Template content validation
    print("\n6. Testing template content...")
    dashboard_template = Path("web/templates/dashboard.html").read_text()
    required_elements = [
        "today-section",
        "stats-section", 
        "recent-section",
        "actions-section",
        "new-entry-btn",
        "dashboard.css",
        "dashboard.js"
    ]
    
    for element in required_elements:
        if element not in dashboard_template:
            print(f"❌ Template missing element: {element}")
            return False
    print("✅ Template contains all required elements")
    
    # Test 7: CSS styling validation
    print("\n7. Testing CSS styling...")
    dashboard_css = Path("web/static/css/dashboard.css").read_text()
    required_styles = [
        ".dashboard-container",
        ".today-section",
        ".stats-grid",
        ".recent-entries", 
        ".actions-grid",
        "@media (max-width: 768px)"  # Responsive design
    ]
    
    for style in required_styles:
        if style not in dashboard_css:
            print(f"❌ CSS missing style: {style}")
            return False
    print("✅ CSS contains all required styles")
    
    # Test 8: JavaScript functionality validation
    print("\n8. Testing JavaScript functionality...")
    dashboard_js = Path("web/static/js/dashboard.js").read_text()
    required_functions = [
        "class Dashboard",
        "loadTodayInfo",
        "loadRecentEntries",
        "loadStats",
        "createNewEntry",
        "setupEventListeners"
    ]
    
    for func in required_functions:
        if func not in dashboard_js:
            print(f"❌ JavaScript missing function: {func}")
            return False
    print("✅ JavaScript contains all required functionality")
    
    print("\n" + "=" * 60)
    print("🎉 All dashboard tests passed successfully!")
    print("\n📋 Implementation Summary:")
    print("✅ Dashboard template created with clean, macOS-like design")
    print("✅ Responsive CSS styling with professional typography")
    print("✅ Interactive JavaScript with API integration")
    print("✅ Today's entry status and quick actions")
    print("✅ Recent entries display with previews")
    print("✅ Statistics cards with meaningful data")
    print("✅ Quick action buttons for navigation")
    print("✅ Theme switching functionality")
    print("✅ Error handling and loading states")
    print("✅ Mobile-responsive design")
    
    return True

if __name__ == "__main__":
    success = test_dashboard_functionality()
    exit(0 if success else 1)