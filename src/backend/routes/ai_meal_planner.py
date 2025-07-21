# AI Meal Planner Route for Full-Stack Recipe App
# Uses Llama 3.2 (or compatible) LLM API to generate a meal plan based on user preferences

from flask import Blueprint, request, jsonify, session
from services.user_preferences_service import UserPreferencesService
import os
import requests

ai_meal_planner_bp = Blueprint('ai_meal_planner', __name__)
user_preferences_service = UserPreferencesService()

LLAMA_API_URL = os.environ.get('LLAMA_API_URL', 'http://localhost:8000/v1/chat/completions')
LLAMA_API_KEY = os.environ.get('LLAMA_API_KEY', '')


def build_llama_prompt(preferences):
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

    prompt = (
        f"You are an expert meal planner and chef. Build a detailed, delicious, and realistic weekly meal plan for a user with the following preferences. "
        f"Be creative, but respect all restrictions. For each day, suggest breakfast, lunch, dinner, and a snack. They should serve to make a proper full day of eating for most indiviuals "
        f"Use cuisines: {', '.join(cuisines) if cuisines else 'any'}. "
        f"Dietary restrictions: {', '.join(dietary) if dietary else 'none'}. "
        f"Allergens to avoid: {', '.join(allergens) if allergens else 'none'}. "
        f"Cooking skill: {skill or 'any'}. "
        f"Favorite foods: {', '.join(favorite_foods) if favorite_foods else 'none'}. "
        f"Health goals: {', '.join(health_goals) if health_goals else 'none'}. "
        f"Max cooking time per meal: {max_time or 'any'}. "
        f"Respond in clear markdown. Add a short summary at the top about why you chose these meals."
    )
    return prompt


@ai_meal_planner_bp.route('/ai/meal_plan', methods=['POST'])
def ai_meal_plan():
    # Get user from session
    user_id = session.get('user_email')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    preferences = user_preferences_service.get_preferences(user_id)
    if not preferences:
        return jsonify({'error': 'No preferences found for user'}), 404

    # Build Llama prompt
    prompt = build_llama_prompt(preferences)

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
        response = requests.post(LLAMA_API_URL, json=llama_payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        # Llama API: response['choices'][0]['message']['content']
        meal_plan = data['choices'][0]['message']['content']
        return jsonify({'meal_plan': meal_plan})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
