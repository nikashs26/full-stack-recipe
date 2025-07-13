from flask import Blueprint, request, jsonify, session
from services.user_preferences_service import UserPreferencesService
import uuid
import json

temp_preferences_bp = Blueprint('temp_preferences', __name__)
user_preferences_service = UserPreferencesService()

@temp_preferences_bp.route('/temp-preferences', methods=['POST'])
def save_temp_preferences():
    """
    Save temporary preferences for users without authentication
    Creates a session-based user ID and stores preferences in ChromaDB
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract preferences from the request
        preferences_data = data.get('preferences', {})
        if not preferences_data:
            return jsonify({"error": "No preferences data provided"}), 400
        
        # Get or create a session-based user ID
        if 'temp_user_id' not in session:
            session['temp_user_id'] = f"temp_user_{str(uuid.uuid4())[:8]}"
        
        temp_user_id = session['temp_user_id']
        
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
        user_preferences_service.save_preferences(temp_user_id, processed_preferences)
        
        return jsonify({
            "success": True,
            "message": "Temporary preferences saved successfully",
            "temp_user_id": temp_user_id,
            "preferences": processed_preferences
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@temp_preferences_bp.route('/temp-preferences', methods=['GET'])
def get_temp_preferences():
    """
    Get temporary preferences for the current session
    """
    try:
        # Check if we have a temp user ID in session
        if 'temp_user_id' not in session:
            return jsonify({
                "success": False,
                "message": "No temporary preferences found",
                "preferences": None
            }), 200
        
        temp_user_id = session['temp_user_id']
        
        # Get preferences from ChromaDB
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
        return jsonify({"error": str(e)}), 500

@temp_preferences_bp.route('/temp-preferences/demo', methods=['POST'])
def create_demo_preferences():
    """
    Create demo preferences for testing meal planning
    """
    try:
        # Create a demo user ID
        demo_user_id = "demo_user_session"
        session['temp_user_id'] = demo_user_id
        
        # Demo preferences
        demo_preferences = {
            "dietaryRestrictions": ["vegetarian"],
            "favoriteCuisines": ["Mediterranean", "Asian", "Italian"],
            "allergens": [],
            "cookingSkillLevel": "intermediate",
            "healthGoals": ["weight loss", "general wellness"],
            "maxCookingTime": "45 minutes"
        }
        
        # Save to ChromaDB
        user_preferences_service.save_preferences(demo_user_id, demo_preferences)
        
        return jsonify({
            "success": True,
            "message": "Demo preferences created successfully",
            "temp_user_id": demo_user_id,
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
            "message": "Temporary preferences cleared"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 