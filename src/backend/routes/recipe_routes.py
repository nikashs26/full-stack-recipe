
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
        print("\n=== /get_recipes endpoint called ===")
        print(f"Query params: {request.args}")
        
        try:
            # Get query parameters
            query = request.args.get('query', '').strip()
            ingredient = request.args.get('ingredient', '').strip()
            print(f"Search query: '{query}', Ingredient: '{ingredient}'")
            
            # Get all recipes from ChromaDB
            print("Fetching recipes from ChromaDB...")
            try:
                results = recipe_cache.recipe_collection.get()
                print(f"ChromaDB response received. Keys: {list(results.keys()) if results else 'No results'}")
            except Exception as e:
                print(f"Error fetching from ChromaDB: {str(e)}")
                return jsonify({
                    'results': [],
                    'message': 'Error fetching recipes from database',
                    'success': False,
                    'error': str(e)
                }), 500
            
            if not results or 'documents' not in results or not results['documents']:
                print("No documents found in ChromaDB response")
                return jsonify({
                    'results': [],
                    'message': 'No recipes found in database',
                    'success': True,
                    'total': 0
                })
            
            print(f"Found {len(results['documents'])} documents in ChromaDB")
            
            # Parse the JSON strings in documents
            recipes = []
            for i, doc in enumerate(results['documents']):
                try:
                    print(f"\n--- Processing document {i+1}/{len(results['documents'])} ---")
                    print(f"Document type: {type(doc)}")
                    
                    # Handle case where doc might already be a dict
                    if isinstance(doc, dict):
                        print("Document is already a dictionary")
                        recipe = doc
                    elif isinstance(doc, str):
                        # Try to parse as JSON
                        try:
                            recipe = json.loads(doc)
                            print("Successfully parsed document as JSON")
                        except json.JSONDecodeError as e:
                            print(f"Error parsing document as JSON: {e}")
                            # Handle as raw string
                            print("Handling as raw string")
                            recipe = {
                                'id': f'raw_{i}',
                                'title': 'Untitled Recipe',
                                'ingredients': [],
                                'instructions': doc,
                                'source': 'chromadb'
                            }
                    else:
                        print(f"Skipping document of type {type(doc)}")
                        continue
                    
                    # Ensure recipe is a dictionary
                    if not isinstance(recipe, dict):
                        print(f"Skipping non-dict recipe: {recipe}")
                        continue
                    
                    # Normalize recipe fields
                    recipe.setdefault('id', str(hash(str(doc))))
                    recipe.setdefault('title', 'Untitled Recipe')
                    recipe.setdefault('ingredients', [])
                    recipe.setdefault('instructions', [])
                    recipe.setdefault('cuisines', [])
                    recipe.setdefault('diets', [])
                    recipe.setdefault('image', '')
                    recipe.setdefault('source', 'chromadb')
                    
                    # Handle different field naming conventions
                    if 'cuisine' in recipe and not recipe['cuisines']:
                        recipe['cuisines'] = [recipe.pop('cuisine')]
                    
                    print(f"Processed recipe: {recipe.get('id')} - {recipe.get('title')}")
                    recipes.append(recipe)
                    
                except Exception as e:
                    print(f"Error processing document {i+1}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Apply search filters if provided
            if query or ingredient:
                query_lower = query.lower()
                ingredient_lower = ingredient.lower()
                
                def matches_search(r):
                    # Match query in title or ingredients
                    matches_query = not query or \
                        (isinstance(r.get('title'), str) and query_lower in r['title'].lower()) or \
                        (isinstance(r.get('ingredients'), list) and 
                         any(ing.get('name', '').lower().find(query_lower) != -1 for ing in r['ingredients'] 
                             if isinstance(ing, dict) and 'name' in ing))
                    
                    # Match ingredient filter
                    matches_ingredient = not ingredient or \
                        (isinstance(r.get('ingredients'), list) and 
                         any(ing.get('name', '').lower().find(ingredient_lower) != -1 for ing in r['ingredients'] 
                             if isinstance(ing, dict) and 'name' in ing))
                    
                    return matches_query and matches_ingredient
                
                filtered_recipes = [r for r in recipes if matches_search(r)]
                print(f"Filtered {len(recipes)} recipes to {len(filtered_recipes)} matching search criteria")
                recipes = filtered_recipes
            
            print(f"\nSuccessfully processed {len(recipes)} recipes")
            return jsonify({
                'results': recipes,
                'total': len(recipes),
                'success': True,
                'message': f'Found {len(recipes)} recipes'
            })
            
        except Exception as e:
            error_msg = f"Error in /get_recipes: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return jsonify({
                'results': [],
                'message': 'An error occurred while fetching recipes',
                'error': str(e),
                'success': False
            }), 500

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
