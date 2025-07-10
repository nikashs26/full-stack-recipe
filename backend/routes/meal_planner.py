from flask import Blueprint, request, jsonify
from services.meal_planner_agent import MealPlannerAgent, RecipeServicePlaceholder
from services.user_preferences_service import UserPreferencesService
from auth import require_auth  # Assuming you have an auth decorator

meal_planner_bp = Blueprint('meal_planner', __name__)

# Initialize services
user_preferences_service = UserPreferencesService()
# IMPORTANT: Replace RecipeServicePlaceholder with your actual recipe fetching logic
# This could be your MongoDB connection or another service that gets all recipes.
recipe_service = RecipeServicePlaceholder() 
meal_planner_agent = MealPlannerAgent(user_preferences_service, recipe_service)

@meal_planner_bp.route('/meal-plan/generate', methods=['GET'])
@require_auth
def generate_meal_plan():
    user_id = request.usexr_id  # Get user_id from your authentication token/middleware
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        plan_result = meal_planner_agent.generate_weekly_plan(user_id)
        if "error" in plan_result:
            return jsonify(plan_result), 400 # Return error from agent logic
        return jsonify(plan_result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500 