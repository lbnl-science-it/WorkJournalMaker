# Daily Work Journal Web Application - Developer-Ready Specification

## 🎯 Executive Summary

Transform the existing command-line WorkJournalMaker into a cross-platform web application that provides a user-friendly interface for daily journal entry creation while maintaining full compatibility with the existing summarization system. The application will run as a local web server accessible through any browser, packaged as standalone executables for Windows, macOS, and Linux.

## 📋 Requirements

### Functional Requirements

#### FR1: Daily Journal Entry Management
- **FR1.1:** Users can create a new journal entry for today's date with a single button click
- **FR1.2:** Each entry automatically includes "Day and Date" header (e.g., "Monday, June 23, 2025")
- **FR1.3:** Users can edit any existing entry at any time (no restrictions)
- **FR1.4:** Entries auto-save every 30 seconds with manual save option
- **FR1.5:** Real-time word count display during editing

#### FR2: Calendar Navigation System
- **FR2.1:** Monthly calendar view showing all dates with visual indicators for existing entries
- **FR2.2:** Users can click any date to view/edit that day's entry
- **FR2.3:** Month navigation (previous/next) with "Today" quick access
- **FR2.4:** Clear visual distinction between dates with and without entries

#### FR3: File System Compatibility
- **FR3.1:** Maintain existing directory structure: `worklogs_YYYY/worklogs_YYYY-MM/week_ending_YYYY-MM-DD/worklog_YYYY-MM-DD.txt`
- **FR3.2:** Automatic directory creation when needed
- **FR3.3:** Files remain editable outside the application
- **FR3.4:** Full compatibility with existing summarization system

#### FR4: Summarization Integration
- **FR4.1:** Manual date range entry (YYYY-MM-DD format)
- **FR4.2:** Weekly and monthly summary type selection
- **FR4.3:** Real-time progress display during summarization
- **FR4.4:** Summary results displayed in web interface
- **FR4.5:** Direct integration with existing summarization modules

#### FR5: Configuration Management
- **FR5.1:** Inherit settings from existing config.yaml
- **FR5.2:** Web interface for common settings (worklog storage directory, output directory)
- **FR5.3:** Settings persistence in local database
- **FR5.4:** Configuration validation and error reporting

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1:** Application startup time < 3 seconds
- **NFR1.2:** Memory usage < 100MB baseline
- **NFR1.3:** Calendar loading < 1 second for any month
- **NFR1.4:** Auto-save operations without UI lag

#### NFR2: Usability
- **NFR2.1:** Single-click access to today's entry
- **NFR2.2:** Maximum 2 clicks to access any historical entry
- **NFR2.3:** Responsive design for different screen sizes
- **NFR2.4:** Keyboard shortcuts for common actions

#### NFR3: Reliability
- **NFR3.1:** <1% error rate in normal usage
- **NFR3.2:** Graceful handling of file system errors
- **NFR3.3:** Data integrity protection during concurrent access
- **NFR3.4:** Automatic recovery from temporary failures

#### NFR4: Security
- **NFR4.1:** Local-only web server (127.0.0.1 binding)
- **NFR4.2:** No external network access
- **NFR4.3:** File system access restricted to configured directories
- **NFR4.4:** Input sanitization and validation

#### NFR5: Cross-Platform Compatibility
- **NFR5.1:** Identical functionality on Windows, macOS, and Linux
- **NFR5.2:** Standalone executables requiring no Python installation
- **NFR5.3:** Native file system integration on each platform

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Browser                         │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP (localhost:8080)
┌─────────────────────▼───────────────────────────────────┐
│                FastAPI Web Server                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐│
│  │   Entry     │ │  Calendar   │ │   Summarization     ││
│  │  Manager    │ │   Service   │ │     Service         ││
│  └─────────────┘ └─────────────┘ └─────────────────────┘│
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐│
│  │   SQLite    │ │    File     │ │    Existing         ││
│  │  Database   │ │   System    │ │   Summarizer        ││
│  └─────────────┘ └─────────────┘ └─────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Backend Framework** | FastAPI | Modern Python framework, async support, automatic API docs, seamless integration with existing codebase |
| **Database** | SQLite | Serverless, cross-platform, no setup required, perfect for local applications |
| **Frontend** | HTML/CSS/JavaScript (Vanilla) | Lightweight, no build process, universal browser compatibility |
| **Packaging** | PyInstaller | Creates standalone executables, cross-platform support |
| **Web Server** | Uvicorn | High-performance ASGI server, built-in with FastAPI |

### Data Architecture

