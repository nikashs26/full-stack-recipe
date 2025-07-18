from flask import Blueprint, request, jsonify, session
from services.user_preferences_service import UserPreferencesService
import uuid
import json

temp_preferences_bp = Blueprint('temp_preferences', __name__)
user_preferences_service = UserPreferencesService()

# Apply CORS to this blueprint
from flask_cors import CORS
CORS(temp_preferences_bp,
     supports_credentials=True,
     origins=[
         'http://localhost:8080',
         'http://localhost:8081',
         'http://localhost:8082'
     ],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

@temp_preferences_bp.route('/temp-preferences', methods=['POST', 'OPTIONS'])
@temp_preferences_bp.route('/preferences', methods=['POST', 'OPTIONS'])
def save_temp_preferences():
    print(f'🔥 BACKEND: [SAVE] SESSION: {dict(session)}')
    print(f'🔥 BACKEND: [SAVE] HEADERS: {dict(request.headers)}')
    print(f'🔥 BACKEND: [SAVE] COOKIES: {request.cookies}')
    """
    Save temporary preferences for users without authentication
    Creates a session-based user ID and stores preferences in ChromaDB
    """
    if request.method == 'OPTIONS':
        print('🔥 BACKEND: OPTIONS /temp-preferences preflight received')
        return '', 200
    print('🔥 BACKEND: POST /temp-preferences called')
    try:
        data = request.get_json()
        print(f'🔥 BACKEND: Received data: {data}')
        
        if not data:
            print('🔥 BACKEND: No data provided')
            return jsonify({"error": "No data provided"}), 400
        
        # Extract preferences from the request
        preferences_data = data.get('preferences', {})
        print(f'🔥 BACKEND: Extracted preferences_data: {preferences_data}')
        
        if not preferences_data:
            print('🔥 BACKEND: No preferences data provided')
            return jsonify({"error": "No preferences data provided"}), 400
        
        # Validate and set defaults for preferences
        # Ensure favoriteFoods is always an array of length 3
        favorite_foods = preferences_data.get('favoriteFoods', [])
        if not isinstance(favorite_foods, list):
            favorite_foods = [str(favorite_foods)]
        while len(favorite_foods) < 3:
            favorite_foods.append("")
        favorite_foods = favorite_foods[:3]

        processed_preferences = {
            'dietaryRestrictions': preferences_data.get('dietaryRestrictions', []),
            'favoriteCuisines': preferences_data.get('favoriteCuisines', ["International"]),
            'allergens': preferences_data.get('allergens', []),
            'cookingSkillLevel': preferences_data.get('cookingSkillLevel', "beginner"),
            'healthGoals': preferences_data.get('healthGoals', ["General wellness"]),
            'maxCookingTime': preferences_data.get('maxCookingTime', "30 minutes"),
            'favoriteFoods': favorite_foods
        }
        
        print(f'🔥 BACKEND: Processed preferences: {processed_preferences}')
        
        # Use logged-in user's email as key if authenticated, else temp_user_id
        if 'user_email' in session:
            user_id = session['user_email']
            print(f'🔥 BACKEND: [SAVE] user_email in session: {user_id}')
            print(f'🔥 BACKEND: [SAVE] preferences: {processed_preferences}')
            user_preferences_service.save_preferences(user_id, processed_preferences)
            response_data = {
                "success": True,
                "message": "Preferences saved for user",
                "user_id": user_id,
                "preferences": processed_preferences
            }
        else:
            if 'temp_user_id' not in session:
                session['temp_user_id'] = str(uuid.uuid4())
                print(f'🔥 BACKEND: Generated new temp_user_id: {session["temp_user_id"]}')
            temp_user_id = session['temp_user_id']
            print(f'🔥 BACKEND: [SAVE] temp_user_id in session: {temp_user_id}')
            print(f'🔥 BACKEND: [SAVE] preferences: {processed_preferences}')
            user_preferences_service.save_preferences(temp_user_id, processed_preferences)
            response_data = {
                "success": True,
                "message": "Temporary preferences saved successfully",
                "temp_user_id": temp_user_id,
                "preferences": processed_preferences
            }
        
        print(f'🔥 BACKEND: Returning response: {response_data}')
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f'🔥 BACKEND: Error in save_temp_preferences: {str(e)}')
        return jsonify({"error": str(e)}), 500

@temp_preferences_bp.route('/temp-preferences', methods=['GET', 'OPTIONS'])
@temp_preferences_bp.route('/preferences', methods=['GET', 'OPTIONS'])
def get_temp_preferences():
    print(f'🔥 BACKEND: [GET] SESSION: {dict(session)}')
    print(f'🔥 BACKEND: [GET] HEADERS: {dict(request.headers)}')
    print(f'🔥 BACKEND: [GET] COOKIES: {request.cookies}')
    if request.method == 'OPTIONS':
        print('🔥 BACKEND: OPTIONS /temp-preferences (GET) preflight received')
        return '', 200

    """
    Get temporary preferences for the current session
    """
    print('🔥 BACKEND: GET /temp-preferences called')
    try:
        # If logged in, use user_email as key
        if 'user_email' in session:
            user_id = session['user_email']
            print(f'🔥 BACKEND: Loading preferences for logged-in user: {user_id}')
            preferences = user_preferences_service.get_preferences(user_id)
            if preferences:
                return jsonify({
                    "success": True,
                    "user_id": user_id,
                    "preferences": preferences
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "message": "No preferences found for this user",
                    "preferences": None
                }), 200
        # Else, use temp_user_id for guests
        if 'temp_user_id' not in session:
            print('🔥 BACKEND: No temp_user_id in session')
            return jsonify({
                "success": False,
                "message": "No temporary preferences found",
                "preferences": None
            }), 200
        temp_user_id = session['temp_user_id']
        preferences = user_preferences_service.get_preferences(temp_user_id)
        if preferences:
            return jsonify({
                "success": True,
                "temp_user_id": temp_user_id,
                "preferences": preferences
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "No preferences found for this session",
                "preferences": None
            }), 200
    except Exception as e:
        print(f'🔥 BACKEND: Error in get_temp_preferences: {str(e)}')
        return jsonify({"error": str(e)}), 500

@temp_preferences_bp.route('/temp-preferences/demo', methods=['POST'])
def create_demo_preferences():
    """
    Create demo preferences for testing
    """
    try:
        demo_preferences = {
            'dietaryRestrictions': ['vegetarian'],
            'favoriteCuisines': ['Italian', 'Mediterranean'],
            'allergens': ['nuts'],
            'cookingSkillLevel': 'intermediate',
            'healthGoals': ['Weight loss', 'Heart health'],
            'maxCookingTime': '45 minutes'
        }
        
        # Create a demo user ID
        demo_user_id = "demo_user_123"
        
        # Save to ChromaDB
        user_preferences_service.save_preferences(demo_user_id, demo_preferences)
        
        return jsonify({
            "success": True,
            "message": "Demo preferences created successfully",
            "user_id": demo_user_id,
            "preferences": demo_preferences
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@temp_preferences_bp.route('/temp-preferences/clear', methods=['POST'])
def clear_temp_preferences():
    """
    Clear temporary preferences for the current session
    """
    try:
        if 'temp_user_id' in session:
            session.pop('temp_user_id', None)
            return jsonify({
                "success": True,
                "message": "Temporary preferences cleared successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "No temporary preferences to clear"
            }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 