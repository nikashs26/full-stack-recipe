from flask import Blueprint, request, jsonify
import requests
from services.recipe_cache_service import RecipeCacheService
from services.recipe_service import RecipeService

# Create a Blueprint for TheMealDB routes
mealdb_bp = Blueprint('mealdb_bp', __name__)

# Initialize services
recipe_cache = RecipeCacheService()
recipe_service = RecipeService()

@mealdb_bp.route('/api/mealdb/search', methods=['GET'])
def search_mealdb():
    """Search for recipes in TheMealDB"""
    try:
        search_term = request.args.get('query', '').strip()
        cuisine = request.args.get('cuisine', '').strip()
        limit = int(request.args.get('limit', 12))
        
        # Call the recipe service to search TheMealDB
        recipes = recipe_service.search_mealdb_recipes(
            search_term=search_term if search_term else None,
            cuisine=cuisine if cuisine else None,
            limit=limit
        )
        
        # Store the recipes in ChromaDB for future reference
        if recipes:
            recipe_cache.add_recipes(recipes)
        
        return jsonify(recipes)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mealdb_bp.route('/api/mealdb/recipe/<recipe_id>', methods=['GET'])
def get_mealdb_recipe(recipe_id):
    """Get a specific recipe from TheMealDB by ID"""
    try:
        # First check if we have it in ChromaDB
        cached_recipe = recipe_cache.get_recipe(recipe_id)
        if cached_recipe:
            return jsonify(cached_recipe)
        
        # If not in cache, fetch from TheMealDB
        recipe = recipe_service.get_mealdb_recipe(recipe_id)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
            
        # Store in cache for future use
        recipe_cache.add_recipe(recipe)
        
        return jsonify(recipe)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mealdb_bp.route('/api/mealdb/cuisines', methods=['GET'])
def get_mealdb_cuisines():
    """Get all available cuisine areas from TheMealDB"""
    try:
        cuisines = recipe_service.get_mealdb_cuisines()
        return jsonify(cuisines)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def register_mealdb_routes(app):
    """Register TheMealDB routes with the Flask app"""
    app.register_blueprint(mealdb_bp)
