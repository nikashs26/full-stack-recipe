#!/usr/bin/env python3
"""
Script to import thousands of free recipes into the recipe app
This uses the Spoonacular API via the existing endpoints to populate the database
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:5003"

def test_backend_connection():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health")
        if response.ok:
            print("✅ Backend is running!")
            print(f"Status: {response.json()}")
            return True
        else:
            print("❌ Backend not responding properly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

def populate_recipes_via_api():
    """Populate recipes by making various searches which will cache them via Spoonacular API"""
    print("\n🍳 Populating recipes via search API...")
    
    # Various search terms to get a diverse collection of recipes
    search_terms = [
        # Cuisines
        "italian", "mexican", "indian", "chinese", "japanese", "thai", "mediterranean", 
        "french", "korean", "american", "greek", "spanish", "vietnamese",
        
        # Meal types
        "breakfast", "lunch", "dinner", "dessert", "snack", "appetizer", 
        "soup", "salad", "main course", "side dish",
        
        # Cooking methods
        "grilled", "baked", "fried", "steamed", "roasted", "slow cooker", 
        "instant pot", "air fryer", "no cook",
        
        # Dietary preferences
        "vegetarian", "vegan", "gluten free", "keto", "paleo", "low carb",
        "healthy", "low calorie", "high protein",
        
        # Popular dishes
        "pasta", "pizza", "chicken", "beef", "fish", "seafood", "rice",
        "noodles", "curry", "stir fry", "casserole", "sandwich",
        
        # Ingredients
        "tomato", "chicken breast", "ground beef", "salmon", "broccoli",
        "cheese", "eggs", "potatoes", "onions", "garlic"
    ]
    
    total_recipes = 0
    successful_searches = 0
    
    for i, term in enumerate(search_terms):
        try:
            print(f"🔍 Search {i+1}/{len(search_terms)}: '{term}'")
            
            # Make search request
            response = requests.get(f"{BACKEND_URL}/get_recipes", params={"query": term})
            print("From Recipe API: ", response)
            if response.ok:
                data = response.json()
                recipes = data.get("results", [])
                recipe_count = len(recipes)
                total_recipes += recipe_count
                successful_searches += 1
                
                print(f"   ✅ Found {recipe_count} recipes")
                
                # Small delay to be respectful to the API
                time.sleep(0.5)
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error searching for '{term}': {e}")
    
    print(f"\n📊 Search Summary:")
    print(f"   - Successful searches: {successful_searches}/{len(search_terms)}")
    print(f"   - Total recipes found: {total_recipes}")
    
    return successful_searches > 0

def get_popular_recipes():
    """Get popular recipes without search parameters"""
    print("\n⭐ Getting popular recipes...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/get_recipes")
        
        if response.ok:
            data = response.json()
            recipes = data.get("results", [])
            print(f"✅ Found {len(recipes)} popular recipes")
            return len(recipes) > 0
        else:
            print(f"❌ Failed to get popular recipes: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting popular recipes: {e}")
        return False

def check_recipe_count():
    """Check how many recipes are currently available"""
    print("\n📊 Checking current recipe count...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/recipes")
        
        if response.ok:
            data = response.json()
            recipes = data.get("results", [])
            count = len(recipes)
            print(f"📈 Current recipe count: {count}")
            
            if count > 0:
                print("   Sample recipes:")
                for i, recipe in enumerate(recipes[:5]):
                    title = recipe.get("title", "Untitled")
                    cuisine = recipe.get("cuisines", ["Unknown"])
                    if isinstance(cuisine, list) and cuisine:
                        cuisine = cuisine[0]
                    print(f"   {i+1}. {title} ({cuisine})")
            
            return count
        else:
            print(f"❌ Failed to get recipe count: {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"❌ Error checking recipe count: {e}")
        return 0

def search_specific_ingredients():
    """Search for recipes with specific popular ingredients"""
    print("\n🥘 Searching by popular ingredients...")
    
    ingredients = [
        "chicken", "beef", "salmon", "shrimp", "eggs", "cheese", "tomatoes",
        "onions", "garlic", "potatoes", "rice", "pasta", "beans", "mushrooms"
    ]
    
    total_found = 0
    
    for ingredient in ingredients:
        try:
            print(f"🔍 Searching recipes with: {ingredient}")
            
            response = requests.get(f"{BACKEND_URL}/get_recipes", params={"ingredient": ingredient})
            
            if response.ok:
                data = response.json()
                recipes = data.get("results", [])
                count = len(recipes)
                total_found += count
                print(f"   ✅ Found {count} recipes with {ingredient}")
                
                time.sleep(0.5)  # Rate limiting
            else:
                print(f"   ❌ Search failed for {ingredient}")
                
        except Exception as e:
            print(f"   ❌ Error searching for {ingredient}: {e}")
    
    print(f"🍽️ Total recipes found by ingredient: {total_found}")
    return total_found > 0

def main():
    print("🍳 Free Recipe Population Script")
    print("=" * 50)
    
    # Test backend connection
    if not test_backend_connection():
        print("\n❌ Cannot proceed without backend connection")
        return
    
    # Check initial recipe count
    initial_count = check_recipe_count()
    
    # Method 1: Get popular recipes
    print("\n" + "="*50)
    get_popular_recipes()
    
    # Method 2: Search by various terms to populate the database
    print("\n" + "="*50)
    populate_recipes_via_api()
    
    # Method 3: Search by ingredients
    print("\n" + "="*50)
    search_specific_ingredients()
    
    # Check final count
    print("\n" + "="*50)
    final_count = check_recipe_count()
    
    if final_count > initial_count:
        print(f"\n🎉 Success! Added {final_count - initial_count} recipes to the database")
        print("💡 These recipes are now cached and will load instantly on subsequent searches")
        print("\n🌐 Open your browser to http://localhost:8081 to see the recipes!")
        print("🔍 Try searching for different cuisines, ingredients, or meal types in your browser!")
    else:
        print(f"\n⚠️  No new recipes were added. Current count: {final_count}")
        if final_count > 0:
            print("✅ But you already have recipes available in the app!")
            print("🌐 Open your browser to http://localhost:8081 to see them")

if __name__ == "__main__":
    main() 