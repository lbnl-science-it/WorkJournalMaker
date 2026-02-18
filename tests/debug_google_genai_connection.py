#!/usr/bin/env python3
"""
Debug Google GenAI Connection Issues

This script helps diagnose the "Failed to parse API response: Expecting value: line 1 column 1 (char 0)" error
by testing various aspects of the Google GenAI configuration and connection.
"""

import os
import sys
import json
import logging
try:
    import google.genai as genai
    from google.genai import errors as genai_errors
    GENAI_AVAILABLE = True
except ImportError as e:
    GENAI_AVAILABLE = False
    IMPORT_ERROR = str(e)

from config_manager import ConfigManager, GoogleGenAIConfig
from google_genai_client import GoogleGenAIClient

def setup_logging():
    """Setup detailed logging for debugging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debug_google_genai.log')
        ]
    )
    return logging.getLogger(__name__)

def check_genai_import():
    """Check if google.genai is properly imported."""
    print("🔍 Checking Google GenAI Import...")
    print("-" * 40)
    
    if not GENAI_AVAILABLE:
        print(f"❌ google.genai import failed: {IMPORT_ERROR}")
        print("💡 Solution: Install with 'pip install google-genai'")
        return False
    else:
        print("✅ google.genai imported successfully")
        print(f"📦 GenAI version: {getattr(genai, '__version__', 'Unknown')}")
        return True

def check_configuration():
    """Check configuration loading and validation."""
    print("\n🔍 Checking Configuration...")
    print("-" * 40)
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print("✅ Configuration loaded successfully")
        print(f"📝 LLM Provider: {config.llm.provider}")
        
        if config.llm.provider == "google_genai":
            print(f"📝 Project: {config.google_genai.project}")
            print(f"📝 Location: {config.google_genai.location}")
            print(f"📝 Model: {config.google_genai.model}")
            return config
        else:
            print(f"❌ LLM provider is set to '{config.llm.provider}', not 'google_genai'")
            print("💡 Solution: Set llm.provider to 'google_genai' in config.yaml")
            return None
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Solution: Check config.yaml file exists and is valid")
        return None

def check_google_cloud_auth():
    """Check Google Cloud authentication."""
    print("\n🔍 Checking Google Cloud Authentication...")
    print("-" * 40)
    
    # Check for various authentication methods
    auth_methods = []
    
    # Check for service account key file
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if os.path.exists(cred_path):
            auth_methods.append(f"✅ Service Account Key: {cred_path}")
        else:
            auth_methods.append(f"❌ Service Account Key file not found: {cred_path}")
    
    # Check for gcloud CLI authentication
    try:
        import subprocess
        result = subprocess.run(['gcloud', 'auth', 'list', '--format=json'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            accounts = json.loads(result.stdout)
            active_accounts = [acc for acc in accounts if acc.get('status') == 'ACTIVE']
            if active_accounts:
                auth_methods.append(f"✅ gcloud CLI authenticated: {active_accounts[0]['account']}")
            else:
                auth_methods.append("❌ gcloud CLI: No active accounts")
        else:
            auth_methods.append("❌ gcloud CLI not available or not authenticated")
    except Exception as e:
        auth_methods.append(f"❌ gcloud CLI check failed: {e}")
    
    # Check for metadata server (for GCE/Cloud Run)
    try:
        import requests
        response = requests.get(
            'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',
            headers={'Metadata-Flavor': 'Google'},
            timeout=5
        )
        if response.status_code == 200:
            auth_methods.append("✅ Metadata server authentication available")
        else:
            auth_methods.append(f"❌ Metadata server returned: {response.status_code}")
    except Exception as e:
        auth_methods.append(f"❌ Metadata server not available: {e}")
    
    if not auth_methods:
        auth_methods.append("❌ No authentication methods detected")
    
    for method in auth_methods:
        print(method)
    
    return any("✅" in method for method in auth_methods)

def test_raw_genai_client(config):
    """Test raw Google GenAI client creation."""
    print("\n🔍 Testing Raw Google GenAI Client...")
    print("-" * 40)
    
    try:
        # Create client with Vertex AI configuration
        client = genai.Client(
            vertexai=True,
            project=config.google_genai.project,
            location=config.google_genai.location
        )
        print("✅ Raw GenAI client created successfully")
        return client
    except Exception as e:
        print(f"❌ Raw GenAI client creation failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        return None

def test_simple_api_call(client, model):
    """Test a simple API call to diagnose response issues."""
    print("\n🔍 Testing Simple API Call...")
    print("-" * 40)
    
    try:
        # Very simple test prompt
        test_prompt = "Say 'Hello' in JSON format: {\"message\": \"Hello\"}"
        
        print(f"📝 Using model: {model}")
        print(f"📝 Test prompt: {test_prompt}")
        
        # Make the API call
        response = client.models.generate_content(
            model=model,
            contents=test_prompt,
            config={
                'temperature': 0.1,
                'top_p': 0.9,
                'max_output_tokens': 100
            }
        )
        
        print("✅ API call completed successfully")
        
        # Examine response structure
        print(f"🔍 Response type: {type(response)}")
        print(f"🔍 Response attributes: {dir(response)}")
        
        # Try to extract text
        response_text = None
        if hasattr(response, 'text') and response.text:
            response_text = response.text
            print(f"✅ Found response.text: {repr(response_text)}")
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            print(f"🔍 Candidate type: {type(candidate)}")
            print(f"🔍 Candidate attributes: {dir(candidate)}")
            
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts = candidate.content.parts
                print(f"🔍 Parts count: {len(parts)}")
                if parts and hasattr(parts[0], 'text'):
                    response_text = parts[0].text
                    print(f"✅ Found parts[0].text: {repr(response_text)}")
                else:
                    print("❌ No text found in parts")
            else:
                print("❌ No content.parts found in candidate")
        else:
            print("❌ No text or candidates found in response")
        
        if response_text:
            print(f"📝 Final response text: {response_text}")
            
            # Test JSON parsing
            try:
                # Try to extract JSON from the response
                import re
                json_pattern = r'\{.*\}'
                match = re.search(json_pattern, response_text, re.DOTALL)
                if match:
                    json_text = match.group(0)
                    parsed = json.loads(json_text)
                    print(f"✅ JSON parsing successful: {parsed}")
                else:
                    print(f"❌ No JSON found in response: {repr(response_text)}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
        else:
            print("❌ No response text to parse - this explains the empty response error!")
            
        return response_text is not None
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        # Check for specific error types
        error_str = str(e).lower()
        if 'authentication' in error_str or 'unauthorized' in error_str:
            print("💡 This appears to be an authentication error")
        elif 'permission' in error_str or 'access denied' in error_str:
            print("💡 This appears to be a permissions error")
        elif 'not found' in error_str or 'invalid' in error_str:
            print("💡 This appears to be a configuration error (invalid model/project)")
        elif 'quota' in error_str or 'rate limit' in error_str:
            print("💡 This appears to be a quota/rate limiting error")
        
        return False

def test_google_genai_client(config):
    """Test the actual GoogleGenAIClient class."""
    print("\n🔍 Testing GoogleGenAIClient Class...")
    print("-" * 40)
    
    try:
        client = GoogleGenAIClient(config.google_genai)
        print("✅ GoogleGenAIClient created successfully")
        
        # Test connection
        if client.test_connection():
            print("✅ GoogleGenAIClient connection test passed")
            return True
        else:
            print("❌ GoogleGenAIClient connection test failed")
            return False
            
    except Exception as e:
        print(f"❌ GoogleGenAIClient creation failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

def main():
    """Main diagnostic function."""
    logger = setup_logging()
    
    print("🔧 Google GenAI Connection Diagnostic Tool")
    print("=" * 50)
    
    # Step 1: Check imports
    if not check_genai_import():
        return
    
    # Step 2: Check configuration
    config = check_configuration()
    if not config:
        return
    
    # Step 3: Check authentication
    auth_ok = check_google_cloud_auth()
    if not auth_ok:
        print("\n💡 Authentication issues detected. Try:")
        print("   - gcloud auth application-default login")
        print("   - Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("   - Ensure the service account has Vertex AI permissions")
    
    # Step 4: Test raw client
    raw_client = test_raw_genai_client(config)
    if not raw_client:
        return
    
    # Step 5: Test simple API call
    api_ok = test_simple_api_call(raw_client, config.google_genai.model)
    
    # Step 6: Test our client class
    client_ok = test_google_genai_client(config)
    
    # Summary
    print("\n📊 Diagnostic Summary")
    print("=" * 30)
    print(f"Import: {'✅' if GENAI_AVAILABLE else '❌'}")
    print(f"Config: {'✅' if config else '❌'}")
    print(f"Auth: {'✅' if auth_ok else '❌'}")
    print(f"Raw Client: {'✅' if raw_client else '❌'}")
    print(f"API Call: {'✅' if api_ok else '❌'}")
    print(f"Our Client: {'✅' if client_ok else '❌'}")
    
    if not api_ok:
        print("\n🎯 Root Cause: API calls are returning empty responses")
        print("This explains the 'Expecting value: line 1 column 1 (char 0)' error")
        
        if not auth_ok:
            print("💡 Most likely cause: Authentication issues")
        else:
            print("💡 Most likely cause: Model configuration or API permissions")

if __name__ == "__main__":
    main()