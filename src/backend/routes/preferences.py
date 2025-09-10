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

@preferences_bp.route('/preferences', methods=['POST', 'OPTIONS'])
@require_auth
def save_user_preferences():
    """Save user preferences (requires authentication)"""
    
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        user_id = get_current_user_id()
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No preferences data provided"}), 400
        
        print(f"Received preferences data: {data}")  # Debug log
        
        # Extract preferences from the request
        preferences_data = data.get('preferences', data)  # Support both formats
        
        # Debug log the incoming data
        print(f"Processing preferences: {preferences_data}")
        
        # Validate and set defaults for preferences - respect user choices, don't force defaults
        processed_preferences = {
            'dietaryRestrictions': preferences_data.get('dietaryRestrictions', []),
            'favoriteCuisines': preferences_data.get('favoriteCuisines', []),  # Don't force defaults
            'foodsToAvoid': preferences_data.get('foodsToAvoid', []),
            'allergens': preferences_data.get('allergens', []),
            'cookingSkillLevel': preferences_data.get('cookingSkillLevel', "beginner"),
            'healthGoals': preferences_data.get('healthGoals', []),  # Don't force defaults
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
        
        # Debug log before saving
        print(f"Saving preferences for user {user_id}: {processed_preferences}")
        
        # Save to ChromaDB
        user_preferences_service.save_preferences(user_id, processed_preferences)
        
        # Debug log after saving
        print(f"Preferences saved successfully for user {user_id}")
        
        response = jsonify({
            "success": True,
            "message": "Preferences saved successfully to ChromaDB",
            "preferences": processed_preferences
        })
        
        # Add CORS headers to the response
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8081')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        
        return response, 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to save preferences: {str(e)}"}), 500

@preferences_bp.route('/preferences', methods=['GET', 'OPTIONS'])
@require_auth
def get_user_preferences():
    """Get user preferences (requires authentication)"""
    
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        user_id = get_current_user_id()
        
        # Get preferences from ChromaDB
        preferences = user_preferences_service.get_preferences(user_id)
        
        if not preferences:
            response = jsonify({
                "message": "No preferences found. Using minimal defaults.",
                "preferences": {
                    "dietaryRestrictions": [],
                    "favoriteCuisines": [],  # Don't force any cuisines
                    "foodsToAvoid": [],
                    "allergens": [],
                    "cookingSkillLevel": "beginner",
                    "healthGoals": [],  # Don't force any health goals
                    "maxCookingTime": "30 minutes",
                    "favoriteFoods": []
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