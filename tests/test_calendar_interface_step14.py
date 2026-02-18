"""
Test Suite for Step 14: Calendar View Interface Implementation

This test suite validates the calendar interface functionality including:
- Calendar grid rendering and navigation
- Entry indicators and preview functionality
- Responsive design and keyboard navigation
- Integration with CalendarService API
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from web.app import app
from web.database import DatabaseManager
from config_manager import ConfigManager
from file_discovery import FileDiscovery


class TestCalendarInterface:
    """Test calendar interface functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_config(self, temp_workspace):
        """Create test configuration."""
        config_path = temp_workspace / "config.yaml"
        config_content = f"""
processing:
  base_path: "{temp_workspace / 'worklogs'}"
  output_path: "{temp_workspace / 'output'}"
  max_file_size_mb: 10

llm:
  provider: "mock"

logging:
  level: "INFO"
  file_enabled: false
"""
        config_path.write_text(config_content)
        return config_path
    
    @pytest.fixture
    def test_client(self, test_config):
        """Create test client with temporary configuration."""
        import os
        os.environ['CONFIG_PATH'] = str(test_config)
        
        with TestClient(app) as client:
            yield client
    
    @pytest.fixture
    def sample_entries(self, temp_workspace):
        """Create sample journal entries for testing."""
        base_path = temp_workspace / "worklogs"
        
        # Create entries for the current month
        entries = []
        today = date.today()
        
        # Create entries for the past 15 days
        for i in range(15):
            entry_date = today - timedelta(days=i)
            
            # Use FileDiscovery to create proper structure
            file_discovery = FileDiscovery(str(base_path))
            week_ending_date = file_discovery._calculate_week_ending_for_date(entry_date)
            file_path = file_discovery._construct_file_path(entry_date, week_ending_date)
            
            # Create directory structure
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write sample content
            content = f"""
{entry_date.strftime('%A, %B %d, %Y')}

Sample journal entry for {entry_date}.
This is test content for calendar interface testing.
Word count should be calculated correctly.

Tasks completed:
- Task 1 for {entry_date}
- Task 2 for {entry_date}
- Task 3 for {entry_date}

Notes:
This is a sample entry for calendar testing purposes.
Entry created on {entry_date}.
"""
            file_path.write_text(content.strip())
            entries.append({
                'date': entry_date,
                'path': file_path,
                'content': content.strip()
            })
        
        return entries
    
    def test_calendar_page_loads(self, test_client):
        """Test that calendar page loads successfully."""
        response = test_client.get("/calendar")
        assert response.status_code == 200
        assert "Calendar - Daily Work Journal" in response.text
        assert "calendar-container" in response.text
        assert "calendar-grid" in response.text
    
    def test_calendar_api_current_month(self, test_client, sample_entries):
        """Test calendar API for current month."""
        today = date.today()
        response = test_client.get(f"/api/calendar/{today.year}/{today.month}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["year"] == today.year
        assert data["month"] == today.month
        assert "month_name" in data
        assert "entries" in data
        assert isinstance(data["entries"], list)
    
    def test_calendar_api_navigation(self, test_client):
        """Test calendar navigation API."""
        today = date.today()
        response = test_client.get(f"/api/calendar/{today.year}/{today.month}/navigation")
        assert response.status_code == 200
        
        data = response.json()
        assert "current" in data
        assert "previous" in data
        assert "next" in data
        assert "today" in data
        
        assert data["current"]["year"] == today.year
        assert data["current"]["month"] == today.month
    
    def test_calendar_api_today_info(self, test_client):
        """Test today info API endpoint."""
        response = test_client.get("/api/calendar/today")
        assert response.status_code == 200
        
        data = response.json()
        assert "today" in data
        assert "formatted_date" in data
        assert "has_entry" in data
        assert "day_name" in data
    
    def test_calendar_api_date_range(self, test_client, sample_entries):
        """Test calendar date range API."""
        today = date.today()
        start_date = today - timedelta(days=7)
        end_date = today
        
        response = test_client.get(f"/api/calendar/range/{start_date}/{end_date}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should have entries from sample data
        assert len(data) > 0
    
    def test_calendar_api_entry_exists(self, test_client, sample_entries):
        """Test entry existence check API."""
        today = date.today()
        response = test_client.get(f"/api/calendar/date/{today}/exists")
        assert response.status_code == 200
        
        data = response.json()
        assert "date" in data
        assert "has_entry" in data
        assert "formatted_date" in data
        assert "day_name" in data
    
    def test_calendar_api_week_info(self, test_client, sample_entries):
        """Test week info API endpoint."""
        today = date.today()
        print(f"DEBUG: Testing week info for date: {today}")
        print(f"DEBUG: URL: /api/calendar/week/{today}")
        response = test_client.get(f"/api/calendar/week/{today}")
        print(f"DEBUG: Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"DEBUG: Response content: {response.text}")
        assert response.status_code == 200
        
        data = response.json()
        assert "entry_date" in data
        assert "week_start" in data
        assert "week_ending" in data
        assert "entries" in data
        assert "total_entries" in data
    
    def test_calendar_api_stats(self, test_client, sample_entries):
        """Test calendar statistics API."""
        today = date.today()
        response = test_client.get(f"/api/calendar/stats?year={today.year}&month={today.month}")
        assert response.status_code == 200
        
        data = response.json()
        assert "period" in data
        assert "entries" in data
        assert "content" in data
        
        assert data["period"]["year"] == today.year
        assert data["period"]["month"] == today.month
    
    def test_calendar_api_year_overview(self, test_client, sample_entries):
        """Test year overview API endpoint."""
        today = date.today()
        print(f"DEBUG: Testing year overview for year: {today.year}")
        print(f"DEBUG: URL: /api/calendar/months/{today.year}")
        response = test_client.get(f"/api/calendar/months/{today.year}")
        print(f"DEBUG: Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"DEBUG: Response content: {response.text}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["year"] == today.year
        assert "months" in data
        assert len(data["months"]) == 12
        assert "total_entries" in data
        assert "average_completion_rate" in data
    
    def test_calendar_api_validation(self, test_client):
        """Test calendar API input validation."""
        # Test invalid year
        print(f"DEBUG: Testing invalid year validation")
        print(f"DEBUG: URL: /api/calendar/1800/1")
        response = test_client.get("/api/calendar/1800/1")
        print(f"DEBUG: Response status: {response.status_code}")
        if response.status_code != 400:
            print(f"DEBUG: Response content: {response.text}")
        assert response.status_code == 400
        
        # Test invalid month
        response = test_client.get("/api/calendar/2025/13")
        assert response.status_code == 400
        
        # Test invalid date range
        start_date = date.today()
        end_date = start_date - timedelta(days=1)  # End before start
        response = test_client.get(f"/api/calendar/range/{start_date}/{end_date}")
        assert response.status_code == 400
    
    def test_calendar_javascript_structure(self):
        """Test that calendar JavaScript file has correct structure."""
        js_file = Path(__file__).parent.parent / "web" / "static" / "js" / "calendar.js"
        assert js_file.exists(), "Calendar JavaScript file should exist"
        
        content = js_file.read_text()
        
        # Check for key classes and methods
        assert "class CalendarView" in content
        assert "constructor()" in content
        assert "async init()" in content
        assert "async loadCalendarData()" in content
        assert "renderCalendar()" in content
        assert "setupEventListeners()" in content
        assert "async navigateMonth(" in content
        assert "async selectDate(" in content
        assert "async showEntryPreview(" in content
        
        # Check for event handlers
        assert "prev-month-btn" in content
        assert "next-month-btn" in content
        assert "today-btn" in content
        assert "new-entry-btn" in content
        
        # Check for keyboard navigation
        assert "keydown" in content
        assert "ArrowLeft" in content
        assert "ArrowRight" in content
        assert "Escape" in content
    
    def test_calendar_css_structure(self):
        """Test that calendar CSS file has correct structure."""
        css_file = Path(__file__).parent.parent / "web" / "static" / "css" / "calendar.css"
        assert css_file.exists(), "Calendar CSS file should exist"
        
        content = css_file.read_text()
        
        # Check for key CSS classes
        assert ".calendar-container" in content
        assert ".calendar-header" in content
        assert ".calendar-grid" in content
        assert ".calendar-day" in content
        assert ".calendar-day.today" in content
        assert ".calendar-day.has-entry" in content
        assert ".calendar-day.selected" in content
        assert ".entry-preview-panel" in content
        assert ".calendar-sidebar" in content
        
        # Check for responsive design
        assert "@media (max-width: 1024px)" in content
        assert "@media (max-width: 768px)" in content
        
        # Check for animations
        assert "transition:" in content
        assert "transform:" in content
        assert "@keyframes" in content
    
    def test_calendar_template_structure(self):
        """Test that calendar template has correct structure."""
        template_file = Path(__file__).parent.parent / "web" / "templates" / "calendar.html"
        assert template_file.exists(), "Calendar template file should exist"
        
        content = template_file.read_text()
        
        # Check for key template elements
        assert "calendar-container" in content
        assert "calendar-header" in content
        assert "calendar-nav" in content
        assert "prev-month-btn" in content
        assert "next-month-btn" in content
        assert "today-btn" in content
        assert "new-entry-btn" in content
        assert "calendar-grid" in content
        assert "entry-preview-panel" in content
        assert "calendar-sidebar" in content
        
        # Check for legend
        assert "calendar-legend" in content
        assert "legend-dot today" in content
        assert "legend-dot has-entry" in content
        assert "legend-dot selected" in content
        
        # Check for stats section
        assert "stats-card" in content
        assert "month-entries" in content
        assert "month-words" in content
        assert "month-streak" in content
        
        # Check for recent entries
        assert "recent-card" in content
        assert "recent-list" in content


class TestCalendarIntegration:
    """Test calendar integration with other components."""
    
    @pytest.fixture
    def test_client(self):
        """Create test client."""
        with TestClient(app) as client:
            yield client
    
    def test_calendar_entry_creation_integration(self, test_client):
        """Test calendar integration with entry creation."""
        today = date.today().isoformat()
        
        # Create entry via API
        entry_data = {
            "date": today,
            "content": "Test entry for calendar integration"
        }
        
        response = test_client.post(f"/api/entries/{today}", json=entry_data)
        assert response.status_code == 200
        
        # Check that calendar reflects the new entry
        calendar_response = test_client.get(f"/api/calendar/{date.today().year}/{date.today().month}")
        assert calendar_response.status_code == 200
        
        calendar_data = calendar_response.json()
        today_entry = next((e for e in calendar_data["entries"] if e["date"] == today), None)
        assert today_entry is not None
        assert today_entry["has_content"] == True
    
    def test_calendar_navigation_consistency(self, test_client):
        """Test calendar navigation consistency."""
        today = date.today()
        
        # Test current month
        response = test_client.get(f"/api/calendar/{today.year}/{today.month}")
        assert response.status_code == 200
        current_data = response.json()
        
        # Test navigation data
        nav_response = test_client.get(f"/api/calendar/{today.year}/{today.month}/navigation")
        assert nav_response.status_code == 200
        nav_data = nav_response.json()
        
        # Verify consistency
        assert nav_data["current"]["year"] == current_data["year"]
        assert nav_data["current"]["month"] == current_data["month"]
        
        # Test previous month
        prev_year, prev_month = nav_data["previous"]["year"], nav_data["previous"]["month"]
        prev_response = test_client.get(f"/api/calendar/{prev_year}/{prev_month}")
        assert prev_response.status_code == 200
        
        # Test next month
        next_year, next_month = nav_data["next"]["year"], nav_data["next"]["month"]
        next_response = test_client.get(f"/api/calendar/{next_year}/{next_month}")
        assert next_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])