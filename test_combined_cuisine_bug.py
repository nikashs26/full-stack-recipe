#!/usr/bin/env python3
"""
Test the combined cuisine search to identify the bug
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def test_combined_cuisine_bug():
    """Test the combined cuisine search to identify the bug"""
    
    print("=== Testing Combined Cuisine Search Bug ===\n")
    
    # Test 1: Individual cuisine searches (should work correctly)
    print("1. Testing individual cuisine searches...")
    
    indian_response = requests.get(f"{BASE_URL}/get_recipes?cuisine=indian&limit=1000")
    italian_response = requests.get(f"{BASE_URL}/get_recipes?cuisine=italian&limit=1000")
    
    if indian_response.status_code == 200 and italian_response.status_code == 200:
        indian_data = indian_response.json()
        italian_data = italian_response.json()
        
        indian_count = indian_data.get('total', 0)
        italian_count = italian_data.get('total', 0)
        
        print(f"   Indian only: {indian_count} recipes")
        print(f"   Italian only: {italian_count} recipes")
        print(f"   Expected combined total: {indian_count + italian_count}")
    else:
        print(f"   Error getting individual cuisine recipes")
        return
    
    # Test 2: Combined cuisine search (the problematic one)
    print(f"\n2. Testing combined cuisine search...")
    
    combined_response = requests.get(f"{BASE_URL}/get_recipes?cuisine=indian,italian&limit=1000")
    
    if combined_response.status_code == 200:
        combined_data = combined_response.json()
        combined_count = combined_data.get('total', 0)
        combined_recipes = combined_data.get('results', [])
        
        print(f"   Indian + Italian combined: {combined_count} recipes")
        print(f"   Difference from expected: {indian_count + italian_count - combined_count}")
        
        if combined_count < max(indian_count, italian_count):
            print(f"   ⚠️  BUG: Combined count is LESS than individual counts!")
        elif combined_count > indian_count + italian_count:
            print(f"   ✅ Combined count is MORE than sum (some recipes have multiple cuisines)")
        else:
            print(f"   ℹ️  Combined count equals sum (no overlap)")
        
        # Show sample recipes from combined search
        print(f"\n   Sample recipes from combined search:")
        for i, recipe in enumerate(combined_recipes[:5], 1):
            title = recipe.get('title', 'Unknown')
            cuisines = recipe.get('cuisines', [])
            cuisine = recipe.get('cuisine', '')
            print(f"     {i}. {title}")
            print(f"        cuisines: {cuisines}")
            print(f"        cuisine: {cuisine}")
    else:
        print(f"   Error getting combined cuisine recipes: {combined_response.status_code}")
        return
    
    # Test 3: Check if there are recipes that should match both
    print(f"\n3. Checking for recipes that should match both cuisines...")
    
    # Get all recipes and check for multiple cuisine tags
    all_response = requests.get(f"{BASE_URL}/get_recipes?limit=1000")
    
    if all_response.status_code == 200:
        all_data = all_response.json()
        all_recipes = all_data.get('results', [])
        
        recipes_with_both = []
        
        for recipe in all_recipes:
            title = recipe.get('title', 'Unknown')
            recipe_cuisines = set()
            
            # Check cuisines field
            if 'cuisines' in recipe and recipe['cuisines']:
                if isinstance(recipe['cuisines'], list):
                    for c in recipe['cuisines']:
                        if c and isinstance(c, str):
                            recipe_cuisines.add(c.lower().strip())
                elif isinstance(recipe['cuisines'], str):
                    for c in recipe['cuisines'].split(','):
                        if c.strip():
                            recipe_cuisines.add(c.lower().strip())
            
            # Check cuisine field
            if 'cuisine' in recipe and recipe['cuisine']:
                if isinstance(recipe['cuisine'], list):
                    for c in recipe['cuisine']:
                        if c and isinstance(c, str):
                            recipe_cuisines.add(c.lower().strip())
                elif isinstance(recipe['cuisine'], str):
                    for c in recipe['cuisine'].split(','):
                        if c.strip():
                            recipe_cuisines.add(c.lower().strip())
            
            # Check if recipe has both Indian and Italian
            if 'indian' in recipe_cuisines and 'italian' in recipe_cuisines:
                recipes_with_both.append({
                    'title': title,
                    'cuisines': list(recipe_cuisines)
                })
        
        print(f"   Recipes with both Indian AND Italian cuisines: {len(recipes_with_both)}")
        
        if recipes_with_both:
            print(f"   These recipes should appear in both individual searches:")
            for i, recipe in enumerate(recipes_with_both[:5], 1):
                print(f"     {i}. {recipe['title']} - {recipe['cuisines']}")
            if len(recipes_with_both) > 5:
                print(f"     ... and {len(recipes_with_both) - 5} more")
        else:
            print(f"   No recipes have both Indian and Italian cuisines")
    
    # Test 4: Check backend parameter parsing
    print(f"\n4. Testing backend parameter parsing...")
    
    # Test different parameter formats
    test_params = [
        "indian,italian",
        "indian, italian",  # with space
        "indian , italian",  # with spaces around comma
        "indian,italian,mexican"  # three cuisines
    ]
    
    for param in test_params:
        response = requests.get(f"{BASE_URL}/get_recipes?cuisine={param}&limit=1000")
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            print(f"   '{param}': {count} recipes")
        else:
            print(f"   '{param}': Error {response.status_code}")

if __name__ == "__main__":
    test_combined_cuisine_bug()