#### Hybrid Storage System
- **Primary Storage:** File system (maintains existing structure for compatibility)
- **Secondary Storage:** SQLite database (indexes, metadata, fast queries)

#### Database Schema
```sql
CREATE TABLE journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    week_ending_date DATE NOT NULL,
    word_count INTEGER DEFAULT 0,
    has_content BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_entries_date ON journal_entries(date);
CREATE INDEX idx_entries_week_ending ON journal_entries(week_ending_date);
CREATE INDEX idx_entries_modified ON journal_entries(modified_at);
```

#### File System Structure (Unchanged)
```
{base_path}/  ← Configurable worklog storage directory
├── worklogs_2024/
│   ├── worklogs_2024-01/
│   │   └── week_ending_2024-01-05/
│   │       ├── worklog_2024-01-01.txt
│   │       ├── worklog_2024-01-02.txt
│   │       └── worklog_2024-01-05.txt
│   └── worklogs_2024-12/
│       └── week_ending_2025-01-03/  ← Cross-year support
│           ├── worklog_2024-12-30.txt
│           └── worklog_2024-12-31.txt
└── worklogs_2025/
    └── worklogs_2025-01/
        └── week_ending_2025-01-03/
            ├── worklog_2025-01-01.txt
            ├── worklog_2025-01-02.txt
            └── worklog_2025-01-03.txt
```

## 🔧 Detailed Technical Specifications

### Core Services

#### 1. FileManager Service
```python
class FileManager:
    """Handles all file system operations following existing structure"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path).expanduser()
    
    def get_entry_path(self, entry_date: date) -> Path:
        """Calculate file path: base_path/worklogs_YYYY/worklogs_YYYY-MM/week_ending_YYYY-MM-DD/worklog_YYYY-MM-DD.txt"""
        
    def calculate_week_ending(self, entry_date: date) -> date:
        """Find Friday of the week containing entry_date"""
        
    def read_entry(self, entry_date: date) -> str:
        """Read entry content, return empty string if file doesn't exist"""
        
    def write_entry(self, entry_date: date, content: str) -> bool:
        """Write entry content, create directories as needed"""
        
    def ensure_directory_exists(self, dir_path: Path) -> bool:
        """Create directory structure if it doesn't exist"""
```

#### 2. JournalDatabase Service
```python
class JournalDatabase:
    """SQLite database operations for indexing and metadata"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.init_database()
    
    def sync_with_filesystem(self, base_path: Path) -> int:
        """Scan filesystem and update database index"""
        
    def add_entry(self, date: date, file_path: Path, week_ending: date) -> bool:
        """Add or update entry record"""
        
    def get_entry_by_date(self, entry_date: date) -> Optional[JournalEntry]:
        """Retrieve entry metadata by date"""
        
    def get_recent_entries(self, limit: int = 10) -> List[JournalEntry]:
        """Get recent entries for dashboard"""
        
    def get_entries_for_month(self, year: int, month: int) -> List[JournalEntry]:
        """Get all entries for calendar display"""
        
    def update_word_count(self, entry_date: date, word_count: int) -> bool:
        """Update word count for an entry"""
```

#### 3. CalendarService
```python
class CalendarService:
    """Calendar data processing and navigation"""
    
    def __init__(self, database: JournalDatabase):
        self.db = database
    
    def get_month_data(self, year: int, month: int) -> CalendarMonth:
        """Generate calendar grid with entry indicators"""
        
    def get_adjacent_months(self, year: int, month: int) -> Tuple[date, date]:
        """Get previous and next month for navigation"""
        
    def has_entry(self, entry_date: date) -> bool:
        """Check if entry exists for given date"""
```

#### 4. SummarizationService
```python
class SummarizationService:
    """Integration with existing summarization system"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    async def generate_summary(self, start_date: date, end_date: date, 
                             summary_type: str) -> SummaryResult:
        """Run existing summarizer with progress tracking"""
        
    def validate_date_range(self, start_date: date, end_date: date) -> bool:
        """Validate summarization date range"""
        
    def get_progress_updates(self) -> AsyncGenerator[ProgressUpdate, None]:
        """Stream progress updates during summarization"""
```

### API Endpoints

#### Entry Management
```python
@app.get("/")
async def dashboard(request: Request):
    """Main dashboard page"""

@app.get("/calendar")
async def calendar_view(request: Request):
    """Calendar navigation page"""

@app.get("/api/entries/recent")
async def get_recent_entries(limit: int = 10) -> List[JournalEntryResponse]:
    """Get recent journal entries for dashboard"""

@app.get("/api/entries/{date}")
async def get_entry(date: str) -> JournalEntryResponse:
    """Get specific entry by date (YYYY-MM-DD)"""

@app.post("/api/entries/new")
async def create_entry() -> JournalEntryResponse:
    """Create new entry for today with auto-header"""

@app.put("/api/entries/{date}")
async def update_entry(date: str, request: UpdateEntryRequest) -> JournalEntryResponse:
    """Update existing entry content"""
```

