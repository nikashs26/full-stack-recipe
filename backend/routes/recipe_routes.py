
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

# Simple request deduplication cache
request_cache = {}
CACHE_TTL = 5  # 5 seconds

def deduplicate_requests(f):
    """Decorator to deduplicate identical requests within a short time window"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create a cache key based on the request parameters
        cache_key = f"{request.endpoint}_{request.method}_{request.query_string.decode()}_{request.get_data().decode()}"
        
        current_time = time.time()
        
        # Check if we have a recent identical request
        if cache_key in request_cache:
            cached_result, timestamp = request_cache[cache_key]
            if current_time - timestamp < CACHE_TTL:
                # Return cached result if it's still valid
                return cached_result
        
        # Process the request normally
        result = f(*args, **kwargs)
        
        # Cache the result
        request_cache[cache_key] = (result, current_time)
        
        # Clean up old cache entries
        for key in list(request_cache.keys()):
            if current_time - request_cache[key][1] > CACHE_TTL:
                del request_cache[key]
        
        return result
    return decorated_function

def async_route(f):
    """Decorator to handle async functions in Flask"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get the current event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async function
            if asyncio.iscoroutinefunction(f):
                result = loop.run_until_complete(f(*args, **kwargs))
            else:
                result = f(*args, **kwargs)
            
            return result
        except Exception as e:
            print(f"Error in async_route: {e}")
            raise
    return decorated_function

def register_recipe_routes(app, recipe_cache):
    # Initialize services
    recipe_service = RecipeService(recipe_cache)
    user_preferences_service = UserPreferencesService()
    
    @app.route("/api/recipe-counts", methods=["GET"])
    @cross_origin(origins=["http://localhost:5173", "https://betterbulk.netlify.app"], supports_credentials=True)
    def get_recipe_counts():
        """Get the count of recipes in the cache"""
        try:
            counts = recipe_cache.get_recipe_count()
            return jsonify({
                "status": "success",
                "data": counts
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Failed to get recipe counts: {str(e)}"
            }), 500
    
    @app.route("/get_recipe_by_id", methods=["GET", "OPTIONS"])
    @cross_origin(origins=["http://localhost:8081", "http://localhost:5173", "https://betterbulk.netlify.app"], 
                 supports_credentials=True)
    @async_route
    async def get_recipe_by_id():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
            response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
            
        recipe_id = request.args.get("id")
        if not recipe_id:
            return jsonify({"error": "Recipe ID is required"}), 400
        
        try:
            # Use the proper recipe service instead of searching through all recipes
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

    @app.route("/api/get_recipes", methods=["GET", "OPTIONS"])
    @cross_origin(origins=["http://localhost:8081", "http://localhost:5173", "https://betterbulk.netlify.app"], 
                 supports_credentials=True)
    @async_route
    async def get_recipes():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
            response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
            
        start_time = time.time()
        query = request.args.get("query", "").strip()
        ingredient = request.args.get("ingredient", "").strip()
        
        offset = int(request.args.get("offset", "0"))
        limit = int(request.args.get("limit", "1000"))  # Default to 1000 results
        
        # Debug pagination parameters
        print(f"🔍 BACKEND PAGINATION DEBUG:")
        print(f"   - Received offset: {offset}")
        print(f"   - Received limit: {limit}")
        print(f"   - Request args: {dict(request.args)}")
        
        # Get cuisine and dietary restrictions filters
        cuisine_param = request.args.get("cuisine", "")
        diet_param = request.args.get("dietary_restrictions", "")
        
        # Parse comma-separated values
        cuisines = [c.strip() for c in cuisine_param.split(",") if c.strip()] if cuisine_param else []
        dietary_restrictions = [d.strip() for d in diet_param.split(",") if d.strip()] if diet_param else []
        
        # Get user's preferences
        foods_to_avoid = []
        favorite_foods = []
        try:
            user_id = get_current_user_id()
            if user_id:
                preferences = user_preferences_service.get_preferences(user_id)
                if preferences:
                    # Get foods to avoid
                    if 'foodsToAvoid' in preferences:
                        foods_to_avoid = [f.lower() for f in preferences['foodsToAvoid'] if f and isinstance(f, str)]
                        print(f"Found {len(foods_to_avoid)} foods to avoid in user preferences")
                    
                    # Get favorite foods
                    if 'favoriteFoods' in preferences:
                        favorite_foods = [f.lower() for f in preferences['favoriteFoods'] if f and isinstance(f, str)]
                        print(f"Found {len(favorite_foods)} favorite foods in user preferences")
        except Exception as e:
            print(f"Error getting user preferences: {e}")
        
        print(f"\n=== Recipe Search Request ===")
        print(f"Query: '{query}'")
        print(f"Ingredient: '{ingredient}'")
        print(f"Cuisines: {cuisines} (type: {type(cuisines)}, length: {len(cuisines)})")
        print(f"Dietary Restrictions: {dietary_restrictions} (type: {type(dietary_restrictions)}, length: {len(dietary_restrictions)})")
        print(f"Offset: {offset}, Limit: {limit}")
        print(f"Foods to avoid: {foods_to_avoid} (type: {type(foods_to_avoid)}, length: {len(foods_to_avoid)})")
        print(f"Favorite foods: {favorite_foods} (type: {type(favorite_foods)}, length: {len(favorite_foods)})")
        print(f"Raw cuisine_param: '{cuisine_param}' (type: {type(cuisine_param)})")
        print(f"Raw diet_param: '{diet_param}' (type: {type(diet_param)})")
        print(f"Parsed dietary_restrictions: {dietary_restrictions}")
        print(f"Request args keys: {list(request.args.keys())}")
        print(f"Request args values: {dict(request.args)}")
        
        try:
            # Create service instance for this request
            from services.recipe_service import RecipeService
            service = RecipeService(recipe_cache)
            
            # Search recipes from all sources with pagination and filters
            result = await service.search_recipes(
                query=query,
                ingredient=ingredient,
                offset=offset,
                limit=limit,
                cuisines=cuisines,
                dietary_restrictions=dietary_restrictions,
                foods_to_avoid=foods_to_avoid,
                favorite_foods=favorite_foods
            )
            
            print(f"Found {result['total']} recipes in {time.time() - start_time:.2f}s")
            return jsonify(result), 200
            
        except Exception as e:
            print(f"Error searching recipes: {e}")
            return jsonify({
                "error": "Failed to search recipes",
                "details": str(e)
            }), 500


    return app
