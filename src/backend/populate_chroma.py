import requests
import time
import json
from services.recipe_cache_service import RecipeCacheService

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
                    
                    # Store recipe directly in ChromaDB
                    recipe_id = str(normalized_recipe['id'])
                    metadata = {
                        "id": recipe_id,
                        "title": normalized_recipe['title'],
                        "cuisine": normalized_recipe['cuisine'],
                        "cached_at": str(int(time.time()))
                    }
                    
                    # Create search text
                    search_terms = [
                        normalized_recipe['title'],
                        normalized_recipe['cuisine'],
                        *[ing['name'] for ing in normalized_recipe['ingredients']],
                        *normalized_recipe['diets']
                    ]
                    search_text = ' '.join(filter(None, search_terms))
                    
                    # Store in both collections
                    recipe_cache.recipe_collection.upsert(
                        ids=[recipe_id],
                        documents=[json.dumps(normalized_recipe)],
                        metadatas=[metadata]
                    )
                    
                    recipe_cache.search_collection.upsert(
                        ids=[recipe_id],
                        documents=[search_text],
                        metadatas=[metadata]
                    )
                    
                    print(f"Added recipe: {normalized_recipe['title']}")
                    all_recipes.append(normalized_recipe)
                time.sleep(0.2)  # Rate limiting
            except Exception as e:
                print(f"Error processing recipe {meal['idMeal']}: {e}")
    
    print(f"\nStored {len(all_recipes)} recipes in ChromaDB!")

if __name__ == "__main__":
    # Clear existing data
    try:
        recipe_cache.clear_cache()
        print("Cleared existing cache")
    except:
        pass
    
    # Fetch and store new recipes
    fetch_and_store_recipes() 