
import json
import requests
from flask import request, jsonify
import time
from bson import ObjectId
from datetime import datetime
from services.recipe_cache_service import RecipeCacheService

# Initialize recipe cache service
recipe_cache = RecipeCacheService()

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def register_recipe_routes(app, recipe_cache):
    from services.user_preferences_service import UserPreferencesService
    user_preferences_service = UserPreferencesService()

    @app.route('/recommend_recipes', methods=['GET'])
    def recommend_recipes():
        # Accept user_id (email) or temp_user_id as query param
        user_id = request.args.get('user_id')
        temp_user_id = request.args.get('temp_user_id')
        preferences = None
        if user_id:
            preferences = user_preferences_service.get_preferences(user_id)
        elif temp_user_id:
            preferences = user_preferences_service.get_preferences(temp_user_id)
        if not preferences:
            return jsonify({'results': [], 'message': 'No preferences found for user'}), 200

        # Load all recipes
        all_results = recipe_cache.collection.get()
        recipes = []
        if all_results and all_results["documents"]:
            for doc in all_results["documents"]:
                try:
                    rec = json.loads(doc)
                    if isinstance(rec, list):
                        recipes.extend(rec)
                    else:
                        recipes.append(rec)
                except Exception:
                    pass

        # Scoring: prioritize favoriteFoods, then cuisines, then dietaryRestrictions, then allergens (penalty)
        fav_foods = [f.lower() for f in preferences.get('favoriteFoods', []) if f]
        fav_cuisines = [c.lower() for c in preferences.get('favoriteCuisines', [])]
        dietary = [d.lower() for d in preferences.get('dietaryRestrictions', [])]
        allergens = [a.lower() for a in preferences.get('allergens', [])]

        def score(recipe):
            score = 0
            title = recipe.get('title', '').lower()
            ingredients = ' '.join(recipe.get('ingredients', [])).lower() if recipe.get('ingredients') else ''
            cuisine = ' '.join(recipe.get('cuisines', [])).lower() if recipe.get('cuisines') else ''
            diets = ' '.join(recipe.get('diets', [])).lower() if recipe.get('diets') else ''
            # Favorite foods: +10 for each match in title or ingredients
            for food in fav_foods:
                if food and (food in title or food in ingredients):
                    score += 10
            # Cuisine: +3 for each match
            for c in fav_cuisines:
                if c and c in cuisine:
                    score += 3
            # Dietary: +2 for each match
            for d in dietary:
                if d and d in diets:
                    score += 2
            # Allergen penalty: -10 for each match in ingredients
            for a in allergens:
                if a and a in ingredients:
                    score -= 10
            return score
        
        ranked = sorted(recipes, key=score, reverse=True)
        return jsonify({'results': ranked[:20]})

    SPOONACULAR_API_KEY = "01f12ed117584307b5cba262f43a8d49"
    SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"
    
    @app.route("/get_recipes", methods=["GET"])
    def get_recipes():
        try:
            # Get all recipes from ChromaDB
            results = recipe_cache.recipe_collection.get()
            
            if not results or 'documents' not in results:
                return jsonify({'results': [], 'message': 'No recipes found in ChromaDB'})
            
            # Parse the JSON strings in documents
            recipes = []
            for doc in results['documents']:
                try:
                    recipe = json.loads(doc)
                    # Ensure the recipe has required fields
                    if not recipe.get('id'):
                        recipe['id'] = str(hash(doc))  # Generate a unique ID if missing
                    if not recipe.get('cuisines') and recipe.get('cuisine'):
                        recipe['cuisines'] = [recipe['cuisine']]
                    if not recipe.get('diets'):
                        recipe['diets'] = []
                    if not recipe.get('image'):
                        recipe['image'] = ''  # Add default image if missing
                    recipes.append(recipe)
                except json.JSONDecodeError:
                    continue
            
            return jsonify({'results': recipes})
        except Exception as e:
            print(f"Error fetching from ChromaDB: {e}")
        
        # 2. Get hardcoded/fallback recipes
        try:
            from lib.spoonacular import FALLBACK_RECIPES
            
            # Filter fallback recipes based on search terms
            filtered_fallback = []
            for recipe in FALLBACK_RECIPES:
                matches = True
                
                # Match query against title and cuisine
                if query:
                    query_lower = query.lower()
                    title_match = recipe['title'].lower().find(query_lower) != -1
                    cuisine_match = any(c.lower().find(query_lower) != -1 for c in recipe.get('cuisines', []))
                    if not (title_match or cuisine_match):
                        matches = False
                
                # Match ingredient in title (since fallback recipes don't have detailed ingredients)
                if ingredient and matches:
                    if recipe['title'].lower().find(ingredient.lower()) == -1:
                        matches = False
                
                if matches:
                    filtered_fallback.append(recipe)
            
            print(f"Found {len(filtered_fallback)} matching fallback recipes")
            all_recipes.extend(filtered_fallback)
        except Exception as e:
            print(f"Error processing fallback recipes: {e}")
        
        # Remove duplicates based on recipe ID
        seen_ids = set()
        unique_recipes = []
        for recipe in all_recipes:
            recipe_id = str(recipe.get('id'))
            if recipe_id not in seen_ids:
                seen_ids.add(recipe_id)
                unique_recipes.append(recipe)
        
        print(f"Returning {len(unique_recipes)} total unique recipes")
        return jsonify({"results": unique_recipes})

    # Add a route to test specific queries and show cache usage
    @app.route("/test/query", methods=["GET"])
    def test_query():
        query = request.args.get("q", "")
        
        # Check cache first
        cached_recipes = recipe_cache.get_cached_recipes(query, "")
        if cached_recipes:
            return jsonify({
                "source": "cache",
                "query": query,
                "results": cached_recipes[:5],  # Return first 5 for testing
                "total_cached": len(cached_recipes)
            })
        
        # If not in cache, return message
        return jsonify({
            "source": "not_cached",
            "query": query,
            "message": f"Query '{query}' not found in cache. Try calling /get_recipes?query={query} first."
        })

    # Add a route to clear the cache
    @app.route("/cache/clear", methods=["POST"])
    def clear_cache():
        success = recipe_cache.clear_cache()
        if success:
            return jsonify({"message": "Cache cleared successfully"})
        else:
            return jsonify({"error": "Failed to clear cache"}), 500

    # Add a route to get cache statistics
    @app.route("/cache/stats", methods=["GET"])
    def get_cache_stats():
        stats = recipe_cache.get_cache_stats()
        return jsonify(stats)

    @app.route("/get_recipe_by_id", methods=["GET"])
    def get_recipe_by_id():
        recipe_id = request.args.get("id")
        if not recipe_id:
            return jsonify({"error": "Recipe ID is required"}), 400
        
        # First check if we have this recipe in MongoDB
        if mongo_available:
            try:
                # Try to find as integer ID (for external recipes)
                try:
                    db_recipe = recipes_collection.find_one({"id": int(recipe_id)})
                except ValueError:
                    # If not an integer, look for it as a string (for local recipes)
                    db_recipe = recipes_collection.find_one({"id": recipe_id})
                    
                if db_recipe:
                    print(f"Found recipe {recipe_id} in MongoDB database")
                    return JSONEncoder().encode(db_recipe)
            except Exception as e:
                print(f"Error querying MongoDB for recipe {recipe_id}: {e}")
        else:
            # Check in-memory storage
            for recipe in in_memory_recipes:
                if str(recipe.get("id")) == str(recipe_id):
                    print(f"Found recipe {recipe_id} in in-memory storage")
                    return jsonify(recipe)
        
        # If not in storage, call the Spoonacular API
        api_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        params = {"apiKey": SPOONACULAR_API_KEY}
        
        try:
            print(f"Calling Spoonacular API for recipe {recipe_id}")
            response = requests.get(api_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Ensure recipe has all necessary fields
            if "title" not in data:
                data["title"] = "Untitled Recipe"
            if "cuisines" not in data or not data["cuisines"]:
                data["cuisines"] = ["Misc"]
            
            # Normalize diets for consistent filtering
            if "diets" in data:
                normalized_diets = []
                for diet in data["diets"]:
                    diet_lower = diet.lower()
                    if "vegetarian" in diet_lower:
                        normalized_diets.append("vegetarian")
                    if "vegan" in diet_lower:
                        normalized_diets.append("vegan")
                    if "gluten" in diet_lower and "free" in diet_lower:
                        normalized_diets.append("gluten-free")
                    if "carnivore" in diet_lower or "meat" in diet_lower:
                        normalized_diets.append("carnivore")
                    # Keep the original diet as well
                    normalized_diets.append(diet)
                data["diets"] = normalized_diets
                
            # Store in MongoDB for future queries
            try:
                if mongo_available:
                    existing = recipes_collection.find_one({"id": data["id"]})
                    if not existing:
                        recipes_collection.insert_one(data)
                        print(f"Stored recipe {recipe_id} in MongoDB Atlas")
                else:
                    # Store in in-memory cache
                    if not any(r.get("id") == data["id"] for r in in_memory_recipes):
                        in_memory_recipes.append(data)
                        print(f"Stored recipe {recipe_id} in in-memory storage")
            except Exception as e:
                print(f"Error storing recipe {recipe_id}: {e}")
            
            return jsonify(data)
        except requests.exceptions.Timeout:
            return jsonify({"error": "Request to Spoonacular API timed out"}), 504
        except requests.exceptions.RequestException as e:
            return jsonify({"error": str(e)}), 500

    # Endpoints for direct MongoDB CRUD operations
    @app.route("/recipes", methods=["GET"])
    def get_all_recipes():
        try:
            # Get all recipes from Chroma
            all_results = recipe_cache.recipe_collection.get(
                include=["documents", "metadatas"]
            )
            recipes = []
            if all_results and all_results["documents"]:
                for doc in all_results["documents"]:
                    try:
                        recipe = json.loads(doc)
                        recipes.append(recipe)
                    except Exception:
                        pass
            return jsonify({"results": recipes}), 200
        except Exception as e:
            return jsonify({"results": [], "error": str(e)}), 200


    @app.route("/recipes/<recipe_id>", methods=["GET"])
    def get_recipe_from_db(recipe_id):
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            # Try first as ObjectId
            try:
                recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
            except:
                # Then try as regular id
                recipe = recipes_collection.find_one({"id": recipe_id})
                if not recipe:
                    try:
                        recipe = recipes_collection.find_one({"id": int(recipe_id)})
                    except ValueError:
                        pass
                    
            if recipe:
                return JSONEncoder().encode(recipe)
            return jsonify({"error": "Recipe not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/recipes", methods=["POST"])
    def add_recipe_to_db():
        try:
            recipe = request.json
            if not recipe:
                return jsonify({"error": "Recipe data is required"}), 400
            if "title" not in recipe:
                recipe["title"] = "Untitled Recipe"
            if "id" not in recipe:
                recipe["id"] = str(int(time.time() * 1000))  # simple unique ID
            # Store in Chroma
            recipe_cache.cache_recipes([recipe], query=recipe.get("title", ""), ingredient="")
            return jsonify({"message": "Recipe added", "id": recipe["id"]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/recipes/<recipe_id>", methods=["PUT"])
    def update_recipe_in_db(recipe_id):
        try:
            recipe = request.json
            if not recipe:
                return jsonify({"error": "Recipe data is required"}), 400
            # For Chroma, simply cache the updated recipe (replace by ID)
            recipe["id"] = recipe_id
            recipe_cache.cache_recipes([recipe], query=recipe.get("title", ""), ingredient="")
            return jsonify({"message": "Recipe updated"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/recipes/<recipe_id>", methods=["DELETE"])
    def delete_recipe_from_db(recipe_id):
        try:
            # Chroma: delete by cache key (ID)
            # This assumes you use recipe ID as a cache key, or you can extend RecipeCacheService
            recipe_cache.collection.delete(ids=[recipe_id])
            return jsonify({"message": "Recipe deleted"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
