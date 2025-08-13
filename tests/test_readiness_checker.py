# ABOUTME: Comprehensive test suite for server readiness checker component
# ABOUTME: Tests HTTP health checks, retry logic, timeout scenarios, and error handling

import pytest
import time
import socket
from unittest.mock import patch, MagicMock, call
from typing import Dict, Any, Optional
import requests
from requests.exceptions import RequestException, ConnectTimeout, HTTPError, Timeout

# Import the module we'll be testing
from desktop.readiness_checker import ReadinessChecker, HealthCheckResult, CheckType


class TestReadinessCheckerInitialization:
    """Test cases for ReadinessChecker initialization."""
    
    def test_readiness_checker_default_initialization(self):
        """Test ReadinessChecker initializes with default values."""
        checker = ReadinessChecker()
        
        assert checker.timeout == 30.0
        assert checker.retry_interval == 0.5
        assert checker.max_retries == 60  # 30 seconds / 0.5 interval
        assert checker.backoff_factor == 1.0
        assert checker.jitter_max == 0.1
        assert checker.expected_status_codes == [200]
        assert checker.custom_headers == {}
    
    def test_readiness_checker_custom_initialization(self):
        """Test ReadinessChecker initializes with custom values."""
        checker = ReadinessChecker(
            timeout=60.0,
            retry_interval=1.0,
            max_retries=30,
            backoff_factor=1.5,
            jitter_max=0.2,
            expected_status_codes=[200, 204],
            custom_headers={"User-Agent": "HealthChecker/1.0"}
        )
        
        assert checker.timeout == 60.0
        assert checker.retry_interval == 1.0
        assert checker.max_retries == 30
        assert checker.backoff_factor == 1.5
        assert checker.jitter_max == 0.2
        assert checker.expected_status_codes == [200, 204]
        assert checker.custom_headers == {"User-Agent": "HealthChecker/1.0"}
    
    def test_readiness_checker_invalid_values(self):
        """Test ReadinessChecker validation of invalid values."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            ReadinessChecker(timeout=-1.0)
        
        with pytest.raises(ValueError, match="Retry interval must be positive"):
            ReadinessChecker(retry_interval=0.0)
        
        with pytest.raises(ValueError, match="Max retries must be non-negative"):
            ReadinessChecker(max_retries=-1)
        
        with pytest.raises(ValueError, match="Backoff factor must be positive"):
            ReadinessChecker(backoff_factor=0.0)


class TestHealthCheckResult:
    """Test cases for HealthCheckResult data structure."""
    
    def test_health_check_result_success(self):
        """Test HealthCheckResult for successful check."""
        result = HealthCheckResult(
            success=True,
            status_code=200,
            response_time=0.5,
            attempt_count=1,
            error_message=None,
            check_type=CheckType.HTTP,
            url="http://localhost:8080"
        )
        
        assert result.success is True
        assert result.status_code == 200
        assert result.response_time == 0.5
        assert result.attempt_count == 1
        assert result.error_message is None
        assert result.check_type == CheckType.HTTP
        assert result.url == "http://localhost:8080"
    
    def test_health_check_result_failure(self):
        """Test HealthCheckResult for failed check."""
        result = HealthCheckResult(
            success=False,
            status_code=None,
            response_time=1.0,
            attempt_count=5,
            error_message="Connection timeout",
            check_type=CheckType.HTTP,
            url="http://localhost:8080"
        )
        
        assert result.success is False
        assert result.status_code is None
        assert result.response_time == 1.0
        assert result.attempt_count == 5
        assert result.error_message == "Connection timeout"


class TestHTTPHealthChecks:
    """Test cases for HTTP health check functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = ReadinessChecker(timeout=5.0, retry_interval=0.1)
    
    @patch('desktop.readiness_checker.requests.get')
    def test_http_check_success(self, mock_get):
        """Test successful HTTP health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_get.return_value = mock_response
        
        result = self.checker.check_http_health("http://localhost:8080")
        
        assert result.success is True
        assert result.status_code == 200
        assert result.response_time == 0.5
        assert result.attempt_count == 1
        assert result.error_message is None
        assert result.check_type == CheckType.HTTP
        assert result.url == "http://localhost:8080"
        
        mock_get.assert_called_once_with(
            "http://localhost:8080",
            timeout=5.0,
            headers={}
        )
    
    @patch('desktop.readiness_checker.requests.get')
    def test_http_check_custom_headers(self, mock_get):
        """Test HTTP health check with custom headers."""
        checker = ReadinessChecker(
            custom_headers={"User-Agent": "Test", "Accept": "application/json"}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_get.return_value = mock_response
        
        result = checker.check_http_health("http://localhost:8080/health")
        
        assert result.success is True
        mock_get.assert_called_once_with(
            "http://localhost:8080/health",
            timeout=30.0,
            headers={"User-Agent": "Test", "Accept": "application/json"}
        )
    
    @patch('desktop.readiness_checker.requests.get')
    def test_http_check_wrong_status_code(self, mock_get):
        """Test HTTP health check with unexpected status code."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_get.return_value = mock_response
        
        result = self.checker.check_http_health("http://localhost:8080")
        
        assert result.success is False
        assert result.status_code == 500
        assert result.error_message == "Unexpected status code: 500 (expected: [200])"
    
    @patch('desktop.readiness_checker.requests.get')
    def test_http_check_connection_error(self, mock_get):
        """Test HTTP health check with connection error."""
        mock_get.side_effect = ConnectTimeout("Connection timeout")
        
        result = self.checker.check_http_health("http://localhost:8080")
        
        assert result.success is False
        assert result.status_code is None
        assert "Connection timeout" in result.error_message
        assert result.check_type == CheckType.HTTP
    
    @patch('desktop.readiness_checker.requests.get')
    def test_http_check_multiple_expected_status_codes(self, mock_get):
        """Test HTTP health check with multiple expected status codes."""
        checker = ReadinessChecker(expected_status_codes=[200, 204, 301])
        
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_get.return_value = mock_response
        
        result = checker.check_http_health("http://localhost:8080")
        
        assert result.success is True
        assert result.status_code == 204


