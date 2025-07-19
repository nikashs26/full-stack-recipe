
import requests
import os
from flask import request, jsonify, make_response
import time
from dotenv import load_dotenv
from services.recipe_service import RecipeService
from flask_cors import cross_origin
import asyncio
from functools import wraps

# Load environment variables
load_dotenv()

def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

def register_recipe_routes(app, recipe_cache):
    # Initialize recipe service
    recipe_service = RecipeService(recipe_cache)
    
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
        
        print(f"\n=== Recipe Search Request ===")
        print(f"Query: '{query}'")
        print(f"Ingredient: '{ingredient}'")
        print(f"Offset: {offset}")
        
        try:
            # Search recipes from all sources
            recipes = await recipe_service.search_recipes(query, ingredient, offset)
            
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
