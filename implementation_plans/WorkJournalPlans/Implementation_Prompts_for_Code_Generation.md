# Implementation Prompts for Code Generation

This document contains detailed prompts for implementing each step of the Daily Work Journal Web Application. Each prompt is designed to be used with a code-generation LLM in a test-driven manner, building incrementally on previous work.

---

## **Prompt 1: Project Foundation Setup**

```
Create the foundational structure for a FastAPI-based Daily Work Journal web application. Set up a clean, professional project structure with the following requirements:

1. Create a `web_app/` directory with proper Python package structure
2. Set up FastAPI application with basic configuration
3. Add SQLite database integration using SQLAlchemy
4. Include static file serving for CSS/JS/images
5. Create basic error handling and logging
6. Add development server configuration
7. Update requirements.txt with web dependencies: fastapi, uvicorn, sqlalchemy, jinja2

Project structure should be:
```
web_app/
├── __init__.py
├── main.py              # FastAPI application
├── database.py          # Database configuration
├── models/              # Pydantic models
│   ├── __init__.py
│   └── journal.py
├── services/            # Business logic
│   └── __init__.py
├── api/                 # API routes
│   ├── __init__.py
│   └── entries.py
├── templates/           # Jinja2 templates
└── static/              # CSS, JS, images
    ├── css/
    ├── js/
    └── images/
```

Include comprehensive error handling, proper logging setup, and ensure the development server can start successfully. Add health check endpoint at `/health` that returns application status.

Write complete, production-ready code with proper type hints, docstrings, and error handling. Include basic tests to verify the setup works correctly.
```

---

## **Prompt 2: Database Schema and Models**

```
Implement the SQLite database schema and Pydantic models for the Daily Work Journal web application. Create a hybrid storage system that maintains file system compatibility while providing fast database queries.

Requirements:
1. Create SQLAlchemy models for journal entries and settings
2. Implement database schema matching the specification:
   - journal_entries table with date, file_path, week_ending_date, word_count, has_content, timestamps
   - app_settings table for configuration storage
   - Proper indexes for performance
3. Create Pydantic models for API requests/responses
4. Add database migration system
5. Include connection management and session handling
6. Add data validation and constraints

Database Schema:
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
```

Pydantic Models needed:
- JournalEntryResponse, UpdateEntryRequest
- CalendarResponse, SummarizeRequest, SummaryResponse
- SettingsResponse, UpdateSettingsRequest

Include proper error handling, data validation, and comprehensive tests. Ensure backward compatibility with existing file structure. Write clean, maintainable code with full type annotations.
```

---

## **Prompt 3: File System Integration Service**

```
Create the FileManager service that integrates with the existing file discovery system while maintaining full compatibility with the current directory structure. This service should bridge the web application with the existing CLI codebase.

Requirements:
1. Create FileManager class that works with existing FileDiscovery
2. Maintain directory structure: ~/Desktop/worklogs/worklogs_YYYY/worklogs_YYYY-MM/week_ending_YYYY-MM-DD/worklog_YYYY-MM-DD.txt
3. Implement file operations: read, write, create directories
4. Add integration with existing file_discovery.py
5. Include error handling for file system operations
6. Add file system monitoring capabilities
7. Implement week ending date calculation (Friday of week)

Key Methods:
- get_entry_path(entry_date: date) -> Path
- calculate_week_ending(entry_date: date) -> date  
- read_entry(entry_date: date) -> str
- write_entry(entry_date: date, content: str) -> bool
- ensure_directory_exists(dir_path: Path) -> bool
- sync_with_filesystem(base_path: Path) -> int

Integration points:
- Use existing FileDiscovery class from file_discovery.py
- Maintain compatibility with existing directory structure
- Support cross-year date ranges
- Handle missing files gracefully

Include comprehensive error handling, logging, and unit tests. Ensure the service can handle concurrent access and file system errors gracefully. Write production-ready code with proper documentation.
```

---

## **Prompt 4: Journal Entry CRUD API**

```
Implement comprehensive CRUD operations for journal entries with REST API endpoints. Create a robust system that maintains data consistency between the SQLite database and file system.

