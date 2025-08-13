# ABOUTME: Comprehensive test suite for browser controller component
# ABOUTME: Tests cross-platform browser opening, URL validation, and error handling

import pytest
import platform
import webbrowser
from unittest.mock import patch, MagicMock
from desktop.browser_controller import BrowserController


class TestBrowserControllerInitialization:
    """Test cases for BrowserController initialization."""
    
    def test_browser_controller_initialization_default(self):
        """Test BrowserController initializes with default values."""
        controller = BrowserController()
        
        assert controller.preferred_browser is None
        assert controller.timeout == 5.0
        assert controller.retry_attempts == 3
    
    def test_browser_controller_initialization_custom(self):
        """Test BrowserController initializes with custom values."""
        controller = BrowserController(
            preferred_browser='chrome',
            timeout=10.0,
            retry_attempts=5
        )
        
        assert controller.preferred_browser == 'chrome'
        assert controller.timeout == 10.0
        assert controller.retry_attempts == 5
    
    def test_browser_controller_invalid_timeout(self):
        """Test BrowserController validation of timeout parameter."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            BrowserController(timeout=0)
        
        with pytest.raises(ValueError, match="Timeout must be positive"):
            BrowserController(timeout=-1)
    
    def test_browser_controller_invalid_retry_attempts(self):
        """Test BrowserController validation of retry_attempts parameter."""
        with pytest.raises(ValueError, match="Retry attempts must be positive"):
            BrowserController(retry_attempts=0)
        
        with pytest.raises(ValueError, match="Retry attempts must be positive"):
            BrowserController(retry_attempts=-1)


class TestBrowserControllerURLValidation:
    """Test cases for URL validation."""
    
    def test_valid_http_url(self):
        """Test validation of valid HTTP URLs."""
        controller = BrowserController()
        
        assert controller._validate_url("http://localhost:8000") is True
        assert controller._validate_url("http://example.com") is True
        assert controller._validate_url("http://192.168.1.1:3000") is True
    
    def test_valid_https_url(self):
        """Test validation of valid HTTPS URLs."""
        controller = BrowserController()
        
        assert controller._validate_url("https://localhost:8000") is True
        assert controller._validate_url("https://example.com") is True
        assert controller._validate_url("https://www.google.com") is True
    
    def test_invalid_url_schemes(self):
        """Test validation rejects invalid URL schemes."""
        controller = BrowserController()
        
        assert controller._validate_url("ftp://example.com") is False
        assert controller._validate_url("file:///etc/passwd") is False
        assert controller._validate_url("javascript:alert('xss')") is False
        assert controller._validate_url("data:text/html,<script>alert('xss')</script>") is False
    
    def test_malformed_urls(self):
        """Test validation rejects malformed URLs."""
        controller = BrowserController()
        
        assert controller._validate_url("not-a-url") is False
        assert controller._validate_url("http://") is False
        assert controller._validate_url("://example.com") is False
        assert controller._validate_url("") is False
        assert controller._validate_url(None) is False
    
    def test_url_with_special_characters(self):
        """Test validation of URLs with special characters."""
        controller = BrowserController()
        
        assert controller._validate_url("http://localhost:8000/path?query=value") is True
        assert controller._validate_url("https://example.com/path#fragment") is True
        assert controller._validate_url("http://example.com/path with spaces") is True


class TestBrowserControllerOpening:
    """Test cases for browser opening functionality."""
    
    @patch('webbrowser.open')
    def test_open_browser_success(self, mock_webbrowser_open):
        """Test successful browser opening."""
        mock_webbrowser_open.return_value = True
        
        controller = BrowserController()
        result = controller.open_browser("http://localhost:8000")
        
        assert result is True
        mock_webbrowser_open.assert_called_once_with(
            "http://localhost:8000",
            new=2,
            autoraise=True
        )
    
    @patch('webbrowser.open')
    def test_open_browser_with_preferred_browser(self, mock_webbrowser_open):
        """Test opening browser with preferred browser specified."""
        mock_webbrowser_open.return_value = True
        
        controller = BrowserController(preferred_browser='chrome')
        
        with patch('webbrowser.get') as mock_get:
            mock_browser = MagicMock()
            mock_browser.open.return_value = True
            mock_get.return_value = mock_browser
            
            result = controller.open_browser("http://localhost:8000")
            
            assert result is True
            mock_get.assert_called_once_with('chrome')
            mock_browser.open.assert_called_once_with(
                "http://localhost:8000",
                new=2,
                autoraise=True
            )
    
    @patch('webbrowser.open')
    def test_open_browser_invalid_url(self, mock_webbrowser_open):
        """Test opening browser with invalid URL."""
        controller = BrowserController()
        
        with pytest.raises(ValueError, match="Invalid URL"):
            controller.open_browser("not-a-url")
        
        mock_webbrowser_open.assert_not_called()
    
    @patch('webbrowser.open')
    def test_open_browser_webbrowser_failure(self, mock_webbrowser_open):
        """Test handling when webbrowser.open fails."""
        mock_webbrowser_open.return_value = False
        
        controller = BrowserController()
        result = controller.open_browser("http://localhost:8000")
        
        assert result is False
        # Should retry 3 times (default retry_attempts)
        assert mock_webbrowser_open.call_count == 3
    
    @patch('webbrowser.open')
    def test_open_browser_webbrowser_exception(self, mock_webbrowser_open):
        """Test handling when webbrowser.open raises exception."""
        mock_webbrowser_open.side_effect = webbrowser.Error("No web browser found")
        
        controller = BrowserController()
        result = controller.open_browser("http://localhost:8000")
        
        assert result is False
        mock_webbrowser_open.assert_called_once()
    
    @patch('webbrowser.get')
    def test_open_browser_preferred_browser_not_found(self, mock_get):
        """Test handling when preferred browser is not found."""
        mock_get.side_effect = webbrowser.Error("Browser not found")
        
        controller = BrowserController(preferred_browser='nonexistent-browser')
        
        with patch('webbrowser.open') as mock_open:
            mock_open.return_value = True
            result = controller.open_browser("http://localhost:8000")
            
            assert result is True
            # Should fall back to default browser
            mock_open.assert_called_once()


class TestBrowserControllerRetryLogic:
    """Test cases for retry logic."""
    
    @patch('webbrowser.open')
    def test_retry_on_failure(self, mock_webbrowser_open):
        """Test retry logic when browser opening fails."""
        # Fail twice, succeed on third attempt
        mock_webbrowser_open.side_effect = [False, False, True]
        
        controller = BrowserController()
        result = controller.open_browser("http://localhost:8000")
        
        assert result is True
        assert mock_webbrowser_open.call_count == 3
    
    @patch('webbrowser.open')
    def test_retry_exhausted(self, mock_webbrowser_open):
        """Test behavior when all retry attempts are exhausted."""
        mock_webbrowser_open.return_value = False
        
        controller = BrowserController(retry_attempts=2)
        result = controller.open_browser("http://localhost:8000")
        
        assert result is False
        assert mock_webbrowser_open.call_count == 2
    
    @patch('webbrowser.open')
    @patch('time.sleep')
    def test_retry_delay(self, mock_sleep, mock_webbrowser_open):
        """Test that retry attempts include delay."""
        mock_webbrowser_open.side_effect = [False, True]
        
        controller = BrowserController()
        result = controller.open_browser("http://localhost:8000")
        
        assert result is True
        mock_sleep.assert_called_once_with(1.0)  # 1 second delay between retries


class TestBrowserControllerCrossPlatform:
    """Test cases for cross-platform functionality."""
    
    @patch('platform.system')
    @patch('webbrowser.open')
    def test_windows_browser_handling(self, mock_webbrowser_open, mock_platform):
        """Test browser handling on Windows."""
        mock_platform.return_value = 'Windows'
        mock_webbrowser_open.return_value = True
        
        controller = BrowserController()
        result = controller.open_browser("http://localhost:8000")
        
        assert result is True
        mock_webbrowser_open.assert_called_once()
    
    @patch('platform.system')
    @patch('webbrowser.open')
    def test_macos_browser_handling(self, mock_webbrowser_open, mock_platform):
        """Test browser handling on macOS."""
        mock_platform.return_value = 'Darwin'
        mock_webbrowser_open.return_value = True
        
        controller = BrowserController()
        result = controller.open_browser("http://localhost:8000")
        
        assert result is True
        mock_webbrowser_open.assert_called_once()
    
    @patch('platform.system')
    @patch('webbrowser.open')
    def test_linux_browser_handling(self, mock_webbrowser_open, mock_platform):
        """Test browser handling on Linux."""
        mock_platform.return_value = 'Linux'
        mock_webbrowser_open.return_value = True
        
        controller = BrowserController()
        result = controller.open_browser("http://localhost:8000")
        
        assert result is True
        mock_webbrowser_open.assert_called_once()
    
    def test_get_platform_info(self):
        """Test platform information retrieval."""
        controller = BrowserController()
        platform_info = controller.get_platform_info()
        
        assert 'system' in platform_info
        assert 'version' in platform_info
        assert isinstance(platform_info['system'], str)
        assert isinstance(platform_info['version'], str)


class TestBrowserControllerErrorHandling:
    """Test cases for error handling scenarios."""
    
    @patch('webbrowser.open')
    def test_general_exception_handling(self, mock_webbrowser_open):
        """Test handling of unexpected exceptions."""
        mock_webbrowser_open.side_effect = Exception("Unexpected error")
        
        controller = BrowserController()
        result = controller.open_browser("http://localhost:8000")
        
        assert result is False
    
    def test_url_sanitization(self):
        """Test URL sanitization functionality."""
        controller = BrowserController()
        
        # Test whitespace trimming
        assert controller._sanitize_url("  http://localhost:8000  ") == "http://localhost:8000"
        
        # Test case normalization for scheme
        assert controller._sanitize_url("HTTP://localhost:8000") == "http://localhost:8000"
        assert controller._sanitize_url("HTTPS://localhost:8000") == "https://localhost:8000"
    
    @patch('webbrowser.open')
    def test_empty_url_handling(self, mock_webbrowser_open):
        """Test handling of empty or None URLs."""
        controller = BrowserController()
        
        with pytest.raises(ValueError, match="Invalid URL"):
            controller.open_browser("")
        
        with pytest.raises(ValueError, match="Invalid URL"):
            controller.open_browser(None)
        
        mock_webbrowser_open.assert_not_called()


class TestBrowserControllerBrowserDetection:
    """Test cases for browser detection functionality."""
    
    @patch('webbrowser.get')
    def test_detect_available_browsers(self, mock_get):
        """Test detection of available browsers."""
        # Mock available browsers
        browsers = ['chrome', 'firefox', 'safari']
        
        def mock_get_browser(name):
            if name in browsers:
                return MagicMock()
            raise webbrowser.Error("Browser not found")
        
        mock_get.side_effect = mock_get_browser
        
        controller = BrowserController()
        available = controller.get_available_browsers(['chrome', 'firefox', 'edge', 'safari'])
        
        assert 'chrome' in available
        assert 'firefox' in available
        assert 'safari' in available
        assert 'edge' not in available
    
    def test_browser_priority_selection(self):
        """Test browser selection based on priority."""
        controller = BrowserController()
        
        # Test priority-based selection
        browsers = ['firefox', 'chrome', 'safari']
        priority = ['chrome', 'firefox', 'safari']
        
        selected = controller._select_best_browser(browsers, priority)
        assert selected == 'chrome'
        
        # Test when preferred browser not available
        browsers = ['firefox', 'safari']
        selected = controller._select_best_browser(browsers, priority)
        assert selected == 'firefox'


class TestBrowserControllerIntegration:
    """Integration tests for BrowserController."""
    
    @patch('webbrowser.open')
    def test_full_workflow(self, mock_webbrowser_open):
        """Test complete browser opening workflow."""
        mock_webbrowser_open.return_value = True
        
        controller = BrowserController()
        
        # Test URL validation and opening
        url = "http://localhost:8000/dashboard"
        result = controller.open_browser(url)
        
        assert result is True
        mock_webbrowser_open.assert_called_once_with(
            url,
            new=2,
            autoraise=True
        )
    
    def test_real_url_validation(self):
        """Test URL validation with real-world URLs."""
        controller = BrowserController()
        
        # Valid URLs
        assert controller._validate_url("http://localhost:8000") is True
        assert controller._validate_url("https://www.example.com") is True
        assert controller._validate_url("http://127.0.0.1:3000") is True
        
        # Invalid URLs
        assert controller._validate_url("not-a-url") is False
        assert controller._validate_url("") is False
        assert controller._validate_url("javascript:void(0)") is False


class TestBrowserControllerContextManager:
    """Test cases for context manager support (if implemented)."""
    
    def test_context_manager_support_basic(self):
        """Test basic context manager functionality."""
        # This test assumes context manager support might be added
        with BrowserController() as controller:
            assert controller is not None
            assert isinstance(controller, BrowserController)
    
    def test_context_manager_cleanup(self):
        """Test context manager cleanup."""
        controller = BrowserController()
        
        with controller:
            # Test that controller works within context
            assert controller._validate_url("http://localhost:8000") is True
        
        # Test that controller still works after context
        assert controller._validate_url("http://localhost:8000") is True