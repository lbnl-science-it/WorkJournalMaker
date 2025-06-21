#!/usr/bin/env python3
"""
Test to confirm the prompt/parsing mismatch issue.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from google_genai_client import GoogleGenAIClient

def test_prompt_mismatch():
    """Test the actual prompt being used and show the mismatch."""
    print("🔍 Testing Prompt/Parsing Mismatch")
    print("=" * 50)
    
    # Load config
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Create client
    client = GoogleGenAIClient(config.google_genai)
    
    # Test with sample journal content
    sample_content = """2024-07-02
Office Hours
Working on AI Parser project
Fixed bug in data processing
Meeting with team about next steps"""
    
    print("📝 Sample journal content:")
    print(sample_content)
    print()
    
    # Show the actual prompt being sent
    prompt = client._create_analysis_prompt(sample_content)
    print("📤 Actual prompt being sent to API:")
    print("-" * 40)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print()
    
    # Make the API call and show raw response
    try:
        response_text = client._make_api_call_with_retry(prompt)
        print("📥 Raw API response:")
        print("-" * 40)
        print(repr(response_text))
        print()
        print("📥 Formatted API response:")
        print("-" * 40)
        print(response_text)
        print()
        
        # Try to parse it
        print("🔧 Attempting to parse as JSON...")
        try:
            parsed = client._parse_response(response_text)
            print("✅ Parsing successful:", parsed)
        except Exception as e:
            print(f"❌ Parsing failed: {e}")
            print("💡 This confirms the mismatch - API returns text, parser expects JSON")
            
    except Exception as e:
        print(f"❌ API call failed: {e}")

if __name__ == "__main__":
    test_prompt_mismatch()