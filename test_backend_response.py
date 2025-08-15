#!/usr/bin/env python3
"""
Test what the backend is actually returning for recipes
"""

import requests
import json

def test_backend_response():
    """Test the backend response to see what cuisine data is being returned"""
    
    # Test the get_recipes endpoint
    url = "http://localhost:5003/get_recipes"
    params = {
        "limit": 3,
        "offset": 0
    }
    
    try:
        print("🔍 Testing backend response...")
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
            
            for i, recipe in enumerate(recipes[:3]):
                print(f"\n🍳 Recipe {i+1}: {recipe.get('title', 'No title')}")
                print(f"  ID: {recipe.get('id', 'No ID')}")
                print(f"  Cuisine field: {recipe.get('cuisine', 'No cuisine')}")
                print(f"  Cuisines field: {recipe.get('cuisines', 'No cuisines')}")
                print(f"  All keys: {list(recipe.keys())}")
                
                # Check if cuisine data exists in other fields
                if 'cuisine' in recipe:
                    print(f"  Cuisine type: {type(recipe['cuisine'])}")
                    if isinstance(recipe['cuisine'], list):
                        print(f"  Cuisine list: {recipe['cuisine']}")
                    elif isinstance(recipe['cuisine'], str):
                        print(f"  Cuisine string: {recipe['cuisine']}")
                
                if 'cuisines' in recipe:
                    print(f"  Cuisines type: {type(recipe['cuisines'])}")
                    if isinstance(recipe['cuisines'], list):
                        print(f"  Cuisines list: {recipe['cuisines']}")
                    elif isinstance(recipe['cuisines'], str):
                        print(f"  Cuisines string: {recipe['cuisines']}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_backend_response()