#### Calendar Navigation
```python
@app.get("/api/calendar/{year}/{month}")
async def get_calendar_data(year: int, month: int) -> CalendarResponse:
    """Get calendar data with entry indicators"""

@app.get("/api/calendar/today")
async def get_today_info() -> TodayResponse:
    """Get today's date and entry status"""
```

#### Summarization
```python
@app.post("/api/summarize")
async def generate_summary(request: SummarizeRequest) -> SummaryResponse:
    """Generate summary using existing system"""

@app.get("/api/summarize/progress/{task_id}")
async def get_summary_progress(task_id: str) -> ProgressResponse:
    """Get summarization progress"""
```

#### Configuration
```python
@app.get("/api/settings")
async def get_settings() -> SettingsResponse:
    """Get current application settings"""

@app.put("/api/settings")
async def update_settings(request: UpdateSettingsRequest) -> SettingsResponse:
    """Update application settings"""

@app.post("/api/settings/validate-path")
async def validate_path(request: ValidatePathRequest) -> ValidationResponse:
    """Validate directory path accessibility"""
```

### Data Models

#### Request/Response Models
```python
from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class JournalEntryResponse(BaseModel):
    date: date
    content: str
    word_count: int
    has_content: bool
    created_at: datetime
    modified_at: datetime

class UpdateEntryRequest(BaseModel):
    content: str

class CalendarResponse(BaseModel):
    year: int
    month: int
    month_name: str
    calendar_grid: List[List[int]]  # Calendar grid (weeks x days)
    entry_dates: List[date]         # Dates with entries
    today: date

class SummarizeRequest(BaseModel):
    start_date: date
    end_date: date
    summary_type: str  # "weekly" or "monthly"

class SummaryResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None

class SettingsResponse(BaseModel):
    base_path: str      # Worklog storage directory
    output_path: str    # Summary output directory
    auto_save_interval: int  # Seconds
    
class UpdateSettingsRequest(BaseModel):
    base_path: Optional[str] = None
    output_path: Optional[str] = None
    auto_save_interval: Optional[int] = None
```

## 🎨 User Interface Specifications

### Main Dashboard Layout
```html
<!DOCTYPE html>
<html>
<head>
    <title>Daily Work Journal</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <header>
        <h1>Daily Work Journal</h1>
        <nav>
            <button id="calendar-btn">📅 Calendar</button>
            <button id="settings-btn">⚙️ Settings</button>
        </nav>
    </header>
    
    <main>
        <section id="today-section">
            <h2>📅 Today: <span id="today-date"></span></h2>
            <button id="new-entry-btn" class="primary-btn">New Entry</button>
        </section>
        
        <section id="recent-entries">
            <h3>Recent Entries</h3>
            <div id="entries-list">
                <!-- Populated by JavaScript -->
            </div>
        </section>
        
        <section id="summarization">
            <h3>Generate Summary</h3>
            <form id="summary-form">
                <label>Start Date: <input type="date" id="start-date" required></label>
                <label>End Date: <input type="date" id="end-date" required></label>
                <label>Type: 
                    <select id="summary-type" required>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                    </select>
                </label>
                <button type="submit">Generate Summary</button>
            </form>
            <div id="progress-container" style="display: none;">
                <div id="progress-bar"></div>
                <div id="progress-text"></div>
            </div>
            <div id="summary-result"></div>
        </section>
    </main>
    
    <script src="/static/js/main.js"></script>
</body>
</html>
```

### Calendar View Layout
```html
<div id="calendar-container">
    <header id="calendar-header">
        <button id="prev-month">‹</button>
        <h2 id="month-year">June 2025</h2>
        <button id="next-month">›</button>
        <button id="today-btn">Today</button>
    </header>
    
    <div id="calendar-grid">
        <div class="calendar-weekdays">
            <div>Sun</div><div>Mon</div><div>Tue</div>
            <div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div>
        </div>
        <div class="calendar-days">
            <!-- Generated by JavaScript -->
        </div>
    </div>
    
    <div id="calendar-legend">
        <span>● = Has Entry</span>
        <span>* = Today</span>
    </div>
</div>
```