class TestTCPHealthChecks:
    """Test cases for TCP socket health check functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = ReadinessChecker(timeout=2.0)
    
    @patch('desktop.readiness_checker.socket.socket')
    def test_tcp_check_success(self, mock_socket):
        """Test successful TCP health check."""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.connect.return_value = None
        
        result = self.checker.check_tcp_health("localhost", 8080)
        
        assert result.success is True
        assert result.status_code is None  # TCP checks don't have status codes
        assert result.error_message is None
        assert result.check_type == CheckType.TCP
        assert result.url == "localhost:8080"
        
        mock_sock.connect.assert_called_once_with(("localhost", 8080))
        mock_sock.close.assert_called_once()
    
    @patch('desktop.readiness_checker.socket.socket')
    def test_tcp_check_connection_refused(self, mock_socket):
        """Test TCP health check with connection refused."""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        
        result = self.checker.check_tcp_health("localhost", 8080)
        
        assert result.success is False
        assert "Connection refused" in result.error_message
        assert result.check_type == CheckType.TCP
        mock_sock.close.assert_called_once()
    
    @patch('desktop.readiness_checker.socket.socket')
    def test_tcp_check_timeout(self, mock_socket):
        """Test TCP health check with timeout."""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.connect.side_effect = socket.timeout("Socket timeout")
        
        result = self.checker.check_tcp_health("localhost", 8080)
        
        assert result.success is False
        assert "Socket timeout" in result.error_message
        mock_sock.close.assert_called_once()


class TestRetryLogic:
    """Test cases for retry logic and backoff strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = ReadinessChecker(
            timeout=2.0,
            retry_interval=0.1,
            max_retries=5,
            backoff_factor=1.5,
            jitter_max=0.05
        )
    
    @patch('desktop.readiness_checker.time.sleep')
    @patch('desktop.readiness_checker.requests.get')
    def test_retry_logic_eventual_success(self, mock_get, mock_sleep):
        """Test retry logic with eventual success."""
        # First 2 calls fail, 3rd succeeds
        mock_get.side_effect = [
            ConnectTimeout("Timeout 1"),
            ConnectTimeout("Timeout 2"),
            MagicMock(status_code=200, elapsed=MagicMock(total_seconds=lambda: 0.5))
        ]
        
        result = self.checker.wait_for_ready("http://localhost:8080")
        
        assert result.success is True
        assert result.attempt_count == 3
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between retries
    
    @patch('desktop.readiness_checker.time.sleep')
    @patch('desktop.readiness_checker.requests.get')
    def test_retry_logic_max_retries_exceeded(self, mock_get, mock_sleep):
        """Test retry logic when max retries exceeded."""
        mock_get.side_effect = ConnectTimeout("Persistent timeout")
        
        result = self.checker.wait_for_ready("http://localhost:8080")
        
        assert result.success is False
        assert result.attempt_count == 5  # max_retries = 5, so 5 attempts
        assert mock_get.call_count == 5
        assert mock_sleep.call_count == 4  # Sleep between retries (4 sleeps between 5 attempts)
        assert "Max retries exceeded" in result.error_message
    
    @patch('desktop.readiness_checker.time.sleep')
    @patch('desktop.readiness_checker.requests.get')
    def test_backoff_calculation(self, mock_get, mock_sleep):
        """Test exponential backoff calculation."""
        mock_get.side_effect = ConnectTimeout("Timeout")
        
        # Mock random to return consistent values for testing
        with patch('desktop.readiness_checker.random.uniform', return_value=0.02):
            result = self.checker.wait_for_ready("http://localhost:8080")
        
        # Check that sleep was called with increasing intervals (with jitter)
        # With max_retries=5, we get 5 attempts total, so 4 sleep calls between attempts
        expected_calls = []
        for i in range(4):  # 4 sleep calls (between 5 attempts)
            base_interval = 0.1 * (1.5 ** i)  # backoff_factor applied
            jittered_interval = base_interval + 0.02  # jitter added
            expected_calls.append(call(jittered_interval))
        
        mock_sleep.assert_has_calls(expected_calls)
    
    @patch('desktop.readiness_checker.time.time')
    @patch('desktop.readiness_checker.requests.get')
    def test_timeout_override_retries(self, mock_get, mock_time):
        """Test that timeout overrides max retries."""
        # Mock time to simulate timeout after 2 attempts
        # Start=0, after 1st attempt=0.5 (within timeout), timeout check=2.5 (exceeds timeout)
        mock_time.side_effect = [0, 0.5, 2.5, 2.5, 2.5, 2.5, 2.5]  # Start, after 1st, timeout checks
        mock_get.side_effect = ConnectTimeout("Timeout")
        
        result = self.checker.wait_for_ready("http://localhost:8080")
        
        assert result.success is False
        assert result.attempt_count == 1  # Only 1 attempt before timeout
        assert mock_get.call_count == 1
        assert "Timeout exceeded" in result.error_message


