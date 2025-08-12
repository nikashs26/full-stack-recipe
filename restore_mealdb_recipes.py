#!/usr/bin/env python3
"""
Simple script to restore recipes from TheMealDB API
This will help get you back to a good number of recipes after the data loss
"""

import requests
import time
import json
import chromadb

# Configuration
MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"

# Cuisines to fetch from TheMealDB
CUISINES = [
    "Italian", "Chinese", "Mexican", "Indian", "French", 
    "Thai", "Japanese", "American", "Spanish", "Moroccan", 
    "Greek", "Turkish", "British", "Irish", "Caribbean"
]

def get_current_recipe_count():
    """Get current recipe count from ChromaDB"""
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("recipe_details_cache")
        return collection.count()
    except Exception as e:
        print(f"Error getting recipe count: {e}")
        return 0

def fetch_mealdb_recipes():
    """Fetch recipes from TheMealDB API"""
    print("🍽️ Fetching recipes from TheMealDB...")
    all_recipes = []
    
    for cuisine in CUISINES:
        try:
            print(f"   🔍 Fetching {cuisine} recipes...")
            
            # Get recipe list for cuisine
            response = requests.get(f"{MEALDB_BASE_URL}/filter.php?a={cuisine}")
            if response.ok:
                data = response.json()
                if data and 'meals' in data and data['meals']:
                    # Limit to 60 recipes per cuisine to get more variety
                    for meal in data['meals'][:60]:
                        try:
                            # Get full recipe details
                            meal_response = requests.get(f"{MEALDB_BASE_URL}/lookup.php?i={meal['idMeal']}")
                            if meal_response.ok:
                                meal_data = meal_response.json()
                                if meal_data and 'meals' in meal_data and meal_data['meals']:
                                    recipe = meal_data['meals'][0]
                                    # Add cuisine info
                                    recipe['cuisine'] = cuisine
                                    all_recipes.append(recipe)
                        except Exception as e:
                            continue
                            
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ Error fetching {cuisine} recipes: {e}")
            continue
    
    print(f"✅ Fetched {len(all_recipes)} recipes from TheMealDB")
    return all_recipes

def normalize_recipe(recipe):
    """Normalize TheMealDB recipe format"""
    normalized = {
        'id': f"mealdb_{recipe['idMeal']}",
        'title': recipe.get('strMeal', 'Untitled'),
        'cuisines': [recipe.get('cuisine', 'Unknown')],
        'diets': [],
        'ingredients': [],
        'instructions': recipe.get('strInstructions', ''),
        'image': recipe.get('strMealThumb', ''),
        'source': 'TheMealDB'
    }
    
    # Extract ingredients
    for i in range(1, 21):  # TheMealDB has up to 20 ingredients
        ingredient = recipe.get(f'strIngredient{i}')
        measure = recipe.get(f'strMeasure{i}')
        if ingredient and ingredient.strip():
            normalized['ingredients'].append({
                'name': ingredient.strip(),
                'amount': measure.strip() if measure else ''
            })
    
    # Infer dietary restrictions
    ingredients_lower = [ing['name'].lower() for ing in normalized['ingredients']]
    if not any(meat in ' '.join(ingredients_lower) for meat in ['chicken', 'beef', 'pork', 'fish', 'meat', 'lamb']):
        normalized['diets'].append('vegetarian')
    
    return normalized

def store_recipes_in_chromadb(recipes):
    """Store recipes in ChromaDB"""
    if not recipes:
        print("No recipes to store")
        return 0
    
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("recipe_details_cache")
        
        stored_count = 0
        
        for recipe in recipes:
            try:
                # Convert recipe to JSON string
                recipe_doc = json.dumps(recipe)
                
                # Create metadata
                metadata = {
                    'id': recipe['id'],
                    'title': recipe['title'],
                    'cuisines': ','.join(recipe['cuisines']),
                    'diets': ','.join(recipe['diets']),
                    'ingredients': json.dumps(recipe['ingredients']),
                    'source': recipe['source']
                }
                
                # Store in ChromaDB
                collection.upsert(
                    ids=[recipe['id']],
                    documents=[recipe_doc],
                    metadatas=[metadata]
                )
                
                stored_count += 1
                
                if stored_count % 50 == 0:
                    print(f"   📝 Stored {stored_count} recipes...")
                    
            except Exception as e:
                print(f"   ❌ Error storing recipe {recipe.get('id', 'unknown')}: {e}")
                continue
        
        print(f"✅ Successfully stored {stored_count} recipes in ChromaDB")
        return stored_count
        
    except Exception as e:
        print(f"❌ Error storing recipes in ChromaDB: {e}")
        return 0

def main():
    print("🍳 TheMealDB Recipe Restoration Script")
    print("=" * 50)
    
    # Check initial recipe count
    initial_count = get_current_recipe_count()
    print(f"📊 Current recipe count: {initial_count}")
    
    # Fetch recipes from TheMealDB
    mealdb_recipes = fetch_mealdb_recipes()
    
    if not mealdb_recipes:
        print("❌ No recipes fetched from TheMealDB")
        return
    
    # Normalize recipes
    print("\n🔄 Normalizing recipes...")
    normalized_recipes = [normalize_recipe(r) for r in mealdb_recipes]
    
    # Remove duplicates
    unique_recipes = {r['id']: r for r in normalized_recipes}.values()
    
    print(f"📋 Total unique recipes to store: {len(unique_recipes)}")
    
    # Store in ChromaDB
    print("\n💾 Storing recipes in ChromaDB...")
    stored_count = store_recipes_in_chromadb(list(unique_recipes))
    
    # Check final count
    final_count = get_current_recipe_count()
    
    print("\n" + "="*50)
    print("📊 Restoration Summary:")
    print(f"   Initial count: {initial_count}")
    print(f"   Recipes added: {stored_count}")
    print(f"   Final count: {final_count}")
    
    if final_count > initial_count:
        print("🎉 Success! Added recipes from TheMealDB!")
        print(f"💡 You now have {final_count} recipes total")
        
        if final_count < 1000:
            print("💡 To get more recipes, you can:")
            print("   1. Run this script again to add more cuisines")
            print("   2. Use the full restoration script with Spoonacular API key")
    else:
        print("⚠️  No new recipes were added")
    
    print(f"\n🌐 Your recipes are now available in the app!")

if __name__ == "__main__":
    main() 