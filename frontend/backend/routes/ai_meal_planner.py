# AI Meal Planner Route for Full-Stack Recipe App
# Uses Llama 3.2 (or compatible) LLM API to generate a meal plan based on user preferences

from flask import Blueprint, jsonify, session, request
from flask_cors import cross_origin
from ..services.user_preferences_service import UserPreferencesService
import os
import requests
from functools import wraps

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
@cross_origin(origins=['http://localhost:8081'], 
              methods=['POST', 'OPTIONS'],
              allow_headers=['Content-Type', 'Authorization'],
              supports_credentials=True)
def ai_meal_plan():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    # Get user from session
    user_id = session.get('user_email')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    # Get preferences from user profile
    preferences = user_preferences_service.get_preferences(user_id)
    if not preferences:
        return jsonify({'error': 'No preferences found for user'}), 404
    
    # Get budget and dietary goals from request
    data = request.get_json() or {}
    budget = data.get('budget')
    dietary_goals = data.get('dietary_goals', [])
    currency = data.get('currency', '$')

    # Build Llama prompt with all parameters
    prompt = build_llama_prompt(
        preferences,
        budget=float(budget) if budget is not None else None,
        dietary_goals=dietary_goals,
        currency=currency
    )

    llama_payload = {
        "model": "llama-3-70b-instruct",  # Update as needed
        "messages": [
            {"role": "system", "content": "You are a helpful, expert meal planner and chef."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1200,
        "temperature": 0.7
    }
    headers = {
        "Content-Type": "application/json"
    }
    if LLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {LLAMA_API_KEY}"

    try:
        # Call Llama API
        response = requests.post(
            LLAMA_API_URL,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {LLAMA_API_KEY}'
            },
            json=llama_payload
        )

        if response.status_code != 200:
            return jsonify({'error': 'Failed to generate meal plan'}), 500

        data = response.json()
        # Llama API: response['choices'][0]['message']['content']
        meal_plan = data['choices'][0]['message']['content']
        return jsonify({'meal_plan': meal_plan})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
