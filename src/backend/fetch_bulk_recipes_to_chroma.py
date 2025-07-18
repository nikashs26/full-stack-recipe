import requests
import time
import json
import os
from services.recipe_cache_service import RecipeCacheService

CUISINES = [
    "Italian", "Chinese", "Mexican", "Indian", "French", "Thai", "Japanese", "American", "Spanish", "Moroccan", "Greek", "Turkish"
]
RECIPES_PER_CUISINE = 50  # TheMealDB has fewer per area, so use 50 max
HARDCODED_PATH = os.path.join(os.path.dirname(__file__), "hardcoded_recipes.json")

recipe_cache = RecipeCacheService()

MEALDB_LIST_URL = "https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
MEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}"

def normalize_recipe(recipe):
    # Ensure required tags exist and are the correct type
    if "cuisine" not in recipe or not recipe["cuisine"]:
        recipe["cuisine"] = "Misc"
    if "dietaryRestrictions" not in recipe or not isinstance(recipe["dietaryRestrictions"], list):
        recipe["dietaryRestrictions"] = []
    return recipe

def fetch_and_store_recipes():
    all_recipes = []
    # 1. Load hardcoded recipes
    if os.path.exists(HARDCODED_PATH):
        with open(HARDCODED_PATH, "r") as f:
            hardcoded = json.load(f)
            print(f"Loaded {len(hardcoded)} hardcoded recipes.")
            for recipe in hardcoded:
                all_recipes.append(normalize_recipe(recipe))
    else:
        print("No hardcoded_recipes.json found.")

    # 2. Fetch from TheMealDB
    for cuisine in CUISINES:
        print(f"Fetching up to {RECIPES_PER_CUISINE} recipes for cuisine: {cuisine}")
        resp = requests.get(MEALDB_LIST_URL.format(area=cuisine))
        if not resp.ok or 'meals' not in resp.json() or not resp.json()['meals']:
            print(f"No recipes found for cuisine: {cuisine}")
            continue
        meal_ids = [meal['idMeal'] for meal in resp.json()['meals']][:RECIPES_PER_CUISINE]
        for meal_id in meal_ids:
            detail_resp = requests.get(MEALDB_LOOKUP_URL.format(id=meal_id))
            if detail_resp.ok and detail_resp.json().get('meals'):
                meal = detail_resp.json()['meals'][0]
                # Normalize and tag
                meal['cuisine'] = cuisine
                if 'dietaryRestrictions' not in meal:
                    meal['dietaryRestrictions'] = []
                all_recipes.append(normalize_recipe(meal))
            time.sleep(0.2)
        print(f"Fetched {len(meal_ids)} recipes for {cuisine}")

    print(f"Total recipes to cache: {len(all_recipes)}")
    # 3. Store ALL recipes in Chroma
    if all_recipes:
        recipe_cache.cache_recipes(all_recipes, query="all", ingredient="")
        print(f"Cached {len(all_recipes)} recipes in Chroma.")
    else:
        print("No recipes to cache!")

if __name__ == "__main__":
    fetch_and_store_recipes()
