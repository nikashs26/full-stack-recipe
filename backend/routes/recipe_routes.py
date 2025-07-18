
import requests
import os
from flask import request, jsonify
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def register_recipe_routes(app, recipe_cache):
    # Get configuration from environment variables
    SPOONACULAR_API_KEY = os.environ.get('SPOONACULAR_API_KEY')
    SPOONACULAR_BASE_URL = os.environ.get('SPOONACULAR_BASE_URL', 'https://api.spoonacular.com')
    SPOONACULAR_URL = f"{SPOONACULAR_BASE_URL}/recipes/complexSearch"
    
    if not SPOONACULAR_API_KEY:
        print("Warning: SPOONACULAR_API_KEY not found in environment variables")
    else:
        print(f"Using Spoonacular API key: {SPOONACULAR_API_KEY[:5]}...")
    
    @app.route("/get_recipes", methods=["GET"])
    def get_recipes():
        start_time = time.time()
        query = request.args.get("query", "").strip()
        ingredient = request.args.get("ingredient", "").strip()
        
        print(f"\n=== Recipe Search Request ===")
        print(f"Query: '{query}'")
        print(f"Ingredient: '{ingredient}'")
        
        # First check ChromaDB cache
        cached_results = recipe_cache.get_cached_recipes(query, ingredient)
        if cached_results:
            print(f"Found {len(cached_results)} recipes in ChromaDB cache")
            return jsonify({"results": cached_results}), 200
        else:
            print("No cached results found, querying Spoonacular API")
        
        # Check if we have a valid API key
        if not SPOONACULAR_API_KEY:
            return jsonify({
                "error": "Spoonacular API key not configured",
                "message": "Please configure SPOONACULAR_API_KEY in environment variables"
            }), 500
        
        # If no search parameters, return some default popular recipes
        if not query and not ingredient:
            # Try to get some popular recipes from Spoonacular API
            try:
                params = {
                    "apiKey": SPOONACULAR_API_KEY,
                    "number": 12,
                    "addRecipeInformation": "true",
                    "fillIngredients": "true",
                    "instructionsRequired": "true",
                    "sort": "popularity"
                }
                
                print(f"\nCalling Spoonacular API for popular recipes")
                print(f"URL: {SPOONACULAR_URL}")
                print(f"Params: {params}")
                
                response = requests.get(SPOONACULAR_URL, params=params, timeout=10)
                print(f"\nSpoonacular API Response:")
                print(f"Status Code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.ok:
                    data = response.json()
                    print(f"\nResponse Data:")
                    print(f"Has 'results' key: {'results' in data}")
                    if "results" in data:
                        print(f"Number of results: {len(data['results'])}")
                        if len(data['results']) > 0:
                            print(f"First recipe title: {data['results'][0].get('title', 'No title')}")
                            # Cache the results in ChromaDB
                            recipe_cache.cache_recipes(data['results'], query, ingredient)
                            print("Cached results in ChromaDB")
                        return jsonify(data)
                    else:
                        print(f"Response content: {response.text[:200]}...")
                else:
                    try:
                        error_data = response.json()
                        if response.status_code == 402 and "message" in error_data:
                            error_msg = "API rate limit reached. Using cached results if available."
                            print(f"Rate limit error: {error_data['message']}")
                            # Try to get any cached results as fallback
                            cached_results = recipe_cache.get_cached_recipes("", "")
                            if cached_results:
                                print(f"Found {len(cached_results)} cached recipes to use as fallback")
                                return jsonify({
                                    "results": cached_results,
                                    "warning": error_msg
                                }), 200
                            return jsonify({
                                "error": error_msg,
                                "code": response.status_code,
                                "results": []
                            }), response.status_code
                        else:
                            print(f"Error response content: {response.text[:200]}...")
                    except:
                        print(f"Error response content: {response.text[:200]}...")
            except Exception as e:
                print(f"Error fetching popular recipes: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                # Try to get cached results as fallback
                cached_results = recipe_cache.get_cached_recipes("", "")
                if cached_results:
                    print(f"Found {len(cached_results)} cached recipes to use as fallback")
                    return jsonify({
                        "results": cached_results,
                        "warning": "Using cached results due to API error"
                    }), 200
            
            return jsonify({"results": []}), 200

        # Search for specific recipes
        print(f"\nSearching Spoonacular for recipes")
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "number": 10,
            "addRecipeInformation": "true",
            "fillIngredients": "true",
            "instructionsRequired": "true"
        }
        
        if query:
            params["query"] = query
        if ingredient:
            params["includeIngredients"] = ingredient

        try:
            print(f"\nCalling Spoonacular API")
            print(f"URL: {SPOONACULAR_URL}")
            print(f"Params: {params}")
            
            response = requests.get(SPOONACULAR_URL, params=params, timeout=10)
            print(f"\nSpoonacular API Response:")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if not response.ok:
                error_msg = f"Spoonacular API error (Status: {response.status_code})"
                try:
                    error_data = response.json()
                    if response.status_code == 402 and "message" in error_data:
                        error_msg = "API rate limit reached. Using cached results if available."
                        print(f"Rate limit error: {error_data['message']}")
                        # Try to get cached results as fallback
                        cached_results = recipe_cache.get_cached_recipes(query, ingredient)
                        if cached_results:
                            print(f"Found {len(cached_results)} cached recipes to use as fallback")
                            return jsonify({
                                "results": cached_results,
                                "warning": error_msg
                            }), 200
                    else:
                        print(f"Error response content: {response.text[:200]}...")
                except:
                    print(f"Error response content: {response.text[:200]}...")
                return jsonify({
                    "error": error_msg,
                    "code": response.status_code
                }), response.status_code
            
            data = response.json()
            print(f"\nResponse Data:")
            print(f"Has 'results' key: {'results' in data}")
            if "results" in data:
                print(f"Number of results: {len(data['results'])}")
                if len(data['results']) > 0:
                    print(f"First recipe title: {data['results'][0].get('title', 'No title')}")
                    # Cache the results in ChromaDB
                    recipe_cache.cache_recipes(data['results'], query, ingredient)
                    print("Cached results in ChromaDB")
            else:
                print(f"Response content: {response.text[:200]}...")

            if "results" not in data:
                return jsonify({"error": "Invalid response from Spoonacular"}), 500

            return jsonify(data), 200
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error calling Spoonacular API: {str(e)}"
            print(error_msg)
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Try to get cached results as fallback
            cached_results = recipe_cache.get_cached_recipes(query, ingredient)
            if cached_results:
                print(f"Found {len(cached_results)} cached recipes to use as fallback")
                return jsonify({
                    "results": cached_results,
                    "warning": "Using cached results due to API error"
                }), 200
            return jsonify({"error": error_msg}), 500

    @app.route("/get_recipe_by_id", methods=["GET"])
    def get_recipe_by_id():
        recipe_id = request.args.get("id")
        if not recipe_id:
            return jsonify({"error": "Recipe ID is required"}), 400
            
        if not SPOONACULAR_API_KEY:
            return jsonify({
                "error": "Spoonacular API key not configured",
                "message": "Please configure SPOONACULAR_API_KEY in environment variables"
            }), 500
            
        try:
            api_url = f"{SPOONACULAR_BASE_URL}/recipes/{recipe_id}/information"
            params = {"apiKey": SPOONACULAR_API_KEY}
            
            response = requests.get(api_url, params=params, timeout=10)
            print(f"Spoonacular API response status for recipe {recipe_id}: {response.status_code}")
            
            if not response.ok:
                error_msg = f"Failed to fetch recipe (Status: {response.status_code})"
                print(error_msg)
                return jsonify({"error": error_msg}), response.status_code
                
            data = response.json()
            print(f"Got recipe {recipe_id} from Spoonacular")
            return jsonify(data), 200
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching recipe {recipe_id}: {str(e)}"
            print(error_msg)
            return jsonify({"error": error_msg}), 500

    return app
