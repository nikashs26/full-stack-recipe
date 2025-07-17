from flask import Blueprint, request, jsonify, session
import logging
from services.llm_meal_planner_agent import LLMMealPlannerAgent
from services.user_preferences_service import UserPreferencesService
from middleware.auth_middleware import require_auth, get_current_user_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

meal_planner_bp = Blueprint('meal_planner', __name__)

# Initialize services
user_preferences_service = UserPreferencesService()
llm_meal_planner_agent = LLMMealPlannerAgent()

@meal_planner_bp.route('/meal-plan/generate', methods=['GET', 'POST'])
@require_auth
def generate_meal_plan():
    """Generate comprehensive weekly meal plan using LLM (requires authentication)"""
    
    try:
        logger.info("Generating meal plan request received")
        
        # Get authenticated user ID
        user_id = get_current_user_id()
        logger.info(f"Generating meal plan for user: {user_id}")
        
        # Get preferences from ChromaDB for authenticated user
        preferences = user_preferences_service.get_preferences(user_id)
        if not preferences:
            return jsonify({
                "error": "No preferences found. Please set your preferences first.",
                "redirect_to": "/preferences"
            }), 400
        
        logger.info(f"Using preferences for user {user_id}: {list(preferences.keys())}")
        
        # Generate meal plan using LLM agent
        result = llm_meal_planner_agent.generate_weekly_meal_plan(preferences)
        
        if "error" in result:
            logger.error(f"Meal plan generation failed: {result['error']}")
            return jsonify({"error": result["error"]}), 500
        
        logger.info("Meal plan generated successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Exception in generate_meal_plan: {str(e)}")
        return jsonify({"error": f"Failed to generate meal plan: {str(e)}"}), 500

@meal_planner_bp.route('/meal-plan/regenerate-meal', methods=['POST'])
@require_auth  
def regenerate_specific_meal():
    """Regenerate a specific meal in the plan (requires authentication)"""
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get authenticated user ID
        user_id = get_current_user_id()
        
        day = data.get('day')
        meal_type = data.get('meal_type') 
        current_plan = data.get('current_plan', {})
        
        if not day or not meal_type:
            return jsonify({"error": "Day and meal_type are required"}), 400
        
        logger.info(f"Regenerating {meal_type} for {day} for user {user_id}")
        
        # Regenerate specific meal
        result = llm_meal_planner_agent.regenerate_specific_meal(user_id, day, meal_type, current_plan)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 500
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Exception in regenerate_specific_meal: {str(e)}")
        return jsonify({"error": f"Failed to regenerate meal: {str(e)}"}), 500

@meal_planner_bp.route('/meal-plan/recipe-suggestions', methods=['POST'])
def get_recipe_suggestions():
    """Get LLM-powered recipe suggestions for a specific meal type"""
    
    data = request.get_json()
    if not data or 'mealType' not in data:
        return jsonify({"error": "Missing required field: mealType"}), 400
    
    try:
        meal_type = data['mealType']
        preferences = data.get('preferences', {})
        count = data.get('count', 5)
        
        logger.info(f"Getting {count} recipe suggestions for {meal_type}")
        
        if not preferences:
            logger.warning("No preferences provided for recipe suggestions")
            return jsonify({"error": "No preferences provided"}), 400
        
        recipes = llm_meal_planner_agent.get_recipe_suggestions(meal_type, preferences, count)
        
        return jsonify({
            "success": True,
            "recipes": recipes,
            "meal_type": meal_type,
            "count": len(recipes)
        }), 200
        
    except Exception as e:
        logger.error(f"Exception in get_recipe_suggestions: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@meal_planner_bp.route('/meal-plan/health-check', methods=['GET'])
def health_check():
    """Health check endpoint for meal planner service"""
    
    try:
        # Test if services are working
        test_preferences = {
            "dietary_restrictions": ["vegetarian"],
            "favorite_cuisines": ["Mediterranean"],
            "allergies": [],
            "cooking_time": "medium",
            "skill_level": "intermediate"
        }
        
        # Test the LLM agent (this will use fallback if LLM is not available)
        plan_result = llm_meal_planner_agent.generate_weekly_meal_plan(test_preferences)
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "llm_available": plan_result.get("plan_type") == "llm_generated",
            "fallback_working": plan_result.get("plan_type") == "rule_based_fallback",
            "services": {
                "llm_meal_planner_agent": "working",
                "user_preferences_service": "working"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500 