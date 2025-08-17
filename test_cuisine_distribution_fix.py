#!/usr/bin/env python3
"""
Test script to verify that the cuisine distribution fix is working correctly
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def test_cuisine_distribution_fix():
    """Test that recommendations are properly distributed across multiple cuisines"""
    
    print("=== Testing Cuisine Distribution Fix ===\n")
    
    # Test 1: Check if the backend is running and accessible
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
    
    # Test 2: Check individual cuisine counts
    print("\n2. Checking individual cuisine counts...")
    cuisines = ["indian", "italian", "mexican"]
    cuisine_counts = {}
    
    for cuisine in cuisines:
        response = requests.get(f"{BASE_URL}/get_recipes?cuisine={cuisine}&limit=1000")
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            cuisine_counts[cuisine] = count
            print(f"   {cuisine.capitalize()}: {count} recipes")
        else:
            print(f"   ❌ Error getting {cuisine} recipes: {response.status_code}")
    
    # Test 3: Check combined cuisine search
    print("\n3. Testing combined cuisine search...")
    combined_cuisines = ",".join(cuisines)
    response = requests.get(f"{BASE_URL}/get_recipes?cuisine={combined_cuisines}&limit=1000")
    
    if response.status_code == 200:
        data = response.json()
        combined_count = data.get('total', 0)
        expected_count = sum(cuisine_counts.values())
        
        print(f"   Combined search ({combined_cuisines}): {combined_count} recipes")
        print(f"   Expected total: {expected_count} recipes")
        
        if combined_count == expected_count:
            print("   ✅ Combined cuisine search is working correctly")
        else:
            print(f"   ⚠️  Combined count ({combined_count}) doesn't match expected ({expected_count})")
    else:
        print(f"   ❌ Error in combined cuisine search: {response.status_code}")
    
    # Test 4: Check if recommendations endpoint is working
    print("\n4. Testing recommendations endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/smart-features/recommendations/simple?limit=8")
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            print(f"   ✅ Recommendations endpoint working: {len(recommendations)} recipes")
            
            # Analyze cuisine distribution in recommendations
            if recommendations:
                cuisine_distribution = {}
                for recipe in recommendations:
                    cuisine = recipe.get('cuisine', 'Unknown')
                    cuisine_distribution[cuisine] = cuisine_distribution.get(cuisine, 0) + 1
                
                print(f"   📊 Cuisine distribution in recommendations:")
                for cuisine, count in sorted(cuisine_distribution.items()):
                    print(f"      {cuisine}: {count} recipes")
                
                # Check if we have multiple cuisines represented
                if len(cuisine_distribution) > 1:
                    print("   ✅ Multiple cuisines are represented in recommendations")
                else:
                    print("   ⚠️  Only one cuisine is represented in recommendations")
        else:
            print(f"   ❌ Recommendations endpoint returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing recommendations: {e}")
    
    print("\n=== Test Complete ===")
    print("\nNote: If you're still seeing one cuisine dominating recommendations,")
    print("you may need to restart your backend server for the changes to take effect.")

if __name__ == "__main__":
    test_cuisine_distribution_fix()
