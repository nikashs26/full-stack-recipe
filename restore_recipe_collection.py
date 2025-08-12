#!/usr/bin/env python3
"""
Comprehensive script to restore recipe collection from both Spoonacular and TheMealDB
This will help get you back to around 1200 recipes after the data loss
"""

import requests
import time
import json
import chromadb
from collections import defaultdict

# Configuration
BACKEND_URL = "http://localhost:5003"
SPOONACULAR_API_KEY = "fe61cea1027f4164a8fbf96fe54fdbb4"  # Replace with your actual API key
MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"

# Cuisines to fetch from TheMealDB
CUISINES = [
    "Italian", "Chinese", "Mexican", "Indian", "French", 
    "Thai", "Japanese", "American", "Spanish", "Moroccan", 
    "Greek", "Turkish", "British", "Irish", "Caribbean"
]

# Search terms for Spoonacular
SPOONACULAR_SEARCH_TERMS = [
    # Cuisines
    "italian", "mexican", "indian", "chinese", "japanese", "thai", "mediterranean", 
    "french", "korean", "american", "greek", "spanish", "vietnamese",
    
    # Meal types
    "breakfast", "lunch", "dinner", "dessert", "snack", "appetizer", 
    "soup", "salad", "main course", "side dish",
    
    # Popular dishes
    "pasta", "pizza", "chicken", "beef", "fish", "seafood", "rice",
    "noodles", "curry", "stir fry", "casserole", "sandwich",
    
    # Ingredients
    "tomato", "chicken breast", "ground beef", "salmon", "broccoli",
    "cheese", "eggs", "potatoes", "onions", "garlic"
]

def test_backend_connection():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health")
        if response.ok:
            print("✅ Backend is running!")
            return True
        else:
            print("❌ Backend not responding properly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

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
    print("\n🍽️ Fetching recipes from TheMealDB...")
    all_recipes = []
    
    for cuisine in CUISINES:
        try:
            print(f"   🔍 Fetching {cuisine} recipes...")
            
            # Get recipe list for cuisine
            response = requests.get(f"{MEALDB_BASE_URL}/filter.php?a={cuisine}")
            if response.ok:
                data = response.json()
                if data and 'meals' in data and data['meals']:
                    # Limit to 50 recipes per cuisine to avoid overwhelming
                    for meal in data['meals'][:50]:
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

def fetch_spoonacular_recipes():
    """Fetch recipes from Spoonacular API"""
    if not SPOONACULAR_API_KEY:
        print("⚠️  No Spoonacular API key provided - skipping Spoonacular recipes")
        return []
    
    print("\n🍽️ Fetching recipes from Spoonacular...")
    all_recipes = []
    
    for term in SPOONACULAR_SEARCH_TERMS:
        try:
            print(f"   🔍 Searching for: {term}")
            
            # Search recipes
            response = requests.get(
                "https://api.spoonacular.com/recipes/complexSearch",
                params={
                    "apiKey": SPOONACULAR_API_KEY,
                    "query": term,
                    "number": 20,  # Limit per search
                    "addRecipeInformation": True
                }
            )
            
            if response.ok:
                data = response.json()
                recipes = data.get("results", [])
                all_recipes.extend(recipes)
                print(f"   ✅ Found {len(recipes)} recipes for '{term}'")
            else:
                print(f"   ❌ Search failed for '{term}': {response.status_code}")
                
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ Error searching for '{term}': {e}")
            continue
    
    print(f"✅ Fetched {len(all_recipes)} recipes from Spoonacular")
    return all_recipes

def normalize_mealdb_recipe(recipe):
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

def normalize_spoonacular_recipe(recipe):
    """Normalize Spoonacular recipe format"""
    normalized = {
        'id': f"spoonacular_{recipe['id']}",
        'title': recipe.get('title', 'Untitled'),
        'cuisines': recipe.get('cuisines', ['Unknown']),
        'diets': recipe.get('diets', []),
        'ingredients': [],
        'instructions': recipe.get('instructions', ''),
        'image': recipe.get('image', ''),
        'source': 'Spoonacular'
    }
    
    # Extract ingredients
    for ingredient in recipe.get('extendedIngredients', []):
        normalized['ingredients'].append({
            'name': ingredient.get('name', ''),
            'amount': f"{ingredient.get('amount', '')} {ingredient.get('unit', '')}".strip()
        })
    
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
    print("🍳 Recipe Collection Restoration Script")
    print("=" * 50)
    
    # Test backend connection
    if not test_backend_connection():
        print("\n❌ Cannot proceed without backend connection")
        return
    
    # Check initial recipe count
    initial_count = get_current_recipe_count()
    print(f"📊 Current recipe count: {initial_count}")
    
    target_count = 1200
    recipes_needed = target_count - initial_count
    
    if recipes_needed <= 0:
        print(f"✅ You already have {initial_count} recipes, which meets your target of {target_count}")
        return
    
    print(f"🎯 Target: {target_count} recipes")
    print(f"📈 Need to add: {recipes_needed} recipes")
    
    # Fetch recipes from both sources
    mealdb_recipes = fetch_mealdb_recipes()
    spoonacular_recipes = fetch_spoonacular_recipes()
    
    # Normalize recipes
    print("\n🔄 Normalizing recipes...")
    normalized_mealdb = [normalize_mealdb_recipe(r) for r in mealdb_recipes]
    normalized_spoonacular = [normalize_spoonacular_recipe(r) for r in spoonacular_recipes]
    
    # Combine and remove duplicates
    all_recipes = normalized_mealdb + normalized_spoonacular
    unique_recipes = {r['id']: r for r in all_recipes}.values()
    
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
    print(f"   Target: {target_count}")
    
    if final_count >= target_count:
        print("🎉 Success! You now have enough recipes!")
    else:
        print(f"⚠️  Still need {target_count - final_count} more recipes")
        print("💡 You can run this script again to add more recipes")
    
    print(f"\n🌐 Your recipes are now available in the app!")

if __name__ == "__main__":
    main() 