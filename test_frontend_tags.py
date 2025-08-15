#!/usr/bin/env python3
"""
Test if the frontend is now receiving the tag data correctly
"""

import requests
import json

def test_frontend_tags():
    """Test if the frontend is receiving tag data"""
    
    # Test the get_recipes endpoint
    url = "http://localhost:5003/get_recipes"
    params = {
        "limit": 3,
        "offset": 0
    }
    
    try:
        print("🔍 Testing frontend tag data...")
        print(f"URL: {url}")
        print(f"Params: {params}")
        print("=" * 50)
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response status: {response.status_code}")
            print(f"📊 Total recipes: {data.get('total', 'N/A')}")
            
            recipes = data.get('results', [])
            
            for i, recipe in enumerate(recipes[:3]):
                print(f"\n🍳 Recipe {i+1}: {recipe.get('title', 'No title')}")
                print(f"  ID: {recipe.get('id', 'No ID')}")
                
                # Check all tag fields
                print(f"  Cuisine: {recipe.get('cuisine', 'No cuisine')}")
                print(f"  Cuisines: {recipe.get('cuisines', 'No cuisines')}")
                print(f"  Tags: {recipe.get('tags', 'No tags')}")
                print(f"  Diets: {recipe.get('diets', 'No diets')}")
                print(f"  Dietary Restrictions: {recipe.get('dietary_restrictions', 'No dietary restrictions')}")
                print(f"  Dish Types: {recipe.get('dish_types', 'No dish types')}")
                
                # Check if any tags are missing
                missing_tags = []
                if not recipe.get('cuisine') and not recipe.get('cuisines'):
                    missing_tags.append('cuisine')
                if not recipe.get('tags'):
                    missing_tags.append('tags')
                if not recipe.get('diets') and not recipe.get('dietary_restrictions'):
                    missing_tags.append('diets')
                
                if missing_tags:
                    print(f"  ⚠️  Missing tag fields: {missing_tags}")
                else:
                    print(f"  ✅ All tag fields present")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_frontend_tags()