class TestWaitForReady:
    """Test cases for the main wait_for_ready method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = ReadinessChecker(timeout=1.0, retry_interval=0.1)
    
    @patch('desktop.readiness_checker.requests.get')
    def test_wait_for_ready_http_success(self, mock_get):
        """Test wait_for_ready with successful HTTP check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_get.return_value = mock_response
        
        result = self.checker.wait_for_ready("http://localhost:8080")
        
        assert result.success is True
        assert result.check_type == CheckType.HTTP
        assert result.url == "http://localhost:8080"
    
    def test_wait_for_ready_tcp_by_host_port(self):
        """Test wait_for_ready with TCP check using host and port."""
        with patch.object(self.checker, 'check_tcp_health') as mock_tcp:
            mock_tcp.return_value = HealthCheckResult(
                success=True,
                status_code=None,
                response_time=0.1,
                attempt_count=1,
                error_message=None,
                check_type=CheckType.TCP,
                url="localhost:8080"
            )
            
            result = self.checker.wait_for_ready_tcp("localhost", 8080)
            
            assert result.success is True
            assert result.check_type == CheckType.TCP
            mock_tcp.assert_called_once_with("localhost", 8080)
    
    def test_wait_for_ready_invalid_url(self):
        """Test wait_for_ready with invalid URL."""
        result = self.checker.wait_for_ready("invalid-url")
        
        assert result.success is False
        assert "Invalid URL" in result.error_message


