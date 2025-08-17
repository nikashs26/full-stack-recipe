#!/usr/bin/env python3
"""
Test script to verify that recommendations are properly distributed across multiple cuisines
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def test_recommendation_distribution():
    """Test that recommendations are properly distributed across multiple cuisines"""
    
    print("=== Testing Recommendation Distribution ===\n")
    
    # Test 1: Get recommendations for a user with multiple cuisine preferences
    print("1. Testing recommendations with multiple cuisines...")
    
    # Simulate a user with multiple cuisine preferences
    test_preferences = {
        "favoriteCuisines": ["indian", "italian", "mexican"],
        "favoriteFoods": ["chicken", "pasta"],
        "dietaryRestrictions": [],
        "foodsToAvoid": [],
        "cookingSkillLevel": "intermediate",
        "healthGoals": []
    }
    
    # Call the recommendations endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/smart-features/recommendations?limit=8")
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            
            print(f"   ✅ Got {len(recommendations)} recommendations")
            
            # Analyze cuisine distribution
            cuisine_counts = {}
            for recipe in recommendations:
                cuisine = recipe.get('cuisine', 'Unknown')
                if cuisine not in cuisine_counts:
                    cuisine_counts[cuisine] = 0
                cuisine_counts[cuisine] += 1
            
            print(f"\n2. Cuisine distribution in recommendations:")
            for cuisine, count in sorted(cuisine_counts.items()):
                print(f"   {cuisine}: {count} recipes")
            
            # Check if we have recipes from all requested cuisines
            requested_cuisines = set([c.lower() for c in test_preferences["favoriteCuisines"]])
            found_cuisines = set([c.lower() for c in cuisine_counts.keys()])
            
            print(f"\n3. Cuisine coverage analysis:")
            print(f"   Requested cuisines: {requested_cuisines}")
            print(f"   Found cuisines: {found_cuisines}")
            
            missing_cuisines = requested_cuisines - found_cuisines
            if missing_cuisines:
                print(f"   ⚠️  Missing cuisines: {missing_cuisines}")
            else:
                print(f"   ✅ All requested cuisines are represented")
            
            # Check distribution balance
            if len(cuisine_counts) > 1:
                min_count = min(cuisine_counts.values())
                max_count = max(cuisine_counts.values())
                balance_ratio = min_count / max_count if max_count > 0 else 0
                
                print(f"\n4. Distribution balance:")
                print(f"   Min recipes per cuisine: {min_count}")
                print(f"   Max recipes per cuisine: {max_count}")
                print(f"   Balance ratio: {balance_ratio:.2f}")
                
                if balance_ratio >= 0.5:
                    print(f"   ✅ Distribution is well balanced")
                elif balance_ratio >= 0.3:
                    print(f"   ⚠️  Distribution is moderately balanced")
                else:
                    print(f"   ❌ Distribution is poorly balanced")
            
        else:
            print(f"   ❌ Error getting recommendations: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Compare with direct cuisine search
    print(f"\n5. Comparing with direct cuisine search...")
    
    for cuisine in test_preferences["favoriteCuisines"]:
        response = requests.get(f"{BASE_URL}/get_recipes?cuisine={cuisine}&limit=10")
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            print(f"   {cuisine}: {count} total recipes available")
        else:
            print(f"   {cuisine}: Error {response.status_code}")

if __name__ == "__main__":
    test_recommendation_distribution()
