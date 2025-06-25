"""
Main FastAPI Application for Work Journal Maker Web Interface

This module implements the core FastAPI application with comprehensive
middleware, error handling, and integration with existing configuration
and logging infrastructure.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_manager import ConfigManager, AppConfig
from logger import LogConfig, JournalSummarizerLogger, ErrorCategory
from web.database import DatabaseManager, db_manager
from web.api import health
from web.middleware import LoggingMiddleware, ErrorHandlingMiddleware


def create_logger_with_config(log_config: LogConfig) -> JournalSummarizerLogger:
    """Create logger instance with the provided configuration."""
    return JournalSummarizerLogger(log_config)


class WorkJournalWebApp:
    """Main web application class with integrated lifecycle management."""
    
    def __init__(self):
        self.config: Optional[AppConfig] = None
        self.logger: Optional[JournalSummarizerLogger] = None
        self.db_manager: DatabaseManager = db_manager
        
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
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
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

# Static files and templates (will be created in later steps)
# app.mount("/static", StaticFiles(directory="web/static"), name="static")
# templates = Jinja2Templates(directory="web/templates")


@app.get("/")
async def root():
    """Root endpoint with basic application information."""
    return {
        "service": "Work Journal Maker Web Interface",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)