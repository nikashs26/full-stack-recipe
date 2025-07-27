import os
import sys
import json
from services.llm_meal_planner_agent import LLMMealPlannerAgent

def test_meal_planner():
    # Create test preferences
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
    
    # Initialize the meal planner
    print("🚀 Initializing LLM Meal Planner...")
    meal_planner = LLMMealPlannerAgent()
    
    # Generate the meal plan
    print("🍳 Generating meal plan...")
    try:
        meal_plan = meal_planner.generate_weekly_meal_plan(preferences)
        
        # Save the full response for inspection
        with open('test_meal_plan.json', 'w') as f:
            json.dump(meal_plan, f, indent=2)
        
        # Print a summary
        print("\n✅ Meal Plan Generated Successfully!")
        
        # Handle both list and dict formats for days
        days = meal_plan.get('days', [])
        if isinstance(days, dict):
            days = list(days.values())
        
        print(f"📅 Days: {len(days)}")
        
        # Print nutrition summary
        if 'nutrition_summary' in meal_plan:
            print("\n📊 Nutrition Summary:")
            if 'daily_average' in meal_plan['nutrition_summary']:
                print(f"Daily Calories: {meal_plan['nutrition_summary']['daily_average'].get('calories')}")
                print(f"Daily Protein: {meal_plan['nutrition_summary']['daily_average'].get('protein')}g")
            else:
                print(f"Daily Calories: {meal_plan['nutrition_summary'].get('calories')}")
                print(f"Daily Protein: {meal_plan['nutrition_summary'].get('protein')}g")
        
        print("\n📝 Sample Day (Monday):")
        if days:
            monday = next((day for day in days if day.get('day') == 'Monday'), days[0] if days else None)
            if monday:
                meals = monday.get('meals', {})
                if isinstance(meals, list):
                    # Handle list format
                    for meal in meals:
                        if isinstance(meal, dict):
                            print(f"\n{meal.get('meal_type', 'MEAL').upper()}:")
                            print(f"  {meal.get('name')}")
                            print(f"  Calories: {meal.get('calories')}")
                            print(f"  Protein: {meal.get('protein')}g")
                            print(f"  Carbs: {meal.get('carbs')}g")
                            print(f"  Fat: {meal.get('fat')}g")
                else:
                    # Handle dict format
                    for meal_type, meal in meals.items():
                        if isinstance(meal, dict):
                            print(f"\n{meal_type.upper()}:")
                            print(f"  {meal.get('name')}")
                            print(f"  Calories: {meal.get('calories')}")
                            print(f"  Protein: {meal.get('protein')}g")
                            print(f"  Carbs: {meal.get('carbs')}g")
                            print(f"  Fat: {meal.get('fat')}g")
        
        print("\n🛒 Shopping List Preview:")
        if 'shopping_list' in meal_plan and 'ingredients' in meal_plan['shopping_list']:
            print(f"Total items: {len(meal_plan['shopping_list']['ingredients'])}")
            print("Sample items:", ", ".join(meal_plan['shopping_list']['ingredients'][:5]))
        
        print("\n📄 Full meal plan saved to 'test_meal_plan.json'")
        
    except Exception as e:
        print(f"❌ Error generating meal plan: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_meal_planner()
