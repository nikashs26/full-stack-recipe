import requests
from services.recipe_cache_service import RecipeCacheService

# Initialize ChromaDB
recipe_cache = RecipeCacheService()

# TheMealDB API endpoints
MEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}"

# Two specific recipe IDs from TheMealDB
RECIPE_IDS = ["52772", "52959"]  # Teriyaki Chicken Casserole and Baked salmon with fennel & tomatoes

def fetch_and_store_recipes():
    """Fetch specific recipes and store them in ChromaDB"""
    
    for recipe_id in RECIPE_IDS:
        print(f"\nFetching recipe {recipe_id}...")
        
        # Get recipe from TheMealDB
        response = requests.get(MEALDB_LOOKUP_URL.format(id=recipe_id))
        if response.ok and response.json()['meals']:
            meal_data = response.json()['meals'][0]
            
            # Extract ingredients
            ingredients = []
            for i in range(1, 21):
                ingredient = meal_data.get(f'strIngredient{i}')
                measure = meal_data.get(f'strMeasure{i}')
                if ingredient and ingredient.strip():
                    ingredients.append({
                        'name': ingredient.strip(),
                        'amount': measure.strip() if measure else ''
                    })
            
            # Normalize recipe data
            recipe = {
                'id': meal_data['idMeal'],
                'title': meal_data['strMeal'],
                'cuisine': meal_data.get('strArea', 'International'),
                'cuisines': [meal_data.get('strArea', 'International')],
                'image': meal_data['strMealThumb'],
                'instructions': meal_data['strInstructions'].split('\r\n'),
                'ingredients': ingredients,
                'diets': []  # TheMealDB doesn't provide dietary info
            }
            
            # Store in ChromaDB
            recipe_id = str(recipe['id'])
            metadata = {
                "id": recipe_id,
                "title": recipe['title'],
                "cuisine": recipe['cuisine'],
                "cached_at": str(int(time.time()))
            }
            
            # Create search text
            search_terms = [
                recipe['title'],
                recipe['cuisine'],
                *[ing['name'] for ing in recipe['ingredients']]
            ]
            search_text = ' '.join(filter(None, search_terms))
            
            # Store in both collections
            recipe_cache.recipe_collection.upsert(
                ids=[recipe_id],
                documents=[json.dumps(recipe)],
                metadatas=[metadata]
            )
            
            recipe_cache.search_collection.upsert(
                ids=[recipe_id],
                documents=[search_text],
                metadatas=[metadata]
            )
            
            print(f"✅ Added recipe: {recipe['title']}")
        else:
            print(f"❌ Failed to fetch recipe {recipe_id}")

if __name__ == "__main__":
    import time
    import json
    
    print("Starting recipe import process...")
    
    # Clear existing data
    try:
        print("Clearing existing cache...")
        recipe_cache.clear_cache()
        print("✓ Cache cleared successfully")
    except Exception as e:
        print(f"⚠️ Error clearing cache: {e}")
    
    # Add new recipes
    print("\nAdding new recipes to ChromaDB...")
    fetch_and_store_recipes()
    
    # Verify recipes were added
    print("\nVerifying recipes in ChromaDB...")
    try:
        results = recipe_cache.recipe_collection.get()
        if not results or 'documents' not in results or not results['documents']:
            print("❌ No recipes found in ChromaDB")
        else:
            print(f"✓ Found {len(results['documents'])} recipes in ChromaDB:")
            for i, doc in enumerate(results['documents'], 1):
                try:
                    recipe = json.loads(doc)
                    print(f"\nRecipe {i}:")
                    print(f"  ID: {recipe.get('id', 'N/A')}")
                    print(f"  Title: {recipe.get('title', 'N/A')}")
                    print(f"  Cuisine: {recipe.get('cuisine', 'N/A')}")
                    print(f"  Ingredients: {len(recipe.get('ingredients', []))}")
                except json.JSONDecodeError as e:
                    print(f"  ❌ Error parsing recipe {i}: {e}")
                    print(f"  Raw document: {doc[:200]}...")
    except Exception as e:
        print(f"❌ Error querying ChromaDB: {e}")
    
    print("\nVerification complete!")
    
    # Print a summary of all recipes
    try:
        if results and 'documents' in results and results['documents']:
            print("\nSummary of all recipes in ChromaDB:")
            for doc in results['documents']:
                try:
                    recipe = json.loads(doc)
                    print(f"- {recipe.get('title', 'Untitled')} (ID: {recipe.get('id', 'N/A')}, Cuisine: {recipe.get('cuisine', 'N/A')})")
                except json.JSONDecodeError:
                    print("- [Error parsing recipe]")
    except Exception as e:
        print(f"Error generating recipe summary: {e}")