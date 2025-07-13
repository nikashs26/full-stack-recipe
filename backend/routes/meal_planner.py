from flask import Blueprint, request, jsonify, session
from services.free_llm_meal_planner import FreeLLMMealPlannerAgent
from services.user_preferences_service import UserPreferencesService

meal_planner_bp = Blueprint('meal_planner', __name__)

# Initialize services
user_preferences_service = UserPreferencesService()
meal_planner_agent = FreeLLMMealPlannerAgent(user_preferences_service)

@meal_planner_bp.route('/meal-plan/generate', methods=['GET', 'POST'])
def generate_meal_plan():
    """Generate meal plan using session-based temporary preferences"""
    
    try:
        # Get user ID from session or create one
        if 'temp_user_id' not in session:
            # If no session, try to get preferences from request
            if request.method == 'POST':
                data = request.get_json() or {}
                preferences = data.get('preferences', {})
                
                if preferences:
                    # Create a temporary user ID and save preferences
                    import uuid
                    temp_user_id = f"temp_user_{str(uuid.uuid4())[:8]}"
                    session['temp_user_id'] = temp_user_id
                    
                    # Set defaults for missing fields
                    default_preferences = {
                        "dietaryRestrictions": [],
                        "favoriteCuisines": ["International", "Mediterranean", "Asian"],
                        "allergens": [],
                        "cookingSkillLevel": "beginner",
                        "healthGoals": ["General wellness"],
                        "maxCookingTime": "30 minutes"
                    }
                    
                    # Merge provided preferences with defaults
                    for key, value in default_preferences.items():
                        if key not in preferences:
                            preferences[key] = value
                    
                    # Save to ChromaDB
                    user_preferences_service.save_preferences(temp_user_id, preferences)
                else:
                    return jsonify({
                        "error": "No preferences found. Please set your preferences first using /api/temp-preferences/demo or /api/temp-preferences"
                    }), 400
            else:
                return jsonify({
                    "error": "No preferences found. Please set your preferences first using /api/temp-preferences/demo or /api/temp-preferences"
                }), 400
        
        # Get the user ID from session
        user_id = session['temp_user_id']
        
        # Verify preferences exist in ChromaDB
        preferences = user_preferences_service.get_preferences(user_id)
        if not preferences:
            return jsonify({
                "error": "Preferences not found in ChromaDB. Please set your preferences first using /api/temp-preferences/demo"
            }), 400
        
        # Generate meal plan using the ChromaDB-stored preferences
        plan_result = meal_planner_agent.generate_weekly_meal_plan(user_id)
        
        if "error" in plan_result:
            return jsonify(plan_result), 400
            
        return jsonify(plan_result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@meal_planner_bp.route('/meal-plan/regenerate-meal', methods=['POST'])
def regenerate_meal():
    """Regenerate specific meal without authentication (for testing)"""
    
    data = request.get_json()
    if not data or 'day' not in data or 'mealType' not in data or 'currentPlan' not in data:
        return jsonify({"error": "Missing required fields: day, mealType, currentPlan"}), 400

    # Use demo user ID
    demo_user_id = "demo_user"
    
    # Get preferences from request or use defaults
    preferences = data.get('preferences', {
        "dietaryRestrictions": [],
        "favoriteCuisines": ["International", "Mediterranean", "Asian"],
        "allergens": [],
        "cookingSkillLevel": "beginner",
        "healthGoals": ["General wellness"],
        "maxCookingTime": "30 minutes"
    })
    
    # Save preferences temporarily
    try:
        user_preferences_service.save_preferences(demo_user_id, preferences)
    except Exception as e:
        print(f"Could not save preferences: {e}")

    try:
        result = meal_planner_agent.regenerate_specific_meal(
            demo_user_id, 
            data['day'], 
            data['mealType'], 
            data['currentPlan']
        )
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@meal_planner_bp.route('/meal-plan/set-preferences', methods=['POST'])
def set_preferences():
    """Set meal planning preferences without authentication (for testing)"""
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No preferences provided"}), 400
    
    demo_user_id = "demo_user"
    
    try:
        user_preferences_service.save_preferences(demo_user_id, data)
        return jsonify({"success": True, "message": "Preferences saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to save preferences: {str(e)}"}), 500 