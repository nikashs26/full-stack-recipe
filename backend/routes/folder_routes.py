from flask import Blueprint, request, jsonify
from services.get_folder_service() import FolderService
from middleware.auth_middleware import require_auth, get_current_user_id

folder_bp = Blueprint('folders', __name__)

# Lazy initialization to avoid startup crashes
def get_get_folder_service()():
    """Get FolderService instance with lazy initialization"""
    if not hasattr(get_get_folder_service(), '_instance'):
        get_get_folder_service()._instance = FolderService()
    return get_get_folder_service()._instance

@folder_bp.route('/folders', methods=['OPTIONS'])
def handle_folders_options():
    """Handle CORS preflight request for folders endpoint"""
    response = jsonify({})
    response.status_code = 200
    return response

@folder_bp.route('/folders', methods=['POST'])
@require_auth
def create_folder():
    """Create a new folder"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({"error": "Folder name is required"}), 400
            
        # Create the folder
        folder = get_folder_service().create_folder(
            user_id=user_id,
            name=data['name'].strip(),
            description=data.get('description', '').strip()
        )
        
        return jsonify(folder), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@folder_bp.route('/folders', methods=['GET'])
@require_auth
def get_my_folders():
    """Get all folders for the current user"""
    try:
        user_id = get_current_user_id()
        folders = get_folder_service().get_user_folders(user_id)
        return jsonify(folders)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@folder_bp.route('/folders/<folder_id>', methods=['GET'])
@require_auth
def get_folder(folder_id):
    """Get a specific folder with its contents"""
    try:
        user_id = get_current_user_id()
        folder_data = get_folder_service().get_folder_contents(folder_id, user_id)
        
        if not folder_data['folder']:
            return jsonify({"error": "Folder not found"}), 404
            
        return jsonify(folder_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@folder_bp.route('/folders/<folder_id>', methods=['PUT'])
@require_auth
def update_folder(folder_id):
    """Update folder details"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        updates = {}
        if 'name' in data:
            updates['name'] = data['name'].strip()
        if 'description' in data:
            updates['description'] = data['description'].strip()
            
        if not updates:
            return jsonify({"error": "No updates provided"}), 400
            
        updated_folder = get_folder_service().update_folder(folder_id, user_id, **updates)
        
        if not updated_folder:
            return jsonify({"error": "Folder not found or access denied"}), 404
            
        return jsonify(updated_folder)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@folder_bp.route('/folders/<folder_id>', methods=['DELETE'])
@require_auth
def delete_folder(folder_id):
    """Delete a folder and all its contents"""
    try:
        user_id = get_current_user_id()
        success = get_folder_service().delete_folder(folder_id, user_id)
        
        if not success:
            return jsonify({"error": "Folder not found or access denied"}), 404
            
        return jsonify({"message": "Folder deleted successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@folder_bp.route('/folders/<folder_id>/items', methods=['POST'])
@require_auth
def add_to_folder(folder_id):
    """Add a recipe to a folder"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['recipe_id', 'recipe_type', 'recipe_data']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Add to folder
        item = get_folder_service().add_to_folder(
            folder_id=folder_id,
            user_id=user_id,
            recipe_id=data['recipe_id'],
            recipe_type=data['recipe_type'],
            recipe_data=data['recipe_data']
        )
        
        if not item:
            return jsonify({
                "error": "Folder not found, access denied, or recipe already in folder"
            }), 400
            
        return jsonify(item), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@folder_bp.route('/folders/<folder_id>/items', methods=['OPTIONS'])
def handle_add_to_folder_options(folder_id):
    """Handle CORS preflight request for add to folder endpoint"""
    response = jsonify({})
    response.status_code = 200
    return response

@folder_bp.route('/folders/items/<item_id>', methods=['DELETE'])
@require_auth
def remove_from_folder(item_id):
    """Remove a recipe from a folder"""
    try:
        user_id = get_current_user_id()
        
        # First get the folder ID from the item
        items = get_folder_service().folder_items_collection.get(
            ids=[item_id],
            include=[]
        )
        
        if not items['ids']:
            return jsonify({"error": "Item not found"}), 404
            
        # Verify the folder belongs to the user
        folder_id = items['metadatas'][0]['folder_id']
        folder = get_folder_service().folders_collection.get(
            ids=[folder_id],
            where={"user_id": user_id}
        )
        
        if not folder['ids']:
            return jsonify({"error": "Access denied"}), 403
            
        # Remove the item
        success = get_folder_service().remove_from_folder(folder_id, user_id, item_id)
        
        if not success:
            return jsonify({"error": "Failed to remove item"}), 400
            
        return jsonify({"message": "Item removed from folder"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@folder_bp.route('/folders/items/<item_id>', methods=['OPTIONS'])
def handle_remove_from_folder_options(item_id):
    """Handle CORS preflight request for remove from folder endpoint"""
    response = jsonify({})
    response.status_code = 200
    return response

@folder_bp.route('/recipes/<recipe_type>/<recipe_id>/folders', methods=['GET'])
@require_auth
def get_folders_for_recipe(recipe_type, recipe_id):
    """Get all folders containing a specific recipe"""
    try:
        user_id = get_current_user_id()
        folders = get_folder_service().get_recipe_folders(user_id, recipe_id, recipe_type)
        return jsonify(folders)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@folder_bp.route('/recipes/<recipe_type>/<recipe_id>/folders', methods=['OPTIONS'])
def handle_recipe_folders_options(recipe_type, recipe_id):
    """Handle CORS preflight request for recipe folders endpoint"""
    response = jsonify({})
    response.status_code = 200
    return response

@folder_bp.route('/folders/search', methods=['GET'])
@require_auth
def search_folders():
    """Search user's folders by name or description"""
    try:
        user_id = get_current_user_id()
        query = request.args.get('q', '')
        
        if not query:
            return jsonify([])
            
        results = get_folder_service().search_folders(user_id, query)
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@folder_bp.route('/folders/search', methods=['OPTIONS'])
def handle_search_folders_options():
    """Handle CORS preflight request for search folders endpoint"""
    response = jsonify({})
    response.status_code = 200
    return response
