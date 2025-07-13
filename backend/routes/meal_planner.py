from flask import Blueprint, request, jsonify, session
import logging
from services.meal_planner_agent import MealPlannerAgent
from services.user_preferences_service import UserPreferencesService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

meal_planner_bp = Blueprint('meal_planner', __name__)

# Initialize services
user_preferences_service = UserPreferencesService()
meal_planner_agent = MealPlannerAgent(user_preferences_service, None)

@meal_planner_bp.route('/meal-plan/generate', methods=['GET', 'POST'])
def generate_meal_plan():
    """Generate comprehensive weekly meal plan using LLM with session-based preferences"""
    
    try:
        logger.info("Generating meal plan request received")
        
        # Get preferences from request or session
        if request.method == 'POST':
            data = request.get_json() or {}
            preferences = data.get('preferences', {})
            
            if preferences:
                logger.info(f"Using provided preferences: {list(preferences.keys())}")
                # Use the preferences directly for meal plan generation
                plan_result = meal_planner_agent.generate_meal_plan_with_preferences(preferences)
                
                if "error" in plan_result:
                    logger.error(f"Error generating meal plan: {plan_result['error']}")
                    return jsonify({
                        "success": False,
                        "error": plan_result["error"]
                    }), 400
                    
                return jsonify({
                    "success": True,
                    "meal_plan": plan_result,
                    "llm_used": plan_result.get("plan_type", "unknown"),
                    "preferences_used": preferences,
                    "generated_at": plan_result.get("generated_at"),
                    "total_recipes": plan_result.get("week_summary", {}).get("total_recipes", 0)
                }), 200
            else:
                logger.warning("No preferences provided in POST request")
                return jsonify({
                    "success": False,
                    "error": "No preferences found. Please set your preferences first."
                }), 400
        else:
            # GET request - try to use session preferences
            print(f'🔥 MEAL_PLANNER_ROUTE: GET request - checking session')
            print(f'🔥 MEAL_PLANNER_ROUTE: Session contents: {dict(session)}')
            
            if 'temp_user_id' not in session:
                logger.warning("No temp_user_id in session")
                print(f'🔥 MEAL_PLANNER_ROUTE: No temp_user_id in session')
                return jsonify({
                    "success": False,
                    "error": "No preferences found. Please set your preferences first."
                }), 400
            
            user_id = session['temp_user_id']
            logger.info(f"Using session preferences for user: {user_id}")
            print(f'🔥 MEAL_PLANNER_ROUTE: Using session preferences for user: {user_id}')
            preferences = user_preferences_service.get_preferences(user_id)
            
            if not preferences:
                logger.warning(f"No preferences found for user: {user_id}")
                return jsonify({
                    "success": False,
                    "error": "Preferences not found. Please set your preferences first."
                }), 400
            
            plan_result = meal_planner_agent.generate_meal_plan_with_preferences(preferences)
            
            if "error" in plan_result:
                logger.error(f"Error generating meal plan: {plan_result['error']}")
                return jsonify({
                    "success": False,
                    "error": plan_result["error"]
                }), 400
                
            return jsonify({
                "success": True,
                "meal_plan": plan_result,
                "llm_used": plan_result.get("plan_type", "unknown"),
                "preferences_used": preferences,
                "generated_at": plan_result.get("generated_at"),
                "total_recipes": plan_result.get("week_summary", {}).get("total_recipes", 0)
            }), 200
        
    except Exception as e:
        logger.error(f"Exception in generate_meal_plan: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@meal_planner_bp.route('/meal-plan/regenerate-meal', methods=['POST'])
def regenerate_meal():
    """Regenerate specific meal using LLM"""
    
    data = request.get_json()
    if not data or 'day' not in data or 'mealType' not in data:
        return jsonify({"error": "Missing required fields: day, mealType"}), 400

    try:
        logger.info(f"Regenerating meal for {data['day']} {data['mealType']}")
        
        # Get preferences from request
        preferences = data.get('preferences', {})
        
        if not preferences:
            logger.warning("No preferences provided for meal regeneration")
            return jsonify({"error": "No preferences provided"}), 400
        
        # Use LLM to get recipe suggestions for the specific meal type
        meal_type = data['mealType']
        recipes = meal_planner_agent.get_recipe_suggestions(meal_type, preferences, count=1)
        
        if recipes:
            new_meal = recipes[0]
            logger.info(f"Successfully regenerated {meal_type} meal: {new_meal.get('name', 'Unknown')}")
            return jsonify({
                "success": True,
                "meal": new_meal,
                "generated_with": "llm_recipe_suggestions"
            }), 200
        else:
            # Fall back to generating a full plan and extracting the meal
            logger.info("Falling back to full meal plan generation")
            plan_result = meal_planner_agent.generate_meal_plan_with_preferences(preferences)
            
            if "error" in plan_result:
                return jsonify({"error": plan_result["error"]}), 400
            
            day = data['day']
            meal_type = data['mealType']
            
            # Look for the day in the plan
            for day_plan in plan_result.get("days", []):
                if day_plan.get("day", "").lower() == day.lower():
                    if meal_type in day_plan.get("meals", {}):
                        new_meal = day_plan["meals"][meal_type]
                        return jsonify({
                            "success": True,
                            "meal": new_meal,
                            "generated_with": "full_plan_extraction"
                        }), 200
            
            return jsonify({"error": "Could not generate meal for specified day and type"}), 400
            
    except Exception as e:
        logger.error(f"Exception in regenerate_meal: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

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
        
        recipes = meal_planner_agent.get_recipe_suggestions(meal_type, preferences, count)
        
        return jsonify({
            "success": True,
            "recipes": recipes,
            "meal_type": meal_type,
            "count": len(recipes)
        }), 200
        
    except Exception as e:
        logger.error(f"Exception in get_recipe_suggestions: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@meal_planner_bp.route('/meal-plan/set-preferences', methods=['POST'])
def set_preferences():
    """Set meal planning preferences without authentication (for testing)"""
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No preferences provided"}), 400
    
    demo_user_id = "demo_user"
    
    try:
        logger.info(f"Setting preferences for demo user: {list(data.keys())}")
        user_preferences_service.save_preferences(demo_user_id, data)
        return jsonify({"success": True, "message": "Preferences saved successfully"}), 200
    except Exception as e:
        logger.error(f"Exception in set_preferences: {str(e)}")
        return jsonify({"error": f"Failed to save preferences: {str(e)}"}), 500

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
        plan_result = meal_planner_agent.generate_meal_plan_with_preferences(test_preferences)
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "llm_available": plan_result.get("plan_type") == "llm_generated",
            "fallback_working": plan_result.get("plan_type") == "rule_based_fallback",
            "services": {
                "meal_planner_agent": "working",
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