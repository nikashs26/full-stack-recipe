from flask import Blueprint, request, jsonify
from services.shopping_list_agent import ShoppingListAgent
from services.recipe_service import RecipeService
from utils.auth_middleware import require_auth

shopping_list_bp = Blueprint('shopping_list', __name__)

# Initialize services (these would typically be passed in via dependency injection)
recipe_service = RecipeService()
shopping_list_agent = ShoppingListAgent(recipe_service)

@shopping_list_bp.route('/generate', methods=['POST'])
@require_auth
def generate_list():
    data = request.get_json()
    if not data or 'weekly_plan' not in data:
        return jsonify({'error': 'Missing weekly_plan in request body'}), 400

    weekly_plan = data['weekly_plan']
    
    try:
        shopping_list_result = shopping_list_agent.generate_shopping_list(weekly_plan)
        return jsonify(shopping_list_result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 