from flask import Blueprint, request, jsonify
from services.shopping_list_agent import ShoppingListAgent
from services.recipe_service import RecipeService
from middleware.auth_middleware import require_auth, get_current_user_id

shopping_list_bp = Blueprint('shopping_list', __name__)

# Initialize services (these would typically be passed in via dependency injection)
recipe_service = RecipeService()
shopping_list_agent = ShoppingListAgent(recipe_service)

@shopping_list_bp.route('/shopping-list/generate', methods=['POST'])
@require_auth
def generate_list():
    """Generate shopping list (requires authentication)"""
    try:
        user_id = get_current_user_id()
        
        data = request.get_json()
        if not data or 'weekly_plan' not in data:
            return jsonify({'error': 'Missing weekly_plan in request body'}), 400

        weekly_plan = data['weekly_plan']
        
        # Optional parameters
        serving_size = data.get('serving_size', 2)
        dietary_preferences = data.get('dietary_preferences', [])
        
        shopping_list_result = shopping_list_agent.generate_shopping_list(
            weekly_plan, 
            serving_size=serving_size,
            dietary_preferences=dietary_preferences
        )
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "shopping_list": shopping_list_result,
            "serving_size": serving_size
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate shopping list: {str(e)}'}), 500

@shopping_list_bp.route('/shopping-list/optimize', methods=['POST'])
@require_auth
def optimize_shopping_list():
    """Optimize shopping list by removing duplicates and grouping items (requires authentication)"""
    try:
        user_id = get_current_user_id()
        
        data = request.get_json()
        if not data or 'shopping_list' not in data:
            return jsonify({'error': 'Missing shopping_list in request body'}), 400

        shopping_list = data['shopping_list']
        
        # Optimize the shopping list
        optimized_list = shopping_list_agent.optimize_shopping_list(shopping_list)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "optimized_shopping_list": optimized_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to optimize shopping list: {str(e)}'}), 500 