#!/usr/bin/env python3
"""
Test preferences functionality on live backend
"""

import requests
import json

BACKEND_URL = "https://dietary-delight.onrender.com"

def test_preferences():
    """Test if preferences are working"""
    
    print("🧪 Testing preferences functionality...")
    
    # Test 1: Check if we can get recipes without preferences
    print("\n1️⃣ Testing basic recipe search...")
    response = requests.get(f"{BACKEND_URL}/api/get_recipes?limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Basic search works: {data.get('total', 0)} recipes found")
    else:
        print(f"❌ Basic search failed: {response.status_code}")
        return
    
    # Test 2: Test cuisine filtering
    print("\n2️⃣ Testing cuisine filtering...")
    response = requests.get(f"{BACKEND_URL}/api/get_recipes?cuisine=Italian&limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Italian filter works: {data.get('total', 0)} Italian recipes found")
    else:
        print(f"❌ Italian filter failed: {response.status_code}")
    
    # Test 3: Test dietary restrictions filtering
    print("\n3️⃣ Testing dietary restrictions filtering...")
    response = requests.get(f"{BACKEND_URL}/api/get_recipes?dietary_restrictions=vegetarian&limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Vegetarian filter works: {data.get('total', 0)} vegetarian recipes found")
    else:
        print(f"❌ Vegetarian filter failed: {response.status_code}")
    
    # Test 4: Test combined filters
    print("\n4️⃣ Testing combined filters...")
    response = requests.get(f"{BACKEND_URL}/api/get_recipes?cuisine=Italian&dietary_restrictions=vegetarian&limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Combined filters work: {data.get('total', 0)} Italian vegetarian recipes found")
    else:
        print(f"❌ Combined filters failed: {response.status_code}")
    
    # Test 5: Test cuisines endpoint
    print("\n5️⃣ Testing cuisines endpoint...")
    response = requests.get(f"{BACKEND_URL}/api/recipes/cuisines")
    if response.status_code == 200:
        data = response.json()
        cuisines = data.get('cuisines', [])
        print(f"✅ Cuisines endpoint works: {len(cuisines)} cuisines available")
        print(f"Sample cuisines: {cuisines[:10]}")
    else:
        print(f"❌ Cuisines endpoint failed: {response.status_code}")
    
    print("\n🎉 Preferences testing completed!")

if __name__ == "__main__":
    test_preferences()
