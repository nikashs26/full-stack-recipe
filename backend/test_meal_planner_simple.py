#!/usr/bin/env python3
"""
Simple test script to test the meal planner service
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = str(Path(__file__).parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.free_llm_meal_planner import FreeLLMMealPlannerAgent
from services.user_preferences_service import UserPreferencesService

def test_meal_planner():
    """Test the meal planner service"""
    print("🧪 Testing Meal Planner Service")
    print("=" * 50)
    
    # Initialize services
    user_preferences_service = UserPreferencesService()
    meal_planner = FreeLLMMealPlannerAgent(user_preferences_service)
    
    # Test preferences
    print("\n1. Testing User Preferences Service...")
    test_user_id = "test@example.com"
    
    # Create test preferences
    test_preferences = {
        "dietaryRestrictions": ["vegetarian"],
        "favoriteCuisines": ["Indian", "Mediterranean"],
        "allergens": ["nuts"],
        "cookingSkillLevel": "beginner",
        "favoriteFoods": ["pasta", "rice", "vegetables"],
        "healthGoals": ["weight loss"],
        "maxCookingTime": "30 minutes",
        "targetCalories": 1800,
        "targetProtein": 120,
        "targetCarbs": 180,
        "targetFat": 60
    }
    
    print(f"   Creating test preferences for user: {test_user_id}")
    user_preferences_service.save_preferences(test_user_id, test_preferences)
    
    # Retrieve preferences
    print("   Retrieving preferences...")
    retrieved_prefs = user_preferences_service.get_preferences(test_user_id)
    print(f"   Retrieved preferences: {retrieved_prefs}")
    
    if not retrieved_prefs:
        print("   ❌ Failed to retrieve preferences")
        return
    
    print("   ✅ Preferences service working")
    
    # Test meal planner
    print("\n2. Testing Meal Planner...")
    print("   Generating meal plan...")
    
    try:
        result = meal_planner.generate_weekly_meal_plan(test_user_id)
        print(f"   Result: {result}")
        
        if result.get('error'):
            print(f"   ❌ Meal planner error: {result['error']}")
        elif result.get('success'):
            print("   ✅ Meal plan generated successfully!")
            print(f"   Source: {result.get('source', 'unknown')}")
        else:
            print("   ⚠️  Unexpected result format")
            
    except Exception as e:
        print(f"   ❌ Exception in meal planner: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_meal_planner()
