import sys
import unittest
from unittest.mock import patch
from web.resource_utils import resource_path, get_user_data_dir

class TestUtils(unittest.TestCase):
    def test_resource_path_frozen(self):
        """Test resource_path when running as a bundled executable."""
        with patch.dict('sys.__dict__', {'_MEIPASS': '/tmp/test_path'}):
            expected_path = '/tmp/test_path/assets/style.css'
            result = resource_path('assets/style.css')
            self.assertEqual(result, expected_path)

    def test_resource_path_not_frozen(self):
        """Test resource_path when not running as a bundled executable."""
        # Ensure _MEIPASS is not in sys.__dict__
        if '_MEIPASS' in sys.__dict__:
            del sys.__dict__['_MEIPASS']
        expected_path = 'assets/style.css'
        result = resource_path('assets/style.css')
        self.assertEqual(result, expected_path)

    def test_get_user_data_dir(self):
        """Test get_user_data_dir function."""
        with patch('appdirs.user_data_dir', return_value='/mock/user/data/dir'):
            with patch('os.makedirs') as mock_makedirs:
                result = get_user_data_dir()
                self.assertEqual(result, '/mock/user/data/dir')
                mock_makedirs.assert_called_once_with('/mock/user/data/dir', exist_ok=True)

if __name__ == '__main__':
    unittest.main()

# Add test for setup_logging function
class TestLogging(unittest.TestCase):
    def test_setup_logging(self):
        """Test that setup_logging configures the logger correctly."""
        from web.resource_utils import get_user_data_dir
        import os

        # Call setup_logging and get the log file path
        from tests.test_utils import setup_logging
        log_file_path = setup_logging()

        # Verify the log file exists
        self.assertTrue(os.path.exists(log_file_path), f"Log file was not created at {log_file_path}")

        # Verify the log file is in the user data directory
        user_data_dir = get_user_data_dir()
        self.assertTrue(log_file_path.startswith(user_data_dir),
                       f"Log file is not in the user data directory: {log_file_path}")

        # Verify the log file name is correct
        self.assertTrue(log_file_path.endswith('app.log'),
                       f"Log file has incorrect name: {log_file_path}")

        # Clean up the log file after test
        if os.path.exists(log_file_path):
            os.remove(log_file_path)

def setup_logging():
    """Configure logging to write to a file."""
    import logging
    from web.resource_utils import get_user_data_dir
    import os

    # Get the user data directory
    data_dir = get_user_data_dir()

    # Create the log file path
    log_file_path = os.path.join(data_dir, 'app.log')

    # Configure the root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )

    # Return the log file path for testing purposes
    return log_file_path

def setup_logging():
    """Configure logging to write to a file."""
    import logging
    from web.resource_utils import get_user_data_dir
    import os

    # Get the user data directory
    data_dir = get_user_data_dir()

    # Create the log file path
    log_file_path = os.path.join(data_dir, 'app.log')

    # Configure the root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )

    # Return the log file path for testing purposes
    return log_file_path