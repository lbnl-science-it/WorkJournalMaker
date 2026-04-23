# ABOUTME: Central dependency functions for FastAPI dependency injection.
# ABOUTME: Provides get_db_manager as the single override point for test DB isolation.

"""
FastAPI Dependency Functions

Provides dependency functions that endpoints use via Depends() to obtain
shared resources. Tests override these via app.dependency_overrides to
inject temporary instances.
"""

from fastapi import Request

from web.database import DatabaseManager


def get_db_manager(request: Request) -> DatabaseManager:
    """Dependency to get DatabaseManager from app state."""
    return request.app.state.db_manager
