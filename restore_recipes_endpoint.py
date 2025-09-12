#!/usr/bin/env python3
"""
Recipe Restoration Script for Production Deployment
This script creates an endpoint to restore recipes to ChromaDB after deployment
"""

import requests
import json
import time

def trigger_recipe_restoration(backend_url="https://dietary-delight.onrender.com"):
    """
    Trigger recipe restoration on the deployed backend
    """
    try:
        print(f"🚀 Triggering recipe restoration on {backend_url}")
        
        # Create the restoration endpoint payload
        restore_payload = {
            "action": "restore_recipes",
            "source": "production_backup",
            "force": True
        }
        
        # Make request to trigger restoration
        response = requests.post(
            f"{backend_url}/api/admin/restore-recipes",
            json=restore_payload,
            timeout=300  # 5 minutes timeout for large recipe imports
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Recipe restoration successful!")
            print(f"📊 Restored {result.get('recipes_restored', 0)} recipes")
            return True
        else:
            print(f"❌ Recipe restoration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error triggering restoration: {e}")
        return False

def check_recipe_count(backend_url="https://dietary-delight.onrender.com"):
    """
    Check current recipe count in ChromaDB
    """
    try:
        response = requests.get(f"{backend_url}/api/recipe-counts", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            print(f"📊 Current recipe count: {count}")
            return count
        else:
            print(f"❌ Failed to get recipe count: {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"❌ Error checking recipe count: {e}")
        return 0

if __name__ == "__main__":
    print("🍳 Production Recipe Restoration Tool")
    print("=" * 50)
    
    # Check current state
    print("\n1. Checking current recipe count...")
    current_count = check_recipe_count()
    
    if current_count == 0:
        print("\n2. No recipes found - triggering restoration...")
        success = trigger_recipe_restoration()
        
        if success:
            print("\n3. Waiting for restoration to complete...")
            time.sleep(10)  # Wait for processing
            
            print("\n4. Checking final recipe count...")
            final_count = check_recipe_count()
            
            if final_count > 0:
                print(f"\n🎉 SUCCESS! Restored {final_count} recipes to production!")
            else:
                print(f"\n⚠️ Restoration may still be in progress. Check again in a few minutes.")
        else:
            print(f"\n❌ Restoration failed. Manual intervention may be required.")
    else:
        print(f"\n✅ Recipes already loaded ({current_count} found)")
    
    print("\n" + "=" * 50)
    print("🌐 Your site should now have all recipes available!")
