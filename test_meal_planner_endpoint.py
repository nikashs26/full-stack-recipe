#!/usr/bin/env python3

import requests
import json

def test_meal_planner_endpoint():
    """Test the meal planner endpoint"""
    
    print("Testing meal planner endpoint...")
    
    # Test the endpoint
    url = "http://localhost:5003/api/ai/simple_meal_plan"
    
    # Test with a simple POST request
    try:
        response = requests.post(url, json={}, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ Endpoint is working (401 is expected without auth)")
        elif response.status_code == 200:
            print("✅ Endpoint is working!")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - backend might not be running on port 5004")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_meal_planner_endpoint() 