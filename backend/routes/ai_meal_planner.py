# AI Meal Planner Route for Full-Stack Recipe App
# Uses Llama 3.2 (or compatible) LLM API to generate a meal plan based on user preferences

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from services.user_preferences_service import UserPreferencesService
from services.free_llm_meal_planner import FreeLLMMealPlannerAgent
from services.user_service import UserService
import os
import requests

ai_meal_planner_bp = Blueprint('ai_meal_planner', __name__)
user_preferences_service = UserPreferencesService()
user_service = UserService()

# Initialize the free LLM meal planner agent
free_llm_meal_planner = FreeLLMMealPlannerAgent(user_preferences_service)

LLAMA_API_URL = os.environ.get('LLAMA_API_URL', 'http://localhost:8000/v1/chat/completions')
LLAMA_API_KEY = os.environ.get('LLAMA_API_KEY', '')


# Note: This route uses FreeLLMMealPlannerAgent which has its own prompt generation


@ai_meal_planner_bp.route('/ai/meal_plan', methods=['POST', 'OPTIONS'])
def ai_meal_plan():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    # Get data from request body
    data = request.get_json() or {}
    preferences = data.get('preferences', {})
    
    # If no preferences provided, use default preferences
    if not preferences:
        preferences = {
            'favoriteCuisines': ['American', 'Italian'],
            'dietaryRestrictions': [],
            'allergens': [],
            'favoriteFoods': [],
            'cookingSkillLevel': 'beginner',
            'maxCookingTime': '30 minutes',
            'targetCalories': 2000,
            'targetProtein': 150,
            'targetCarbs': 200,
            'targetFat': 65,
            'includeBreakfast': True,
            'includeLunch': True,
            'includeDinner': True,
            'includeSnacks': False
        }
    
    print(f"🎯 Using preferences for meal planning: {preferences}")  # Debug log
    
    # Get additional parameters from request
    budget = data.get('budget')
    dietary_goals = data.get('dietary_goals', [])
    currency = data.get('currency', '$')

    # Call the LLM service
    try:
        # Generate the meal plan using the free LLM meal planner agent WITH preferences
        # Use a generic user_id for public access
        result = free_llm_meal_planner.generate_weekly_meal_plan_with_preferences("public_user", preferences)
        
        # Check if the LLM agent returned an error
        if 'error' in result:
            response = jsonify({'error': result['error']})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response, 500
        
        # Check if the result has the expected structure
        if not result.get('success') or 'meal_plan' not in result:
            response = jsonify({'error': 'Invalid response structure from LLM agent'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response, 500
        
        # Extract the actual meal plan from the result
        meal_plan = result.get('meal_plan', {})
        
        # Return the meal plan in the expected format
        response = jsonify({
            'success': True,
            'meal_plan': meal_plan,
            'message': 'Meal plan generated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 500
