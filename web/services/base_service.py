"""
Base Service Class

This module provides a base service class with common functionality
for all business logic services in the web interface.
"""

import sys
from pathlib import Path
from typing import Optional

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from config_manager import AppConfig
from logger import JournalSummarizerLogger
from web.database import DatabaseManager


class BaseService:
    """
    Base service class providing common functionality for all services.
    
    This class provides standardized initialization and access to core
    components like configuration, logging, and database management.
    """
    
    def __init__(self, config: AppConfig, logger: JournalSummarizerLogger, 
                 db_manager: DatabaseManager):
        """
        Initialize base service with core dependencies.
        
        Args:
            config: Application configuration
            logger: Logger instance
            db_manager: Database manager instance
        """
        self.config = config
        self.logger = logger
        self.db_manager = db_manager
    
    def _log_operation_start(self, operation: str, **kwargs) -> None:
        """Log the start of an operation with context."""
        context = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.logger.debug(f"Starting {operation}" + (f" ({context})" if context else ""))
    
    def _log_operation_success(self, operation: str, **kwargs) -> None:
        """Log successful completion of an operation."""
        context = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.logger.debug(f"Completed {operation}" + (f" ({context})" if context else ""))
    
    def _log_operation_error(self, operation: str, error: Exception, **kwargs) -> None:
        """Log operation error with context."""
        context = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.logger.error(
            f"Failed {operation}: {str(error)}" + (f" ({context})" if context else "")
        )