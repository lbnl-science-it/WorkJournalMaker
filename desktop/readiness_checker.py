# ABOUTME: Server readiness checker component with advanced health checking
# ABOUTME: Provides HTTP/TCP health checks with configurable retry logic and backoff strategies

import time
import socket
import random
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException, ConnectTimeout, HTTPError, Timeout


class CheckType(Enum):
    """Enumeration of supported health check types."""
    HTTP = "http"
    TCP = "tcp"


@dataclass
class HealthCheckResult:
    """Result of a health check operation.
    
    Attributes:
        success: Whether the health check passed
        status_code: HTTP status code (None for TCP checks)
        response_time: Time taken for the check in seconds
        attempt_count: Number of attempts made
        error_message: Error message if check failed
        check_type: Type of health check performed
        url: URL or address that was checked
    """
    success: bool
    status_code: Optional[int]
    response_time: float
    attempt_count: int
    error_message: Optional[str]
    check_type: CheckType
    url: str


class ReadinessChecker:
    """Advanced server readiness checker with configurable retry logic.
    
    Provides HTTP and TCP health checks with support for:
    - Configurable timeout and retry settings
    - Exponential backoff with jitter
    - Custom HTTP headers and status codes
    - Detailed health check reporting
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        retry_interval: float = 0.5,
        max_retries: Optional[int] = None,
        backoff_factor: float = 1.0,
        jitter_max: float = 0.1,
        expected_status_codes: Optional[List[int]] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> None:
        """Initialize the ReadinessChecker.
        
        Args:
            timeout: Maximum time to wait for readiness in seconds
            retry_interval: Base interval between retries in seconds
            max_retries: Maximum number of retries (calculated from timeout if None)
            backoff_factor: Multiplier for exponential backoff (1.0 = no backoff)
            jitter_max: Maximum jitter to add to retry intervals
            expected_status_codes: List of HTTP status codes considered successful
            custom_headers: Custom headers to include in HTTP requests
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        if retry_interval <= 0:
            raise ValueError("Retry interval must be positive")
        if max_retries is not None and max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        if backoff_factor <= 0:
            raise ValueError("Backoff factor must be positive")
        
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.max_retries = max_retries or int(timeout / retry_interval)
        self.backoff_factor = backoff_factor
        self.jitter_max = jitter_max
        self.expected_status_codes = expected_status_codes or [200]
        self.custom_headers = custom_headers or {}
    
    def check_http_health(self, url: str) -> HealthCheckResult:
        """Perform a single HTTP health check.
        
        Args:
            url: URL to check
            
        Returns:
            HealthCheckResult containing the check results
        """
        start_time = time.time()
        
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers=self.custom_headers
            )
            
            # Use response.elapsed if available, otherwise calculate
            if hasattr(response, 'elapsed') and response.elapsed:
                response_time = response.elapsed.total_seconds()
            else:
                response_time = time.time() - start_time
            
            if response.status_code in self.expected_status_codes:
                return HealthCheckResult(
                    success=True,
                    status_code=response.status_code,
                    response_time=response_time,
                    attempt_count=1,
                    error_message=None,
                    check_type=CheckType.HTTP,
                    url=url
                )
            else:
                return HealthCheckResult(
                    success=False,
                    status_code=response.status_code,
                    response_time=response_time,
                    attempt_count=1,
                    error_message=f"Unexpected status code: {response.status_code} (expected: {self.expected_status_codes})",
                    check_type=CheckType.HTTP,
                    url=url
                )
                
        except RequestException as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                success=False,
                status_code=None,
                response_time=response_time,
                attempt_count=1,
                error_message=str(e),
                check_type=CheckType.HTTP,
                url=url
            )
    
    def check_tcp_health(self, host: str, port: int) -> HealthCheckResult:
        """Perform a single TCP health check.
        
        Args:
            host: Hostname to check
            port: Port number to check
            
        Returns:
            HealthCheckResult containing the check results
        """
        start_time = time.time()
        url = f"{host}:{port}"
        
        # Validate inputs
        if not host or not host.strip():
            return HealthCheckResult(
                success=False,
                status_code=None,
                response_time=0.0,
                attempt_count=1,
                error_message="Invalid host: empty or None",
                check_type=CheckType.TCP,
                url=url
            )
        
        if port <= 0 or port > 65535:
            return HealthCheckResult(
                success=False,
                status_code=None,
                response_time=0.0,
                attempt_count=1,
                error_message=f"Invalid port: {port} (must be 1-65535)",
                check_type=CheckType.TCP,
                url=url
            )
        
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((host, port))
            
            response_time = time.time() - start_time
            return HealthCheckResult(
                success=True,
                status_code=None,
                response_time=response_time,
                attempt_count=1,
                error_message=None,
                check_type=CheckType.TCP,
                url=url
            )
            
        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                success=False,
                status_code=None,
                response_time=response_time,
                attempt_count=1,
                error_message=str(e),
                check_type=CheckType.TCP,
                url=url
            )
        finally:
            if sock:
                sock.close()
    
    def wait_for_ready(self, url: str) -> HealthCheckResult:
        """Wait for a server to become ready using HTTP checks.
        
        Args:
            url: URL to check for readiness
            
        Returns:
            HealthCheckResult containing the final check results
        """
        # Validate URL format
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return HealthCheckResult(
                    success=False,
                    status_code=None,
                    response_time=0.0,
                    attempt_count=0,
                    error_message=f"Invalid URL format: {url}",
                    check_type=CheckType.HTTP,
                    url=url
                )
        except Exception as e:
            return HealthCheckResult(
                success=False,
                status_code=None,
                response_time=0.0,
                attempt_count=0,
                error_message=f"Invalid URL: {e}",
                check_type=CheckType.HTTP,
                url=url
            )
        
        start_time = time.time()
        attempt_count = 0
        last_result = None
        
        while attempt_count <= self.max_retries:
            attempt_count += 1
            result = self.check_http_health(url)
            result.attempt_count = attempt_count
            last_result = result
            
            if result.success:
                return result
            
            # Check if we've exceeded max retries first
            if attempt_count >= self.max_retries:
                result.error_message = f"Max retries exceeded ({self.max_retries} attempts)"
                return result
            
            # Check if we've exceeded timeout
            if time.time() - start_time >= self.timeout:
                result.error_message = f"Timeout exceeded after {self.timeout}s"
                return result
            
            # Calculate retry interval with backoff and jitter
            retry_delay = self._calculate_retry_delay(attempt_count - 1)
            time.sleep(retry_delay)
        
        # If we exit the loop without success, return the last result
        if last_result:
            if time.time() - start_time >= self.timeout:
                last_result.error_message = f"Timeout exceeded after {self.timeout}s"
            else:
                last_result.error_message = f"Max retries exceeded ({self.max_retries} attempts)"
            return last_result
        
        # Fallback result if no attempts were made
        return HealthCheckResult(
            success=False,
            status_code=None,
            response_time=time.time() - start_time,
            attempt_count=0,
            error_message="No attempts made",
            check_type=CheckType.HTTP,
            url=url
        )
    
    def wait_for_ready_tcp(self, host: str, port: int) -> HealthCheckResult:
        """Wait for a server to become ready using TCP checks.
        
        Args:
            host: Hostname to check
            port: Port number to check
            
        Returns:
            HealthCheckResult containing the final check results
        """
        start_time = time.time()
        attempt_count = 0
        last_result = None
        url = f"{host}:{port}"
        
        while attempt_count <= self.max_retries:
            attempt_count += 1
            result = self.check_tcp_health(host, port)
            result.attempt_count = attempt_count
            last_result = result
            
            if result.success:
                return result
            
            # Check if we've exceeded max retries first
            if attempt_count >= self.max_retries:
                result.error_message = f"Max retries exceeded ({self.max_retries} attempts)"
                return result
            
            # Check if we've exceeded timeout
            if time.time() - start_time >= self.timeout:
                result.error_message = f"Timeout exceeded after {self.timeout}s"
                return result
            
            # Calculate retry interval with backoff and jitter
            retry_delay = self._calculate_retry_delay(attempt_count - 1)
            time.sleep(retry_delay)
        
        # If we exit the loop without success, return the last result
        if last_result:
            if time.time() - start_time >= self.timeout:
                last_result.error_message = f"Timeout exceeded after {self.timeout}s"
            else:
                last_result.error_message = f"Max retries exceeded ({self.max_retries} attempts)"
            return last_result
        
        # Fallback result if no attempts were made
        return HealthCheckResult(
            success=False,
            status_code=None,
            response_time=time.time() - start_time,
            attempt_count=0,
            error_message="No attempts made",
            check_type=CheckType.TCP,
            url=url
        )
    
    def _calculate_retry_delay(self, attempt_number: int) -> float:
        """Calculate retry delay with exponential backoff and jitter.
        
        Args:
            attempt_number: Current attempt number (0-based)
            
        Returns:
            Delay in seconds before next retry
        """
        base_delay = self.retry_interval * (self.backoff_factor ** attempt_number)
        jitter = random.uniform(0, self.jitter_max)
        return base_delay + jitter
    
    def get_health_check_summary(self, result: HealthCheckResult) -> str:
        """Generate a human-readable summary of health check results.
        
        Args:
            result: HealthCheckResult to summarize
            
        Returns:
            Formatted summary string
        """
        status_icon = "✅" if result.success else "❌"
        status_text = "PASSED" if result.success else "FAILED"
        
        summary_lines = [
            f"{status_icon} Health check {status_text}",
            f"Type: {result.check_type.value.upper()}",
            f"URL: {result.url}",
            f"Response time: {result.response_time:.2f}s",
            f"Attempts: {result.attempt_count}"
        ]
        
        if result.status_code is not None:
            summary_lines.insert(3, f"Status: {result.status_code}")
        
        if result.error_message:
            summary_lines.append(f"Error: {result.error_message}")
        
        return "\n".join(summary_lines)
    
    @classmethod
    def configure_for_fast_checks(cls) -> 'ReadinessChecker':
        """Create a ReadinessChecker configured for fast local checks.
        
        Returns:
            ReadinessChecker instance optimized for fast checks
        """
        return cls(
            timeout=5.0,
            retry_interval=0.1,
            max_retries=50,
            backoff_factor=1.0,
            jitter_max=0.05
        )
    
    @classmethod
    def configure_for_slow_checks(cls) -> 'ReadinessChecker':
        """Create a ReadinessChecker configured for slow remote checks.
        
        Returns:
            ReadinessChecker instance optimized for slow checks
        """
        return cls(
            timeout=60.0,
            retry_interval=1.0,
            max_retries=60,
            backoff_factor=1.2,
            jitter_max=0.2
        )
    
    @classmethod
    def configure_for_production(cls) -> 'ReadinessChecker':
        """Create a ReadinessChecker configured for production environments.
        
        Returns:
            ReadinessChecker instance optimized for production
        """
        return cls(
            timeout=120.0,
            retry_interval=2.0,
            max_retries=60,
            backoff_factor=1.5,
            jitter_max=0.5,
            expected_status_codes=[200, 204],
            custom_headers={"User-Agent": "WorkJournalMaker-HealthChecker/1.0"}
        )