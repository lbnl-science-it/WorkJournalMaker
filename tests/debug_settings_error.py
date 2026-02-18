import asyncio
import os
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

from fastapi.testclient import TestClient
from web.app import app

async def test_settings_directly():
    """Test settings service directly."""
    from web.services.settings_service import SettingsService
    from core.config_manager import ConfigManager
    from core.database.database_manager import DatabaseManager
    from core.logger import JournalSummarizerLogger
    
    try:
        # Initialize components
        config = ConfigManager()
        logger = JournalSummarizerLogger("test_settings")
        db_manager = DatabaseManager(config, logger)
        
        # Initialize settings service
        settings_service = SettingsService(config, db_manager, logger)
        
        # Test the update directly
        result = await settings_service.update_setting("filesystem.base_path", "/tmp/test_journal_path")
        print(f"Direct service result: {result}")
        
    except Exception as e:
        print(f"Direct service exception: {e}")
        import traceback
        traceback.print_exc()

def test_settings_error():
    """Debug the settings error."""
    client = TestClient(app)
    
    try:
        # First test if the setting exists
        get_response = client.get("/api/settings/filesystem.base_path")
        print(f"GET Status Code: {get_response.status_code}")
        print(f"GET Response: {get_response.text}")
        
        # Then try to update
        response = client.put(
            "/api/settings/filesystem.base_path",
            json={"value": "/tmp/test_journal_path"}
        )
        print(f"PUT Status Code: {response.status_code}")
        print(f"PUT Response: {response.text}")
        if response.status_code != 200:
            print(f"Error details: {response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing API endpoint...")
    test_settings_error()
    print("\nTesting service directly...")
    asyncio.run(test_settings_directly())