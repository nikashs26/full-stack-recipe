#!/usr/bin/env python3
"""
Investigate why many recipes are missing cuisine data
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def investigate_missing_cuisines():
    """Investigate why many recipes are missing cuisine data"""
    
    print("=== Investigating Missing Cuisine Data ===\n")
    
    # Get all recipes to analyze
    print("1. Getting all recipes to analyze...")
    response = requests.get(f"{BASE_URL}/get_recipes?limit=1000")
    
    if response.status_code != 200:
        print(f"Error getting recipes: {response.status_code}")
        return
    
    data = response.json()
    recipes = data.get('results', [])
    total = data.get('total', 0)
    
    print(f"   Total recipes: {total}")
    print(f"   Analyzing {len(recipes)} recipes...\n")
    
    # Analyze recipe sources and data structure
    missing_cuisine_recipes = []
    cuisine_field_analysis = {
        'has_cuisine': 0,
        'has_cuisines': 0,
        'has_tags': 0,
        'has_neither': 0,
        'source_analysis': {}
    }
    
    for recipe in recipes:
        title = recipe.get('title', 'Unknown')
        source = recipe.get('source', 'unknown')
        
        # Check what cuisine-related fields exist
        has_cuisine = 'cuisine' in recipe and recipe['cuisine']
        has_cuisines = 'cuisines' in recipe and recipe['cuisines']
        has_tags = 'tags' in recipe and recipe['tags']
        
        # Track source analysis
        if source not in cuisine_field_analysis['source_analysis']:
            cuisine_field_analysis['source_analysis'][source] = {
                'total': 0,
                'has_cuisine': 0,
                'has_cuisines': 0,
                'has_tags': 0,
                'missing_all': 0
            }
        
        cuisine_field_analysis['source_analysis'][source]['total'] += 1
        
        if has_cuisine:
            cuisine_field_analysis['has_cuisine'] += 1
            cuisine_field_analysis['source_analysis'][source]['has_cuisine'] += 1
        
        if has_cuisines:
            cuisine_field_analysis['has_cuisines'] += 1
            cuisine_field_analysis['source_analysis'][source]['has_cuisines'] += 1
        
        if has_tags:
            cuisine_field_analysis['has_tags'] += 1
            cuisine_field_analysis['source_analysis'][source]['has_tags'] += 1
        
        # Check if recipe has any cuisine information
        if not (has_cuisine or has_cuisines or has_tags):
            cuisine_field_analysis['has_neither'] += 1
            cuisine_field_analysis['source_analysis'][source]['missing_all'] += 1
            missing_cuisine_recipes.append({
                'title': title,
                'source': source,
                'id': recipe.get('id', 'unknown')
            })
    
    # Report findings
    print("2. Overall cuisine field analysis:")
    print(f"   Recipes with 'cuisine' field: {cuisine_field_analysis['has_cuisine']}")
    print(f"   Recipes with 'cuisines' field: {cuisine_field_analysis['has_cuisines']}")
    print(f"   Recipes with 'tags' field: {cuisine_field_analysis['has_tags']}")
    print(f"   Recipes missing ALL cuisine data: {cuisine_field_analysis['has_neither']}")
    
    print(f"\n3. Analysis by source:")
    for source, stats in cuisine_field_analysis['source_analysis'].items():
        total = stats['total']
        missing_pct = (stats['missing_all'] / total * 100) if total > 0 else 0
        print(f"\n   Source: {source}")
        print(f"     Total recipes: {total}")
        print(f"     Has cuisine field: {stats['has_cuisine']}")
        print(f"     Has cuisines field: {stats['has_cuisines']}")
        print(f"     Has tags field: {stats['has_tags']}")
        print(f"     Missing all cuisine data: {stats['missing_all']} ({missing_pct:.1f}%)")
    
    print(f"\n4. Sample recipes missing cuisine data:")
    if missing_cuisine_recipes:
        for i, recipe in enumerate(missing_cuisine_recipes[:10], 1):
            print(f"   {i}. {recipe['title']} (Source: {recipe['source']}, ID: {recipe['id']})")
        if len(missing_cuisine_recipes) > 10:
            print(f"   ... and {len(missing_cuisine_recipes) - 10} more")
    
    # Check if there are patterns in missing data
    print(f"\n5. Recommendations:")
    if cuisine_field_analysis['has_neither'] > total * 0.5:
        print(f"   ⚠️  CRITICAL: More than 50% of recipes are missing cuisine data!")
        print(f"   This will cause major issues with cuisine-based filtering and search.")
        print(f"   Need to implement cuisine detection/assignment for missing recipes.")
    
    if cuisine_field_analysis['has_cuisines'] > cuisine_field_analysis['has_cuisine']:
        print(f"   ℹ️  Most recipes use 'cuisines' field rather than 'cuisine' field.")
        print(f"   Ensure the backend properly handles both fields.")
    
    if cuisine_field_analysis['has_neither'] > 0:
        print(f"   🔧 Consider implementing automatic cuisine detection based on:")
        print(f"      - Recipe title and ingredients")
        print(f"      - Recipe tags and categories")
        print(f"      - Source API data")

if __name__ == "__main__":
    investigate_missing_cuisines()
