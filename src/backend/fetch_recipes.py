import os
import json
import time
import requests
from dotenv import load_dotenv
from services.recipe_cache_service import RecipeCacheService

# Load environment variables
load_dotenv()

# Initialize ChromaDB
recipe_cache = RecipeCacheService()

# Spoonacular API configuration
SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY', '01f12ed117584307b5cba262f43a8d49')
BASE_URL = 'https://api.spoonacular.com/recipes'

def fetch_recipes_from_spoonacular(limit=500):
    """Fetch recipes from Spoonacular API with comprehensive details"""
    print(f"\nFetching {limit} recipes from Spoonacular API...")
    
    # First, get recipe IDs with basic info
    search_url = f"{BASE_URL}/complexSearch"
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'number': limit,
        'addRecipeInformation': 'true',
        'fillIngredients': 'true',
        'instructionsRequired': 'true',
        'addRecipeNutrition': 'true',
        'sort': 'popularity',
        'sortDirection': 'desc'
    }
    
    try:
        # Get list of recipes with basic info
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'results' not in data or not data['results']:
            print("No recipes found in the response")
            return []
            
        recipes = []
        total_recipes = len(data['results'])
        print(f"Found {total_recipes} recipes. Fetching detailed information...")
        
        # Process each recipe to get detailed information
        for i, recipe in enumerate(data['results'], 1):
            try:
                recipe_id = recipe['id']
                print(f"\nProcessing recipe {i}/{total_recipes}: ID {recipe_id}")
                
                # Get detailed recipe information
                detail_url = f"{BASE_URL}/{recipe_id}/information"
                detail_params = {
                    'apiKey': SPOONACULAR_API_KEY,
                    'includeNutrition': 'true'
                }
                
                detail_response = requests.get(detail_url, params=detail_params)
                detail_response.raise_for_status()
                detailed_recipe = detail_response.json()
                
                # Extract and format recipe data
                formatted_recipe = {
                    'id': str(detailed_recipe['id']),
                    'title': detailed_recipe.get('title', 'Untitled Recipe'),
                    'image': detailed_recipe.get('image', ''),
                    'servings': detailed_recipe.get('servings', 2),
                    'readyInMinutes': detailed_recipe.get('readyInMinutes', 30),
                    'sourceUrl': detailed_recipe.get('sourceUrl', ''),
                    'sourceName': detailed_recipe.get('sourceName', ''),
                    'summary': detailed_recipe.get('summary', ''),
                    'cuisines': detailed_recipe.get('cuisines', []),
                    'diets': detailed_recipe.get('diets', []),
                    'dishTypes': detailed_recipe.get('dishTypes', []),
                    'instructions': detailed_recipe.get('instructions', ''),
                    'ingredients': [
                        {
                            'id': ing.get('id'),
                            'name': ing.get('name', '').lower(),
                            'amount': ing.get('measures', {}).get('metric', {}).get('amount', 0),
                            'unit': ing.get('measures', {}).get('metric', {}).get('unitShort', ''),
                            'original': ing.get('original', '')
                        }
                        for ing in detailed_recipe.get('extendedIngredients', [])
                    ],
                    'nutrition': {
                        'calories': next(
                            (n['amount'] for n in detailed_recipe.get('nutrition', {}).get('nutrients', [])
                             if n['name'] == 'Calories'), 0
                        ),
                        'protein': next(
                            (n['amount'] for n in detailed_recipe.get('nutrition', {}).get('nutrients', [])
                             if n['name'] == 'Protein'), 0
                        ),
                        'carbs': next(
                            (n['amount'] for n in detailed_recipe.get('nutrition', {}).get('nutrients', [])
                             if n['name'] == 'Carbohydrates'), 0
                        ),
                        'fat': next(
                            (n['amount'] for n in detailed_recipe.get('nutrition', {}).get('nutrients', [])
                             if n['name'] == 'Fat'), 0
                        )
                    },
                    'analyzedInstructions': detailed_recipe.get('analyzedInstructions', [])
                }
                
                recipes.append(formatted_recipe)
                print(f"✅ Processed: {formatted_recipe['title']}")
                
                # Be nice to the API - add a small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing recipe {recipe_id}: {str(e)}")
                continue
                
        return recipes
        
    except Exception as e:
        print(f"Error fetching recipes: {str(e)}")
        return []

def store_recipes_in_chromadb(recipes):
    """Store recipes in ChromaDB"""
    if not recipes:
        print("No recipes to store")
        return
    
    print(f"\nStoring {len(recipes)} recipes in ChromaDB...")
    
    try:
        # Clear existing data
        print("Clearing existing cache...")
        recipe_cache.clear_cache()
        print("✓ Cache cleared successfully")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        search_texts = []
        
        for recipe in recipes:
            recipe_id = str(recipe['id'])
            ids.append(recipe_id)
            
            # Store the full recipe as a JSON string
            documents.append(json.dumps(recipe))
            
            # Create metadata
            metadata = {
                'id': recipe_id,
                'title': recipe['title'],
                'cuisine': recipe['cuisines'][0] if recipe.get('cuisines') else 'International',
                'diet': recipe['diets'][0] if recipe.get('diets') else 'None',
                'calories': recipe.get('nutrition', {}).get('calories', 0),
                'readyInMinutes': recipe.get('readyInMinutes', 30),
                'ingredients_count': len(recipe.get('ingredients', [])),
                'cached_at': str(int(time.time()))
            }
            metadatas.append(metadata)
            
            # Create search text
            search_terms = [
                recipe['title'],
                *[ing['name'] for ing in recipe.get('ingredients', [])],
                *recipe.get('cuisines', []),
                *recipe.get('diets', []),
                *recipe.get('dishTypes', [])
            ]
            search_text = ' '.join(filter(None, search_terms)).lower()
            search_texts.append(search_text)
        
        # Store in recipe collection
        recipe_cache.recipe_collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        # Store in search collection
        recipe_cache.search_collection.upsert(
            ids=ids,
            documents=search_texts,
            metadatas=metadatas
        )
        
        print(f"✓ Successfully stored {len(recipes)} recipes in ChromaDB")
        
    except Exception as e:
        print(f"Error storing recipes in ChromaDB: {str(e)}")
        raise

def main():
    print("Starting recipe import process...")
    
    # Fetch recipes from Spoonacular
    recipes = fetch_recipes_from_spoonacular(limit=500)
    
    if recipes:
        # Store recipes in ChromaDB
        store_recipes_in_chromadb(recipes)
        
        # Verify the count
        count = len(recipe_cache.recipe_collection.get()['documents'])
        print(f"\nTotal recipes in ChromaDB: {count}")
    else:
        print("No recipes were fetched. Please check the API key and try again.")

if __name__ == "__main__":
    main()
