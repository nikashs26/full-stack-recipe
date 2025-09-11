#!/usr/bin/env python3
"""
Debug script to check ChromaDB status on Render
"""

import requests
import json
import os

def check_render_chromadb():
    """Check ChromaDB status on Render"""
    base_url = os.getenv('RENDER_URL', 'https://dietary-delight.onrender.com')
    
    print("🔍 ChromaDB Debug for Render")
    print("=" * 40)
    print(f"🌐 Render URL: {base_url}")
    
    # Test health endpoint
    try:
        print("\n1. Testing health endpoint...")
        response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test recipe cache status
    try:
        print("\n2. Testing recipe cache...")
        response = requests.get(f"{base_url}/api/debug-recipes", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Recipe count: {data.get('recipe_collection_count', 'Unknown')}")
            print(f"   Sample titles: {data.get('sample_titles', [])}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test user service initialization
    try:
        print("\n3. Testing user service...")
        # Try to register a test user to see the exact error
        test_data = {
            "email": "debug-test@example.com",
            "password": "TestPassword123!",
            "full_name": "Debug Test"
        }
        response = requests.post(
            f"{base_url}/api/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Registration status: {response.status_code}")
        if response.status_code != 201:
            print(f"   Error: {response.text}")
        else:
            print("   ✅ User registration successful")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test admin stats (if we have admin token)
    admin_token = os.getenv('ADMIN_TOKEN')
    if admin_token:
        try:
            print("\n4. Testing admin stats...")
            headers = {"X-Admin-Token": admin_token}
            response = requests.get(f"{base_url}/api/admin/stats", headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Stats: {json.dumps(data, indent=2)}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("\n4. Skipping admin test (no ADMIN_TOKEN set)")

if __name__ == "__main__":
    check_render_chromadb()
