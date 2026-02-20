# ABOUTME: REST API endpoints for application health checks and system metrics.
# ABOUTME: Reports service status, database connectivity, and configuration validity.
"""
Health Check API Endpoints

This module provides comprehensive health check endpoints for monitoring
the web application status, configuration, and system metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pathlib import Path
import os
from datetime import datetime

from config_manager import AppConfig
from logger import JournalSummarizerLogger
from web.database import DatabaseManager
from web.models.responses import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health_check(request: Request):
    """Comprehensive health check endpoint."""
    config: AppConfig = request.app.state.config
    logger: JournalSummarizerLogger = request.app.state.logger
    db_manager: DatabaseManager = request.app.state.db_manager
    
    logger.logger.debug("Health check requested")
    
    # Check database health
    db_health = await db_manager.health_check()
    
    # Check file system access
    base_path = Path(config.processing.base_path).expanduser()
    fs_accessible = base_path.exists() and os.access(base_path, os.R_OK | os.W_OK)
    
    health_status = HealthResponse(
        status="healthy" if db_health["status"] == "healthy" and fs_accessible else "degraded",
        service="Work Journal Maker Web",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        components={
            "database": db_health,
            "filesystem": {
                "status": "healthy" if fs_accessible else "unhealthy",
                "base_path": str(base_path),
                "accessible": fs_accessible
            },
            "configuration": {
                "status": "healthy" if config else "unhealthy",
                "llm_provider": config.llm.provider if config else None
            }
        }
    )
    
    return health_status


@router.get("/config")
async def config_status(request: Request):
    """Detailed configuration status endpoint."""
    config: AppConfig = request.app.state.config
    
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not loaded")
    
    return {
        "llm": {
            "provider": config.llm.provider,
            "bedrock_region": config.bedrock.region,
            "bedrock_model": config.bedrock.model_id
        },
        "processing": {
            "base_path": config.processing.base_path,
            "output_path": config.processing.output_path,
            "max_file_size_mb": config.processing.max_file_size_mb
        },
        "logging": {
            "level": config.logging.level.value,
            "file_output": config.logging.file_output
        }
    }


@router.get("/metrics")
async def system_metrics(request: Request):
    """System metrics endpoint."""
    db_manager: DatabaseManager = request.app.state.db_manager
    
    # Get database stats
    db_stats = await db_manager.health_check()
    
    return {
        "database": {
            "entry_count": db_stats.get("entry_count", 0),
            "status": db_stats.get("status", "unknown")
        },
        "uptime": datetime.utcnow().isoformat()
    }