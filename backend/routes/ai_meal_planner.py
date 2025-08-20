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
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    # TEMPORARY: For testing, allow any user ID
    # TODO: Restore proper JWT authentication
    user_id = "test@example.com"  # Use a test user ID that exists in preferences
    
    # Get user from JWT token (commented out for testing)
    # auth_header = request.headers.get('Authorization')
    # if not auth_header:
    #     response = jsonify({'error': 'No authorization header provided'})
    #     response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
    #     response.headers.add('Access-Control-Allow-Credentials', 'true')
    #     return response, 401
    
    # try:
    #     # Extract token from "Bearer <token>"
    #     if not auth_header.startswith('Bearer '):
    #         response = jsonify({'error': 'Invalid authorization header format'})
    #         response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
    #         response.headers.add('Access-Control-Allow-Credentials', 'true')
    #         return response, 401
        
    #     token = auth_header.split(' ')[1]
    #     if not token or token in ['null', 'undefined']:
    #         response = jsonify({'error': 'Invalid token'})
    #         response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
    #         response.headers.add('Access-Control-Allow-Credentials', 'true')
    #         return response, 401
        
    #     # Decode and verify JWT token
    #     payload = user_service.decode_jwt_token(token)
    #     if not payload:
    #         response = jsonify({'error': 'Invalid or expired token'})
    #         response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
    #         response.headers.add('Access-Control-Allow-Credentials', 'true')
    #         return response, 401
        
    #     user_id = payload.get('user_id') or payload.get('sub') or payload.get('email')
    #     if not user_id:
    #         response = jsonify({'error': 'Invalid token payload'})
    #         response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
    #         response.headers.add('Access-Control-Allow-Credentials', 'true')
    #         return response, 401
            
    # except Exception as e:
    #     response = jsonify({'error': f'Authentication failed: {str(e)}'})
    #     response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
    #     response.headers.add('Access-Control-Allow-Credentials', 'true')
    #     return response, 500

    # Get preferences from user profile
    preferences = user_preferences_service.get_preferences(user_id)
    if not preferences:
        response = jsonify({'error': 'No preferences found for user'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 404
    
    # Get preferences from request body
    data = request.get_json() or {}
    preferences = data.get('preferences', {})
    
    # If no preferences in request, use the ones from user profile
    if not preferences:
        preferences = user_preferences_service.get_preferences(user_id)
    
    # Get additional parameters from request
    budget = data.get('budget')
    dietary_goals = data.get('dietary_goals', [])
    currency = data.get('currency', '$')

    # Call the LLM service
    try:
        # Generate the meal plan using the free LLM meal planner agent
        result = free_llm_meal_planner.generate_weekly_meal_plan(user_id)
        
        # Check if the LLM agent returned an error
        if 'error' in result:
            response = jsonify({'error': result['error']})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response, 500
        
        # Check if the result has the expected structure
        if not result.get('success') or 'meal_plan' not in result:
            response = jsonify({'error': 'Invalid response structure from LLM agent'})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response, 500
        
        # Extract the actual meal plan from the result
        meal_plan = result.get('meal_plan', {})
        
        # Return the meal plan in the expected format
        response = jsonify({
            'success': True,
            'meal_plan': meal_plan
        })
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 500
