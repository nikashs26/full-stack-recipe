from flask import Blueprint, request, jsonify
from services.user_preferences_service import UserPreferencesService
from middleware.auth_middleware import require_auth, get_current_user_id

preferences_bp = Blueprint('preferences', __name__)
user_preferences_service = UserPreferencesService()

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
            'maxCookingTime': preferences_data.get('maxCookingTime', "30 minutes")
        }
        
        # Save to ChromaDB
        user_preferences_service.save_preferences(user_id, processed_preferences)
        
        return jsonify({
            "success": True,
            "message": "Preferences saved successfully to ChromaDB",
            "preferences": processed_preferences
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to save preferences: {str(e)}"}), 500

@preferences_bp.route('/preferences', methods=['GET'])
@require_auth
def get_user_preferences():
    """Get user preferences (requires authentication)"""
    try:
        user_id = get_current_user_id()
        
        preferences = user_preferences_service.get_preferences(user_id)
        if preferences:
            return jsonify({
                "success": True,
                "preferences": preferences
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "No preferences found for this user. Please set your preferences first.",
                "preferences": None
            }), 200
            
    except Exception as e:
        return jsonify({"error": f"Failed to get preferences: {str(e)}"}), 500 