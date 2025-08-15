#!/usr/bin/env python3
"""
Test what tags are available in the recipe data
"""

import requests
import json

def test_recipe_tags():
    """Test the backend response to see what tags are available"""
    
    # Test the get_recipes endpoint
    url = "http://localhost:5003/get_recipes"
    params = {
        "limit": 5,
        "offset": 0
    }
    
    try:
        print("🔍 Testing recipe tags...")
        print(f"URL: {url}")
        print(f"Params: {params}")
        print("=" * 50)
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response status: {response.status_code}")
            print(f"📊 Total recipes: {data.get('total', 'N/A')}")
            print(f"📝 Results count: {len(data.get('results', []))}")
            
            recipes = data.get('results', [])
            
            for i, recipe in enumerate(recipes[:5]):
                print(f"\n🍳 Recipe {i+1}: {recipe.get('title', 'No title')}")
                print(f"  ID: {recipe.get('id', 'No ID')}")
                
                # Check all tag-related fields
                print(f"  Tags: {recipe.get('tags', 'No tags')}")
                print(f"  Diets: {recipe.get('diets', 'No diets')}")
                print(f"  Dietary Restrictions: {recipe.get('dietary_restrictions', 'No dietary restrictions')}")
                print(f"  Dish Types: {recipe.get('dish_types', 'No dish types')}")
                print(f"  Cuisine: {recipe.get('cuisine', 'No cuisine')}")
                print(f"  Cuisines: {recipe.get('cuisines', 'No cuisines')}")
                
                # Show the types of each field
                if 'tags' in recipe:
                    print(f"  Tags type: {type(recipe['tags'])}")
                if 'diets' in recipe:
                    print(f"  Diets type: {type(recipe['diets'])}")
                if 'dietary_restrictions' in recipe:
                    print(f"  Dietary restrictions type: {type(recipe['dietary_restrictions'])}")
                if 'dish_types' in recipe:
                    print(f"  Dish types type: {type(recipe['dish_types'])}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_recipe_tags()
