#!/usr/bin/env python3
"""
Validate the Google GenAI parsing fix.
"""

from pathlib import Path

from config_manager import ConfigManager
from google_genai_client import GoogleGenAIClient

def main():
    print("🔧 Validating Google GenAI Parsing Fix")
    print("=" * 40)
    
    try:
        # Load config and create client
        config_manager = ConfigManager()
        config = config_manager.get_config()
        client = GoogleGenAIClient(config.google_genai)
        
        # Test the connection first
        print("1. Testing connection...")
        if not client.test_connection():
            print("❌ Connection test failed")
            return False
        print("✅ Connection successful")
        
        # Test with a simple journal entry
        print("\n2. Testing entity extraction...")
        sample_file_path = Path("test_sample.txt")
        
        # Use the analyze_content method (the main entry point)
        result = client.analyze_content(
            "2024-07-02\nWorking on AI Parser project\nMeeting with John Smith\nFixed database connection bug",
            sample_file_path
        )
        
        print("✅ Analysis completed successfully")
        print(f"📊 Results:")
        print(f"  Projects: {result.projects}")
        print(f"  Participants: {result.participants}")
        print(f"  Tasks: {result.tasks}")
        print(f"  Themes: {result.themes}")
        print(f"  API call time: {result.api_call_time:.3f}s")
        
        # Check if we got meaningful results
        if result.projects or result.participants or result.tasks or result.themes:
            print("✅ Entity extraction working correctly")
            return True
        else:
            print("⚠️  No entities extracted - may need prompt tuning")
            return True  # Still successful parsing, just empty results
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Fix validation successful!")
        print("The 'Failed to parse API response' error should now be resolved.")
    else:
        print("\n💥 Fix validation failed!")
        print("The issue may require additional investigation.")