from flask import Blueprint, request, jsonify, make_response
from flask_cors import cross_origin
from services.recipe_cache_service import RecipeCacheService
import re

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

def _flexible_search_match(search_terms, recipe_data):
    """
    Perform flexible search matching that supports:
    - ANY substring matches (e.g., 'a' matches anything with 'a', 'ch' matches 'chicken', 'pasta' matches 'spaghetti')
    - Character-by-character matching anywhere in the recipe content
    - Case-insensitive matching
    - Matching in titles, descriptions, ingredients, and other fields
    """
    if not search_terms:
        return True
    
    # Convert search terms to lowercase for case-insensitive matching
    search_terms_lower = search_terms.lower().strip()
    if not search_terms_lower:
        return True
    
    # Get all searchable text from the recipe
    searchable_fields = []
    
    # Title
    if recipe_data.get('title'):
        searchable_fields.append(str(recipe_data['title']).lower())
    
    # Description/Summary
    if recipe_data.get('description'):
        searchable_fields.append(str(recipe_data['description']).lower())
    if recipe_data.get('summary'):
        searchable_fields.append(str(recipe_data['summary']).lower())
    
    # Ingredients
    if recipe_data.get('ingredients') and isinstance(recipe_data['ingredients'], list):
        for ing in recipe_data['ingredients']:
            if isinstance(ing, dict) and ing.get('name'):
                searchable_fields.append(str(ing['name']).lower())
    if recipe_data.get('extendedIngredients') and isinstance(recipe_data['extendedIngredients'], list):
        for ing in recipe_data['extendedIngredients']:
            if isinstance(ing, dict) and ing.get('name'):
                searchable_fields.append(str(ing['name']).lower())
    
    # Cuisines
    if recipe_data.get('cuisines') and isinstance(recipe_data['cuisines'], list):
        for cuisine in recipe_data['cuisines']:
            searchable_fields.append(str(cuisine).lower())
    if recipe_data.get('cuisine'):
        searchable_fields.append(str(recipe_data['cuisine']).lower())
    
    # Diets
    if recipe_data.get('diets') and isinstance(recipe_data['diets'], list):
        for diet in recipe_data['diets']:
            searchable_fields.append(str(diet).lower())
    if recipe_data.get('dietaryRestrictions') and isinstance(recipe_data['dietaryRestrictions'], list):
        for diet in recipe_data['dietaryRestrictions']:
            searchable_fields.append(str(diet).lower())
    
    # Tags
    if recipe_data.get('tags') and isinstance(recipe_data['tags'], list):
        for tag in recipe_data['tags']:
            searchable_fields.append(str(tag).lower())
    
    # Instructions
    if recipe_data.get('instructions'):
        if isinstance(recipe_data['instructions'], list):
            for instruction in recipe_data['instructions']:
                searchable_fields.append(str(instruction).lower())
        else:
            searchable_fields.append(str(recipe_data['instructions']).lower())
    
    # Combine all searchable text into one big string
    all_text = ' '.join(searchable_fields)
    
    # Debug output for troubleshooting
    print(f"🔍 SEARCH DEBUG:")
    print(f"  - Search term: '{search_terms_lower}'")
    print(f"  - Recipe title: '{recipe_data.get('title', 'No title')}'")
    print(f"  - All searchable text: '{all_text[:200]}...'")
    print(f"  - Contains search term: {search_terms_lower in all_text}")
    
    # Simple substring check - if ANY part of the search query appears anywhere in the recipe text
    # This allows for single characters, partial words, or any sequence of characters
    return search_terms_lower in all_text

def register_recipe_routes(app, recipe_cache):
    @recipe_bp.route('/get_recipes', methods=['GET', 'OPTIONS'])
    @cross_origin(supports_credentials=True)
    def get_recipes():
        print("\n=== /get_recipes endpoint (local only) ===")
        
        try:
            # Get query parameters
            query = request.args.get('query', '').strip()
            ingredient = request.args.get('ingredient', '').strip()
            print(f"Search query: '{query}', Ingredient: '{ingredient}'")
            
            # Get all recipes from ChromaDB
            print("Fetching recipes from ChromaDB...")
            all_recipes = recipe_cache.get_all_recipes()
            print(f"Found {len(all_recipes)} recipes in ChromaDB")
            
            # If no recipes found in ChromaDB, return empty result
            if not all_recipes:
                print("No recipes found in ChromaDB")
                return jsonify({"results": []})
            
            # Filter recipes based on query and ingredient using flexible search
            filtered_recipes = []
            print(f"🔍 PROCESSING {len(all_recipes)} recipes for search...")
            
            for i, recipe in enumerate(all_recipes):
                # Skip if recipe is not a dictionary
                if not isinstance(recipe, dict):
                    continue
                
                print(f"🔍 Processing recipe {i+1}/{len(all_recipes)}: '{recipe.get('title', 'No title')}'")
                
                # Check if recipe matches query using flexible search
                matches_query = not query or _flexible_search_match(query, recipe)
                
                # Check if recipe matches ingredient using flexible search
                matches_ingredient = not ingredient or _flexible_search_match(ingredient, recipe)
                
                print(f"  - Matches query '{query}': {matches_query}")
                print(f"  - Matches ingredient '{ingredient}': {matches_ingredient}")
                
                if matches_query and matches_ingredient:
                    filtered_recipes.append(recipe)
                    print(f"  - ✅ Recipe ADDED to results")
                else:
                    print(f"  - ❌ Recipe EXCLUDED from results")
            
            print(f"🔍 SEARCH COMPLETE: Found {len(filtered_recipes)} matching recipes out of {len(all_recipes)} total")
            return jsonify({"results": filtered_recipes})
            
        except Exception as e:
            error_msg = f"Error in get_recipes: {str(e)}"
            print(error_msg)
            return jsonify({"results": [], "error": error_msg})
    
    return recipe_bp
