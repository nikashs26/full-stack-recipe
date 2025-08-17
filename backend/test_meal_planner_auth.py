#!/usr/bin/env python3
"""
Test script to verify meal planner endpoint works with authentication
"""

import requests
import json

def test_meal_planner_with_auth():
    """Test the meal planner endpoint with authentication"""
    
    base_url = "http://localhost:5003"
    
    print("🧪 Testing meal planner endpoint with authentication...")
    
    # Step 1: Login to get a token
    print("\n1️⃣ Logging in...")
    login_data = {
        "email": "test@example.com",
        "password": "Test123!"
    }
    
    try:
        login_response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return
        
        login_data = login_response.json()
        token = login_data.get('token')
        if not token:
            print("❌ No token received from login")
            return
        
        print("✅ Login successful, token received")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Test the meal planner endpoint
    print("\n2️⃣ Testing meal planner endpoint...")
    
    meal_plan_data = {
        "preferences": {
            "allergens": ["peanuts"],
            "dietaryRestrictions": ["vegetarian"],
            "favoriteCuisines": ["italian", "indian"],
            "favoriteFoods": ["pasta", "curry"],
            "cookingSkillLevel": "intermediate",
            "maxCookingTime": 60,
            "includeBreakfast": True,
            "includeLunch": True,
            "includeDinner": True,
            "includeSnacks": False,
            "targetCalories": 2000,
            "targetProtein": 150,
            "targetCarbs": 200,
            "targetFat": 65
        }
    }
    
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        meal_plan_response = requests.post(
            f"{base_url}/api/ai/simple_meal_plan",
            json=meal_plan_data,
            headers=headers
        )
        
        print(f"📊 Meal planner response status: {meal_plan_response.status_code}")
        
        if meal_plan_response.status_code == 200:
            print("✅ Meal planner endpoint working!")
            response_data = meal_plan_response.json()
            print("📦 Response data:")
            print(json.dumps(response_data, indent=2))
        else:
            print("❌ Meal planner endpoint failed")
            print(f"Response: {meal_plan_response.text}")
            
    except Exception as e:
        print(f"❌ Meal planner test error: {e}")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    test_meal_planner_with_auth()
