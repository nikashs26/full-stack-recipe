import json
import requests
from flask import request, jsonify
import time
from bson import ObjectId
from datetime import datetime
from services.recipe_cache_service import RecipeCacheService

# Import the enhanced recipe database service at the top
from services.recipe_database_service import RecipeDatabaseService

# Initialize enhanced recipe database service
try:
    enhanced_recipe_service = RecipeDatabaseService()
    print("✅ Enhanced Recipe Database Service initialized with AI support")
except ImportError:
    enhanced_recipe_service = None
    print("⚠️ Enhanced Recipe Database Service not available - falling back to basic mode")

# Initialize recipe cache service
recipe_cache = RecipeCacheService()

# Large fallback recipe collection for when MongoDB is unavailable
FALLBACK_RECIPES = [
    # Italian Cuisine (Enhanced)
    {
        "id": 10001,
        "title": "Classic Spaghetti Carbonara",
        "image": "https://images.unsplash.com/photo-1551892589-865f69869476?w=400",
        "cuisines": ["Italian"],
        "diets": [],
        "readyInMinutes": 25,
        "servings": 4,
        "summary": "Authentic Italian carbonara with eggs, cheese, and pancetta",
        "instructions": "Cook pasta, mix with eggs and cheese, add pancetta",
        "tags": ["Italian"],
        "extendedIngredients": [
            {"name": "spaghetti", "amount": 400, "unit": "g"},
            {"name": "eggs", "amount": 4, "unit": "large"},
            {"name": "pancetta", "amount": 150, "unit": "g"},
            {"name": "parmesan cheese", "amount": 100, "unit": "g"}
        ]
    },
    {
        "id": 10041,
        "title": "Penne Arrabbiata",
        "image": "https://images.unsplash.com/photo-1563379091339-03246963d719?w=400",
        "cuisines": ["Italian"],
        "diets": ["Vegetarian"],
        "readyInMinutes": 20,
        "servings": 4,
        "summary": "Spicy tomato pasta with garlic and red pepper flakes",
        "tags": ["Italian", "Vegetarian"],
        "extendedIngredients": [
            {"name": "penne pasta", "amount": 400, "unit": "g"},
            {"name": "tomatoes", "amount": 400, "unit": "g"},
            {"name": "garlic", "amount": 4, "unit": "cloves"},
            {"name": "red pepper flakes", "amount": 1, "unit": "tsp"}
        ]
    },
    {
        "id": 10042,
        "title": "Osso Buco Milanese",
        "image": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400",
        "cuisines": ["Italian"],
        "diets": [],
        "readyInMinutes": 180,
        "servings": 6,
        "summary": "Braised veal shanks with vegetables and saffron risotto",
        "tags": ["Italian"],
        "extendedIngredients": [
            {"name": "veal shanks", "amount": 1500, "unit": "g"},
            {"name": "white wine", "amount": 300, "unit": "ml"},
            {"name": "carrots", "amount": 200, "unit": "g"},
            {"name": "celery", "amount": 150, "unit": "g"}
        ]
    },

    # Mexican Cuisine (Enhanced)
    {
        "id": 10043,
        "title": "Carnitas Tacos",
        "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400",
        "cuisines": ["Mexican"],
        "diets": [],
        "readyInMinutes": 240,
        "servings": 8,
        "summary": "Slow-cooked pork shoulder with traditional Mexican spices",
        "tags": ["Mexican"],
        "extendedIngredients": [
            {"name": "pork shoulder", "amount": 2000, "unit": "g"},
            {"name": "cumin", "amount": 2, "unit": "tsp"},
            {"name": "oregano", "amount": 1, "unit": "tsp"},
            {"name": "corn tortillas", "amount": 16, "unit": "pieces"}
        ]
    },
    {
        "id": 10044,
        "title": "Mole Poblano",
        "image": "https://images.unsplash.com/photo-1599974579688-8dbdd335c77f?w=400",
        "cuisines": ["Mexican"],
        "diets": [],
        "readyInMinutes": 300,
        "servings": 8,
        "summary": "Complex sauce with chocolate and chilies served over chicken",
        "tags": ["Mexican"],
        "extendedIngredients": [
            {"name": "chicken", "amount": 1500, "unit": "g"},
            {"name": "dried chilies", "amount": 8, "unit": "pieces"},
            {"name": "dark chocolate", "amount": 50, "unit": "g"},
            {"name": "sesame seeds", "amount": 30, "unit": "g"}
        ]
    },

    # Indian Cuisine (Enhanced)
    {
        "id": 10045,
        "title": "Lamb Rogan Josh",
        "image": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=400",
        "cuisines": ["Indian"],
        "diets": [],
        "readyInMinutes": 120,
        "servings": 6,
        "summary": "Aromatic Kashmiri lamb curry with yogurt and spices",
        "tags": ["Indian"],
        "extendedIngredients": [
            {"name": "lamb shoulder", "amount": 1000, "unit": "g"},
            {"name": "yogurt", "amount": 200, "unit": "ml"},
            {"name": "kashmiri chili", "amount": 2, "unit": "tsp"},
            {"name": "fennel powder", "amount": 1, "unit": "tsp"}
        ]
    },
    {
        "id": 10046,
        "title": "Palak Paneer",
        "image": "https://images.unsplash.com/photo-1563379091339-03246963d719?w=400",
        "cuisines": ["Indian"],
        "diets": ["Vegetarian"],
        "readyInMinutes": 30,
        "servings": 4,
        "summary": "Creamy spinach curry with cottage cheese cubes",
        "tags": ["Indian", "Vegetarian"],
        "extendedIngredients": [
            {"name": "spinach", "amount": 500, "unit": "g"},
            {"name": "paneer", "amount": 300, "unit": "g"},
            {"name": "heavy cream", "amount": 100, "unit": "ml"},
            {"name": "garam masala", "amount": 1, "unit": "tsp"}
        ]
    },

    # Chinese Cuisine (Enhanced)
    {
        "id": 10047,
        "title": "Peking Duck",
        "image": "https://images.unsplash.com/photo-1562059390-a761a084768e?w=400",
        "cuisines": ["Chinese"],
        "diets": [],
        "readyInMinutes": 720,
        "servings": 6,
        "summary": "Traditional roasted duck with pancakes and hoisin sauce",
        "tags": ["Chinese"],
        "extendedIngredients": [
            {"name": "whole duck", "amount": 2500, "unit": "g"},
            {"name": "five spice", "amount": 2, "unit": "tsp"},
            {"name": "hoisin sauce", "amount": 100, "unit": "ml"},
            {"name": "pancakes", "amount": 12, "unit": "pieces"}
        ]
    },
    {
        "id": 10048,
        "title": "Dan Dan Noodles",
        "image": "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=400",
        "cuisines": ["Chinese"],
        "diets": [],
        "readyInMinutes": 20,
        "servings": 4,
        "summary": "Spicy Sichuan noodles with ground pork and peanuts",
        "tags": ["Chinese"],
        "extendedIngredients": [
            {"name": "wheat noodles", "amount": 400, "unit": "g"},
            {"name": "ground pork", "amount": 200, "unit": "g"},
            {"name": "sichuan peppercorns", "amount": 1, "unit": "tsp"},
            {"name": "peanuts", "amount": 50, "unit": "g"}
        ]
    },

    # Thai Cuisine (Enhanced)
    {
        "id": 10049,
        "title": "Massaman Curry",
        "image": "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=400",
        "cuisines": ["Thai"],
        "diets": [],
        "readyInMinutes": 45,
        "servings": 4,
        "summary": "Rich and mild Thai curry with beef and potatoes",
        "tags": ["Thai"],
        "extendedIngredients": [
            {"name": "beef chuck", "amount": 600, "unit": "g"},
            {"name": "massaman paste", "amount": 3, "unit": "tbsp"},
            {"name": "coconut milk", "amount": 400, "unit": "ml"},
            {"name": "potatoes", "amount": 300, "unit": "g"}
        ]
    },
    {
        "id": 10050,
        "title": "Som Tam (Papaya Salad)",
        "image": "https://images.unsplash.com/photo-1569562211093-4ed0d0758f12?w=400",
        "cuisines": ["Thai"],
        "diets": ["Vegan"],
        "readyInMinutes": 15,
        "servings": 4,
        "summary": "Fresh and spicy green papaya salad with lime dressing",
        "tags": ["Thai", "Vegan"],
        "extendedIngredients": [
            {"name": "green papaya", "amount": 500, "unit": "g"},
            {"name": "thai chilies", "amount": 3, "unit": "pieces"},
            {"name": "fish sauce", "amount": 2, "unit": "tbsp"},
            {"name": "lime juice", "amount": 3, "unit": "tbsp"}
        ]
    },

    # Japanese Cuisine (Enhanced)
    {
        "id": 10051,
        "title": "Ramen with Chashu",
        "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400",
        "cuisines": ["Japanese"],
        "diets": [],
        "readyInMinutes": 60,
        "servings": 4,
        "summary": "Rich pork bone broth with tender pork belly and noodles",
        "tags": ["Japanese"],
        "extendedIngredients": [
            {"name": "ramen noodles", "amount": 400, "unit": "g"},
            {"name": "pork belly", "amount": 500, "unit": "g"},
            {"name": "miso paste", "amount": 3, "unit": "tbsp"},
            {"name": "soft boiled eggs", "amount": 4, "unit": "pieces"}
        ]
    },
    {
        "id": 10052,
        "title": "Katsu Curry",
        "image": "https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?w=400",
        "cuisines": ["Japanese"],
        "diets": [],
        "readyInMinutes": 45,
        "servings": 4,
        "summary": "Breaded pork cutlet with Japanese curry sauce",
        "tags": ["Japanese"],
        "extendedIngredients": [
            {"name": "pork loin", "amount": 600, "unit": "g"},
            {"name": "curry roux", "amount": 100, "unit": "g"},
            {"name": "panko breadcrumbs", "amount": 150, "unit": "g"},
            {"name": "Japanese rice", "amount": 300, "unit": "g"}
        ]
    },

    # Korean Cuisine (Enhanced)
    {
        "id": 10053,
        "title": "Korean BBQ Galbi",
        "image": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400",
        "cuisines": ["Korean"],
        "diets": [],
        "readyInMinutes": 30,
        "servings": 4,
        "summary": "Marinated short ribs grilled to perfection",
        "tags": ["Korean"],
        "extendedIngredients": [
            {"name": "beef short ribs", "amount": 1200, "unit": "g"},
            {"name": "soy sauce", "amount": 100, "unit": "ml"},
            {"name": "pear", "amount": 1, "unit": "large"},
            {"name": "sesame oil", "amount": 2, "unit": "tbsp"}
        ]
    },
    {
        "id": 10054,
        "title": "Kimchi Jjigae",
        "image": "https://images.unsplash.com/photo-1553056061-7b7b07b44d8a?w=400",
        "cuisines": ["Korean"],
        "diets": [],
        "readyInMinutes": 25,
        "servings": 4,
        "summary": "Spicy kimchi stew with pork and tofu",
        "tags": ["Korean"],
        "extendedIngredients": [
            {"name": "aged kimchi", "amount": 300, "unit": "g"},
            {"name": "pork belly", "amount": 200, "unit": "g"},
            {"name": "soft tofu", "amount": 200, "unit": "g"},
            {"name": "gochugaru", "amount": 1, "unit": "tbsp"}
        ]
    },

    # Spanish Cuisine (Enhanced)
    {
        "id": 10055,
        "title": "Seafood Paella",
        "image": "https://images.unsplash.com/photo-1534080564583-6be75777b70a?w=400",
        "cuisines": ["Spanish"],
        "diets": [],
        "readyInMinutes": 45,
        "servings": 8,
        "summary": "Traditional Spanish rice with seafood and saffron",
        "tags": ["Spanish"],
        "extendedIngredients": [
            {"name": "bomba rice", "amount": 400, "unit": "g"},
            {"name": "mixed seafood", "amount": 800, "unit": "g"},
            {"name": "saffron", "amount": 1, "unit": "pinch"},
            {"name": "fish stock", "amount": 1000, "unit": "ml"}
        ]
    },
    {
        "id": 10056,
        "title": "Patatas Bravas",
        "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
        "cuisines": ["Spanish"],
        "diets": ["Vegetarian"],
        "readyInMinutes": 30,
        "servings": 6,
        "summary": "Crispy potatoes with spicy tomato sauce and aioli",
        "tags": ["Spanish", "Vegetarian"],
        "extendedIngredients": [
            {"name": "potatoes", "amount": 800, "unit": "g"},
            {"name": "tomato sauce", "amount": 200, "unit": "ml"},
            {"name": "smoked paprika", "amount": 1, "unit": "tsp"},
            {"name": "garlic aioli", "amount": 100, "unit": "ml"}
        ]
    },

    # German Cuisine (Enhanced)
    {
        "id": 10057,
        "title": "Sauerbraten",
        "image": "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400",
        "cuisines": ["German"],
        "diets": [],
        "readyInMinutes": 300,
        "servings": 8,
        "summary": "Traditional pot roast marinated in vinegar and spices",
        "tags": ["German"],
        "extendedIngredients": [
            {"name": "beef roast", "amount": 2000, "unit": "g"},
            {"name": "red wine vinegar", "amount": 500, "unit": "ml"},
            {"name": "juniper berries", "amount": 8, "unit": "pieces"},
            {"name": "gingersnap cookies", "amount": 100, "unit": "g"}
        ]
    },
    {
        "id": 10058,
        "title": "Currywurst",
        "image": "https://images.unsplash.com/photo-1544943910-4c1d10e74134?w=400",
        "cuisines": ["German"],
        "diets": [],
        "readyInMinutes": 15,
        "servings": 4,
        "summary": "German street food with curry ketchup and bratwurst",
        "tags": ["German"],
        "extendedIngredients": [
            {"name": "bratwurst", "amount": 4, "unit": "pieces"},
            {"name": "ketchup", "amount": 150, "unit": "ml"},
            {"name": "curry powder", "amount": 2, "unit": "tsp"},
            {"name": "french fries", "amount": 400, "unit": "g"}
        ]
    },

    # Mediterranean Cuisine (Enhanced)  
    {
        "id": 10059,
        "title": "Lamb Souvlaki",
        "image": "https://images.unsplash.com/photo-1563379091339-03246963d719?w=400",
        "cuisines": ["Mediterranean", "Greek"],
        "diets": [],
        "readyInMinutes": 25,
        "servings": 4,
        "summary": "Grilled lamb skewers with herbs and lemon",
        "tags": ["Mediterranean", "Greek"],
        "extendedIngredients": [
            {"name": "lamb leg", "amount": 600, "unit": "g"},
            {"name": "oregano", "amount": 2, "unit": "tsp"},
            {"name": "lemon juice", "amount": 50, "unit": "ml"},
            {"name": "pita bread", "amount": 4, "unit": "pieces"}
        ]
    },
    {
        "id": 10060,
        "title": "Shakshuka",
        "image": "https://images.unsplash.com/photo-1571197119282-621c2694b15c?w=400",
        "cuisines": ["Mediterranean"],
        "diets": ["Vegetarian"],
        "readyInMinutes": 25,
        "servings": 4,
        "summary": "Eggs poached in spicy tomato sauce with peppers",
        "tags": ["Mediterranean", "Vegetarian"],
        "extendedIngredients": [
            {"name": "tomatoes", "amount": 800, "unit": "g"},
            {"name": "eggs", "amount": 6, "unit": "large"},
            {"name": "bell peppers", "amount": 2, "unit": "pieces"},
            {"name": "harissa", "amount": 1, "unit": "tbsp"}
        ]
    }
]

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def register_recipe_routes(app, recipes_collection, mongo_available, in_memory_recipes):
    SPOONACULAR_API_KEY = "01f12ed117584307b5cba262f43a8d49"
    SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"
    
    # Initialize enhanced recipe database service
    try:
        from services.recipe_database_service import RecipeDatabaseService
        enhanced_recipe_service = RecipeDatabaseService()
        print("✅ Enhanced Recipe Database Service initialized with AI support")
    except ImportError:
        enhanced_recipe_service = None
        print("⚠️ Enhanced Recipe Database Service not available - falling back to basic mode")
    
    # Initialize in-memory recipes with fallback data if empty and MongoDB not available
    if not mongo_available and len(in_memory_recipes) == 0:
        in_memory_recipes.extend(FALLBACK_RECIPES)
        print(f"Initialized in-memory storage with {len(FALLBACK_RECIPES)} fallback recipes")
    
    @app.route("/get_recipes", methods=["GET"])
    def get_recipes():
        start_time = time.time()
        query = request.args.get("query", "").strip()
        ingredient = request.args.get("ingredient", "").strip()
        cuisine = request.args.get("cuisine", "").strip()
        diet = request.args.get("diet", "").strip()
        
        # Get user preferences if available (for personalization)
        user_preferences = None
        try:
            from middleware.auth_middleware import get_current_user_id
            from services.user_preferences_service import UserPreferencesService
            
            user_id = get_current_user_id()
            if user_id:
                user_prefs_service = UserPreferencesService()
                user_preferences = user_prefs_service.get_preferences(user_id)
        except:
            pass  # No authentication or preferences available
        
        # Check ChromaDB cache first
        cached_recipes = recipe_cache.get_cached_recipes(query, ingredient)
        if cached_recipes:
            print(f"Returning {len(cached_recipes)} cached recipes for query: '{query}', ingredient: '{ingredient}'")
            return jsonify({"results": cached_recipes})
        
        # Use enhanced recipe service for MASSIVE recipe variety
        if enhanced_recipe_service:
            try:
                # Use the enhanced service to search across multiple APIs
                search_limit = 50 if query or ingredient or cuisine or diet else 24
                
                # Combine query and ingredient for better search
                combined_query = query
                if ingredient and not query:
                    combined_query = ingredient
                elif ingredient and query:
                    combined_query = f"{query} {ingredient}"
                
                results = enhanced_recipe_service.search_massive_recipe_database(
                    query=combined_query,
                    cuisine=cuisine,
                    diet=diet,
                    max_time=60,
                    difficulty="",
                    limit=search_limit,
                    user_preferences=user_preferences
                )
                
                if results and len(results) > 0:
                    print(f"✨ Enhanced service returned {len(results)} high-quality recipes from multiple sources")
                    # Cache the enhanced results
                    recipe_cache.cache_recipes(results, query, ingredient)
                    return jsonify({"results": results})
                else:
                    print("⚠️ Enhanced service returned no results, falling back to direct API calls")
            except Exception as e:
                print(f"⚠️ Enhanced recipe service failed: {e}, falling back to traditional methods")
        
        # Enhanced fallback: Try direct Spoonacular API call with better parameters
        print("Using direct Spoonacular API fallback")
        try:
            # Build search parameters for Spoonacular
            spoon_params = {
                "apiKey": SPOONACULAR_API_KEY,
                "number": 20,
                "addRecipeInformation": "true",
                "fillIngredients": "true",
                "instructionsRequired": "true",
                "sort": "popularity"
            }
            
            # Handle different search types
            if query and ingredient:
                spoon_params["query"] = f"{query} {ingredient}"
            elif query:
                spoon_params["query"] = query
            elif ingredient:
                spoon_params["includeIngredients"] = ingredient
                spoon_params["query"] = ingredient  # Also search in title/description
            
            if cuisine:
                spoon_params["cuisine"] = cuisine
            if diet:
                spoon_params["diet"] = diet
            
            print(f"Direct Spoonacular API call with params: {spoon_params}")
            response = requests.get(SPOONACULAR_URL, params=spoon_params, timeout=10)
            
            if response.ok:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    print(f"✅ Direct Spoonacular returned {len(results)} recipes")
                    
                    # Process and improve the results
                    for recipe in results:
                        # Ensure proper image URLs
                        if not recipe.get('image') or recipe.get('image') == '/placeholder.svg':
                            recipe['image'] = f"https://img.spoonacular.com/recipes/{recipe['id']}-636x393.jpg"
                        elif 'spoonacular.com' in recipe.get('image', '') and '556x370' in recipe.get('image', ''):
                            # Upgrade existing Spoonacular images to higher resolution
                            recipe['image'] = recipe['image'].replace('556x370', '636x393')
                        
                        # Ensure we have cuisines
                        if not recipe.get('cuisines'):
                            recipe['cuisines'] = ['American']
                        elif isinstance(recipe.get('cuisines'), str):
                            recipe['cuisines'] = [recipe['cuisines']]
                        
                        # Ensure we have diets
                        if not recipe.get('diets'):
                            recipe['diets'] = []
                    
                    # Cache and return results
                    recipe_cache.cache_recipes(results, query, ingredient)
                    print(f"Direct Spoonacular API request completed in {time.time() - start_time:.2f}s")
                    return jsonify({"results": results})
                else:
                    print("Direct Spoonacular returned no results")
            else:
                print(f"Direct Spoonacular API error: {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            print(f"Direct Spoonacular API failed: {e}")
        
        # Fallback to traditional methods if enhanced service fails
        # If no search parameters, try to get popular recipes
        if not query and not ingredient and not cuisine and not diet:
            # First try MongoDB if available
            if mongo_available:
                try:
                    popular_recipes = list(recipes_collection.find().limit(24))
                    if popular_recipes:
                        print(f"Found {len(popular_recipes)} popular recipes from MongoDB")
                        recipe_cache.cache_recipes(popular_recipes, query, ingredient)
                        return JSONEncoder().encode({"results": popular_recipes})
                except Exception as e:
                    print(f"Error fetching popular recipes from MongoDB: {e}")
            
            # Fallback to in-memory recipes
            if in_memory_recipes:
                popular_fallback = in_memory_recipes[:24]  # Return first 24 as popular
                print(f"Found {len(popular_fallback)} popular recipes from fallback")
                recipe_cache.cache_recipes(popular_fallback, query, ingredient)
                return jsonify({"results": popular_fallback})
            
            # Last resort: try Spoonacular API for popular recipes
            try:
                params = {
                    "apiKey": SPOONACULAR_API_KEY,
                    "number": 24,
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
                print(f"Error fetching popular recipes from API: {e}")
            
            # If all fails, return empty results
            return jsonify({"results": []}), 200

        # Search with parameters using traditional methods as fallback
        results = []
        
        # First check MongoDB if available
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
                db_results = list(recipes_collection.find(search_query).limit(20))
                print(f"MongoDB search returned {len(db_results)} results")
                
                if db_results:
                    print(f"Found {len(db_results)} recipes in database in {time.time() - start_time:.2f}s")
                    # Cache the MongoDB results
                    recipe_cache.cache_recipes(db_results, query, ingredient)
                    return JSONEncoder().encode({"results": db_results})
                else:
                    print("No results found in MongoDB, checking in-memory storage")
            except Exception as e:
                print(f"Error querying MongoDB: {e}")
        else:
            print("MongoDB not available, checking in-memory storage")
        
        # Search in-memory storage
        if in_memory_recipes:
            query_lower = query.lower() if query else ""
            ingredient_lower = ingredient.lower() if ingredient else ""
            
            for recipe in in_memory_recipes:
                title_match = not query or query_lower in recipe.get("title", "").lower()
                cuisine_match = not query or any(query_lower in cuisine.lower() for cuisine in recipe.get("cuisines", []))
                diet_match = not query or any(query_lower in diet.lower() for diet in recipe.get("diets", []))
                ingredient_match = not ingredient or any(
                    ingredient_lower in ing.get("name", "").lower() 
                    for ing in recipe.get("extendedIngredients", [])
                )
                
                if (title_match or cuisine_match or diet_match) and ingredient_match:
                    results.append(recipe)
                    
            if results:
                # Limit results and cache them
                results = results[:20]
                print(f"Found {len(results)} recipes in in-memory storage")
                recipe_cache.cache_recipes(results, query, ingredient)
                return jsonify({"results": results})
            else:
                print("No results found in in-memory storage")

        # If no local results, try Spoonacular API
        print("No results found locally, calling Spoonacular API")
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "number": 20,  # Limit to 20 results
            "addRecipeInformation": "true",
        }
        
        if query:
            params["query"] = query
        if ingredient:
            params["includeIngredients"] = ingredient
        if cuisine:
            params["cuisine"] = cuisine
        if diet:
            params["diet"] = diet

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

            # Enhanced validation and processing for recipe titles
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
                        if "dairy" in diet_lower and "free" in diet_lower:
                            normalized_diets.append("dairy-free")
                        if "ketogenic" in diet_lower or "keto" in diet_lower:
                            normalized_diets.append("keto")
                        if "paleo" in diet_lower or "paleolithic" in diet_lower:
                            normalized_diets.append("paleo")
                        if "carnivore" in diet_lower or "meat" in diet_lower:
                            normalized_diets.append("carnivore")
                        # Keep the original diet as well
                        normalized_diets.append(diet)
                    recipe["diets"] = normalized_diets
                
                # Ensure consistent and organized cuisine data
                if "cuisines" not in recipe or not recipe["cuisines"]:
                    # Try to infer cuisine from title or dish types
                    inferred_cuisine = None
                    recipe_title = recipe.get("title", "").lower()
                    
                    # Map common cuisine indicators in titles using standard cuisines
                    cuisine_indicators = {
                        "Italian": ["pasta", "pizza", "risotto", "italian", "parmesan", "mozzarella", "marinara", "pesto"],
                        "Mexican": ["taco", "burrito", "mexican", "salsa", "guacamole", "enchilada", "quesadilla", "chipotle"],
                        "Asian": ["stir fry", "teriyaki", "soy sauce", "ginger", "asian"],
                        "Chinese": ["kung pao", "sweet and sour", "chow mein", "chinese", "szechuan", "wonton"],
                        "Indian": ["curry", "tikka", "masala", "indian", "turmeric", "cumin", "tandoori", "biryani"],
                        "Thai": ["pad thai", "thai", "coconut milk", "lemongrass", "tom yum", "green curry"],
                        "Japanese": ["sushi", "miso", "teriyaki", "japanese", "ramen", "tempura", "katsu"],
                        "Mediterranean": ["olive oil", "feta", "mediterranean", "greek", "hummus", "tzatziki"],
                        "American": ["burger", "bbq", "american", "classic", "fries", "meatloaf", "pancake"],
                        "French": ["french", "coq au vin", "bouillabaisse", "ratatouille", "quiche", "cassoulet"],
                        "Korean": ["korean", "kimchi", "bulgogi", "bibimbap", "gochujang"],
                        "Spanish": ["spanish", "paella", "tapas", "gazpacho", "churros"],
                        "German": ["german", "sauerkraut", "bratwurst", "schnitzel", "pretzel"],
                        "Vietnamese": ["vietnamese", "pho", "banh mi", "spring roll"],
                        "Middle Eastern": ["middle eastern", "lebanese", "shawarma", "kebab", "tahini", "harissa"],
                        "British": ["british", "english", "fish and chips", "shepherd's pie"],
                        "Caribbean": ["caribbean", "jerk", "plantain", "coconut rice"]
                    }
                    
                    for cuisine, indicators in cuisine_indicators.items():
                        if any(indicator in recipe_title for indicator in indicators):
                            inferred_cuisine = cuisine
                            break
                    
                    # Set the inferred cuisine or conservative fallback
                    recipe["cuisines"] = [inferred_cuisine or "European"]
                    print(f"🌍 Set cuisine for '{recipe.get('title')}': {recipe['cuisines']}")
                
                # Normalize cuisine names for consistency using standard list
                standard_cuisines = [
                    'American', 'British', 'Chinese', 'French', 'German', 'Greek', 
                    'Indian', 'Italian', 'Japanese', 'Korean', 'Mexican', 'Spanish', 
                    'Thai', 'Vietnamese', 'Mediterranean', 'Middle Eastern', 'Caribbean',
                    'African', 'European', 'Asian'
                ]
                
                normalized_cuisines = []
                for cuisine in recipe.get("cuisines", []):
                    if cuisine:
                        # Standardize cuisine names
                        cuisine_lower = cuisine.lower().strip()
                        cuisine_mapping = {
                            "italian": "Italian", "italy": "Italian",
                            "mexican": "Mexican", "mexico": "Mexican",
                            "chinese": "Chinese", "china": "Chinese",
                            "indian": "Indian", "india": "Indian",
                            "thai": "Thai", "thailand": "Thai",
                            "japanese": "Japanese", "japan": "Japanese",
                            "american": "American", "usa": "American", "united states": "American",
                            "french": "French", "france": "French",
                            "mediterranean": "Mediterranean", "greek": "Greek", "greece": "Greek",
                            "asian": "Asian",
                            "korean": "Korean", "korea": "Korean",
                            "spanish": "Spanish", "spain": "Spanish",
                            "german": "German", "germany": "German",
                            "vietnamese": "Vietnamese", "vietnam": "Vietnamese",
                            "middle eastern": "Middle Eastern", "lebanese": "Middle Eastern", "moroccan": "Middle Eastern",
                            "british": "British", "english": "British", "uk": "British",
                            "caribbean": "Caribbean", "jamaican": "Caribbean",
                            "african": "African",
                            "european": "European"
                        }
                        
                        if cuisine_lower in cuisine_mapping:
                            normalized_cuisines.append(cuisine_mapping[cuisine_lower])
                        else:
                            # Try to find partial matches
                            found_match = False
                            for key, value in cuisine_mapping.items():
                                if key in cuisine_lower or cuisine_lower in key:
                                    normalized_cuisines.append(value)
                                    found_match = True
                                    break
                            
                            if not found_match:
                                # Capitalize and check if it's in our standard list
                                cuisine_title = cuisine.title()
                                if cuisine_title in standard_cuisines:
                                    normalized_cuisines.append(cuisine_title)
                                else:
                                    # Fallback to European for unknown cuisines
                                    normalized_cuisines.append("European")
                
                if normalized_cuisines:
                    recipe["cuisines"] = list(set(normalized_cuisines))  # Remove duplicates
                else:
                    recipe["cuisines"] = ["European"]

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
        try:
            # First try MongoDB if available
            if mongo_available:
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
                except Exception as e:
                    print(f"MongoDB query failed: {e}")
            
            # If MongoDB not available or recipe not found, check fallback recipes
            try:
                recipe_id_int = int(recipe_id)
                for recipe in FALLBACK_RECIPES:
                    if recipe["id"] == recipe_id_int:
                        print(f"Found recipe {recipe_id} in fallback collection")
                        return jsonify(recipe)
            except ValueError:
                pass
            
            # If not in fallback, try Spoonacular API
            try:
                api_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
                response = requests.get(api_url, params={
                    'apiKey': SPOONACULAR_API_KEY
                }, timeout=10)
                
                if response.status_code == 200:
                    recipe_data = response.json()
                    print(f"Found recipe {recipe_id} via Spoonacular API")
                    return jsonify(recipe_data)
                elif response.status_code == 402:
                    print(f"Spoonacular API quota exceeded for recipe {recipe_id}")
                else:
                    print(f"Spoonacular API error for recipe {recipe_id}: {response.status_code}")
            except Exception as e:
                print(f"Error calling Spoonacular API for recipe {recipe_id}: {e}")
            
            return jsonify({"error": "Recipe not found"}), 404
            
        except Exception as e:
            print(f"Error in get_recipe_from_db: {e}")
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

    @app.route("/load-1200-recipes", methods=["POST"])
    def load_1200_recipes():
        """DISABLED - Load recipes on-demand through search for better quality"""
        return jsonify({
            "success": True,
            "message": "Bulk loading disabled - recipes are loaded on-demand through search for better quality",
            "action": "disabled"
        })

    @app.route("/bulk-load-recipes", methods=["POST"])
    def bulk_load_recipes():
        """DISABLED - Load recipes on-demand through search for better quality"""
        return jsonify({
            "success": True,
            "message": "Bulk loading disabled - recipes are loaded on-demand through search for better quality",
            "action": "disabled"
        })

    @app.route("/recipe-stats", methods=["GET"])
    def get_recipe_stats():
        """Get statistics about available recipes"""
        try:
            stats = {
                "mongo_available": mongo_available,
                "in_memory_count": len(in_memory_recipes),
                "enhanced_service_available": enhanced_recipe_service is not None
            }
            
            # Get MongoDB count
            if mongo_available:
                try:
                    mongo_count = recipes_collection.count_documents({})
                    stats["mongo_count"] = mongo_count
                except:
                    stats["mongo_count"] = 0
            else:
                stats["mongo_count"] = 0
            
            # Get enhanced service stats
            if enhanced_recipe_service:
                try:
                    enhanced_stats = enhanced_recipe_service.get_recipe_stats()
                    stats["enhanced_service"] = enhanced_stats
                except:
                    stats["enhanced_service"] = {"error": "Failed to get enhanced stats"}
            
            stats["total_available"] = stats["mongo_count"] + stats["in_memory_count"]
            
            return jsonify(stats)
            
        except Exception as e:
            return jsonify({"error": f"Failed to get stats: {str(e)}"}), 500

    @app.route("/recipe-distribution", methods=["GET"])
    def get_recipe_distribution():
        """Get current distribution of recipes by cuisine"""
        try:
            if not mongo_available:
                return jsonify({"error": "MongoDB not available"}), 503
            
            # Aggregate recipes by cuisine
            pipeline = [
                {"$unwind": "$cuisines"},
                {"$group": {
                    "_id": "$cuisines",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            
            distribution = list(recipes_collection.aggregate(pipeline))
            total_recipes = recipes_collection.count_documents({})
            
            return jsonify({
                "total_recipes": total_recipes,
                "distribution": distribution,
                "target": 1200
            })
            
        except Exception as e:
            return jsonify({"error": f"Failed to get distribution: {str(e)}"}), 500
