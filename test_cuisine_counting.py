#!/usr/bin/env python3
"""
Test script to investigate cuisine counting discrepancy
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def test_cuisine_counts():
    """Test individual vs multiple cuisine counts"""
    
    print("=== Testing Cuisine Counts ===\n")
    
    # Test individual cuisines
    print("1. Testing individual cuisine counts:")
    
    # Test Indian cuisine
    response = requests.get(f"{BASE_URL}/get_recipes?cuisine=indian&limit=1000")
    if response.status_code == 200:
        data = response.json()
        indian_count = data.get('total', 0)
        print(f"   Indian only: {indian_count} recipes")
    else:
        print(f"   Error getting Indian recipes: {response.status_code}")
        indian_count = 0
    
    # Test Italian cuisine
    response = requests.get(f"{BASE_URL}/get_recipes?cuisine=italian&limit=1000")
    if response.status_code == 200:
        data = response.json()
        italian_count = data.get('total', 0)
        print(f"   Italian only: {italian_count} recipes")
    else:
        print(f"   Error getting Italian recipes: {response.status_code}")
        italian_count = 0
    
    # Test both cuisines together
    print("\n2. Testing combined cuisine count:")
    response = requests.get(f"{BASE_URL}/get_recipes?cuisine=indian,italian&limit=1000")
    if response.status_code == 200:
        data = response.json()
        combined_count = data.get('total', 0)
        print(f"   Indian + Italian: {combined_count} recipes")
    else:
        print(f"   Error getting combined recipes: {response.status_code}")
        combined_count = 0
    
    # Analysis
    print(f"\n3. Analysis:")
    print(f"   Individual counts sum: {indian_count + italian_count}")
    print(f"   Combined count: {combined_count}")
    
    if combined_count < max(indian_count, italian_count):
        print(f"   ⚠️  Combined count is LESS than individual counts!")
        print(f"   This suggests recipes are being counted multiple times in individual counts")
    elif combined_count > indian_count + italian_count:
        print(f"   ✅ Combined count is MORE than sum of individual counts")
        print(f"   This suggests some recipes have multiple cuisine tags")
    else:
        print(f"   ℹ️  Combined count equals sum of individual counts")
        print(f"   This suggests no overlap between cuisines")
    
    # Test with a small sample to see actual recipes
    print(f"\n4. Sample recipes from combined search:")
    if combined_count > 0:
        response = requests.get(f"{BASE_URL}/get_recipes?cuisine=indian,italian&limit=5")
        if response.status_code == 200:
            data = response.json()
            recipes = data.get('results', [])
            for i, recipe in enumerate(recipes[:3], 1):
                title = recipe.get('title', 'Unknown')
                cuisines = recipe.get('cuisines', [])
                cuisine = recipe.get('cuisine', '')
                print(f"   {i}. {title}")
                print(f"      Cuisines: {cuisines}")
                print(f"      Cuisine: {cuisine}")
                print()

if __name__ == "__main__":
    test_cuisine_counts()
