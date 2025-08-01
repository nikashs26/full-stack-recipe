#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.free_llm_meal_planner import FreeLLMMealPlannerAgent
from services.user_preferences_service import UserPreferencesService
import json

def test_meal_planner():
    """Test the meal planner with sample preferences"""
    
    print("Testing AI Meal Planner...")
    
    # Initialize services
    user_preferences_service = UserPreferencesService()
    meal_planner = FreeLLMMealPlannerAgent(user_preferences_service)
    
    # Sample user preferences
    test_preferences = {
        "dietaryRestrictions": ["vegetarian"],
        "favoriteCuisines": ["Italian", "Mexican"],
        "favoriteFoods": ["pasta", "cheese", "tomatoes"],
        "cookingSkillLevel": "beginner",
        "includeBreakfast": True,
        "includeLunch": True,
        "includeDinner": True,
        "includeSnacks": False,
        "targetCalories": 2000,
        "targetProtein": 150,
        "maxCookingTime": "30 minutes"
    }
    
    print("Sample preferences:")
    print(json.dumps(test_preferences, indent=2))
    
    try:
        # Test meal plan generation directly with preferences
        print("\nGenerating meal plan...")
        
        # Try Ollama first (local, completely free)
        try:
            meal_plan = meal_planner._generate_with_ollama(test_preferences)
            if meal_plan:
                print("Success! Used: Ollama (Local)")
                plan = meal_plan
            else:
                raise Exception("Ollama returned no results")
        except Exception as e:
            print(f"Ollama failed: {e}")
            
            # Fallback to rule-based
            print("Using rule-based fallback...")
            meal_plan = meal_planner._generate_rule_based_plan(test_preferences)
            print("Success! Used: Rule-based (Fallback)")
        
        # Show the meal plan
        if "days" in meal_plan:
            print("\nGenerated Meal Plan:")
            for day, meals in meal_plan["days"].items():
                print(f"\n{day.title()}:")
                for meal_type, meal in meals.items():
                    print(f"  {meal_type}: {meal.get('name', 'No name')}")
                    print(f"    Cuisine: {meal.get('cuisine', 'Unknown')}")
                    print(f"    Time: {meal.get('cookingTime', 'Unknown')}")
        
        # Test recipe suggestions
        print("\nTesting recipe suggestions...")
        suggestions = meal_planner.get_recipe_suggestions("dinner", test_preferences, 3)
        print(f"Found {len(suggestions)} dinner suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion.get('name', 'No name')} - {suggestion.get('cuisine', 'Unknown')}")
        
    except Exception as e:
        print(f"Error testing meal planner: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_meal_planner() 