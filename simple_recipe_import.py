import requests
import time
import json
import chromadb
from chromadb.utils import embedding_functions

def import_recipes_simple():
    """Simple recipe import that won't hang"""
    
    print("🚀 Starting simple recipe import...")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    
    # Get or create the recipe collection
    recipe_collection = client.get_or_create_collection(
        name="recipe_details_cache",
        metadata={"description": "Cache for individual recipe details"},
        embedding_function=embedding_function
    )
    
    print(f"📊 Current recipe count: {recipe_collection.count()}")
    
    # TheMealDB API endpoints
    MEALDB_LIST_URL = "https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
    MEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}"
    
    # Cuisines to fetch (expanded to get more recipes)
    CUISINES = [
        "Italian", "Chinese", "Mexican", "Indian", "French", "Thai", "Japanese", "American",
        "Spanish", "Moroccan", "Greek", "Turkish", "British", "Irish", "Caribbean",
        "Vietnamese", "Korean", "Indonesian", "Malaysian", "Filipino", "Lebanese", "Egyptian"
    ]
    
    total_imported = 0
    
    for cuisine in CUISINES:
        print(f"\n🍽️  Importing {cuisine} recipes...")
        
        try:
            # Fetch recipe list for this cuisine
            response = requests.get(MEALDB_LIST_URL.format(area=cuisine), timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to fetch {cuisine} recipes: {response.status_code}")
                continue
                
            data = response.json()
            if not data or 'meals' not in data or not data['meals']:
                print(f"⚠️  No {cuisine} recipes found")
                continue
            
            recipes = data['meals'][:25]  # Limit to 25 per cuisine to get more recipes
            print(f"📋 Found {len(recipes)} {cuisine} recipes")
            
            cuisine_imported = 0
            
            for i, meal in enumerate(recipes):
                try:
                    # Get full recipe details
                    detail_response = requests.get(MEALDB_LOOKUP_URL.format(id=meal['idMeal']), timeout=10)
                    if detail_response.status_code != 200:
                        continue
                        
                    meal_detail = detail_response.json()
                    if not meal_detail or 'meals' not in meal_detail or not meal_detail['meals']:
                        continue
                    
                    meal_data = meal_detail['meals'][0]
                    
                    # Create recipe object
                    recipe = {
                        'id': meal_data['idMeal'],
                        'title': meal_data['strMeal'],
                        'cuisine': cuisine,
                        'image': meal_data.get('strMealThumb', ''),
                        'instructions': meal_data.get('strInstructions', ''),
                        'ingredients': [],
                        'diets': []
                    }
                    
                    # Extract ingredients
                    for i in range(1, 21):
                        ingredient = meal_data.get(f'strIngredient{i}')
                        measure = meal_data.get(f'strMeasure{i}')
                        if ingredient and ingredient.strip():
                            recipe['ingredients'].append({
                                'name': ingredient.strip(),
                                'amount': measure.strip() if measure else ''
                            })
                    
                    # Determine dietary restrictions
                    if any('chicken' in ing['name'].lower() for ing in recipe['ingredients']):
                        recipe['diets'].append('contains-meat')
                    elif any('beef' in ing['name'].lower() for ing in recipe['ingredients']):
                        recipe['diets'].append('contains-meat')
                    elif any('pork' in ing['name'].lower() for ing in recipe['ingredients']):
                        recipe['diets'].append('contains-meat')
                    else:
                        recipe['diets'].append('vegetarian')
                    
                    # Add to ChromaDB
                    doc_text = f"{recipe['title']} {cuisine} {' '.join([ing['name'] for ing in recipe['ingredients']])}"
                    
                    recipe_collection.upsert(
                        ids=[recipe['id']],
                        documents=[doc_text],
                        metadatas=[{
                            'id': recipe['id'],
                            'title': recipe['title'],
                            'cuisine': cuisine,
                            'image': recipe['image'],
                            'diets': ', '.join(recipe['diets']),
                            'ingredient_count': len(recipe['ingredients'])
                        }]
                    )
                    
                    cuisine_imported += 1
                    total_imported += 1
                    
                    if cuisine_imported % 5 == 0:
                        print(f"   ✅ Imported {cuisine_imported} {cuisine} recipes...")
                    
                    # Small delay to avoid overwhelming the API
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"   ⚠️  Error importing recipe {meal.get('idMeal', 'unknown')}: {e}")
                    continue
            
            print(f"✅ Successfully imported {cuisine_imported} {cuisine} recipes")
            
        except Exception as e:
            print(f"❌ Error processing {cuisine}: {e}")
            continue
    
    print(f"\n🎉 Import complete! Total recipes imported: {total_imported}")
    print(f"📊 Final recipe count: {recipe_collection.count()}")
    
    if recipe_collection.count() > 100:
        print("✅ Success! Your app should now show recipes!")
    else:
        print("⚠️  Recipe count is still low - there might be an issue")

if __name__ == "__main__":
    import_recipes_simple() 