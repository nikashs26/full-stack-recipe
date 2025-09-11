#!/usr/bin/env python3
"""
Script to trigger recipe seeding on the deployed app via admin API
"""
import requests
import json
import sys

# Your deployment URL
DEPLOYMENT_URL = "https://dietary-delight.onrender.com"

def trigger_seeding(admin_token=None):
    """Trigger recipe seeding via admin API"""
    
    if not admin_token:
        print("❌ Please provide your admin token")
        print("Get it from Render dashboard > Environment Variables > ADMIN_SEED_TOKEN")
        return False
    
    url = f"{DEPLOYMENT_URL}/api/admin/seed"
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Token": admin_token
    }
    
    # Try different file paths and limits
    configs = [
        {"path": "backend/recipes_data.json", "limit": 10000},
        {"path": "recipes_data.json", "limit": 10000},
        {"path": "/opt/render/project/src/backend/recipes_data.json", "limit": 10000},
        {"path": "/opt/render/project/src/recipes_data.json", "limit": 10000}
    ]
    
    for config in configs:
        print(f"\n🌱 Trying to seed with config: {config}")
        
        try:
            response = requests.post(url, headers=headers, json=config, timeout=60)
            
            print(f"Status: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                print("✅ Seeding successful!")
                return True
            elif response.status_code == 401:
                print("❌ Unauthorized - check your admin token")
                return False
            else:
                print(f"⚠️ Seeding failed for this config, trying next...")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out - seeding might still be in progress")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    print("❌ All seeding attempts failed")
    return False

def check_recipe_count():
    """Check current recipe count"""
    try:
        # Try to get recipes to see current count
        url = f"{DEPLOYMENT_URL}/api/recipes/search"
        params = {"query": "", "limit": 1, "offset": 0}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            total = data.get('pagination', {}).get('total', 0)
            print(f"📊 Current recipe count: {total}")
            return total
        else:
            print(f"❌ Failed to check recipe count: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking recipe count: {e}")
    
    return 0

def main():
    print("🚀 Recipe Seeding Tool for Deployment")
    print("=" * 50)
    
    # Check current recipe count
    print("\n1. Checking current recipe count...")
    count = check_recipe_count()
    
    if count > 0:
        print(f"✅ Found {count} recipes - seeding may not be needed")
        response = input("Continue with seeding anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Get admin token
    print("\n2. Admin token required:")
    print("   - Go to Render dashboard")
    print("   - Find your service > Environment Variables")
    print("   - Copy the value of ADMIN_SEED_TOKEN")
    
    admin_token = input("\nEnter admin token: ").strip()
    
    if not admin_token:
        print("❌ No token provided, exiting")
        return
    
    # Trigger seeding
    print("\n3. Triggering recipe seeding...")
    success = trigger_seeding(admin_token)
    
    if success:
        print("\n4. Checking new recipe count...")
        new_count = check_recipe_count()
        print(f"✅ Deployment now has {new_count} recipes!")
    else:
        print("\n❌ Seeding failed - check logs above for details")

if __name__ == "__main__":
    main()
