import os
import sys
import appdirs

def resource_path(relative_path):
    """Get the absolute path to a resource when running as a bundled executable.

    Args:
        relative_path (str): The relative path to the resource.

    Returns:
        str: The absolute path to the resource.
    """
    if hasattr(sys, '_MEIPASS'):
        # Running as a bundled executable
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Running in development mode
        return relative_path

def get_user_data_dir():
    """Get the user data directory path for the application.

    This function uses appdirs to determine the appropriate directory based on
    the operating system and creates it if it doesn't exist.

    Returns:
        str: The path to the user data directory.
    """
    data_dir = appdirs.user_data_dir('WorkJournal', 'WorkJournalMaker')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def setup_logging():
    """Configure logging to write to a file.

    This function sets up the root logger to write to app.log inside the user data directory.
    It configures the logger with a specific format and includes both file and console output.

    Returns:
        str: The path to the log file.
    """
    import logging
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

    return log_file_path