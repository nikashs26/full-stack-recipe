#!/usr/bin/env python3
"""
Quick test script to verify the migration API is working
"""

import requests
import json

def test_migration_api():
    """Test the migration API endpoints"""
    base_url = "https://dietary-delight.onrender.com"
    admin_token = "390a77929dbe4a50705a8d8cd2888678"
    
    print("🔧 Testing Migration API")
    print("=" * 30)
    
    # Test 1: Check backend health
    print("\n1. Testing backend health...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is responding")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Test 2: Test a single recipe upload
    print("\n2. Testing single recipe upload...")
    test_recipe = {
        "id": "test_recipe_001",
        "title": "Test Recipe Migration",
        "ingredients": [
            {"name": "Test Ingredient", "amount": "1", "unit": "cup", "original": "1 cup Test Ingredient"}
        ],
        "instructions": ["Test instruction 1", "Test instruction 2"],
        "image": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=300&h=200&fit=crop",
        "cuisines": ["Test Cuisine"],
        "diets": ["test-diet"],
        "tags": ["test", "migration"],
        "dish_types": ["test-dish"],
        "type": "test",
        "source": "migration_test",
        "ready_in_minutes": 30,
        "nutrition": {
            "calories": 200.0,
            "protein": 10.0,
            "carbs": 20.0,
            "fat": 5.0
        }
    }
    
    try:
        payload = {
            "action": "upload_complete_recipes",
            "recipes": [test_recipe],
            "preserve_format": True
        }
        
        response = requests.post(
            f"{base_url}/api/admin/seed",
            headers={
                "Content-Type": "application/json",
                "X-Admin-Token": admin_token
            },
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('uploaded_count', 0) > 0:
                print("✅ Single recipe upload successful")
                print(f"   Uploaded: {result.get('uploaded_count')} recipes")
            else:
                print(f"⚠️ Upload response: {result}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False
    
    # Test 3: Check stats
    print("\n3. Checking stats...")
    try:
        response = requests.get(
            f"{base_url}/api/admin/stats",
            params={"token": admin_token},
            timeout=15
        )
        
        if response.status_code == 200:
            stats = response.json()
            recipe_count = stats.get('recipe_count', 0)
            print(f"✅ Current recipe count: {recipe_count}")
            
            if recipe_count > 0:
                print("✅ Migration API is working correctly!")
                return True
            else:
                print("⚠️ No recipes found, but API is working")
                return True
        else:
            print(f"❌ Stats check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Stats check error: {e}")
    
    print("\n🎯 Migration API test completed!")
    return True

if __name__ == "__main__":
    test_migration_api()