class TestHealthCheckIntegration:
    """Test cases for integration scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = ReadinessChecker(timeout=2.0, retry_interval=0.1)
    
    @patch('desktop.readiness_checker.requests.get')
    def test_server_startup_simulation(self, mock_get):
        """Test realistic server startup scenario."""
        # Simulate server startup: connection refused, then 503, then 200
        mock_get.side_effect = [
            ConnectTimeout("Server not started"),
            MagicMock(status_code=503, elapsed=MagicMock(total_seconds=lambda: 0.1)),
            MagicMock(status_code=200, elapsed=MagicMock(total_seconds=lambda: 0.2))
        ]
        
        result = self.checker.wait_for_ready("http://localhost:8080/health")
        
        assert result.success is True
        assert result.attempt_count == 3
        assert mock_get.call_count == 3
    
    def test_get_health_check_summary(self):
        """Test health check summary generation."""
        result = HealthCheckResult(
            success=True,
            status_code=200,
            response_time=0.5,
            attempt_count=3,
            error_message=None,
            check_type=CheckType.HTTP,
            url="http://localhost:8080"
        )
        
        summary = self.checker.get_health_check_summary(result)
        
        assert "✅ Health check PASSED" in summary
        assert "URL: http://localhost:8080" in summary
        assert "Status: 200" in summary
        assert "Response time: 0.50s" in summary
        assert "Attempts: 3" in summary
    
    def test_get_health_check_summary_failure(self):
        """Test health check summary for failure."""
        result = HealthCheckResult(
            success=False,
            status_code=None,
            response_time=2.0,
            attempt_count=5,
            error_message="Connection timeout",
            check_type=CheckType.TCP,
            url="localhost:8080"
        )
        
        summary = self.checker.get_health_check_summary(result)
        
        assert "❌ Health check FAILED" in summary
        assert "URL: localhost:8080" in summary
        assert "Error: Connection timeout" in summary
        assert "Attempts: 5" in summary


class TestReadinessCheckerConfiguration:
    """Test cases for configuration and customization."""
    
    def test_configure_for_fast_checks(self):
        """Test configuration for fast local checks."""
        checker = ReadinessChecker.configure_for_fast_checks()
        
        assert checker.timeout == 5.0
        assert checker.retry_interval == 0.1
        assert checker.max_retries == 50
        assert checker.backoff_factor == 1.0
    
    def test_configure_for_slow_checks(self):
        """Test configuration for slow remote checks."""
        checker = ReadinessChecker.configure_for_slow_checks()
        
        assert checker.timeout == 60.0
        assert checker.retry_interval == 1.0
        assert checker.max_retries == 60
        assert checker.backoff_factor == 1.2
    
    def test_configure_for_production(self):
        """Test configuration for production environment."""
        checker = ReadinessChecker.configure_for_production()
        
        assert checker.timeout == 120.0
        assert checker.retry_interval == 2.0
        assert checker.backoff_factor == 1.5
        assert checker.expected_status_codes == [200, 204]


class TestErrorHandling:
    """Test cases for error handling and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = ReadinessChecker(timeout=1.0)
    
    @patch('desktop.readiness_checker.requests.get')
    def test_http_error_handling(self, mock_get):
        """Test handling of various HTTP errors."""
        mock_get.side_effect = HTTPError("HTTP 404 Error")
        
        result = self.checker.check_http_health("http://localhost:8080")
        
        assert result.success is False
        assert "HTTP 404 Error" in result.error_message
    
    @patch('desktop.readiness_checker.requests.get')
    def test_timeout_error_handling(self, mock_get):
        """Test handling of timeout errors."""
        mock_get.side_effect = Timeout("Request timeout")
        
        result = self.checker.check_http_health("http://localhost:8080")
        
        assert result.success is False
        assert "Request timeout" in result.error_message
    
    def test_invalid_port_handling(self):
        """Test handling of invalid port numbers."""
        result = self.checker.check_tcp_health("localhost", 70000)
        
        assert result.success is False
        assert "Invalid port" in result.error_message
    
    def test_invalid_host_handling(self):
        """Test handling of invalid hostnames."""
        result = self.checker.check_tcp_health("", 8080)
        
        assert result.success is False
        assert "Invalid host" in result.error_message