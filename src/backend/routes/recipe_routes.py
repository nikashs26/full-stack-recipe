from flask import Blueprint, request, jsonify, make_response
from flask_cors import cross_origin
from services.recipe_cache_service import RecipeCacheService

# Create a Blueprint for recipe routes
recipe_bp = Blueprint('recipe_bp', __name__)

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", request.headers.get('Origin', '*'))
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", request.headers.get('Origin', '*'))
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

def register_recipe_routes(app, recipe_cache):
    @recipe_bp.route('/get_recipes', methods=['GET', 'OPTIONS'])
    @cross_origin(supports_credentials=True)
    def get_recipes():
        print("\n=== /get_recipes endpoint (local only) ===")
        
        try:
            # Get query parameters
            query = request.args.get('query', '').strip().lower()
            ingredient = request.args.get('ingredient', '').strip().lower()
            print(f"Search query: '{query}', Ingredient: '{ingredient}'")
            
            # Get all recipes from ChromaDB
            print("Fetching recipes from ChromaDB...")
            all_recipes = recipe_cache.get_all_recipes()
            print(f"Found {len(all_recipes)} recipes in ChromaDB")
            
            # If no recipes found in ChromaDB, return empty result
            if not all_recipes:
                print("No recipes found in ChromaDB")
                return jsonify({"results": []})
            
            # Filter recipes based on query and ingredient
            filtered_recipes = []
            for recipe in all_recipes:
                # Skip if recipe is not a dictionary
                if not isinstance(recipe, dict):
                    continue
                    
                # Check if recipe matches query
                recipe_title = str(recipe.get('title', '')).lower()
                recipe_summary = str(recipe.get('summary', '')).lower()
                
                matches_query = not query or query in recipe_title or query in recipe_summary
                
                # Check if recipe matches ingredient
                matches_ingredient = not ingredient
                if ingredient and 'extendedIngredients' in recipe and isinstance(recipe['extendedIngredients'], list):
                    for ing in recipe['extendedIngredients']:
                        if isinstance(ing, dict) and 'name' in ing and ingredient in str(ing['name']).lower():
                            matches_ingredient = True
                            break
                
                if matches_query and matches_ingredient:
                    filtered_recipes.append(recipe)
            
            print(f"Found {len(filtered_recipes)} matching recipes")
            return jsonify({"results": filtered_recipes})
            
        except Exception as e:
            error_msg = f"Error in get_recipes: {str(e)}"
            print(error_msg)
            return jsonify({"results": [], "error": error_msg})
    
    return recipe_bp
