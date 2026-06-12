# ABOUTME: Request/response middleware for logging, error handling, and CSRF.
# ABOUTME: Provides cross-cutting concerns for all API and page requests.
"""
Custom Middleware for Work Journal Maker Web Interface

This module provides custom middleware for request/response logging,
error handling, and other cross-cutting concerns.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import traceback
from typing import Callable
from logger import JournalSummarizerLogger, ErrorCategory


# Paths exempt from CSRF header requirement (pre-auth endpoints)
CSRF_EXEMPT_PATHS = frozenset({
    "/api/auth/login",
    "/api/auth/refresh",
})

# HTTP methods that never modify state
CSRF_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class CSRFMiddleware(BaseHTTPMiddleware):
    """Reject state-changing requests that lack the X-Requested-With header.

    Cross-origin requests with custom headers trigger a CORS preflight, so
    requiring this header prevents cross-site form submissions and simple
    cross-origin fetches from mutating data.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if (
            request.method not in CSRF_SAFE_METHODS
            and request.url.path not in CSRF_EXEMPT_PATHS
        ):
            if not request.headers.get("x-requested-with"):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF validation failed: missing X-Requested-With header"},
                )
        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get logger from app state
        logger: JournalSummarizerLogger = getattr(request.app.state, 'logger', None)
        
        if logger:
            logger.logger.debug(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        if logger:
            logger.logger.debug(
                f"Response: {response.status_code} for {request.method} {request.url} "
                f"in {process_time:.4f}s"
            )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Don't catch HTTPException - let FastAPI handle it properly
            from fastapi import HTTPException
            if isinstance(e, HTTPException):
                raise
            
            # Get logger from app state
            logger: JournalSummarizerLogger = getattr(request.app.state, 'logger', None)
            
            if logger:
                logger.log_error_with_category(
                    ErrorCategory.PROCESSING_ERROR,
                    f"Unhandled exception in {request.method} {request.url}: {str(e)}",
                    exception=e
                )
                logger.logger.debug(f"Exception traceback: {traceback.format_exc()}")
            
            # Return JSON error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "request_id": getattr(request.state, 'request_id', None)
                }
            )