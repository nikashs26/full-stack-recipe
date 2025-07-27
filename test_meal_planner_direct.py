#!/usr/bin/env python3
"""Direct test of the meal planner with fallback"""

import sys
import json
from backend.services.llm_meal_planner_agent import LLMMealPlannerAgent

def test_meal_planner():
    # Test preferences
    preferences = {
        'dietary_restrictions': [],
        'favorite_cuisines': ['Mediterranean', 'Asian'],
        'target_calories': 2200,
        'target_protein': 180,
        'target_carbs': 200,
        'target_fat': 70,
        'include_breakfast': True,
        'include_lunch': True,
        'include_dinner': True,
        'include_snacks': True
    }
    
    print("🚀 Testing Meal Planner...")
    print("📋 Preferences:", json.dumps(preferences, indent=2))
    
    # Initialize the meal planner
    print("\n🔧 Initializing meal planner...")
    meal_planner = LLMMealPlannerAgent()
    
    # Force fallback for testing
    print("\n🍽️  Generating meal plan (using fallback)...")
    meal_plan = meal_planner._generate_fallback_meal_plan(preferences)
    
    # Save the full response
    with open('test_meal_plan.json', 'w') as f:
        json.dump(meal_plan, f, indent=2)
    
    # Print summary
    print("\n✅ Meal Plan Generated Successfully!")
    print_meal_plan_summary(meal_plan)
    
    print("\n📄 Full meal plan saved to 'test_meal_plan.json'")

def print_meal_plan_summary(meal_plan):
    print("\n📅 Days in Plan:", len(meal_plan.get('days', [])))
    
    # Calculate and print nutrition summary
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    meal_count = 0
    
    for day in meal_plan.get('days', []):
        for meal in day.get('meals', []):
            nutrition = meal.get('nutrition', {})
            total_calories += nutrition.get('calories', 0)
            total_protein += nutrition.get('protein', 0)
            total_carbs += nutrition.get('carbs', 0)
            total_fat += nutrition.get('fat', 0)
            meal_count += 1
    
    days = max(1, len(meal_plan.get('days', [])))
    avg_daily_calories = total_calories / days
    avg_daily_protein = total_protein / days
    avg_daily_carbs = total_carbs / days
    avg_daily_fat = total_fat / days
    
    print("\n📊 Nutrition Summary (Daily Averages):")
    print(f"  • Calories: {round(avg_daily_calories)} kcal")
    print(f"  • Protein: {avg_daily_protein:.1f}g")
    print(f"  • Carbs: {avg_daily_carbs:.1f}g")
    print(f"  • Fat: {avg_daily_fat:.1f}g")
    
    # Print sample day
    if meal_plan.get('days'):
        sample_day = meal_plan['days'][0]
        print("\n📝 Sample Day (Monday):\n")
        
        for meal in sample_day.get('meals', []):
            nutrition = meal.get('nutrition', {})
            print(f"🍽️  {meal['meal_type'].upper()}:")
            print(f"   {meal['name']} ({meal.get('cuisine', 'International')})")
            print(f"   🥗 Nutrition:")
            print(f"      • Calories: {nutrition.get('calories', 'N/A')} kcal")
            print(f"      • Protein: {nutrition.get('protein', 'N/A'):.1f}g")
            print(f"      • Carbs: {nutrition.get('carbs', 'N/A'):.1f}g")
            print(f"      • Fat: {nutrition.get('fat', 'N/A'):.1f}g")
            
            # Print first 3 ingredients as a preview
            ingredients = meal.get('ingredients', [])
            if ingredients and isinstance(ingredients, list):
                print("   🛒 Ingredients (sample):")
                for ing in ingredients[:3]:
                    if isinstance(ing, dict):
                        print(f"      • {ing.get('name', 'Ingredient')}: {ing.get('amount', '')}")
                    else:
                        print(f"      • {ing}")
                if len(ingredients) > 3:
                    print(f"      • ... and {len(ingredients) - 3} more")
            print()  # Add space between meals
    
    print("\n🛒 Shopping List Preview:")
    if 'shopping_list' in meal_plan and 'ingredients' in meal_plan['shopping_list']:
        ingredients = meal_plan['shopping_list']['ingredients']
        if isinstance(ingredients, list) and len(ingredients) > 0:
            # Handle both list of strings and list of dicts
            if isinstance(ingredients[0], dict):
                # Extract ingredient names from dicts
                ingredient_names = [ing.get('name', 'ingredient') for ing in ingredients[:5]]
            else:
                ingredient_names = ingredients[:5]
            print(f"Total items: {len(ingredients)}")
            print("Sample items:", ", ".join(ingredient_names))
        else:
            print("No ingredients found in shopping list")
    
    print("\n📄 Full meal plan saved to 'test_meal_plan.json'")

if __name__ == "__main__":
    test_meal_planner()
