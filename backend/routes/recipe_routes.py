
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

def register_recipe_routes(app, recipes_collection, mongo_available, in_memory_recipes):
    SPOONACULAR_API_KEY = "01f12ed117584307b5cba262f43a8d49"
    SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"
    
    @app.route("/get_recipes", methods=["GET"])
    def get_recipes():
        start_time = time.time()
        query = request.args.get("query", "").strip()
        ingredient = request.args.get("ingredient", "").strip()
        
        # Check ChromaDB cache first
        cached_recipes = recipe_cache.get_cached_recipes(query, ingredient)
        if cached_recipes:
            print(f"Returning {len(cached_recipes)} cached recipes for query: '{query}', ingredient: '{ingredient}'")
            return jsonify({"results": cached_recipes})
        
        # If no search parameters, return some default popular recipes
        if not query and not ingredient:
            # Try to get some popular recipes from Spoonacular API
            try:
                params = {
                    "apiKey": SPOONACULAR_API_KEY,
                    "number": 12,
                    "addRecipeInformation": "true",
                    "sort": "popularity"
                }
                
                response = requests.get(SPOONACULAR_URL, params=params, timeout=5)
                if response.ok and 'application/json' in response.headers.get('Content-Type', ''):
                    data = response.json()
                    if "results" in data:
                        # Cache the results
                        recipe_cache.cache_recipes(data["results"], query, ingredient)
                        return jsonify(data)
            except Exception as e:
                print(f"Error fetching popular recipes: {e}")
            
            # If API fails, return empty results
            return jsonify({"results": []}), 200

        # First check if we have recipes in MongoDB that match the query
        db_results = []
        if mongo_available:
            try:
                search_query = {}
                if query:
                    search_query["title"] = {"$regex": query, "$options": "i"}
                if ingredient:
                    search_query["$or"] = [
                        {"extendedIngredients.name": {"$regex": ingredient, "$options": "i"}},
                        {"ingredients": {"$regex": ingredient, "$options": "i"}}
                    ]
                
                print(f"Searching MongoDB with query: {search_query}")
                db_results = list(recipes_collection.find(search_query).limit(10))
                print(f"MongoDB search returned {len(db_results)} results")
                
                if db_results:
                    print(f"Found {len(db_results)} recipes in database in {time.time() - start_time:.2f}s")
                    # Cache the MongoDB results
                    recipe_cache.cache_recipes(db_results, query, ingredient)
                    return JSONEncoder().encode({"results": db_results})
                else:
                    print("No results found in MongoDB, falling back to Spoonacular API")
            except Exception as e:
                print(f"Error querying MongoDB: {e}")
                # Continue to in-memory or API if MongoDB query fails
        else:
            print("MongoDB not available, checking in-memory storage")
        
        # If MongoDB is not available or no results, check in-memory storage
        if not mongo_available:
            results = []
            for recipe in in_memory_recipes:
                if (query and query.lower() in recipe.get("title", "").lower()) or \
                (ingredient and ingredient.lower() in json.dumps(recipe).lower()):
                    results.append(recipe)
            if results:
                print(f"Found {len(results)} recipes in in-memory storage")
                # Cache the in-memory results
                recipe_cache.cache_recipes(results, query, ingredient)
                return jsonify({"results": results})

        # If no results in DB or in-memory, call the Spoonacular API
        print("No results found locally, calling Spoonacular API")
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "number": 10,  # Limit to 10 results
            "addRecipeInformation": "true",
        }
        
        if query:
            params["query"] = query
        if ingredient:
            params["includeIngredients"] = ingredient

        try:
            # Use a short timeout to avoid hanging
            print(f"Calling Spoonacular API with params: {params}")
            response = requests.get(SPOONACULAR_URL, params=params, timeout=5)
            
            # Check if content type is JSON
            if 'application/json' not in response.headers.get('Content-Type', ''):
                return jsonify({
                    "error": f"API returned non-JSON response. Status: {response.status_code}",
                    "message": response.text[:100] + "..." # Show part of the response for debugging
                }), 500
                
            response.raise_for_status()  # Raise an error for HTTP failures
            data = response.json()

            if "results" not in data:
                return jsonify({"error": "Invalid response from Spoonacular"}), 500

            # Process the diets for filtering consistency
            for recipe in data["results"]:
                # Normalize diet names for consistent filtering
                if "diets" in recipe:
                    normalized_diets = []
                    for diet in recipe["diets"]:
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
                    recipe["diets"] = normalized_diets

            # Cache the API results in ChromaDB
            recipe_cache.cache_recipes(data["results"], query, ingredient)

            # Store results in MongoDB for future queries
            api_store_count = 0
            try:
                if mongo_available:
                    for recipe in data["results"]:
                        # Ensure recipe has all necessary fields
                        if "title" not in recipe:
                            recipe["title"] = "Untitled Recipe"
                        if "cuisines" not in recipe or not recipe["cuisines"]:
                            recipe["cuisines"] = ["Misc"]
                            
                        # Check if recipe already exists in the database
                        try:
                            # Try with recipe ID as integer
                            existing = recipes_collection.find_one({"id": recipe["id"]})
                        except:
                            # If not an integer, try as string
                            existing = recipes_collection.find_one({"id": str(recipe["id"])})
                            
                        if not existing:
                            # Insert to MongoDB and ensure proper indexing
                            recipes_collection.insert_one(recipe)
                            api_store_count += 1
                    print(f"Stored {api_store_count} new recipes in MongoDB Atlas")
                else:
                    # Store in in-memory cache if MongoDB not available
                    for recipe in data["results"]:
                        if not any(r.get("id") == recipe["id"] for r in in_memory_recipes):
                            in_memory_recipes.append(recipe)
                    print(f"Stored {len(data['results'])} recipes in in-memory storage")
            except Exception as e:
                print(f"Error storing recipes: {e}")

            print(f"API request completed in {time.time() - start_time:.2f}s")
            return jsonify(data)  # Send results to frontend

        except requests.exceptions.Timeout:
            return jsonify({"error": "Request to Spoonacular API timed out", "results": []}), 504
        except ValueError as e:  # JSON parsing error
            return jsonify({
                "error": "Failed to parse API response as JSON",
                "message": str(e),
                "results": []
            }), 500
        except requests.exceptions.RequestException as e:
            return jsonify({"error": str(e), "results": []}), 500

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
        if not mongo_available:
            # Return fallback data when MongoDB is not available
            return jsonify({"results": in_memory_recipes}), 200
        
        try:
            recipes = list(recipes_collection.find())
            return JSONEncoder().encode({"results": recipes})
        except Exception as e:
            # If MongoDB query fails, return fallback data
            return jsonify({"results": in_memory_recipes}), 200

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
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            recipe = request.json
            if not recipe:
                return jsonify({"error": "Recipe data is required"}), 400
            
            # Ensure recipe has all necessary fields
            if "title" not in recipe:
                recipe["title"] = "Untitled Recipe"
                
            # If no ID is provided, generate one
            if "id" not in recipe:
                recipe["id"] = str(ObjectId())
                
            # Check if recipe already exists
            existing = None
            if "id" in recipe:
                try:
                    existing = recipes_collection.find_one({"id": recipe["id"]})
                except:
                    # Try as integer if string fails
                    try:
                        existing = recipes_collection.find_one({"id": int(recipe["id"])})
                    except ValueError:
                        pass
            
            if existing:
                recipes_collection.update_one({"id": recipe["id"]}, {"$set": recipe})
                return jsonify({"message": "Recipe updated", "id": recipe["id"]})
            else:
                result = recipes_collection.insert_one(recipe)
                return jsonify({"message": "Recipe added", "id": recipe["id"] if "id" in recipe else str(result.inserted_id)})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/recipes/<recipe_id>", methods=["PUT"])
    def update_recipe_in_db(recipe_id):
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            recipe = request.json
            if not recipe:
                return jsonify({"error": "Recipe data is required"}), 400
            
            # Try to update by ObjectId first
            try:
                result = recipes_collection.update_one({"_id": ObjectId(recipe_id)}, {"$set": recipe})
            except:
                # Then try by regular id
                result = recipes_collection.update_one({"id": recipe_id}, {"$set": recipe})
                
            if result.matched_count == 0:
                return jsonify({"error": "Recipe not found"}), 404
            
            return jsonify({"message": "Recipe updated"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/recipes/<recipe_id>", methods=["DELETE"])
    def delete_recipe_from_db(recipe_id):
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            # Try to delete by ObjectId first
            try:
                result = recipes_collection.delete_one({"_id": ObjectId(recipe_id)})
            except:
                # Then try by regular id
                result = recipes_collection.delete_one({"id": recipe_id})
                if result.deleted_count == 0:
                    try:
                        result = recipes_collection.delete_one({"id": int(recipe_id)})
                    except ValueError:
                        pass
                    
            if result.deleted_count == 0:
                return jsonify({"error": "Recipe not found"}), 404
            
            return jsonify({"message": "Recipe deleted"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
