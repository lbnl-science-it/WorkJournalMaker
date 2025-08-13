# ABOUTME: Cross-platform browser controller for opening web applications
# ABOUTME: Handles URL validation, browser detection, and error recovery with retry logic

import time
import platform
import webbrowser
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse


class BrowserController:
    """Cross-platform browser controller for opening web applications.
    
    Provides URL validation, browser detection, retry logic, and error handling
    for reliably opening web browsers across different platforms.
    """
    
    def __init__(
        self,
        preferred_browser: Optional[str] = None,
        timeout: float = 5.0,
        retry_attempts: int = 3
    ) -> None:
        """Initialize the BrowserController.
        
        Args:
            preferred_browser: Name of preferred browser (e.g., 'chrome', 'firefox')
            timeout: Timeout for browser operations in seconds
            retry_attempts: Number of retry attempts for failed operations
            
        Raises:
            ValueError: If timeout or retry_attempts are not positive
        """
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        if retry_attempts <= 0:
            raise ValueError("Retry attempts must be positive")
            
        self.preferred_browser = preferred_browser
        self.timeout = timeout
        self.retry_attempts = retry_attempts
    
    def open_browser(self, url: str) -> bool:
        """Open the specified URL in a browser.
        
        Args:
            url: The URL to open
            
        Returns:
            True if browser opened successfully, False otherwise
            
        Raises:
            ValueError: If URL is invalid
        """
        if not self._validate_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        sanitized_url = self._sanitize_url(url)
        
        for attempt in range(self.retry_attempts):
            try:
                if self.preferred_browser:
                    try:
                        browser = webbrowser.get(self.preferred_browser)
                        success = browser.open(sanitized_url, new=2, autoraise=True)
                    except webbrowser.Error:
                        # Fall back to default browser if preferred browser not found
                        success = webbrowser.open(sanitized_url, new=2, autoraise=True)
                else:
                    success = webbrowser.open(sanitized_url, new=2, autoraise=True)
                
                if success:
                    return True
                    
            except Exception:
                # Handle all exceptions (webbrowser.Error, general exceptions)
                # For exceptions, we should stop retrying (not a temporary failure)
                return False
            
            # Add delay between retry attempts (except for last attempt)
            if attempt < self.retry_attempts - 1:
                time.sleep(1.0)
        
        return False
    
    def _validate_url(self, url: Any) -> bool:
        """Validate that the URL is properly formatted and uses allowed schemes.
        
        Args:
            url: The URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        try:
            parsed = urlparse(url.strip())
            
            # Check for valid scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for valid netloc (domain/host)
            if not parsed.netloc:
                return False
                
            return True
            
        except Exception:
            return False
    
    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL by trimming whitespace and normalizing scheme case.
        
        Args:
            url: The URL to sanitize
            
        Returns:
            Sanitized URL string
        """
        sanitized = url.strip()
        
        # Normalize scheme to lowercase
        parsed = urlparse(sanitized)
        if parsed.scheme:
            # Replace only the first occurrence of the scheme
            scheme_end = sanitized.find('://')
            if scheme_end != -1:
                sanitized = parsed.scheme.lower() + sanitized[scheme_end:]
            
        return sanitized
    
    def get_platform_info(self) -> Dict[str, str]:
        """Get platform information for cross-platform compatibility.
        
        Returns:
            Dictionary containing platform system and version
        """
        return {
            'system': platform.system(),
            'version': platform.version()
        }
    
    def get_available_browsers(self, browser_names: List[str]) -> List[str]:
        """Get list of available browsers from given list.
        
        Args:
            browser_names: List of browser names to check
            
        Returns:
            List of available browser names
        """
        available = []
        
        for browser_name in browser_names:
            try:
                webbrowser.get(browser_name)
                available.append(browser_name)
            except webbrowser.Error:
                continue
                
        return available
    
    def _select_best_browser(self, available_browsers: List[str], priority: List[str]) -> Optional[str]:
        """Select the best browser from available browsers based on priority.
        
        Args:
            available_browsers: List of available browser names
            priority: List of browser names in priority order
            
        Returns:
            Best available browser name or None if none available
        """
        for preferred in priority:
            if preferred in available_browsers:
                return preferred
        
        # Return first available if no priority match
        return available_browsers[0] if available_browsers else None
    
    def __enter__(self) -> 'BrowserController':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit with cleanup."""
        # No specific cleanup needed for browser controller
        pass