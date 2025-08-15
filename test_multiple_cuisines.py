#!/usr/bin/env python3
"""
Test script to find recipes with multiple cuisine tags
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def find_recipes_with_multiple_cuisines():
    """Find recipes that might have multiple cuisine tags"""
    
    print("=== Finding Recipes with Multiple Cuisine Tags ===\n")
    
    # Get all recipes to analyze
    print("1. Getting all recipes to analyze...")
    response = requests.get(f"{BASE_URL}/get_recipes?limit=1000")
    
    if response.status_code != 200:
        print(f"Error getting recipes: {response.status_code}")
        return
    
    data = response.json()
    recipes = data.get('results', [])
    total = data.get('total', 0)
    
    print(f"   Found {total} total recipes")
    print(f"   Analyzing {len(recipes)} recipes...\n")
    
    # Analyze each recipe for multiple cuisines
    multiple_cuisine_recipes = []
    cuisine_counts = {}
    
    for recipe in recipes:
        title = recipe.get('title', 'Unknown')
        
        # Check cuisines field
        cuisines = []
        if 'cuisines' in recipe and recipe['cuisines']:
            if isinstance(recipe['cuisines'], list):
                cuisines.extend([c.lower() for c in recipe['cuisines'] if c])
            elif isinstance(recipe['cuisines'], str):
                cuisines.extend([c.strip().lower() for c in recipe['cuisines'].split(',') if c.strip()])
        
        # Check cuisine field
        if 'cuisine' in recipe and recipe['cuisine']:
            if isinstance(recipe['cuisine'], list):
                cuisines.extend([c.lower() for c in recipe['cuisine'] if c])
            elif isinstance(recipe['cuisine'], str):
                cuisines.extend([c.strip().lower() for c in recipe['cuisine'].split(',') if c.strip()])
        
        # Check tags field for cuisine tags
        if 'tags' in recipe and recipe['tags']:
            if isinstance(recipe['tags'], list):
                for tag in recipe['tags']:
                    if tag and isinstance(tag, str):
                        tag_lower = tag.lower()
                        if tag_lower in ['indian', 'italian', 'mexican', 'chinese', 'japanese', 'thai', 'french', 'greek', 'spanish', 'mediterranean', 'american']:
                            cuisines.append(tag_lower)
            elif isinstance(recipe['tags'], str):
                for tag in recipe['tags'].split(','):
                    tag_lower = tag.strip().lower()
                    if tag_lower in ['indian', 'italian', 'mexican', 'chinese', 'japanese', 'thai', 'french', 'greek', 'spanish', 'mediterranean', 'american']:
                        cuisines.append(tag_lower)
        
        # Remove duplicates and normalize
        cuisines = list(set(cuisines))
        
        # Count cuisines for this recipe
        if len(cuisines) > 1:
            multiple_cuisine_recipes.append({
                'title': title,
                'cuisines': cuisines,
                'count': len(cuisines)
            })
        
        # Count individual cuisines
        for cuisine in cuisines:
            cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
    
    # Report findings
    print("2. Recipes with multiple cuisine tags:")
    if multiple_cuisine_recipes:
        for recipe in multiple_cuisine_recipes[:10]:  # Show first 10
            print(f"   - {recipe['title']}: {recipe['cuisines']} ({recipe['count']} cuisines)")
        if len(multiple_cuisine_recipes) > 10:
            print(f"   ... and {len(multiple_cuisine_recipes) - 10} more")
    else:
        print("   No recipes found with multiple cuisine tags")
    
    print(f"\n3. Individual cuisine counts (including duplicates):")
    for cuisine, count in sorted(cuisine_counts.items()):
        print(f"   {cuisine}: {count}")
    
    print(f"\n4. Analysis:")
    total_individual_count = sum(cuisine_counts.values())
    print(f"   Total individual cuisine counts: {total_individual_count}")
    print(f"   Total recipes: {total}")
    print(f"   Duplication factor: {total_individual_count / total:.2f}x")
    
    if multiple_cuisine_recipes:
        print(f"   Recipes with multiple cuisines: {len(multiple_cuisine_recipes)}")
        print(f"   This explains why combined searches show fewer results!")

if __name__ == "__main__":
    find_recipes_with_multiple_cuisines()
