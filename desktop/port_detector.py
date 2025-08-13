# ABOUTME: Port detection utility for finding available ports on localhost
# ABOUTME: Provides functions to check port availability and find next available port

import socket


def is_port_available(port: int) -> bool:
    """
    Check if a port is available on localhost.
    
    Args:
        port: Port number to check (1-65535)
        
    Returns:
        True if port is available, False if in use
        
    Raises:
        ValueError: If port number is outside valid range
    """
    if not (1 <= port <= 65535):
        raise ValueError("Port number must be between 1 and 65535")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)  # 1 second timeout
            result = sock.connect_ex(('localhost', port))
            # Return True if connection failed (port available)
            # Return False if connection succeeded (port in use)
            return result != 0
    except (OSError, socket.timeout):
        # Network errors or timeouts mean port is likely available
        return True


def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    """
    Find the next available port starting from start_port.
    
    Args:
        start_port: Port number to start searching from (default: 8000)
        max_attempts: Maximum number of ports to check (default: 10)
        
    Returns:
        First available port number found
        
    Raises:
        ValueError: If start_port is outside valid range or max_attempts is invalid
        RuntimeError: If no available port is found within max_attempts
    """
    if not (1 <= start_port <= 65535):
        raise ValueError("Start port must be between 1 and 65535")
    
    if max_attempts <= 0:
        raise ValueError("max_attempts must be a positive integer")
    
    for i in range(max_attempts):
        current_port = start_port + i
        
        # Ensure we don't exceed valid port range
        if current_port > 65535:
            break
            
        if is_port_available(current_port):
            return current_port
    
    raise RuntimeError(f"No available ports found after {max_attempts} attempts starting from {start_port}")