#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.free_llm_meal_planner import FreeLLMMealPlannerAgent
from services.user_preferences_service import UserPreferencesService

def test_llm_meal_planner():
    """Test the LLM meal planner directly"""
    
    print("🧪 Testing LLM Meal Planner...")
    
    # Initialize services
    user_preferences_service = UserPreferencesService()
    meal_planner = FreeLLMMealPlannerAgent(user_preferences_service)
    
    # Test preferences
    test_preferences = {
        "dietaryRestrictions": [],
        "favoriteCuisines": ["International", "japanese"],
        "foodsToAvoid": [],
        "allergens": [],
        "cookingSkillLevel": "beginner",
        "healthGoals": ["General wellness"],
        "maxCookingTime": "30 minutes",
        "favoriteFoods": ["burger", "sushi", "pasta"],
        "includeBreakfast": True,
        "includeLunch": True,
        "includeDinner": True,
        "includeSnacks": False,
        "targetCalories": 2000,
        "targetProtein": 150,
        "targetCarbs": 200,
        "targetFat": 65
    }
    
    print("📋 Test preferences:", test_preferences)
    
    # Test Ollama directly
    print("\n🤖 Testing Ollama directly...")
    try:
        result = meal_planner._generate_with_ollama(test_preferences)
        if result:
            print("✅ Ollama generated meal plan successfully!")
            print("📄 Generated plan structure:", list(result.keys()) if isinstance(result, dict) else type(result))
        else:
            print("❌ Ollama returned None")
    except Exception as e:
        print(f"❌ Ollama failed: {e}")
    
    # Test full meal planner
    print("\n🎯 Testing full meal planner...")
    try:
        result = meal_planner.generate_weekly_meal_plan("test_user")
        print(f"📊 Result: {result.get('llm_used', 'Unknown')}")
        print(f"✅ Success: {result.get('success', False)}")
        if result.get('plan'):
            print(f"📋 Plan structure: {list(result['plan'].keys()) if isinstance(result['plan'], dict) else type(result['plan'])}")
    except Exception as e:
        print(f"❌ Full meal planner failed: {e}")

if __name__ == "__main__":
    test_llm_meal_planner() 