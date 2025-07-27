
import requests
import os
from flask import request, jsonify, make_response
import time
from dotenv import load_dotenv
from services.recipe_service import RecipeService
from services.user_preferences_service import UserPreferencesService
from flask_cors import cross_origin
import asyncio
from functools import wraps
from middleware.auth_middleware import get_current_user_id

# Load environment variables
load_dotenv()

def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

def register_recipe_routes(app, recipe_cache):
    # Initialize services
    recipe_service = RecipeService(recipe_cache)
    user_preferences_service = UserPreferencesService()
    
    @app.route("/get_recipes", methods=["GET", "OPTIONS"])
    @cross_origin(origins=["http://localhost:8081"], 
                 supports_credentials=True)
    @async_route
    async def get_recipes():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            return response
            
        start_time = time.time()
        query = request.args.get("query", "").strip()
        ingredient = request.args.get("ingredient", "").strip()
        offset = int(request.args.get("offset", "0"))
        limit = int(request.args.get("limit", "1000"))  # Default to 1000 results
        
        # Get cuisine and dietary restrictions filters
        cuisine_param = request.args.get("cuisine", "")
        diet_param = request.args.get("dietary_restrictions", "")
        
        # Parse comma-separated values
        cuisines = [c.strip() for c in cuisine_param.split(",") if c.strip()] if cuisine_param else []
        dietary_restrictions = [d.strip() for d in diet_param.split(",") if d.strip()] if diet_param else []
        
        # Get user's foods to avoid from preferences
        foods_to_avoid = []
        try:
            user_id = get_current_user_id()
            if user_id:
                preferences = user_preferences_service.get_preferences(user_id)
                if preferences and 'foodsToAvoid' in preferences:
                    foods_to_avoid = [f.lower() for f in preferences['foodsToAvoid'] if f and isinstance(f, str)]
                    print(f"Found {len(foods_to_avoid)} foods to avoid in user preferences")
        except Exception as e:
            print(f"Error getting user preferences for foods to avoid: {e}")
        
        print(f"\n=== Recipe Search Request ===")
        print(f"Query: '{query}'")
        print(f"Ingredient: '{ingredient}'")
        print(f"Foods to avoid: {foods_to_avoid}")
        print(f"Offset: {offset}")
        print(f"Limit: {limit}")
        print(f"Cuisines filter: {cuisines}")
        print(f"Dietary restrictions filter: {dietary_restrictions}")
        
        try:
            # Search recipes from all sources with pagination and filters
            recipes = await recipe_service.search_recipes(
                query=query,
                ingredient=ingredient,
                offset=offset,
                limit=limit,
                cuisines=cuisines,
                dietary_restrictions=dietary_restrictions,
                foods_to_avoid=foods_to_avoid
            )
            
            print(f"Found {len(recipes)} recipes in {time.time() - start_time:.2f}s")
            return jsonify({"results": recipes}), 200
            
        except Exception as e:
            print(f"Error searching recipes: {e}")
            return jsonify({
                "error": "Failed to search recipes",
                "details": str(e)
            }), 500

    @app.route("/get_recipe_by_id", methods=["GET", "OPTIONS"])
    @cross_origin(origins=["http://localhost:8081"], 
                 supports_credentials=True)
    @async_route
    async def get_recipe_by_id():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            return response
            
        recipe_id = request.args.get("id")
        if not recipe_id:
            return jsonify({"error": "Recipe ID is required"}), 400
        
        try:
            recipe = await recipe_service.get_recipe_by_id(recipe_id)
                                
            if recipe:
                return jsonify(recipe), 200
            else:
                return jsonify({"error": "Recipe not found"}), 404
            
        except Exception as e:
            print(f"Error fetching recipe {recipe_id}: {e}")
            return jsonify({
                "error": "Failed to fetch recipe",
                "details": str(e)
            }), 500

    return app
