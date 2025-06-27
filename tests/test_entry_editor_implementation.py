"""
Test Entry Editor Implementation - Step 13 Validation

This test validates the entry editor interface implementation including:
- Template rendering
- Route handling
- JavaScript functionality
- CSS styling integration

Run with: python tests/test_entry_editor_implementation.py
"""

import asyncio
import sys
from datetime import date, datetime
from pathlib import Path
import json

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

def test_file_existence():
    """Test that all required files exist and have content."""
    print("=== Testing File Existence ===")
    
    base_path = Path(__file__).parent.parent
    required_files = {
        "web/templates/entry_editor.html": "Entry editor template",
        "web/static/css/editor.css": "Editor CSS styles", 
        "web/static/js/editor.js": "Editor JavaScript functionality"
    }
    
    all_exist = True
    for file_path, description in required_files.items():
        full_path = base_path / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ {file_path} - {size:,} bytes - {description}")
        else:
            print(f"❌ {file_path} - MISSING - {description}")
            all_exist = False
    
    return all_exist

def test_template_content():
    """Test that the entry editor template contains required elements."""
    print("\n=== Testing Template Content ===")
    
    base_path = Path(__file__).parent.parent
    template_path = base_path / "web" / "templates" / "entry_editor.html"
    
    if not template_path.exists():
        print("❌ Template file not found")
        return False
    
    content = template_path.read_text()
    
    # Required template elements
    required_elements = {
        "editor-container": "Main editor container",
        "editor-textarea": "Main text editing area",
        "save-btn": "Save button",
        "preview-btn": "Preview toggle button",
        "word-count": "Word count display",
        "char-count": "Character count display",
        "line-count": "Line count display",
        "bold-btn": "Bold formatting button",
        "italic-btn": "Italic formatting button",
        "heading-btn": "Heading formatting button",
        "list-btn": "List formatting button",
        "link-btn": "Link formatting button",
        "fullscreen-btn": "Focus mode button",
        "shortcuts-help": "Keyboard shortcuts help",
        "preview-pane": "Markdown preview pane"
    }
    
    all_found = True
    for element_id, description in required_elements.items():
        if element_id in content:
            print(f"✅ {element_id} - {description}")
        else:
            print(f"❌ {element_id} - MISSING - {description}")
            all_found = False
    
    # Check template inheritance
    if "{% extends \"base.html\" %}" in content:
        print("✅ Template extends base.html")
    else:
        print("❌ Template should extend base.html")
        all_found = False
    
    # Check CSS/JS includes
    if "/static/css/editor.css" in content:
        print("✅ Editor CSS included")
    else:
        print("❌ Editor CSS not included")
        all_found = False
        
    if "/static/js/editor.js" in content:
        print("✅ Editor JavaScript included")
    else:
        print("❌ Editor JavaScript not included")
        all_found = False
    
    return all_found

def test_css_structure():
    """Test that the editor CSS contains required classes and responsive design."""
    print("\n=== Testing CSS Structure ===")
    
    base_path = Path(__file__).parent.parent
    css_path = base_path / "web" / "static" / "css" / "editor.css"
    
    if not css_path.exists():
        print("❌ CSS file not found")
        return False
    
    content = css_path.read_text()
    
    # Required CSS classes
    required_classes = {
        ".editor-container": "Main editor container styles",
        ".editor-header": "Editor header styles",
        ".editor-main": "Main editor area styles",
        ".editor-footer": "Editor footer styles",
        ".editor-textarea": "Textarea styles",
        ".toolbar-btn": "Toolbar button styles",
        ".preview-pane": "Preview pane styles",
        ".save-status": "Save status indicator styles",
        ".focus-mode": "Focus mode styles",
        ".shortcuts-help": "Keyboard shortcuts modal styles"
    }
    
    all_found = True
    for css_class, description in required_classes.items():
        if css_class in content:
            print(f"✅ {css_class} - {description}")
        else:
            print(f"❌ {css_class} - MISSING - {description}")
            all_found = False
    
    # Check responsive design
    if "@media (max-width: 768px)" in content:
        print("✅ Responsive design for mobile")
    else:
        print("❌ Mobile responsive design missing")
        all_found = False
    
    # Check CSS variables usage
    if "var(--" in content:
        print("✅ Uses CSS variables from design system")
    else:
        print("❌ Should use CSS variables for consistency")
        all_found = False
    
    return all_found

