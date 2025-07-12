import requests
import os
from typing import List, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId # Import ObjectId

# Assuming these are defined as environment variables for security
SPOONACULAR_API_KEY = os.environ.get("SPOONACULAR_API_KEY", "YOUR_SPOONACULAR_API_KEY")
SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"
SPOONACULAR_GET_BY_BY_ID_URL = "https://api.spoonacular.com/recipes/{id}/information"

# Placeholder for a hypothetical external web search API (no longer used for agentic search, Spoonacular preferred)
EXTERNAL_WEB_SEARCH_API_URL = os.environ.get("EXTERNAL_WEB_SEARCH_API_URL", "https://api.example.com/websearch") # Replace with actual API
EXTERNAL_WEB_SEARCH_API_KEY = os.environ.get("EXTERNAL_WEB_SEARCH_API_KEY", "YOUR_WEB_SEARCH_API_KEY")

class RecipeService:
    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.recipes_collection = None
        self.mongo_available = False
        # Attempt MongoDB connection, but it's now optional for recipes
        self._connect_to_mongodb()
        self._in_memory_recipes = self._load_hardcoded_recipes()

    def _connect_to_mongodb(self):
        # This method remains for future MongoDB use, but recipes are now primarily in-memory
        try:
            mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1000) # Shorter timeout
            self.mongo_client.admin.command('ping') 
            self.db = self.mongo_client["recipe_app"]
            self.recipes_collection = self.db["recipes"]
            self.mongo_available = True
            print("Successfully connected to MongoDB (optional for recipes).")
        except ConnectionFailure as e:
            print(f"MongoDB connection failed: {e}. Using in-memory recipes and Spoonacular fallback.")
            self.mongo_available = False
        except Exception as e:
            print(f"An unexpected error occurred during MongoDB connection: {e}")
            self.mongo_available = False

    def _load_hardcoded_recipes(self) -> List[Dict[str, Any]]:
        # A large collection of hardcoded recipes for the agent to use
        return [
            # Breakfast Recipes
            {
                "id": "b1", "name": "Fluffy Blueberry Pancakes", "cuisine": "American",
                "dietaryRestrictions": ["vegetarian"], "ingredients": ["flour", "milk", "eggs", "blueberries"], 
                "instructions": "Mix ingredients, cook on griddle.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "breakfast"
            },
            {
                "id": "b2", "name": "Spinach and Feta Omelette", "cuisine": "Mediterranean",
                "dietaryRestrictions": ["vegetarian"], "ingredients": ["eggs", "spinach", "feta"], 
                "instructions": "Whisk eggs, cook with spinach and feta.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "breakfast"
            },
            {
                "id": "b3", "name": "Overnight Oats with Berries", "cuisine": "Healthy",
                "dietaryRestrictions": ["vegetarian", "vegan", "gluten-free"], "ingredients": ["oats", "almond milk", "chia seeds", "berries"], 
                "instructions": "Combine, refrigerate overnight.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "breakfast"
            },
            {
                "id": "b4", "name": "Keto Breakfast Bowl", "cuisine": "American",
                "dietaryRestrictions": ["keto", "gluten-free"], "ingredients": ["eggs", "avocado", "bacon"], 
                "instructions": "Cook eggs, slice avocado, crisp bacon.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "breakfast"
            },
            {
                "id": "b5", "name": "Mexican Breakfast Burrito", "cuisine": "Mexican",
                "dietaryRestrictions": [], "ingredients": ["tortilla", "eggs", "beans", "salsa"], 
                "instructions": "Scramble eggs, fill tortilla with ingredients.", "image": "/placeholder.svg", 
                "difficulty": "medium", "mealType": "breakfast"
            },

            # Lunch Recipes
            {
                "id": "l1", "name": "Classic Caesar Salad with Chicken", "cuisine": "American",
                "dietaryRestrictions": [], "ingredients": ["romaine", "chicken breast", "croutons", "parmesan"], 
                "instructions": "Grill chicken, toss with salad.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "lunch"
            },
            {
                "id": "l2", "name": "Mediterranean Quinoa Salad", "cuisine": "Mediterranean",
                "dietaryRestrictions": ["vegetarian", "vegan", "gluten-free"], "ingredients": ["quinoa", "cucumber", "tomato", "olives"], 
                "instructions": "Cook quinoa, mix with chopped veggies.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "lunch"
            },
            {
                "id": "l3", "name": "Quick Lentil Soup", "cuisine": "Mediterranean",
                "dietaryRestrictions": ["vegetarian", "vegan"], "ingredients": ["lentils", "carrots", "celery", "broth"], 
                "instructions": "Simmer lentils with vegetables.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "lunch"
            },
            {
                "id": "l4", "name": "Spicy Tuna Wrap", "cuisine": "American",
                "dietaryRestrictions": [], "ingredients": ["tuna", "mayo", "sriracha", "lettuce", "wrap"], 
                "instructions": "Mix tuna, spread on wrap, add lettuce.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "lunch"
            },
            {
                "id": "l5", "name": "Vegetable Spring Rolls", "cuisine": "Asian",
                "dietaryRestrictions": ["vegetarian", "vegan"], "ingredients": ["rice paper", "cabbage", "carrots", "peanuts"], 
                "instructions": "Roll veggies in rice paper, serve with sauce.", "image": "/placeholder.svg", 
                "difficulty": "medium", "mealType": "lunch"
            },

            # Dinner Recipes
            {
                "id": "d1", "name": "Chicken and Broccoli Stir-fry", "cuisine": "Asian",
                "dietaryRestrictions": [], "ingredients": ["chicken breast", "broccoli", "soy sauce", "rice"], 
                "instructions": "Stir-fry chicken and broccoli, serve with rice.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "dinner"
            },
            {
                "id": "d2", "name": "Classic Spaghetti Bolognese", "cuisine": "Italian",
                "dietaryRestrictions": [], "ingredients": ["ground beef", "pasta", "tomato sauce", "onion"], 
                "instructions": "Brown meat, simmer sauce, serve with pasta.", "image": "/placeholder.svg", 
                "difficulty": "medium", "mealType": "dinner"
            },
            {
                "id": "d3", "name": "Vegetarian Chili", "cuisine": "American",
                "dietaryRestrictions": ["vegetarian", "vegan"], "ingredients": ["beans", "tomatoes", "peppers", "chili powder"], 
                "instructions": "Combine ingredients, simmer until thick.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "dinner"
            },
            {
                "id": "d4", "name": "Sheet Pan Lemon Herb Salmon", "cuisine": "Mediterranean",
                "dietaryRestrictions": ["gluten-free"], "ingredients": ["salmon fillet", "lemon", "herbs", "asparagus"], 
                "instructions": "Bake salmon and asparagus on a sheet pan.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "dinner"
            },
            {
                "id": "d5", "name": "Tofu and Vegetable Curry", "cuisine": "Indian",
                "dietaryRestrictions": ["vegetarian", "vegan", "gluten-free"], "ingredients": ["tofu", "curry paste", "coconut milk", "mixed vegetables"], 
                "instructions": "Cook tofu and veggies in curry sauce.", "image": "/placeholder.svg", 
                "difficulty": "medium", "mealType": "dinner"
            },
            {
                "id": "d6", "name": "Chicken Fajita Bowls", "cuisine": "Mexican",
                "dietaryRestrictions": ["gluten-free"], "ingredients": ["chicken breast", "peppers", "onions", "rice"], 
                "instructions": "Cook chicken and veggies, serve over rice.", "image": "/placeholder.svg", 
                "difficulty": "medium", "mealType": "dinner"
            },
            {
                "id": "d7", "name": "Mushroom Risotto", "cuisine": "Italian",
                "dietaryRestrictions": ["vegetarian"], "ingredients": ["arborio rice", "mushrooms", "broth", "parmesan"], 
                "instructions": "Slowly cook rice with broth and mushrooms.", "image": "/placeholder.svg", 
                "difficulty": "hard", "mealType": "dinner"
            },
            {
                "id": "d8", "name": "Simple Baked Cod with Veggies", "cuisine": "Mediterranean",
                "dietaryRestrictions": ["gluten-free", "keto"], "ingredients": ["cod fillet", "zucchini", "cherry tomatoes"], 
                "instructions": "Bake cod with vegetables until flaky.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "dinner"
            },
            {
                "id": "d9", "name": "Beef and Vegetable Skewers", "cuisine": "American",
                "dietaryRestrictions": ["gluten-free", "carnivore"], "ingredients": ["beef cubes", "bell peppers", "onions"], 
                "instructions": "Thread meat and veggies on skewers, grill.", "image": "/placeholder.svg", 
                "difficulty": "medium", "mealType": "dinner"
            },
            {
                "id": "d10", "name": "Vegan Black Bean Burgers", "cuisine": "American",
                "dietaryRestrictions": ["vegan", "vegetarian"], "ingredients": ["black beans", "oats", "spices"], 
                "instructions": "Form patties, cook, serve on buns.", "image": "/placeholder.svg", 
                "difficulty": "medium", "mealType": "dinner"
            },

            # Any/Snack Recipes (examples for other meal types)
            {
                "id": "s1", "name": "Fruit Smoothie", "cuisine": "Healthy",
                "dietaryRestrictions": ["vegan", "vegetarian", "gluten-free"], "ingredients": ["banana", "berries", "spinach", "almond milk"], 
                "instructions": "Blend all ingredients until smooth.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "any"
            },
            {
                "id": "s2", "name": "Hard-Boiled Eggs", "cuisine": "American",
                "dietaryRestrictions": ["keto", "carnivore"], "ingredients": ["eggs"], 
                "instructions": "Boil eggs for 8-10 minutes.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "snack"
            },
            {
                "id": "s3", "name": "Avocado Toast", "cuisine": "Cafe",
                "dietaryRestrictions": ["vegetarian"], "ingredients": ["bread", "avocado", "salt", "pepper"], 
                "instructions": "Toast bread, mash avocado, spread on toast.", "image": "/placeholder.svg", 
                "difficulty": "easy", "mealType": "any"
            },
        ]

    def get_all_recipes(self) -> List[Dict[str, Any]]:
        recipes = []
        # Start with in-memory recipes
        recipes.extend(self._in_memory_recipes)

        if self.mongo_available and self.recipes_collection:
            # Fetch from MongoDB if available and add them
            try:
                mongo_recipes = list(self.recipes_collection.find({}))
                recipes.extend([
                    {
                        "id": str(r.get("_id", r.get("id"))),
                        "name": r.get("title", r.get("name", "Untitled")),
                        "cuisine": r.get("cuisine", r.get("cuisines", ["Unknown"])[0] if r.get("cuisines") else "Unknown"),
                        "dietaryRestrictions": r.get("dietaryRestrictions", r.get("diets", [])),
                        "ingredients": r.get("extendedIngredients", r.get("ingredients", [])),
                        "instructions": r.get("instructions", "No instructions provided."),
                        "image": r.get("image", "/placeholder.svg"),
                        "difficulty": r.get("difficulty", "beginner"),
                        "mealType": r.get("mealType", "any") # Assume 'any' if not specified in DB
                    } for r in mongo_recipes
                ])
                print(f"Fetched {len(mongo_recipes)} recipes from MongoDB.")
            except Exception as e:
                print(f"Error fetching from MongoDB: {e}")

        # Complement with Spoonacular search if current pool is small
        if len(recipes) < 50: # Example threshold to fetch more recipes
            try:
                print("Fetching additional recipes from Spoonacular API...")
                params = {
                    "apiKey": SPOONACULAR_API_KEY,
                    "number": 50, # Fetch a reasonable number
                    "addRecipeInformation": True # Get full details
                }
                response = requests.get(SPOONACULAR_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if "results" in data:
                    spoonacular_recipes = []
                    for r in data["results"]:
                        spoonacular_recipes.append(self._normalize_spoonacular_recipe(r))
                    recipes.extend(spoonacular_recipes)
                    print(f"Added {len(spoonacular_recipes)} recipes from Spoonacular to the pool.")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching from Spoonacular API: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during Spoonacular fetch: {e}")

        return recipes

    def _normalize_spoonacular_recipe(self, spoonacular_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes Spoonacular recipe data to the internal Recipe format."""
        normalized_diets = []
        for diet in spoonacular_data.get("diets", []):
            diet_lower = diet.lower()
            if "vegetarian" in diet_lower:
                normalized_diets.append("vegetarian")
            if "vegan" in diet_lower:
                normalized_diets.append("vegan")
            if "gluten" in diet_lower and "free" in diet_lower:
                normalized_diets.append("gluten-free")
            if "carnivore" in diet_lower or "meat" in diet_lower or "paleo" in diet_lower: 
                normalized_diets.append("carnivore")
            if "ketogenic" in diet_lower:
                normalized_diets.append("keto")

        # Infer mealType from Spoonacular dishTypes or title, defaulting to 'any'
        meal_type = "any"
        dish_types = [dt.lower() for dt in spoonacular_data.get("dishTypes", [])]
        if "breakfast" in dish_types:
            meal_type = "breakfast"
        elif "lunch" in dish_types:
            meal_type = "lunch"
        elif "dinner" in dish_types or "main course" in dish_types:
            meal_type = "dinner"
        elif "dessert" in dish_types:
            meal_type = "dessert"
        elif "snack" in dish_types:
            meal_type = "snack"
        
        # Fallback to title if dishTypes is not helpful
        if meal_type == "any" and spoonacular_data.get("title"):
            title_lower = spoonacular_data["title"].lower()
            if "breakfast" in title_lower: meal_type = "breakfast"
            elif "lunch" in title_lower: meal_type = "lunch"
            elif "dinner" in title_lower: meal_type = "dinner"
            elif "dessert" in title_lower: meal_type = "dessert"
            elif "snack" in title_lower: meal_type = "snack"


        return {
            "id": str(spoonacular_data.get("id")), 
            "name": spoonacular_data.get("title", "Untitled Recipe"),
            "cuisine": spoonacular_data.get("cuisine", spoonacular_data.get("cuisines", ["Unknown"])[0] if spoonacular_data.get("cuisines") else "Unknown"),
            "dietaryRestrictions": list(set(normalized_diets)), 
            "ingredients": [ing.get("original", "") for ing in spoonacular_data.get("extendedIngredients", []) if ing.get("original")],
            "instructions": spoonacular_data.get("instructions", "No instructions provided.") or "No instructions provided.", 
            "image": spoonacular_data.get("image", "/placeholder.svg"),
            "difficulty": "medium", 
            "mealType": meal_type,
            "ratings": [], 
            "comments": [] 
        }

    def search_online_recipe_ideas(self, query: str, number: int = 10) -> List[Dict[str, Any]]:
        """
        Searches for online recipe ideas using Spoonacular API and returns full recipe data.
        """
        print(f"Searching Spoonacular for online recipe ideas with query: '{query}'")
        try:
            # Step 1: Perform a complex search to get recipe IDs and basic info
            search_params = {
                "apiKey": SPOONACULAR_API_KEY,
                "query": query,
                "number": number,
                "addRecipeInformation": False, 
                "fillIngredients": False,
            }
            search_response = requests.get(SPOONACULAR_URL, params=search_params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()

            if "results" not in search_data or not search_data["results"]:
                print(f"No initial search results from Spoonacular for query: '{query}'")
                return []

            recipe_ids = [r["id"] for r in search_data["results"]]
            
            # Step 2: Fetch full information for each recipe ID
            full_recipes: List[Dict[str, Any]] = []
            for recipe_id in recipe_ids:
                info_url = SPOONACULAR_GET_BY_BY_ID_URL.format(id=recipe_id)
                info_params = {
                    "apiKey": SPOONACULAR_API_KEY,
                    "includeNutrition": False, 
                }
                info_response = requests.get(info_url, params=info_params, timeout=10)
                info_response.raise_for_status()
                recipe_data = info_response.json()
                
                # Normalize and add to list
                full_recipes.append(self._normalize_spoonacular_recipe(recipe_data))
            
            print(f"Successfully fetched and normalized {len(full_recipes)} online recipes from Spoonacular.")
            return full_recipes

        except requests.exceptions.RequestException as e:
            print(f"Error during Spoonacular API request for online ideas: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during Spoonacular online ideas search: {e}")
            return []