Requirements:
1. Create JournalDatabase service for database operations
2. Implement API endpoints for entry management:
   - GET /api/entries/recent - Get recent entries
   - GET /api/entries/{date} - Get specific entry
   - POST /api/entries/new - Create new entry for today
   - PUT /api/entries/{date} - Update entry content
3. Add automatic header generation for new entries (e.g., "Monday, June 23, 2025")
4. Implement word count tracking and updates
5. Add entry metadata management
6. Include data validation and error handling
7. Add database-file system synchronization

API Endpoints:
```python
@app.get("/api/entries/recent")
async def get_recent_entries(limit: int = 10) -> List[JournalEntryResponse]

@app.get("/api/entries/{date}")
async def get_entry(date: str) -> JournalEntryResponse

@app.post("/api/entries/new")
async def create_entry() -> JournalEntryResponse

@app.put("/api/entries/{date}")
async def update_entry(date: str, request: UpdateEntryRequest) -> JournalEntryResponse
```

Key Features:
- Auto-generate date headers for new entries
- Real-time word count calculation
- Atomic operations for data consistency
- Proper error responses with helpful messages
- Input validation and sanitization

Include comprehensive error handling, input validation, and integration tests. Ensure data consistency between database and file system. Write clean, maintainable code with proper documentation and type hints.
```

---

## **Prompt 5: Calendar Navigation System**

```
Develop the CalendarService and API endpoints for calendar navigation with entry indicators. Create an efficient system for displaying monthly calendars with visual indicators for existing entries.

Requirements:
1. Create CalendarService class for calendar data processing
2. Implement calendar grid generation for any month/year
3. Add entry existence indicators
4. Create API endpoints for calendar data
5. Support month navigation (previous/next/today)
6. Optimize database queries for performance
7. Add caching for frequently accessed data

API Endpoints:
```python
@app.get("/api/calendar/{year}/{month}")
async def get_calendar_data(year: int, month: int) -> CalendarResponse

@app.get("/api/calendar/today")
async def get_today_info() -> TodayResponse
```

CalendarService Methods:
- get_month_data(year: int, month: int) -> CalendarMonth
- get_adjacent_months(year: int, month: int) -> Tuple[date, date]
- has_entry(entry_date: date) -> bool

Calendar Response Structure:
```python
class CalendarResponse(BaseModel):
    year: int
    month: int
    month_name: str
    calendar_grid: List[List[int]]  # Calendar grid (weeks x days)
    entry_dates: List[date]         # Dates with entries
    today: date
```

Include proper error handling, performance optimization, and comprehensive tests. Ensure the calendar system can handle large datasets efficiently. Write clean, maintainable code with full documentation.
```

---

## **Prompt 6: Base UI Templates and CSS Framework**

```
Create the foundational HTML templates and CSS framework with minimalistic, clean, premium, aesthetic, macos-like design. Establish a consistent design system that provides a professional, modern user experience.

Requirements:
1. Create base HTML template with proper structure
2. Develop CSS framework with macos-like design principles:
   - Clean typography using system fonts
   - Subtle shadows and rounded corners
   - Consistent spacing and layout
   - Professional color scheme
   - Smooth transitions and animations
3. Implement responsive design for different screen sizes
4. Add component library for buttons, forms, cards
5. Include accessibility features (ARIA labels, keyboard navigation)
6. Create layout templates for different page types

Design Principles:
- Minimalistic and clean interface
- Premium, professional appearance
- macOS-like aesthetic with subtle details
- Consistent spacing and typography
- Smooth, subtle animations
- High contrast for readability