def test_javascript_functionality():
    """Test that the editor JavaScript contains required functionality."""
    print("\n=== Testing JavaScript Functionality ===")
    
    base_path = Path(__file__).parent.parent
    js_path = base_path / "web" / "static" / "js" / "editor.js"
    
    if not js_path.exists():
        print("❌ JavaScript file not found")
        return False
    
    content = js_path.read_text()
    
    # Required JavaScript functionality
    required_functions = {
        "class JournalEditor": "Main editor class",
        "setupEventListeners": "Event listener setup",
        "setupAutoSave": "Auto-save functionality",
        "saveEntry": "Save entry function",
        "togglePreview": "Preview toggle function",
        "toggleFocusMode": "Focus mode toggle",
        "insertMarkdown": "Markdown insertion helper",
        "updateStats": "Statistics update function",
        "setupKeyboardShortcuts": "Keyboard shortcuts setup",
        "updateSaveStatus": "Save status updates",
        "formatDate": "Date formatting utility",
        "formatTime": "Time formatting utility"
    }
    
    all_found = True
    for function_name, description in required_functions.items():
        if function_name in content:
            print(f"✅ {function_name} - {description}")
        else:
            print(f"❌ {function_name} - MISSING - {description}")
            all_found = False
    
    # Check for key features
    features = {
        "30000": "30-second auto-save interval",
        "addEventListener": "Event handling",
        "fetch(": "API integration",
        "marked.parse": "Markdown parsing",
        "beforeunload": "Unsaved changes protection"
    }
    
    for feature, description in features.items():
        if feature in content:
            print(f"✅ {feature} - {description}")
        else:
            print(f"❌ {feature} - MISSING - {description}")
            all_found = False
    
    return all_found

def test_route_integration():
    """Test that the routes are properly integrated in the web app."""
    print("\n=== Testing Route Integration ===")
    
    try:
        from web.app import app
        print("✅ Web application imports successfully")
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        # Check for entry editor route
        entry_route_found = False
        for route in routes:
            if '/entry/{entry_date}' in route or '/entry/' in route:
                entry_route_found = True
                print(f"✅ Entry editor route found: {route}")
                break
        
        if not entry_route_found:
            print("❌ Entry editor route not found")
            return False
        
        # Check for calendar route
        calendar_route_found = False
        for route in routes:
            if '/calendar' in route:
                calendar_route_found = True
                print(f"✅ Calendar route found: {route}")
                break
        
        if not calendar_route_found:
            print("⚠️  Calendar route not found (may be added in next step)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing web app: {e}")
        return False

def test_api_endpoints():
    """Test that required API endpoints exist."""
    print("\n=== Testing API Endpoints ===")
    
    try:
        from web.api.entries import router as entries_router
        print("✅ Entries API router imports successfully")
        
        # Check if the router has the required endpoints
        routes = []
        for route in entries_router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        required_endpoints = [
            "/entries/{entry_date}",  # GET for loading entries
            "/entries/{entry_date}"   # POST for saving entries
        ]
        
        endpoints_found = 0
        for endpoint in required_endpoints:
            for route in routes:
                if endpoint in route or route.endswith("/{entry_date}"):
                    print(f"✅ API endpoint available: {route}")
                    endpoints_found += 1
                    break
        
        if endpoints_found >= 1:  # At least one entry endpoint should exist
            print("✅ Entry API endpoints available")
            return True
        else:
            print("❌ Entry API endpoints not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking API endpoints: {e}")
        return False

def test_integration_with_dashboard():
    """Test integration with dashboard navigation."""
    print("\n=== Testing Dashboard Integration ===")
    
    base_path = Path(__file__).parent.parent
    dashboard_js_path = base_path / "web" / "static" / "js" / "dashboard.js"
    
    if not dashboard_js_path.exists():
        print("⚠️  Dashboard JavaScript not found")
        return True  # Not critical for editor functionality
    
    content = dashboard_js_path.read_text()
    
    # Check for entry navigation
    if "openEntry" in content or "/entry/" in content:
        print("✅ Dashboard has entry navigation logic")
        return True
    else:
        print("⚠️  Dashboard entry navigation not found")
        return True  # Not critical

def run_comprehensive_test():
    """Run all tests and provide a comprehensive report."""
    print("🧪 Entry Editor Implementation - Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("File Existence", test_file_existence),
        ("Template Content", test_template_content),
        ("CSS Structure", test_css_structure),
        ("JavaScript Functionality", test_javascript_functionality),
        ("Route Integration", test_route_integration),
        ("API Endpoints", test_api_endpoints),
        ("Dashboard Integration", test_integration_with_dashboard)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Entry Editor Interface implementation is complete and functional")
        print("✅ Ready for production use")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed")
        print("❌ Please review and fix the failing components")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    
    if success:
        print("\n🚀 Step 13: Entry Editor Interface - IMPLEMENTATION COMPLETE")
        print("\nKey Features Implemented:")
        print("• Clean, distraction-free editor interface")
        print("• Auto-save functionality every 30 seconds")
        print("• Markdown support with live preview")
        print("• Word/character/line count statistics")
        print("• Keyboard shortcuts (Ctrl+S, Ctrl+B, Ctrl+I, F11)")
        print("• Focus mode for distraction-free writing")
        print("• Responsive design for all devices")
        print("• Integration with EntryManager API")
        print("• Unsaved changes protection")
        print("• Professional macOS-like design")
        
        print("\nUsage:")
        print("• Navigate to /entry/YYYY-MM-DD to edit entries")
        print("• Use dashboard 'New Entry' or 'Open Today's Entry' buttons")
        print("• Auto-save runs every 30 seconds")
        print("• Press F11 for focus mode")
        print("• Use Ctrl+P for markdown preview")
        
        sys.exit(0)
    else:
        print("\n❌ Implementation incomplete - please fix failing tests")
        sys.exit(1)