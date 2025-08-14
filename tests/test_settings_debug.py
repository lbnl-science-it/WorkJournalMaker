"""Debug script to test settings API endpoint."""

from fastapi.testclient import TestClient
from web.app import app

def test_settings_endpoint():
    """Test the settings endpoint to see what's happening."""
    client = TestClient(app)
    
    try:
        response = client.get("/api/settings/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print("Error details:")
            try:
                error_data = response.json()
                print(f"Error JSON: {error_data}")
            except:
                print("Could not parse error as JSON")
                
    except Exception as e:
        print(f"Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_settings_endpoint()