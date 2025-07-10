from flask import Blueprint, request, jsonify
from services.user_preferences_service import UserPreferencesService
from auth import require_auth  # Assuming you have an auth decorator

preferences_bp = Blueprint('preferences', __name__)
user_preferences_service = UserPreferencesService()

@preferences_bp.route('/preferences', methods=['POST'])
@require_auth
def save_user_preferences():
    user_id = request.user_id # Get user_id from your authentication token/middleware
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    preferences_data = request.json
    if not preferences_data:
        return jsonify({"error": "No preferences data provided"}), 400
    
    try:
        user_preferences_service.save_preferences(user_id, preferences_data)
        return jsonify({"message": "Preferences saved successfully to ChromaDB"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@preferences_bp.route('/preferences', methods=['GET'])
@require_auth
def get_user_preferences():
    user_id = request.user_id # Get user_id from your authentication token/middleware
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        preferences = user_preferences_service.get_preferences(user_id)
        if preferences:
            return jsonify({"preferences": preferences}), 200
        else:
            return jsonify({"message": "No preferences found for this user"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500 