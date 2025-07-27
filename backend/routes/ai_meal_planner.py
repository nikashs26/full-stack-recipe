# AI Meal Planner Route for Full-Stack Recipe App
# Uses Llama 3.2 (or compatible) LLM API to generate a meal plan based on user preferences

from flask import Blueprint, jsonify, session, request
from flask_cors import cross_origin
from services.user_preferences_service import UserPreferencesService
import os
import requests

ai_meal_planner_bp = Blueprint('ai_meal_planner', __name__)
user_preferences_service = UserPreferencesService()

LLAMA_API_URL = os.environ.get('LLAMA_API_URL', 'http://localhost:8000/v1/chat/completions')
LLAMA_API_KEY = os.environ.get('LLAMA_API_KEY', '')


def build_llama_prompt(preferences, budget=None, dietary_goals=None, currency='$'):
    """
    Build a Llama 3.2 prompt for meal planning, using all user preferences.
    """
    dietary = preferences.get('dietaryRestrictions', [])
    cuisines = preferences.get('favoriteCuisines', [])
    allergens = preferences.get('allergens', [])
    skill = preferences.get('cookingSkillLevel', '')
    favorite_foods = preferences.get('favoriteFoods', [])
    health_goals = preferences.get('healthGoals', [])
    max_time = preferences.get('maxCookingTime', '')
    
    # Add dietary goals to health goals if provided
    if dietary_goals:
        health_goals = list(set(health_goals + dietary_goals))

    prompt_parts = [
        "You are an expert meal planner and chef. Build a detailed, delicious, and realistic weekly meal plan for a user with the following preferences. "
        "Be creative, but respect all restrictions. For each day, suggest breakfast, lunch, dinner, and a snack. "
        "They should serve to make a proper full day of eating for most individuals. "
        "For each meal, include a name, description, cuisine type, cooking time, difficulty level, and ingredients list. "
        "Also include an estimated cost per serving and total cost for each meal.",
        "",
        "User Preferences:",
        f"- Cuisines: {', '.join(cuisines) if cuisines else 'Any'}",
        f"- Dietary Restrictions: {', '.join(dietary) if dietary else 'None'}",
        f"- Allergens to avoid: {', '.join(allergens) if allergens else 'None'}",
        f"- Cooking skill: {skill or 'Any'}",
        f"- Favorite foods: {', '.join(favorite_foods) if favorite_foods else 'None'}",
        f"- Health goals: {', '.join(health_goals) if health_goals else 'None'}",
        f"- Max cooking time per meal: {max_time or 'Any'}",
    ]
    
    # Add budget information if provided
    if budget is not None:
        prompt_parts.append(f"- Weekly food budget: {currency}{budget} (approximately {currency}{budget/21:.2f} per meal)")
    
    # Add dietary goals if provided
    if dietary_goals:
        prompt_parts.append(f"- Specific dietary goals: {', '.join(dietary_goals)}")
    
    prompt_parts.extend([
        "",
        "Response Format (in markdown):",
        "1. A brief summary of the meal plan and how it meets the user's preferences",
        "2. For each day of the week:",
        "   - Day Name",
        "   - Breakfast: Name, Description, Cuisine, Time, Difficulty, Cost per serving, Ingredients",
        "   - Lunch: [same structure]",
        "   - Dinner: [same structure]",
        "   - Snack: [same structure]"
    ])
    
    return "\n".join(prompt_parts)


@ai_meal_planner_bp.route('/ai/meal_plan', methods=['POST', 'OPTIONS'])
def ai_meal_plan():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    # Get user from session
    user_id = session.get('user_email')
    if not user_id:
        response = jsonify({'error': 'Not logged in'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 401

    # Get preferences from user profile
    preferences = user_preferences_service.get_preferences(user_id)
    if not preferences:
        response = jsonify({'error': 'No preferences found for user'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 404
    
    # Get budget and dietary goals from request
    data = request.get_json() or {}
    budget = data.get('budget')
    dietary_goals = data.get('dietary_goals', [])
    currency = data.get('currency', '$')

    # Build Llama prompt with all parameters
    # Call the LLM service
    try:
        # Initialize the meal planner agent
        meal_planner = LLMMealPlannerAgent()
        
        # Prepare preferences for the meal planner
        meal_plan_preferences = {
            **preferences,
            'budget': request.json.get('budget'),
            'dietaryGoals': request.json.get('dietary_goals', []),
            'currency': request.json.get('currency', '$'),
            'mealPreferences': request.json.get('meal_preferences', {
                'includeBreakfast': True,
                'includeLunch': True,
                'includeDinner': True,
                'includeSnacks': True
            }),
            'nutritionTargets': request.json.get('nutrition_targets', {
                'calories': 2000,
                'protein': 150,
                'carbs': 200,
                'fat': 65
            })
        }
        
        # Generate the meal plan
        meal_plan = meal_planner.generate_weekly_meal_plan(meal_plan_preferences)
        
        # Return the meal plan in the expected format
        response = jsonify({
            'success': True,
            'data': meal_plan
        })
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 500
