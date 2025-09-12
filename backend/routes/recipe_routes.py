
import requests
import json
import os
from flask import request, jsonify, make_response
import time
# Try to import dotenv, fallback if not available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not available, using environment variables only")
    def load_dotenv():
        pass  # No-op fallback
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
                # Fix data structure - if recipe has nested data, extract the actual recipe data
                if 'data' in recipe and isinstance(recipe['data'], dict):
                    # Extract the actual recipe data from the nested structure
                    recipe_data = recipe['data']
                    
                    # Merge in any additional fields from the top level that might be useful
                    if 'id' in recipe and 'id' not in recipe_data:
                        recipe_data['id'] = recipe['id']
                    if 'source' in recipe and 'source' not in recipe_data:
                        recipe_data['source'] = recipe['source']
                    
                    return jsonify(recipe_data), 200
                elif 'document' in recipe and isinstance(recipe['document'], str):
                    try:
                        import json
                        document_data = json.loads(recipe['document'])
                        # Return the merged document data instead of the nested structure
                        return jsonify(document_data), 200
                    except:
                        pass
                
                # If no nested data structure, return the recipe as-is
                return jsonify(recipe), 200
            else:
                return jsonify({"error": "Recipe not found"}), 404
            
        except Exception as e:
            print(f"Error fetching recipe {recipe_id}: {e}")
            return jsonify({
                "error": "Failed to fetch recipe",
                "details": str(e)
            }), 500

    # Add alias for frontend compatibility
    @app.route("/api/recipes", methods=["GET", "OPTIONS"])
    @cross_origin(origins=["http://localhost:8081", "http://localhost:5173", "https://betterbulk.netlify.app"], 
                 supports_credentials=True)
    @async_route
    async def get_recipes_alias():
        return await get_recipes()

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
        limit = int(request.args.get("limit", "10000"))  # Default to 10000 results to show more recipes
        
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

    @app.route("/api/recipes/cuisines", methods=["GET", "OPTIONS"])
    @cross_origin(origins=["http://localhost:8081", "http://localhost:5173", "https://betterbulk.netlify.app"], 
                 supports_credentials=True)
    def get_cuisines():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
            response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
            
        try:
            # Get all unique cuisines from the recipe cache
            cuisines = recipe_service.get_all_cuisines()
            return jsonify({"cuisines": cuisines}), 200
        except Exception as e:
            print(f"Error fetching cuisines: {e}")
            return jsonify({
                "error": "Failed to fetch cuisines",
                "details": str(e)
            }), 500

    # --- Admin: export all recipes (protected) ---
    @app.route("/api/admin/export-recipes", methods=["GET"])  # server-to-server
    def admin_export_recipes():
        admin_token = request.headers.get("X-Admin-Token", "")
        expected = os.environ.get("ADMIN_TOKEN") or os.environ.get("ADMIN_SEED_TOKEN", "")
        if not expected or admin_token != expected:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        try:
            # Collect all recipes from Chroma in batches
            total_count = recipe_cache.recipe_collection.count()
            all_docs = []
            batch_size = 1000
            fetched = 0
            # Try direct get in chunks
            while fetched < total_count:
                try:
                    batch = recipe_cache.recipe_collection.get(
                        include=["documents", "metadatas"],
                        limit=min(batch_size, total_count - fetched),
                        offset=fetched
                    )
                    docs = batch.get("documents") or []
                    metas = batch.get("metadatas") or []
                    if isinstance(docs, list) and isinstance(metas, list):
                        # Some clients return flat lists; normalize
                        if len(docs) and isinstance(docs[0], list):
                            docs = docs[0]
                            metas = metas[0]
                        for d in docs:
                            try:
                                all_docs.append(json.loads(d))
                            except Exception:
                                pass
                    fetched += len(docs) if isinstance(docs, list) else 0
                    if len(docs) == 0:
                        break
                except Exception:
                    break
            return jsonify({
                "status": "success",
                "total": len(all_docs),
                "recipes": all_docs
            }), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # --- Admin: cleanup prior assistant imports (dry-run or delete) ---
    @app.route("/api/admin/assist-cleanup", methods=["GET", "POST"])  # server-to-server
    def admin_assist_cleanup():
        admin_token = request.headers.get("X-Admin-Token", "")
        expected = os.environ.get("ADMIN_TOKEN") or os.environ.get("ADMIN_SEED_TOKEN", "")
        if not expected or admin_token != expected:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        try:
            # Identify by id prefix or source metadata
            where_filter = {"$or": [
                {"id": {"$contains": "assist_"}},
                {"source": {"$eq": "assistant"}}
            ]}
        except Exception:
            # If where expressions unsupported, fall back to client-side filter
            where_filter = None

        try:
            # Fetch all and filter client-side (more compatible)
            total = recipe_cache.recipe_collection.count()
            ids_to_delete = []
            metas_to_check = []
            step = 1000
            grabbed = 0
            while grabbed < total:
                batch = recipe_cache.recipe_collection.get(include=["metadatas"], limit=min(step, total - grabbed), offset=grabbed)
                metas = batch.get("metadatas") or []
                if len(metas) and isinstance(metas[0], list):
                    metas = metas[0]
                # We must also fetch ids in same call if available
                ids = batch.get("ids") or []
                if len(ids) and isinstance(ids[0], list):
                    ids = ids[0]
                for meta, rid in zip(metas, ids):
                    mid = str(meta.get("id") or rid or "")
                    src = str(meta.get("source", ""))
                    if mid.startswith("assist_") or src == "assistant":
                        ids_to_delete.append(mid or rid)
                grabbed += len(metas)

            dry = request.method == "GET" or str(request.args.get("dry_run", "false")).lower() == "true"
            if dry:
                return jsonify({
                    "status": "success",
                    "would_delete": len(ids_to_delete)
                }), 200

            # Delete in chunks
            deleted = 0
            for i in range(0, len(ids_to_delete), 500):
                chunk = ids_to_delete[i:i+500]
                try:
                    recipe_cache.recipe_collection.delete(ids=chunk)
                    deleted += len(chunk)
                except Exception as e:
                    print(f"Delete chunk failed: {e}")
            return jsonify({"status": "success", "deleted": deleted}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # --- Admin: import recipes in bulk (protected) ---
    @app.route("/api/admin/import-recipes", methods=["POST"])  # No CORS needed for server-to-server
    def admin_import_recipes():
        try:
            admin_token = request.headers.get("X-Admin-Token", "")
            expected = os.environ.get("ADMIN_TOKEN") or os.environ.get("ADMIN_SEED_TOKEN", "")
            if not expected or admin_token != expected:
                return jsonify({"status": "error", "message": "Unauthorized"}), 401

            # Determine source of recipes: request JSON or file on disk
            payload = request.get_json(silent=True) or {}
            recipes = payload.get("recipes")
            if not recipes:
                file_path = payload.get("file") or os.environ.get("ASSISTANT_RECIPES_FILE", "assistant_recipes_curated_200.json")
                if not os.path.exists(file_path):
                    # Try project root relative
                    root_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", file_path)
                    root_path = os.path.abspath(root_path)
                    if os.path.exists(root_path):
                        file_path = root_path
                if not os.path.exists(file_path):
                    return jsonify({"status": "error", "message": f"File not found: {file_path}"}), 400
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                recipes = data.get("recipes", data if isinstance(data, list) else [])

            if not isinstance(recipes, list) or len(recipes) == 0:
                return jsonify({"status": "error", "message": "No recipes provided"}), 400

            # Optional clear first
            if str(payload.get("clear_first", "false")).lower() == "true":
                try:
                    recipe_cache.recipe_collection.delete(where={})
                except Exception as e:
                    print(f"Could not clear existing recipes: {e}")

            # Ingest in batches into ChromaDB
            batch_size = int(payload.get("batch_size", 100))
            total = 0
            for i in range(0, len(recipes), batch_size):
                batch = recipes[i:i+batch_size]
                documents, metadatas, ids = [], [], []
                for r in batch:
                    rid = str(r.get("id") or r.get("_id") or f"import_{i}_{len(ids)}")
                    title = r.get("title", "")
                    doc = {
                        "id": rid,
                        "title": title,
                        "description": r.get("description", ""),
                        "ingredients": r.get("ingredients", []),
                        "instructions": r.get("instructions", []),
                        "cuisines": r.get("cuisines", [r.get("cuisine")] if r.get("cuisine") else []),
                        "diets": r.get("diets", []),
                        "image": r.get("image", ""),
                        "readyInMinutes": r.get("readyInMinutes", r.get("ready_in_minutes", 30)),
                        "servings": r.get("servings", 2),
                        "calories": r.get("calories", 0),
                        "protein": r.get("protein", 0),
                        "carbs": r.get("carbs", 0),
                        "fat": r.get("fat", 0),
                        "source": r.get("source", "import")
                    }
                    documents.append(json.dumps(doc))
                    metadatas.append({
                        "id": rid,
                        "title": title,
                        "cuisines": doc.get("cuisines", []),
                        "diets": doc.get("diets", []),
                        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    })
                    ids.append(rid)

                if ids:
                    recipe_cache.recipe_collection.add(documents=documents, metadatas=metadatas, ids=ids)
                    total += len(ids)

            # Return new count
            try:
                count = recipe_cache.recipe_collection.count()
            except Exception:
                count = total

            return jsonify({
                "status": "success",
                "imported": total,
                "total_in_db": count
            }), 200

        except Exception as e:
            print(f"Admin import error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500


    return app
