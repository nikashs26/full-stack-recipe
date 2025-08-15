#!/usr/bin/env python3
"""
Test the exact cuisine matching logic to identify the counting discrepancy
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def test_cuisine_matching_logic():
    """Test the exact cuisine matching logic"""
    
    print("=== Testing Cuisine Matching Logic ===\n")
    
    # Test 1: Get all recipes and manually count by cuisine
    print("1. Manually counting recipes by cuisine...")
    response = requests.get(f"{BASE_URL}/get_recipes?limit=1000")
    
    if response.status_code != 200:
        print(f"Error getting recipes: {response.status_code}")
        return
    
    data = response.json()
    recipes = data.get('results', [])
    total = data.get('total', 0)
    
    print(f"   Total recipes: {total}")
    print(f"   Analyzing {len(recipes)} recipes...\n")
    
    # Manual cuisine counting
    manual_cuisine_counts = {}
    recipes_by_cuisine = {}
    
    for recipe in recipes:
        title = recipe.get('title', 'Unknown')
        
        # Extract all possible cuisines from the recipe
        recipe_cuisines = set()
        
        # Check cuisines field (most common)
        if 'cuisines' in recipe and recipe['cuisines']:
            if isinstance(recipe['cuisines'], list):
                for c in recipe['cuisines']:
                    if c and isinstance(c, str):
                        recipe_cuisines.add(c.lower().strip())
            elif isinstance(recipe['cuisines'], str):
                for c in recipe['cuisines'].split(','):
                    if c.strip():
                        recipe_cuisines.add(c.lower().strip())
        
        # Check cuisine field (less common)
        if 'cuisine' in recipe and recipe['cuisine']:
            if isinstance(recipe['cuisine'], list):
                for c in recipe['cuisine']:
                    if c and isinstance(c, str):
                        recipe_cuisines.add(c.lower().strip())
            elif isinstance(recipe['cuisine'], str):
                for c in recipe['cuisine'].split(','):
                    if c.strip():
                        recipe_cuisines.add(c.lower().strip())
        
        # Count each cuisine
        for cuisine in recipe_cuisines:
            if cuisine not in manual_cuisine_counts:
                manual_cuisine_counts[cuisine] = 0
                recipes_by_cuisine[cuisine] = []
            
            manual_cuisine_counts[cuisine] += 1
            recipes_by_cuisine[cuisine].append(title)
    
    # Report manual counts
    print("2. Manual cuisine counts:")
    for cuisine, count in sorted(manual_cuisine_counts.items()):
        print(f"   {cuisine}: {count}")
    
    # Test 3: Compare with API counts
    print(f"\n3. Comparing with API counts...")
    
    test_cuisines = ['indian', 'italian', 'mexican']
    for cuisine in test_cuisines:
        if cuisine in manual_cuisine_counts:
            manual_count = manual_cuisine_counts[cuisine]
            
            # Get API count
            response = requests.get(f"{BASE_URL}/get_recipes?cuisine={cuisine}&limit=1000")
            if response.status_code == 200:
                data = response.json()
                api_count = data.get('total', 0)
                
                print(f"\n   {cuisine.title()}:")
                print(f"     Manual count: {manual_count}")
                print(f"     API count: {api_count}")
                
                if manual_count != api_count:
                    print(f"     ⚠️  MISMATCH! Difference: {abs(manual_count - api_count)}")
                    
                    # Show some recipes that should match
                    if cuisine in recipes_by_cuisine:
                        print(f"     Sample recipes that should match:")
                        for i, title in enumerate(recipes_by_cuisine[cuisine][:3], 1):
                            print(f"       {i}. {title}")
                else:
                    print(f"     ✅ Counts match")
            else:
                print(f"   Error getting {cuisine} recipes: {response.status_code}")
        else:
            print(f"   {cuisine.title()}: Not found in manual count")
    
    # Test 4: Check for data inconsistencies
    print(f"\n4. Checking for data inconsistencies...")
    
    # Look for recipes with unexpected cuisine values
    unexpected_cuisines = []
    for recipe in recipes:
        title = recipe.get('title', 'Unknown')
        
        # Check cuisines field
        if 'cuisines' in recipe and recipe['cuisines']:
            if isinstance(recipe['cuisines'], list):
                for c in recipe['cuisines']:
                    if c and isinstance(c, str):
                        cuisine_lower = c.lower().strip()
                        if cuisine_lower not in manual_cuisine_counts:
                            unexpected_cuisines.append({
                                'title': title,
                                'cuisine': c,
                                'field': 'cuisines'
                            })
            elif isinstance(recipe['cuisines'], str):
                for c in recipe['cuisines'].split(','):
                    if c.strip():
                        cuisine_lower = c.lower().strip()
                        if cuisine_lower not in manual_cuisine_counts:
                            unexpected_cuisines.append({
                                'title': title,
                                'cuisine': c.strip(),
                                'field': 'cuisines'
                            })
    
    if unexpected_cuisines:
        print(f"   Found {len(unexpected_cuisines)} recipes with unexpected cuisine values:")
        for i, item in enumerate(unexpected_cuisines[:5], 1):
            print(f"     {i}. {item['title']} - '{item['cuisine']}' (from {item['field']})")
        if len(unexpected_cuisines) > 5:
            print(f"     ... and {len(unexpected_cuisines) - 5} more")
    else:
        print(f"   No unexpected cuisine values found")

if __name__ == "__main__":
    test_cuisine_matching_logic()
