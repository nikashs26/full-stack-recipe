from flask import Blueprint, request, jsonify
from services.user_preferences_service import UserPreferencesService
from middleware.auth_middleware import require_auth, get_current_user_id

preferences_bp = Blueprint('preferences', __name__)
user_preferences_service = UserPreferencesService()

@preferences_bp.route('/preferences', methods=['OPTIONS'])
def handle_preflight():
    """Handle CORS preflight requests"""
    response = jsonify({"status": "preflight"})
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response, 200

@preferences_bp.route('/preferences', methods=['POST'])
@require_auth
def save_user_preferences():
    """Save user preferences (requires authentication)"""
    try:
        user_id = get_current_user_id()
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No preferences data provided"}), 400
        
        # Extract preferences from the request
        preferences_data = data.get('preferences', data)  # Support both formats
        
        # Validate and set defaults for preferences
        processed_preferences = {
            'dietaryRestrictions': preferences_data.get('dietaryRestrictions', []),
            'favoriteCuisines': preferences_data.get('favoriteCuisines', ["International"]),
            'allergens': preferences_data.get('allergens', []),
            'cookingSkillLevel': preferences_data.get('cookingSkillLevel', "beginner"),
            'healthGoals': preferences_data.get('healthGoals', ["General wellness"]),
            'maxCookingTime': preferences_data.get('maxCookingTime', "30 minutes"),
            'favoriteFoods': preferences_data.get('favoriteFoods', []),
            # New meal preference fields
            'includeBreakfast': preferences_data.get('includeBreakfast', True),
            'includeLunch': preferences_data.get('includeLunch', True),
            'includeDinner': preferences_data.get('includeDinner', True),
            'includeSnacks': preferences_data.get('includeSnacks', False),
            # Nutritional targets
            'targetCalories': preferences_data.get('targetCalories', 2000),
            'targetProtein': preferences_data.get('targetProtein', 150),
            'targetCarbs': preferences_data.get('targetCarbs', 200),
            'targetFat': preferences_data.get('targetFat', 65)
        }
        
        # Save to ChromaDB
        user_preferences_service.save_preferences(user_id, processed_preferences)
        
        response = jsonify({
            "success": True,
            "message": "Preferences saved successfully to ChromaDB",
            "preferences": processed_preferences
        })
        
        # Add CORS headers to the response
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        
        return response, 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to save preferences: {str(e)}"}), 500

@preferences_bp.route('/preferences', methods=['GET'])
@require_auth
def get_user_preferences():
    """Get user preferences (requires authentication)"""
    try:
        user_id = get_current_user_id()
        
        # Get preferences from ChromaDB
        preferences = user_preferences_service.get_preferences(user_id)
        
        if not preferences:
            response = jsonify({
                "message": "No preferences found. Using default preferences.",
                "preferences": {
                    "dietaryRestrictions": [],
                    "favoriteCuisines": ["International"],
                    "allergens": [],
                    "cookingSkillLevel": "beginner",
                    "healthGoals": ["General wellness"],
                    "maxCookingTime": "30 minutes",
                    "favoriteFoods": ["", "", ""]
                }
            })
        else:
            response = jsonify({
                "success": True,
                "preferences": preferences
            })
        
        # Add CORS headers to the response
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        
        return response, 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get preferences: {str(e)}"}), 500