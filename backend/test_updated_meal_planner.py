#!/usr/bin/env python3
"""
Test script to verify the updated meal planner is working correctly.
This will test the FreeLLMMealPlannerAgent directly to see if it's generating LLM responses.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_updated_meal_planner():
    """Test the updated meal planner directly"""
    
    print("🧪 Testing Updated Meal Planner...")
    print("=" * 50)
    
    try:
        # Import the updated meal planner
        from services.free_llm_meal_planner import FreeLLMMealPlannerAgent
        from services.user_preferences_service import UserPreferencesService
        
        print("✅ Successfully imported updated meal planner")
        
        # Initialize services
        user_preferences_service = UserPreferencesService()
        meal_planner = FreeLLMMealPlannerAgent(user_preferences_service)
        
        print("✅ Services initialized successfully")
        
        # Create test preferences
        test_preferences = {
            'dietaryRestrictions': ['vegetarian'],
            'favoriteCuisines': ['Italian', 'Mexican', 'Indian'],
            'allergens': ['nuts'],
            'cookingSkillLevel': 'beginner',
            'favoriteFoods': ['pasta', 'rice', 'vegetables'],
            'healthGoals': ['weight loss'],
            'maxCookingTime': '45 minutes',
            'targetCalories': 1800,
            'targetProtein': 120,
            'targetCarbs': 180,
            'targetFat': 60
        }
        
        print("📋 Test preferences created:")
        print(json.dumps(test_preferences, indent=2))
        
        # Test the meal planner
        print("\n🚀 Testing meal plan generation...")
        
        # We need a user ID, so let's create a mock one
        test_user_id = "test_user_123"
        
        # Store test preferences
        user_preferences_service.collection.add(
            documents=[json.dumps(test_preferences)],
            metadatas=[{"user_id": test_user_id}],
            ids=[test_user_id]
        )
        
        print("✅ Test preferences stored in database")
        
        # Generate meal plan
        result = meal_planner.generate_weekly_meal_plan(test_user_id)
        
        print("\n📊 Meal Plan Generation Result:")
        print("=" * 50)
        print(json.dumps(result, indent=2))
        
        # Analyze the result
        if "error" in result:
            print(f"\n❌ Meal plan generation failed: {result['error']}")
            return False
        
        if "meal_plan" in result:
            meal_plan = result["meal_plan"]
            print(f"\n✅ Meal plan generated successfully!")
            print(f"📅 Source: {result.get('source', 'unknown')}")
            print(f"🕐 Generated at: {result.get('generated_at', 'unknown')}")
            
            # Check if it has the expected structure
            if "week_plan" in meal_plan:
                week_plan = meal_plan["week_plan"]
                print(f"📋 Week plan structure: {list(week_plan.keys())}")
                
                # Check a sample day
                if "monday" in week_plan:
                    monday = week_plan["monday"]
                    print(f"🌅 Monday meals: {list(monday.keys())}")
                    
                    if "breakfast" in monday:
                        breakfast = monday["breakfast"]
                        print(f"🍳 Breakfast details:")
                        print(f"   Name: {breakfast.get('name', 'N/A')}")
                        print(f"   Ingredients: {breakfast.get('ingredients', [])}")
                        print(f"   Instructions: {breakfast.get('instructions', 'N/A')}")
                        print(f"   Cooking time: {breakfast.get('cooking_time', 'N/A')}")
                        print(f"   Nutrition: {breakfast.get('nutrition', {})}")
            
            return True
        else:
            print("\n❌ Unexpected result format")
            print(f"Result keys: {list(result.keys())}")
            return False
            
    except Exception as e:
        print(f"\n💥 Error testing meal planner: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Updated Meal Planner Test")
    print("=" * 50)
    
    success = test_updated_meal_planner()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("✅ The updated meal planner is working correctly")
    else:
        print("\n❌ Test failed!")
        print("🔧 There may be an issue with the updated meal planner")
    
    print("\n" + "=" * 50)
