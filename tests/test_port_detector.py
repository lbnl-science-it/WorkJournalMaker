# ABOUTME: Comprehensive test suite for port detection utility
# ABOUTME: Tests port availability checking, finding available ports, and error handling scenarios

import pytest
import socket
from unittest.mock import patch, MagicMock
from desktop.port_detector import is_port_available, find_available_port


class TestIsPortAvailable:
    """Test cases for port availability checking."""
    
    def test_port_available_when_nothing_listening(self):
        """Test that an unused port is reported as available."""
        # Use a high port number that's unlikely to be in use
        port = 65432
        assert is_port_available(port) is True
    
    @patch('socket.socket')
    def test_port_unavailable_when_connection_refused(self, mock_socket):
        """Test that a port reports unavailable when connection is refused."""
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect_ex.return_value = 111  # Connection refused
        
        result = is_port_available(8000)
        assert result is True  # Connection refused means port is available
    
    @patch('socket.socket')
    def test_port_unavailable_when_in_use(self, mock_socket):
        """Test that a port in use is reported as unavailable."""
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect_ex.return_value = 0  # Connection successful
        
        result = is_port_available(8000)
        assert result is False
    
    @patch('socket.socket')
    def test_network_error_handling(self, mock_socket):
        """Test proper handling of network errors during port checking."""
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect_ex.side_effect = OSError("Network unreachable")
        
        result = is_port_available(8000)
        assert result is True  # Network errors should default to available
    
    def test_invalid_port_numbers(self):
        """Test handling of invalid port numbers."""
        # Port number too low
        with pytest.raises(ValueError, match="Port number must be between 1 and 65535"):
            is_port_available(0)
        
        # Port number too high
        with pytest.raises(ValueError, match="Port number must be between 1 and 65535"):
            is_port_available(65536)
        
        # Negative port number
        with pytest.raises(ValueError, match="Port number must be between 1 and 65535"):
            is_port_available(-1)
    
    def test_valid_port_range_boundaries(self):
        """Test that boundary port numbers are handled correctly."""
        # These might fail if ports are actually in use, but should not raise exceptions
        try:
            result = is_port_available(1)
            assert isinstance(result, bool)
        except PermissionError:
            # Privileged ports might require special permissions
            pass
        
        result = is_port_available(65535)
        assert isinstance(result, bool)


class TestFindAvailablePort:
    """Test cases for finding available ports."""
    
    @patch('desktop.port_detector.is_port_available')
    def test_find_first_available_port(self, mock_is_available):
        """Test finding the first available port when start port is available."""
        mock_is_available.return_value = True
        
        port = find_available_port(8000)
        assert port == 8000
        mock_is_available.assert_called_once_with(8000)
    
    @patch('desktop.port_detector.is_port_available')
    def test_find_available_port_after_several_attempts(self, mock_is_available):
        """Test finding an available port when first few are unavailable."""
        # First two ports unavailable, third one available
        mock_is_available.side_effect = [False, False, True]
        
        port = find_available_port(8000)
        assert port == 8002
        assert mock_is_available.call_count == 3
    
    @patch('desktop.port_detector.is_port_available')
    def test_no_ports_available_in_range(self, mock_is_available):
        """Test handling when no ports are available in the specified range."""
        mock_is_available.return_value = False
        
        with pytest.raises(RuntimeError, match="No available ports found after 10 attempts starting from 8000"):
            find_available_port(8000, max_attempts=10)
        
        assert mock_is_available.call_count == 10
    
    @patch('desktop.port_detector.is_port_available')
    def test_custom_max_attempts(self, mock_is_available):
        """Test using custom max_attempts parameter."""
        mock_is_available.return_value = False
        
        with pytest.raises(RuntimeError, match="No available ports found after 5 attempts starting from 9000"):
            find_available_port(9000, max_attempts=5)
        
        assert mock_is_available.call_count == 5
    
    @patch('desktop.port_detector.is_port_available')
    def test_find_available_port_with_port_wraparound(self, mock_is_available):
        """Test that port numbers don't exceed valid range during search."""
        # Test near the upper limit of valid ports
        mock_is_available.side_effect = [False, True]
        
        port = find_available_port(65534, max_attempts=3)
        assert port == 65535  # Should find the last valid port
        # Should only check 2 ports (65534, 65535) before exceeding range
        assert mock_is_available.call_count == 2
    
    def test_invalid_start_port(self):
        """Test handling of invalid start port numbers."""
        with pytest.raises(ValueError, match="Start port must be between 1 and 65535"):
            find_available_port(0)
        
        with pytest.raises(ValueError, match="Start port must be between 1 and 65535"):
            find_available_port(65536)
    
    def test_invalid_max_attempts(self):
        """Test handling of invalid max_attempts parameter."""
        with pytest.raises(ValueError, match="max_attempts must be a positive integer"):
            find_available_port(8000, max_attempts=0)
        
        with pytest.raises(ValueError, match="max_attempts must be a positive integer"):
            find_available_port(8000, max_attempts=-1)
    
    def test_default_parameters(self):
        """Test that default parameters work correctly."""
        # This will likely pass since we're testing with real network
        port = find_available_port()
        assert isinstance(port, int)
        assert 8000 <= port <= 8009  # Should find something in first 10 attempts


class TestPortDetectorEdgeCases:
    """Test edge cases and error scenarios."""
    
    @patch('socket.socket')
    def test_socket_creation_failure(self, mock_socket):
        """Test handling when socket creation fails."""
        mock_socket.side_effect = OSError("Socket creation failed")
        
        result = is_port_available(8000)
        assert result is True  # Should default to available on socket errors
    
    @patch('socket.socket')
    def test_socket_timeout_handling(self, mock_socket):
        """Test handling of socket timeout scenarios."""
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect_ex.side_effect = socket.timeout("Connection timed out")
        
        result = is_port_available(8000)
        assert result is True  # Timeout should be treated as available
    
    @patch('desktop.port_detector.is_port_available')
    def test_find_port_near_upper_limit(self, mock_is_available):
        """Test finding ports near the upper limit of valid port range."""
        mock_is_available.return_value = True
        
        # Start near upper limit
        port = find_available_port(65530)
        assert port == 65530
    
    @patch('desktop.port_detector.is_port_available')
    def test_find_port_exceeding_valid_range(self, mock_is_available):
        """Test behavior when search would exceed valid port range."""
        mock_is_available.return_value = False
        
        # This should raise an error when it tries to check invalid ports
        with pytest.raises(RuntimeError):
            find_available_port(65534, max_attempts=5)


class TestPortDetectorIntegration:
    """Integration tests using real network operations."""
    
    def test_real_port_detection(self):
        """Test port detection with real network operations."""
        # Find an available port
        port = find_available_port(50000, max_attempts=5)
        assert isinstance(port, int)
        assert 50000 <= port <= 50004
        
        # Verify the port is actually available
        assert is_port_available(port) is True
    
    def test_port_becomes_unavailable(self):
        """Test detection when a port becomes unavailable."""
        # Find an available port
        port = find_available_port(50010, max_attempts=5)
        
        # Create a server on that port
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_socket.bind(('localhost', port))
            server_socket.listen(1)
            
            # Now the port should be unavailable
            assert is_port_available(port) is False
            
        finally:
            server_socket.close()
        
        # After closing, port should be available again
        assert is_port_available(port) is True