Base Template Structure:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Daily Work Journal{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <header class="app-header">
        <!-- Navigation -->
    </header>
    <main class="app-main">
        {% block content %}{% endblock %}
    </main>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

CSS Framework Features:
- CSS custom properties for theming
- Flexbox/Grid layouts
- Component-based styling
- Responsive breakpoints
- Smooth transitions
- Focus states for accessibility

Include comprehensive CSS documentation and ensure cross-browser compatibility. Create a style guide showing all components and their usage.
```

---

## **Prompt 7: Dashboard Interface**

```
Implement the main dashboard interface with minimalistic, clean, premium, aesthetic, macos-like design. Create an intuitive homepage that provides quick access to today's entry, recent entries, and key functionality.

Requirements:
1. Create dashboard HTML template with clean, professional layout
2. Implement JavaScript for dynamic content loading
3. Add "New Entry" button with single-click access to today's entry
4. Display recent entries with preview and quick access
5. Include today's date prominently with entry status
6. Add smooth animations and transitions
7. Implement responsive design for different screen sizes

Dashboard Features:
- Today's entry section with prominent "New Entry" button
- Recent entries list with entry previews
- Quick navigation to calendar view
- Settings access
- Clean, uncluttered layout with plenty of white space

HTML Structure:
```html
<main class="dashboard">
    <section class="today-section">
        <h2 class="today-header">
            <span class="today-label">Today</span>
            <span class="today-date" id="today-date"></span>
        </h2>
        <button id="new-entry-btn" class="primary-btn">
            <span class="btn-icon">✏️</span>
            <span class="btn-text">New Entry</span>
        </button>
    </section>
    
    <section class="recent-entries">
        <h3>Recent Entries</h3>
        <div id="entries-list" class="entries-grid">
            <!-- Populated by JavaScript -->
        </div>
    </section>
</main>
```

JavaScript Features:
- Dynamic date display
- Recent entries loading
- Smooth page transitions
- Error handling with user feedback
- Loading states and animations

Design Requirements:
- Minimalistic, clean interface
- Premium, professional appearance  
- macOS-like aesthetic with subtle shadows
- Consistent spacing and typography
- Smooth hover effects and transitions
- Responsive layout for mobile/tablet

Include comprehensive JavaScript functionality with error handling and loading states. Ensure accessibility compliance and smooth user experience.
```

---

## **Prompt 8: Calendar View Interface**

```
Develop the calendar navigation interface with minimalistic, clean, premium, aesthetic, macos-like styling. Create an intuitive calendar view that clearly shows entry indicators and provides seamless month navigation.

Requirements:
1. Create calendar view template with professional grid layout
2. Implement interactive calendar with entry indicators
3. Add smooth month navigation (previous/next/today)
4. Include clear visual distinction for dates with/without entries
5. Add hover effects and click interactions
6. Implement responsive design for different screen sizes
7. Include keyboard navigation support

Calendar Features:
- Monthly calendar grid with proper week layout
- Clear entry indicators (dots or highlights)
- Today's date highlighting
- Month/year navigation controls
- "Today" quick access button
- Smooth transitions between months

HTML Structure:
```html
<div class="calendar-container">
    <header class="calendar-header">
        <button id="prev-month" class="nav-btn" aria-label="Previous month">‹</button>
        <h2 id="month-year" class="month-title">June 2025</h2>
        <button id="next-month" class="nav-btn" aria-label="Next month">›</button>
        <button id="today-btn" class="today-btn">Today</button>
    </header>
    
    <div class="calendar-grid">
        <div class="calendar-weekdays">
            <div class="weekday">Sun</div>
            <div class="weekday">Mon</div>
            <!-- ... -->
        </div>
        <div class="calendar-days" id="calendar-days">
            <!-- Generated by JavaScript -->
        </div>
    </div>
    
    <div class="calendar-legend">
        <span class="legend-item">
            <span class="legend-dot has-entry"></span>
            Has Entry
        </span>
        <span class="legend-item">
            <span class="legend-dot today"></span>
            Today
        </span>
    </div>
</div>
```

JavaScript Features:
- Dynamic calendar generation
- Month navigation with smooth transitions
- Entry indicator management
- Date click handling
- Keyboard navigation (arrow keys)
- Loading states and error handling

Design Requirements:
- Minimalistic, clean calendar grid
- Premium, professional appearance
- macOS-like aesthetic with subtle styling
- Clear visual hierarchy
- Smooth hover and click effects
- Responsive layout for mobile devices

Include comprehensive JavaScript functionality with proper event handling and accessibility features. Ensure smooth user experience with loading states and error handling.
```

---

## **Prompt 9: Entry Editor Interface**

```
Create the journal entry editor with minimalistic, clean, premium, aesthetic, macos-like design. Develop a seamless editing experience with real-time features, auto-save functionality, and professional styling.

Requirements:
1. Create entry editor template with clean, focused layout
2. Implement real-time word count display
3. Add auto-save functionality with status indicators
4. Include keyboard shortcuts for common actions
5. Add smooth transitions and professional styling
6. Implement responsive design for different screen sizes
7. Include accessibility features and proper focus management

Editor Features:
- Large, comfortable textarea for writing
- Real-time word count display
- Auto-save status with timestamps
- Save button for manual saves
- Back navigation to previous view
- Date header display
- Clean, distraction-free interface

HTML Structure:
```html
<div class="editor-container">
    <header class="editor-header">
        <button id="back-btn" class="back-btn" aria-label="Go back">
            <span class="back-icon">←</span>
            <span class="back-text">Back</span>
        </button>
        <h2 id="entry-date" class="entry-date">Monday, June 23, 2025</h2>
        <button id="save-btn" class="primary-btn">
            <span class="save-icon">💾</span>
            <span class="save-text">Save</span>
        </button>
    </header>
    
    <main class="editor-main">
        <textarea 
            id="entry-content" 
            class="entry-textarea"
            placeholder="Write your journal entry here..."
            aria-label="Journal entry content"
        ></textarea>
    </main>
    
    <footer class="editor-footer">
        <span id="word-count" class="word-count">0 words</span>
        <span id="save-status" class="save-status">Auto-saved 2 minutes ago</span>
    </footer>
</div>
```

JavaScript Features:
- Real-time word count calculation
- Auto-save with configurable intervals
- Save status updates with timestamps
- Keyboard shortcuts (Ctrl+S for save)
- Content change detection
- Error handling with user feedback
- Loading states for save operations

Design Requirements:
- Minimalistic, clean editor interface
- Premium, professional appearance
- macOS-like aesthetic with subtle details
- Comfortable typography for writing
- Smooth transitions and animations
- Responsive layout for mobile/tablet
- Distraction-free writing environment

Include comprehensive JavaScript functionality with proper error handling, auto-save logic, and accessibility features. Ensure smooth user experience with clear feedback for all operations.
```

---

## **Prompt 10: Summarization Integration**

```
Integrate the existing summarization system into the web application while maintaining full compatibility. Create a web-based interface for generating summaries with progress tracking and results display.

Requirements:
1. Create SummarizationService that wraps existing summarizer
2. Integrate with existing components:
   - unified_llm_client.py
   - summary_generator.py  
   - content_processor.py
   - config_manager.py
3. Add progress tracking for long-running operations
4. Implement async task handling
5. Create API endpoints for summarization
6. Add error handling and recovery
7. Maintain compatibility with existing configuration

Integration Points:
- Use existing UnifiedLLMClient for LLM operations
- Leverage existing SummaryGenerator for processing
- Maintain existing config.yaml compatibility
- Support both weekly and monthly summaries
- Handle existing file discovery system

API Endpoints:
```python
@app.post("/api/summarize")
async def generate_summary(request: SummarizeRequest) -> SummaryResponse

@app.get("/api/summarize/progress/{task_id}")
async def get_summary_progress(task_id: str) -> ProgressResponse
```

SummarizationService Methods:
- async generate_summary(start_date, end_date, summary_type) -> SummaryResult
- validate_date_range(start_date, end_date) -> bool
- get_progress_updates() -> AsyncGenerator[ProgressUpdate, None]

Key Features:
- Async task processing with progress tracking
- Integration with existing LLM providers (Bedrock, Google GenAI)
- Error handling and recovery mechanisms
- Results formatting and display
- Configuration validation

Include comprehensive error handling, progress tracking, and integration tests. Ensure backward compatibility with existing summarization system. Write clean, maintainable code with proper documentation.
```

---

## **Prompt 11: Summarization Web Interface**

```
Develop the summarization interface with minimalistic, clean, premium, aesthetic, macos-like design. Create an intuitive form for date selection, progress visualization, and professional results display.

Requirements:
1. Create summarization form with clean, professional layout
2. Implement date range selection with validation
3. Add summary type selection (weekly/monthly)
4. Include progress visualization during processing
5. Display results with proper formatting
6. Add export functionality for summaries
7. Implement error handling with user feedback

Interface Features:
- Date range picker with validation
- Summary type selection (radio buttons or dropdown)
- Progress bar with status messages
- Results display with markdown formatting
- Export options (copy, download)
- Clear error messages and recovery suggestions

HTML Structure:
```html
<section class="summarization-section">
    <h3 class="section-title">Generate Summary</h3>
    
    <form id="summary-form" class="summary-form">
        <div class="form-group">
            <label for="start-date" class="form-label">Start Date</label>
            <input type="date" id="start-date" class="form-input" required>
        </div>
        
        <div class="form-group">
            <label for="end-date" class="form-label">End Date</label>
            <input type="date" id="end-date" class="form-input" required>
        </div>
        
        <div class="form-group">
            <label class="form-label">Summary Type</label>
            <div class="radio-group">
                <label class="radio-label">
                    <input type="radio" name="summary-type" value="weekly" checked>
                    <span class="radio-text">Weekly</span>
                </label>
                <label class="radio-label">
                    <input type="radio" name="summary-type" value="monthly">
                    <span class="radio-text">Monthly</span>
                </label>
            </div>
        </div>
        
        <button type="submit" class="primary-btn">Generate Summary</button>
    </form>
    
    <div id="progress-container" class="progress-container" style="display: none;">
        <div class="progress-bar">
            <div id="progress-fill" class="progress-fill"></div>
        </div>
        <div id="progress-text" class="progress-text">Initializing...</div>
    </div>
    
    <div id="summary-result" class="summary-result" style="display: none;">
        <div class="result-header">
            <h4 class="result-title">Summary Results</h4>
            <div class="result-actions">
                <button id="copy-btn" class="secondary-btn">Copy</button>
                <button id="download-btn" class="secondary-btn">Download</button>
            </div>
        </div>
        <div id="result-content" class="result-content">
            <!-- Summary content -->
        </div>
    </div>
</section>
```

JavaScript Features:
- Form validation with real-time feedback
- Progress tracking with WebSocket or polling
- Results formatting with markdown support
- Copy to clipboard functionality
- Download as text/markdown file
- Error handling with user-friendly messages

Design Requirements:
- Minimalistic, clean form design
- Premium, professional appearance
- macOS-like aesthetic with subtle styling
- Clear visual hierarchy and spacing
- Smooth progress animations
- Responsive layout for mobile devices

Include comprehensive JavaScript functionality with proper form validation, progress tracking, and error handling. Ensure smooth user experience with clear feedback for all operations.
```

---

## **Prompt 12: Settings Management System**

```
Implement comprehensive settings management that integrates with the existing config system while providing web-based configuration options. Create a robust system for managing application settings with validation and persistence.

Requirements:
1. Create SettingsService that integrates with existing ConfigManager
2. Implement database storage for web-specific settings
3. Add path validation and directory checking
4. Create API endpoints for settings management
5. Include configuration import/export functionality
6. Add real-time validation and error handling
7. Maintain compatibility with existing config.yaml

Integration Points:
- Use existing ConfigManager from config_manager.py
- Support existing configuration structure
- Maintain config.yaml compatibility
- Add web-specific settings to database
- Validate file system paths and permissions

API Endpoints:
```python
@app.get("/api/settings")
async def get_settings() -> SettingsResponse

@app.put("/api/settings")
async def update_settings(request: UpdateSettingsRequest) -> SettingsResponse

@app.post("/api/settings/validate-path")
async def validate_path(request: ValidatePathRequest) -> ValidationResponse
```

Key Features:
- Integration with existing config system
- Real-time path validation
- Settings persistence in database
- Configuration backup and restore
- Error handling with recovery suggestions

Include comprehensive error handling, validation logic, and integration tests. Ensure backward compatibility with existing configuration system. Write clean, maintainable code with proper documentation.
```

---

## **Prompt 13: Settings Web Interface**

```
Create the settings interface with minimalistic, clean, premium, aesthetic, macos-like design. Develop a user-friendly configuration panel with real-time validation and clear feedback.

Requirements:
1. Create settings form with clean, professional layout
2. Implement real-time path validation with visual feedback
3. Add configuration sections for different settings groups
4. Include import/export functionality for settings
5. Add reset to defaults option
6. Implement responsive design for different screen sizes
7. Include accessibility features and proper form handling

Interface Features:
- Organized settings sections (Paths, Preferences, Advanced)
- Real-time validation with success/error indicators
- Path browser/selector for directory settings
- Import/export configuration options
- Reset to defaults with confirmation
- Clear help text and tooltips

HTML Structure:
```html
<div class="settings-container">
    <header class="settings-header">
        <h2 class="settings-title">Settings</h2>
        <div class="settings-actions">
            <button id="import-btn" class="secondary-btn">Import</button>
            <button id="export-btn" class="secondary-btn">Export</button>
            <button id="reset-btn" class="secondary-btn">Reset</button>
        </div>
    </header>
    
    <form id="settings-form" class="settings-form">
        <section class="settings-section">
            <h3 class="section-title">File Paths</h3>
            
            <div class="form-group">
                <label for="base-path" class="form-label">
                    Worklog Storage Directory
                    <span class="help-text">Where your journal files are stored</span>
                </label>
                <div class="path-input-group">
                    <input type="text" id="base-path" class="form-input path-input" required>
                    <button type="button" id="browse-base-path" class="browse-btn">Browse</button>
                </div>
                <div id="base-path-validation" class="validation-message"></div>
            </div>
            
            <div class="form-group">
                <label for="output-path" class="form-label">
                    Summary Output Directory
                    <span class="help-text">Where generated summaries are saved</span>
                </label>
                <div class="path-input-group">
                    <input type="text" id="output-path" class="form-input path-input" required>
                    <button type="button" id="browse-output-path" class="browse-btn">Browse</button>
                </div>
                <div id="output-path-validation" class="validation-message"></div>
            </div>
        </section>
        
        <section class="settings-section">
            <h3 class="section-title">Preferences</h3>
            
            <div class="form-group">
                <label for="auto-save-interval" class="form-label">
                    Auto-save Interval (seconds)
                    <span class="help-text">How often to automatically save entries</span>
                </label>
                <input type="number" id="auto-save-interval" class="form-input" min="10" max="300" required>
            </div>
        </section>
        
        <div class="form-actions">
            <button type="submit" class="primary-btn">Save Settings</button>
            <button type="button" id="cancel-btn" class="secondary-btn">Cancel</button>
        </div>
    </form>
</div>
```

JavaScript Features:
- Real-time path validation with visual feedback
- Directory browser integration (where possible)
- Form validation with error handling
- Settings import/export functionality
- Reset confirmation dialogs
- Auto-save of settings changes

Design Requirements:
- Minimalistic, clean settings interface
- Premium, professional appearance
- macOS-like aesthetic with subtle styling
- Clear visual hierarchy and grouping
- Smooth transitions and animations
- Responsive layout for mobile devices

Include comprehensive JavaScript functionality with proper form handling, validation, and error management. Ensure smooth user experience with clear feedback for all operations.
```

---

## **Prompt 14: Auto-Save and Real-Time Features**

```
Implement auto-save functionality and real-time features for the journal entry editor. Create a robust system that prevents data loss while providing smooth user experience with clear feedback.

Requirements:
1. Implement auto-save with configurable intervals
2. Add real-time word count calculation
3. Create save status indicators with timestamps
4. Add conflict detection and resolution
5. Implement debounced saving to prevent excessive API calls
6. Add offline capability with local storage backup
7. Include error handling and recovery mechanisms

Auto-Save Features:
- Configurable save intervals (default 30 seconds)
- Debounced saving (wait for pause in typing)
- Visual indicators for save status
- Conflict detection for concurrent edits
- Local storage backup for offline scenarios
- Recovery from failed saves

JavaScript Implementation:
```javascript
class AutoSaveManager {
    constructor(entryDate, saveInterval = 30000) {
        this.entryDate = entryDate;
        this.saveInterval = saveInterval;
        this.saveTimeout = null;
        this.lastSavedContent = '';
        this.isOnline = navigator.onLine;
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Content change detection
        // Online/offline status
        // Window beforeunload protection
    }
    
    debouncedSave(content) {
        // Implement debounced saving logic
    }
    
    async saveEntry(content) {
        // API call with error handling
    }
    
    handleSaveError(error) {
        // Error recovery and user notification
    }
    
    updateSaveStatus(status, timestamp) {
        // Update UI with save status
    }
}
```

Real-Time Features:
- Word count updates on every keystroke
- Character count and reading time estimation
- Save status with "last saved" timestamps
- Network status indicators
- Typing indicators (for future multi-user support)

Error Handling:
- Network connectivity issues
- Server errors during save
- Concurrent edit conflicts
- Browser storage limitations
- Recovery from partial saves

Design Requirements:
- Subtle, non-intrusive status indicators
- Clear error messages with recovery options
- Smooth animations for status changes
- Accessible status announcements
- Mobile-friendly touch interactions

Include comprehensive error handling, offline support, and user feedback mechanisms. Ensure data integrity and provide clear recovery options for all failure scenarios.
```

---

## **Prompt 15: Cross-Platform Packaging and Deployment**

```
Implement cross-platform packaging using PyInstaller to create standalone executables for Windows, macOS, and Linux. Create a complete deployment solution that requires no Python installation.

Requirements:
1. Create PyInstaller configuration for each platform
2. Add build scripts for automated packaging
3. Include all necessary dependencies and assets
4. Create installer packages for each platform
5. Add application icons and metadata
6. Implement auto-update mechanism (optional)
7. Create distribution and installation documentation

PyInstaller Configuration:
```python
# build_config.py
import PyInstaller.__main__
import sys
import os
from pathlib import Path

def build_application():
    """Build standalone executable for current platform."""
    
    # Common options
    options = [
        '--name=DailyWorkJournal',
        '--onefile',
        '--windowed',
        '--add-data=web_app/templates:web_app/templates',
        '--add-data=web_app/static:web_app/static',
        '--hidden-import=uvicorn',
        '--hidden-import=fastapi',
        '--hidden-import=sqlalchemy',
        'web_app/main.py'
    ]
    
    # Platform-specific options
    if sys.platform == 'win32':
        options.extend([
            '--icon=assets/icon.ico',
            '--version-file=version_info.txt'
        ])
    elif sys.platform == 'darwin':
        options.extend([
            '--icon=assets/icon.icns',
            '--osx-bundle-identifier=com.workjournal.app'
        ])
    else:  # Linux
        options.extend([
            '--icon=assets/icon.png'
        ])
    
    PyInstaller.__main__.run(options)
```

Build Scripts:
- Cross-platform build automation
- Dependency verification
- Asset bundling and optimization
- Code signing (for macOS/Windows)
- Package creation and testing

Distribution Features:
- Standalone executables requiring no Python
- Bundled web server and database
- Local-only operation (no external dependencies)
- Automatic port selection and browser launching
- Clean uninstallation support

Platform-Specific Requirements:
- Windows: MSI installer with proper registry entries
- macOS: DMG package with drag-to-Applications
- Linux: AppImage or DEB/RPM packages
- All platforms: Desktop shortcuts and file associations

Testing Strategy:
- Automated build testing on each platform
- Installation and uninstallation testing
- Functionality verification in packaged form
- Performance testing of bundled application
- Security scanning of executables

Include comprehensive build documentation, troubleshooting