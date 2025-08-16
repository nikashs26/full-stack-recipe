#!/usr/bin/env python3
"""
Test script to compare search results for "chi" vs "chicken"
This will help identify why substring search isn't working
"""

import requests
import json

def test_search_comparison():
    """Test search for 'chi' vs 'chicken' to see the difference"""
    
    base_url = "http://localhost:5003"
    
    print("🔍 Testing Search: 'chi' vs 'chicken'")
    print("=" * 50)
    
    # Test 1: Search for "chi" (should find recipes with "chicken" in title)
    print("\n1. Testing search for 'chi':")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/get_recipes", params={
            "query": "chi",
            "ingredient": "",
            "offset": 0,
            "limit": 20
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Total results: {data.get('total', 0)}")
            print(f"📝 Recipes found: {len(data.get('results', []))}")
            
            if data.get('results'):
                print("\n📋 Sample recipe titles:")
                for i, recipe in enumerate(data['results'][:5]):
                    title = recipe.get('title', 'No title')
                    print(f"  {i+1}. {title}")
            else:
                print("❌ No recipes found for 'chi'")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Search for "chicken" (should find recipes with "chicken" in title)
    print("\n2. Testing search for 'chicken':")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/get_recipes", params={
            "query": "chicken",
            "ingredient": "",
            "offset": 0,
            "limit": 20
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Total results: {data.get('total', 0)}")
            print(f"📝 Recipes found: {len(data.get('results', []))}")
            
            if data.get('results'):
                print("\n📋 Sample recipe titles:")
                for i, recipe in enumerate(data['results'][:5]):
                    title = recipe.get('title', 'No title')
                    print(f"  {i+1}. {title}")
            else:
                print("❌ No recipes found for 'chicken'")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Search for "chi" in ingredients (should find recipes with chicken in ingredients)
    print("\n3. Testing ingredient search for 'chi':")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/get_recipes", params={
            "query": "",
            "ingredient": "chi",
            "offset": 0,
            "limit": 20
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Total results: {data.get('total', 0)}")
            print(f"📝 Recipes found: {len(data.get('results', []))}")
            
            if data.get('results'):
                print("\n📋 Sample recipe titles:")
                for i, recipe in enumerate(data['results'][:5]):
                    title = recipe.get('title', 'No title')
                    print(f"  {i+1}. {title}")
            else:
                print("❌ No recipes found for ingredient 'chi'")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 Analysis:")
    print("- If 'chi' returns 0 results but 'chicken' returns results, substring search is broken")
    print("- If 'chi' in ingredients returns results, the data exists but title search is failing")
    print("- Check backend logs for detailed debugging information")

if __name__ == "__main__":
    test_search_comparison()
