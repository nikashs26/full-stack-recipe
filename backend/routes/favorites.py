from flask import Blueprint, request, jsonify
from utils.auth_middleware import require_auth, get_user_id_from_request

favorites_bp = Blueprint('favorites', __name__)

# In-memory storage for favorites (in production, this would be in a database)
user_favorites = {}

@favorites_bp.route('/favorites', methods=['GET'])
@require_auth
def get_favorites():
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    favorites = user_favorites.get(user_id, [])
    return jsonify({'favorites': favorites}), 200

@favorites_bp.route('/favorites', methods=['POST'])
@require_auth
def add_favorite():
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    data = request.get_json()
    recipe_id = data.get('recipe_id')
    
    if not recipe_id:
        return jsonify({'error': 'Recipe ID is required'}), 400
    
    if user_id not in user_favorites:
        user_favorites[user_id] = []
    
    if recipe_id not in user_favorites[user_id]:
        user_favorites[user_id].append(recipe_id)
    
    return jsonify({'message': 'Recipe added to favorites'}), 200

@favorites_bp.route('/favorites/<recipe_id>', methods=['DELETE'])
@require_auth
def remove_favorite(recipe_id):
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    if user_id in user_favorites and recipe_id in user_favorites[user_id]:
        user_favorites[user_id].remove(recipe_id)
    
    return jsonify({'message': 'Recipe removed from favorites'}), 200 