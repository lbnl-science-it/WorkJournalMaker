"""Simple test for settings service functionality."""

import asyncio
import tempfile
import shutil
from pathlib import Path
from web.database import DatabaseManager
from web.services.settings_service import SettingsService
from config_manager import ConfigManager
from logger import JournalSummarizerLogger

async def test_settings_service():
    """Test the settings service directly."""
    # Create temporary workspace
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create test configuration
        config_manager = ConfigManager()
        config = config_manager.get_config()
        config.processing.base_path = str(temp_path / "worklogs")
        config.processing.output_path = str(temp_path / "output")
        
        # Create logger
        logger = JournalSummarizerLogger(config.logging)
        
        # Create database manager
        db_path = temp_path / "test_settings.db"
        db_manager = DatabaseManager(str(db_path))
        await db_manager.initialize()
        
        # Create settings service
        settings_service = SettingsService(config, logger, db_manager)
        
        print("Testing settings service...")
        
        # Test getting all settings
        settings = await settings_service.get_all_settings()
        print(f"Retrieved {len(settings)} settings")
        
        # Test getting a specific setting
        theme_setting = await settings_service.get_setting('ui.theme')
        print(f"Theme setting: {theme_setting.parsed_value if theme_setting else 'Not found'}")
        
        # Test updating a setting
        updated_setting = await settings_service.update_setting('ui.theme', 'dark')
        print(f"Updated theme to: {updated_setting.parsed_value if updated_setting else 'Failed'}")
        
        # Test filesystem path setting
        base_path_setting = await settings_service.get_setting('filesystem.base_path')
        print(f"Base path: {base_path_setting.parsed_value if base_path_setting else 'Not found'}")
        
        # Test categories
        categories = settings_service.get_setting_categories()
        print(f"Categories: {list(categories.keys())}")
        
        print("Settings service test completed successfully!")
        
        # Cleanup
        if db_manager.engine:
            await db_manager.engine.dispose()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    asyncio.run(test_settings_service())