### Entry Editor Layout
```html
<div id="editor-container">
    <header id="editor-header">
        <button id="back-btn">← Back</button>
        <h2 id="entry-date">Monday, June 23, 2025</h2>
        <button id="save-btn" class="primary-btn">Save</button>
    </header>
    
    <main id="editor-main">
        <textarea id="entry-content" placeholder="Write your journal entry here..."></textarea>
    </main>
    
    <footer id="editor-footer">
        <span id="word-count">0 words</span>
        <span id="save-status">Auto-saved 2 minutes ago</span>
    </footer>
</div>
```

### CSS Styling Guidelines
```css
/* Color Scheme */
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --success-color: #059669;
    --warning-color: #d97706;
    --error-color: #dc2626;
    --background-color: #f8fafc;
    --surface-color: #ffffff;
    --text-color: #1e293b;
    --text-muted: #64748b;
}

/* Typography */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: var(--text-color);
}

/* Layout */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Buttons */
.primary-btn {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.primary-btn:hover {
    background-color: #1d4ed8;
}

/* Calendar Styling */
.calendar-day {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #e2e8f0;
    cursor: pointer;
    position: relative;
}

.calendar-day.has-entry::after {
    content: '●';
    position: absolute;
    bottom: 2px;
    right: 2px;
    color: var(--primary-color);
    font-size: 8px;
}

.calendar-day.today {
    background-color: var(--primary-color);
    color: white;
}
```

## 🔒 Error Handling Strategy

### Error Categories and Responses

#### 1. File System Errors
```python
class FileSystemError(Exception):
    """Base class for file system related errors"""
    pass

class DirectoryNotFoundError(FileSystemError):
    """Raised when base directory doesn't exist"""
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Directory not found: {path}")

class PermissionError(FileSystemError):
    """Raised when insufficient permissions"""
    def __init__(self, path: str, operation: str):
        self.path = path
        self.operation = operation
        super().__init__(f"Permission denied for {operation} on {path}")

# Error Handler
@app.exception_handler(FileSystemError)
async def file_system_error_handler(request: Request, exc: FileSystemError):
    return JSONResponse(
        status_code=500,
        content={
            "error": "file_system_error",
            "message": str(exc),
            "recovery_suggestions": [
                "Check that the directory exists",
                "Verify read/write permissions",
                "Try a different directory"
            ]
        }
    )
```

#### 2. Database Errors
```python
class DatabaseError(Exception):
    """Database operation errors"""
    pass

@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "database_error",
            "message": "Internal database error occurred",
            "recovery_suggestions": [
                "Try refreshing the page",
                "Restart the application if problem persists"
            ]
        }
    )
```

#### 3. Validation Errors
```python
from pydantic import ValidationError

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Invalid input data",
            "details": exc.errors()
        }
    )
```

#### 4. Summarization Errors
```python
class SummarizationError(Exception):
    """Errors during summary generation"""
    pass

@app.exception_handler(SummarizationError)
async def summarization_error_handler(request: Request, exc: SummarizationError):
    return JSONResponse(
        status_code=500,
        content={
            "error": "summarization_error",
            "message": str(exc),
            "recovery_suggestions": [
                "Check your LLM provider configuration",
                "Verify internet connection",
                "Try a smaller date range"
            ]
        }
    )
```

### Frontend Error Handling
```javascript
// Global error handler
class ErrorHandler {
    static show(error, container = document.body) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <div class="error-content">
                <h4>Error: ${error.error || 'Unknown Error'}</h4>
                <p>${error.message}</p>
                ${error.recovery_suggestions ? 
                    `<ul>${error.recovery_suggestions.map(s => `<li>${s}</li>`).join('')}</ul>` 
                    : ''}
                <button onclick="this.parentElement.parentElement.remove()">Dismiss</button>
            </div>
        `;
        container.appendChild(errorDiv);
        
        // Auto-dismiss after 10 seconds
        setTimeout(() => errorDiv.remove(), 10000);
    }
    
    static async handleApiError(response) {
        if (!response.ok) {
            const error = await response.json();
            this.show(error);
            throw new Error(error.message);
        }
        return response;
    }
}

