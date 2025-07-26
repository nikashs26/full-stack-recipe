import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test user credentials
TEST_EMAIL = 'test@example.com'
TEST_PASSWORD = 'test123'

# Base URL for the API
BASE_URL = 'http://localhost:5005/api'

def get_auth_token():
    """Get authentication token using test credentials"""
    login_data = {
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return response.json().get('token')
    except requests.exceptions.RequestException as e:
        print(f"Error getting auth token: {e}")
        return None

def test_ai_meal_plan():
    """Test the AI meal plan endpoint"""
    # First get auth token
    token = get_auth_token()
    if not token:
        print("Failed to get authentication token")
        return
    
    # Test data for the request
    test_data = {
        "budget": 100,
        "dietary_goals": ["weight loss", "high protein"],
        "currency": "$"
    }
    
    # Make the request to our endpoint with auth token
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/ai/meal_plan',
            json=test_data,
            headers=headers
        )
        
        # Print the response
        print(f"Status Code: {response.status_code}")
        if response.text:
            try:
                print("Response:")
                print(json.dumps(response.json(), indent=2))
            except json.JSONDecodeError:
                print("Response (raw):")
                print(response.text)
        else:
            print("No response body")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_ai_meal_plan()
