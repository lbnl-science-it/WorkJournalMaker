"""
Main FastAPI Application for Work Journal Maker Web Interface

This module implements the core FastAPI application with comprehensive
middleware, error handling, and integration with existing configuration
and logging infrastructure.
"""

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import time
import traceback
import json
from pathlib import Path
from typing import Dict, Any, Optional

from config_manager import ConfigManager, AppConfig
from logger import LogConfig, JournalSummarizerLogger, ErrorCategory
from web.database import DatabaseManager, db_manager
from web.api import health, entries, sync, calendar, summarization, settings
from web.middleware import LoggingMiddleware, ErrorHandlingMiddleware
from web.services.entry_manager import EntryManager
from web.services.calendar_service import CalendarService
from web.services.web_summarizer import WebSummarizationService
from web.services.sync_service import DatabaseSyncService
from web.services.scheduler import SyncScheduler
from web.services.settings_service import SettingsService
from web.services.work_week_service import WorkWeekService


def create_logger_with_config(log_config: LogConfig) -> JournalSummarizerLogger:
    """Create logger instance with the provided configuration."""
    return JournalSummarizerLogger(log_config)


class WorkJournalWebApp:
    """Main web application class with integrated lifecycle management."""
    
    def __init__(self):
        self.config: Optional[AppConfig] = None
        self.logger: Optional[JournalSummarizerLogger] = None
        #self.db_manager: Optional[DatabaseManager] = None
        self.db_manager: DatabaseManager=db_manager
        self.work_week_service: Optional[WorkWeekService] = None
        self.entry_manager: Optional[EntryManager] = None
        self.calendar_service: Optional[CalendarService] = None
        self.settings_service: Optional[SettingsService] = None
        self.summarization_service: Optional[WebSummarizationService] = None
        self.sync_service: Optional['DatabaseSyncService'] = None
        self.scheduler: Optional[SyncScheduler] = None
        
    async def startup(self):
        """Application startup sequence."""
        try:
            # Initialize configuration
            config_manager = ConfigManager()
            self.config = config_manager.get_config()
            
            # Initialize logging
            self.logger = create_logger_with_config(self.config.logging)
            self.logger.logger.info("Starting Work Journal Web Application...")
            
            # Initialize database
            await self.db_manager.initialize()
            self.logger.logger.info("Database initialized successfully")

            
            # Initialize WorkWeekService for proper directory organization
            self.work_week_service = WorkWeekService(self.config, self.logger, self.db_manager)
            self.logger.logger.info("WorkWeekService initialized successfully")
            
            # Initialize EntryManager service with WorkWeekService dependency
            self.entry_manager = EntryManager(self.config, self.logger, self.db_manager, self.work_week_service)
            self.logger.logger.info("EntryManager service initialized successfully with work week integration")
            
            # Initialize CalendarService
            self.calendar_service = CalendarService(self.config, self.logger, self.db_manager)
            self.logger.logger.info("CalendarService initialized successfully")

            # Initialize SettingsService
            self.settings_service = SettingsService(self.config, self.logger, self.db_manager)
            self.logger.logger.info("SettingsService initialized successfully")

            # Initialize DatabaseSyncService
            self.sync_service = DatabaseSyncService(self.config, self.logger, self.db_manager)
            self.logger.logger.info("DatabaseSyncService initialized successfully")
            
            # Initialize WebSummarizationService
            self.summarization_service = WebSummarizationService(self.config, self.logger, self.db_manager)
            self.logger.logger.info("WebSummarizationService initialized successfully")
            
            # Set up WebSocket connection manager for real-time updates
            from web.api.summarization import connection_manager
            self.summarization_service.set_connection_manager(connection_manager)
            self.logger.logger.info("WebSocket connection manager configured for summarization service")
            
            # Initialize and start sync scheduler
            self.scheduler = SyncScheduler(self.config, self.logger, self.db_manager)
            await self.scheduler.start()
            self.logger.logger.info("Sync scheduler started successfully")
            
            # Log startup completion
            self.logger.logger.info("Web application startup completed successfully")
            
        except Exception as e:
            if self.logger:
                self.logger.log_error_with_category(
                    ErrorCategory.CONFIGURATION_ERROR,
                    f"Failed to start web application: {str(e)}",
                    exception=e
                )
            raise
    
    async def shutdown(self):
        """Application shutdown sequence."""
        if self.logger:
            self.logger.logger.info("Shutting down Work Journal Web Application...")
            
        # Stop sync scheduler
        if self.scheduler:
            await self.scheduler.stop()
            self.logger.logger.info("Sync scheduler stopped")
            
        # Close database connections
        if self.db_manager and self.db_manager.engine:
            await self.db_manager.engine.dispose()
            
        if self.logger:
            self.logger.logger.info("Web application shutdown complete")


# Create application instance
web_app = WorkJournalWebApp()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    await web_app.startup()
    app.state.config = web_app.config
    app.state.logger = web_app.logger
    app.state.db_manager = web_app.db_manager
    app.state.work_week_service = web_app.work_week_service
    app.state.entry_manager = web_app.entry_manager
    app.state.calendar_service = web_app.calendar_service
    app.state.settings_service = web_app.settings_service
    app.state.sync_service = web_app.sync_service
    app.state.summarization_service = web_app.summarization_service
    app.state.scheduler = web_app.scheduler
    
    yield
    
    # Shutdown
    await web_app.shutdown()


# Create FastAPI application
app = FastAPI(
    title="Work Journal Maker",
    description="Web interface for the Work Journal Summarizer",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "*.localhost", "testserver"]
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Include API routers
app.include_router(health.router)
app.include_router(entries.router)
app.include_router(sync.router)
app.include_router(calendar.router)
app.include_router(summarization.router)
app.include_router(settings.router)

# Static files and templates
static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/")
async def dashboard(request: Request):
    """Dashboard - main entry point for the web interface."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/entry/{entry_date}")
async def entry_editor(request: Request, entry_date: str):
    """Entry editor interface for creating and editing journal entries."""
    # Validate date format (basic validation)
    try:
        from datetime import datetime
        datetime.strptime(entry_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    return templates.TemplateResponse("entry_editor.html", {
        "request": request,
        "entry_date": entry_date
    })


@app.get("/calendar")
async def calendar_view(request: Request):
    """Calendar view interface for browsing journal entries."""
    return templates.TemplateResponse("calendar.html", {"request": request})


@app.get("/summarize")
async def summarization_page(request: Request):
    """Summarization interface for generating journal summaries."""
    return templates.TemplateResponse("summarization.html", {"request": request})


@app.get("/settings")
async def settings_page(request: Request):
    """Settings management interface."""
    return templates.TemplateResponse("settings.html", {"request": request})


@app.get("/api")
async def api_root():
    """API root endpoint with basic application information."""
    return {
        "service": "Work Journal Maker Web Interface",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/test")
async def test_page(request: Request):
    """Test page for base templates and styling."""
    return templates.TemplateResponse("test.html", {"request": request})


@app.websocket("/ws")
async def general_websocket_endpoint(websocket: WebSocket):
    """General WebSocket endpoint for system-wide updates."""
    await websocket.accept()
    try:
        # Send initial connection status
        await websocket.send_text(json.dumps({
            "type": "connection_status",
            "status": "connected",
            "message": "WebSocket connection established",
            "service": "general"
        }))
        
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back for connection testing
            await websocket.send_text(json.dumps({
                "type": "connection_status", 
                "status": "connected",
                "message": "WebSocket connection established"
            }))
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)