// Usage in API calls
async function saveEntry(date, content) {
    try {
        const response = await fetch(`/api/entries/${date}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({content})
        });
        
        await ErrorHandler.handleApiError(response);
        return await response.json();
    } catch (error) {
        console.error('Failed to save entry:', error);
        throw error;
    }
}
```

## 🧪 Testing Strategy

### Unit Testing Framework
```python
# pytest configuration (pytest.ini)
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=web_app --cov-report=html --cov-report=term-missing

# Example unit tests
import pytest
from datetime import date
from web_app.services.file_manager import FileManager
from web_app.models.database import JournalDatabase

class TestFileManager:
    @pytest.fixture
    def file_manager(self, tmp_path):
        return FileManager(str(tmp_path))
    
    def test_get_entry_path(self, file_manager):
        """Test file path generation follows existing structure"""
        path = file_manager.get_entry_path(date(2025, 6, 23))
        expected_parts = [
            "worklogs_2025",
            "worklogs_2025-06", 
            "week_ending_2025-06-27",
            "worklog_2025-06-23.txt"
        ]
        for part in expected_parts:
            assert part in str(path)
    
    def test_calculate_week_ending(self, file_manager):
        """Test week ending calculation (Friday of week)"""
        # Monday should end on Friday
        assert file_manager.calculate_week_ending(date(2025, 6, 23)) == date(2025, 6, 27)
        # Friday should end on same Friday
        assert file_manager.calculate_week_ending(date(2025, 6, 27)) == date(2025, 6, 27)
        # Sunday should end on next Friday
        assert file_manager.calculate_week_ending(date(2025, 6, 22)) == date(2025, 6, 27)
    
    def test_write_and_read_entry(self, file_manager):
        """Test complete write/read cycle"""
        test_date = date(2025, 6, 23)
        test_content = "Monday, June 23, 2025\n\nTest entry content"
        
        # Write entry
        assert file_manager.write_entry(test_date, test_content) == True
        
        # Read entry
        read_content = file_manager.read_entry(test_date)
        assert read_content == test_content
        
        # Verify file exists at correct path
        expected_path = file_manager.get_entry_path(test_date)
        assert expected_path.exists()

class TestJournalDatabase:
    @pytest.fixture
    def database(self, tmp_path):
        db_path = tmp_path / "test.db"
        return JournalDatabase(db_path)
    
    def test_add_and_retrieve_entry(self, database):
        """Test entry CRUD operations"""
        test_date = date(2025, 6, 23)
        test_path = Path("/test/path/worklog_2025-06-23.txt")
        week_ending = date(2025, 6, 27)
        
        # Add entry
        assert database.add_entry(test_date, test_path, week_ending) == True
        
        # Retrieve entry
        entry = database.get_entry_by_date(test_date)
        assert entry is not None
        assert entry.date == test_date
        assert entry.file_path == str(test_path)
        assert entry.week_ending_date == week_ending
    
    def test_get_entries_for_month(self, database):
        """Test calendar month queries"""
        # Add entries for June 2025
        dates = [date(2025, 6, 1), date(2025, 6, 15), date(2025, 6, 30)]
        for d in dates:
            database.add_entry(d, Path(f"/test/worklog_{d}.txt"), d)
        
        # Query June entries
        june_entries = database.get_entries_for_month(2025, 6)
        assert len(june_entries) == 3
        
        # Query different month (should be empty)
        may_entries = database.get_entries_for_month(2025, 5)
        assert len(may_entries) == 0
```

### Integration Testing
```python
import pytest
from fastapi.testclient import TestClient
from web_app.main import app

client = TestClient(app)

class TestAPIEndpoints:
    def test_create_and_retrieve_entry(self):
        """Test complete entry workflow"""
        # Create new entry
        response = client.post("/api/entries/new")
        assert response.status_code == 200
        data = response.json()
        assert "Monday" in data["content"] or "Tuesday" in data["content"]  # Auto-header
        
        # Retrieve entry
        today = date.today().isoformat()
        response = client.get(f"/api/entries/{today}")
        assert response.status_code == 200
        
        # Update entry
        new_content = f"{data['content']}\n\nUpdated content"
        response = client.put(f"/api/entries/{today}", 
                            json={"content": new_content})
        assert response.status_code == 200
        assert response.json()["content"] == new_content
    
    def test_calendar_api(self):
        """Test calendar data retrieval"""
        response = client.get("/api/calendar/2025/6")
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2025
        assert data["month"] == 6
        assert data["month_name"] == "June"
        assert isinstance(data["calendar_grid"], list)
        assert isinstance(data["entry_dates"], list)
    
    def test_settings_management(self):
        """Test settings CRUD operations"""
        # Get current settings
        response = client.get("/api/settings")
        assert response.status_code == 200
        original_settings = response.json()
        
        # Update settings
        new_settings = {
            "base_path": "/new/test/path",
            "auto_save_interval": 60
        }
        response = client.put("/api/settings", json=new_settings)
        assert response.status_code == 200
        
        # Verify update
        response = client.get("/api/settings")
        updated_settings = response.json()
        assert updated_settings["base_path"] == "/new/test/path"
        assert updated_settings["auto_save_interval"] == 60
```

### End-to-End Testing
```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.