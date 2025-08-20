#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import logging
from services.free_llm_meal_planner import FreeLLMMealPlannerAgent

# Setup logging to see debug output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_meal_planner():
    logger.info("🧪 Testing meal planner agent...")
    
    # Mock user preferences service (we don't need it for this test)
    class MockUserPreferencesService:
        def get_preferences(self, user_id):
            return {}
    
    # Create agent
    agent = FreeLLMMealPlannerAgent(MockUserPreferencesService())
    
    # Test preferences with just 2 cuisines for better focus
    test_preferences = {
        'favoriteCuisines': ['Italian', 'Thai'],
        'dietaryRestrictions': [],
        'allergens': [],
        'cookingSkillLevel': 'intermediate',
        'maxCookingTime': '45 minutes',
        'targetCalories': 2000,
        'targetProtein': 150,
        'targetCarbs': 200,
        'targetFat': 65
    }
    
    logger.info(f"🎯 Using test preferences: {test_preferences}")
    
    # Generate meal plan
    result = agent.generate_weekly_meal_plan_with_preferences("test_user", test_preferences)
    
    logger.info(f"📊 Result type: {type(result)}")
    logger.info(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
    
    if result.get('success'):
        logger.info("✅ Agent returned successful result")
        meal_plan = result.get('meal_plan', {})
        logger.info(f"📋 Meal plan keys: {list(meal_plan.keys()) if isinstance(meal_plan, dict) else 'Not a dict'}")
        if 'days' in meal_plan:
            logger.info(f"📅 Number of days: {len(meal_plan['days'])}")
            if meal_plan['days']:
                first_day = meal_plan['days'][0]
                logger.info(f"📅 First day structure: {list(first_day.keys()) if isinstance(first_day, dict) else 'Not a dict'}")
    else:
        logger.error(f"❌ Agent failed: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    result = test_meal_planner()
    print("\n" + "="*50)
    print("FINAL RESULT:")
    print("="*50)
    print(result)
