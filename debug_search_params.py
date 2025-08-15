#!/usr/bin/env python3
"""
Debug the search parameters to see exactly what's being passed
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def debug_search_params():
    """Debug the search parameters"""
    
    print("=== Debugging Search Parameters ===\n")
    
    # Test 1: Check what the backend receives
    print("1. Testing what the backend receives...")
    
    # Test with different parameter formats
    test_params = [
        "indian",
        "italian", 
        "indian,italian",
        "indian, italian",
        "indian , italian"
    ]
    
    for param in test_params:
        print(f"\n   Testing parameter: '{param}'")
        
        # Make the request
        response = requests.get(f"{BASE_URL}/get_recipes?cuisine={param}&limit=1000")
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            print(f"     Total recipes: {count}")
            
            # Show the first few recipes to see what's being returned
            recipes = data.get('results', [])
            if recipes:
                print(f"     First recipe: {recipes[0].get('title', 'Unknown')}")
                print(f"     First recipe cuisines: {recipes[0].get('cuisines', [])}")
                print(f"     First recipe cuisine: {recipes[0].get('cuisine', '')}")
        else:
            print(f"     Error: {response.status_code}")
    
    # Test 2: Check if there's a backend issue with parameter parsing
    print(f"\n2. Testing backend parameter parsing...")
    
    # Test with URL encoding
    import urllib.parse
    
    test_cuisines = ["indian", "italian"]
    encoded_param = urllib.parse.quote(",".join(test_cuisines))
    
    print(f"   Testing with URL encoding: '{encoded_param}'")
    response = requests.get(f"{BASE_URL}/get_recipes?cuisine={encoded_param}&limit=1000")
    
    if response.status_code == 200:
        data = response.json()
        count = data.get('total', 0)
        print(f"     Total recipes: {count}")
    else:
        print(f"     Error: {response.status_code}")
    
    # Test 3: Check if there's a backend caching issue
    print(f"\n3. Testing for backend caching issues...")
    
    # Make the same request multiple times to see if results change
    print(f"   Making multiple requests for 'indian,italian'...")
    
    for i in range(3):
        response = requests.get(f"{BASE_URL}/get_recipes?cuisine=indian,italian&limit=1000")
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            print(f"     Request {i+1}: {count} recipes")
        else:
            print(f"     Request {i+1}: Error {response.status_code}")
    
    # Test 4: Check if there's a data consistency issue
    print(f"\n4. Testing data consistency...")
    
    # Get all recipes and manually check cuisine distribution
    response = requests.get(f"{BASE_URL}/get_recipes?limit=1000")
    
    if response.status_code == 200:
        data = response.json()
        recipes = data.get('results', [])
        total = data.get('total', 0)
        
        print(f"   Total recipes available: {total}")
        
        # Count recipes by cuisine manually
        cuisine_counts = {}
        for recipe in recipes:
            cuisines = recipe.get('cuisines', [])
            if isinstance(cuisines, list):
                for cuisine in cuisines:
                    if cuisine:
                        cuisine_lower = cuisine.lower()
                        cuisine_counts[cuisine_lower] = cuisine_counts.get(cuisine_lower, 0) + 1
        
        print(f"   Manual cuisine counts:")
        for cuisine, count in sorted(cuisine_counts.items()):
            print(f"     {cuisine}: {count}")
        
        # Check if the issue is in the data
        indian_count = cuisine_counts.get('indian', 0)
        italian_count = cuisine_counts.get('italian', 0)
        
        print(f"\n   Expected combined count: {indian_count + italian_count}")
        print(f"   Actual combined count: 116")
        print(f"   Missing: {indian_count + italian_count - 116}")
        
        if indian_count + italian_count > 116:
            print(f"   ⚠️  The backend search is not returning all matching recipes!")

if __name__ == "__main__":
    debug_search_params()
