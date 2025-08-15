#!/usr/bin/env python3
"""
Debug script to investigate cuisine matching logic
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def debug_cuisine_matching():
    """Debug the cuisine matching logic"""
    
    print("=== Debugging Cuisine Matching ===\n")
    
    # Test 1: Get all recipes and analyze their cuisine fields
    print("1. Analyzing all recipes' cuisine fields...")
    response = requests.get(f"{BASE_URL}/get_recipes?limit=1000")
    
    if response.status_code != 200:
        print(f"Error getting recipes: {response.status_code}")
        return
    
    data = response.json()
    recipes = data.get('results', [])
    total = data.get('total', 0)
    
    print(f"   Total recipes: {total}")
    print(f"   Analyzing {len(recipes)} recipes...\n")
    
    # Analyze cuisine fields
    cuisine_field_analysis = {
        'cuisine': {},
        'cuisines': {},
        'tags': {},
        'missing_cuisine': 0
    }
    
    recipes_with_multiple_cuisines = []
    
    for i, recipe in enumerate(recipes):
        title = recipe.get('title', 'Unknown')
        
        # Check cuisine field
        cuisine = recipe.get('cuisine', '')
        if cuisine:
            if isinstance(cuisine, list):
                cuisine_str = ','.join([str(c) for c in cuisine if c])
            else:
                cuisine_str = str(cuisine)
            
            if cuisine_str:
                cuisine_field_analysis['cuisine'][cuisine_str] = cuisine_field_analysis['cuisine'].get(cuisine_str, 0) + 1
        else:
            cuisine_field_analysis['missing_cuisine'] += 1
        
        # Check cuisines field
        cuisines = recipe.get('cuisines', '')
        if cuisines:
            if isinstance(cuisines, list):
                cuisines_str = ','.join([str(c) for c in cuisines if c])
            else:
                cuisines_str = str(cuisines)
            
            if cuisines_str:
                cuisine_field_analysis['cuisines'][cuisines_str] = cuisine_field_analysis['cuisines'].get(cuisines_str, 0) + 1
        
        # Check tags field
        tags = recipe.get('tags', '')
        if tags:
            if isinstance(tags, list):
                tags_str = ','.join([str(t) for t in tags if t])
            else:
                tags_str = str(tags)
            
            if tags_str:
                cuisine_field_analysis['tags'][tags_str] = cuisine_field_analysis['tags'].get(tags_str, 0) + 1
        
        # Check for recipes with multiple cuisines
        all_cuisines = set()
        if cuisine:
            if isinstance(cuisine, list):
                all_cuisines.update([str(c).lower() for c in cuisine if c])
            else:
                all_cuisines.add(str(cuisine).lower())
        
        if cuisines:
            if isinstance(cuisines, list):
                all_cuisines.update([str(c).lower() for c in cuisines if c])
            else:
                all_cuisines.add(str(cuisines).lower())
        
        if len(all_cuisines) > 1:
            recipes_with_multiple_cuisines.append({
                'title': title,
                'cuisines': list(all_cuisines)
            })
    
    # Report findings
    print("2. Cuisine field analysis:")
    print(f"   Missing cuisine field: {cuisine_field_analysis['missing_cuisine']}")
    
    print(f"\n   Cuisine field values (top 10):")
    for cuisine, count in sorted(cuisine_field_analysis['cuisine'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"     '{cuisine}': {count}")
    
    print(f"\n   Cuisines field values (top 10):")
    for cuisines, count in sorted(cuisine_field_analysis['cuisines'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"     '{cuisines}': {count}")
    
    print(f"\n   Tags field values (top 10):")
    for tags, count in sorted(cuisine_field_analysis['tags'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"     '{tags}': {count}")
    
    print(f"\n3. Recipes with multiple cuisines:")
    if recipes_with_multiple_cuisines:
        for recipe in recipes_with_multiple_cuisines[:10]:
            print(f"   - {recipe['title']}: {recipe['cuisines']}")
        if len(recipes_with_multiple_cuisines) > 10:
            print(f"   ... and {len(recipes_with_multiple_cuisines) - 10} more")
    else:
        print("   No recipes found with multiple cuisines")
    
    # Test 2: Check specific cuisine searches
    print(f"\n4. Testing specific cuisine searches...")
    
    test_cuisines = ['indian', 'italian', 'mexican']
    for cuisine in test_cuisines:
        response = requests.get(f"{BASE_URL}/get_recipes?cuisine={cuisine}&limit=5")
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            recipes = data.get('results', [])
            print(f"\n   {cuisine.title()} cuisine:")
            print(f"     Total count: {count}")
            print(f"     Sample recipes:")
            for i, recipe in enumerate(recipes[:3], 1):
                title = recipe.get('title', 'Unknown')
                cuisine_field = recipe.get('cuisine', '')
                cuisines_field = recipe.get('cuisines', '')
                print(f"       {i}. {title}")
                print(f"          cuisine: {cuisine_field}")
                print(f"          cuisines: {cuisines_field}")
        else:
            print(f"   Error getting {cuisine} recipes: {response.status_code}")

if __name__ == "__main__":
    debug_cuisine_matching()
