#!/usr/bin/env python3
"""
Test backend with logging to see what's happening
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def test_backend_logs():
    """Test backend with logging to see what's happening"""
    
    print("=== Testing Backend with Logging ===\n")
    
    # Test 1: Check if backend is running and accessible
    print("1. Testing backend connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/get_recipes?limit=1")
        if response.status_code == 200:
            print("   ✅ Backend is running and accessible")
        else:
            print(f"   ❌ Backend returned status {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to backend: {e}")
        return
    
    # Test 2: Test individual cuisine searches with detailed logging
    print(f"\n2. Testing individual cuisine searches...")
    
    test_cuisines = ['indian', 'italian']
    individual_counts = {}
    
    for cuisine in test_cuisines:
        print(f"\n   Testing '{cuisine}' cuisine...")
        response = requests.get(f"{BASE_URL}/get_recipes?cuisine={cuisine}&limit=1000")
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            individual_counts[cuisine] = count
            print(f"     Found {count} recipes")
            
            # Show first few recipes
            recipes = data.get('results', [])
            for i, recipe in enumerate(recipes[:3], 1):
                title = recipe.get('title', 'Unknown')
                cuisines = recipe.get('cuisines', [])
                cuisine_field = recipe.get('cuisine', '')
                print(f"       {i}. {title}")
                print(f"          cuisines: {cuisines}")
                print(f"          cuisine: {cuisine_field}")
        else:
            print(f"     Error: {response.status_code}")
    
    # Test 3: Test combined cuisine search
    print(f"\n3. Testing combined cuisine search...")
    
    combined_response = requests.get(f"{BASE_URL}/get_recipes?cuisine=indian,italian&limit=1000")
    
    if combined_response.status_code == 200:
        combined_data = combined_response.json()
        combined_count = combined_data.get('total', 0)
        
        print(f"   Combined search (indian,italian): {combined_count} recipes")
        
        # Calculate expected vs actual
        expected_total = sum(individual_counts.values())
        difference = expected_total - combined_count
        
        print(f"   Expected total: {expected_total}")
        print(f"   Difference: {difference}")
        
        if difference > 0:
            print(f"   ⚠️  Missing {difference} recipes in combined search!")
            
            # Show some recipes from combined search
            combined_recipes = combined_data.get('results', [])
            print(f"\n   Sample recipes from combined search:")
            for i, recipe in enumerate(combined_recipes[:5], 1):
                title = recipe.get('title', 'Unknown')
                cuisines = recipe.get('cuisines', [])
                cuisine_field = recipe.get('cuisine', '')
                print(f"     {i}. {title}")
                print(f"        cuisines: {cuisines}")
                print(f"        cuisine: {cuisine_field}")
        
        # Test 4: Check if there's a backend issue by testing different combinations
        print(f"\n4. Testing different cuisine combinations...")
        
        test_combinations = [
            "indian,mexican",
            "italian,mexican", 
            "indian,italian,mexican"
        ]
        
        for combo in test_combinations:
            response = requests.get(f"{BASE_URL}/get_recipes?cuisine={combo}&limit=1000")
            if response.status_code == 200:
                data = response.json()
                count = data.get('total', 0)
                print(f"   '{combo}': {count} recipes")
            else:
                print(f"   '{combo}': Error {response.status_code}")

if __name__ == "__main__":
    test_backend_logs()
