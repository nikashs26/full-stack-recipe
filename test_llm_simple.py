#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.free_llm_meal_planner import FreeLLMMealPlannerAgent
from services.user_preferences_service import UserPreferencesService

def test_llm_simple():
    """Simple test of LLM meal planner"""
    
    print("🧪 Simple LLM Test...")
    
    # Initialize services
    user_preferences_service = UserPreferencesService()
    meal_planner = FreeLLMMealPlannerAgent(user_preferences_service)
    
    # Test preferences
    test_preferences = {
        "dietaryRestrictions": [],
        "favoriteCuisines": ["International", "japanese"],
        "favoriteFoods": ["burger", "sushi", "pasta"],
        "cookingSkillLevel": "beginner",
        "maxCookingTime": "30 minutes"
    }
    
    print("📋 Testing with preferences:", test_preferences)
    
    # Test Ollama
    try:
        result = meal_planner._generate_with_ollama(test_preferences)
        if result:
            print("✅ LLM generated meal plan!")
            print(f"📊 Plan keys: {list(result.keys())}")
            if 'monday' in result:
                print(f"📅 Monday meals: {list(result['monday'].keys())}")
        else:
            print("❌ LLM returned None")
    except Exception as e:
        print(f"❌ LLM failed: {e}")

if __name__ == "__main__":
    test_llm_simple() 