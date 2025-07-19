import requests
import time
import json
from backend.services.recipe_cache_service import RecipeCacheService

# Initialize ChromaDB service
recipe_cache = RecipeCacheService()

# TheMealDB API endpoints
MEALDB_LIST_URL = "https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
MEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}"

# Cuisines to fetch
CUISINES = [
    "Italian", "Chinese", "Mexican", "Indian", "French", 
    "Thai", "Japanese", "American", "Spanish", "Moroccan", 
    "Greek", "Turkish"
]

def normalize_recipe(recipe):
    """Normalize recipe data for storage"""
    normalized = {
        'id': recipe['idMeal'],
        'title': recipe['strMeal'],
        'cuisine': recipe.get('cuisine', 'International'),
        'image': recipe['strMealThumb'],
        'instructions': recipe['strInstructions'],
        'ingredients': [],
        'cuisines': [recipe.get('cuisine', 'International')],
        'diets': [],
        'readyInMinutes': 30  # Default value
    }
    
    # Extract ingredients
    for i in range(1, 21):
        ingredient = recipe.get(f'strIngredient{i}')
        measure = recipe.get(f'strMeasure{i}')
        if ingredient and ingredient.strip():
            normalized['ingredients'].append({
                'name': ingredient.strip(),
                'amount': measure.strip() if measure else ''
            })
    
    # Infer dietary restrictions
    ingredients_lower = [ing['name'].lower() for ing in normalized['ingredients']]
    if not any(meat in ' '.join(ingredients_lower) for meat in ['chicken', 'beef', 'pork', 'fish', 'meat']):
        normalized['diets'].append('vegetarian')
    
    return normalized

def fetch_and_store_recipes():
    """Fetch recipes from TheMealDB and store in ChromaDB"""
    all_recipes = []
    
    # Fetch recipes for each cuisine
    for cuisine in CUISINES:
        print(f"Fetching recipes for {cuisine} cuisine...")
        
        # Get list of meals for cuisine
        resp = requests.get(MEALDB_LIST_URL.format(area=cuisine))
        if not resp.ok or 'meals' not in resp.json() or not resp.json()['meals']:
            print(f"No recipes found for {cuisine}")
            continue
            
        # Get details for each meal
        meals = resp.json()['meals']
        print(f"Found {len(meals)} recipes for {cuisine}")
        
        for meal in meals:
            try:
                # Get detailed recipe info
                detail_resp = requests.get(MEALDB_LOOKUP_URL.format(id=meal['idMeal']))
                if detail_resp.ok and detail_resp.json()['meals']:
                    recipe_data = detail_resp.json()['meals'][0]
                    recipe_data['cuisine'] = cuisine
                    normalized_recipe = normalize_recipe(recipe_data)
                    all_recipes.append(normalized_recipe)
                    print(f"Added recipe: {normalized_recipe['title']}")
                time.sleep(0.2)  # Rate limiting
            except Exception as e:
                print(f"Error processing recipe {meal['idMeal']}: {e}")
    
    # Store all recipes in ChromaDB
    if all_recipes:
        print(f"\nStoring {len(all_recipes)} recipes in ChromaDB...")
        recipe_cache.cache_recipes(all_recipes, query="all", ingredient="")
        print("Successfully stored recipes in ChromaDB!")
    else:
        print("No recipes to store!")

if __name__ == "__main__":
    fetch_and_store_recipes() 